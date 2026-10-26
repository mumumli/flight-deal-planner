---
name: flight-deal-planner
description: Plan a year of trips around a country's public holidays by scanning real fares, then recommending which holiday to spend on which destination, which flight to book, why (season and fit), and what to do there. Use when the user asks to plan holidays around public holidays, find cheap weekend or long-weekend flights, decide where to go on a given leave allowance, compare destinations under a budget, or build a leave-optimised travel calendar.
---

# Flight Deal Planner

Turns a holiday calendar plus a traveller profile into a dated, priced,
justified travel plan: **which holiday → which destination → which flight →
why → what to do there.**

The value of this skill is not "find a cheap flight". It is refusing to
recommend a cheap flight that lands in monsoon season, and refusing to compare
a 2-night weekend against a 9-day bridge on absolute price.

---

## 0. Fastest path — the local web UI

```bash
python3 web/server.py        # → http://127.0.0.1:8765
```

The page collects everything in §1 as a form: origin, holiday calendar, year,
leave allowance, the windows worth using, the airports under consideration, and
the style flags. It runs the same scanner and ranker and returns a ranked table.

Use it when a human is present and wants to drive. Use the CLI path below when
you are the one doing the planning, or when the answer has to be reproducible.

---

## 1. Collect the inputs

Ask for these; if the user has already volunteered them, do not re-ask.

| Input | Why it matters | Default if absent |
|---|---|---|
| **Origin airport** (IATA) | every query needs it | ask; never guess |
| **Country whose public holidays apply** + year | defines the windows | ask |
| **Must-go destinations** | gets scanned even if expensive | none |
| **Visited list** | avoids re-recommending; "would revisit" is separate | ask, keep short |
| **Would-revisit list** | these are *features*, not exclusions | empty |
| **Travel style** | filters and annotations | see below |
| Budget ceiling (optional) | used for thresholds only | none |

Travel-style flags that change the plan:

- **Red-eye tolerance** — if low, exclude departures between 23:00–05:00 and
  returns arriving after midnight; if high, the cheapest fare is usually a
  red-eye and gets a bonus rather than a penalty.
- **Checked bag** — if the user travels carry-on only, sort by bare fare and
  always show the "+bag" column so the reversal is visible. If they need a
  bag, a full-service fare often beats a low-cost fare + bag.
- **Weekend warrior vs holiday-only** — decides whether ordinary weekends enter
  the scan at all. Weekend warriors need short sectors (≤4h); holiday-only
  travellers can be sent far.
- **Leave allowance** (days/year) — caps how many bridges you may propose.

Write the profile to `assets/traveller.yaml` so re-runs are cheap.

---

## 2. Build the calendar

```bash
python3 scripts/holidays.py --country SG --year 2027
python3 scripts/holidays.py --file my-country.csv --year 2027   # other countries
```

Bundled: `SG`, `HK`, `JP`, `AU`, `US`, `CN`, `KR`, `MY`. Each carries a
confidence label — `official`, `rule-based`, or `fixed-dates-only` — and the
command prints it. Only `SG` and `HK` are official; `CN`/`KR`/`MY` omit lunar
festivals, so a Chinese New Year or Chuseok plan needs `--file` with the
government's published dates. Never let a `fixed-dates-only` calendar silently
stand in for a full one.

This prints (a) the natural long weekends and (b) for each holiday, what 1, 2
and 3 days of annual leave actually buy — anchored on that holiday, with a
**leave-efficiency ratio** (days off ÷ leave days).

Rules:

- **Never invent a public holiday.** If the calendar is not bundled, fetch the
  official government source and cite it.
- Substituted/observed days (a Sunday holiday moving to Monday) change
  everything — verify them.
- Prefer windows with efficiency ≥ 3.0 and ≥ 4 days off. A 3-day window at
  efficiency 3.0 usually beats a 9-day window at 2.0 unless the user has leave
  to burn.
- Long windows (>5 nights) are where far destinations become rational, because
  the fixed cost of the flight amortises.

Output of this step: a table of **windows**, each with `label`, `out` date,
`ret` date, nights, and leave cost.

---

## 3. Build the destination universe

Three buckets, all scanned:

1. **Must-go** — from the user's list, regardless of price.
2. **Revisit** — places they liked; treat "cheap + right season" as a strong
   signal, and say so in the reason.
3. **Explore** — never visited.

Scope each destination honestly:

- `short` — flight ≤ ~4h: valid for a 2–4 night weekend.
- `long` — longer: only propose on windows ≥5 nights, unless the user is
  explicitly a red-eye weekend warrior.

Then filter by **entry friction** before spending a scan on it:

- Visa-free / visa-on-arrival / already-held visa → zero friction, fine.
- e-visa in ≤3 working days → fine for anything ≥1 month out.
- Visa needing >5 working days and the window is inside 14 days → drop it from
  the near term but keep it for later windows.

See `references/visa-and-entry.md`.

---

## 4. Scan fares

```bash
cp assets/job.example.json job.json      # edit origin/destinations/windows
python3 scripts/scan.py --spec job.json
python3 scripts/rank.py --fares data/fares.jsonl --config config.json
python3 scripts/report.py --summary data/summary.json --out report.md
```

Dependencies: `pip install -r scripts/requirements.txt`.

Scan in two passes, because they answer different questions:

- **Pass A — grid.** every destination × every window. Broad, cheap, gives the
  route's own price distribution.
- **Pass B — depth.** once Pass A shows which routes are cheap, scan every
  weekend of the year for the top few, to find whether a price is one lucky
  date or a stable low band. A stable band is far more actionable.

