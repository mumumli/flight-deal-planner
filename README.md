# flight-deal-planner · 机票 + 假期规划器

> **EN** below each heading · **中文** follows it. Same content, both languages.

An [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) that plans a
year of travel around a country's public holidays: it scans **real fares**,
filters by **season** and **visa friction**, and outputs a dated plan —
*which holiday → which city → which flight → why → what to do there.*

一个 [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills)：围绕一个国家的公共假期，
扫描**真实票价**，再用**季节**和**签证摩擦度**过滤，最后产出一份带日期的计划：
*哪个假期 → 去哪个城市 → 买哪个航班 → 为什么 → 到那儿玩什么*。

It exists because "cheapest flight" and "trip worth taking" are different
questions. The cheapest fare in a spreadsheet is usually pointed at monsoon
season, or at a country whose visa takes three weeks.

做这个是因为「最便宜的机票」和「值得去的旅行」是两个问题。表格里最便宜的那张票，
通常要么指向雨季，要么指向一个签证要办三周的国家。

```
holiday calendar ──► windows ──► fare scan ──► season + visa filter ──► plan
假期日历         ──► 旅行窗口 ──► 扫价     ──► 季节 + 签证过滤    ──► 计划
```

![the web UI · 网页界面](examples/web-ui.png)

---

## Three ways to use it · 三种用法

### 1. In a browser, no CLI · 浏览器直接用，不用命令行

```bash
python3 web/server.py          # → http://127.0.0.1:8765
```

Pick origin, holiday calendar and year, tick the windows worth using, tick the
airports you'd consider, and press **Scan**. It returns a ranked table: fare,
baggage state, fare-with-a-20kg-bag, cost per night, and how the date compares
to the other windows you scanned. Right-click an airport to mark it *visited* so
it stops being suggested.

选出发地、假期日历和年份，勾上值得用的窗口，再勾上你愿意去的机场，点 **Scan**。
返回的是一张排序表：裸票价、行李状态、加 20kg 后的价格、每晚成本，以及这个日期
相对你本次扫描的其它窗口处在什么位置。**右键机场**可以标记「去过」，之后不再推荐。

Stdlib only — nothing to install beyond the two scraper dependencies.

后端只用 Python 标准库——除了两个抓取依赖之外不需要装任何东西。

### 2. As an agent skill · 作为 agent skill 使用

Drop the folder into your agent's skills directory (`~/.claude/skills/` or your
harness's equivalent) and ask it *"plan my 2027 holidays"*. It will collect the
profile in step 1 of `SKILL.md`, run the pipeline, and write the plan.

把整个目录放进你的 agent skills 目录（`~/.claude/skills/` 或你所用 harness 的等价位置），
然后说一句「帮我规划 2027 假期」。它会按 `SKILL.md` 第 1 步收集信息，跑完整条流水线，
再把计划写出来。

### 3. As a library or CLI · 作为库 / 命令行

```bash
python3 scripts/holidays.py --country SG --year 2027 --max-leave 3
python3 scripts/scan.py   --spec job.json
python3 scripts/rank.py   --fares data/fares.jsonl --config config.json
python3 scripts/report.py --summary data/summary.json --out report.md
```

---

## What it actually produces · 实际输出长什么样

A real scan, unfiltered. Bali, April 2027, three nights, one day of leave:

下面是真实抓取的结果，未经修饰。巴厘岛，2027 年 4 月，三晚，请一天假：

```
### 2027-04-09 → 2027-04-12
Bali DPS · Scoot TR282 16:05→19:00 (2h55) · S$178 round trip ·
carry-on only, +S$38 for 20kg → S$216 · S$72/night ·
lowest of the 36 windows scanned for this route
```

And the same week in Bangkok — where the full-service fare beats the low-cost one:

同一周换到曼谷——这张全服务航司的票反而比廉航便宜：

```
### 2027-01-29 → 2027-02-01
Bangkok BKK · Singapore Airlines · S$276 round trip, 30kg checked included ·
S$92/night · Scoot on the same dates is S$400, so the sale flips the ranking
```

`scripts/report.py` emits the factual skeleton with a `_fill in by hand_` marker;
the *why* and the *what to do* are written by the agent from
`references/seasonality.md`. A generated example is in
[`examples/example-report.md`](examples/example-report.md).

`scripts/report.py` 只输出事实骨架，末尾固定一行 `_fill in by hand_`；
「为什么去」和「玩什么」由 agent 参照 `references/seasonality.md` 来写。
一份生成好的样例在 [`examples/example-report.md`](examples/example-report.md)。

---

## Holiday calendars · 内置假期日历

| Code 代码 | Coverage 覆盖范围 | Confidence 可信度 |
|---|---|---|
| `SG` | Singapore 2026, 2027 · 新加坡 | **official 官方**（MOM） |
| `HK` | Hong Kong 2027 · 香港 | **official 官方**（gov.hk gazetted · 宪报） |
| `JP` | Japan, any year · 日本，任意年 | rule-based 规则推算 — equinox ±1 day · 春秋分 ±1 天 |
| `AU` | Australia, any year · 澳洲 | rule-based — national only 仅全国假日 |
| `US` | United States, any year · 美国 | rule-based — federal only 仅联邦假日，含 observed 顺延 |
| `CN` | mainland China · 中国内地 | fixed dates only 仅固定日期 — **lunar festivals omitted 不含农历节** |
| `KR` | South Korea · 韩国 | fixed dates only — **Seollal and Chuseok omitted 不含春节/秋夕** |
| `MY` | Malaysia · 马来西亚 | fixed dates only — **state and Islamic holidays omitted 不含州/伊斯兰节** |

