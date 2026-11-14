from __future__ import annotations

import json
from pathlib import Path

import pytest
from bonetwin_contracts import Countermeasure, EngineInput, MarkerId
from twin_core import get_engine
from twin_core.engines.bayes import BayesBoneEngine
from twin_core.sim import synthetic as syn

FIXTURES = Path(__file__).resolve().parents[3] / "contracts" / "fixtures"


def _base() -> EngineInput:
    return EngineInput.model_validate(json.loads((FIXTURES / "engine_input_example.json").read_text()))


def _end_mean(inp: EngineInput) -> float:
    return get_engine("bayes").forecast(inp).sites[0].points[-1].mean_pct_change


def test_countermeasure_reduces_loss() -> None:
    cms = [Countermeasure.model_validate(c) for c in syn.COUNTERMEASURES]
    resistive = [c for c in cms if c.id == "resistive_exercise"]
    assert resistive, "fixture must offer resistive_exercise"
    none = _base().model_copy(update={"countermeasures": []})
    with_cm = _base().model_copy(update={"countermeasures": resistive})
    assert _end_mean(with_cm) > _end_mean(none)  # less negative = less loss


def test_uncertainty_widens_over_time() -> None:
    pts = get_engine("bayes").forecast(_base()).sites[0].points
    widths = [p.upper_95 - p.lower_95 for p in pts]
    assert widths[0] == 0 and widths[-1] > widths[1] > 0


def test_higher_ctx_means_more_loss() -> None:
    inp = _base()
    if BayesBoneEngine._resorption(inp)[0] is None:
        pytest.skip("fixture has no pre/post CTX pair")
    raised = [
        m.model_copy(update={"value": m.value * 1.5})
        if m.marker == MarkerId.ctx and m.mission_day >= 0
        else m
        for m in inp.measurements
    ]
    assert _end_mean(inp.model_copy(update={"measurements": raised})) < _end_mean(inp)


def test_no_measurements_flags_review() -> None:
    out = get_engine("bayes").forecast(_base().model_copy(update={"measurements": []}))
    assert out.requires_physician_review
    assert any("population prior" in w for w in out.warnings)
