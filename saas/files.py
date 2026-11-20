"""Private file uploads: PDFs, zips, images to send in DMs or put on the link page.

Turned on only for the Instagram usernames in FILES_ACCOUNTS (comma separated), so it stays a private
tool for now. Files live in a private Vercel Blob store (connect it to this project: Vercel → Storage →
Blob → Connect, which adds BLOB_READ_WRITE_TOKEN) and are served through /f/<id>/<name>.
"""
import os
import secrets
import time

import requests
from flask import request

import store

MAX_MB = 4  # Vercel functions reject request bodies over 4.5 MB
MAX_FILES = 200
TYPES = {"pdf", "zip", "png", "jpg", "jpeg", "webp", "gif", "mp4", "mp3", "m4a", "wav", "ogg", "txt", "md", "csv", "json", "epub", "docx", "xlsx", "pptx"}
API = "https://vercel.com/api/blob"


class FileError(Exception):
    """A problem to show the person as it is."""


def _env(name):
    return os.environ.get(name, "").strip().strip("\"'").strip()


def _token():
    """Read-write token if one was added, else the per-request Vercel OIDC token (stores connected without a token)."""
    tok = _env("BLOB_READ_WRITE_TOKEN")
    if tok:
        return tok
    if not _store_id():
        return ""
    try:
        return (request.headers.get("x-vercel-oidc-token") or _env("VERCEL_OIDC_TOKEN")).strip()
    except RuntimeError:  # outside a request
        return _env("VERCEL_OIDC_TOKEN")


def _store_id():
    sid = _env("BLOB_STORE_ID").removeprefix("store_")
    tok = _env("BLOB_READ_WRITE_TOKEN")
    return sid or (tok.split("_")[3] if tok.count("_") >= 4 else "")


def configured():
    return bool(_store_id() and _token())


def available(acc):
    if not acc or acc.get("demo"):
        return False
    allowed = {u.strip().lstrip("@").lower() for u in _env("FILES_ACCOUNTS").split(",") if u.strip()}
    return (acc.get("username") or "").lower() in allowed or acc.get("id") in allowed


def _key(acc_id):
    return store.account_key(acc_id, "files")


def load(acc_id):
    return store.get_json(_key(acc_id), [])


def _clean(filename):
    name = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in os.path.basename(filename or ""))
    return name[-80:].lstrip(".-") or "file"


def link(f):
    return f"/f/{f['id']}/{f['name']}"


def view(f):
    return {**{k: f[k] for k in ("id", "name", "size", "type", "created")}, "url": link(f)}


def upload(acc, filename, data, mimetype, paid=False, listed=True):
    name = _clean(filename)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in TYPES:
        raise FileError(f"File type .{ext or '?'} isn't allowed. Use: " + ", ".join(sorted(TYPES)))
    if not data:
        raise FileError("That file is empty.")
    if len(data) > MAX_MB * 1024 * 1024:
        raise FileError(f"File is over {MAX_MB} MB. Upload it to Google Drive and paste that link instead.")
    items = load(acc["id"])
    if listed and len(items) >= MAX_FILES:
        raise FileError(f"You have {MAX_FILES} files. Delete some old ones first.")
    if not configured():
        raise FileError("File storage isn't connected yet (Vercel → Storage → Blob → Connect to this project).")
    fid = secrets.token_urlsafe(9)
    r = None
    for access in ("private", "public"):  # the store's access type decides which one it accepts
        try:
            r = requests.put(f"{API}/", params={"pathname": f"replyinbox/{acc['id']}/{fid}-{name}"}, data=data, timeout=60,
                             headers={"authorization": f"Bearer {_token()}", "x-api-version": "13",
                                      "x-vercel-blob-store-id": _store_id(), "x-vercel-blob-access": access,
                                      "x-content-type": mimetype or "application/octet-stream"})
        except requests.RequestException:
            raise FileError("Storage didn't answer. Try again in a minute.")
        if r.ok:
            break
    if not r.ok:
        print(f"Blob upload refused: HTTP {r.status_code} {r.text[:200]}")
        raise FileError(f"Upload failed ({r.status_code}). Try again.")
    blob = r.json()
    f = {"id": fid, "acc": acc["id"], "name": name, "size": len(data), "type": mimetype or "", "created": int(time.time()),
         "blob": blob["url"], "pathname": blob["pathname"], "paid": bool(paid)}
    store.set_json(f"s:file:{fid}", f)
    if listed:  # product files (paid) aren't listed in Files
        items.insert(0, f)
        store.set_json(_key(acc["id"]), items)
    return f


def delete(acc, fid):
    items = load(acc["id"])
    f = next((x for x in items if x["id"] == fid), None)
    if not f:
        return False
    try:  # best effort: the link stops working either way
        requests.post(f"{API}/delete", json={"urls": [f["blob"]]}, timeout=20,
                      headers={"authorization": f"Bearer {_token()}", "x-api-version": "13", "x-vercel-blob-store-id": _store_id()})
    except requests.RequestException:
        pass
    store.redis("DEL", f"s:file:{fid}")
    store.set_json(_key(acc["id"]), [x for x in items if x["id"] != fid])
    return True


def delete_all(acc):
    for f in load(acc["id"]):
        delete(acc, f["id"])


def fetch(fid, name=None, paid_ok=False):
    """The file's bytes, type and record, or None. Paid product files only with paid_ok (a valid download token)."""
    f = store.get_json(f"s:file:{fid}") if fid else None
    if not f or (name is not None and f["name"] != name) or not configured() or (f.get("paid") and not paid_ok):
        return None
    if ".private.blob." in f["blob"]:
        r = requests.get(f["blob"], headers={"authorization": f"Bearer {_token()}"}, timeout=30)
    else:
        r = requests.get(f["blob"], timeout=30)
    if not r.ok:
        return None
    return r.content, r.headers.get("content-type") or f["type"] or "application/octet-stream", f
