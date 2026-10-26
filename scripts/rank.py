#!/usr/bin/env python3
"""Rank scanned fares and emit a decision-ready summary.

Reads the JSONL produced by scan.py plus a config that describes each
destination (display name, flight hours, whether it works as a weekend hop or
only on a long holiday, and the baggage rules of the carriers involved).

Config
------
{
  "home": "SIN",
  "currency": "SGD",
  "today": "2026-10-26",
  "near_days": 64,
  "destinations": {
    "DPS": {"name": "Bali", "hours": 2.6, "scope": "short", "visa": "VOA ~USD 35"},
    "NRT": {"name": "Tokyo", "hours": 7.0, "scope": "long",  "visa": "visa-free for X"}
  },
  "baggage": {
    "Scoot": {"tier": "low-cost", "cabin": "10kg, 2 pieces", "checked": "none", "add20": 38},
    "Singapore Airlines": {"tier": "full-service", "cabin": "7kg", "checked": "30kg included", "add20": 0}
  },
  "long_windows": ["MAY", "MAY6", "HRP", "CNY"],
  "exclude": {"destinations": [], "windows": []}
}

Usage
-----
    python3 rank.py --fares data/fares.jsonl --config config.json --out data/summary.json
"""
import argparse
import json
import re
import statistics as st
from datetime import date, datetime
from collections import Counter

DEFAULT_BAG = {"tier": "unknown", "cabin": "not confirmed", "checked": "verify", "add20": 35}


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def hour(t):
    m = re.match(r"(\d{1,2}):(\d{2})\s*([AP]M)", t or "")
    if not m:
        return None
    h, mi, ap = int(m.group(1)) % 12, int(m.group(2)), m.group(3)
    return h + mi / 60 + (12 if ap == "PM" else 0)


def dur_min(d):
    hh = re.search(r"(\d+)\s*hr", d or "")
    mm = re.search(r"(\d+)\s*min", d or "")
    return (int(hh.group(1)) * 60 if hh else 0) + (int(mm.group(1)) if mm else 0)


def choose(rows, scope, dur_cap=None):
    """Pick one itinerary per cell.

    Short trips: prefer nonstop, and a genuine evening departure if it is
    within 12% of the cheapest nonstop.
    Long trips: nonstop first, else one stop inside the route's duration cap.
    """
    nonstop = [x for x in rows if x["stops"] == "0"]
    if scope == "long":
        cap = dur_cap or 720
        ok = nonstop or [x for x in rows
                         if x["stops"] == "1 stop" and dur_min(x["dur"]) <= cap]
        if ok:
            return min(ok, key=lambda x: x["price"])
        return min(rows, key=lambda x: (dur_min(x["dur"]), x["price"]))
    pool = nonstop or rows
    best = min(pool, key=lambda x: x["price"])
    eve = [x for x in pool if (hour(x["dep"]) or 0) >= 17]
    if eve:
        ev = min(eve, key=lambda x: x["price"])
        if ev["price"] <= best["price"] * 1.12:
            return ev
    return best


