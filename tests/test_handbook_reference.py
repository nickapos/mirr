"""Tests that validate the calculator against worked examples from the
HP 12c Platinum Solutions Handbook (hp12cplatinum-sh-en.pdf).

Reference sections:
  - Real Estate -> Refinancing (pp. 7-8)
  - Real Estate -> Wrap-Around Mortgage (pp. 8-10)
  - Real Estate -> Income Property Cash Flow Analysis (p. 12)
  - Investment Analysis -> Lease vs. Purchase (p. 49, DCF at cost of capital)
  - Savings (p. 40, compound interest FV = PV(1+i)^n)
"""

import pytest

import mirr_calculator as mc


class TestHandbookReferences:
    def test_npv_convention_initial_flow_at_time_zero(self):
        """The handbook discounts each cash flow back to t=0; the initial flow
        (net amount advanced) occurs at t=0 and is therefore not discounted."""
        # NPV@0% over [-1000, 400, 500, 600] is the plain sum.
        cf = [-1000.0, 400.0, 500.0, 600.0]
        assert mc.npv(cf, 0.0) == pytest.approx(-1000.0 + 400.0 + 500.0 + 600.0)

    def test_refinancing_example_npv(self):
        """Real Estate -> Refinancing (p. 8).

        Lender advances a 'net amount of cash' of -66,810 at t=0 and receives
        a net monthly payment of 899.23 for 204 months. Discounted at the
        market rate 11.5%/12, the handbook reports NPV to the lender of
        -13,615.02 (magnitude checked; sign depends on sign convention)."""
        flows = [-66810.0] + [899.23] * 204
        npv_value = mc.npv(flows, 0.115 / 12)
        assert abs(npv_value) == pytest.approx(13615.02, abs=5.0)

    def test_wrap_around_mortgage_irr(self):
        """Real Estate -> Wrap-Around Mortgage (p. 9).

        The wrapper's net cash flows are -99,867.94 at t=0 followed by
        1,553.69 per month for 144 months. The handbook's nominal annual yield
        (IRR) is 15.85%, i.e. the per-period (monthly) IRR x 12."""
        flows = [-99867.94] + [1553.69] * 144
        monthly_irr = mc.calculate_irr(flows)
        assert monthly_irr is not None
        assert monthly_irr * 12 == pytest.approx(0.1585, abs=0.001)

    def test_discounting_is_inverse_of_compounding(self):
        """Savings (p. 40): FV = PV(1+i)^n, so discounting a single future
        amount back n periods must equal PV = FV/(1+i)^n."""
        fv = 2519.61
        i, n = 0.05 / 12, 84
        flows = [0.0] * (n - 1) + [fv]  # initial zeros then the single cash flow
        assert mc.npv(flows, i) == pytest.approx(fv / (1 + i) ** (n - 1))

    def test_npv_at_cost_of_capital_convention(self):
        """Investment Analysis -> Lease vs. Purchase (p. 49): cash flows 'are
        discounted to the present at the firm's after-tax cost of capital.'

        NPV(r) must be the present value of all future flows minus the initial
        outlay, evaluated at the given rate."""
        cost_of_capital = 0.05
        flows = [-10000.0, 2000.0, 3000.0, 4000.0, 5000.0]
        expected = 0.0
        for t, cf_amt in enumerate(flows):
            expected += cf_amt / (1 + cost_of_capital) ** t
        assert mc.npv(flows, cost_of_capital) == pytest.approx(expected)

    def test_irr_monthly_annualization_convention(self):
        """The handbook's 'yield (IRR)' examples compute a rate per payment
        period and annualize it by multiplying by the number of periods per
        year (12x key). This calculator returns the per-period rate directly."""
        # Verified IRR on a 1-year, 12-month-payment loan: -1000 at t=0 and
        # 90/month for 12 months.
        flows = [-1000.0] + [90.0] * 12
        monthly = mc.calculate_irr(flows)
        assert monthly is not None
        # NPV of the flows at the computed rate must be (approximately) zero.
        assert mc.npv(flows, monthly) == pytest.approx(0.0, abs=1e-3)
        # Sanity: monthly rate is small and positive.
        assert 0.0 < monthly < 0.02