# flight-deal-planner · 机票与假期规划器

[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776ab.svg)](https://www.python.org/)
[![Agent Skill](https://img.shields.io/badge/Agent-Skill-8a63d2.svg)](SKILL.md)

Plan a year of trips around a country's public holidays — real fares, filtered
by season and visa friction, with a reason for every pick.

围绕一个国家的公共假期规划一整年的旅行：扫真实票价，用季节和签证摩擦度过滤，
每一个推荐都附带理由。

> **Read this in** — English paragraphs come first; the Chinese version of each
> paragraph follows as a quote block.
>
> **语言约定** — 每段先英文，中文版本以引用块紧随其后。

<img src="examples/web-ui.png" width="820" alt="the web UI">

---

## Why · 为什么做这个

"Cheapest flight" and "trip worth taking" are different questions. The cheapest
fare in a spreadsheet is usually pointed at monsoon season, or at a country
whose visa takes three weeks.

> 「最便宜的机票」和「值得去的旅行」是两个问题。表格里最便宜的那张票，通常要么
> 指向雨季，要么指向一个签证要办三周的国家。

```text
holiday calendar → windows → fare scan → season + visa filter → plan
```

> 假期日历 → 旅行窗口 → 扫价 → 季节与签证过滤 → 计划

---

## What it does · 它做什么

| | Capability 能力 | 说明 |
|---|---|---|
| 🗓 | Computes what 1, 2 or 3 days of leave actually buy, anchored on each holiday, with a leave-efficiency ratio | 算出请 1 / 2 / 3 天年假分别能换几天连休，**锚定在该假期上**，并给出效率倍数 |
| ✈️ | Scans live Google Flights fares — real prices, not estimates | 扫 Google Flights 的实时票价，不是估算 |
| 🌦 | Treats season as a **filter**, not a tiebreak: never recommends rain because it is cheap | 把季节当**过滤器**而非加分项：不因为便宜就推荐雨季 |
| ⚖️ | Ranks by cost per night, so a 9-day bridge isn't compared to a 2-night weekend | 按「每晚成本」排序，不会拿 9 天窗口跟 2 晚周末直接比 |
| 🧳 | Annotates baggage on every price — carry-on vs suitcase often reverses the ranking | 每个价格都标注行李：裸票和含托运经常把排名反过来 |

**It does not · 它不做什么**

| | |
|---|---|
| ❌ | Book anything — it produces a plan with links · 不负责订票，只产出带链接的计划 |
| ❌ | Claim historical lows — the "route percentile" is cross-sectional across the windows you scanned · 不声称历史低位，分位是本次各窗口的横向排名 |

---

## Quick start · 快速开始

### 1 · In a browser, no CLI · 浏览器直接用

```bash
git clone https://github.com/mumumli/flight-deal-planner.git
cd flight-deal-planner
pip install -r scripts/requirements.txt
python3 web/server.py          # → http://127.0.0.1:8765
```

Pick origin, holiday calendar and year, tick the windows worth using, tick the
airports you'd consider, press **Scan**. You get a ranked table: fare, baggage
state, fare with a 20kg bag, cost per night, and how the date compares to the
other windows scanned. Right-click an airport to mark it *visited* so it stops
being suggested.

> 选出发地、假期日历和年份，勾上值得用的窗口，再勾上你愿意去的机场，点 **Scan**。
> 会返回一张排序表：裸票价、行李状态、加 20kg 后的价格、每晚成本，以及该日期相对
> 本次其它窗口的位置。**右键机场**可标记「去过」，之后不再推荐。

Stdlib only — nothing to install beyond the two scraper dependencies.

> 后端只用 Python 标准库，除两个抓取依赖外无需安装任何东西。

### 2 · As an agent skill · 作为 agent skill 使用

Drop the folder into your agent's skills directory (`~/.claude/skills/` or your
harness's equivalent) and say *"plan my 2027 holidays"*. It follows
[`SKILL.md`](SKILL.md) end to end.

> 把整个目录放进 agent 的 skills 目录（`~/.claude/skills/` 或等价位置），
> 说一句「帮我规划 2027 假期」，它会按 [`SKILL.md`](SKILL.md) 完整执行。

### 3 · As a library or CLI · 作为库或命令行

```bash
python3 scripts/holidays.py --country SG --year 2027 --max-leave 3
python3 scripts/scan.py   --spec job.json
python3 scripts/rank.py   --fares data/fares.jsonl --config config.json
python3 scripts/report.py --summary data/summary.json --out report.md
```

---

## What it produces · 输出长什么样

A real scan, unedited. Bali, April 2027, three nights, one day of leave:

> 下面是真实抓取结果，未做修饰。巴厘岛，2027 年 4 月，三晚，请一天假。

```text
2027-04-09 → 2027-04-12

Bali DPS · Scoot TR282 16:05→19:00 (2h55)
S$178 round trip · carry-on only, +S$38 for 20kg → S$216 · S$72/night
lowest of the 36 windows scanned for this route
```

Same week, Bangkok — where the full-service fare beats the low-cost one:

> 同一周换到曼谷——这张全服务航司的票反而比廉航便宜。

```text
2027-01-29 → 2027-02-01

Bangkok BKK · Singapore Airlines
S$276 round trip · 30kg checked included · S$92/night
Scoot on the same dates is S$400 — the sale flips the ranking
```

`scripts/report.py` emits the factual skeleton and stops at
`_fill in by hand_`; the *why* and the *what to do* are written by the agent
from [`references/seasonality.md`](references/seasonality.md). A generated
example sits in [`examples/example-report.md`](examples/example-report.md).

> `scripts/report.py` 只输出事实骨架，到 `_fill in by hand_` 为止；
> 「为什么去」和「玩什么」由 agent 参照
> [`references/seasonality.md`](references/seasonality.md) 来写。
> 生成好的样例在 [`examples/example-report.md`](examples/example-report.md)。

---

## Holiday calendars · 假期日历

| Code 代码 | Coverage 覆盖 | Confidence 可信度 |
|:---|:---|:---|
| `SG` | Singapore 2026–2027 · 新加坡 | **official 官方** — MOM |
| `HK` | Hong Kong 2027 · 香港 | **official 官方** — gov.hk 宪报 |
| `JP` | Japan, any year · 日本 | rule-based 规则推算 — equinox ±1 day 春秋分 ±1 天 |
| `AU` | Australia, any year · 澳洲 | rule-based — national only 仅全国假日 |
| `US` | United States, any year · 美国 | rule-based — federal only 仅联邦假日 |
| `CN` | Mainland China · 中国内地 | fixed dates only 仅固定日期 — **no lunar festivals 不含农历节** |
| `KR` | South Korea · 韩国 | fixed dates only — **no Seollal / Chuseok 不含春节秋夕** |
| `MY` | Malaysia · 马来西亚 | fixed dates only — **no state / Islamic holidays 不含州与伊斯兰节** |

Anything not rated `official` prints a warning, because a wrong holiday date
produces a confidently wrong plan. To supply your own calendar:

> 可信度不是 `official` 的都会打印警告——假日错一天，整个计划会错得很自信。
> 也可以自己提供日历：

```bash
python3 scripts/holidays.py --file my-holidays.csv --year 2027
# my-holidays.csv:  2027-01-01,New Year
```

---

## How fare scanning works · 扫价原理

`scripts/gf.py` builds Google Flights' `?tfs=` protobuf parameter (via
`fast-flights`), fetches the page, and parses the server-rendered result cards.
The plain `?q=` URL returns an empty shell — that parameter is the whole trick.

> `scripts/gf.py` 借助 `fast-flights` 构造 Google Flights 的 `?tfs=` protobuf 参数，
> 抓取页面后解析服务端渲染的结果卡片。直接用 `?q=` 只会拿到空壳页面——这个参数是关键。

Known limits — full list in [`SKILL.md`](SKILL.md) §8:

> 已知限制，完整清单见 [`SKILL.md`](SKILL.md) 第 8 节：

| | Limitation 限制 |
|:---|:---|
| 🔍 | Results are **outbound-only**; a round-trip price pairs outbound options with the cheapest acceptable return · 结果**只有去程**，往返价是「去程 + 系统挑的最便宜返程」 |
| 📉 | The list is **capped**; cells with fewer than five rows are flagged unreliable · 列表有**条数上限**，少于 5 行标记为样本不足 |
| 💱 | **One-way ≠ half a round trip** on full-service carriers — a promo round trip can be cheaper than a one-way · 全服务航司**单程 ≠ 往返一半**，往返促销可能比单程更便宜 |
| 📅 | Booking horizon is ~330 days; further out returns nothing · 可订窗口约 **330 天**，更远的日期查不到 |

---

## Repo layout · 目录结构

```text
SKILL.md                         the method the agent executes · 方法论
web/server.py                    local web UI, stdlib only · 本地网页后端
web/index.html                   single-page front end · 单页前端
references/seasonality.md        month × region climate + events · 气候与节庆
references/visa-and-entry.md     entry-friction framework · 入境摩擦框架
references/fares-and-baggage.md  fare brands & baggage economics · 票价与行李
scripts/gf.py                    Google Flights fetch + parse · 抓取解析
scripts/holidays.py              8 calendars + leave optimiser · 日历与请假优化
scripts/scan.py                  batch scanner, resumable · 批量扫描
scripts/rank.py                  scoring and bucketing · 打分分级
scripts/report.py                Markdown brief · 报告骨架
assets/                          destination catalogue + example configs · 机场目录与配置
examples/                        a real generated report + UI screenshot · 真实样例
```

---

## Adding a calendar · 添加一套日历

Calendars live in `scripts/holidays.py`. One dict, one line in two tables:

> 日历都在 `scripts/holidays.py` 里。加一个 dict，再在两个表里各加一行：

```python
def _tw(year):
    return {
        f"{year}-01-01": "New Year's Day",
        f"{year}-02-28": "Peace Memorial Day",
        # ... lunar holidays: take them from the government gazette
    }

BUILDERS = {..., "TW": _tw}
CALENDAR_META = {..., "TW": ("fixed-dates-only", "lunar holidays need --file")}
```

Set `confidence` honestly — `official` only when you copied a government source,
`fixed-dates-only` when you left lunar or religious holidays out. A wrong date
is worse than a missing one.

> `confidence` 要如实填写——只有照抄政府公告才能标 `official`；漏掉农历或宗教节日
> 就标 `fixed-dates-only`。**日期写错比不写更糟。**


---

## Caveats · 注意事项

Fares are snapshots; low-cost inventory moves within hours. Baggage fees are
ranges, not quotes — the booking page is authoritative. Entry rules change, and
[`references/visa-and-entry.md`](references/visa-and-entry.md) is a framework
with one worked example, not legal advice. Nothing here is a price guarantee.

> 票价是快照，廉航库存几小时内就会变。行李费给的是区间估算，以订票页为准。
> 入境规则会变，[`references/visa-and-entry.md`](references/visa-and-entry.md)
> 只是框架加一个实例，不构成法律建议。这里的一切都不构成价格承诺。

## License · 许可

MIT — see [`LICENSE`](LICENSE). · 详见 [`LICENSE`](LICENSE)。
