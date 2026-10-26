"""Google Flights scraper: any origin, any currency, one adult.

Fetch strategy: build the ?tfs= protobuf URL with fast_flights' encoder, GET it
with urllib (Google server-renders the full result list into the HTML), then
parse the rendered text. The JSON payload no longer exposes a stable price
field, so text parsing is the reliable path.

Each call returns the cheapest *round-trip* totals for a (destination, weekend)
cell, with the outbound leg optionally constrained to an evening window.
"""
import hashlib
import html as _html
import os
import re
import time
import urllib.parse
import urllib.request

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
os.makedirs(CACHE, exist_ok=True)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def build_url(o, d, out_date, ret_date=None, curr="SGD",
              out_window=None, ret_window=None):
    from fast_flights import FlightQuery, create_query

    kw = {}
    if out_window:
        kw["earliest_departure_hour"], kw["latest_departure_hour"] = out_window
    l1 = FlightQuery(date=out_date, from_airport=o, to_airport=d, **kw)

    legs, trip = [l1], "one-way"
    if ret_date:
        kw2 = {}
        if ret_window:
            kw2["earliest_departure_hour"], kw2["latest_departure_hour"] = ret_window
        legs.append(FlightQuery(date=ret_date, from_airport=d, to_airport=o, **kw2))
        trip = "round-trip"

    q = create_query(flights=legs, trip=trip, seat="economy",
                     currency=curr, language="en")
    return "https://www.google.com/travel/flights?" + urllib.parse.urlencode(q.params())


def _path(url):
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:16] + ".html")


def fetch(url, tries=3, force=False):
    path = _path(url)
    if os.path.exists(path) and not force:
        return open(path, encoding="utf-8", errors="replace").read()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept-Language": "en-SG,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            })
            with urllib.request.urlopen(req, timeout=50) as r:
                body = r.read().decode("utf-8", "replace")
            if len(body) < 400_000:
                raise RuntimeError(f"small page ({len(body)}B)")
            open(path, "w", encoding="utf-8").write(body)
            return body
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + 4 * i)
    raise RuntimeError(f"fetch failed: {last}")


def visible_text(h):
    body = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", _html.unescape(body))


SEG = re.compile(
    r"(?P<price>[\d,]+)\s+(?:(?P<trip>round trip|one way)\s+)?"
    r"(?P<dep>\d{1,2}:\d{2}\s?[AP]M)\s+(?P<orig>[A-Z]{3})\s+"
    r"(?P<arr>\d{1,2}:\d{2}\s?[AP]M)(?P<plus>\s\+\d)?\s+(?P<dest>[A-Z]{3})\s+"
    r"(?:SGD\s+)?[\d,]+\s*(?:(?:round trip|one way)\s+)?"
    r"(?P<stops>Nonstop|\d+\s+stops?)(?:\s+in\s+[A-Z]{3})?\s+(?:Nonstop|\d+\s+stops?)\s+"
    r"(?P<dur>(?:\d+\s+hr)?\s*(?:\d+\s+min)?)?\s*"
    r"(?P<air>[A-Z][A-Za-z0-9 .&'\-]*?)\s+(?P<co2>\d+)\s+kg\s+CO2e"
)

AIR_ALIASES = [
    ("Singapore Airlines", "Singapore Airlines"), ("Malaysia Airlines", "Malaysia Airlines"),
    ("Batik Air", "Batik Air"), ("AirAsia", "AirAsia"), ("Scoot", "Scoot"),
    ("VietJet", "VietJet"), ("Vietjet", "VietJet"), ("Vietnam Airlines", "Vietnam Airlines"),
    ("Thai AirAsia", "Thai AirAsia"), ("Thai Lion", "Thai Lion Air"), ("Thai Airways", "Thai Airways"),
    ("Firefly", "Firefly"), ("Jetstar", "Jetstar"), ("Cebu Pacific", "Cebu Pacific"),
    ("Philippine Airlines", "Philippine Airlines"), ("Garuda", "Garuda Indonesia"),
    ("Citilink", "Citilink"), ("Lion Air", "Lion Air"), ("Super Air Jet", "Super Air Jet"),
    ("Bamboo", "Bamboo Airways"), ("Emirates", "Emirates"), ("Qatar", "Qatar Airways"),
    ("Cathay", "Cathay Pacific"), ("Ethiopian", "Ethiopian"), ("Gulf Air", "Gulf Air"),
    ("Turkish", "Turkish Airlines"), ("EVA", "EVA Air"), ("China Airlines", "China Airlines"),
    ("Korean Air", "Korean Air"), ("Asiana", "Asiana"), ("ANA", "ANA"),
    ("Japan Airlines", "Japan Airlines"), ("Peach", "Peach"), ("Starlux", "STARLUX"),
    ("Qantas", "Qantas"), ("IndiGo", "IndiGo"), ("Royal Brunei", "Royal Brunei"),
    ("Thai Vietjet", "Thai VietJet"), ("Myanmar", "Myanmar Airways"),
]


