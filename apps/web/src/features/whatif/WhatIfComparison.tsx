import { AlertTriangle } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { useCrew, useScenarios, useWhatIf } from "../../api/hooks";
import { translations } from "../../i18n/translations";
import type { Language } from "../../types";

// Constant so the query key stays stable between renders.
const PLANS = [
  { plan_id: "none", label: "No countermeasure", countermeasure_ids: [] as string[] },
  { plan_id: "resist", label: "Resistive exercise", countermeasure_ids: ["resistive_exercise"] },
  {
    plan_id: "resist_bis",
    label: "Exercise + bisphosphonate",
    countermeasure_ids: ["resistive_exercise", "bisphosphonate"],
  },
];

const BADGE: Record<string, string> = {
  low: "bg-emerald-100 text-emerald-700 border-emerald-300",
  moderate: "bg-amber-100 text-amber-700 border-amber-300",
  high: "bg-rose-100 text-rose-700 border-rose-300",
};

export const WhatIfComparison: React.FC<{ lang: Language }> = ({ lang }) => {
  const t = translations[lang];
  const crew = useCrew();
  const scenarios = useScenarios();
  const [crewId, setCrewId] = useState("crew-02");
  const [scenarioId, setScenarioId] = useState("mars-transit-210");
  const whatIf = useWhatIf(crewId, scenarioId, PLANS);

  const planName: Record<string, string> = {
    none: t.whatIfPlanNone,
    resist: t.whatIfPlanResist,
    resist_bis: t.whatIfPlanResistBis,
  };

  return (
    <div className="glass-panel rounded-3xl p-6 flex flex-col gap-4 text-brand-700">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-bold text-base">{t.whatIfTitle}</h3>
        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-brand-200/50 border border-brand-300/60">
          {t.illustrativeModel}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <select
          value={crewId}
          onChange={(e) => setCrewId(e.target.value)}
          className="p-2 rounded-xl bg-white/60 border border-brand-500/15"
        >
          {crew.data?.items.map((c) => (
            <option key={c.id} value={c.id}>
              {c.display_name}
            </option>
          ))}
        </select>
        <select
          value={scenarioId}
          onChange={(e) => setScenarioId(e.target.value)}
          className="p-2 rounded-xl bg-white/60 border border-brand-500/15"
        >
          {scenarios.data?.items.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {whatIf.isLoading && <p className="text-xs text-slate-500">{t.whatIfLoading}</p>}
      {whatIf.isError && <p className="text-xs text-rose-600">{t.whatIfError}</p>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {whatIf.data?.results.map((r) => {
          const hip = r.forecast.sites.find((s) => s.site === "total_hip") ?? r.forecast.sites[0];
          const end = hip?.points.at(-1);
          if (!hip || !end) return null;
          const worst = Math.max(
            ...r.forecast.sites.map((s) => s.risk.prob_below_threshold_at_end),
          );
          const level = hip.risk.level;
          return (
            <div
              key={r.plan_id}
              className="flex flex-col gap-2 p-3.5 rounded-2xl bg-white/60 border border-brand-500/15 shadow-sm"
            >
              <span className="text-xs font-semibold">{planName[r.plan_id] ?? r.label}</span>
              <span className="text-[11px] text-slate-500">{t.whatIfHipLoss}</span>
              <span className="font-bold text-xl text-rose-600" dir="ltr">
                {end.mean_pct_change.toFixed(1)}%
              </span>
              <span className="text-[11px] text-slate-500" dir="ltr">
                [{end.lower_95.toFixed(1)}, {end.upper_95.toFixed(1)}]
              </span>
              <span
                className={`self-start text-[11px] font-bold px-2 py-0.5 rounded-full border ${BADGE[level] ?? ""}`}
              >
                {t.whatIfRisk} {Math.round(worst * 100)}%
              </span>
              {r.forecast.requires_physician_review && (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-700">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {t.whatIfReview}
                </span>
              )}
            </div>
          );
        })}
      </div>
      <p className="text-[11px] leading-relaxed text-slate-500">{t.whatIfNote}</p>
    </div>
  );
};
