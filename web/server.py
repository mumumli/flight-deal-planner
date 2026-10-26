#!/usr/bin/env python3
"""Local web UI for flight-deal-planner.

    python3 web/server.py            # then open http://127.0.0.1:8765

Stdlib only. The page collects origin, holiday calendar, travel windows,
destinations and style flags, then POSTs a scan job; the server runs the same
scanner and ranker the CLI uses and streams progress back.

Nothing leaves your machine except the Google Flights queries themselves.
"""
import json
import os
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import gf            # noqa: E402
import holidays as holiday_mod   # noqa: E402
import rank as rank_mod          # noqa: E402
import scan as scan_mod          # noqa: E402

PORT = int(os.environ.get("PORT", "8765"))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DEST_CATALOG = json.load(open(os.path.join(ROOT, "assets", "destinations.json"),
                              encoding="utf-8"))["destinations"]
DEST_BY_CODE = {d["code"]: d for d in DEST_CATALOG}

JOBS = {}
JOBS_LOCK = threading.Lock()


def default_baggage():
    return {
        "Scoot": {"tier": "low-cost", "cabin": "10kg, 2 pieces", "checked": "none", "add20": 38},
        "AirAsia": {"tier": "low-cost", "cabin": "7kg", "checked": "none", "add20": 42},
        "Thai AirAsia": {"tier": "low-cost", "cabin": "7kg", "checked": "none", "add20": 42},
        "VietJet": {"tier": "low-cost", "cabin": "7kg, 2 pieces", "checked": "none", "add20": 29},
        "Cebu Pacific": {"tier": "low-cost", "cabin": "7kg", "checked": "none", "add20": 45},
        "Batik Air": {"tier": "mixed", "cabin": "7kg", "checked": "brand-dependent", "add20": 35},
        "Malaysia Airlines": {"tier": "full-service", "cabin": "7kg", "checked": "20kg included", "add20": 0},
        "Singapore Airlines": {"tier": "full-service", "cabin": "7kg", "checked": "30kg included", "add20": 0},
        "Thai Airways": {"tier": "full-service", "cabin": "7kg", "checked": "20kg included", "add20": 0},
        "Vietnam Airlines": {"tier": "full-service", "cabin": "10kg", "checked": "20kg included", "add20": 0},
        "Garuda Indonesia": {"tier": "full-service", "cabin": "7kg", "checked": "20kg included", "add20": 0},
        "China Airlines": {"tier": "full-service", "cabin": "7kg", "checked": "23kg included", "add20": 0},
        "Emirates": {"tier": "full-service", "cabin": "7kg", "checked": "25kg included", "add20": 0},
        "Qantas": {"tier": "full-service", "cabin": "7kg", "checked": "30kg included", "add20": 0},
        "KLM": {"tier": "full-service", "cabin": "12kg", "checked": "23kg included", "add20": 0},
        "Japan Airlines": {"tier": "full-service", "cabin": "7kg", "checked": "23kg included", "add20": 0},
        "ANA": {"tier": "full-service", "cabin": "7kg", "checked": "23kg included", "add20": 0},
        "Asiana": {"tier": "full-service", "cabin": "10kg", "checked": "23kg included", "add20": 0},
        "Korean Air": {"tier": "full-service", "cabin": "10kg", "checked": "23kg included", "add20": 0},
        "China Southern": {"tier": "full-service", "cabin": "7kg", "checked": "23kg included", "add20": 0},
    }


