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
    python mirr_calculator.py -300 23 44 24 67 88 44 33 77 88 -f 7.5 -r 0.75 --sensitivity
    python mirr_calculator.py -300 23 44 24 67 88 44 33 77 88 -f 10% --scenario
    python mirr_calculator.py -300 23 44 24 67 88 44 33 77 88 -f 10% --breakeven
    python mirr_calculator.py

Options:
    -f, --finance-rate   Discount rate for negative cash flows (default: 10%)
    -r, --reinvest-rate  Reinvestment rate for positive cash flows (default: 10%)
    -d, --discount-rate  Discount rate for NPV/PV calculations (default: same as finance rate)
    --all                Calculate all metrics
    --sensitivity        Run sensitivity analysis on NPV/MIRR
    --scenario           Run scenario analysis (best/worst/base case)
    --breakeven          Calculate break-even discount rate
    --help               Show this help message
"""

import sys
import math
import re
from typing import List, Optional, Tuple


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


def parse_args(args: List[str]) -> dict:
    """
    Parse command line arguments.
    Returns dict with cash_flows, finance_rate, reinvest_rate, discount_rate, all.
    """
    finance_rate = 0.10
    reinvest_rate = 0.10
    discount_rate = None  # Will default to finance_rate
    cash_flows = []
    all_metrics = False
    sensitivity = False
    scenario = False
    breakeven = False

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
            # Try to parse as a cash flow
            try:
                cash_flows.append(parse_cash_flow(arg))
            except ValueError:
                raise ValueError(f"Invalid argument: {arg}. Must be a number or -f/-r flag")
            i += 1

    # Discount rate defaults to finance rate
    if discount_rate is None:
        discount_rate = finance_rate

    return {
        "cash_flows": cash_flows,
        "finance_rate": finance_rate,
        "reinvest_rate": reinvest_rate,
        "discount_rate": discount_rate,
        "all_metrics": all_metrics,
        "sensitivity": sensitivity,
        "scenario": scenario,
        "breakeven": breakeven,
    }


def npv(cash_flows: List[float], rate: float) -> float:
    """Calculate Net Present Value at given discount rate."""
    return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))


def calculate_mirr(cash_flows: List[float], finance_rate: float = 0.10,
                   reinvest_rate: float = 0.10) -> float:
    """Calculate the Modified Internal Rate of Return (MIRR)."""
    n = len(cash_flows)
    if n < 2:
        raise ValueError("Need at least 2 cash flows to calculate MIRR")
    if finance_rate < 0 or reinvest_rate < 0:
        raise ValueError("Rates must be non-negative")

    # PV of negative cash flows (discounted to period 0)
    pv_negative = sum(abs(cf) / ((1 + finance_rate) ** i)
                      for i, cf in enumerate(cash_flows) if cf < 0)

    # FV of positive cash flows (compounded to final period)
    fv_positive = sum(cf * ((1 + reinvest_rate) ** (n - 1 - i))
                      for i, cf in enumerate(cash_flows) if cf > 0)

    # MIRR formula
    mirr = (fv_positive / pv_negative) ** (1 / (n - 1)) - 1

    return mirr


def calculate_irr(cash_flows: List[float], tolerance: float = 0.0001,
                  max_iter: int = 1000) -> float:
    """
    Calculate Internal Rate of Return using Newton's method.
    IRR is the rate where NPV = 0.
    """
    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows to calculate IRR")

    def npv_rate(rate: float) -> float:
        return npv(cash_flows, rate)

    # Initial guess
    rate = 0.10
    for _ in range(max_iter):
        npv_value = npv_rate(rate)
        if abs(npv_value) < tolerance:
            return rate

        # Derivative of NPV with respect to rate
        derivative = sum(-i * cf / ((1 + rate) ** (i + 1))
                         for i, cf in enumerate(cash_flows) if i > 0)

        if abs(derivative) < 1e-12:
            break

        new_rate = rate - npv_value / derivative
        if not math.isfinite(new_rate) or new_rate < -1:
            # Newton's method failed; fall back to bisection
            rate = new_rate
            break

        rate = new_rate

    # Fallback to bisection method
    low, high = -0.9999, 10.0
    for _ in range(max_iter):
        mid = (low + high) / 2
        npv_value = npv_rate(mid)

        if abs(npv_value) < tolerance:
            return mid
        elif npv_value > 0:
            low = mid
        else:
            high = mid

    return (low + high) / 2


def calculate_pv(cash_flows: List[float], discount_rate: float) -> float:
    """Calculate Present Value of all cash flows."""
    return npv(cash_flows, discount_rate)


def calculate_payback_period(cash_flows: List[float]) -> Optional[float]:
    """Calculate Payback Period (in years) - time to recover initial investment."""
    cumulative = 0.0
    for i, cf in enumerate(cash_flows):
        cumulative += cf
        if cumulative >= 0:
            if i == 0:
                return 0.0
            prev_cumulative = cumulative - cf
            fraction = (0 - prev_cumulative) / cf if cf != 0 else 0.0
            return (i - 1) + fraction

    return None  # Never pays back


def calculate_discounted_payback_period(cash_flows: List[float], discount_rate: float) -> Optional[float]:
    """Calculate Discounted Payback Period (in years) - time to recover initial investment using discounted cash flows."""
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

    return None  # Never pays back


def calculate_profitability_index(cash_flows: List[float], discount_rate: float) -> float:
    """
    Calculate Profitability Index (PI) = PV of Future Cash Flows / Initial Investment
    Also known as Benefit-Cost Ratio
    """
    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows to calculate PI")
    
    initial_investment = abs(cash_flows[0]) if cash_flows[0] < 0 else 0
    if initial_investment == 0:
        # If no initial outflow, use the first negative cash flow as investment
        for cf in cash_flows:
            if cf < 0:
                initial_investment = abs(cf)
                break
    
    if initial_investment == 0:
        return float('inf')  # No investment required
    
    # PV of all cash flows except the initial investment
    pv_future_cflows = npv(cash_flows[1:], discount_rate) if len(cash_flows) > 1 else 0
    # Add back the initial investment (since NPV includes it as negative)
    pv_total = npv(cash_flows, discount_rate)
    pv_future_cflows = pv_total + initial_investment  # Because initial investment is negative in cash_flows[0]
    
    return pv_future_cflows / initial_investment


def calculate_roi(cash_flows: List[float]) -> float:
    """Calculate Return on Investment (ROI) = (Total Inflows - Initial Investment) / Initial Investment."""
    initial_investment = abs(cash_flows[0]) if cash_flows[0] < 0 else 0
    if initial_investment == 0:
        for cf in cash_flows:
            if cf < 0:
                initial_investment = abs(cf)
                break
    if initial_investment == 0:
        return float('inf')
    total_inflows = sum(cf for cf in cash_flows if cf > 0)
    return (total_inflows - initial_investment) / initial_investment


def calculate_eaa(cash_flows: List[float], discount_rate: float) -> Optional[float]:
    """Calculate Equivalent Annual Annuity (EAA) for comparing projects of different lifespans."""
    n = len(cash_flows)
    if n < 2:
        return None
    npv_value = npv(cash_flows, discount_rate)
    # EAA = NPV / Annuity Factor
    # Annuity Factor = (1 - (1+r)^(-n)) / r
    if discount_rate == 0:
        annuity_factor = n
    else:
        annuity_factor = (1 - (1 + discount_rate) ** (-n)) / discount_rate
    if annuity_factor == 0:
        return None
    return npv_value / annuity_factor


def find_break_even_rate(cash_flows: List[float], tolerance: float = 0.0001) -> Optional[float]:
    """Find the discount rate where NPV = 0 (break-even rate)."""
    def npv_at_rate(rate: float) -> float:
        return npv(cash_flows, rate)

    low, high = -0.9999, 10.0
    for _ in range(1000):
        mid = (low + high) / 2
        npv_value = npv_at_rate(mid)
        if abs(npv_value) < tolerance:
            return mid
        elif npv_value > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def run_sensitivity_analysis(cash_flows: List[float], base_discount_rate: float) -> List[dict]:
    """Run sensitivity analysis showing NPV and MIRR at different discount rates."""
    results = []
    rates = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.075, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]
    for rate in rates:
        npv_val = npv(cash_flows, rate)
        mirr_val = calculate_mirr(cash_flows, finance_rate=rate, reinvest_rate=rate)
        results.append({"rate": rate, "npv": npv_val, "mirr": mirr_val})
    return results


def run_scenario_analysis(cash_flows: List[float], discount_rate: float) -> dict:
    """Run scenario analysis: best case, worst case, base case."""
    # Base case is the original cash flows
    base_npv = npv(cash_flows, discount_rate)
    base_irr = calculate_irr(cash_flows)

    # Best case: scale positive cash flows up by 20%
    best_case = cash_flows.copy()
    for i in range(len(best_case)):
        if best_case[i] > 0:
            best_case[i] *= 1.2
    best_npv = npv(best_case, discount_rate)
    best_irr = calculate_irr(best_case)

    # Worst case: scale positive cash flows down by 20%
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
    """Print the calculation results."""
    cash_flows = data["cash_flows"]
    finance_rate = data["finance_rate"]
    reinvest_rate = data["reinvest_rate"]
    discount_rate = data["discount_rate"]
    all_metrics = data["all_metrics"]
    sensitivity = data["sensitivity"]
    scenario = data["scenario"]
    breakeven = data["breakeven"]

    mirr = calculate_mirr(cash_flows, finance_rate, reinvest_rate)
    irr = calculate_irr(cash_flows)
    npv_value = npv(cash_flows, discount_rate)
    pv_value = calculate_pv(cash_flows, discount_rate)
    payback = calculate_payback_period(cash_flows)
    discounted_payback = calculate_discounted_payback_period(cash_flows, discount_rate)
    profitability_index = calculate_profitability_index(cash_flows, discount_rate)
    roi = calculate_roi(cash_flows)
    eaa = calculate_eaa(cash_flows, discount_rate)

    n = len(cash_flows)
    pv_negative = sum(abs(cf) / ((1 + finance_rate) ** i)
                      for i, cf in enumerate(cash_flows) if cf < 0)
    fv_positive = sum(cf * ((1 + reinvest_rate) ** (n - 1 - i))
                      for i, cf in enumerate(cash_flows) if cf > 0)

    print("\n" + "=" * 60)
    print("       FINANCE CALCULATION RESULTS")
    print("=" * 60)
    print(f"\nCash flows: {cash_flows}")
    print(f"Finance rate:  {finance_rate * 100:.2f}%")
    print(f"Reinvest rate: {reinvest_rate * 100:.2f}%")
    print(f"Discount rate: {discount_rate * 100:.2f}%")

    print("\n--- Core Metrics ---")
    print(f"MIRR:      {mirr * 100:>8.4f}%")
    print(f"IRR:       {irr * 100:>8.4f}%")
    print(f"NPV:       {npv_value:>12.4f}")
    print(f"PV:        {pv_value:>12.4f}")
    if payback is None:
        print(f"Payback:   {'Never':>12}")
    else:
        print(f"Payback:   {payback:>12.2f} years")
    if discounted_payback is None:
        print(f"Disc. PB:  {'Never':>12}")
    else:
        print(f"Disc. PB:  {discounted_payback:>12.2f} years")
    print(f"Profitability Index: {profitability_index:>8.4f}")
    print(f"ROI:       {roi * 100:>8.4f}%")
    if eaa is not None:
        print(f"EAA:       {eaa:>12.4f}")
    else:
        print(f"EAA:       {'N/A':>12}")

    # Break-even rate
    if breakeven_rate := find_break_even_rate(cash_flows):
        print(f"\nBreak-even Discount Rate: {breakeven_rate * 100:.4f}%")
        if discount_rate < breakeven_rate:
            print(f"  → Current discount rate ({discount_rate*100:.2f}%) < breakeven ({breakeven_rate*100:.2f}%) → NPV > 0")
        else:
            print(f"  → Current discount rate ({discount_rate*100:.2f}%) > breakeven ({breakeven_rate*100:.2f}%) → NPV < 0")

    print("\n--- MIRR Breakdown ---")
    print(f"PV of negative cash flows: {pv_negative:.4f}")
    print(f"FV of positive cash flows: {fv_positive:.4f}")
    print(f"Formula: (FV_positive / PV_negative)^(1/{n-1}) - 1")
    print(f"         = ({fv_positive:.4f} / {pv_negative:.4f})^(1/{n-1}) - 1")

    print("\n--- NPV Breakdown ---")
    print(f"Formula: Σ(CF_i / (1 + discount_rate)^i)")
    print(f"         = {npv_value:.4f}")

    print("\n--- Profitability Index ---")
    initial_investment = abs(cash_flows[0]) if cash_flows[0] < 0 else 0
    if initial_investment == 0:
        for cf in cash_flows:
            if cf < 0:
                initial_investment = abs(cf)
                break
    print(f"Formula: PV of Future Cash Flows / Initial Investment")
    print(f"         = {npv_value + initial_investment:.4f} / {initial_investment:.4f}")
    print(f"         = {profitability_index:.4f}")
    if profitability_index > 1:
        print(f"         → Project creates value (PI > 1)")
    elif profitability_index == 1:
        print(f"         → Project breaks even (PI = 1)")
    else:
        print(f"         → Project destroys value (PI < 1)")

    print("\n--- Return on Investment (ROI) ---")
    print(f"Formula: (Total Inflows - Initial Investment) / Initial Investment")
    total_inflows = sum(cf for cf in cash_flows if cf > 0)
    print(f"         = ({total_inflows:.4f} - {initial_investment:.4f}) / {initial_investment:.4f}")
    print(f"         = {roi * 100:.4f}%")

    # EAA
    if eaa is not None:
        print("\n--- Equivalent Annual Annuity (EAA) ---")
        print(f"Formula: NPV / Annuity Factor")
        annuity_factor = (1 - (1 + discount_rate) ** (-n)) / discount_rate if discount_rate != 0 else n
        print(f"         = {npv_value:.4f} / {annuity_factor:.4f}")
        print(f"         = {eaa:.4f} per year")

    # Sensitivity Analysis
    if sensitivity or all_metrics:
        print("\n--- Sensitivity Analysis ---")
        print(f"{'Discount Rate':>14} | {'NPV':>12} | {'MIRR':>10}")
        print("-" * 40)
        sens_results = run_sensitivity_analysis(cash_flows, discount_rate)
        for r in sens_results:
            rate_pct = r["rate"] * 100
            print(f"{rate_pct:>13.1f}% | {r['npv']:>12.4f} | {r['mirr']*100:>9.4f}%")

    # Scenario Analysis
    if scenario or all_metrics:
        print("\n--- Scenario Analysis ---")
        scen_results = run_scenario_analysis(cash_flows, discount_rate)
        print(f"{'Scenario':>14} | {'NPV':>12} | {'IRR':>10}")
        print("-" * 40)
        for name, metrics in [("Base Case", scen_results["base"]), ("Best Case", scen_results["best"]), ("Worst Case", scen_results["worst"])]:
            print(f"{name:>14} | {metrics['npv']:>12.4f} | {metrics['irr']*100:>9.4f}%")

    print("\n" + "=" * 60)


def interactive_input() -> dict:
    """Prompt the user interactively for cash flows and rates."""
    print("=" * 60)
    print("       FINANCE CALCULATOR - Interactive Mode")
    print("=" * 60)

    print("\nEnter cash flows separated by spaces")
    print("(first value is typically the initial investment)")
    cf_input = input("Cash flows: ")
    try:
        cash_flows = [parse_cash_flow(x.strip()) for x in cf_input.replace(",", " ").split()]
        if len(cash_flows) < 2:
            raise ValueError
    except ValueError:
        raise ValueError("Please enter at least 2 numeric cash flows separated by spaces")

    finance_rate = 0.10
    reinvest_rate = 0.10
    discount_rate = None
    all_metrics = True

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
    choice = input("Select option (1-13, default 1): ").strip()

    return {
        "cash_flows": cash_flows,
        "finance_rate": finance_rate,
        "reinvest_rate": reinvest_rate,
        "discount_rate": discount_rate,
        "all_metrics": choice == "1",
        "sensitivity": choice == "12",
        "scenario": choice == "13",
        "breakeven": choice == "11",
        "metrics": {
            "1": all_metrics,
            "2": all_metrics,
            "3": "mirr",
            "4": "irr",
            "5": "npv",
            "6": "pv",
            "7": "payback",
            "8": "discounted_payback",
            "9": "profitability_index",
            "10": "roi",
            "11": "eaa",
            "12": "breakeven",
            "13": "sensitivity",
            "14": "scenario",
        }.get(choice, "mirr") if choice in {"2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"} else all_metrics,
    }


def main() -> None:
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        # No arguments - use interactive mode
        try:
            data = interactive_input()
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Parse arguments
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