#!/usr/bin/env python3
"""Holiday calendar -> trip shapes -> leave-costed date pairs.

Two things this module deliberately does NOT do the naive way:

1. **Substitute days are derived by rule, not hard-coded.** Feed it the dates the
   government gazetted and it applies the country's rule:
       SG  a Sunday holiday moves to Monday; a Saturday holiday does NOT move
       HK  the gazette already lists substitutes, so none are applied
       US  a Saturday holiday moves to Friday, a Sunday one to Monday
       CN  no automatic substitute -- 调休 is announced separately and is
           supplied as *make-up workdays* (weekends that become working days)

2. **A "window" is not fixed in advance.** For each holiday the module
   enumerates the date pairs you could actually fly -- leave the day before,
   the day after, both, neither -- and costs each one in annual-leave days.
   Choosing between them is then a question of fare, not of habit.

Usage
-----
    python3 holidays.py --country SG --year 2027
    python3 holidays.py --country SG --year 2027 --max-leave 2 --json
    python3 holidays.py --file my-holidays.csv --year 2027
"""
import argparse
import json
from datetime import date, timedelta
from itertools import combinations

# --- date helpers ------------------------------------------------------------


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
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(days=7 * (n - 1))


def last_weekday(year, month, weekday):
    d = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


# --- substitute-day rules ----------------------------------------------------


def substitute_sun_to_mon(days):
    """SG / MY: a Sunday holiday moves to Monday. A Saturday one does not move."""
    out = dict(days)
    for d, name in list(days.items()):
        if d.weekday() == 6:
            out.setdefault(d + timedelta(days=1), f"{name} (observed)")
    return out


def substitute_us(days):
    """US: Saturday -> Friday, Sunday -> Monday."""
    out = {}
    for d, name in days.items():
        if d.weekday() == 5:
            out[d - timedelta(days=1)] = f"{name} (observed)"
        elif d.weekday() == 6:
            out[d + timedelta(days=1)] = f"{name} (observed)"
        out.setdefault(d, name)
    return out


# --- base calendars (gazetted dates BEFORE substitution where a rule exists) --


def _sg_raw(year):
    """Singapore MOM dates as gazetted; substitutes are applied by rule."""
    if year == 2026:
        return {date(2026, 1, 1): "New Year's Day",
                date(2026, 2, 17): "Chinese New Year",
                date(2026, 2, 18): "Chinese New Year",
                date(2026, 3, 21): "Hari Raya Puasa",
                date(2026, 4, 3): "Good Friday", date(2026, 5, 1): "Labour Day",
                date(2026, 5, 27): "Hari Raya Haji", date(2026, 5, 31): "Vesak Day",
                date(2026, 8, 9): "National Day", date(2026, 11, 8): "Deepavali",
                date(2026, 12, 25): "Christmas Day"}
    if year == 2027:
        return {date(2027, 1, 1): "New Year's Day",
                date(2027, 2, 6): "Chinese New Year",
                date(2027, 2, 7): "Chinese New Year",
                date(2027, 3, 10): "Hari Raya Puasa",
                date(2027, 3, 26): "Good Friday", date(2027, 5, 1): "Labour Day",
                date(2027, 5, 17): "Hari Raya Haji", date(2027, 5, 20): "Vesak Day",
                date(2027, 8, 9): "National Day", date(2027, 10, 28): "Deepavali",
                date(2027, 12, 25): "Christmas Day"}
    return {}


def _hk_raw(year):
    """HK 2027: the gazette already lists substitutes, so no rule is applied."""
    if year != 2027:
        return {}
    return {date(2027, 1, 1): "The first day of January",
            date(2027, 2, 6): "Lunar New Year's Day",
            date(2027, 2, 8): "The third day of Lunar New Year",
            date(2027, 2, 9): "The fourth day of Lunar New Year",
            date(2027, 3, 26): "Good Friday",
            date(2027, 3, 27): "The day following Good Friday",
            date(2027, 3, 29): "Easter Monday",
            date(2027, 4, 5): "Ching Ming Festival", date(2027, 5, 1): "Labour Day",
            date(2027, 5, 13): "The Birthday of the Buddha",
            date(2027, 6, 9): "Tuen Ng Festival",
            date(2027, 7, 1): "HKSAR Establishment Day",
            date(2027, 9, 16): "Day following Mid-Autumn Festival",
            date(2027, 10, 1): "National Day",
            date(2027, 10, 8): "Chung Yeung Festival",
            date(2027, 12, 25): "Christmas Day",
            date(2027, 12, 27): "The first weekday after Christmas Day"}


