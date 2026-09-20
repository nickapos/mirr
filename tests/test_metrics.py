"""Tests for the core financial metric functions.

Expected values are either closed-form analytical results or hand-computed
references; several are cross-checked against the HP 12c Platinum Solutions
Handbook conventions in test_handbook_reference.py.
"""

import math

import pytest

import mirr_calculator as mc


# Sample project used across several tests: -1000, then +400/+500/+600.
CF = [-1000.0, 400.0, 500.0, 600.0]


# ---------------------------------------------------------------------------
# npv
# ---------------------------------------------------------------------------

class TestNpv:
    def test_initial_flow_undiscounted(self):
        # Handbook convention: CF0 happens at t=0 and is NOT discounted.
        assert mc.npv([-1000.0, 110.0], 0.10) == pytest.approx(-1000.0 + 100.0)

    def test_basic(self):
        assert mc.npv([100.0, 50.0, 50.0], 0.10) == pytest.approx(186.77686)

    def test_zero_rate_is_plain_sum(self):
        assert mc.npv([-100.0, 60.0, 60.0], 0.0) == pytest.approx(20.0)

    def test_sample_project_at_10_percent(self):
        assert mc.npv(CF, 0.10) == pytest.approx(227.6484, abs=1e-4)


# ---------------------------------------------------------------------------
# calculate_mirr
# ---------------------------------------------------------------------------

class TestMirr:
    def test_single_period_matches_irr(self):
        # MIRR([-100, 110], 10%, 10%) = (110/100)^(1/1) - 1 = 10%
        assert mc.calculate_mirr([-100.0, 110.0], 0.10, 0.10) == pytest.approx(0.10)

    def test_two_period_closed_form(self):
        # flows [-100, 60, 60], finance = reinvest = 10%
        # FV = 60*1.10 + 60 = 126, PV_neg = 100, n-1 = 2
        expected = math.sqrt(126.0 / 100.0) - 1.0
        assert mc.calculate_mirr([-100.0, 60.0, 60.0], 0.10, 0.10) == pytest.approx(expected)

    def test_classic_three_period_project(self):
        # flows [-1000, 300, 400, 500], finance 10%, reinvest 12%
        # FV = 300*1.12^2 + 400*1.12 + 500 = 1324.32 ; PV_neg = 1000 ; n-1 = 3
        expected = (1324.32 / 1000.0) ** (1 / 3) - 1.0
        assert mc.calculate_mirr([-1000.0, 300.0, 400.0, 500.0], 0.10, 0.12) == pytest.approx(expected)
        assert mc.calculate_mirr([-1000.0, 300.0, 400.0, 500.0], 0.10, 0.12) == pytest.approx(0.098157, abs=1e-4)

    def test_reinvestment_rate_raises_future_value(self):
        # With a higher reinvestment rate the MIRR must increase
        # (same finance rate).
        low = mc.calculate_mirr(CF, 0.10, 0.10)
        high = mc.calculate_mirr(CF, 0.10, 0.12)
        assert high > low

    def test_all_positive_raises(self):
        with pytest.raises(ValueError, match="negative cash flow"):
            mc.calculate_mirr([100.0, 50.0, 60.0], 0.10, 0.10)

    def test_all_negative_raises(self):
        with pytest.raises(ValueError, match="positive cash flow"):
            mc.calculate_mirr([-100.0, -50.0], 0.10, 0.10)

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            mc.calculate_mirr([-100.0], 0.10, 0.10)

    def test_negative_rates_raise(self):
        with pytest.raises(ValueError, match="non-negative"):
            mc.calculate_mirr([-100.0, 50.0], -0.1, 0.1)


# ---------------------------------------------------------------------------
# calculate_irr
# ---------------------------------------------------------------------------

class TestIrr:
    def test_single_period(self):
        assert mc.calculate_irr([-100.0, 110.0]) == pytest.approx(0.10)

    def test_two_period_closed_form(self):
        # [-100, 60, 60]: solve 60x^2 + 60x - 100 = 0 where x = 1/(1+r)
        # x = (sqrt(69) - 3) / 6  ->  r = 1/x - 1
        x = (math.sqrt(69.0) - 3.0) / 6.0
        expected = 1.0 / x - 1.0
        assert mc.calculate_irr([-100.0, 60.0, 60.0]) == pytest.approx(expected, abs=1e-4)

    def test_three_period_project(self):
        assert mc.calculate_irr([-1000.0, 300.0, 400.0, 500.0]) == pytest.approx(0.088963, abs=1e-4)

    def test_no_sign_change_returns_none(self):
        assert mc.calculate_irr([100.0, 50.0]) is None
        assert mc.calculate_irr([-100.0, -50.0]) is None

    def test_too_short_returns_none(self):
        assert mc.calculate_irr([-100.0]) is None

    def test_irr_makes_npv_zero(self):
        r = mc.calculate_irr(CF)
        assert mc.npv(CF, r) == pytest.approx(0.0, abs=1e-4)


