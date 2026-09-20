"""Tests for rate/cash-flow parsing, argument parsing, and file input."""

import json

import pytest

import mirr_calculator as mc


# ---------------------------------------------------------------------------
# parse_rate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("7.5", 0.075),            # bare number > 1 is treated as a percentage
    ("7.5%", 0.075),           # explicit percent sign
    ("0.075", 0.075),          # bare decimal < 1 is treated as a decimal rate
    ("0.75%", 0.0075),         # explicit percent sign wins over size heuristic
    ("10", 0.10),
    ("10%", 0.10),
    ("1%", 0.01),
    ("0", 0.0),
    ("  5%  ", 0.05),          # surrounding whitespace is stripped
])
def test_parse_rate_valid(value, expected):
    assert mc.parse_rate(value, "rate") == pytest.approx(expected)


def test_parse_rate_one_is_decimal():
    # Documented behavior: a bare "1" is not > 1, so it stays a decimal (100%).
    assert mc.parse_rate("1", "rate") == pytest.approx(1.0)
    # With an explicit "%" it is 1%.
    assert mc.parse_rate("1%", "rate") == pytest.approx(0.01)


@pytest.mark.parametrize("value", ["", "  ", "-5", "-5%", "abc", "%", "1.2.3"])
def test_parse_rate_invalid(value):
    with pytest.raises(ValueError):
        mc.parse_rate(value, "rate")


# ---------------------------------------------------------------------------
# parse_cash_flow
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("300", 300.0),
    ("-42.5", -42.5),
    ("1e3", 1000.0),
    ("+77", 77.0),
])
def test_parse_cash_flow_valid(value, expected):
    assert mc.parse_cash_flow(value) == expected


def test_parse_cash_flow_invalid():
    with pytest.raises(ValueError):
        mc.parse_cash_flow("abc")


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

def test_parse_args_defaults():
    data = mc.parse_args(["-100", "50", "60"])
    assert data["cash_flows"] == [-100.0, 50.0, 60.0]
    assert data["finance_rate"] == pytest.approx(0.10)
    assert data["reinvest_rate"] == pytest.approx(0.10)
    # discount rate falls back to the finance rate
    assert data["discount_rate"] == pytest.approx(data["finance_rate"])
    assert data["metrics"]["break_even"] is False
    assert data["metrics"]["sensitivity"] is False
    assert data["metrics"]["scenario"] is False


def test_parse_args_rates_and_flags():
    data = mc.parse_args([
        "-100", "50", "60",
        "-f", "7.5%", "-r", "0.0125", "-d", "0.09",
        "--breakeven", "--sensitivity", "--scenario",
    ])
    assert data["finance_rate"] == pytest.approx(0.075)
    assert data["reinvest_rate"] == pytest.approx(0.0125)
    assert data["discount_rate"] == pytest.approx(0.09)
    assert data["metrics"]["break_even"] is True
    assert data["metrics"]["sensitivity"] is True
    assert data["metrics"]["scenario"] is True


def test_parse_args_all_flag_enables_everything():
    data = mc.parse_args(["-100", "50", "--all"])
    for key, val in data["metrics"].items():
        assert val is True, f"metric {key!r} should be enabled by --all"


def test_parse_args_at_file(tmp_path):
    f = tmp_path / "flows.txt"
    f.write_text("-300 100 200")
    data = mc.parse_args([f"@{f}"])
    assert data["cash_flows"] == [-300.0, 100.0, 200.0]


def test_parse_args_input_file_flag(tmp_path):
    f = tmp_path / "flows.json"
    f.write_text(json.dumps([-300, 100, 200]))
    data = mc.parse_args(["-i", str(f)])
    assert data["cash_flows"] == [-300.0, 100.0, 200.0]


def test_parse_args_unknown_argument_raises():
    with pytest.raises(ValueError):
        mc.parse_args(["-x"])


def test_parse_args_missing_rate_value_raises():
    with pytest.raises(ValueError):
        mc.parse_args(["-100", "-f"])


# ---------------------------------------------------------------------------
# read_cash_flows_from_file
# ---------------------------------------------------------------------------

def test_read_csv_space_separated(tmp_path):
    f = tmp_path / "flows.csv"
    f.write_text("-300 33 55 66")
    assert mc.read_cash_flows_from_file(str(f)) == [-300.0, 33.0, 55.0, 66.0]


def test_read_csv_comma_separated(tmp_path):
    f = tmp_path / "flows.csv"
    f.write_text("100,200,300\n")
    assert mc.read_cash_flows_from_file(str(f)) == [100.0, 200.0, 300.0]


def test_read_json_array(tmp_path):
    f = tmp_path / "flows.json"
    f.write_text("[-300, 33, 55, 66]")
    assert mc.read_cash_flows_from_file(str(f)) == [-300.0, 33.0, 55.0, 66.0]


def test_read_json_object_with_key(tmp_path):
    f = tmp_path / "flows.json"
    f.write_text('{"cash_flows": [-300, 33, 55, 66]}')
    assert mc.read_cash_flows_from_file(str(f)) == [-300.0, 33.0, 55.0, 66.0]


def test_read_plain_text_newline_separated(tmp_path):
    f = tmp_path / "flows.txt"
    f.write_text("-300\n33\n55\n66\n")
    assert mc.read_cash_flows_from_file(str(f)) == [-300.0, 33.0, 55.0, 66.0]


def test_read_missing_file_raises(tmp_path):
    with pytest.raises(ValueError, match="File not found"):
        mc.read_cash_flows_from_file(str(tmp_path / "nope.csv"))


def test_read_empty_file_raises(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("")
    with pytest.raises(ValueError, match="empty"):
        mc.read_cash_flows_from_file(str(f))


def test_read_invalid_csv_raises(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("100, not-a-number, 200")
    with pytest.raises(ValueError, match="Invalid value in CSV"):
        mc.read_cash_flows_from_file(str(f))


def test_read_invalid_plain_text_raises(tmp_path):
    f = tmp_path / "bad.txt"
    f.write_text("100 abc 200")
    with pytest.raises(ValueError, match="Could not parse cash flows"):
        mc.read_cash_flows_from_file(str(f))