def _jp(year):
    base = 20.8431 + 0.242194 * (year - 1980) - (year - 1980) // 4
    aut = 23.2488 + 0.242194 * (year - 1980) - (year - 1980) // 4
    return {date(year, 1, 1): "New Year's Day",
            nth_weekday(year, 1, 0, 2): "Coming of Age Day",
            date(year, 2, 11): "National Foundation Day",
            date(year, 2, 23): "Emperor's Birthday",
            date(year, 3, int(base)): "Vernal Equinox Day",
            date(year, 4, 29): "Showa Day",
            date(year, 5, 3): "Constitution Memorial Day",
            date(year, 5, 4): "Greenery Day", date(year, 5, 5): "Children's Day",
            nth_weekday(year, 7, 0, 3): "Marine Day",
            date(year, 8, 11): "Mountain Day",
            nth_weekday(year, 9, 0, 3): "Respect for the Aged Day",
            date(year, 9, int(aut)): "Autumnal Equinox Day",
            nth_weekday(year, 10, 0, 2): "Sports Day",
            date(year, 11, 3): "Culture Day",
            date(year, 11, 23): "Labour Thanksgiving Day"}


def _au(year):
    e = easter(year)
    d = {date(year, 1, 1): "New Year's Day", date(year, 1, 26): "Australia Day",
         e - timedelta(days=2): "Good Friday",
         e - timedelta(days=1): "Easter Saturday", e: "Easter Sunday",
         e + timedelta(days=1): "Easter Monday", date(year, 4, 25): "Anzac Day",
         nth_weekday(year, 6, 0, 2): "King's Birthday (national)",
         date(year, 12, 25): "Christmas Day", date(year, 12, 26): "Boxing Day"}
    out = dict(d)
    for k in (date(year, 1, 26), date(year, 4, 25)):
        if k.weekday() >= 5:
            out.setdefault(k + timedelta(days=(7 - k.weekday()) % 7),
                           f"{d[k]} (observed)")
    return out


def _us(year):
    return {date(year, 1, 1): "New Year's Day",
            nth_weekday(year, 1, 0, 3): "Martin Luther King Jr. Day",
            nth_weekday(year, 2, 0, 3): "Washington's Birthday",
            last_weekday(year, 5, 0): "Memorial Day",
            date(year, 6, 19): "Juneteenth",
            date(year, 7, 4): "Independence Day",
            nth_weekday(year, 9, 0, 1): "Labor Day",
            nth_weekday(year, 10, 0, 2): "Columbus Day",
            date(year, 11, 11): "Veterans Day",
            nth_weekday(year, 11, 3, 4): "Thanksgiving",
            date(year, 12, 25): "Christmas Day"}


def _cn(year):
    """Fixed-date only. 调休 is announced separately -- pass make-up workdays."""
    return {date(year, 1, 1): "New Year's Day",
            date(year, 4, 5): "Qingming Festival",
            date(year, 5, 1): "Labour Day",
            date(year, 10, 1): "National Day"}


def _kr(year):
    return {date(year, 1, 1): "New Year's Day",
            date(year, 3, 1): "Independence Movement Day",
            date(year, 5, 5): "Children's Day", date(year, 6, 6): "Memorial Day",
            date(year, 8, 15): "Liberation Day",
            date(year, 10, 3): "National Foundation Day",
            date(year, 10, 9): "Hangul Day", date(year, 12, 25): "Christmas Day"}


def _my(year):
    return {date(year, 1, 1): "New Year's Day", date(year, 5, 1): "Labour Day",
            date(year, 8, 31): "National Day", date(year, 9, 16): "Malaysia Day",
            date(year, 12, 25): "Christmas Day"}


CALENDARS = {
    # code: (builder, substitute-rule, confidence, source)
    "SG": (_sg_raw, substitute_sun_to_mon, "official",
           "MOM; Sunday->Monday substitute applied by rule, Saturday not moved"),
    "HK": (_hk_raw, None, "official", "gov.hk gazetted list for 2027"),
    "JP": (_jp, None, "rule-based",
           "Cabinet Office holiday law; equinox dates +/-1 day"),
    "AU": (_au, None, "rule-based", "national holidays only; state variations not modelled"),
    "US": (_us, substitute_us, "rule-based", "federal holidays with observed-day shifting"),
    "CN": (_cn, None, "fixed-dates-only",
           "lunar festivals omitted; 调休 supplied as make-up workdays"),
    "KR": (_kr, None, "fixed-dates-only", "Seollal and Chuseok omitted"),
    "MY": (_my, substitute_sun_to_mon, "fixed-dates-only",
           "state and Islamic holidays omitted"),
}