def rank(fares_path, cfg):
    """Score a fares JSONL against a config dict. Returns (items, stats)."""
    meta = cfg["destinations"]
    bags = cfg.get("baggage", {})
    long_windows = set(cfg.get("long_windows", []))
    exclude_d = set(cfg.get("exclude", {}).get("destinations", []))
    exclude_w = set(cfg.get("exclude", {}).get("windows", []))
    today = parse_date(cfg.get("today", date.today().isoformat()))
    near = int(cfg.get("near_days", 64))

    raw = [json.loads(l) for l in open(fares_path, encoding="utf-8")]
    raw = [r for r in raw if r.get("rows")]

    cells = []
    for r in raw:
        dst = r["to"]
        if dst not in meta:
            continue
        m = meta[dst]
        scope = m.get("scope", "short")
        pick = choose(r["rows"], scope, m.get("dur_cap"))
        h = hour(pick["dep"]) or 0
        nights = (parse_date(r["ret"]) - parse_date(r["out"])).days if r.get("ret") else 0
        cells.append({
            "dest": dst, "name": m.get("name", dst), "country": m.get("country", ""),
            "visa": m.get("visa", ""), "hours": m.get("hours", 0), "scope": scope,
            "label": r["label"], "kind": r.get("kind", ""),
            "out": r["out"], "ret": r.get("ret"), "nights": nights,
            "days_out": (parse_date(r["out"]) - today).days,
            "price": pick["price"], "air": pick["air"], "dep": pick["dep"],
            "arr": pick["arr"], "plus": pick["plus"], "stops": pick["stops"],
            "dur": pick["dur"], "red_eye": bool(pick["plus"]),
            "hour": h, "url": r.get("url", ""), "n_rows": r["n"],
        })

    by_route = {}
    for c in cells:
        by_route.setdefault(c["dest"], []).append(c)

    stats = {}
    for dst, cs in by_route.items():
        base = [c["price"] for c in cs
                if c["scope"] == "long" or c["nights"] <= 3] or [c["price"] for c in cs]
        stats[dst] = {"median": st.median(base), "min": min(base),
                      "max": max(base), "n": len(base)}
        for c in cs:
            ranked = c["scope"] == "long" or c["nights"] <= 3
            if not ranked:
                c["rank"] = c["vs_median"] = None
            else:
                c["rank"] = 1 + sum(1 for p in base if p < c["price"])
                c["vs_median"] = round((c["price"] / stats[dst]["median"] - 1) * 100)

    items = []
    for c in cells:
        b = dict(bags.get(c["air"], DEFAULT_BAG))
        excluded = c["dest"] in exclude_d or c["label"] in exclude_w
        total = c["price"] + b.get("add20", 0)
        v = c["vs_median"]
        if excluded:
            pri = "skip"
        elif c["scope"] == "long":
            pri = "green" if (v is None or v <= 8) else "grey"
        elif c["days_out"] <= near:
            ok = (c["nights"] <= 3 and (c["rank"] or 99) <= 3
                  and not c["red_eye"] and c["hour"] >= 15)
            pri = "red" if ok else "amber"
        elif c["label"] in long_windows:
            pri = "green" if (v is None or v <= 5) else "grey"
        else:
            pri = "amber" if (v is not None and v <= -5) else "grey"

        items.append({
            **{k: c[k] for k in ("dest", "name", "country", "visa", "hours", "scope",
                                 "label", "kind", "out", "ret", "nights", "days_out",
                                 "price", "air", "dep", "arr", "plus", "stops",
                                 "dur", "red_eye", "url")},
            "bag": b, "price_with_bag": total,
            "per_night": round(total / max(c["nights"], 1)),
            "rank": c["rank"], "n_windows": stats[c["dest"]]["n"],
            "median": stats[c["dest"]]["median"], "vs_median": v,
            "priority": pri, "n_rows": c["n_rows"],
            "confidence": "high" if c["n_rows"] >= 5 else "low",
        })

    order = {"red": 0, "green": 1, "amber": 2, "grey": 3, "skip": 9}
    items.sort(key=lambda x: (order[x["priority"]], x["per_night"]))
    return items, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fares", default="data/fares.jsonl")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="data/summary.json")
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    items, stats = rank(a.fares, cfg)
    json.dump({"generated": cfg.get("today", ""), "items": items,
               "route_stats": stats},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"cells={len(items)}", Counter(i["priority"] for i in items))
    print("\ncheapest per night, per window:")
    for lbl in sorted({i["label"] for i in items if i["priority"] != "skip"}):
        best = sorted([i for i in items if i["label"] == lbl and i["priority"] != "skip"],
                      key=lambda x: x["per_night"])[:3]
        for b in best:
            print(f"  {lbl:6} {b['name'][:16]:16} {b['price']:>6} {b['air'][:18]:18} "
                  f"{b['nights']}n  per-night {b['per_night']:>5}  {b['priority']}")


if __name__ == "__main__":
    main()
