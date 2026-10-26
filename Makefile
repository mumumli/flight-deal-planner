.PHONY: help web holidays demo install clean

help:
	@echo "make install    install scraper dependencies"
	@echo "make web        open the local web UI at http://127.0.0.1:8765"
	@echo "make holidays   show 2027 windows for Singapore"
	@echo "make demo       run the bundled example end to end"
	@echo "make clean      remove generated data"

install:
	pip install -r scripts/requirements.txt

web:
	python3 web/server.py

holidays:
	python3 scripts/holidays.py --country SG --year 2027 --max-leave 3

demo:
	mkdir -p data
	python3 scripts/scan.py --spec assets/job.example.json
	python3 scripts/rank.py --fares data/fares.jsonl --config assets/config.example.json
	python3 scripts/report.py --summary data/summary.json --out report.md
	@echo "wrote data/summary.json and report.md"

clean:
	rm -rf data report.md scripts/__pycache__ web/__pycache__ scripts/.cache
