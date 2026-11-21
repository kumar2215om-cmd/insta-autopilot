"""Course videos uploaded straight to ReplyInbox (no YouTube needed).

Vercel functions take at most 4.5 MB per request and per response, so a video is uploaded in CHUNK-sized pieces
(each its own private Blob) and played back through /learn/.../video/<id> with HTTP Range requests, answered one
piece at a time. Browsers' <video> players handle partial answers, so seeking works.

Video: s:video:<id> = {id, acc, name, size, type, chunks: [{url, pathname}], done, created}.
"""
import secrets
import time

import requests

import files
import store

CHUNK = 3_500_000
MAX_MB = 1024
TYPES = {"mp4": "video/mp4", "m4v": "video/mp4", "mov": "video/quicktime", "webm": "video/webm"}


class VideoError(Exception):
    """A problem to show the person as it is."""


def get(vid):
    return store.get_json(f"s:video:{vid}") if vid and len(vid) <= 24 else None


def start(acc, name, size):
    """Begins an upload; returns the video record. The browser then sends pieces 0..n-1 and calls finish()."""
    name = files._clean(name)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in TYPES:
        raise VideoError("Upload an MP4, MOV or WebM video.")
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 0
    if not 0 < size <= MAX_MB * 1024 * 1024:
        raise VideoError(f"Videos can be up to {MAX_MB // 1024} GB. Compress it (HandBrake, or export at 1080p) and try again.")
    if not files.configured():
        raise VideoError("File storage isn't connected yet.")
    v = {"id": secrets.token_urlsafe(12), "acc": acc["id"], "name": name, "size": size, "type": TYPES[ext],
         "parts": -(-size // CHUNK), "chunks": {}, "done": False, "created": int(time.time())}
    store.set_json(f"s:video:{v['id']}", v)
    return v


def put_chunk(acc, vid, n, data):
    v = get(vid)
    if not v or v["acc"] != acc["id"] or v["done"]:
        raise VideoError("Upload not found. Start again.")
    if not 0 <= n < v["parts"]:
        raise VideoError("Wrong piece number.")
    want = min(CHUNK, v["size"] - n * CHUNK)
    if len(data) != want:
        raise VideoError("A piece arrived broken. Try again.")
    r = None
    for access in ("private", "public"):
        try:
            r = requests.put(f"{files.API}/", params={"pathname": f"replyinbox/{acc['id']}/video/{vid}/{n:05d}"}, data=data, timeout=60,
                             headers={"authorization": f"Bearer {files._token()}", "x-api-version": "13",
                                      "x-vercel-blob-store-id": files._store_id(), "x-vercel-blob-access": access,
                                      "x-content-type": "application/octet-stream"})
        except requests.RequestException:
            raise VideoError("Storage didn't answer. Retrying…")
        if r.ok:
            break
    if not r.ok:
        raise VideoError(f"Upload failed ({r.status_code}).")
    blob = r.json()
    v = get(vid)  # re-read: pieces arrive one after another
    v["chunks"][str(n)] = blob["url"]
    store.set_json(f"s:video:{vid}", v)
    return len(v["chunks"])


def finish(acc, vid):
    v = get(vid)
    if not v or v["acc"] != acc["id"]:
        raise VideoError("Upload not found.")
    missing = [n for n in range(v["parts"]) if str(n) not in v["chunks"]]
    if missing:
        raise VideoError(f"{len(missing)} pieces are missing. Upload again.")
    v["done"] = True
    store.set_json(f"s:video:{vid}", v)
    return v


def read(v, range_header):
    """(bytes, start, end) for a Range request, at most one piece long."""
    start, end = 0, v["size"] - 1
    if range_header and range_header.startswith("bytes="):
        a, _, b = range_header[6:].split(",")[0].partition("-")
        try:
            if a:
                start = int(a)
                end = int(b) if b else end
            else:  # bytes=-N: the last N bytes
                start = max(0, v["size"] - int(b))
        except ValueError:
            pass
    if not 0 <= start < v["size"]:
        raise VideoError("range")
    n = start // CHUNK
    end = min(end, v["size"] - 1, (n + 1) * CHUNK - 1)
    url = v["chunks"].get(str(n))
    if not url:
        raise VideoError("missing")
    off = start - n * CHUNK
    hdr = {"Range": f"bytes={off}-{off + end - start}"}
    if ".private.blob." in url:
        hdr["authorization"] = f"Bearer {files._token()}"
    r = requests.get(url, headers=hdr, timeout=30)
    if not r.ok:
        raise VideoError("fetch")
    data = r.content
    if r.status_code == 200:  # the store ignored Range: cut it here
        data = data[off:off + end - start + 1]
    return data, start, start + len(data) - 1


def delete(v):
    try:
        requests.post(f"{files.API}/delete", json={"urls": list(v["chunks"].values())}, timeout=20,
                      headers={"authorization": f"Bearer {files._token()}", "x-api-version": "13", "x-vercel-blob-store-id": files._store_id()})
    except requests.RequestException:
        pass
    store.redis("DEL", f"s:video:{v['id']}")
