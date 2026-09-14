#!/usr/bin/env python3
"""
MIRR / IRR / NPV / PV / Payback Period Calculator

Calculates financial metrics for a series of cash flows:
- MIRR (Modified Internal Rate of Return)
- IRR (Internal Rate of Return)
- NPV (Net Present Value)
- PV (Present Value)
- Payback Period

Formula:
    MIRR = (FV_positive / PV_negative)^(1/(n-1)) - 1

Usage:
    python mirr_calculator.py -300 23 44 24 67 88 44 33 77 88 -f 7.5% -r 0.75% --all
    python mirr_calculator.py -300 23 44 24 67 88 44 33 77 88 -f 7.5 -r 0.75
    python mirr_calculator.py

Options:
    -f, --finance-rate   Discount rate for negative cash flows (default: 10%)
    -r, --reinvest-rate  Reinvestment rate for positive cash flows (default: 10%)
    -d, --discount-rate  Discount rate for NPV/PV calculations (default: same as finance rate)
    --all                Calculate all metrics (MIRR, IRR, NPV, PV, Payback)
    --help               Show this help message
"""

import sys
import math
import re
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


def print_results(data: dict) -> None:
    """Print the calculation results."""
    cash_flows = data["cash_flows"]
    finance_rate = data["finance_rate"]
    reinvest_rate = data["reinvest_rate"]
    discount_rate = data["discount_rate"]
    all_metrics = data["all_metrics"]

    mirr = calculate_mirr(cash_flows, finance_rate, reinvest_rate)
    irr = calculate_irr(cash_flows)
    npv_value = npv(cash_flows, discount_rate)
    pv_value = calculate_pv(cash_flows, discount_rate)
    payback = calculate_payback_period(cash_flows)

    n = len(cash_flows)
    pv_negative = sum(abs(cf) / ((1 + finance_rate) ** i)
                      for i, cf in enumerate(cash_flows) if cf < 0)
    fv_positive = sum(cf * ((1 + reinvest_rate) ** (n - 1 - i))
                      for i, cf in enumerate(cash_flows) if cf > 0)

    print("\n" + "=" * 50)
    print("       FINANCE CALCULATION RESULTS")
    print("=" * 50)
    print(f"\nCash flows: {cash_flows}")
    print(f"Finance rate:  {finance_rate * 100:.2f}%")
    print(f"Reinvest rate: {reinvest_rate * 100:.2f}%")
    print(f"Discount rate: {discount_rate * 100:.2f}%")

    print("\n--- Metrics ---")
    print(f"MIRR:   {mirr * 100:.4f}%")
    print(f"IRR:    {irr * 100:.4f}%")
    print(f"NPV:    {npv_value:.4f}")
    print(f"PV:     {pv_value:.4f}")
    if payback is None:
        print("Payback: Never")
    else:
        print(f"Payback: {payback:.2f} years")

    print("\n--- MIRR Breakdown ---")
    print(f"PV of negative cash flows: {pv_negative:.4f}")
    print(f"FV of positive cash flows: {fv_positive:.4f}")
    print(f"Formula: (FV_positive / PV_negative)^(1/{n-1}) - 1")
    print(f"         = ({fv_positive:.4f} / {pv_negative:.4f})^(1/{n-1}) - 1")

    print("\n--- NPV Breakdown ---")
    print(f"Formula: Σ(CF_i / (1 + discount_rate)^i)")
    print(f"         = {npv_value:.4f}")

    print("\n" + "=" * 50)


def interactive_input() -> dict:
    """Prompt the user interactively for cash flows and rates."""
    print("=" * 50)
    print("       FINANCE CALCULATOR - Interactive Mode")
    print("=" * 50)

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
    print("1. All metrics (MIRR, IRR, NPV, PV, Payback) - default")
    print("2. MIRR only")
    print("3. IRR only")
    print("4. NPV only")
    print("5. PV only")
    print("6. Payback only")
    choice = input("Select option (1-6, default 1): ").strip()

    return {
        "cash_flows": cash_flows,
        "finance_rate": finance_rate,
        "reinvest_rate": reinvest_rate,
        "discount_rate": discount_rate,
        "all_metrics": choice == "1",
        "metrics": {
            "1": all_metrics,
            "2": "mirr",
            "3": "irr",
            "4": "npv",
            "5": "pv",
            "6": "payback",
        }.get(choice, "mirr") if choice in {"2", "3", "4", "5", "6"} else all_metrics,
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
