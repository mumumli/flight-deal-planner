#!/usr/bin/env python3
"""Pre-flight check: is this install actually able to scan and advise?

    python3 scripts/selfcheck.py
    make doctor
"""
import json
import os
import socket
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def line(ok, label, detail=""):
    mark = "OK  " if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def main():
    print("\nflight-deal-planner — self check\n")
    ok = True

    ok &= line(sys.version_info >= (3, 9), "python >= 3.9", sys.version.split()[0])

    try:
        import fast_flights  # noqa: F401
        ok &= line(True, "fast-flights installed")
    except Exception as e:  # noqa: BLE001
        ok &= line(False, "fast-flights installed",
                   "pip install -r scripts/requirements.txt  "
                   "(use a venv: python3 -m venv .venv && source .venv/bin/activate)")

    try:
        import primp  # noqa: F401
        ok &= line(True, "primp installed")
    except Exception:  # noqa: BLE001
        ok &= line(False, "primp installed", "pulled in by fast-flights")

    sys.path.insert(0, HERE)
    try:
        import holidays as H
        shp, conf, src = H.shapes("SG", 2027, 3)
        ok &= line(bool(shp), "holiday engine", f"{len(shp)} shapes, {conf}")
    except Exception as e:  # noqa: BLE001
        ok &= line(False, "holiday engine", str(e))

    for name in ("gf", "carriers", "rank", "scan"):
        try:
            __import__(name)
            ok &= line(True, f"module {name}")
        except Exception as e:  # noqa: BLE001
            ok &= line(False, f"module {name}", str(e))

    try:
        req = urllib.request.Request("https://www.google.com/travel/flights",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            ok &= line(r.status == 200, "network to google.com", f"HTTP {r.status}")
    except Exception as e:  # noqa: BLE001
        ok &= line(False, "network to google.com", str(e))

    s = socket.socket()
    busy = s.connect_ex(("127.0.0.1", 8765)) == 0
    s.close()
    line(True, "port 8765", "in use — a server is probably already running"
         if busy else "free")

    print("\n" + ("All good — run: python3 web/server.py\n"
                  if ok else "Fix the FAILs above, then run: python3 web/server.py\n"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
