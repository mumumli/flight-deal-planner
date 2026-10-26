# Seasonality reference

The single most common failure in cheap-flight planning is recommending a fare
that is cheap *because* the destination is in its worst month. This file exists
so season is checked before price.

Confidence: these are climate norms, not forecasts. For anything weather-critical
(typhoon season, sakura dates, snow), verify against the current year's
forecast before booking — bloom and foliage dates move by 1–2 weeks.

---

## 1. Month-by-region quick table

`★` = best month, `✕` = avoid, `–` = shoulder/neutral.

| Region | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Thailand — Andaman (Phuket, Krabi) | ★ | ★ | ★ | ★ | – | ✕ | ✕ | ✕ | ✕ | – | ★ | ★ |
| Thailand — Gulf (Samui, Ko Tao) | ★ | ★ | – | – | – | – | – | – | – | ✕ | ✕ | ✕ |
| Thailand — inland (Bangkok, Chiang Mai) | ★ | ★ | – | – | – | ✕ | ✕ | ✕ | ✕ | – | ★ | ★ |
| Vietnam — North (Hanoi, Sapa) | – | – | – | – | – | ✕ | ✕ | ✕ | ✕ | ★ | ★ | – |
| Vietnam — Central (Da Nang, Hoi An, Hue) | ✕ | – | – | ★ | ★ | ★ | ★ | ★ | ✕ | ✕ | ✕ | ✕ |
| Vietnam — South (HCMC, Phu Quoc) | ★ | ★ | ★ | – | ✕ | ✕ | ✕ | ✕ | ✕ | ✕ | – | ★ |
| Vietnam — Nha Trang | ★ | ★ | ★ | ★ | ★ | ★ | ★ | ★ | – | – | – | – |
| Bali / Lombok | ✕ | ✕ | – | ★ | ★ | ★ | ★ | ★ | ★ | ★ | – | ✕ |
| Java (Jakarta, Yogyakarta) | ✕ | ✕ | – | – | ★ | ★ | ★ | ★ | ★ | – | – | ✕ |
| Malaysia — west coast (KL, Penang, Langkawi) | ★ | ★ | – | – | – | – | – | – | – | – | – | ★ |
| Malaysia — Borneo (Kuching, Kota Kinabalu) | ✕ | ✕ | – | – | – | – | – | – | – | – | – | ✕ |
| Philippines | ★ | ★ | ★ | ★ | ★ | – | ✕ | ✕ | ✕ | ✕ | – | ★ |
| Japan — Tokyo / Kyoto | ✕ | ✕ | – | ★ | ★ | ✕ | – | – | – | ★ | ★ | – |
| Japan — Hokkaido | ★ | ★ | – | – | – | – | ★ | ★ | – | – | – | ★ |
| Korea | ✕ | ✕ | – | ★ | ★ | – | ✕ | – | – | ★ | ★ | – |
| China — east coast cities | ✕ | ✕ | – | ★ | ★ | – | – | – | – | ★ | ★ | – |
| China — Sichuan / Yunnan highlands | ✕ | – | – | ★ | ★ | ★ | – | – | – | ★ | – | – |
| China — Hainan | ★ | ★ | – | – | ✕ | ✕ | ✕ | ✕ | ✕ | – | ★ | ★ |
| Australia — Sydney / Melbourne | ★ | ★ | ★ | ★ | – | – | – | – | – | ★ | ★ | ★ |
| Australia — Perth | – | – | ★ | ★ | – | ✕ | ✕ | ✕ | ✕ | – | ★ | ★ |
| New Zealand — South Island | ★ | ★ | ★ | – | – | ✕ | ✕ | – | – | – | ★ | ★ |
| UAE / Gulf | ★ | ★ | ★ | – | ✕ | ✕ | ✕ | ✕ | ✕ | – | ★ | ★ |
| Western Europe | ✕ | ✕ | – | – | ★ | ★ | ★ | ★ | ★ | – | – | ✕ |

---

## 2. The monsoon asymmetries that catch people out

**Thailand has two coasts, and their rainy seasons are opposite.** Phuket and
Krabi (Andaman) are wet May–October. Ko Samui (Gulf) is wet October–December.
A "cheap Phuket" in July and a "cheap Samui" in November are the same mistake.

**Vietnam is three climates.** Hanoi wet May–September. Central Vietnam
(Da Nang, Hoi An) wet September–December — its best months are March–August,
which is exactly when the south is wet. Nha Trang is the exception: dry
January–August.

**Bali and Java are in the southern hemisphere monsoon**, so their dry season
(April–October) overlaps the northern wet season. April is the sweet spot:
dry, and before the July–August tourist peak.

**The Philippines is wet June–November** and sits in the typhoon belt
July–October. A cheap Manila fare in August is cheap for a reason.

---

## 3. Event calendars that move prices

| Event | Typical window | Effect |
|---|---|---|
| Japanese cherry blossom | late Mar – early Apr | Japan fares peak; book 4–6 months out |
| Japanese Golden Week | 29 Apr – 5 May | domestic Japan packed; avoid |
| Japan Obon | mid-August | transport and hotels peak |
| Thai Songkran | 13–15 April | Thailand gets busier, not cheaper |
| Chinese New Year | late Jan – late Feb | China domestic crush; also drives SG/MY prices |
| Chinese Golden Week | 1–7 October | China inbound/outbound spike |
| Ramadan / Eid | moves ~11 days earlier each year | Indonesia, Malaysia, Gulf demand shifts |
| Australian school holidays | late Dec – Jan, mid-year | domestic Australia peak |
| European summer | Jul – Aug | long-haul Europe peak |

Check the year's actual dates: Ramadan, Eid and CNY move every year.

---

## 4. How to use this in the recommendation

For each candidate, state one line:

> "April is Bali's dry-season shoulder — dry, but before the July crowds."

If the cheapest candidate fails the season test, **say so explicitly and
recommend the second-cheapest that passes**. Never silently drop the cheapest
one; the user may have a reason to want that city anyway.

If a destination has no good season during the user's available windows, that
is itself the finding — say "not worth using a holiday on" rather than forcing
a pick.
