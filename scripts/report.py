#!/usr/bin/env python3
"""Turn data/summary.json into a Markdown brief.

The script lays out the facts — dates, fares, baggage, per-night cost, route
percentile — grouped by travel window. The narrative (why this destination,
what to do there) is written by the agent on top of this skeleton, because
that part needs the seasonality and visa reasoning in references/, not a
formula.

Usage
-----
    python3 report.py --summary data/summary.json --out report.md [--top 6]
"""
import argparse
import json
from collections import defaultdict

TIER = {"low-cost": "LC", "full-service": "FS", "unknown": "?"}


def money(cur, v):
    return f"{cur}{v:,}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="data/summary.json")
    ap.add_argument("--out", default="report.md")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--currency", default="S$")
    ap.add_argument("--windows", default="",
                    help="comma-separated window labels to include, e.g. CNY,HRP,MAY")
    a = ap.parse_args()

    d = json.load(open(a.summary, encoding="utf-8"))
    items = [i for i in d["items"] if i["priority"] != "skip"]
    keep = {w.strip() for w in a.windows.split(",") if w.strip()}
    by_window = defaultdict(list)
    for i in items:
        if keep and i["label"] not in keep:
            continue
        by_window[i["label"]].append(i)

    lines = ["# Flight + leave plan", "",
             f"Generated from fares scanned on {d['generated']}. "
             f"{len(items)} priced combinations across {len(by_window)} windows.", ""]
    lines += ["Prices are one-adult, economy, taxes included, "
              "**before checked baggage**. Always re-check on the airline site.", ""]

    for lbl, rows in sorted(by_window.items(),
                            key=lambda kv: min(r["days_out"] for r in kv[1])):
        rows.sort(key=lambda x: x["per_night"])
        head = rows[0]
        lines += [f"## {lbl} — {head['kind']}", "",
                  f"{head['out']} → {head['ret']} "
                  f"({head['nights']} nights, {head['days_out']} days out)", "",
                  "| Destination | Airline | Dep → Arr | Fare | Baggage | +bag | Per night | Route percentile |",
                  "|---|---|---|---|---|---|---|---|"]
        for i in rows[: a.top]:
            b = i["bag"]
            bag = (f"{b.get('cabin', '')}; {b.get('checked', '')}"
                   if b.get("add20", 0) == 0
                   else f"{b.get('cabin', '')}; none (+{a.currency}{b['add20']})")
            if i["rank"] is None:
                pct = "n/a (long window)"
            elif i["n_windows"] < 3:
                pct = f"only {i['n_windows']} window scanned"
            else:
                pct = f"{i['rank']}/{i['n_windows']} ({i['vs_median']:+d}%)"
            lines.append(
                f"| **{i['name']}** {i['dest']} | {i['air']} | {i['dep']}→{i['arr']}"
                f"{' +1' if i['plus'] else ''} {i['dur']} | {money(a.currency, i['price'])} | "
                f"{bag} | {money(a.currency, i['price_with_bag'])} | "
                f"{money(a.currency, i['per_night'])} | {pct} |")
        lines += ["", "> Recommendation + reasons + what to do: _fill in by hand._", ""]

    open(a.out, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote", a.out, f"{len(lines)} lines")


if __name__ == "__main__":
    main()
