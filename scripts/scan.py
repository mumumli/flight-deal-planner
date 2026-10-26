#!/usr/bin/env python3
"""Batch fare scanner.

Reads a job spec (JSON), queries Google Flights once per
(destination x travel window), and appends one JSONL record per cell.
Resumable: cells already present in the output file are skipped.

Job spec
--------
{
  "origin": "SIN",
  "currency": "SGD",
  "destinations": ["DPS", "CGK", "HAN"],
  "windows": [
    {"label": "CNY",  "out": "2027-02-05", "ret": "2027-02-08", "kind": "long weekend"},
    {"label": "MAY",  "out": "2027-05-14", "ret": "2027-05-23", "kind": "9-day bridge"}
  ],
  "airlines": ["TR", "SQ"],          // optional; omit to scan every carrier
  "max_stops": 1,                    // optional; 0 = nonstop only
  "max_duration_minutes": 480,       // optional; total travel time cap
  "out_window": [15, 23],            // optional; departure-hour filter, outbound
  "ret_window": [0, 8],              // optional; departure-hour filter, return
  "workers": 5,
  "out": "data/fares.jsonl"
}

Usage
-----
    python3 scan.py --spec job.json
    python3 scan.py --spec job.json --force     # re-scan everything
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf  # noqa: E402


def build(cfg, dest, win):
    """Build the ?tfs= URL, honouring optional airline and hour filters."""
    from fast_flights import FlightQuery, create_query

    kw = {}
    if cfg.get("airlines"):
        kw["airlines"] = cfg["airlines"]
    if cfg.get("max_stops") is not None:
        kw["max_stops"] = cfg["max_stops"]
    if cfg.get("max_duration_minutes"):
        kw["max_duration_minutes"] = cfg["max_duration_minutes"]
    if cfg.get("out_window"):
        kw["earliest_departure_hour"], kw["latest_departure_hour"] = cfg["out_window"]
    legs = [FlightQuery(date=win["out"], from_airport=cfg["origin"],
                        to_airport=dest, **kw)]
    trip = "one-way"
    if win.get("ret"):
        kw2 = {}
        if cfg.get("airlines"):
            kw2["airlines"] = cfg["airlines"]
        if cfg.get("max_stops") is not None:
            kw2["max_stops"] = cfg["max_stops"]
        if cfg.get("ret_window"):
            kw2["earliest_departure_hour"], kw2["latest_departure_hour"] = cfg["ret_window"]
        legs.append(FlightQuery(date=win["ret"], from_airport=dest,
                                to_airport=cfg["origin"], **kw2))
        trip = "round-trip"
    q = create_query(flights=legs, trip=trip, seat="economy",
                     currency=cfg.get("currency", "SGD"), language="en")
    return "https://www.google.com/travel/flights?" + urllib.parse.urlencode(q.params())


def work(cfg, dest, win, force=False):
    try:
        url = build(cfg, dest, win)
        rows = gf.parse(gf.fetch(url, force=force))
        if not rows:
            # the hour filter can be too tight for thin routes -> retry unfiltered
            cfg2 = {k: v for k, v in cfg.items()
                    if k not in ("out_window", "ret_window")}
            url = build(cfg2, dest, win)
            rows = gf.parse(gf.fetch(url, force=force))
    except Exception as e:  # noqa: BLE001
        return {"origin": cfg["origin"], "to": dest, "label": win["label"],
                "kind": win.get("kind", ""), "out": win["out"], "ret": win.get("ret"),
                "n": 0, "rows": [], "error": str(e),
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    return {"origin": cfg["origin"], "to": dest, "label": win["label"],
            "kind": win.get("kind", ""), "out": win["out"], "ret": win.get("ret"),
            "url": url, "n": len(rows), "rows": rows,
            "leave_days": win.get("leave_days"), "holiday": win.get("holiday"),
            "nights": win.get("nights"),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    cfg = json.load(open(a.spec, encoding="utf-8"))
    out = cfg.get("out", "data/fares.jsonl")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    done = set()
    if os.path.exists(out) and not a.force:
        for line in open(out, encoding="utf-8"):
            try:
                r = json.loads(line)
                done.add((r["to"], r["out"], r.get("ret")))
            except Exception:  # noqa: BLE001
                pass

    cells = [(d, w) for d in cfg["destinations"] for w in cfg["windows"]
             if (d, w["out"], w.get("ret")) not in done]
    if a.limit:
        cells = cells[:a.limit]
    print(f"origin={cfg['origin']} cells={len(cells)} skipped={len(done)}", flush=True)

    ok = err = 0
    with ThreadPoolExecutor(max_workers=cfg.get("workers", 5)) as ex:
        futs = [ex.submit(work, cfg, d, w, a.force) for d, w in cells]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            ok, err = (ok + 1, err) if not r.get("error") else (ok, err + 1)
            if i % 10 == 0 or i == len(cells):
                best = r["rows"][0]["price"] if r.get("rows") else "-"
                print(f"[{i}/{len(cells)}] ok={ok} err={err} "
                      f"{r['to']}/{r['label']} n={r.get('n')} best={best}", flush=True)
    print(f"DONE ok={ok} err={err}", flush=True)


if __name__ == "__main__":
    main()
