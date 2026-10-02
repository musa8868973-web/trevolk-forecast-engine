import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, ArrowDownRight, ArrowRight, ArrowUpRight, CalendarDays, ChartNoAxesCombined, ChevronDown, CircleHelp, Clock3, Download, LayoutDashboard, LoaderCircle, Menu, MoreHorizontal, Settings2, SlidersHorizontal, Sparkles, Store, TrendingUp, WandSparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

type ForecastInput = { store_id: number; date: string; promo: boolean; school_holiday: boolean; competition_distance: number };
type DayForecast = { day: string; fullDate: string; sales: number };
type Forecast = { data: DayForecast[]; revenue: number; adjustment: number; confidence: number };

const today = new Date();
const initialDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
const currency = (n: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);

function makeForecast(input: ForecastInput): Forecast {
  const start = new Date(`${input.date}T12:00:00`);
  const base = 7400 + (input.store_id % 11) * 190 + (input.promo ? 1450 : 0) - (input.school_holiday ? 620 : 0) + Math.min(input.competition_distance, 10000) * .08;
  const waves = [.91, 1.02, .97, 1.11, 1.04, 1.22, 1.16];
  const data = waves.map((factor, i) => {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    return { day: date.toLocaleDateString("en-US", { weekday: "short" }), fullDate: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }), sales: Math.round(base * factor + ((input.store_id * 17 + i * 83) % 290)) };
  });
  return { data, revenue: data.reduce((sum, d) => sum + d.sales, 0), adjustment: input.promo ? 4.8 : 3.2, confidence: Math.max(87, Math.min(97, 94 - (input.school_holiday ? 2 : 0) + (input.promo ? 1 : 0))) };
}

async function requestForecast(input: ForecastInput): Promise<Forecast> {
  const fallback = makeForecast(input);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch("http://localhost:8000/api/predict", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input), signal: controller.signal,
    });
    if (!response.ok) throw new Error("Prediction service unavailable");
    const result = await response.json();
    // Accept the expected weekly series if provided, while keeping the demo usable with any other response shape.
    const series = Array.isArray(result?.predictions) ? result.predictions : Array.isArray(result?.data) ? result.data : null;
    if (series?.length === 7 && series.every((item: unknown) => typeof item === "number" || (typeof item === "object" && item !== null && typeof (item as { sales?: unknown }).sales === "number"))) {
      const data = fallback.data.map((d, i) => ({ ...d, sales: Math.round(typeof series[i] === "number" ? series[i] : series[i].sales) }));
      return { data, revenue: data.reduce((sum, d) => sum + d.sales, 0), adjustment: Number(result.adjustment) || fallback.adjustment, confidence: Number(result.confidence) || fallback.confidence };
    }
    return fallback;
  } catch {
    return fallback;
  } finally {
    clearTimeout(timeout);
  }
}

function CountUp({ value, format }: { value: number; format: (n: number) => string }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    let frame = 0;
    const started = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - started) / 950, 1);
      setShown(value * (1 - Math.pow(1 - progress, 3)));
      if (progress < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return <span className="metric-number inline-block">{format(shown)}</span>;
}

