#!/usr/bin/env python3
"""
MIRR / IRR / NPV / PV / Payback / Discounted Payback / PI / ROI / EAA / Sensitivity Calculator

Calculates financial metrics for a series of cash flows:
- MIRR (Modified Internal Rate of Return)
- IRR (Internal Rate of Return)
- NPV (Net Present Value)
- PV (Present Value)
- Payback Period
- Discounted Payback Period
- Profitability Index (PI)
- Return on Investment (ROI)
- Equivalent Annual Annuity (EAA)
- Sensitivity Analysis
- Break-even Discount Rate
- Scenario Analysis (Best/Worst/Base Case)

Formula:
    MIRR = (FV_positive / PV_negative)^(1/(n-1)) - 1

Usage:
    python mirr_calculator.py -300 23 44 24 67 88 44 33 77 88 -f 7.5% -r 0.75% --all
    python mirr_calculator.py -i cashflows.csv -f 7.5% -r 0.75% --all
    python mirr_calculator.py --help

Options:
    -f, --finance-rate   Discount rate for negative cash flows (default: 10%)
    -r, --reinvest-rate  Reinvestment rate for positive cash flows (default: 10%)
    -d, --discount-rate  Discount rate for NPV/PV calculations (default: same as finance rate)
    -i, --input FILE     Read cash flows from a file (CSV, JSON, or plain text)
    --all                Calculate all metrics
    --sensitivity        Run sensitivity analysis on NPV/MIRR
    --scenario           Run scenario analysis (best/worst/base case)
    --breakeven          Calculate break-even discount rate
    --help               Show this help message
"""

import sys
import math
import json
import csv
from typing import List, Optional


def parse_rate(value: str, option: str) -> float:
    """Parse a rate from input, accepting both percentage and decimal formats.

    Formats accepted:
    - "7.5" or "7.5%" -> 0.075 (7.5%)
    - "0.075" -> 0.075 (7.5%)
    - "0.75%" -> 0.0075 (0.75%)
    """
    value = value.strip()
    if not value:
        raise ValueError(f"{option} cannot be empty")

    # Check for percentage sign
    has_percent = value.endswith("%")
    if has_percent:
        value = value[:-1].strip()

    try:
        rate = float(value)
        if rate < 0:
            raise ValueError
    except ValueError:
        raise ValueError(f"{option} must be a number (e.g., 7.5% or 0.075)")

    # If percentage sign was present, convert to decimal
    if has_percent:
        return rate / 100.0

    # If value > 1, assume it's a percentage (e.g., 7.5 means 7.5%)
    # Otherwise assume it's already a decimal (e.g., 0.075)
    return rate / 100.0 if rate > 1 else rate


def parse_cash_flow(value: str) -> float:
    """Parse a cash flow value from input."""
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid cash flow: {value}")


def read_cash_flows_from_file(filename: str) -> List[float]:
    """Read cash flows from a file (CSV, JSON, or plain text).

    Supports:
    - CSV: One value per line, or comma-separated values
    - JSON: Array of numbers, e.g., [-300, 50, 10, 22]
    - Plain text: One value per line or space/comma-separated
    """
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        raise ValueError(f"File not found: {filename}")
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

    if not content:
        raise ValueError("File is empty")

    # Try JSON first
    if content.startswith('[') or content.startswith('{'):
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return [float(x) for x in data]
            elif isinstance(data, dict) and 'cash_flows' in data:
                return [float(x) for x in data['cash_flows']]
            else:
                raise ValueError("JSON must be an array or object with 'cash_flows' key")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    # Try CSV format
    if filename.endswith('.csv'):
        try:
            flows = []
            reader = csv.reader(content.splitlines())
            for row in reader:
                for val in row:
                    # A single field may contain space- or tab-separated numbers
                    for token in val.replace('\t', ' ').split():
                        if token:
                            flows.append(parse_cash_flow(token))
            if flows:
                return flows
        except ValueError as e:
            raise ValueError(f"Invalid value in CSV: {e}")
        except Exception as e:
            raise ValueError(f"Could not parse CSV: {e}")

    # Plain text: try comma-separated first, then space-separated
    if ',' in content:
        try:
            return [parse_cash_flow(x.strip()) for x in content.split(',') if x.strip()]
        except ValueError:
            pass

    # Space/newline separated
    try:
        return [parse_cash_flow(x.strip()) for x in content.replace('\n', ' ').replace('\t', ' ').split() if x.strip()]
    except ValueError:
        raise ValueError(f"Could not parse cash flows from file: {filename}")


