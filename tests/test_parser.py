"""Tests for the DSL parser: the table of values and the states of the line."""

from __future__ import annotations

import pytest

from custom_components.zte_h186.api import (
    DSL_FIELDS,
    ZteH186ProtocolError,
    parse_dsl_values,
)
from custom_components.zte_h186.const import DSL_RAW_KEYS

UP = {
    "Status": "Up",
    "Downstream_current_rate": "109200",
    "Upstream_current_rate": "42800",
    "Downstream_max_rate": "118500",
    "Upstream_max_rate": "45000",
    "Downstream_noise_margin": "103",
    "Upstream_noise_margin": "68",
    "Downstream_attenuation": "110",
    "Upstream_attenuation": "112",
    "CurrentProfile": "17a",
    "Module_type": "VDSL2",
    "Downstream_power": "144",
    "DownCrc_errors": "26",
    "Showtime_start": "2017149",
}
REQUIRED = [f.key for f in DSL_FIELDS if f.required]


def test_table_is_consistent() -> None:
    """Every key of the table is known to diagnostics; no attribute or key appears twice."""
    assert len({f.attr for f in DSL_FIELDS}) == len(DSL_FIELDS)
    assert len({f.key for f in DSL_FIELDS}) == len(DSL_FIELDS)
    assert {f.key for f in DSL_FIELDS} <= set(DSL_RAW_KEYS)
    assert len(REQUIRED) == 10


def test_up_with_all_values() -> None:
    """A line in Showtime is converted with the divisors of the table."""
    data, missing = parse_dsl_values(UP)
    assert missing == []
    assert data.dsl_status == "Up"
    assert data.downstream_sync == pytest.approx(109.2)
    assert data.downstream_snr == pytest.approx(10.3)
    assert data.downstream_attenuation == pytest.approx(11.0)
    assert data.downstream_power == pytest.approx(14.4)
    assert data.downstream_crc == 26
    assert data.showtime == 2017149
    assert data.profile == "17a"
    assert data.upstream_power is None  # optional, absent
    assert data.raw_values == UP


def test_up_with_fields_missing_is_tolerated() -> None:
    """Missing required values while Up are None and reported, the rest is kept."""
    values = {k: v for k, v in UP.items() if k not in ("Downstream_current_rate", "Module_type")}
    data, missing = parse_dsl_values(values)
    assert sorted(missing) == ["Downstream_current_rate", "Module_type"]
    assert data.downstream_sync is None
    assert data.modulation is None
    assert data.upstream_sync == pytest.approx(42.8)
    assert data.profile == "17a"


def test_up_with_only_the_status() -> None:
    """Even a bare Status=Up gives data (all unknown) and names all required values."""
    data, missing = parse_dsl_values({"Status": "Up"})
    assert sorted(missing) == sorted(REQUIRED)
    assert data.downstream_sync is None


@pytest.mark.parametrize("status", ["Down", "Training", "Handshake", "NoSignal"])
def test_not_up_leaves_out_values_without_complaint(status: str) -> None:
    """While the line trains or is down the modem omits the metrics by design."""
    data, missing = parse_dsl_values({"Status": status})
    assert missing == []
    assert data.dsl_status == status
    assert data.downstream_sync is None
    assert data.profile is None


def test_status_missing_defaults_to_down() -> None:
    """Without a Status but with values, the line counts as Down."""
    data, missing = parse_dsl_values({"CurrentProfile": "17a"})
    assert (data.dsl_status, missing) == ("Down", [])
    assert data.profile == "17a"


def test_not_a_number_is_unknown() -> None:
    """A value that is not a number is None instead of an exception."""
    values = {**UP, "Downstream_current_rate": "n/a", "DownCrc_errors": "x"}
    data, _ = parse_dsl_values(values)
    assert data.downstream_sync is None
    assert data.downstream_crc is None


@pytest.mark.parametrize("values", [{}, {"IF_ERRORSTR": "SUCC"}, {"Foo": "bar"}])
def test_answer_without_dsl_values_is_an_error(values: dict[str, str]) -> None:
    """Only an empty or foreign answer is an error."""
    with pytest.raises(ZteH186ProtocolError):
        parse_dsl_values(values)