function LoadingBlock({ className = "" }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-md ${className}`} />;
}

const nav = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Forecasts", icon: ChartNoAxesCombined },
  { label: "Stores", icon: Store },
  { label: "Analytics", icon: Activity },
];

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Overview | Forecaster" },
    { name: "description", content: "Generate dynamic sales forecasts and explore a clear seven-day revenue outlook." },
    { property: "og:title", content: "Overview | Forecaster" },
    { property: "og:description", content: "Generate dynamic sales forecasts and explore a clear seven-day revenue outlook." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary_large_image" },
  ] }),
  component: Dashboard,
});

function Dashboard() {
  const [form, setForm] = useState<ForecastInput>({ store_id: 1042, date: initialDate, promo: true, school_holiday: false, competition_distance: 850 });
  const [forecast, setForecast] = useState(() => makeForecast({ store_id: 1042, date: initialDate, promo: true, school_holiday: false, competition_distance: 850 }));
  const [loading, setLoading] = useState(false);
  const [updated, setUpdated] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const dateRange = useMemo(() => `${forecast.data[0]?.fullDate ?? ""} – ${forecast.data[6]?.fullDate ?? ""}`, [forecast]);

  const generate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (loading) return;
    setLoading(true);
    setUpdated(false);
    try {
      const [result] = await Promise.all([requestForecast(form), new Promise(resolve => setTimeout(resolve, 1100))]);
      setForecast(result);
      setUpdated(true);
    } finally { setLoading(false); }
  };

  const exportCsv = () => {
    const csv = ["Date,Predicted Sales", ...forecast.data.map(d => `${d.fullDate},${d.sales}`)].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "sales-forecast.csv"; a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-background font-sans text-foreground lg:flex">
      <aside className={`${mobileNav ? "fixed inset-y-0 left-0 z-50 flex" : "hidden"} w-[248px] shrink-0 flex-col border-r border-border bg-card lg:sticky lg:top-0 lg:flex lg:h-screen`}>
        <div className="flex h-[85px] items-center justify-between border-b border-divider px-7">
          <div className="flex items-center gap-2.5"><span className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground"><ChartNoAxesCombined size={19} strokeWidth={2.2}/></span><span className="text-[19px] font-bold tracking-tight">forecaster<span className="text-primary">.</span></span></div>
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Close menu" onClick={() => setMobileNav(false)}><X /></Button>
        </div>
        <div className="px-4 pt-7"><p className="px-3 text-[10px] font-bold uppercase tracking-[.14em] text-muted-foreground">Workspace</p><nav className="mt-4 space-y-1" aria-label="Main navigation">{nav.map(item => <div key={item.label} aria-current={item.active ? "page" : undefined} className={`flex h-10 items-center gap-3 rounded-md px-3 text-[13px] font-semibold ${item.active ? "bg-nav-active text-primary" : "text-muted-foreground"}`}><item.icon size={17} strokeWidth={1.9}/>{item.label}</div>)}</nav></div>
        <div className="mt-10 px-4"><p className="px-3 text-[10px] font-bold uppercase tracking-[.14em] text-muted-foreground">Preferences</p><div className="mt-4 flex h-10 items-center gap-3 px-3 text-[13px] font-semibold text-muted-foreground"><Settings2 size={17}/>Settings</div></div>
        <div className="mt-auto border-t border-divider p-5"><div className="flex items-center gap-3"><div className="flex size-9 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">JD</div><div className="min-w-0 flex-1"><p className="truncate text-[13px] font-bold">Jordan Davis</p><p className="text-[11px] text-muted-foreground">Workspace admin</p></div><MoreHorizontal size={17} className="text-muted-foreground"/></div></div>
      </aside>
      {mobileNav && <div className="fixed inset-0 z-40 bg-foreground/30 lg:hidden" onClick={() => setMobileNav(false)} />}

      <div className="min-w-0 flex-1">
        <header className="flex h-[70px] items-center justify-between border-b border-border bg-card px-5 sm:px-8 lg:h-[85px] lg:px-10 xl:px-14">
          <div className="flex items-center gap-3"><Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open menu" onClick={() => setMobileNav(true)}><Menu/></Button><span className="text-[13px] text-muted-foreground">Workspace</span><span className="text-muted-foreground/50">/</span><span className="text-[13px] font-semibold">Overview</span></div>
          <div className="flex items-center gap-3 sm:gap-5"><span className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><span className="size-1.5 rounded-full bg-positive"/> System operational</span><span className="hidden h-5 w-px bg-border sm:block"/><Button variant="ghost" size="icon" aria-label="Help" title="Help" onClick={() => window.alert("Forecaster uses demo data when the prediction service is unavailable.")}><CircleHelp size={18} className="text-muted-foreground"/></Button><div className="flex size-8 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">JD</div></div>
        </header>

        <main className="mx-auto max-w-[1500px] px-5 pb-16 pt-8 sm:px-8 lg:px-10 lg:pt-11 xl:px-14">
          <div className="reveal flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between"><div><div className="mb-3 flex items-center gap-2 text-xs font-semibold text-muted-foreground"><span className="size-1.5 rounded-full bg-primary"/> SALES INTELLIGENCE <span className="text-border">/</span> OVERVIEW</div><h1 className="text-[30px] font-bold leading-tight sm:text-[36px]">Sales overview</h1><p className="mt-2 text-[13px] text-muted-foreground sm:text-sm">Your next seven days, a little more predictable.</p></div><div className="flex items-center gap-2 self-start rounded-md border border-border bg-card px-3.5 py-2.5 text-xs font-semibold text-foreground sm:self-auto"><CalendarDays size={15} className="text-muted-foreground"/> {dateRange} <ChevronDown size={14} className="ml-2 text-muted-foreground"/></div></div>

          <div className="stagger mt-9 grid gap-4 md:grid-cols-3">
            <MetricCard label="EXPECTED REVENUE" icon={TrendingUp} value={forecast.revenue} format={currency} loading={loading} note="vs. previous 7 days" change="+12.8%" />
            <MetricCard label="OPTIMAL PRICE ADJUSTMENT" icon={SlidersHorizontal} value={forecast.adjustment} format={n => `+${n.toFixed(1)}%`} loading={loading} note="Recommended increase" change="Optimal" />
            <MetricCard label="CONFIDENCE SCORE" icon={Sparkles} value={forecast.confidence} format={n => `${Math.round(n)}%`} loading={loading} note="Model accuracy" change="High confidence" />
          </div>

          <div className="mt-6 grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_318px]">
            <section className="reveal reveal-chart min-w-0 rounded-lg border border-border bg-card p-5 sm:p-7" aria-label="Predicted sales chart">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex items-center gap-2"><h2 className="text-[17px] font-bold">Predicted sales</h2><span className="rounded bg-positive-surface px-2 py-1 text-[10px] font-bold text-positive">↗ +12.8%</span></div><p className="mt-1.5 text-xs text-muted-foreground">Projected daily revenue for the upcoming week</p></div><Button variant="outline" size="sm" onClick={exportCsv} className="self-start gap-2 border-border shadow-none transition-transform hover:-translate-y-0.5"><Download size={14}/> Export</Button></div>
              <div className="mt-8 flex items-center gap-2 text-[11px] font-semibold text-muted-foreground"><span className="size-2 rounded-full bg-chart-line"/> Predicted sales</div>
              <div className="mt-5 h-[265px] w-full sm:h-[330px]" aria-label="Seven-day predicted sales graph">
                {loading ? <div className="flex h-full flex-col justify-end gap-5 pb-6"><LoadingBlock className="h-4 w-1/3"/><LoadingBlock className="h-4 w-2/3"/><LoadingBlock className="h-32 w-full"/></div> : <ResponsiveContainer width="100%" height="100%"><AreaChart data={forecast.data} margin={{ top: 12, right: 5, left: -17, bottom: 0 }}><defs><linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--chart-fill)" stopOpacity={.7}/><stop offset="100%" stopColor="var(--chart-fill)" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} strokeDasharray="3 5" className="chart-grid"/><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} dy={12}/><YAxis axisLine={false} tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} tickFormatter={v => `$${Math.round(v/1000)}k`} domain={[0, "dataMax + 1500"]}/><Tooltip cursor={{ stroke: "var(--border)", strokeDasharray: "4 4" }} content={({ active, payload }) => active && payload?.length ? <div className="rounded-md border border-border bg-card px-3 py-2 shadow-sm"><p className="text-[11px] text-muted-foreground">{payload[0]?.payload?.fullDate}</p><p className="mt-1 text-sm font-bold text-foreground">{currency(Number(payload[0]?.value))}</p></div> : null}/><Area type="monotone" dataKey="sales" stroke="var(--chart-line)" strokeWidth={3} fill="url(#salesFill)" isAnimationActive animationDuration={1200} activeDot={{ r: 5, fill: "var(--chart-line)", stroke: "var(--card)", strokeWidth: 3 }}/></AreaChart></ResponsiveContainer>}
              </div>
              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-divider pt-5 text-[11px] text-muted-foreground"><span className="flex items-center gap-2"><Clock3 size={14}/> {updated ? "Forecast just updated" : "Based on current inputs"}</span><span className="flex items-center gap-1.5 font-medium text-positive"><span className="size-1.5 rounded-full bg-positive"/> {updated ? "Latest forecast" : "Ready to forecast"}</span></div>
            </section>

            <section className="reveal reveal-input rounded-lg border border-border bg-card p-5 sm:p-6" aria-labelledby="forecast-heading"><div className="flex items-start justify-between"><div className="flex size-10 items-center justify-center rounded-md bg-accent text-primary"><WandSparkles size={19}/></div><MoreHorizontal size={18} className="text-muted-foreground"/></div><h2 id="forecast-heading" className="mt-5 text-[17px] font-bold">Generate forecast</h2><p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">Fine-tune your inputs for a more accurate outlook.</p>
              <form className="mt-7 space-y-5" onSubmit={generate}>
                <label className="block"><span className="mb-2 block text-xs font-semibold">Store ID</span><div className="relative"><Store size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"/><Input required type="number" min="1" value={form.store_id} onChange={e => setForm({ ...form, store_id: Number(e.target.value) })} className="h-10 pl-10 shadow-none transition-all duration-200 hover:border-ring focus-visible:ring-2"/></div></label>
                <label className="block"><span className="mb-2 block text-xs font-semibold">Forecast start date</span><Input required type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} className="h-10 shadow-none transition-all duration-200 hover:border-ring focus-visible:ring-2"/></label>
                <div className="border-t border-divider pt-5"><div className="flex items-center justify-between gap-3"><div><label htmlFor="promo" className="text-xs font-semibold">Promotion active</label><p className="mt-0.5 text-[11px] text-muted-foreground">Include promotional impact</p></div><Switch id="promo" checked={form.promo} onCheckedChange={promo => setForm({ ...form, promo })}/></div><div className="mt-5 flex items-center justify-between gap-3"><div><label htmlFor="holiday" className="text-xs font-semibold">School holiday</label><p className="mt-0.5 text-[11px] text-muted-foreground">Adjust for holiday demand</p></div><Switch id="holiday" checked={form.school_holiday} onCheckedChange={school_holiday => setForm({ ...form, school_holiday })}/></div></div>
                <label className="block border-t border-divider pt-5"><span className="mb-2 block text-xs font-semibold">Competition distance <span className="font-normal text-muted-foreground">(meters)</span></span><Input required type="number" min="0" value={form.competition_distance} onChange={e => setForm({ ...form, competition_distance: Number(e.target.value) })} className="h-10 shadow-none transition-all duration-200 hover:border-ring focus-visible:ring-2"/></label>
                <Button type="submit" variant="dashboard" disabled={loading} className="h-11 w-full text-[13px] font-bold">{loading ? <><LoaderCircle className="animate-spin"/> Generating...</> : <><Sparkles size={16}/> Generate forecast <ArrowRight size={16} className="ml-auto"/></>}</Button>
              </form>
              <p className="mt-4 text-center text-[11px] text-muted-foreground">Powered by predictive intelligence</p>
            </section>
          </div>

          <section className="reveal reveal-breakdown mt-6"><div className="mb-4 flex items-center justify-between"><div><h2 className="text-[17px] font-bold">Daily breakdown</h2><p className="mt-1 text-xs text-muted-foreground">A closer look at your projected week</p></div><span className="text-xs font-medium text-muted-foreground">7 days <ChevronDown size={13} className="ml-1 inline"/></span></div><div className="overflow-x-auto rounded-lg border border-border bg-card"><table className="w-full min-w-[520px] text-left text-xs"><thead className="border-b border-divider bg-muted/50 text-[10px] font-bold uppercase tracking-[.09em] text-muted-foreground"><tr><th className="px-6 py-4">Day</th><th className="px-6 py-4">Date</th><th className="px-6 py-4">Predicted sales</th><th className="px-6 py-4">Trend</th></tr></thead><tbody>{forecast.data.map((d, i) => <tr key={`${d.fullDate}-${i}`} className="border-b border-divider last:border-b-0"><td className="px-6 py-3.5 font-semibold">{d.day}</td><td className="px-6 py-3.5 text-muted-foreground">{d.fullDate}</td><td className="px-6 py-3.5 font-bold">{loading ? <LoadingBlock className="h-4 w-16"/> : currency(d.sales)}</td><td className="px-6 py-3.5">{i === 0 ? <span className="text-muted-foreground">—</span> : d.sales >= (forecast.data[i-1]?.sales ?? d.sales) ? <ArrowUpRight size={16} className="text-positive"/> : <ArrowDownRight size={16} className="text-muted-foreground"/>}</td></tr>)}</tbody></table></div></section>
        </main>
      </div>
    </div>
  );
}

function MetricCard({ label, icon: Icon, value, format, loading, note, change }: { label: string; icon: typeof TrendingUp; value: number; format: (n: number) => string; loading: boolean; note: string; change: string }) {
  return <div className="reveal min-w-0 rounded-lg border border-border bg-card p-5 transition-all duration-300 hover:-translate-y-1 hover:border-ring sm:p-6"><div className="flex items-center justify-between"><span className="text-[10px] font-bold tracking-[.1em] text-muted-foreground">{label}</span><span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-accent text-primary"><Icon size={16}/></span></div><div className="mt-5 h-[41px] text-[29px] font-bold leading-none tracking-tight sm:text-[31px]">{loading ? <LoadingBlock className="h-9 w-36"/> : <CountUp value={value} format={format}/>}</div><div className="mt-4 flex flex-wrap items-center gap-2 text-[11px]"><span className="rounded bg-positive-surface px-2 py-1 font-bold text-positive">{change}</span><span className="text-muted-foreground">{note}</span></div></div>;
}