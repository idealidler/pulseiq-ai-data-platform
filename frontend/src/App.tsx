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
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-ink focus:px-4 focus:py-2 focus:text-sm focus:text-shell"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-30 border-b border-ink/10 bg-shell/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-5 px-6 py-5 md:px-10">
          <div>
            <div className="text-[11px] uppercase tracking-[0.34em] text-steel">PulseIQ</div>
            <div className="mt-2 max-w-2xl font-display text-[1.8rem] leading-[1.02] md:text-[2.15rem]">
              A production-style analytics assistant built on top of a modern data stack
            </div>
          </div>
          <nav aria-label="Primary" className="flex flex-wrap gap-3" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                role="tab"
                id={`tab-${tab.id}`}
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                className={`rounded-full px-5 py-3 text-left transition duration-200 ${
                  activeTab === tab.id
                    ? "bg-ink text-shell shadow-panel"
                    : "border border-ink/10 bg-white/70 text-ink hover:-translate-y-0.5 hover:border-ink/20 hover:bg-white"
                }`}
              >
                <div className="text-sm font-semibold">{tab.label}</div>
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main id="main-content">
        {activeTab === "product" ? (
          <section
            id="panel-product"
            role="tabpanel"
            aria-labelledby="tab-product"
          >
            <ProductTab />
          </section>
        ) : (
          <section
            id="panel-architecture"
            role="tabpanel"
            aria-labelledby="tab-architecture"
          >
            <ArchitectureTab />
          </section>
        )}
      </main>
    </div>
  );
}