def parse_args(args: List[str]) -> dict:
    """Parse command line arguments."""
    finance_rate = 0.10
    reinvest_rate = 0.10
    discount_rate = None
    cash_flows = []
    all_metrics = False
    sensitivity = False
    scenario = False
    breakeven = False
    input_file = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-f", "--finance-rate"):
            if i + 1 >= len(args):
                raise ValueError("-f/--finance-rate requires a value")
            finance_rate = parse_rate(args[i + 1], "Finance rate")
            i += 2
        elif arg in ("-r", "--reinvest-rate"):
            if i + 1 >= len(args):
                raise ValueError("-r/--reinvest-rate requires a value")
            reinvest_rate = parse_rate(args[i + 1], "Reinvestment rate")
            i += 2
        elif arg in ("-d", "--discount-rate"):
            if i + 1 >= len(args):
                raise ValueError("-d/--discount-rate requires a value")
            discount_rate = parse_rate(args[i + 1], "Discount rate")
            i += 2
        elif arg in ("-i", "--input"):
            if i + 1 >= len(args):
                raise ValueError("-i/--input requires a filename")
            input_file = args[i + 1]
            i += 2
        elif arg == "--all":
            all_metrics = True
            i += 1
        elif arg == "--sensitivity":
            sensitivity = True
            i += 1
        elif arg == "--scenario":
            scenario = True
            i += 1
        elif arg == "--breakeven":
            breakeven = True
            i += 1
        elif arg == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            # Treat as a cash flow or file path (if starts with @)
            if arg.startswith('@'):
                input_file = arg[1:]
                i += 1
            else:
                try:
                    cash_flows.append(parse_cash_flow(arg))
                except ValueError:
                    raise ValueError(f"Invalid argument: {arg}. Must be a number, -f/-r flag, or @filename")
                i += 1

    # If input file specified, read cash flows from file
    if input_file:
        file_flows = read_cash_flows_from_file(input_file)
        cash_flows.extend(file_flows)

    if discount_rate is None:
        discount_rate = finance_rate

    return {
        "cash_flows": cash_flows,
        "finance_rate": finance_rate,
        "reinvest_rate": reinvest_rate,
        "discount_rate": discount_rate,
        "metrics": {
            "mirr": True,
            "irr": True,
            "npv": True,
            "pv": True,
            "payback": True,
            "discounted_payback": True,
            "profitability_index": True,
            "roi": True,
            "eaa": True,
            "break_even": breakeven or all_metrics,
            "sensitivity": sensitivity or all_metrics,
            "scenario": scenario or all_metrics,
        },
    }


def npv(cash_flows: List[float], rate: float) -> float:
    """Calculate Net Present Value at given discount rate."""
    return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))


def count_sign_changes(cash_flows: List[float]) -> int:
    """Count how many times the sign of the cash flow series changes (zeros ignored)."""
    changes = 0
    prev_sign = 0
    for cf in cash_flows:
        sign = 1 if cf > 0 else (-1 if cf < 0 else 0)
        if sign == 0:
            continue
        if prev_sign != 0 and sign != prev_sign:
            changes += 1
        prev_sign = sign
    return changes