def build(country, year, workdays=None):
    """Return (holidays, workdays, confidence, source)."""
    c = country.upper()
    fn, rule, conf, src = CALENDARS.get(c, (None, None, "unknown", "n/a"))
    if fn is None:
        return {}, set(), conf, src
    raw = fn(year)
    days = rule(raw) if rule else raw
    return days, set(workdays or ()), conf, src


# --- off-day logic -----------------------------------------------------------


def make_is_off(holidays, workdays):
    """Off when it is a weekend (unless a make-up workday) or a holiday."""
    def is_off(d):
        if d in workdays:
            return False
        return d.weekday() >= 5 or d in holidays
    return is_off


def runs(year, holidays, workdays):
    is_off = make_is_off(holidays, workdays)
    out, cur = [], []
    d = date(year, 1, 1)
    while d.year == year:
        if is_off(d):
            cur.append(d)
        elif cur:
            out.append(cur)
            cur = []
        d += timedelta(days=1)
    if cur:
        out.append(cur)
    return out


# --- trip shapes -------------------------------------------------------------


def _workdays_between(a, b, is_off):
    out, d = [], a
    while d <= b:
        if not is_off(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _clusters(blocks, gap=6):
    """Merge holiday blocks that sit close enough to bridge with one leave run.

    Singapore's May 2027 is the case that matters: Hari Raya Haji (Mon 17) and
    Vesak Day (Thu 20) are three working days apart, so 3 days of leave buys a
    single 9-night trip. Enumerating each block separately would never find it.
    """
    out = []
    for b in blocks:
        if out and (b[0] - out[-1][-1]).days <= gap:
            out[-1] = out[-1] + b
        else:
            out.append(list(b))
    return out


def shapes_from(holidays, workdays, year, max_leave=3, per_holiday=8, max_nights=21,
                include_weekends=False):
    """Enumerate flyable date pairs around every holiday cluster, costed in leave."""
    is_off = make_is_off(holidays, workdays)
    blocks = [b for b in runs(year, holidays, workdays)
              if any(d in holidays for d in b) or include_weekends]
    out_shapes, seen = [], set()

    # Each cluster yields both the long bridged shape and the short shape of
    # every individual block inside it -- "just the Monday off" and "the whole
    # nine days" are both real options and must be compared on price.
    spans, seen_spans = [], set()
    for cl in _clusters(blocks):
        names = [holidays[d].replace(" (observed)", "") for d in cl if d in holidays]
        cname = " + ".join(dict.fromkeys(names)) if names else "weekend"
        spans.append((cl[0], cl[-1], cname, len(cl)))
        for b in _clusters(blocks, gap=0):
            if b[0] >= cl[0] and b[-1] <= cl[-1]:
                bname = next((holidays[d].replace(" (observed)", "")
                              for d in b if d in holidays), cname)
                spans.append((b[0], b[-1], bname, len(b)))

    for start, end, name, ndays in spans:
        if (start, end) in seen_spans:
            continue
        seen_spans.add((start, end))
        for pre in (2, 1, 0):
            for post in (0, 1, 2, 3):
                o = start - timedelta(days=pre)
                r = end + timedelta(days=post)
                nights = (r - o).days
                if nights < 1 or nights > max_nights:
                    continue
                lv = _workdays_between(o, r, is_off)
                if len(lv) > max_leave or (o, r) in seen:
                    continue
                seen.add((o, r))
                out_shapes.append({
                    "holiday": name, "anchor": str(start),
                    "out": str(o), "ret": str(r), "nights": nights,
                    "leave_days": len(lv),
                    "leave": [str(x) for x in lv],
                    "days_off": ndays,
                    "label": f"{start:%m%d}·{o:%a}\u2192{r:%a}",
                    "efficiency": round(nights / max(len(lv), 1), 2),
                })

    # keep a spread across leave costs, not just the cheapest: the whole point
    # is to compare "1 day more leave, how much cheaper" later.
    by_anchor = {}
    for sh in out_shapes:
        by_anchor.setdefault(sh["anchor"], []).append(sh)
    kept = []
    for anchor, ss in by_anchor.items():
        per_level = {}
        for sh in ss:
            per_level.setdefault(sh["leave_days"], []).append(sh)
        picked = []
        for lvl, group in sorted(per_level.items()):
            group.sort(key=lambda x: -x["nights"])
            picked.extend(group[:2])
        picked.sort(key=lambda x: (x["leave_days"], -x["nights"]))
        kept.extend(picked[:per_holiday])
    kept.sort(key=lambda x: (x["out"], x["leave_days"]))
    return kept


def shapes(country, year, max_leave=3, per_holiday=6, include_weekends=False):
    holidays, workdays, conf, src = build(country, year)
    if not holidays:
        return [], conf, src
    return shapes_from(holidays, workdays, year, max_leave, per_holiday,
                       include_weekends=include_weekends), conf, src


# --- bridge table (kept for the CLI) -----------------------------------------


def optimise(country, year, max_leave=3):
    holidays, workdays, conf, src = build(country, year)
    is_off = make_is_off(holidays, workdays)

    def block_for(anchor, extra):
        s = set(extra)
        lo, hi = date(year, 1, 1), date(year, 12, 31)
        st = anchor
        while st - timedelta(days=1) >= lo and (
                is_off(st - timedelta(days=1)) or (st - timedelta(days=1)) in s):
            st -= timedelta(days=1)
        en = anchor
        while en + timedelta(days=1) <= hi and (
                is_off(en + timedelta(days=1)) or (en + timedelta(days=1)) in s):
            en += timedelta(days=1)
        return st, en, (en - st).days + 1

    out, seen = [], set()
    for a in sorted(holidays):
        row = {"holiday": holidays[a], "date": str(a), "weekday": a.strftime("%a"),
               "options": []}
        b0 = block_for(a, [])
        row["options"].append({"leave_days": 0, "days_off": b0[2],
                               "start": str(b0[0]), "end": str(b0[1]), "leave": []})
        cand = [a + timedelta(days=k) for k in range(-7, 8) if not is_off(a + timedelta(days=k))]
        for k in range(1, max_leave + 1):
            best = None
            for combo in combinations(cand, k):
                n = block_for(a, combo)[2]
                if best is None or n > best[0]:
                    best = (n, combo)
            if not best:
                continue
            span = block_for(a, best[1])
            row["options"].append({
                "leave_days": k, "days_off": best[0],
                "start": str(span[0]), "end": str(span[1]),
                "leave": [str(x) for x in sorted(best[1])],
                "efficiency": round(best[0] / k, 2)})
        sig = tuple((o["leave_days"], o["start"], o["end"]) for o in row["options"][1:])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(row)
    return out, conf, src


def parse_holiday_file(path):
    """CSV: `date,name` or `date,name,work` for a make-up working day."""
    holidays, workdays = {}, set()
    for i, line in enumerate(open(path, encoding="utf-8")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if i == 0 and not parts[0][:4].isdigit():
            continue
        d = date.fromisoformat(parts[0])
        flags = ",".join(parts[2:]).lower()
        if "work" in flags:
            workdays.add(d)
        else:
            holidays[d] = parts[1] if len(parts) > 1 else "holiday"
    return holidays, workdays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="SG")
    ap.add_argument("--year", type=int, default=2027)
    ap.add_argument("--file")
    ap.add_argument("--max-leave", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--weekends", action="store_true",
                    help="also emit ordinary weekends (weekend-warrior mode)")
    a = ap.parse_args()

    if a.file:
        hol, work = parse_holiday_file(a.file)
        conf, src = "user-supplied", a.file
        shp = shapes_from(hol, work, a.year, a.max_leave,
                          include_weekends=a.weekends)
    else:
        shp, conf, src = shapes(a.country, a.year, a.max_leave,
                                include_weekends=a.weekends)

    if a.json:
        print(json.dumps({"country": a.country.upper(), "year": a.year,
                          "confidence": conf, "source": src, "shapes": shp},
                         ensure_ascii=False, indent=2))
        return

    print(f"\n{a.country.upper()} {a.year}   confidence={conf}   {src}")
    if conf != "official":
        print("  !! verify against the government calendar before booking")
    print("\ntrip shapes — pick on price, not habit")
    cur = None
    for s in shp:
        if s["anchor"] != cur:
            cur = s["anchor"]
            print(f"\n  {s['holiday']}  ({cur})")
        lv = ", ".join(s["leave"]) or "none"
        print(f"    {s['out']} → {s['ret']}  {s['nights']}n  leave {s['leave_days']}d"
              f" [{lv}]  eff {s['efficiency']}x")


if __name__ == "__main__":
    main()
