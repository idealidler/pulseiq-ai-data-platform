import { useEffect, useRef, useState } from "react";
import { ArrowRight, Bot, Database, LineChart, LoaderCircle, MessageSquare, Minus, Radar, Server, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { streamPulseIQ } from "../lib/api";

type Message = {
  role: "user" | "assistant";
  text: string;
  route?: string;
  status?: string;
};

const topQuestions = [
  "Which is the highest selling product?",
  "Which customer has filed for the most refunds?",
  "Which product categories have the highest refund rate?",
  "Which regions are driving the most net revenue?",
  "Which products are converting best from product views to purchases?",
  "Which issue types are creating the biggest support load?",
  "Which products have the lowest CSAT and what are customers saying?",
  "Which products have the highest refund rates and why are customers unhappy with them?",
  "What are customers saying about battery issues in electronics?",
  "Summarize wrong-item complaints in apparel.",
  "What are customers saying about confusing setup experiences?",
  "What changed in the last 30 days for refund-related customer pain?",
  "Compare electronics and beauty in terms of risk and complaint themes.",
  "Give me the current operational picture in one answer.",
  "Which risky products also drive the most support page views, and what complaint themes back that up?",
  "Which issue types take longest to resolve, and how do customers describe those experiences?",
  "Are apparel customers mostly asking for returns or talking about something else?",
  "Which products look operationally fragile, and what specific customer pain backs that up?",
  "Which regions look weaker lately based on revenue and customer complaints?",
  "Show the riskiest products, but only claim complaint themes if the ticket evidence matches the same product.",
];

const stats = [
  { label: "Top-20 benchmark", value: "18 / 20", icon: LineChart },
  { label: "Average score", value: "0.93", icon: Radar },
  { label: "Route accuracy", value: "90%", icon: Bot },
  { label: "Runtime failures", value: "0", icon: Database },
];

const featureCards = [
  {
    title: "Source to warehouse",
    body: "Synthetic source feeds land in raw Parquet and are modeled into serving tables in DuckDB with dbt.",
  },
  {
    title: "Retrieval + orchestration",
    body: "Support-ticket text is indexed for semantic search, and the backend chooses SQL, vector search, or both.",
  },
  {
    title: "Measured quality",
    body: "The interface is backed by benchmark suites that check routing quality, grounded evidence, conciseness, and runtime stability.",
  },
];

export function ProductTab() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "Welcome to the part where a learning project got unreasonably serious. Ask about risk, refunds, complaint themes, or operational weirdness.",
      route: "system",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const promptStartIndex = Math.floor(Date.now() / (1000 * 60 * 60 * 24)) % topQuestions.length;
  const prompts = Array.from({ length: 5 }, (_, offset) => topQuestions[(promptStartIndex + offset) % topQuestions.length]);

  useEffect(() => {
    if (!chatOpen) {
      return;
    }
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, chatOpen]);

  async function submitQuestion(nextQuestion?: string) {
    const prompt = (nextQuestion ?? question).trim();
    if (!prompt || loading) {
      return;
    }

    setMessages((current) => [...current, { role: "user", text: prompt }]);
    setQuestion("");
    setLoading(true);
    const assistantIndexRef = { current: -1 };

    setMessages((current) => {
      assistantIndexRef.current = current.length;
      return [
        ...current,
        {
          role: "assistant",
          text: "",
          route: "thinking",
          status: "Opening the pipeline...",
        },
      ];
    });

    try {
      await streamPulseIQ(prompt, {
        onStatus: (status) => {
          setMessages((current) =>
            current.map((message, index) =>
              index === assistantIndexRef.current ? { ...message, status } : message,
            ),
          );
        },
        onAnswerDelta: (delta) => {
          setMessages((current) =>
            current.map((message, index) =>
              index === assistantIndexRef.current
                ? { ...message, text: `${message.text}${delta}` }
                : message,
            ),
          );
        },
        onComplete: (payload) => {
          setMessages((current) =>
            current.map((message, index) =>
              index === assistantIndexRef.current
                ? { ...message, route: payload.route, status: undefined }
                : message,
            ),
          );
        },
        onError: (message) => {
          setMessages((current) =>
            current.map((entry, index) =>
              index === assistantIndexRef.current
                ? {
                    ...entry,
                    text: `I couldn't reach the backend cleanly. ${message}`,
                    route: "error",
                    status: undefined,
                  }
                : entry,
            ),
          );
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setMessages((current) =>
        current.map((entry, index) =>
          index === assistantIndexRef.current
            ? {
                ...entry,
                text: `I couldn't reach the backend cleanly. ${message}`,
                route: "error",
                status: undefined,
              }
            : entry,
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  function handlePromptClick(prompt: string) {
    setChatOpen(true);
    void submitQuestion(prompt);
  }

  function handleQuestionKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitQuestion();
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(255,107,44,0.16),_transparent_32%),radial-gradient(circle_at_85%_10%,_rgba(15,92,75,0.16),_transparent_26%),linear-gradient(180deg,_rgba(255,255,255,0.5),_rgba(244,239,230,0.85))]" />
      <div className="absolute inset-0 bg-grid bg-[length:42px_42px] opacity-20" />

      <div className="relative mx-auto max-w-7xl px-6 pb-24 pt-10 md:px-10">
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2.5rem] border border-ink/10 bg-ink px-8 py-9 text-shell shadow-panel">
            <div className="flex flex-wrap items-center gap-3 text-[11px] uppercase tracking-[0.26em] text-shell/75">
              <Server className="h-4 w-4" />
              Learning project, built like a product
            </div>
            <h1 className="mt-5 max-w-4xl font-display text-4xl leading-[0.96] text-shell md:text-[4.35rem]">
              I built this to learn data engineering properly.
            </h1>
            <p className="mt-5 max-w-2xl text-sm leading-7 text-shell/85">
              The project simulates an e-commerce business, moves data through ingestion and modeling layers, and then
              exposes that data through an AI assistant that can answer business and support questions.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <div className="rounded-full border border-white/10 px-4 py-2.5 text-sm text-shell/82">
                Synthetic commerce + support data
              </div>
              <div className="rounded-full border border-white/10 px-4 py-2.5 text-sm text-shell/82">
                DuckDB, dbt, Qdrant, FastAPI, React
              </div>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {stats.map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="rounded-[1.7rem] border border-ink/10 bg-white/85 p-5 shadow-panel backdrop-blur transition duration-200 hover:-translate-y-0.5 hover:border-ink/20"
              >
                <Icon className="h-5 w-5 text-accent" />
                <div className="mt-6 text-[10px] uppercase tracking-[0.24em] text-steel/90">{label}</div>
                <div className="mt-2 text-[1.65rem] font-semibold leading-tight text-ink">{value}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2rem] border border-ink/10 bg-white/85 p-8 shadow-panel backdrop-blur">
            <div className="flex items-center gap-3 text-xs uppercase tracking-[0.24em] text-steel">
              <Sparkles className="h-4 w-4 text-accent" />
              Project thesis
            </div>
            <h2 className="mt-3 text-3xl font-semibold text-ink">
              A full-stack data workflow designed around one usable serving layer.
            </h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-steel">
              <p>
                The project starts with synthetic source systems, lands raw data in Parquet, models warehouse-serving tables in DuckDB with dbt, and builds a retrieval layer over support-ticket text.
              </p>
              <p>
                The chatbot is the final interface, but the real work is the pipeline underneath: ingestion, transformations, serving marts, semantic indexing, prompt design, and benchmark-based evaluation.
              </p>
              <p>
                The business data covers orders, refunds, revenue, product performance, customer segments, behavioral events like product views and checkout activity, and support tickets with issue type, priority, CSAT, resolution time, and ticket text.
              </p>
              <p>
                The benchmark numbers above reflect how reliably the assistant routes between SQL and retrieval, stays concise, and answers without runtime failures.
              </p>
            </div>
          </div>

          <div className="overflow-hidden rounded-[2rem] border border-pine/15 bg-[linear-gradient(160deg,rgba(15,92,75,0.98),rgba(11,34,41,0.96))] p-8 text-shell shadow-panel">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[11px] uppercase tracking-[0.24em] text-shell/75">Prompt starter pack</div>
                <div className="mt-2 max-w-md text-2xl font-semibold leading-tight text-shell">
                  The tool can answer questions like these for the business:
                </div>
              </div>
            </div>
            <div className="mt-6 grid gap-3">
              {prompts.map((prompt, index) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handlePromptClick(prompt)}
                  className="group rounded-[1.5rem] border border-white/10 bg-white/8 px-5 py-4 text-left text-sm leading-6 text-shell transition duration-200 hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/12"
                >
                  <div className="flex items-start gap-4">
                    <div className="mt-0.5 flex h-7 w-7 flex-none items-center justify-center rounded-full border border-white/10 bg-white/10 text-[11px] font-semibold text-shell/90">
                      {index + 1}
                    </div>
                    <div className="flex-1">{prompt}</div>
                    <ArrowRight className="mt-1 h-4 w-4 flex-none text-shell/60 transition duration-200 group-hover:translate-x-0.5 group-hover:text-shell/85" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-3">
          {featureCards.map((card) => (
            <div
              key={card.title}
              className="rounded-[2rem] border border-ink/10 bg-white/82 p-7 shadow-panel backdrop-blur transition duration-200 hover:-translate-y-0.5 hover:border-ink/20"
            >
              <div className="text-lg font-semibold text-ink">{card.title}</div>
              <p className="mt-3 text-sm leading-7 text-steel">{card.body}</p>
            </div>
          ))}
        </section>
      </div>

      <div className="fixed bottom-5 right-5 z-30 md:bottom-7 md:right-7">
        {chatOpen ? (
          <div className="w-[calc(100vw-2rem)] max-w-[520px] overflow-hidden rounded-[2rem] border border-ink/10 bg-white/96 shadow-panel backdrop-blur-xl transition duration-200">
            <button
              type="button"
              onClick={() => setChatOpen(false)}
              aria-label="Minimize PulseIQ Assistant"
              className="flex w-full items-center justify-between border-b border-ink/10 px-5 py-4 text-left transition duration-200 hover:bg-shell/80"
            >
              <div>
                <div className="text-sm font-semibold text-ink">PulseIQ Assistant</div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-steel">
                  Warehouse marts + semantic retrieval
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="rounded-full bg-ink px-3 py-1 text-[10px] uppercase tracking-[0.16em] text-shell">
                  Live tools
                </div>
                <div className="rounded-full border border-ink/10 p-2 text-steel">
                  <Minus className="h-4 w-4" />
                </div>
              </div>
            </button>

            <div
              className="max-h-[min(460px,60vh)] space-y-3 overflow-y-auto bg-shell/80 p-4"
              role="log"
              aria-live="polite"
              aria-label="PulseIQ conversation"
            >
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`rounded-[1.25rem] px-4 py-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "ml-auto max-w-[85%] bg-ink text-shell"
                      : "max-w-[92%] bg-white text-ink"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ul:pl-5 prose-ol:my-2 prose-ol:pl-5 prose-li:my-1 prose-strong:text-ink prose-headings:text-ink prose-code:rounded prose-code:bg-shell prose-code:px-1 prose-code:py-0.5 prose-code:text-[0.9em] prose-pre:bg-ink prose-pre:text-shell">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap">{message.text}</div>
                  )}
                  {message.status ? (
                    <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-shell px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-steel">
                      <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                      {message.status}
                    </div>
                  ) : null}
                  {message.route ? (
                    <div className="mt-2 text-[10px] uppercase tracking-[0.2em] text-steel">
                      Route: {message.route}
                    </div>
                  ) : null}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-ink/10 p-4">
              <div className="flex flex-col gap-3">
                <label htmlFor="pulseiq-question" className="text-xs font-medium uppercase tracking-[0.18em] text-steel">
                  Ask a business question
                </label>
                <textarea
                  id="pulseiq-question"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={handleQuestionKeyDown}
                  placeholder="Ask about risk, refunds, complaints, or weird operational patterns..."
                  aria-describedby="pulseiq-input-help"
                  className="min-h-[88px] w-full resize-none rounded-[1.25rem] border border-ink/10 bg-shell px-4 py-3 text-sm text-ink outline-none placeholder:text-steel/80 focus:border-pine/40 focus:ring-2 focus:ring-pine/20"
                />
                <div id="pulseiq-input-help" className="text-xs text-steel">
                  Press Enter to send. Use Shift+Enter for a new line.
                </div>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void submitQuestion()}
                  className="flex items-center justify-center gap-2 rounded-[1.25rem] bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:brightness-95 focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />}
                  {loading ? "Thinking" : "Ask PulseIQ"}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setChatOpen(true)}
            aria-label="Open PulseIQ Assistant"
            className="group flex items-center gap-3 rounded-full border border-ink/10 bg-white/96 px-5 py-4 shadow-panel backdrop-blur-xl transition duration-200 hover:-translate-y-0.5 hover:border-ink/20 focus:outline-none focus:ring-2 focus:ring-accent/25"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white">
              <MessageSquare className="h-5 w-5" />
            </div>
            <div className="text-left">
              <div className="text-sm font-semibold text-ink">PulseIQ Assistant</div>
              <div className="text-xs text-steel">Ask about sales, refunds, risk, or complaints</div>
            </div>
          </button>
        )}
      </div>
    </div>
  );
}
