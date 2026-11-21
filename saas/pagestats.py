"""Link-in-bio analytics (like SuperProfile → Store → Analytics): visits, unique visitors, clicks, CTR, time to click,
top locations, where visitors came from, devices and the most clicked links, per IST day.

Keys (per account, per day, kept 100 days): pv:<day> {visits, unique, clicks, tsum, tcount}, pvu:<day> (set of visitor
hashes), pvc:<day> countries, pvx:<day> cities, pvs:<day> sources, pvd:<day> devices, pvl:<day> clicks per link.
"""
import hashlib
import re

import store

KEEP = 100 * 86400
BOT = re.compile(r"bot|crawl|spider|slurp|preview|facebookexternalhit|meta-externalagent|whatsapp/|twitterbot|slackbot|telegrambot|"
                 r"discordbot|linkedinbot|embedly|curl|wget|python-requests|httpclient|headless|lighthouse|pingdom|uptime", re.I)
SOURCES = (("instagram", r"instagram"), ("whatsapp", r"whatsapp|wa\.me"), ("facebook", r"facebook|fb\.com"), ("youtube", r"youtube|youtu\.be"),
           ("google", r"google\."), ("x", r"t\.co|twitter|x\.com"), ("telegram", r"t\.me|telegram"), ("linkedin", r"linkedin"))


def is_bot(ua):
    return not ua or bool(BOT.search(ua))


def source_of(referrer, ua):
    """Where the visit came from. Instagram's in-app browser often sends no referrer, so its user agent counts too."""
    text = f"{referrer or ''} {'instagram' if 'Instagram' in (ua or '') else ''} {'whatsapp' if 'WhatsApp' in (ua or '') else ''}"
    for name, pat in SOURCES:
        if re.search(pat, text, re.I):
            return name
    return "direct" if not referrer else "other"


def device_of(ua):
    ua = ua or ""
    if re.search(r"iPad|Tablet", ua):
        return "tablet"
    return "mobile" if re.search(r"Mobi|Android|iPhone", ua) else "desktop"


def _k(acc_id, part, day):
    return store.account_key(acc_id, f"{part}:{day}")


def _inc(key, field, n=1):
    store.redis("HINCRBY", key, field, n)
    store.redis("EXPIRE", key, KEEP)


def visit(acc_id, ip, ua, country="", city="", referrer=""):
    if is_bot(ua):
        return False
    day = store.day_str()
    _inc(_k(acc_id, "pv", day), "visits")
    who = hashlib.sha256(f"{ip}|{ua}".encode()).hexdigest()[:16]
    uk = _k(acc_id, "pvu", day)
    if store.redis("SADD", uk, who):
        _inc(_k(acc_id, "pv", day), "unique")
    store.redis("EXPIRE", uk, 2 * 86400)
    if country:
        _inc(_k(acc_id, "pvc", day), country.upper()[:2])
    if city:
        _inc(_k(acc_id, "pvx", day), f"{city[:40]}, {country.upper()[:2]}" if country else city[:40])
    _inc(_k(acc_id, "pvs", day), source_of(referrer, ua))
    _inc(_k(acc_id, "pvd", day), device_of(ua))
    return True


def click(acc_id, item_id, ua="", seconds=None):
    if is_bot(ua):
        return
    day = store.day_str()
    _inc(_k(acc_id, "pv", day), "clicks")
    _inc(_k(acc_id, "pvl", day), item_id[:40])
    if seconds is not None and 0 <= seconds <= 3600:
        _inc(_k(acc_id, "pv", day), "tsum", int(seconds))
        _inc(_k(acc_id, "pv", day), "tcount")


def report(acc_id, days=7):
    """Totals, a per-day series and the top lists for the last `days` days (IST), plus the period before for % change."""
    days = max(1, min(90, int(days)))
    series, tot, prev = [], {"visits": 0, "unique": 0, "clicks": 0, "tsum": 0, "tcount": 0}, {"visits": 0, "clicks": 0}
    tops = {"countries": {}, "cities": {}, "sources": {}, "devices": {}, "links": {}}
    parts = {"countries": "pvc", "cities": "pvx", "sources": "pvs", "devices": "pvd", "links": "pvl"}
    for i in range(days - 1, -1, -1):
        day = store.day_str(i)
        d = store.hash_all(_k(acc_id, "pv", day))
        series.append({"date": day, "visits": d.get("visits", 0), "unique": d.get("unique", 0), "clicks": d.get("clicks", 0)})
        for f in tot:
            tot[f] += d.get(f, 0)
        for name, part in parts.items():
            for k, v in store.hash_all(_k(acc_id, part, day)).items():
                tops[name][k] = tops[name].get(k, 0) + v
    for i in range(2 * days - 1, days - 1, -1):
        d = store.hash_all(_k(acc_id, "pv", store.day_str(i)))
        prev["visits"] += d.get("visits", 0)
        prev["clicks"] += d.get("clicks", 0)
    pct = lambda a, b: round(100 * (a - b) / b) if b else None
    return {"days": days, "visits": tot["visits"], "unique": tot["unique"], "clicks": tot["clicks"],
            "ctr": round(100 * tot["clicks"] / tot["visits"], 1) if tot["visits"] else 0,
            "time_to_click": round(tot["tsum"] / tot["tcount"], 1) if tot["tcount"] else None,
            "change": {"visits": pct(tot["visits"], prev["visits"]), "clicks": pct(tot["clicks"], prev["clicks"])},
            "series": series, **{k: sorted(v.items(), key=lambda kv: -kv[1])[:10] for k, v in tops.items()}}