def calculate_mirr(cash_flows: List[float], finance_rate: float = 0.10,
                   reinvest_rate: float = 0.10) -> float:
    """Calculate MIRR."""
    n = len(cash_flows)
    if n < 2:
        raise ValueError("Need at least 2 cash flows")
    if finance_rate < 0 or reinvest_rate < 0:
        raise ValueError("Rates must be non-negative")
    if not any(cf < 0 for cf in cash_flows):
        raise ValueError("MIRR requires at least one negative cash flow (initial investment)")
    if not any(cf > 0 for cf in cash_flows):
        raise ValueError("MIRR requires at least one positive cash flow")

    pv_negative = sum(abs(cf) / ((1 + finance_rate) ** i)
                      for i, cf in enumerate(cash_flows) if cf < 0)
    fv_positive = sum(cf * ((1 + reinvest_rate) ** (n - 1 - i))
                      for i, cf in enumerate(cash_flows) if cf > 0)
    return (fv_positive / pv_negative) ** (1 / (n - 1)) - 1


def calculate_irr(cash_flows: List[float], tolerance: float = 0.0001,
                  max_iter: int = 1000) -> Optional[float]:
    """Calculate IRR using Newton's method with bisection fallback.

    Returns None if the NPV does not change sign over the search range
    (i.e., no IRR exists for these cash flows).
    """
    if len(cash_flows) < 2:
        return None

    def npv_rate(rate: float) -> float:
        return npv(cash_flows, rate)

    # Newton's method, starting from a reasonable guess
    rate = 0.10
    for _ in range(max_iter):
        npv_value = npv_rate(rate)
        if abs(npv_value) < tolerance:
            return rate
        derivative = sum(-i * cf / ((1 + rate) ** (i + 1))
                         for i, cf in enumerate(cash_flows) if i > 0)
        if abs(derivative) < 1e-12:
            break
        new_rate = rate - npv_value / derivative
        if not math.isfinite(new_rate) or new_rate < -1 or new_rate > 10.0:
            break
        rate = new_rate

    # Bisection fallback — only meaningful if NPV changes sign on the interval
    low, high = -0.9999, 10.0
    f_low = npv_rate(low)
    f_high = npv_rate(high)
    if (f_low > 0) == (f_high > 0):
        return None
    for _ in range(max_iter):
        mid = (low + high) / 2
        npv_value = npv_rate(mid)
        if abs(npv_value) < tolerance:
            return mid
        if (npv_value > 0) == (f_low > 0):
            low = mid
        else:
            high = mid
    return (low + high) / 2


def calculate_pv(cash_flows: List[float], discount_rate: float) -> float:
    """Calculate Present Value."""
    return npv(cash_flows, discount_rate)


def calculate_payback_period(cash_flows: List[float]) -> Optional[float]:
    """Calculate simple Payback Period."""
    cumulative = 0.0
    for i, cf in enumerate(cash_flows):
        cumulative += cf
        if cumulative >= 0:
            if i == 0:
                return 0.0
            prev_cumulative = cumulative - cf
            fraction = (0 - prev_cumulative) / cf if cf != 0 else 0.0
            return (i - 1) + fraction
    return None


def calculate_discounted_payback_period(cash_flows: List[float], discount_rate: float) -> Optional[float]:
    """Calculate Discounted Payback Period."""
    cumulative = 0.0
    for i, cf in enumerate(cash_flows):
        discounted_cf = cf / ((1 + discount_rate) ** i)
        cumulative += discounted_cf
        if cumulative >= 0:
            if i == 0:
                return 0.0
            prev_cumulative = cumulative - discounted_cf
            fraction = (0 - prev_cumulative) / discounted_cf if discounted_cf != 0 else 0.0
            return (i - 1) + fraction
    return None


def calculate_profitability_index(cash_flows: List[float], discount_rate: float) -> Optional[float]:
    """Calculate Profitability Index (PI).

    Returns None if no initial investment (negative cash flow) is present.
    """
    initial_investment = abs(cash_flows[0]) if cash_flows[0] < 0 else 0
    if initial_investment == 0:
        for cf in cash_flows:
            if cf < 0:
                initial_investment = abs(cf)
                break
    if initial_investment == 0:
        return None
    pv_future_cflows = npv(cash_flows, discount_rate) + initial_investment
    return pv_future_cflows / initial_investment


