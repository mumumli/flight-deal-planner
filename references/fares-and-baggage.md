# Fares and baggage reference

A fare without a baggage state is not a quote. This file covers the fare brands,
the baggage economics, and the two pricing asymmetries that ruin comparisons.

---

## 1. The two asymmetries

### One-way is not half a round trip

- **Low-cost carriers** price each direction separately, so
  one-way + one-way ≈ round trip. Summing is safe.
- **Full-service carriers** often price a one-way at 1.5–3× half a round trip.
  So *round trip can be cheaper than one-way*, and this is not a data error.

Consequence: **never validate a round-trip figure by doubling a one-way.** If
two sources disagree by more than ~30% on a full-service carrier, the likely
explanation is exactly this, and the round-trip figure is the one that matches
what the user will actually pay.

### Promotions are usually round-trip only

Airline sales commonly apply to **return** tickets while the low-cost arm's sale
applies to **one-ways**. When a sale is running, state which, because it decides
the tactic:

- return-only sale → the carrier can undercut a low-cost rival on the same route
- one-way sale → stack two one-ways, and check they are on the same ticket type

---

## 2. Fare brands and what they include

Cheapest fare of each carrier, as recorded in 2026. Re-verify — these change.

| Carrier | Cheapest brand | Cabin baggage | Checked in base fare | Typical 20kg add-on |
|---|---|---|---|---|
| **Scoot** | Basic | **10kg across 2 pieces** | none | no flat table; ~SGD 30–45 short-haul, more long-haul |
| **AirAsia** | Low Fare | 7kg (1 bag + 1 small) | none | published table ceiling ~SGD 76; street price SGD 30–50 |
| **VietJet** | Eco | 7kg across 2 pieces, weighed together | none | ~SGD 28–30 on regional routes |
| **Cebu Pacific** | Base | 7kg | none | ~SGD 30–55 |
| **Firefly** | SAVER | 7kg | **10kg included** (BASIC = 20kg) | never cabin-only |
| **Batik Air** | Super Saver | 7kg | none (Value = **15kg**) | not published |
| **Jetstar Airways (JQ/GK)** | Starter | 7kg | none | ~SGD 40–70 |
| Full-service (SQ, MH, TG, VN, GA, QF, NH, JL, KE) | Economy | 7–10kg | **20–30kg included** | n/a |

Three rules that follow:

1. **Firefly can never be labelled "cabin bag only."** Even its cheapest brand
   carries checked baggage.
2. **Batik's mid brand is 15kg, not 20kg.** Do not write "includes 20kg".
3. **Scoot's cabin allowance is two pieces totalling 10kg**, not one piece.

---

## 3. When a full-service fare beats a low-cost one

Rule of thumb for a trip needing checked baggage:

```
low-cost total   = bare fare + bag fee (+ seat + meal)
full-service total = fare (bag included)
```

On short-haul the low-cost option usually still wins. On anything over ~5 hours,
or when the bag fee is charged per direction, the full-service fare often
reverses it. Always publish the **"fare + 20kg"** number alongside the bare fare
so the reversal is visible instead of hidden.

Worked example from a real scan:

- Scoot, 9h sector: fare 544 + bag 65 = **609**
- Full-service, same sector: **681**, 30kg included

The low-cost option is still cheaper, but by 11% rather than 20%, and that
changes the recommendation for a traveller with a suitcase.

---

## 4. Discontinued and lookalike carriers

- **Jetstar Asia (3K)** ceased operations **31 July 2025**. Any 3K row is stale
  inventory — filter it and note that it was filtered.
- **Jetstar Airways (JQ)** and **Jetstar Japan (GK)** still operate; they are
  different companies. Do not drop them along with 3K.
- Codeshare rows often show two carrier names (marketing + operating). Quote
  the **marketing** carrier and mention the operator if it differs, because the
  baggage rules usually follow the operating carrier.

---

## 5. What every quoted fare must carry

- currency and whether taxes are included
- number of passengers
- cabin (economy unless stated)
- baggage state, in one of: `cabin only, no checked bag` /
  `cabin only, +20kg ≈ X` / `includes Nkg checked`
- the total with a 20kg bag
- a timestamp, because low-cost inventory moves within hours
