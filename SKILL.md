---
name: skill-a-share-pit-fundamental-vintage-builder
description: Use when building or auditing A-share financial-factor backtests that must avoid look-ahead bias from current or restated financial reports. Produces historical as-of financial datasets for rebalance dates and verifies whether factor/backtest inputs used only information tradable at the time.
---

# A-Share Financial Factor Backtest Anti-Lookahead Assistant

## Community Project Declaration

This is a QuantSkills Community Project, maintained by repository contributors. It is not an official, certified, validated, endorsed, or production-ready QuantSkills project. Its narrow scope is A-share formal-report PIT data construction and financial-input look-ahead auditing; it does not run generic factor performance backtests or provide investment advice.

Read [references/research-boundaries.md](references/research-boundaries.md) before any live-data run or publication. It defines the Panda Data source and entitlement boundary, the PIT assumptions and parameters, known limits, and research-only risk boundary. The machine-readable upstream declaration is in [skill.yml](skill.yml).

## Core Promise

Answer one quantitative-research question: **when the strategy rebalanced in the past, did its financial factor use only financial reports that were public and tradable then?**

Build a PIT financial-factor dataset when the answer is unknown. Audit an existing backtest when the user already has data and code. Do not use this Skill for latest-financial-report interpretation, stock recommendations, or generic company research.

## First Interaction

At the start of a new user session, first show the following user-facing entry. Do this before asking them to authenticate or opening a login terminal.

```text
这个 Skill 用来确认：你的 A 股财务因子回测，有没有偷看未来财报。

【1. 构建可信回测数据】
给我股票代码、回测期间和调仓频率。我会为每个调仓日还原当时可用的财报，再自动计算因子。
示例："为 000021.SZ 和 600519.SH 构建 2021-2025 年按月调仓的财务因子回测数据。"

【2. 审计已有回测】
给我财务面板、调仓日和因子/回测代码。我会检查修订财报泄漏、未来函数和缺失快照。
示例："审计 D:\data\panel.csv、D:\data\rebalance.csv 和 D:\strategy\factor.py。"

PIT 是这里的保护规则：每个历史调仓日只使用当时已公开、并在下一交易日可使用的财报。单季、TTM 和 ROA 等只是自动生成的回测因子，不是你需要先掌握的概念。
```

Ask the user to choose build or audit. Initiate the platform-specific login flow only before the first live Panda Data request. Do not ask the user to paste credentials into the conversation, log them, or include them in commands. If credentials have already been validated and can be resolved from the platform store, do not show a login window again unless the user asks to replace them or an authenticated request fails.

Route each request before taking action:

1. For build, confirm symbols, start/end period, and either a rebalance-date CSV or a frequency. For monthly rebalancing, generate month-end trading dates. Build PIT data, derive factors, and validate the result. Run the login flow only when no validated credentials are available.
2. For audit, request the factor-input panel, rebalance-date CSV, and Python factor/backtest files. A panel-only audit checks data timing but cannot prove the full strategy has no leakage. Do not require Panda Data login unless source-data cross-validation is requested.
3. Treat financial-version timelines as an advanced diagnostic, not a primary entry point.

Run the deterministic audit after collecting the files:

```powershell
python scripts/audit_backtest_input.py `
  --panel inputs/pit_factor_panel.csv `
  --rebalance-dates inputs/rebalance_dates.csv `
  --factor-code strategy/factor.py strategy/backtest.py `
  --output outputs/backtest_audit.json
```

The panel may contain multiple `as_of_date` partitions. The audit requires exactly one retained `(symbol, quarter)` vintage within each partition and requires every scheduled rebalance date to have a corresponding panel snapshot. It reports deterministic errors for `is_latest=True` and negative `shift`, while `bfill` and forward `merge_asof` remain warnings that require strategy-context review.

## PIT Convention

Use `panda_data.get_fina_reports(is_latest=False)` as the first-release source of truth. It retains multiple versions of a report period and exposes `quarter` plus `date`.

Build only a **formal-report** PIT layer. Forecasts and performance bulletins require separate historical-version validation before inclusion.

## Core Convention

For each research date `T` and report period `(symbol, quarter)`:

1. Fetch all retained report versions with `is_latest=False`.
2. Keep versions with `disclosure_date <= T`.
3. Map each disclosure to the next trading day. This conservative T+1 rule avoids assuming that an announcement was tradable during the same session.
4. Keep versions with `available_date <= T`.
5. Select the latest remaining version for each `(symbol, quarter)`.

Never call `is_latest=True` for a historical backtest input. It selects today's best-known version and can introduce restatement bias.

## Quick Start

