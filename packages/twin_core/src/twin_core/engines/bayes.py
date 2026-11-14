"""BAYES engine v0.1: Bayesian personalisation + Monte Carlo uncertainty.

Still a research prototype. Rates are literature-inspired placeholders (same order of
magnitude as the stub), NOT fitted to a dataset. What is new vs the stub:
  * the person's loss-rate multiplier is a posterior (normal-normal update from CTX),
  * uncertainty comes from sampling, not a fixed formula,
  * countermeasure effects are uncertain (sampled), not point values.
Common random numbers: the seed ignores countermeasures, so what-if plans for the same
crew/scenario differ only because of the countermeasures.
"""

from __future__ import annotations

import hashlib
import math
import random
from datetime import UTC, datetime

from bonetwin_contracts import (
    BoneSite,
    Driver,
    DriverDirection,
    EngineInfo,
    EngineInput,
    EngineKind,
    Forecast,
    ForecastPoint,
    MarkerId,
    RiskLevel,
    RiskSummary,
    SiteForecast,
)

DISCLAIMER = (
    "Research prototype built for a hackathon. Not a medical device. Outputs are decision "
    "support for a qualified flight surgeon and must never replace clinical judgement."
)

_KIND = EngineKind.statistical

_N = 1500
_THRESHOLD = -10.0
_STEP_DAYS = 15

# percent change per 30 days, population prior mean (illustrative)
_MONTHLY_RATE = {
    BoneSite.lumbar_spine: -1.0,
    BoneSite.femoral_neck: -1.1,
    BoneSite.total_hip: -1.2,
    BoneSite.distal_tibia: -0.8,
}
# mean multiplier on the loss rate (illustrative)
_CM_FACTOR = {
    "resistive_exercise": 0.65,
    "flywheel_device": 0.80,
    "vitamin_d_calcium": 0.95,
    "bisphosphonate": 0.50,
}
_PRIOR_SD = 0.20  # between-person spread of the rate multiplier
_OBS_SD = 0.25  # noise of "multiplier implied by one CTX ratio"
_CM_REL_SD = 0.25  # relative uncertainty of a countermeasure's effect
_SITE_REL_SD = 0.10  # site-specific spread
_PROCESS_SD = 0.25  # % per sqrt(month)