def calculate_roi(cash_flows: List[float]) -> Optional[float]:
    """Calculate ROI.

    Returns None if no initial investment (negative cash flow) is present.
    """
    initial_investment = abs(cash_flows[0]) if cash_flows[0] < 0 else 0
    if initial_investment == 0:
        for cf in cash_flows:
            if cf < 0:
                initial_investment = abs(cf)
                break
    if initial_investment == 0:
        return None
    total_inflows = sum(cf for cf in cash_flows if cf > 0)
    return (total_inflows - initial_investment) / initial_investment


def calculate_eaa(cash_flows: List[float], discount_rate: float) -> Optional[float]:
    """Calculate Equivalent Annual Annuity (EAA)."""
    n = len(cash_flows)
    if n < 2:
        return None
    npv_value = npv(cash_flows, discount_rate)
    if discount_rate == 0:
        annuity_factor = n
    else:
        annuity_factor = (1 - (1 + discount_rate) ** (-n)) / discount_rate
    if annuity_factor == 0:
        return None
    return npv_value / annuity_factor


def find_break_even_rate(cash_flows: List[float], tolerance: float = 0.0001) -> Optional[float]:
    """Find discount rate where NPV = 0.

    Returns None if NPV does not change sign over the search range.
    """
    if len(cash_flows) < 2:
        return None

    def npv_at_rate(rate: float) -> float:
        return npv(cash_flows, rate)

    low, high = -0.9999, 10.0
    f_low = npv_at_rate(low)
    f_high = npv_at_rate(high)
    if (f_low > 0) == (f_high > 0):
        return None
    for _ in range(1000):
        mid = (low + high) / 2
        npv_value = npv_at_rate(mid)
        if abs(npv_value) < tolerance:
            return mid
        if (npv_value > 0) == (f_low > 0):
            low = mid
        else:
            high = mid
    return (low + high) / 2


def run_sensitivity_analysis(cash_flows: List[float]) -> List[dict]:
    """Run sensitivity analysis over a range of discount rates.

    Returns an empty list if MIRR cannot be computed (all flows one sign).
    """
    results = []
    if not any(cf < 0 for cf in cash_flows) or not any(cf > 0 for cf in cash_flows):
        return results
    rates = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.075, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]
    for rate in rates:
        npv_val = npv(cash_flows, rate)
        mirr_val = calculate_mirr(cash_flows, finance_rate=rate, reinvest_rate=rate)
        results.append({"rate": rate, "npv": npv_val, "mirr": mirr_val})
    return results


def run_scenario_analysis(cash_flows: List[float], discount_rate: float) -> dict:
    """Run scenario analysis."""
    base_npv = npv(cash_flows, discount_rate)
    base_irr = calculate_irr(cash_flows)

    best_case = cash_flows.copy()
    for i in range(len(best_case)):
        if best_case[i] > 0:
            best_case[i] *= 1.2
    best_npv = npv(best_case, discount_rate)
    best_irr = calculate_irr(best_case)

    worst_case = cash_flows.copy()
    for i in range(len(worst_case)):
        if worst_case[i] > 0:
            worst_case[i] *= 0.8
    worst_npv = npv(worst_case, discount_rate)
    worst_irr = calculate_irr(worst_case)

    return {
        "base": {"npv": base_npv, "irr": base_irr},
        "best": {"npv": best_npv, "irr": best_irr},
        "worst": {"npv": worst_npv, "irr": worst_irr},
    }