After showing the first-interaction examples, open the interactive login terminal before the first live query. It masks the password, automatically prepends `86` when the account does not start with that prefix, validates the account and a small Panda Data request, saves validated credentials to the operating system's user credential store, and closes automatically three seconds after success. The success window tells the user to return to the Skill conversation and choose build or audit. Failed authentication or connectivity checks keep the window open for another attempt.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/open_panda_data_login.ps1
```

macOS:

```bash
bash scripts/open_panda_data_login_macos.sh
```

On Windows, credentials are saved in current-user environment variables. On macOS, they are saved in the login keychain. The builder accepts either `PANDA_DATA_*` or `PANDADATA_*` variable names and first reads the current process, then the platform-native saved values, so it works immediately after a successful login without restarting the original terminal. It never writes credentials to output.

```powershell
python scripts/build_pit_panel.py `
  --symbols 000001.SZ 600519.SH `
  --start-quarter 2021q1 `
  --end-quarter 2025q4 `
  --as-of-date 20240419 `
  --output outputs/pit_snapshot_20240419.csv

python scripts/validate_pit_panel.py outputs/pit_snapshot_20240419.csv
```

The builder chunks requests into no more than 20 quarters because that is the verified Panda Data limit. It writes a CSV and matching `.metadata.json` file.

## Batch Rebalance Workflow

For a backtest, use a CSV with a `rebalance_date` or `date` column in `YYYYMMDD` format. The builder fetches historical report versions once, then emits one PIT partition per rebalance date.

When the user asks for monthly rebalancing and has no schedule file, generate the monthly last-trading-day schedule first:

```powershell
python scripts/generate_rebalance_schedule.py `
  --start-date 20210101 `
  --end-date 20251231 `
  --output outputs/rebalance_month_end_2021_2025.csv
```

```powershell
python scripts/build_pit_panel.py `
  --symbols 000001.SZ 600519.SH `
  --start-quarter 2020q1 `
  --end-quarter 2025q4 `
  --as-of-dates inputs/rebalance_dates.csv `
  --output outputs/pit_rebalance_panel.csv
```

Convert the formal-report cumulative fields into single-quarter values, TTM values, and basic factors only after building the PIT long panel:

```powershell
python scripts/derive_fundamental_factors.py `
  --input outputs/pit_rebalance_panel.csv `
  --output outputs/pit_fundamental_factors.csv
```

Generate the user-facing summary after PIT audit and factor derivation. Use this Markdown report as the primary artifact in the final response; treat raw CSV files as supporting evidence.

```powershell
python scripts/generate_research_summary.py `
  --factors outputs/pit_fundamental_factors.csv `
  --audit outputs/backtest_audit.json `
  --pit-panel outputs/pit_rebalance_panel.csv `
  --schedule outputs/rebalance_month_end_2021_2025.csv `
  --output outputs/research_summary.md
```

The derivation runs independently inside each `(symbol, as_of_date)` partition. It never differences across a missing quarter, fiscal year boundary, or later PIT snapshot. Read [references/factor-definitions.md](references/factor-definitions.md) before interpreting the values.

## Delivery Contract

Lead every final response with a short, human-readable conclusion. Do not lead with CSV paths or raw row counts.

For a build, state:

1. Whether the dataset passed PIT validation and which historical period and rebalance schedule it covers.
2. The latest financial report actually available at the last rebalance date, so the user can see what was intentionally excluded.
3. A compact summary of 3-6 relevant derived factors for the requested securities, in plain language and human units.
4. Material limits, including that this prepares research data and is not an investment recommendation.
5. CSV, metadata, and audit-report links as supporting artifacts.

For an audit, lead with `可信` / `存在风险` / `无法确认`, list concrete violations first, then state which inputs were not supplied.

Every final panel must include:

Every final panel must include:

| Field | Meaning |
| --- | --- |
| `symbol` | Security identifier |
| `quarter` | Financial report period |
| `disclosure_date` | Date of the retained report version |
| `available_date` | First conservative usable trading day |
| `as_of_date` | Research cutoff date |
| `vintage_type` | `formal_report` in this release |

Keep requested financial fields alongside this lineage. Do not silently replace the above dates with report-period end dates.

## Supporting Workflow

Use the bundled scripts in this order: generate a schedule, build PIT snapshots, derive single-quarter/TTM factors, audit the final panel and strategy code, then generate a readable summary. Read [references/factor-definitions.md](references/factor-definitions.md) only when interpreting derived factors. Pair long-horizon research with a separate point-in-time universe/survivorship workflow.

## Known Limits

- `date` is a disclosure date, not an intraday timestamp. T+1 is deliberately conservative.
- The SDK currently lacks the documented `get_stock_disclosure_date`; do not depend on it.
- Formal-report schemas vary across financial and non-financial issuers. Missing fields are data, not zeros.
- If two different retained versions share a symbol, report period, and disclosure date, the builder fails instead of selecting an arbitrary row. Resolve the source ambiguity with a version identifier or timestamp before continuing.
- A PIT financial panel eliminates one class of look-ahead bias; it does not solve survivorship bias, corporate-action handling, execution costs, or model overfitting.

Read [references/data-contract.md](references/data-contract.md) before extending the data model or changing availability logic.
