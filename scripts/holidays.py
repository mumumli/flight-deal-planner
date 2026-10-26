#!/usr/bin/env python3
"""Holiday calendar -> travel windows -> leave-optimised bridges.

Generic: feed it any country's public-holiday list for any year and it will
work out which days off actually form long weekends, and what each extra day
of annual leave buys you.

Usage
-----
    python3 holidays.py --country SG --year 2027
    python3 holidays.py --country SG --year 2027 --max-leave 3 --json
    python3 holidays.py --file my-holidays.csv --year 2027   # date,name rows

The bundled table only covers Singapore 2026-2027; for other countries pass
`--file`. Always confirm against the official source before booking anything.
"""
import argparse
import json
from datetime import date, timedelta
from itertools import combinations

# --- bundled calendars (extend or override via --file) -----------------------
SG = {
    2026: {
        "2026-01-01": "New Year's Day",
        "2026-02-17": "Chinese New Year",
        "2026-02-18": "Chinese New Year (day 2)",
        "2026-03-21": "Hari Raya Puasa",
        "2026-04-03": "Good Friday",
        "2026-05-01": "Labour Day",
        "2026-05-27": "Hari Raya Haji",
        "2026-06-01": "Vesak Day (observed)",
        "2026-08-10": "National Day (observed)",
        "2026-11-09": "Deepavali (observed)",
        "2026-12-25": "Christmas Day",
    },
    2027: {
        "2027-01-01": "New Year's Day",
        "2027-02-06": "Chinese New Year",
        "2027-02-07": "Chinese New Year (day 2)",
        "2027-02-08": "Chinese New Year (observed)",
        "2027-03-10": "Hari Raya Puasa",
        "2027-03-26": "Good Friday",
        "2027-05-01": "Labour Day",
        "2027-05-17": "Hari Raya Haji",
        "2027-05-20": "Vesak Day",
        "2027-08-09": "National Day",
        "2027-10-28": "Deepavali",
        "2027-12-25": "Christmas Day",
    },
}
CALENDARS = {"SG": SG}


def is_off(d, hol):
    return d.weekday() >= 5 or d in hol


def runs(year, hol):
    """Contiguous blocks of non-working days."""
    out, cur = [], []
    d = date(year, 1, 1)
    while d.year == year:
        if is_off(d, hol):
            cur.append(d)
        elif cur:
            out.append(cur)
            cur = []
        d += timedelta(days=1)
    if cur:
        out.append(cur)
    return out


def block_for(year, hol, extra, anchor):
    """The contiguous block containing `anchor`, given `extra` leave days.

    Anchored on purpose: leave should extend the holiday you are targeting,
    not buy you a block somewhere else in the year.
    """
    s = set(extra)
    lo, hi = date(year, 1, 1), date(year, 12, 31)
    start = anchor
    while start - timedelta(days=1) >= lo and (
            is_off(start - timedelta(days=1), hol) or (start - timedelta(days=1)) in s):
        start -= timedelta(days=1)
    end = anchor
    while end + timedelta(days=1) <= hi and (
            is_off(end + timedelta(days=1), hol) or (end + timedelta(days=1)) in s):
        end += timedelta(days=1)
    return start, end, (end - start).days + 1


def optimise(year, hol, max_leave=3):
    """For each anchor holiday, what does 0..max_leave days of leave buy?"""
    anchors = sorted(hol)
    out, seen = [], set()
    for a in anchors:
        row = {"holiday": hol.get(a, "weekend"), "date": str(a),
               "weekday": a.strftime("%a"), "options": []}
        cand = [a + timedelta(days=k) for k in range(-7, 8)
                if not is_off(a + timedelta(days=k), hol)]
        b0 = block_for(year, hol, [], a)
        row["options"].append({"leave_days": 0, "days_off": b0[2],
                               "start": str(b0[0]), "end": str(b0[1]), "leave": []})
        for k in range(1, max_leave + 1):
            best = None
            for combo in combinations(cand, k):
                span_len = block_for(year, hol, combo, a)[2]
                if best is None or span_len > best[0]:
                    best = (span_len, combo)
            if best:
                span = block_for(year, hol, best[1], a)
                row["options"].append({
                    "leave_days": k, "days_off": best[0],
                    "leave": [str(x) for x in sorted(best[1])],
                    "start": str(span[0]), "end": str(span[1]),
                    # leave efficiency: how many days off per annual-leave day
                    "efficiency": round(best[0] / k, 2),
                })
        # one row per distinct set of windows, not per calendar day
        sig = tuple((o["leave_days"], o["start"], o["end"]) for o in row["options"][1:])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(row)
    return out


def load_file(path):
    hol = {}
    for i, line in enumerate(open(path, encoding="utf-8")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if i == 0 and not parts[0][:4].isdigit():
            continue  # header
        hol[date.fromisoformat(parts[0])] = parts[1] if len(parts) > 1 else "holiday"
    return hol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="SG")
    ap.add_argument("--year", type=int, default=2027)
    ap.add_argument("--file", help="CSV of date,name instead of the bundled table")
    ap.add_argument("--max-leave", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.file:
        hol = load_file(a.file)
    else:
        raw = CALENDARS.get(a.country, {}).get(a.year)
        if not raw:
            raise SystemExit(f"no bundled calendar for {a.country} {a.year}; pass --file")
        hol = {date.fromisoformat(k): v for k, v in raw.items()}

    res = optimise(a.year, hol, a.max_leave)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    print(f"\n{a.country} {a.year} — natural long weekends")
    for b in runs(a.year, hol):
        if len(b) >= 3:
            names = [hol[x] for x in b if x in hol]
            print(f"  {b[0]} ({b[0]:%a}) -> {b[-1]} ({b[-1]:%a})  {len(b)}d  {names}")

    print(f"\n{a.country} {a.year} — what each day of leave buys")
    for r in res:
        if r["options"][0]["days_off"] < 2:
            continue
        print(f"\n  anchor {r['date']} ({r['weekday']}) {r['holiday']}")
        for o in r["options"][1:]:
            print(f"    {o['leave_days']}d leave -> {o['days_off']}d off "
                  f"({o['start']} .. {o['end']})  efficiency {o['efficiency']}x  "
                  f"leave {o['leave']}")


if __name__ == "__main__":
    main()