def print_results(data: dict) -> None:
    """Print all calculation results, gated by the requested metrics."""
    cash_flows = data["cash_flows"]
    finance_rate = data["finance_rate"]
    reinvest_rate = data["reinvest_rate"]
    discount_rate = data["discount_rate"]
    metrics = data.get("metrics") or {}

    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows")

    def show(key: str, default: bool = False) -> bool:
        return metrics.get(key, default)

    n = len(cash_flows)

    print("\n" + "=" * 60)
    print("       FINANCE CALCULATION RESULTS")
    print("=" * 60)
    print(f"\nCash flows: {cash_flows}")
    print(f"Finance rate:  {finance_rate * 100:.2f}%")
    print(f"Reinvest rate: {reinvest_rate * 100:.2f}%")
    print(f"Discount rate: {discount_rate * 100:.2f}%")

    core_keys = ("mirr", "irr", "npv", "pv", "payback", "discounted_payback",
                 "profitability_index", "roi", "eaa")
    show_core = any(show(k) for k in core_keys)

    # Compute all metrics up front so sections can share the results.
    mirr = irr = None
    mirr_error = None
    if show("mirr"):
        try:
            mirr = calculate_mirr(cash_flows, finance_rate, reinvest_rate)
        except ValueError as e:
            mirr_error = e
    if show("irr"):
        irr = calculate_irr(cash_flows)
    npv_value = npv(cash_flows, discount_rate)
    payback = calculate_payback_period(cash_flows)
    discounted_payback = calculate_discounted_payback_period(cash_flows, discount_rate)
    profitability_index = calculate_profitability_index(cash_flows, discount_rate)
    roi = calculate_roi(cash_flows)
    eaa = calculate_eaa(cash_flows, discount_rate)

    pv_negative = sum(abs(cf) / ((1 + finance_rate) ** i)
                      for i, cf in enumerate(cash_flows) if cf < 0)
    fv_positive = sum(cf * ((1 + reinvest_rate) ** (n - 1 - i))
                      for i, cf in enumerate(cash_flows) if cf > 0)

    if show_core:
        print("\n--- Core Metrics ---")
        if show("mirr"):
            if mirr_error is not None:
                print(f"MIRR:      {'N/A':>12}  ({mirr_error})")
            else:
                print(f"MIRR:      {mirr * 100:>8.4f}%")
        if show("irr"):
            if irr is None:
                print(f"IRR:       {'N/A':>12}  (no sign change in NPV)")
            else:
                print(f"IRR:       {irr * 100:>8.4f}%")
        if show("npv"):
            print(f"NPV:       {npv_value:>12.4f}")
        if show("pv"):
            print(f"PV:        {npv_value:>12.4f}")
        if show("payback"):
            if payback is None:
                print(f"Payback:   {'Never':>12}")
            else:
                print(f"Payback:   {payback:>12.2f} years")
        if show("discounted_payback"):
            if discounted_payback is None:
                print(f"Disc. PB:  {'Never':>12}")
            else:
                print(f"Disc. PB:  {discounted_payback:>12.2f} years")
        if show("profitability_index"):
            if profitability_index is None:
                print(f"Profitability Index: {'N/A':>8}  (no initial investment)")
            else:
                print(f"Profitability Index: {profitability_index:>8.4f}")
        if show("roi"):
            if roi is None:
                print(f"ROI:       {'N/A':>8}  (no initial investment)")
            else:
                print(f"ROI:       {roi * 100:>8.4f}%")
        if show("eaa"):
            if eaa is None:
                print(f"EAA:       {'N/A':>12}")
            else:
                print(f"EAA:       {eaa:>12.4f}")

        if show("irr") and count_sign_changes(cash_flows) > 1:
            print("\nNote: cash flows change sign more than once, so multiple IRRs "
                  "may exist; the IRR above is only one of several.")

    if show("break_even"):
        breakeven_rate = find_break_even_rate(cash_flows)
        print("\nBreak-even Discount Rate: ", end="")
        if breakeven_rate is None:
            print("none found (NPV does not change sign)")
        else:
            print(f"{breakeven_rate * 100:.4f}%")
            if discount_rate < breakeven_rate:
                print(f"  → Current discount rate ({discount_rate*100:.2f}%) < breakeven ({breakeven_rate*100:.2f}%) → NPV > 0")
            else:
                print(f"  → Current discount rate ({discount_rate*100:.2f}%) > breakeven ({breakeven_rate*100:.2f}%) → NPV < 0")

    if show("mirr"):
        print("\n--- MIRR Breakdown ---")
        if mirr_error is None:
            print(f"PV of negative cash flows: {pv_negative:.4f}")
            print(f"FV of positive cash flows: {fv_positive:.4f}")
            print(f"Formula: (FV_positive / PV_negative)^(1/{n-1}) - 1")
            print(f"         = ({fv_positive:.4f} / {pv_negative:.4f})^(1/{n-1}) - 1")
        else:
            print(f"N/A ({mirr_error})")

    if show("npv"):
        print("\n--- NPV Breakdown ---")
        print(f"Formula: Σ(CF_i / (1 + discount_rate)^i)")
        print(f"         = {npv_value:.4f}")

    if show("profitability_index") and profitability_index is not None:
        initial_investment = abs(cash_flows[0]) if cash_flows[0] < 0 else 0
        if initial_investment == 0:
            for cf in cash_flows:
                if cf < 0:
                    initial_investment = abs(cf)
                    break
        print("\n--- Profitability Index ---")
        print(f"Formula: PV of Future Cash Flows / Initial Investment")
        print(f"         = {npv_value + initial_investment:.4f} / {initial_investment:.4f}")
        print(f"         = {profitability_index:.4f}")
        if profitability_index > 1:
            print(f"         → Project creates value (PI > 1)")
        elif profitability_index == 1:
            print(f"         → Project breaks even (PI = 1)")
        else:
            print(f"         → Project destroys value (PI < 1)")

    if show("roi") and roi is not None:
        initial_investment = abs(cash_flows[0]) if cash_flows[0] < 0 else 0
        if initial_investment == 0:
            for cf in cash_flows:
                if cf < 0:
                    initial_investment = abs(cf)
                    break
        print("\n--- Return on Investment (ROI) ---")
        print(f"Formula: (Total Inflows - Initial Investment) / Initial Investment")
        total_inflows = sum(cf for cf in cash_flows if cf > 0)
        print(f"         = ({total_inflows:.4f} - {initial_investment:.4f}) / {initial_investment:.4f}")
        print(f"         = {roi * 100:.4f}%")

    if show("eaa") and eaa is not None:
        print("\n--- Equivalent Annual Annuity (EAA) ---")
        print(f"Formula: NPV / Annuity Factor")
        annuity_factor = (1 - (1 + discount_rate) ** (-n)) / discount_rate if discount_rate != 0 else n
        print(f"         = {npv_value:.4f} / {annuity_factor:.4f}")
        print(f"         = {eaa:.4f} per year")

    if show("sensitivity"):
        print("\n--- Sensitivity Analysis ---")
        sens_results = run_sensitivity_analysis(cash_flows)
        if not sens_results:
            print("N/A — requires at least one negative and one positive cash flow")
        else:
            print(f"{'Discount Rate':>14} | {'NPV':>12} | {'MIRR':>10}")
            print("-" * 40)
            for r in sens_results:
                rate_pct = r["rate"] * 100
                print(f"{rate_pct:>13.1f}% | {r['npv']:>12.4f} | {r['mirr']*100:>9.4f}%")

    if show("scenario"):
        print("\n--- Scenario Analysis ---")
        scen_results = run_scenario_analysis(cash_flows, discount_rate)
        print(f"{'Scenario':>14} | {'NPV':>12} | {'IRR':>10}")
        print("-" * 40)
        for name, scen_metrics in [("Base Case", scen_results["base"]),
                                   ("Best Case", scen_results["best"]),
                                   ("Worst Case", scen_results["worst"])]:
            irr_val = scen_metrics["irr"]
            irr_str = "N/A" if irr_val is None else f"{irr_val * 100:>9.4f}%"
            print(f"{name:>14} | {scen_metrics['npv']:>12.4f} | {irr_str:>10}")

    print("\n" + "=" * 60)


