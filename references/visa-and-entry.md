# Entry friction reference

Entry rules decide whether a cheap fare is usable at all. Classify every
destination before scanning, because a visa that takes three weeks is
irrelevant on a window three weeks out.

**This file is a framework, not a legal source. Rules change, and they change
fast. Verify against the destination's official immigration site and cite it.**

---

## 1. The four friction classes

| Class | Meaning | Lead time | Usable in a 14-day window? |
|---|---|---|---|
| **Zero** | visa-free, visa-on-arrival, or a visa the traveller already holds | none | yes |
| **Low** | e-visa / ETA / arrival card online | minutes – 3 working days | yes |
| **Needs lead time** | embassy appointment, biometrics, or >5 working days | 1–3 weeks | no — long-holiday only |
| **Blocked** | permit practically unobtainable for this passport | — | no |

Also check, separately:

- **Passport validity** — usually 6 months beyond arrival.
- **Onward/return ticket** — many Asian countries require proof.
- **Proof of funds / accommodation** — occasionally enforced at check-in.
- **Transit rules** — a connection can need its own visa even when the
  destination is visa-free.
- **Arrival cards** — Singapore SGAC, Malaysia MDAC, Thailand TDAC. Free, but
  required and time-boxed (usually within 3 days of arrival).

---

## 2. Extra friction to actively verify, because these are commonly wrong

These four are the ones models and blog posts get wrong most often. Check them
against a government source dated within the last 12 months.

1. **Transit-visa-free schemes are narrower than they look.** A scheme that
   accepts "US / Canada / Australia / NZ / Schengen" visas frequently does
   **not** accept a Japanese visa. Read the eligible-visa list itself.
2. **Transit schemes usually require a real transit**, i.e. the trip must be
   between the eligible country and a third country. A round trip
   home → transit country → home does not qualify.
3. **A "visa-free" destination may actually be visa-on-arrival** (paid), which
   changes the cost but not the lead time. Report the fee.
4. **Conditional visa-free schemes expire.** A scheme announced with a one-year
   validity is a trap for bookings made for the following year — check the
   expiry against the travel date.

New Zealand's NZeTA is a good example of a conditional scheme: it requires
travelling **directly from Australia** with an eligible Australian visa, so a
direct flight from elsewhere in Asia does not qualify even though the traveller
holds the right visa.

---

## 3. Worked example — PRC ordinary passport, resident in Singapore, holding valid Japan and Australia long-term visas

Recorded as of October 2026. Re-verify before use.

| Destination | Class | Rule |
|---|---|---|
| Singapore (as resident) | Zero | 30-day mutual visa exemption; SG Arrival Card within 3 days |
| Malaysia | Zero | visa exemption extended well beyond 2026; MDAC required |
| Thailand | Zero | bilateral exemption, 30 days |
| Indonesia | **Low (paid)** | China is on the **visa-on-arrival** list, not visa-free — roughly USD 35, 30 days |
| Vietnam | Low | 90-day e-visa, ~3 working days. Phu Quoc has a separate direct-arrival exemption |
| Philippines | Low | 14-day visa-free, **unconditional**, but only via Manila and Cebu airports, not extendable — and it was under review in late 2026 |
| Japan | Zero *for this traveller* | the held visa is the entry permission |
| Australia | Zero *for this traveller* | the held visa is the entry permission |
| South Korea | **Needs lead time** | tourist visa ≈8 working days, no expedite. The transit scheme is 30 days (not 24h) and lists Australia but **not Japan** — so only a genuine Australia-connected transit works |
| Taiwan | Needs lead time | entry permit, ~2–3 weeks, obtainable |
| New Zealand | Needs lead time | NZeTA, but only from Australia with an eligible Australian visa |

The generalisable lessons:

- A held visa converts a "needs visa" destination into zero friction — model
  the traveller's *actual* document set, not just their passport.
- "Visa-free" and "visa-on-arrival" are different products; the second costs
  money and time at the airport.
- Transit schemes key off specific visa nationalities. Do not generalise from
  "they accept western visas".

---

## 4. What to write in the output

One line per destination, naming the mechanism, not just the verdict:

> "Visa on arrival, ~USD 35, 30 days — nothing to arrange before flying."

Not:

> "Visa required."

And when a destination fails only because of lead time, keep it in the plan for
a later window and say why:

> "South Korea needs ~8 working days for the visa, so it cannot make the
> February window — it fits the May one comfortably."
