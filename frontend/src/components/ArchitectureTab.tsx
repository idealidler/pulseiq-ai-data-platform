import {
  BadgeCheck,
  Boxes,
  BrainCircuit,
  DatabaseZap,
  FileCog,
  FileStack,
  LayoutPanelTop,
  MessageSquareText,
  Radar,
  SearchCode,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

const architectureSteps = [
  {
    title: "Synthetic source data",
    step: "01",
    detail:
      "The project starts by generating customers, products, orders, events, and support tickets as upstream-style CSV and JSONL files.",
    icon: FileStack,
  },
  {
    title: "Ingestion and raw layer",
    step: "02",
    detail:
      "Python ingestion converts those files into raw Parquet, adds load metadata, and registers raw tables in DuckDB.",
    icon: FileCog,
  },
  {
    title: "dbt transformation layer",
    step: "03",
    detail:
      "dbt builds staging models, dimensions, and serving marts so the chatbot queries prepared business data instead of inventing joins at runtime.",
    icon: DatabaseZap,
  },
  {
    title: "Semantic metadata",
    step: "04",
    detail:
      "Model descriptions, column descriptions, and meta.ai_hint live in dbt and define the semantic meaning the assistant should use.",
    icon: Boxes,
  },
  {
    title: "Embeddings and retrieval",
    step: "05",
    detail:
      "Support-ticket text is chunked, embedded, and stored in Qdrant with metadata such as product, issue type, priority, and region.",
    icon: SearchCode,
  },
  {
    title: "Chat orchestration",
    step: "06",
    detail:
      "FastAPI routes each question to SQL, vector search, or a hybrid path, then synthesizes a grounded answer with evidence.",
    icon: Sparkles,
  },
  {
    title: "Evaluation and frontend",
    step: "07",
    detail:
      "Benchmark suites measure quality, while the React frontend streams answers and presents the project like a real product.",
    icon: LayoutPanelTop,
  },
];

const requestFlow = [
  {
    title: "Question enters the app",
    body: "A user asks from the React frontend. The request goes to FastAPI, not directly to the model.",
  },
  {
    title: "Schema context is loaded",
    body: "The backend injects dbt-driven semantic context so the model knows table purpose, grain, and useful metrics.",
  },
  {
    title: "The model chooses a route",
    body: "It selects SQL for structured metrics, vector search for complaint language, or hybrid when both are needed.",
  },
  {
    title: "Tools return evidence",
    body: "DuckDB returns analytical rows. Qdrant returns ticket snippets and metadata. The backend compresses results before synthesis.",
  },
  {
    title: "A grounded answer is streamed",
    body: "The frontend receives progress states and then the formatted answer, so the interface feels responsive while staying traceable.",
  },
];

const systemCards = [
  {
    title: "Structured analytics path",
    body: "DuckDB + dbt answer things like highest selling product, refund-heavy customers, weak regions, and product risk.",
    icon: DatabaseZap,
  },
  {
    title: "Semantic complaint path",
    body: "Embeddings + Qdrant answer what customers are actually saying, which issues sound similar, and what themes keep repeating.",
    icon: BrainCircuit,
  },
  {
    title: "Quality control path",
    body: "Benchmarks are used to measure routing, grounding, conciseness, and failure rate before calling the system good enough.",
    icon: ShieldCheck,
  },
];

const servingModels = [
  "mart_product_sales",
  "mart_product_risk",
  "mart_region_customer_health",
  "mart_product_engagement_daily",
  "mart_support_issue_trends",
  "fct_support_tickets_enriched",
];

const whyItWorks = [
  "Serving marts reduce runtime joins and keep SQL generation simpler.",
  "dbt metadata acts as the semantic source of truth instead of hardcoded prompt prose.",
  "Vector search adds customer-language understanding that SQL alone cannot provide.",
  "Evaluation suites make the assistant measurable instead of relying on vibes.",
];

const techStack = [
  { label: "Python", icon: FileStack },
  { label: "DuckDB", icon: DatabaseZap },
  { label: "dbt", icon: Boxes },
  { label: "Qdrant", icon: Radar },
  { label: "FastAPI", icon: Workflow },
  { label: "React", icon: MessageSquareText },
];

export function ArchitectureTab() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(15,92,75,0.12),_transparent_30%),radial-gradient(circle_at_80%_0%,_rgba(255,107,44,0.12),_transparent_28%),linear-gradient(180deg,_rgba(255,255,255,0.65),_rgba(244,239,230,0.92))]" />

      <div className="relative mx-auto max-w-7xl px-6 py-10 md:px-10">
        <section className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="rounded-[2.5rem] border border-ink/10 bg-ink p-8 text-shell shadow-panel">
            <div className="text-[11px] uppercase tracking-[0.3em] text-shell/78">Architecture</div>
            <h1 className="mt-3 max-w-4xl font-display text-5xl leading-[0.95] md:text-[4.35rem]">
              The exact system behind this project.
            </h1>
            <p className="mt-5 max-w-2xl text-sm leading-7 text-shell/82">
              This page maps the architecture actually used in PulseIQ. It starts with synthetic commerce and support
              data, moves through raw storage and dbt serving models, adds semantic retrieval for ticket text, and ends
              in a chat product that is benchmarked for grounded answers.
            </p>
            <div className="mt-7 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[1.45rem] border border-white/10 bg-white/5 px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.22em] text-shell/70">Core idea</div>
                <div className="mt-2 text-sm leading-6 text-shell/88">
                  Build the data platform first, then let the assistant read curated business tables and semantic
                  evidence.
                </div>
              </div>
              <div className="rounded-[1.45rem] border border-white/10 bg-white/5 px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.22em] text-shell/70">Flow</div>
                <div className="mt-2 text-sm leading-6 text-shell/88">
                  Source files → raw Parquet → DuckDB + dbt → embeddings + Qdrant → FastAPI routing → React UI
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[2.5rem] border border-ink/10 bg-white/84 p-8 shadow-panel backdrop-blur">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[11px] uppercase tracking-[0.28em] text-steel">Tech stack</div>
                <h2 className="mt-2 font-display text-3xl text-ink">What is actually in the stack</h2>
              </div>
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {techStack.map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.label}
                    className="flex items-center gap-3 rounded-[1.35rem] border border-ink/10 bg-shell/76 px-4 py-4"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-pine text-shell">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="text-sm font-semibold text-ink">{item.label}</div>
                  </div>
                );
              })}
            </div>
            <div className="mt-6 rounded-[1.5rem] border border-ink/10 bg-mist px-5 py-5">
              <div className="text-[11px] uppercase tracking-[0.22em] text-pine">Important detail</div>
              <p className="mt-2 text-sm leading-7 text-steel">
                The assistant no longer relies on hardcoded table meaning in the prompt. dbt metadata now supplies the
                semantic layer at runtime.
              </p>
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-[2.2rem] border border-ink/10 bg-white/84 p-8 shadow-panel backdrop-blur">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.28em] text-steel">System map</div>
              <h2 className="mt-2 font-display text-4xl text-ink">Seven layers from fake source systems to grounded answers</h2>
            </div>
          </div>

          <div className="mt-8 grid gap-5 lg:grid-cols-2">
            {architectureSteps.map((row) => {
              const Icon = row.icon;
              return (
                <div
                  key={row.title}
                  className="rounded-[1.7rem] border border-ink/10 bg-shell/78 p-5 transition duration-200 hover:-translate-y-0.5 hover:border-ink/20 hover:bg-white"
                >
                  <div className="flex gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-pine text-shell">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-xl font-semibold text-ink">{row.title}</h3>
                        <span className="rounded-full bg-white px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-steel">
                          Step {row.step}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-7 text-steel">{row.detail}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_1fr]">
          <div className="rounded-[2rem] border border-ink/10 bg-mist p-8 shadow-panel">
            <div className="text-[11px] uppercase tracking-[0.28em] text-pine">What happens on one question</div>
            <div className="mt-5 space-y-4">
              {requestFlow.map((step, index) => (
                <div
                  key={step.title}
                  className="flex items-start gap-4 rounded-[1.45rem] border border-pine/10 bg-white/88 px-4 py-4"
                >
                  <div className="flex h-8 w-8 flex-none items-center justify-center rounded-full bg-ink text-xs font-semibold text-shell">
                    {index + 1}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-ink">{step.title}</div>
                    <div className="mt-1 text-sm leading-6 text-steel">{step.body}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-6">
            <div className="rounded-[2rem] border border-ink/10 bg-white/84 p-8 shadow-panel backdrop-blur">
              <div className="text-[11px] uppercase tracking-[0.28em] text-steel">Core subsystems</div>
              <div className="mt-5 grid gap-3">
                {systemCards.map((card) => {
                  const Icon = card.icon;
                  return (
                    <div
                      key={card.title}
                      className="rounded-[1.5rem] border border-ink/10 bg-shell/75 px-5 py-4 transition duration-200 hover:-translate-y-0.5 hover:border-ink/20 hover:bg-white"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-ink text-shell">
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="text-lg font-semibold text-ink">{card.title}</div>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-steel">{card.body}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="rounded-[2rem] border border-ink/10 bg-white/84 p-8 shadow-panel backdrop-blur">
              <div className="text-[11px] uppercase tracking-[0.28em] text-steel">Serving layer</div>
              <h3 className="mt-2 font-display text-3xl text-ink">The chatbot reads curated analytical tables, not raw rows.</h3>
              <p className="mt-4 text-sm leading-7 text-steel">
                These are the main serving models that make frequent business questions easier to answer correctly and
                consistently.
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {servingModels.map((model) => (
                  <div
                    key={model}
                    className="rounded-[1.35rem] border border-ink/10 bg-shell/75 px-4 py-3 text-sm font-medium text-ink"
                  >
                    {model}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-[2rem] border border-ink/10 bg-white/84 p-8 shadow-panel backdrop-blur">
          <div className="grid gap-6 lg:grid-cols-[0.96fr_1.04fr]">
            <div>
              <div className="text-[11px] uppercase tracking-[0.28em] text-steel">Why this architecture works</div>
              <h3 className="mt-2 font-display text-3xl text-ink">Each layer removes a different kind of uncertainty.</h3>
              <p className="mt-4 text-sm leading-7 text-steel">
                The project is easier to trust because the data layer, semantic layer, retrieval layer, and evaluation
                layer each have a clear job instead of one huge prompt trying to do everything.
              </p>
            </div>
            <div className="grid gap-3">
              {whyItWorks.map((item) => (
                <div
                  key={item}
                  className="flex gap-3 rounded-[1.35rem] border border-ink/10 bg-shell/75 px-4 py-4 text-sm leading-7 text-steel"
                >
                  <BadgeCheck className="mt-1 h-4 w-4 flex-none text-pine" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
