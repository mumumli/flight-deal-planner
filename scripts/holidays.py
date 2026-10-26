#!/usr/bin/env python3
"""Holiday calendar -> travel windows -> leave-optimised bridges.

Bundled calendars (see CALENDAR_META for provenance and confidence):

    SG  Singapore        official
    HK  Hong Kong        official (gazetted 2027 list)
    JP  Japan            rule-based
    AU  Australia        rule-based (national holidays only)
    US  United States    rule-based (federal holidays only)
    CN  mainland China   fixed dates only  -- lunar festivals NOT included
    KR  South Korea      fixed dates only  -- lunar festivals NOT included
    MY  Malaysia         fixed dates only  -- state + Islamic holidays NOT included

`confidence` is printed with the result. Anything below "official" means: check
the government calendar before you book a non-refundable fare. For full
coverage of a country not listed, pass `--file holidays.csv` (date,name rows).

Usage
-----
    python3 holidays.py --country SG --year 2027
    python3 holidays.py --country JP --year 2027 --max-leave 2 --json
    python3 holidays.py --file my-holidays.csv --year 2027
"""
import argparse
import json
from datetime import date, timedelta
from itertools import combinations

# --- helpers -----------------------------------------------------------------


def easter(year):
    """Anonymous Gregorian algorithm. Used for Good Friday / Easter Monday."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def nth_weekday(year, month, weekday, n):
    """n-th weekday of a month (n=1..5). weekday: Mon=0."""
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(days=7 * (n - 1))


def last_weekday(year, month, weekday):
    d = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def observed(d):
    """US-style: a Saturday holiday is observed Friday, Sunday -> Monday."""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


# --- calendar builders -------------------------------------------------------


def _hk(year):
    """Gazetted general holidays for 2027 (gov.hk). Other years: supply --file."""
    if year != 2027:
        return {}
    return {
        "2027-01-01": "The first day of January",
        "2027-02-06": "Lunar New Year's Day",
        "2027-02-08": "The third day of Lunar New Year",
        "2027-02-09": "The fourth day of Lunar New Year",
        "2027-03-26": "Good Friday",
        "2027-03-27": "The day following Good Friday",
        "2027-03-29": "Easter Monday",
        "2027-04-05": "Ching Ming Festival",
        "2027-05-01": "Labour Day",
        "2027-05-13": "The Birthday of the Buddha",
        "2027-06-09": "Tuen Ng Festival",
        "2027-07-01": "HKSAR Establishment Day",
        "2027-09-16": "Day following the Chinese Mid-Autumn Festival",
        "2027-10-01": "National Day",
        "2027-10-08": "Chung Yeung Festival",
        "2027-12-25": "Christmas Day",
        "2027-12-27": "The first weekday after Christmas Day",
    }


def _sg(year):
    if year == 2026:
        return {
            "2026-01-01": "New Year's Day", "2026-02-17": "Chinese New Year",
            "2026-02-18": "Chinese New Year (day 2)", "2026-03-21": "Hari Raya Puasa",
            "2026-04-03": "Good Friday", "2026-05-01": "Labour Day",
            "2026-05-27": "Hari Raya Haji", "2026-06-01": "Vesak Day (observed)",
            "2026-08-10": "National Day (observed)", "2026-11-09": "Deepavali (observed)",
            "2026-12-25": "Christmas Day",
        }
    if year == 2027:
        return {
            "2027-01-01": "New Year's Day", "2027-02-06": "Chinese New Year",
            "2027-02-07": "Chinese New Year (day 2)",
            "2027-02-08": "Chinese New Year (observed)",
            "2027-03-10": "Hari Raya Puasa", "2027-03-26": "Good Friday",
            "2027-05-01": "Labour Day", "2027-05-17": "Hari Raya Haji",
            "2027-05-20": "Vesak Day", "2027-08-09": "National Day",
            "2027-10-28": "Deepavali", "2027-12-25": "Christmas Day",
        }
    return {}


def _jp(year):
    """Cabinet Office rules. Equinox days are approximate to +/-1 day."""
    base = 20.8431 + 0.242194 * (year - 1980) - (year - 1980) // 4
    aut = 23.2488 + 0.242194 * (year - 1980) - (year - 1980) // 4
    vernal = date(year, 3, int(base))
    autumnal = date(year, 9, int(aut))
    d = {
        date(year, 1, 1): "New Year's Day",
        nth_weekday(year, 1, 0, 2): "Coming of Age Day",
        date(year, 2, 11): "National Foundation Day",
        date(year, 2, 23): "Emperor's Birthday",
        vernal: "Vernal Equinox Day",
        date(year, 4, 29): "Showa Day",
        date(year, 5, 3): "Constitution Memorial Day",
        date(year, 5, 4): "Greenery Day",
        date(year, 5, 5): "Children's Day",
        nth_weekday(year, 7, 0, 3): "Marine Day",
        date(year, 8, 11): "Mountain Day",
        nth_weekday(year, 9, 0, 3): "Respect for the Aged Day",
        autumnal: "Autumnal Equinox Day",
        nth_weekday(year, 10, 0, 2): "Sports Day",
        date(year, 11, 3): "Culture Day",
        date(year, 11, 23): "Labour Thanksgiving Day",
    }
    return {k.isoformat(): v for k, v in d.items()}


def _au(year):
    e = easter(year)
    d = {
        date(year, 1, 1): "New Year's Day",
        date(year, 1, 26): "Australia Day",
        e - timedelta(days=2): "Good Friday",
        e - timedelta(days=1): "Easter Saturday",
        e: "Easter Sunday",
        e + timedelta(days=1): "Easter Monday",
        date(year, 4, 25): "Anzac Day",
        nth_weekday(year, 6, 0, 2): "King's Birthday (national)",
        date(year, 12, 25): "Christmas Day",
        date(year, 12, 26): "Boxing Day",
    }
    return {k.isoformat(): v for k, v in d.items()}


def _us(year):
    d = {
        observed(date(year, 1, 1)): "New Year's Day",
        nth_weekday(year, 1, 0, 3): "Martin Luther King Jr. Day",
        nth_weekday(year, 2, 0, 3): "Washington's Birthday",
        last_weekday(year, 5, 0): "Memorial Day",
        observed(date(year, 6, 19)): "Juneteenth",
        observed(date(year, 7, 4)): "Independence Day",
        nth_weekday(year, 9, 0, 1): "Labor Day",
        nth_weekday(year, 10, 0, 2): "Columbus Day",
        observed(date(year, 11, 11)): "Veterans Day",
        nth_weekday(year, 11, 3, 4): "Thanksgiving",
        observed(date(year, 12, 25)): "Christmas Day",
    }
    return {k.isoformat(): v for k, v in d.items()}


def _cn(year):
    """Fixed-date mainland holidays only. Lunar festivals are NOT included."""
    d = {date(year, 1, 1): "New Year's Day", date(year, 5, 1): "Labour Day",
         date(year, 10, 1): "National Day"}
    d[date(year, 4, 5)] = "Qingming Festival"
    return {k.isoformat(): v for k, v in d.items()}


def _kr(year):
    """Fixed-date Korean holidays only. Seollal / Chuseok NOT included."""
    d = {date(year, 1, 1): "New Year's Day",
         date(year, 3, 1): "Independence Movement Day",
         date(year, 5, 5): "Children's Day", date(year, 6, 6): "Memorial Day",
         date(year, 8, 15): "Liberation Day",
         date(year, 10, 3): "National Foundation Day",
         date(year, 10, 9): "Hangul Day", date(year, 12, 25): "Christmas Day"}
    return {k.isoformat(): v for k, v in d.items()}


def _my(year):
    """Fixed-date Malaysian holidays only. State / Islamic holidays NOT included."""
    d = {date(year, 1, 1): "New Year's Day", date(year, 5, 1): "Labour Day",
         date(year, 8, 31): "National Day", date(year, 9, 16): "Malaysia Day",
         date(year, 12, 25): "Christmas Day"}
    return {k.isoformat(): v for k, v in d.items()}


BUILDERS = {"SG": _sg, "HK": _hk, "JP": _jp, "AU": _au, "US": _us,
            "CN": _cn, "KR": _kr, "MY": _my}

CALENDAR_META = {
    "SG": ("official", "Ministry of Manpower, Public Holidays"),
    "HK": ("official", "gov.hk gazetted general holidays 2027"),
    "JP": ("rule-based", "Cabinet Office holiday law; equinox dates +/-1 day"),
    "AU": ("rule-based", "national holidays only; state variations not modelled"),
    "US": ("rule-based", "federal holidays only, with observed-day shifting"),
    "CN": ("fixed-dates-only", "lunar festivals omitted; State Council gives real breaks"),
    "KR": ("fixed-dates-only", "Seollal and Chuseok omitted"),
    "MY": ("fixed-dates-only", "state and Islamic holidays omitted"),
}


def build(country, year):
    c = country.upper()
    fn = BUILDERS.get(c)
    if not fn:
        return {}
    return {date.fromisoformat(k): v for k, v in fn(year).items()}


# --- window analysis ---------------------------------------------------------


def is_off(d, hol):
    return d.weekday() >= 5 or d in hol


def block_for(year, hol, extra, anchor):
    """The contiguous non-working block containing `anchor`."""
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


def runs(year, hol):
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


def optimise(year, hol, max_leave=3):
    out, seen = [], set()
    for a in sorted(hol):
        row = {"holiday": hol[a], "date": str(a), "weekday": a.strftime("%a"),
               "options": []}
        b0 = block_for(year, hol, [], a)
        row["options"].append({"leave_days": 0, "days_off": b0[2],
                               "start": str(b0[0]), "end": str(b0[1]), "leave": []})
        cand = [a + timedelta(days=k) for k in range(-7, 8)
                if not is_off(a + timedelta(days=k), hol)]
        for k in range(1, max_leave + 1):
            best = None
            for combo in combinations(cand, k):
                n = block_for(year, hol, combo, a)[2]
                if best is None or n > best[0]:
                    best = (n, combo)
            if not best:
                continue
            span = block_for(year, hol, best[1], a)
            row["options"].append({
                "leave_days": k, "days_off": best[0],
                "start": str(span[0]), "end": str(span[1]),
                "leave": [str(x) for x in sorted(best[1])],
                "efficiency": round(best[0] / k, 2),
            })
        sig = tuple((o["leave_days"], o["start"], o["end"]) for o in row["options"][1:])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(row)
    return out


def windows(country, year, max_leave=3):
    """Flat list of usable travel windows, ready to feed the scanner."""
    hol = build(country, year)
    res = []
    for r in optimise(year, hol, max_leave):
        for o in r["options"]:
            if o["days_off"] < 3:
                continue
            res.append({
                "label": f"{r['date'][5:7]}{r['date'][8:10]}L{o['leave_days']}",
                "holiday": r["holiday"], "leave_days": o["leave_days"],
                "days_off": o["days_off"], "start": o["start"], "end": o["end"],
                "efficiency": o.get("efficiency"),
            })
    return res


def load_file(path):
    hol = {}
    for i, line in enumerate(open(path, encoding="utf-8")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if i == 0 and not parts[0][:4].isdigit():
            continue
        hol[date.fromisoformat(parts[0])] = parts[1] if len(parts) > 1 else "holiday"
    return hol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="SG")
    ap.add_argument("--year", type=int, default=2027)
    ap.add_argument("--file")
    ap.add_argument("--max-leave", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.file:
        hol, conf, src = load_file(a.file), "user-supplied", a.file
    else:
        hol = build(a.country, a.year)
        conf, src = CALENDAR_META.get(a.country.upper(), ("unknown", "n/a"))
    if not hol:
        raise SystemExit(f"no calendar for {a.country} {a.year}; pass --file")

    res = optimise(a.year, hol, a.max_leave)
    if a.json:
        print(json.dumps({"country": a.country.upper(), "year": a.year,
                          "confidence": conf, "source": src, "windows": res},
                         ensure_ascii=False, indent=2))
        return

    print(f"\n{a.country.upper()} {a.year}   confidence={conf}   source={src}")
    if conf != "official":
        print("  !! verify against the government calendar before booking")

    print("\nnatural long weekends")
    for b in runs(a.year, hol):
        if len(b) >= 3:
            print(f"  {b[0]} ({b[0]:%a}) -> {b[-1]} ({b[-1]:%a})  {len(b)}d")

    print("\nwhat each day of leave buys")
    for r in res:
        if r["options"][0]["days_off"] < 2:
            continue
        print(f"\n  anchor {r['date']} ({r['weekday']}) {r['holiday']}")
        for o in r["options"][1:]:
            print(f"    {o['leave_days']}d leave -> {o['days_off']}d off "
                  f"({o['start']} .. {o['end']})  eff {o['efficiency']}x")


if __name__ == "__main__":
    main()
