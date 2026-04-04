import { useState } from "react";
import { ArchitectureTab } from "./components/ArchitectureTab";
import { ProductTab } from "./components/ProductTab";

type TabId = "product" | "architecture";

const tabs: Array<{ id: TabId; label: string }> = [
  { id: "product", label: "Experience" },
  { id: "architecture", label: "Architecture" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("product");

  return (
    <div className="min-h-screen bg-shell text-ink">
      <div className="sticky top-0 z-30 border-b border-ink/10 bg-shell/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-5 px-6 py-5 md:px-10">
          <div>
            <div className="text-sm uppercase tracking-[0.32em] text-steel">PulseIQ</div>
            <div className="mt-1 max-w-2xl font-display text-2xl leading-tight">
              A very real data platform hiding inside a very self-aware demo website
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`rounded-full px-5 py-3 text-left transition duration-200 ${
                  activeTab === tab.id
                    ? "bg-ink text-shell shadow-panel"
                    : "border border-ink/10 bg-white/70 text-ink hover:-translate-y-0.5 hover:border-ink/20 hover:bg-white"
                }`}
              >
                <div className="text-sm font-semibold">{tab.label}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {activeTab === "product" ? <ProductTab /> : <ArchitectureTab />}
    </div>
  );
}