def norm_air(a):
    """Marketing carrier leads the string; codeshare partners follow it."""
    a = (a or "").strip()
    low = a.lower()
    for k, v in sorted(AIR_ALIASES, key=lambda kv: -len(kv[0])):
        if low.startswith(k.lower()):
            return v
    for k, v in sorted(AIR_ALIASES, key=lambda kv: -len(kv[0])):
        if k.lower() in low:
            return v
    return a


def parse(h):
    """Return list of fare dicts (deduped, cheapest-first)."""
    txt = visible_text(h)
    out, seen = [], set()
    for m in SEG.finditer(txt):
        d = m.groupdict()
        if "Business" in txt[max(0, m.start() - 40):m.start()]:
            continue
        rec = {
            "price": int(d["price"].replace(",", "")),
            "dep": d["dep"].replace("\u202f", " ").strip(),
            "arr": d["arr"].replace("\u202f", " ").strip(),
            "plus": (d["plus"] or "").strip(),
            "dur": re.sub(r"\s+", " ", (d["dur"] or "").strip()),
            "stops": "0" if d["stops"].lower() == "nonstop" else d["stops"],
            "air": norm_air(d["air"]),
            "co2": int(d["co2"]),
        }
        k = (rec["dep"], rec["arr"], rec["plus"], rec["air"], rec["price"], rec["stops"])
        if k in seen:
            continue
        seen.add(k)
        out.append(rec)
    out.sort(key=lambda r: r["price"])
    return out


def insights(h):
    """Google's own price verdict for the searched dates (its 30-60d model)."""
    t = visible_text(h)
    m = re.search(r"Prices are currently (very )?(low|typical|high)", t)
    verdict = None
    if m:
        verdict = {"low": "低", "typical": "接近均价", "high": "偏高"}[m.group(2)]
        if m.group(1):
            verdict = "很低" if m.group(2) == "low" else "很高"
    rng = re.search(r"The usual price range is (SGD[\d,]+)[^S]{0,6}(SGD[\d,]+)", t)
    return {"verdict": verdict, "usual_range": rng.groups() if rng else None}


def hour(t):
    """'7:45 PM' -> 19.75 ; None if unparseable."""
    m = re.match(r"(\d{1,2}):(\d{2})\s*([AP]M)", t or "")
    if not m:
        return None
    h, mi, ap = int(m.group(1)) % 12, int(m.group(2)), m.group(3)
    return h + mi / 60 + (12 if ap == "PM" else 0)


def query(o, d, out_date, ret_date=None, out_window=None, ret_window=None,
          cleanup=True, force=False):
    url = build_url(o, d, out_date, ret_date, out_window=out_window,
                    ret_window=ret_window)
    html0 = fetch(url, force=force)
    rows = parse(html0)
    ins = insights(html0)
    if not rows and (out_window or ret_window):
        url = build_url(o, d, out_date, ret_date)   # window too tight -> unfiltered
        html0 = fetch(url, force=force)
        rows = parse(html0)
        ins = insights(html0)
        out_window = ret_window = None
    rec = {"from": o, "to": d, "out": out_date, "ret": ret_date,
           "out_window": out_window, "ret_window": ret_window,
           "url": url, "n": len(rows), "rows": rows, **ins}
    if cleanup:
        try:
            os.remove(_path(url))
        except OSError:
            pass
    return rec


if __name__ == "__main__":
    import json
    import sys
    r = query(sys.argv[1], sys.argv[2], sys.argv[3],
              sys.argv[4] if len(sys.argv) > 4 else None,
              out_window=(15, 23) if len(sys.argv) > 4 else None)
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, ensure_ascii=False))
    for x in r["rows"][:8]:
        print(x["price"], x["air"], x["dep"], "->", x["arr"], x["plus"],
              x["stops"], x["dur"])