# ---------------------------------------------------------------------------
# calculate_payback_period
# ---------------------------------------------------------------------------

class TestPayback:
    def test_basic(self):
        assert mc.calculate_payback_period([-1000.0, 300.0, 400.0, 500.0]) == pytest.approx(2.6)

    def test_immediate(self):
        assert mc.calculate_payback_period([100.0, -50.0]) == pytest.approx(0.0)

    def test_never_pays_back(self):
        assert mc.calculate_payback_period([-1000.0, 100.0, 100.0]) is None


# ---------------------------------------------------------------------------
# calculate_discounted_payback_period
# ---------------------------------------------------------------------------

class TestDiscountedPayback:
    def test_basic(self):
        # discounted: -100, 54.5455, 49.5868 -> recovers during period 2
        assert mc.calculate_discounted_payback_period([-100.0, 60.0, 60.0], 0.10) == pytest.approx(1.916667, abs=1e-4)

    def test_never_pays_back(self):
        assert mc.calculate_discounted_payback_period([-100.0, 50.0, 50.0], 0.10) is None


# ---------------------------------------------------------------------------
# calculate_profitability_index
# ---------------------------------------------------------------------------

class TestProfitabilityIndex:
    def test_basic(self):
        # PV of future flows @10% = 1227.6484 ; investment = 1000
        assert mc.calculate_profitability_index(CF, 0.10) == pytest.approx(1.227648, abs=1e-4)

    def test_no_investment_returns_none(self):
        assert mc.calculate_profitability_index([100.0, 50.0], 0.10) is None


# ---------------------------------------------------------------------------
# calculate_roi
# ---------------------------------------------------------------------------

class TestRoi:
    def test_basic(self):
        # (1500 - 1000) / 1000 = 50%
        assert mc.calculate_roi(CF) == pytest.approx(0.50)

    def test_no_investment_returns_none(self):
        assert mc.calculate_roi([100.0, 50.0]) is None


# ---------------------------------------------------------------------------
# calculate_eaa
# ---------------------------------------------------------------------------

class TestEaa:
    def test_basic(self):
        # NPV@10% = 227.6484 ; annuity factor (4 yr, 10%) = 3.1699
        assert mc.calculate_eaa(CF, 0.10) == pytest.approx(71.8164, abs=1e-3)

    def test_zero_discount_rate(self):
        # annuity factor = n = 4 ; NPV = -1000+400+500+600 = 500
        assert mc.calculate_eaa(CF, 0.0) == pytest.approx(500.0 / 4.0)

    def test_less_than_two_flows_returns_none(self):
        assert mc.calculate_eaa([-100.0], 0.10) is None


# ---------------------------------------------------------------------------
# find_break_even_rate
# ---------------------------------------------------------------------------

class TestBreakEven:
    def test_matches_irr_for_single_sign_change(self):
        # For conventional cash flows the break-even discount rate (NPV = 0)
        # is exactly the IRR.
        assert mc.find_break_even_rate(CF) == pytest.approx(mc.calculate_irr(CF))

    def test_none_when_npv_never_crosses_zero(self):
        assert mc.find_break_even_rate([100.0, 50.0]) is None

    def test_too_short_returns_none(self):
        assert mc.find_break_even_rate([-100.0]) is None


# ---------------------------------------------------------------------------
# count_sign_changes (multi-IRR detection)
# ---------------------------------------------------------------------------

class TestCountSignChanges:
    def test_basic(self):
        assert mc.count_sign_changes([-100.0, 50.0, -20.0, 60.0]) == 3
        assert mc.count_sign_changes([-100.0, 50.0, 50.0]) == 1

    def test_zeros_are_ignored(self):
        assert mc.count_sign_changes([0.0, -100.0, 50.0]) == 1
        assert mc.count_sign_changes([-100.0, 0.0, 50.0]) == 1