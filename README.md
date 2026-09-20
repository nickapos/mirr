# MIRR / IRR / NPV / PV / Payback / PI / ROI / EAA Calculator

A command-line financial calculator for investment analysis. Given a series of cash
flows it computes a full suite of investment metrics — including the **Modified
Internal Rate of Return (MIRR)**, **Internal Rate of Return (IRR)**, **Net Present
Value (NPV)**, **Payback Period**, **Profitability Index**, **ROI**, **EAA**, plus
**break-even**, **sensitivity**, and **scenario** analyses.

| Metric | What it answers |
| ------ | --------------- |
| **MIRR** | What rate of return does the project earn, assuming positive cash flows are reinvested at a separate rate? |
| **IRR** | At what discount rate does the project break even (NPV = 0)? |
| **NPV** | How much value (in today's money) does the project create? |
| **PV** | Present value of the cash flow stream at the discount rate. |
| **Payback Period** | How many years until the cumulative cash inflows recover the initial investment? |
| **Discounted Payback** | Same as payback, but using discounted cash flows. |
| **Profitability Index (PI)** | Ratio of the PV of future cash flows to the initial investment. |
| **ROI** | Total return relative to the initial investment. |
| **EAA** | NPV expressed as an equivalent constant annual cash flow. |
| **Break-even rate** | The discount rate at which NPV = 0. |
| **Sensitivity** | How NPV and MIRR change across a range of discount rates. |
| **Scenario analysis** | Base / Best / Worst case NPV and IRR. |

---

## Features

- Calculate the full set of core metrics in a single run, or pick individual ones.
- Custom **finance rate** (for negative cash flows) and **reinvestment rate**
  (for positive cash flows), so MIRR properly models real-world reinvestment.
- Flexible **rate parsing** — enter `7.5%`, `0.075`, or `7.5` (they all mean 7.5%).
- Read cash flows from the command line, or from **CSV, JSON, or plain-text files**
  (including the `@filename` shortcut and the `-i/--input` flag).
- **Interactive mode** — run with no arguments for a guided, prompt-driven session.
- Multi-IRR awareness: warns when a cash-flow series changes sign more than once.
- Cross-checked against worked examples from the **HP 12c Platinum Solutions
  Handbook** (`hp12cplatinum-sh-en.pdf`, plain-text extract in `hp12c_manual.txt`).
- 100% pure Python standard library — no third-party dependencies.

---

## Requirements

- Python 3.7+ (uses `typing`, f-strings, `math`, `json`, `csv` — all stdlib).
- No third-party packages required.

## Installation

Clone the repository and you are ready to go:

```bash
git clone <repo-url> mirr
cd mirr
python3 mirr_calculator.py --help
```

Optionally run the tests:

```bash
python3 -m pytest tests/ -q
```

---

## Quick start

Evaluate a project that costs **$1,000** today (`-1000` at time 0) and then pays
**$400, $500, $600** in years 1–3, with a 10% finance rate and 12% reinvestment rate:

```bash
python3 mirr_calculator.py -1000 400 500 600 -f 10% -r 12%
```

Calculate **everything** (all metrics plus break-even, sensitivity, and scenario):

```bash
python3 mirr_calculator.py -1000 400 500 600 -f 10% -r 12% --all
```

Read cash flows from a file:

```bash
python3 mirr_calculator.py -i cashflows.csv -f 7.5% -r 0.75% --all
```

Interactive (prompt-driven) session:

```bash
python3 mirr_calculator.py
```

### Example output

```
============================================================
       FINANCE CALCULATION RESULTS
============================================================

Cash flows: [-1000.0, 400.0, 500.0, 600.0]
Finance rate:  10.00%
Reinvest rate: 12.00%
Discount rate: 10.00%

--- Core Metrics ---
MIRR:       18.4466%
IRR:        21.6478%
NPV:           227.6484
PV:            227.6484
Payback:           2.17 years
Disc. PB:          2.50 years
Profitability Index:   1.2276
ROI:        50.0000%
EAA:            71.8164

--- MIRR Breakdown ---
PV of negative cash flows: 1000.0000
FV of positive cash flows: 1661.7600
Formula: (FV_positive / PV_negative)^(1/3) - 1
         = (1661.7600 / 1000.0000)^(1/3) - 1
...
```

---

## Command-line reference

```
python3 mirr_calculator.py [-f RATE] [-r RATE] [-d RATE] [-i FILE]
                           [--sensitivity] [--scenario] [--breakeven]
                           [--all] [--help]
                           [CASH_FLOW...] [@FILE]
```

### Options

| Option | Description | Default |
| ------ | ----------- | ------- |
| `-f`, `--finance-rate` | Discount rate applied to **negative** cash flows (for MIRR). | `10%` |
| `-r`, `--reinvest-rate` | Reinvestment rate applied to **positive** cash flows (for MIRR). | `10%` |
| `-d`, `--discount-rate` | Discount rate used for NPV / PV / discounted payback / PI / EAA calculations. | Same as finance rate |
| `-i`, `--input FILE` | Read cash flows from `FILE` (CSV, JSON, or plain text). | — |
| `--all` | Enable every metric: core metrics + break-even + sensitivity + scenario. | off |
| `--sensitivity` | Run sensitivity analysis of NPV and MIRR over discount rates 1%–15%. | off |
| `--scenario` | Run scenario analysis: base, best (+20% inflows), worst (−20% inflows). | off |
| `--breakeven` | Find the discount rate at which NPV = 0. | off |
| `--help` | Show the help message and exit. | — |

### Positional arguments

- **Cash flow values**: numbers entered directly, e.g. `-300 100 200`. The first
  value is conventionally the initial investment at time 0 (negative for an outlay).
- **`@FILE`**: shorthand for `-i FILE`, e.g. `python3 mirr_calculator.py @flows.txt`.

> **Note on metric gating:** without extra flags, the calculator prints the **core
> metrics** (MIRR, IRR, NPV, PV, Payback, Discounted Payback, PI, ROI, EAA).
> Use `--all` or the individual flags to see the additional analyses.

---

## Rate input format

Rates are parsed flexibly — the same rate can be written several ways:

| Input | Interpreted as |
| ----- | -------------- |
| `"10%"` | 10% (0.10) |
| `"10"` | 10% — a bare number **greater than 1** is treated as a percentage |
| `"7.5%"` | 7.5% (0.075) |
| `"7.5"` | 7.5% (bare value > 1) |
| `"0.075"` | 7.5% — a decimal **less than or equal to 1** is treated as a rate |
| `"0.75%"` | 0.75% (0.0075) — an explicit `%` always wins over the size heuristic |
| `"1%"` | 1% (0.01) |
| `"1"` | 100% (1.0) — bare `1` is `<= 1`, so it stays a decimal rate |
| `"0"` | 0% |

Rules of thumb:
1. An explicit `%` sign always converts the number to a fraction (`X%` → `X/100`).
2. Without a `%` sign, values **> 1** are assumed to be percentages; values
   **≤ 1** are assumed to already be decimal rates.
3. Surrounding whitespace is ignored.

---

## Cash-flow input

Cash flows can come from three sources:

### 1. Command-line arguments

```bash
python3 mirr_calculator.py -1000 400 500 600
```

Intermediate zeros are allowed. The first flow is typically the initial investment
at time 0.

### 2. Files (`-i` / `@`)

| Format | Example content |
| ------ | --------------- |
| **CSV** | one value per line, or comma-separated / space-separated values |
| **JSON** | `[-300, 100, 200]` or `{"cash_flows": [-300, 100, 200]}` |
| **Plain text** | newline-, space-, tab-, or comma-separated numbers |

Examples:

```bash
python3 mirr_calculator.py -i cashflows.csv --all
python3 mirr_calculator.py @flows.json --all
```

The bundled `cashflow.csv` is a ready-to-use sample file.

### 3. Interactive mode

Running the script with **no arguments** starts an interactive session that steps
you through the input:

1. Enter cash flows (space separated) **or** a filename to load — e.g. `data.csv`.
2. Enter the finance rate (default `10%`).
3. Enter the reinvestment rate (default `10%`).
4. Enter the discount rate (default: same as finance rate).
5. Choose a calculation set from a numbered menu:
   1. All metrics (default)
   2. Core metrics only
   3. MIRR only
   4. IRR only
   5. NPV only
   6. PV only
   7. Discounted Payback only
   8. Profitability Index only
   9. ROI only
   10. EAA only
   11. Break-even rate only
   12. Sensitivity analysis
   13. Scenario analysis

---

## Metrics and formulas

Conventions (matching the HP 12c Platinum Solutions Handbook):

- The **first cash flow occurs at time 0** and is **not discounted**.
- Cash flows are indexed `i = 0, 1, ..., n-1` where `n` is the total number of
  flows. Future flows are discounted by `1 / (1 + r)^i`.

### NPV  (Net Present Value)

```
NPV = Σ  CF_i / (1 + r)^i         for i = 0 .. n-1,  r = discount rate
```

### MIRR  (Modified Internal Rate of Return)

```
MIRR = ( FV_positive / PV_negative )^(1/(n-1)) − 1

where:
  PV_negative = Σ |CF_i| / (1 + finance_rate)^i      for negative CF_i
  FV_positive = Σ  CF_i  × (1 + reinvest_rate)^(n-1-i)  for positive CF_i
```

- Requires at least 2 cash flows, at least one negative flow, and at least one
  positive flow.
- Rates must be non-negative.

### IRR  (Internal Rate of Return)

- The rate `r` such that `NPV(r) = 0`.
- Computed with **Newton's method**, falling back to **bisection**.
- Returns `N/A` when the NPV does not change sign over the search range
  (no real IRR exists).
- If the cash-flow series changes sign more than once, multiple IRRs may exist —
  the calculator prints a warning that the reported IRR is only one of several.

### PV  (Present Value)

Same as NPV at the discount rate.

### Payback Period

- The number of periods until cumulative (undiscounted) cash flows turn non-negative.
- Fractional years are interpolated within the final period.
- Prints `Never` if the investment is never recovered.

### Discounted Payback Period

- Same as payback, but using cash flows discounted at the discount rate.

### Profitability Index (PI)

```
PI = PV of future cash flows / |initial investment|
```

- Requires at least one negative cash flow (the initial investment). Returns `N/A`
  otherwise.
- PI > 1 → value is created; PI = 1 → break even; PI < 1 → value is destroyed.

### ROI  (Return on Investment)

```
ROI = (total inflows − initial investment) / |initial investment|
```

- Requires at least one negative cash flow. Returns `N/A` otherwise.

### EAA  (Equivalent Annual Annuity)

```
EAA = NPV / annuity factor

annuity factor = (1 − (1 + r)^−n) / r      for r > 0
annuity factor = n                          for r = 0
```

- Converts an NPV into an equivalent constant annual cash flow, useful for
  comparing projects with different lifetimes.

### Break-even Discount Rate

- The discount rate at which `NPV = 0` (identical to IRR for conventional,
  single-sign-change cash flows).
- Returns `none found` if NPV never changes sign over the search range.
- Also reports whether the current discount rate sits above or below the break-even
  rate (and therefore whether NPV is negative or positive).

### Sensitivity Analysis

- Recomputes **NPV** and **MIRR** for discount rates from **1% to 15%**
  (including 7.5%), using the same rate for finance and reinvestment.
- Requires at least one negative and one positive cash flow; otherwise prints `N/A`.

### Scenario Analysis

- **Base case:** the cash flows as entered.
- **Best case:** all positive cash flows increased by **20%**.
- **Worst case:** all positive cash flows decreased by **20%**.
- Reports NPV and IRR for each scenario.

---

## Examples

A classic three-year project at 10% finance / 12% reinvest:

```bash
python3 mirr_calculator.py -1000 300 400 500 -f 10% -r 12%
# MIRR ≈ 9.82%, IRR ≈ 8.90%, NPV@10% ≈ -21.04
```

A small two-period project:

```bash
python3 mirr_calculator.py -100 60 60 -f 10% -r 10%
# MIRR = sqrt(126/100) − 1 ≈ 12.25%
```

Show the break-even rate and scenario analysis together:

```bash
python3 mirr_calculator.py -1000 400 500 600 --breakeven --scenario
```

Load flows from a JSON file and run the full analysis:

```bash
echo '{"cash_flows": [-300, 100, 200]}' > flows.json
python3 mirr_calculator.py -i flows.json --all
```

---

## Project layout

```
mirr_calculator.py          The calculator (CLI + library functions)
cashflow.csv                Sample comma/space-separated cash-flow file
hp12c_manual.txt            Plain-text extract of the HP 12c Solutions Handbook
hp12cplatinum-sh-en.pdf     Reference PDF (worked examples)
tests/
    conftest.py             Pytest bootstrap (adds repo root to sys.path)
    test_metrics.py         Unit tests for all metric functions
    test_parse.py           Tests for rate/cash-flow parsing and file input
    test_handbook_reference.py  Tests validated against HP 12c worked examples
```

## Testing

Run the full suite:

```bash
python3 -m pytest tests/ -q
```

The suite covers:

- **Parsing** — `parse_rate`, `parse_cash_flow`, `parse_args`, and file readers
  (CSV, JSON, plain text, error cases).
- **Metrics** — closed-form analytical checks plus hand-computed references for
  NPV, MIRR, IRR, payback, discounted payback, PI, ROI, EAA, break-even,
  and sign-change counting.
- **Handbook references** — worked examples from the HP 12c Platinum Solutions
  Handbook (refinancing NPV, wrap-around mortgage IRR, discounting/compounding
  inverse relationship, DCF at cost of capital, monthly IRR annualization).

---

## License

See the [LICENSE](LICENSE) file.
