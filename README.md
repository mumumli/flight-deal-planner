# flight-deal-planner

An [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) that plans a
year of travel around a country's public holidays: it scans **real fares**,
filters by **season** and **visa friction**, and outputs a dated plan —
*which holiday → which city → which flight → why → what to do there.*

It exists because "cheapest flight" and "trip worth taking" are different
questions. The cheapest fare in a spreadsheet is usually pointed at monsoon
season, or at a country whose visa takes three weeks.

```
Holiday calendar ──► windows ──► fare scan ──► season + visa filter ──► plan
```

---

## What it does

- **Finds the leave arbitrage.** For each public holiday it computes what 1, 2
  or 3 days of annual leave actually buy, with a leave-efficiency ratio.
  It knows a 9-day window from 3 days of leave beats a 4-day window from 1.
- **Scans real prices**, not estimates — Google Flights, via its server-rendered
  result page. Round-trip totals, per destination per window.
- **Refuses the trap.** Cheapest fares cluster in each destination's worst
  month. Season is a filter, not a tiebreak.
- **Compares fairly.** Cost per night, not absolute fare, when trip lengths
  differ. Route percentile, not "lowest ever".
- **Annotates baggage on every price**, because a carry-on fare and a
  with-a-suitcase fare often reverse the ranking.

## What it does not do

- It does not book. It produces a plan with links.
- It does not claim historical lows. The "route percentile" is cross-sectional
  across the windows it scanned, and says so.
- It does not trust one source. Shortlisted routes get a second check.

---

## Install

```bash
git clone <this repo> flight-deal-planner
cd flight-deal-planner
pip install -r scripts/requirements.txt
```

Drop the folder into your agent's skills directory (e.g. `~/.claude/skills/` or
your harness's equivalent). The `SKILL.md` frontmatter is all the loader needs.

Python 3.9+.

---

## Quickstart

**1 — see what your holidays are worth**

```bash
python3 scripts/holidays.py --country SG --year 2027 --max-leave 3
```

```
SG 2027 — natural long weekends
  2027-02-06 (Sat) -> 2027-02-08 (Mon)  3d  ['Chinese New Year', ...]
  ...

  anchor 2027-05-17 (Mon) Hari Raya Haji
    2d leave -> 6d off (2027-05-15 .. 2027-05-20)  efficiency 3.0x
    3d leave -> 9d off (2027-05-15 .. 2027-05-23)  efficiency 3.0x
```

Only Singapore is bundled. For any other country pass `--file holidays.csv`
(`date,name` rows) from the official government calendar.

**2 — scan fares**

```bash
cp assets/job.example.json job.json     # edit origin, destinations, windows
python3 scripts/scan.py --spec job.json
```

Resumable: re-running skips cells already in the output file.

**3 — rank**

```bash
cp assets/config.example.json config.json   # edit names, hours, baggage rules
python3 scripts/rank.py --fares data/fares.jsonl --config config.json
```

**4 — report**

```bash
python3 scripts/report.py --summary data/summary.json --out report.md
```

`report.py` emits the factual skeleton. The *why* and the *what to do* are
written by the agent on top of it — that part needs
`references/seasonality.md`, not a formula.

---

## The output contract

Every recommendation carries four things, and a price missing its baggage state
is treated as invalid:

```
### Good Friday — 26–29 Mar 2027 (3 nights, 1 day leave)
**Go to:** Tokyo (HND)
**Fly:** Scoot TR808, 26 Mar 17:35 → 01:25+1; return 29 Mar 06:10 → 12:45
**Fare:** S$702 round trip, carry-on only (+S$65 for 20kg → S$767)
**Why this one:** cherry blossom peaks 25 Mar – 5 Apr, so this window lands on
  it; the fare is 25% under the route's own median; only 1 day of leave.
**Do:** Ueno Park, Meguro River at dusk, day trip to Kamakura
**Book by:** 30 Oct — the sale is round-trip only
```

---

## How fare scanning works

`scripts/gf.py` builds Google Flights' `?tfs=` protobuf parameter (via
`fast-flights`), fetches the page, and parses the server-rendered result cards.
The plain `?q=` URL returns an empty shell, which is why this parameter matters.

Known limits, all documented in `SKILL.md` §8:

- the result list is **outbound-only** — a round-trip price shows outbound
  options paired with the cheapest acceptable return
- the list is **capped**; cells with fewer than five rows are marked unreliable
- **one-way ≠ half a round trip** on full-service carriers — a round-trip promo
  can be cheaper than a one-way
- booking horizon is ~330 days; further out returns nothing

---

## Repo layout

```
SKILL.md                       the method (what the agent executes)
references/seasonality.md      month × region table + monsoon asymmetries
references/visa-and-entry.md   entry-friction framework + worked example
references/fares-and-baggage.md fare brands, baggage economics, the two asymmetries
scripts/gf.py                  Google Flights fetch + parse
scripts/holidays.py            calendar → windows → leave optimiser
scripts/scan.py                batch scanner (job spec driven)
scripts/rank.py                scoring and bucketing
scripts/report.py              Markdown brief skeleton
assets/                        example traveller profile, job spec, config
```

---

## Caveats

Fares are snapshots and low-cost inventory moves within hours. Baggage fees are
estimates in the ranges given; the booking page is authoritative. Entry rules
change and `references/visa-and-entry.md` is a framework with one worked
example, not legal advice. Nothing here is a price guarantee.

## License

MIT — see `LICENSE`.
