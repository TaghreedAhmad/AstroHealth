import type React from "react";
import { WhatIfComparison } from "../features/whatif/WhatIfComparison";
import type { Astronaut, Language } from "../types";
import { RiskSimulatorPanel } from "./RiskSimulatorPanel";

interface RiskSimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  astronaut: Astronaut;
  lang: Language;
}

export const RiskSimulatorModal: React.FC<RiskSimulatorModalProps> = ({
  isOpen,
  onClose,
  astronaut,
  lang,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0D223A]/40 backdrop-blur-md animate-fade-in">
      <div className="max-w-3xl w-full max-h-full overflow-y-auto flex flex-col gap-4">
        <RiskSimulatorPanel astronaut={astronaut} lang={lang} onClose={onClose} />
        <WhatIfComparison lang={lang} />
      </div>
    </div>
  );
};
