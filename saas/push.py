"""Web push notifications (phone and computer), without a push library.

Pushes carry no data, so nothing needs encrypting: the service worker fetches the newest note from
/api/notifications/latest when a push arrives. The VAPID signing key is derived from SECRET_KEY, so no extra
setting is needed (changing SECRET_KEY means creators turn notifications on again).
"""
import base64
import hashlib
import json
import os
import time
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

import store

# Push services browsers use; subscriptions to anything else are refused (no requests to arbitrary hosts).
PUSH_HOSTS = ("fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com", ".notify.windows.com",
              ".push.apple.com")
MAX_DEVICES = 10
_N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551  # order of the P-256 curve


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _key():
    secret = os.environ.get("SECRET_KEY") or "replyinbox-dev-only"
    d = int(hashlib.sha256(("vapid|" + secret).encode()).hexdigest(), 16) % (_N - 1) + 1
    return ec.derive_private_key(d, ec.SECP256R1())


def public_key():
    """The applicationServerKey the browser needs to subscribe."""
    point = _key().public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return b64(point)


def _jwt(audience):
    header = b64(json.dumps({"typ": "JWT", "alg": "ES256"}).encode())
    claims = b64(json.dumps({"aud": audience, "exp": int(time.time()) + 12 * 3600,
                             "sub": "mailto:" + (os.environ.get("CONTACT_EMAIL") or "hello@replyinbox.in")}).encode())
    signing = f"{header}.{claims}".encode()
    r, s = decode_dss_signature(_key().sign(signing, ec.ECDSA(hashes.SHA256())))
    return f"{header}.{claims}.{b64(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))}"


def valid_endpoint(url):
    parts = urlparse(str(url or ""))
    host = parts.hostname or ""
    return parts.scheme == "https" and any(host == h or (h.startswith(".") and host.endswith(h)) for h in PUSH_HOSTS)


def _subs_key(ig_id):
    return store.account_key(ig_id, "push")


def subscribe(ig_id, endpoint):
    if not valid_endpoint(endpoint):
        raise ValueError("This browser's push service isn't supported.")
    key = _subs_key(ig_id)
    flat = store.redis("HGETALL", key) or []
    if endpoint not in flat[::2] and len(flat) // 2 >= MAX_DEVICES:
        store.redis("HDEL", key, flat[0])  # drop the oldest device
    store.redis("HSET", key, endpoint, int(time.time()))


def unsubscribe(ig_id, endpoint):
    store.redis("HDEL", _subs_key(ig_id), endpoint)


def devices(ig_id):
    return len((store.redis("HGETALL", _subs_key(ig_id)) or [])) // 2


def notify(acc, title, body, url="/app"):
    """Saves the note and wakes every device that turned notifications on. Never raises."""
    if acc.get("demo"):
        return 0
    notes = store.account_key(acc["id"], "notes")
    store.redis("LPUSH", notes, json.dumps({"title": title[:80], "body": body[:200], "url": url, "at": int(time.time())},
                                          ensure_ascii=False))
    store.redis("LTRIM", notes, 0, 19)
    sent = 0
    for endpoint in (store.redis("HGETALL", _subs_key(acc["id"])) or [])[::2]:
        try:
            parts = urlparse(endpoint)
            r = requests.post(endpoint, timeout=5, data=b"", headers={
                "TTL": "86400", "Urgency": "high", "Content-Length": "0",
                "Authorization": f"vapid t={_jwt(f'{parts.scheme}://{parts.netloc}')}, k={public_key()}"})
            if r.status_code in (404, 410):
                unsubscribe(acc["id"], endpoint)  # the device turned notifications off
            elif r.status_code < 400:
                sent += 1
        except Exception:
            pass
    return sent


def latest(ig_id):
    raw = store.redis("LRANGE", store.account_key(ig_id, "notes"), 0, 0) or []
    return json.loads(raw[0]) if raw else None