def _rng(base: str, label: str) -> random.Random:
    digest = hashlib.sha256(f"{base}|{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


class BayesBoneEngine:
    @property
    def info(self) -> EngineInfo:
        return EngineInfo(name="bayes", version="0.1.0", kind=_KIND)

    def model_card(self) -> dict:
        return {
            "assumptions": [
                "Linear mean loss per site; the person's rate multiplier has a normal prior.",
                "The multiplier is updated from the post-flight/pre-flight CTX ratio "
                "(normal-normal conjugate update; more post-flight samples, tighter posterior).",
                "Countermeasures multiply the loss rate; each effect is uncertain (sampled).",
                "Process noise grows with the square root of time.",
            ],
            "limitations": [
                "Parameters are literature-inspired placeholders, not fitted to a dataset.",
                "Only CTX personalises the forecast; other markers are not used yet.",
                "Countermeasure effects are independent and multiplicative (no interactions).",
                "Intervals are only as good as these assumptions; they are not validated.",
            ],
            "data_sources": [
                {
                    "name": "Published spaceflight bone-loss literature (order of magnitude)",
                    "url": None,
                    "usage": "Prior loss rates. To be calibrated against OSDR-derived data.",
                }
            ],
            "disclaimer": DISCLAIMER,
        }

    def forecast(self, inp: EngineInput) -> Forecast:
        horizon = inp.scenario.duration_days
        ids = [c.id for c in inp.countermeasures]
        base = f"{inp.crew.id}|{inp.scenario.id}|{horizon}"
        days = self._days(horizon)

        ratio, n_post = self._resorption(inp)
        post_mean, post_sd = self._posterior(ratio, n_post)
        rng = _rng(base, "person")
        mult = [max(0.2, rng.gauss(post_mean, post_sd)) for _ in range(_N)]

        drivers: list[Driver] = []
        cm_factor = [1.0] * _N
        for cid in ids:
            f = _CM_FACTOR.get(cid, 1.0)
            effect = 1 - f
            if effect > 0:
                r = _rng(base, f"cm:{cid}")
                cm_factor = [
                    cf * (1 - min(0.9, max(0.0, effect * (1 + _CM_REL_SD * r.gauss(0, 1)))))
                    for cf in cm_factor
                ]
            drivers.append(
                Driver(
                    signal=cid,
                    direction=DriverDirection.protective if effect > 0 else DriverDirection.neutral,
                    weight=round(min(1.0, max(0.0, effect)), 2),
                    explanation=f"Expected loss-rate multiplier x{f} (effect uncertain, sampled).",
                )
            )
        if ratio is not None:
            shift = post_mean - 1.0
            drivers.append(
                Driver(
                    signal="ctx_vs_baseline",
                    direction=(
                        DriverDirection.harmful
                        if shift > 0.02
                        else DriverDirection.protective
                        if shift < -0.02
                        else DriverDirection.neutral
                    ),
                    weight=round(min(1.0, abs(shift) * 2), 2),
                    explanation=(
                        f"Latest CTX is {ratio:.2f}x pre-flight; posterior rate multiplier "
                        f"{post_mean:.2f} (sd {post_sd:.2f})."
                    ),
                )
            )

        sites: list[SiteForecast] = []
        for site, monthly in _MONTHLY_RATE.items():
            r = _rng(base, f"site:{site}")
            rates = [
                monthly * m * cf * (1 + _SITE_REL_SD * r.gauss(0, 1))
                for m, cf in zip(mult, cm_factor, strict=True)
            ]
            noise = [0.0] * _N
            points: list[ForecastPoint] = []
            vals: list[float] = []
            prev = 0
            for day in days:
                dt = (day - prev) / 30
                if dt > 0:
                    s = _PROCESS_SD * math.sqrt(dt)
                    noise = [x + s * r.gauss(0, 1) for x in noise]
                vals = sorted(rt * day / 30 + nz for rt, nz in zip(rates, noise, strict=True))
                mean = sum(vals) / _N
                lo = min(vals[int(0.025 * (_N - 1))], mean)
                hi = max(vals[int(0.975 * (_N - 1))], mean)
                points.append(
                    ForecastPoint(
                        day=day,
                        mean_pct_change=round(mean, 3),
                        lower_95=round(lo, 3),
                        upper_95=round(hi, 3),
                    )
                )
                prev = day
            p = sum(1 for v in vals if v < _THRESHOLD) / _N
            level = RiskLevel.high if p >= 0.5 else RiskLevel.moderate if p >= 0.15 else RiskLevel.low
            sites.append(
                SiteForecast(
                    site=site,
                    points=points,
                    risk=RiskSummary(
                        threshold_pct_change=_THRESHOLD,
                        prob_below_threshold_at_end=round(p, 4),
                        level=level,
                    ),
                )
            )

        warnings = ["Research prototype: parameters are not fitted to real data."]
        if ratio is None:
            warnings.append("No usable pre/post-flight CTX pair: population prior only.")
        needs_review = ratio is None or ratio >= 1.3 or any(s.risk.level != RiskLevel.low for s in sites)
        return Forecast(
            crew_id=inp.crew.id,
            scenario_id=inp.scenario.id,
            countermeasure_ids=ids,
            horizon_days=horizon,
            generated_at=datetime.now(UTC),
            engine=self.info,
            sites=sites,
            drivers=drivers,
            warnings=warnings,
            requires_physician_review=needs_review,
            disclaimer=DISCLAIMER,
        )

    @staticmethod
    def _days(horizon: int) -> list[int]:
        return [*range(0, horizon, _STEP_DAYS), horizon]

    @staticmethod
    def _posterior(ratio: float | None, n_post: int) -> tuple[float, float]:
        if ratio is None:
            return 1.0, _PRIOR_SD
        obs = min(1.6, max(0.6, 1 + 0.3 * (ratio - 1)))
        obs_sd = _OBS_SD / math.sqrt(min(max(n_post, 1), 4))
        w_prior, w_obs = 1 / _PRIOR_SD**2, 1 / obs_sd**2
        mean = (w_prior * 1.0 + w_obs * obs) / (w_prior + w_obs)
        return mean, math.sqrt(1 / (w_prior + w_obs))

    @staticmethod
    def _resorption(inp: EngineInput) -> tuple[float | None, int]:
        ctx = sorted(
            (m for m in inp.measurements if m.marker == MarkerId.ctx),
            key=lambda m: m.mission_day,
        )
        pre = [m for m in ctx if m.mission_day < 0]
        post = [m for m in ctx if m.mission_day >= 0]
        if not pre or not post or pre[-1].value == 0:
            return None, 0
        return post[-1].value / pre[-1].value, len(post)