def run_job(job_id, spec, cfg):
    job = JOBS[job_id]
    fares = os.path.join(DATA_DIR, f"fares_{job_id}.jsonl")
    if os.path.exists(fares):
        os.remove(fares)
    spec = dict(spec)
    spec["out"] = fares

    cells = [(d, w) for d in spec["destinations"] for w in spec["windows"]]
    job["total"] = len(cells)
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=int(spec.get("workers", 5))) as ex:
            futs = [ex.submit(scan_mod.work, spec, d, w) for d, w in cells]
            for f in as_completed(futs):
                r = f.result()
                with open(fares, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                with JOBS_LOCK:
                    job["done"] += 1
                    if r.get("rows"):
                        job["best_seen"] = min(job.get("best_seen") or 10**9,
                                               r["rows"][0]["price"])

        job["phase"] = "ranking"
        items, stats = rank_mod.rank(fares, cfg)
        job["items"] = items
        job["stats"] = stats
        job["phase"] = "done"
    except Exception as e:  # noqa: BLE001
        job["phase"] = "error"
        job["error"] = str(e)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, status=200, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)

        if u.path in ("/", "/index.html"):
            return self._file("index.html", "text/html")
        if u.path == "/api/catalog":
            return self._send({"destinations": DEST_CATALOG,
                               "countries": sorted(holiday_mod.CALENDAR_META)})
        if u.path == "/api/holidays":
            country = (q.get("country", ["SG"])[0]).upper()
            year = int(q.get("year", ["2027"])[0])
            try:
                wins = holiday_mod.windows(country, year, int(q.get("max_leave", ["3"])[0]))
            except Exception as e:  # noqa: BLE001
                return self._send({"error": str(e)}, 400)
            conf, src = holiday_mod.CALENDAR_META.get(country, ("unknown", "n/a"))
            return self._send({"country": country, "year": year, "confidence": conf,
                               "source": src, "windows": wins})
        if u.path == "/api/job":
            jid = q.get("id", [""])[0]
            job = JOBS.get(jid)
            if not job:
                return self._send({"error": "unknown job"}, 404)
            out = {k: job.get(k) for k in
                   ("phase", "done", "total", "error", "best_seen")}
            if job.get("phase") in ("done", "error"):
                out["items"] = job.get("items")
                out["stats"] = job.get("stats")
            return self._send(out)
        return self._send({"error": "not found"}, 404)

    def _file(self, name, ctype):
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            return self._send({"error": "missing " + name}, 404)
        with open(path, "rb") as fh:
            self._send(fh.read(), 200, ctype)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/api/scan":
            return self._send({"error": "not found"}, 404)
        n = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:  # noqa: BLE001
            return self._send({"error": "bad json"}, 400)

        origin = (body.get("origin") or "SIN").upper()
        cur = body.get("currency") or "SGD"
        codes = [c for c in body.get("destinations", []) if c in DEST_BY_CODE]
        wins = body.get("windows", [])
        if not codes or not wins:
            return self._send({"error": "pick at least one destination and one window"}, 400)

        spec = {
            "origin": origin, "currency": cur, "destinations": codes,
            "windows": [{"label": w["label"], "out": w["start"], "ret": w["end"],
                         "kind": f"{w.get('holiday', '')} (+{w.get('leave_days', 0)}d leave)"}
                        for w in wins],
            "airlines": body.get("airlines") or None,
            "out_window": body.get("out_window") or None,
            "workers": 5,
        }
        spec = {k: v for k, v in spec.items() if v not in (None, [])}

        cfg = {
            "home": origin, "currency": cur, "today": time.strftime("%Y-%m-%d"),
            "near_days": int(body.get("near_days", 64)),
            "long_windows": [w["label"] for w in wins if int(w.get("days_off", 0)) >= 5],
            "destinations": {
                c: {"name": DEST_BY_CODE[c]["name"],
                    "country": DEST_BY_CODE[c]["country"],
                    "hours": DEST_BY_CODE[c]["hours"],
                    "scope": "short" if DEST_BY_CODE[c]["hours"] <= 4.5 else "long",
                    "visa": ""}
                for c in codes},
            "baggage": default_baggage(),
            "exclude": {"destinations": body.get("exclude", []), "windows": []},
        }

        jid = uuid.uuid4().hex[:12]
        with JOBS_LOCK:
            JOBS[jid] = {"phase": "scanning", "done": 0, "total": len(codes) * len(wins),
                         "items": None, "stats": None, "error": None, "best_seen": None}
        threading.Thread(target=run_job, args=(jid, spec, cfg), daemon=True).start()
        return self._send({"job_id": jid})


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"flight-deal-planner  →  http://127.0.0.1:{PORT}")
    print("Ctrl-C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
