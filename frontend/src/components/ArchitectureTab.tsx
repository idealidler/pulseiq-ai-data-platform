import { ArrowRight, Boxes, BrainCircuit, DatabaseZap, Layers3, Sparkles } from "lucide-react";

const layers = [
  {
    title: "Source Simulation",
    subtitle: "CSV + JSONL feeds",
    detail: "Synthetic customers, products, orders, events, and support tickets land as upstream-style source data.",
    icon: Layers3,
  },
  {
    title: "Raw + Ingestion",
    subtitle: "Bronze on Parquet",
    detail: "Python ingestion standardizes formats, adds metadata, writes Parquet, and registers raw tables in DuckDB.",
    icon: DatabaseZap,
  },
  {
    title: "Warehouse Modeling",
    subtitle: "dbt silver + gold",
    detail: "dbt builds staging models, business marts, and serving tables such as mart_product_risk and support_issue_trends.",
    icon: Boxes,
  },
  {
    title: "Semantic Retrieval",
    subtitle: "Embeddings + Qdrant",
    detail: "Support ticket text is chunked, embedded with OpenAI embeddings, and indexed in Qdrant with business metadata.",
    icon: BrainCircuit,
  },
  {
    title: "Reasoning Layer",
    subtitle: "FastAPI + tool orchestration",
    detail: "The backend routes questions to SQL, vector search, or both, then synthesizes grounded answers.",
    icon: Sparkles,
  },
  {
    title: "Experience Layer",
    subtitle: "React interface",
    detail: "Users interact through a polished operational intelligence workspace with evidence-backed answers and architecture storytelling.",
    icon: ArrowRight,
  },
];

const principles = [
  "Bronze/silver/gold modeling with Parquet and DuckDB",
  "Serving tables optimized for low-latency chatbot access",
  "Hybrid reasoning across structured metrics and semantic evidence",
  "Benchmark-driven hardening with route, evidence, and conciseness evals",
];

export function ArchitectureTab() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(15,92,75,0.12),_transparent_30%),radial-gradient(circle_at_80%_0%,_rgba(255,107,44,0.12),_transparent_28%)]" />
      <div className="relative mx-auto max-w-7xl px-6 py-10 md:px-10">
        <div className="mb-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-[2.4rem] border border-ink/10 bg-ink p-8 text-shell shadow-panel">
            <p className="text-sm uppercase tracking-[0.3em] text-shell/60">Architecture Walkthrough</p>
            <h2 className="mt-3 max-w-4xl font-display text-5xl leading-[0.95]">
              How a learning project turned into a full data-and-AI system.
            </h2>
            <p className="mt-5 max-w-2xl text-sm leading-7 text-shell/78">
              This tab exists for the people who immediately ask, “cool chatbot, but how was it actually built?” The short answer: one layer at a time, with far more respect for the plumbing than for the buzzwords.
            </p>
          </section>

          <section className="rounded-[2.4rem] border border-ink/10 bg-white/82 p-8 shadow-panel backdrop-blur">
            <p className="text-sm uppercase tracking-[0.28em] text-steel">System Story</p>
            <h3 className="mt-3 font-display text-3xl text-ink">Why this architecture exists at all</h3>
            <p className="mt-4 text-sm leading-7 text-steel">
              PulseIQ is intentionally data-engineering first. The chatbot is the friendly part. The real lesson was learning how ingestion, modeling, retrieval, orchestration, and evaluation fit together without hand-wavy magic.
            </p>
            <div className="mt-6 grid gap-3">
              {principles.map((principle) => (
                <div
                  key={principle}
                  className="rounded-2xl border border-ink/10 bg-shell/70 px-4 py-3 text-sm leading-6 text-steel transition duration-200 hover:-translate-y-0.5 hover:border-ink/20 hover:bg-white"
                >
                  {principle}
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-[2rem] border border-ink/10 bg-white/82 p-8 shadow-panel backdrop-blur">
            <div className="mb-8 flex items-end justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-steel">Pipeline Sequence</p>
                <h2 className="font-display text-4xl text-ink">Six layers from fake source data to grounded answers</h2>
              </div>
              <div className="rounded-full bg-ink px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-shell">
                Production Path
              </div>
            </div>

            <div className="relative grid gap-5">
              {layers.map((layer, index) => {
                const Icon = layer.icon;
                return (
                  <div
                    key={layer.title}
                    className="relative rounded-[1.6rem] border border-ink/10 bg-shell/78 p-5 transition duration-200 hover:-translate-y-0.5 hover:border-ink/20 hover:bg-white"
                  >
                    {index < layers.length - 1 ? (
                      <div className="absolute left-8 top-full h-5 w-px bg-ink/15" />
                    ) : null}
                    <div className="flex gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-pine text-shell">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <h3 className="text-xl font-semibold text-ink">{layer.title}</h3>
                          <span className="rounded-full bg-white px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-steel">
                            {layer.subtitle}
                          </span>
                          <span className="rounded-full bg-ink/5 px-2.5 py-1 text-[11px] font-semibold text-pine">
                            {index + 1}
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-7 text-steel">{layer.detail}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="space-y-6">
            <div className="rounded-[2rem] border border-ink/10 bg-mist p-8 shadow-panel">
              <p className="text-sm uppercase tracking-[0.28em] text-pine">Data Journey</p>
              <div className="mt-5 grid grid-cols-2 gap-4 text-sm">
                <div className="rounded-2xl bg-white p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-panel">
                  <div className="font-semibold text-ink">Storage</div>
                  <div className="mt-2 leading-6 text-steel">CSV/JSONL {"->"} Parquet {"->"} DuckDB {"->"} Qdrant</div>
                </div>
                <div className="rounded-2xl bg-white p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-panel">
                  <div className="font-semibold text-ink">Compute</div>
                  <div className="mt-2 leading-6 text-steel">Python pipelines, dbt transformations, API tool orchestration</div>
                </div>
                <div className="rounded-2xl bg-white p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-panel">
                  <div className="font-semibold text-ink">Reliability</div>
                  <div className="mt-2 leading-6 text-steel">Schema-aware prompting, eval benchmarks, grounded evidence responses</div>
                </div>
                <div className="rounded-2xl bg-white p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-panel">
                  <div className="font-semibold text-ink">Experience</div>
                  <div className="mt-2 leading-6 text-steel">Low-friction questions, compact answers, inspectable evidence</div>
                </div>
              </div>
            </div>

            <div className="rounded-[2rem] border border-ink/10 bg-white/82 p-8 shadow-panel backdrop-blur">
              <p className="text-sm uppercase tracking-[0.28em] text-steel">Why it feels premium</p>
              <h3 className="mt-3 font-display text-3xl text-ink">Because the interface respects the system underneath it.</h3>
              <p className="mt-4 text-sm leading-7 text-steel">
                The architecture tab is not filler. It is part of the product story: the warehouse, the retrieval layer, and the assistant are all meant to be inspectable, explainable, and demo-friendly.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