def _metrics_for_choice(choice: str) -> dict:
    """Translate an interactive menu choice into a metrics selection dict."""
    keys = ("mirr", "irr", "npv", "pv", "payback", "discounted_payback",
            "profitability_index", "roi", "eaa",
            "break_even", "sensitivity", "scenario")
    metrics = {k: False for k in keys}

    core = ("mirr", "irr", "npv", "pv", "payback", "discounted_payback",
            "profitability_index", "roi", "eaa")
    only = {
        "3": "mirr",
        "4": "irr",
        "5": "npv",
        "6": "pv",
        "7": "discounted_payback",
        "8": "profitability_index",
        "9": "roi",
        "10": "eaa",
        "11": "break_even",
        "12": "sensitivity",
        "13": "scenario",
    }
    if choice == "1":
        for k in keys:
            metrics[k] = True
    elif choice == "2":
        for k in core:
            metrics[k] = True
    elif choice in only:
        metrics[only[choice]] = True
    else:
        for k in keys:
            metrics[k] = True
    return metrics


def interactive_input() -> dict:
    """Prompt the user interactively for cash flows and rates."""
    print("=" * 60)
    print("       FINANCE CALCULATOR - Interactive Mode")
    print("=" * 60)

    print("\nEnter cash flows separated by spaces")
    print("(first value is typically the initial investment)")
    print("Or enter a filename to read from (e.g., data.csv)")
    cf_input = input("Cash flows or filename: ").strip()

    # Check if input looks like a filename
    if cf_input and not cf_input.replace('.', '').replace('-', '').replace(' ', '').isdigit():
        # Try to read from file
        try:
            cash_flows = read_cash_flows_from_file(cf_input)
            print(f"Loaded {len(cash_flows)} cash flows from {cf_input}")
        except ValueError:
            # If file read fails, try parsing the input as cash flows
            try:
                cash_flows = [parse_cash_flow(x.strip()) for x in cf_input.replace(',', ' ').split()]
            except ValueError:
                raise ValueError(f"Could not read file '{cf_input}' and invalid cash flow format")
    else:
        try:
            cash_flows = [parse_cash_flow(x.strip()) for x in cf_input.replace(',', ' ').split()]
        except ValueError:
            raise ValueError("Please enter at least 2 numeric cash flows separated by spaces")
    if len(cash_flows) < 2:
        raise ValueError("Please enter at least 2 numeric cash flows separated by spaces")

    finance_rate = 0.10
    reinvest_rate = 0.10
    discount_rate = None

    print("\nEnter finance rate (discount rate for negative cash flows)")
    print("(enter as percentage like 7.5%, or decimal like 0.075, or press Enter for default 10%)")
    finance_input = input("Finance rate (default 10%): ").strip()
    if finance_input:
        finance_rate = parse_rate(finance_input, "Finance rate")

    print("\nEnter reinvestment rate (rate for positive cash flows)")
    print("(enter as percentage like 0.75%, or decimal like 0.0075, or press Enter for default 10%)")
    reinvest_input = input("Reinvestment rate (default 10%): ").strip()
    if reinvest_input:
        reinvest_rate = parse_rate(reinvest_input, "Reinvestment rate")

    print("\nEnter discount rate for NPV/PV calculations")
    print("(press Enter for default: same as finance rate)")
    discount_input = input("Discount rate (default same as finance rate): ").strip()
    if discount_input:
        discount_rate = parse_rate(discount_input, "Discount rate")
    else:
        discount_rate = finance_rate

    print("\nWhich calculations do you want?")
    print("1. All metrics (default)")
    print("2. Core metrics (MIRR, IRR, NPV, PV, Payback, Disc. Payback, PI, ROI, EAA)")
    print("3. MIRR only")
    print("4. IRR only")
    print("5. NPV only")
    print("6. PV only")
    print("7. Discounted Payback only")
    print("8. Profitability Index only")
    print("9. ROI only")
    print("10. EAA only")
    print("11. Break-even rate only")
    print("12. Sensitivity analysis")
    print("13. Scenario analysis")
    choice = input("Select option (1-13, default 1): ").strip() or "1"

    metrics = _metrics_for_choice(choice)

    return {
        "cash_flows": cash_flows,
        "finance_rate": finance_rate,
        "reinvest_rate": reinvest_rate,
        "discount_rate": discount_rate,
        "metrics": metrics,
    }


def main() -> None:
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        try:
            data = interactive_input()
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            data = parse_args(args)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if len(data["cash_flows"]) < 2:
            print("Error: Need at least 2 cash flows", file=sys.stderr)
            sys.exit(1)

    try:
        print_results(data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