Always keep a **second source** for the shortlist. If an MCP flight-price
server is available, use it for flight numbers and a one-way cross-check;
otherwise check the airline's own site.

---

## 5. Score and rank

Sort by **cost per night**, not absolute fare, whenever trip lengths differ.
Then apply, in order:

1. **Season fit** — a hard filter, not a tiebreak. Cheapest fares cluster in
   each destination's worst weather. Never recommend rain because it is cheap;
   recommend it only if the user wants that city anyway.
2. **Route percentile** — is this date low *for this route*? The `rank` field
   is cross-sectional across scanned windows, **not** a 30–60 day historical
   percentile. Say so.
3. **Price sanity vs the airline's own baseline** — for a full-service carrier
   a promo round trip can be cheaper than a one-way; do not "correct" it away,
   but verify it once.
4. **Friction** — visa lead time, connection length, airport transfers.

Bucket each candidate:

- 🔴 **book now** — inside the actionable window (default 64 days) and at a
  route low, non-red-eye, sane hours.
- 🟢 **target** — inside a holiday window, priced at or below the route's own
  median; set an alert.
- 🟡 **watch** — near the threshold but not there.
- ⚪ **reference** — all the rest, kept so the user can see what "expensive"
  looks like.

---

## 6. Verify the shortlist

Before quoting anything as bookable, for each shortlisted row:

- Re-query with the exact dates and read the row again.
- Confirm the **return leg exists** — a round-trip price is only real if the
  return inventory exists.
- Get the **flight number** from a second source; Google Flights' result list
  does not expose it.
- Check the **baggage** of that specific fare brand, not the airline in general.

If two sources disagree by more than ~30% on a full-service carrier, say so in
the output rather than picking one. That gap usually means "one-way priced"
versus "round-trip promo priced", and it changes the recommendation.

---

## 7. Write the plan

One block per holiday window. Never a bare table of prices.

```
### <Holiday> — <dates> (<n> nights, <leave cost>)
**Go to:** <City> (<IATA>)
**Fly:** <airline> <flight no.> <date> <dep>→<arr>; return <date> <dep>→<arr>
**Fare:** <currency><price> round trip, <baggage state>, <currency><price+bag> with a 20kg bag
**Why this one:** <season in one sentence> + <price reason: route percentile> + <fit reason: revisit/new/must-go>
**Do:** <3–5 concrete things, season-appropriate>
**Book by:** <deadline if a sale is running>
```

Rules for the output:

- Every price carries a baggage state. A price without baggage is an invalid
  output.
- Every recommendation carries a season reason. "Cheap" alone is not a reason.
- If the cheapest option is in bad season, say so and recommend the second.
- When a sale is running, state its **booking deadline** and whether it applies
  to round trips or one-ways — the two differ and it decides the tactic.
- Rank by what the user asked for, not by what is easiest to compute.

---

## 8. Hard-won gotchas

These cost real debugging time; do not rediscover them.

- **The Google Flights URL needs the `?tfs=` protobuf parameter.** A plain
  `?q=...` URL returns a shell page with zero fares. `scripts/gf.py` builds it
  with `fast_flights`' encoder.
- **The result list is outbound-only.** A round-trip cell shows outbound
  options priced with the cheapest acceptable return. You cannot see the
  return's time from that page — query the return leg separately when it
  matters.
- **The list is capped (~10–20 rows, sometimes 3).** Cells with fewer than five
  rows have unreliable minimums. Always mark them.
- **Departure-hour filters shrink the list.** If a filtered query returns
  nothing, retry unfiltered; the cheapest option often sits outside the window
  you assumed.
- **One-way ≠ half a round trip.** For low-cost carriers they are close; for
  full-service carriers a round-trip promo can be *cheaper* than a one-way.
  Never validate a round-trip figure by doubling a one-way.
- **"Arrive Monday early morning" means a Sunday 20:00–23:59 departure**, not a
  Monday 00:00 departure. Most carriers' last flight leaves before midnight;
  filtering on the calendar day you land returns nothing.
- **Jetstar Asia (3K) ceased operations on 31 July 2025.** Drop 3K rows.
  Jetstar Airways (JQ) and Jetstar Japan (GK) still fly.
- **Low-cost fares exclude checked baggage.** Scoot's 2026 cabin allowance is
  2 pieces totalling 10kg; AirAsia is 7kg; VietJet is 7kg across 2 pieces.
  Quotes must say which fare brand they are.
- **Booking horizon is ~330 days.** Anything further out returns nothing; mark
  those windows "on sale later" instead of "no flights".
- **A same-price band beats a single cheap date.** Four consecutive weekends at
  the same fare means the user can choose a date; one cheap date means they
  must.

---

## 9. Files

```
web/server.py        local web UI (stdlib only)
web/index.html       single-page front end
scripts/gf.py        Google Flights fetch + parse (the engine)
scripts/holidays.py  calendar -> windows -> leave-efficiency optimiser
scripts/scan.py      batch scanner, resumable, job spec driven
scripts/rank.py      scoring and bucketing
scripts/report.py    Markdown brief skeleton
references/seasonality.md      month-by-region weather and event calendar
references/visa-and-entry.md   entry-friction framework + worked example
references/fares-and-baggage.md fare brands and baggage economics
assets/traveller.example.yaml  input profile
assets/job.example.json        scanner job spec
```

When the user asks for a one-off check ("just tell me the cheapest weekend to
Bali"), skip the pipeline and query directly with `scripts/gf.py`'s `query()`.
The full pipeline is for when they want the whole year planned.