Anything not rated `official` prints a warning, because a wrong holiday date
produces a confidently wrong plan. For full coverage of any country:

凡是可信度不是 `official` 的，命令行都会打印警告——因为假日日期错一天，整个计划就会
错得很自信。要给任何国家补全：

```bash
python3 scripts/holidays.py --file my-holidays.csv --year 2027
# my-holidays.csv:  2027-01-01,New Year
```

---

## What it does · 它做什么

- **Finds the leave arbitrage.** For each holiday it computes what 1, 2 or 3
  days of annual leave actually buy, with a leave-efficiency ratio, anchored on
  that holiday — not on whichever block elsewhere in the year happens to be
  longest.

  **算「请假性价比」。** 对每个假期算出请 1 / 2 / 3 天年假分别能换到几天连休，
  并给出效率倍数。关键是**锚定在这个假期上**，而不是去挑全年最长的那一段。

- **Scans real prices**, not estimates — Google Flights, via its server-rendered
  result page.

  **扫真实价格**，不是估算——直接解析 Google Flights 服务端渲染的结果页。

- **Refuses the trap.** Cheapest fares cluster in each destination's worst
  month. Season is a filter, not a tiebreak.

  **拒绝低价陷阱。** 最便宜的票价往往集中在目的地最差的月份。季节是**过滤器**，
  不是平手时的加分项。

- **Compares fairly.** Cost per night, not absolute fare, when trip lengths
  differ. Route percentile, not "lowest ever".

  **公平比较。** 行程长度不同时比「每晚成本」而不是绝对票价；比的是「该航线的分位」，
  不是「史上最低」。

- **Annotates baggage on every price**, because a carry-on fare and a
  with-a-suitcase fare often reverse the ranking.

  **每个价格都标注行李状态**，因为「只带手提」和「带箱子」两种口径经常把排名反过来。

## What it does not do · 它不做什么

- It does not book. It produces a plan with links.
  不负责订票。产出的是带链接的计划。

- It does not claim historical lows. The "route percentile" is cross-sectional
  across the windows it scanned, and says so.
  不声称历史低位。所谓「航线分位」是本次扫描各窗口的横向排名，界面上也这么写。

- It does not trust one source. Shortlisted routes get a second check.
  不只信一个数据源。进入候选清单的航线会做二次核对。

---

## Install · 安装

```bash
git clone <this repo> flight-deal-planner
cd flight-deal-planner
pip install -r scripts/requirements.txt
```

Python 3.9+.

---

## Repo layout · 目录结构

```
SKILL.md                        the method (what the agent executes) · 方法论，agent 执行这个
web/server.py                   local web UI, stdlib only · 本地网页，纯标准库
web/index.html                  single-page front end · 单页前端
references/seasonality.md       month × region table + monsoon asymmetries · 月份×区域气候表
references/visa-and-entry.md    entry-friction framework + worked example · 入境摩擦框架
references/fares-and-baggage.md fare brands, baggage economics · 票价品牌与行李经济
scripts/gf.py                   Google Flights fetch + parse · 抓取与解析
scripts/holidays.py             8 calendars + leave optimiser · 8 套日历 + 请假优化
scripts/scan.py                 batch scanner, resumable · 批量扫描，可断点续跑
scripts/rank.py                 scoring and bucketing · 打分与分级
scripts/report.py               Markdown brief skeleton · 报告骨架
assets/                         destination catalogue, example profile/job/config · 机场目录与示例配置
examples/                       a real generated report + UI screenshot · 真实报告与界面截图
```

---

## How fare scanning works · 扫价是怎么实现的

`scripts/gf.py` builds Google Flights' `?tfs=` protobuf parameter (via
`fast-flights`), fetches the page, and parses the server-rendered result cards.
The plain `?q=` URL returns an empty shell, which is why this parameter matters.

`scripts/gf.py` 会构造 Google Flights 的 `?tfs=` protobuf 参数（借助 `fast-flights`），
抓取页面，再解析服务端渲染出来的结果卡片。直接用 `?q=` 的 URL 只会拿到一个空壳页面，
所以这个参数是必须的。

Known limits, all documented in `SKILL.md` §8:

已知限制（`SKILL.md` 第 8 节有完整说明）：

- the result list is **outbound-only** — a round-trip price shows outbound
  options paired with the cheapest acceptable return
  结果列表**只有去程**——往返价展示的是「去程班次 + 系统挑的最便宜返程」的组合

- the list is **capped**; cells with fewer than five rows are marked unreliable
  列表**有条数上限**；少于 5 行的格子会被标记为样本不足

- **one-way ≠ half a round trip** on full-service carriers — a round-trip promo
  can be cheaper than a one-way
  全服务航司**单程 ≠ 往返的一半**——往返促销价可能比单程还便宜

- booking horizon is ~330 days; further out returns nothing
  可订窗口约 **330 天**，再远的日期查不到任何结果

---

## Caveats · 注意事项

Fares are snapshots and low-cost inventory moves within hours. Baggage fees are
estimates in the ranges given; the booking page is authoritative. Entry rules
change and `references/visa-and-entry.md` is a framework with one worked
example, not legal advice. Nothing here is a price guarantee.

票价是快照，廉航库存几个小时内就会变。行李费给的是区间估算，以订票页为准。
入境规则会变，`references/visa-and-entry.md` 只是一套框架加一个实例，不构成法律建议。
这里的一切都不构成价格承诺。

## License · 许可

MIT — see `LICENSE` · 详见 `LICENSE`
