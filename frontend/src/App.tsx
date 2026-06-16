import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import {
  BarChart3,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileSpreadsheet,
  LayoutDashboard,
  MessageSquareText,
  Moon,
  Sparkles,
  Sun,
  Table2,
  Target,
  UploadCloud,
  Video,
  Zap
} from "lucide-react";
import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

import type {
  Analysis,
  CalendarItem,
  ForecastPoint,
  HeatmapCell,
  PillarPerformance,
  UploadResponse,
  VideoPerformance
} from "./types";
import { formatDate, formatMonth, formatNumber, formatPercent, formatScore, sum } from "./lib/format";

type PageId = "overview" | "content" | "posting" | "insights" | "strategy" | "upload";

type ChatMessage = {
  role: "user" | "agent";
  content: string;
};

const navItems: Array<{ id: PageId; label: string; icon: typeof LayoutDashboard }> = [
  { id: "overview", label: "Dashboard", icon: LayoutDashboard },
  { id: "content", label: "Content Analysis", icon: BarChart3 },
  { id: "posting", label: "Posting Time", icon: Clock3 },
  { id: "insights", label: "AI Insights", icon: Sparkles },
  { id: "strategy", label: "Monthly Strategy", icon: CalendarDays },
  { id: "upload", label: "Data Upload", icon: UploadCloud }
];

const chartPalette = ["#0068FF", "#F3A000", "#EE2374", "#8FC9FF", "#A2D2FF"];
const heatmapWeekdays = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("overview");
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem("theme");
    if (stored) return stored === "dark";
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "agent",
      content: "Ready to review the active dataset."
    }
  ]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const analysis = dataset?.analysis;
  const chartTone = useMemo(
    () => ({
      grid: darkMode ? "#24304A" : "#BDE0FF",
      axis: darkMode ? "#CFE6FF" : "#2C4973",
      foreground: darkMode ? "#FFFFFF" : "#091836",
      muted: darkMode ? "#8FC9FF" : "#A2D2FF",
      accent: darkMode ? "#8FC9FF" : "#0068FF"
    }),
    [darkMode]
  );

  async function uploadFile(file: File) {
    setUploadError(null);
    if (!/\.(csv|xlsx|xls)$/i.test(file.name)) {
      setUploadError("Only CSV, XLSX, or XLS files are supported.");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("/api/upload", { method: "POST", body: formData });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Upload failed.");
      setDataset(payload);
      setSelectedFile(file);
      setActivePage("overview");
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function loadSample() {
    setUploadError(null);
    setUploading(true);
    try {
      const response = await fetch("/sample-data/content_performance_sample.csv");
      if (!response.ok) throw new Error("Sample dataset is not available.");
      const blob = await response.blob();
      const file = new File([blob], "content_performance_sample.csv", { type: "text/csv" });
      await uploadFile(file);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Could not load sample data.");
    } finally {
      setUploading(false);
    }
  }

  async function sendChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message || chatLoading) return;

    setChatInput("");
    setChatMessages((items) => [...items, { role: "user", content: message }]);
    setChatLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, dataset_id: dataset?.dataset_id })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Agent request failed.");
      setChatMessages((items) => [...items, { role: "agent", content: payload.answer }]);
    } catch (error) {
      setChatMessages((items) => [
        ...items,
        { role: "agent", content: error instanceof Error ? error.message : "Agent request failed." }
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-transparent text-foreground">
      <Sidebar activePage={activePage} onSelect={setActivePage} />
      <main className="min-h-screen md:pl-64">
        <Header
          activePage={activePage}
          dataset={dataset}
          darkMode={darkMode}
          onToggleTheme={() => setDarkMode((value) => !value)}
          onUpload={() => setActivePage("upload")}
        />
        <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
          <MobileNav activePage={activePage} onSelect={setActivePage} />
          {activePage === "overview" && (
            <OverviewPage
              analysis={analysis}
              chartTone={chartTone}
              onUpload={() => setActivePage("upload")}
              onLoadSample={loadSample}
              uploading={uploading}
            />
          )}
          {activePage === "content" && <ContentAnalysisPage analysis={analysis} chartTone={chartTone} />}
          {activePage === "posting" && <PostingTimePage analysis={analysis} chartTone={chartTone} />}
          {activePage === "insights" && (
            <AIInsightsPage
              analysis={analysis}
              chatInput={chatInput}
              chatLoading={chatLoading}
              chatMessages={chatMessages}
              onChatInput={setChatInput}
              onSendChat={sendChat}
            />
          )}
          {activePage === "strategy" && <MonthlyStrategyPage analysis={analysis} chartTone={chartTone} />}
          {activePage === "upload" && (
            <DataUploadPage
              analysis={analysis}
              dataset={dataset}
              selectedFile={selectedFile}
              uploading={uploading}
              uploadError={uploadError}
              onFileSelect={setSelectedFile}
              onUpload={uploadFile}
              onLoadSample={loadSample}
            />
          )}
        </div>
      </main>
    </div>
  );
}

function Sidebar({ activePage, onSelect }: { activePage: PageId; onSelect: (page: PageId) => void }) {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-border bg-surface/85 backdrop-blur md:flex md:flex-col">
      <div className="flex h-16 items-center gap-3 border-b border-border px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-accent-foreground">
          <Zap className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold">Content Strategist</p>
          <p className="text-xs text-muted">AI analytics agent</p>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.id === activePage;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className={`flex h-10 items-center gap-3 rounded-full px-3 text-sm transition-colors ${
                isActive ? "bg-accent text-accent-foreground" : "text-muted hover:bg-surface-muted hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

function Header({
  activePage,
  dataset,
  darkMode,
  onToggleTheme,
  onUpload
}: {
  activePage: PageId;
  dataset: UploadResponse | null;
  darkMode: boolean;
  onToggleTheme: () => void;
  onUpload: () => void;
}) {
  const active = navItems.find((item) => item.id === activePage);
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface/75 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-[1440px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase text-muted">AI Content Strategist</p>
          <h1 className="truncate text-lg font-semibold tracking-normal text-accent">{active?.label}</h1>
        </div>
        <div className="flex items-center gap-2">
          {dataset ? (
            <div className="hidden max-w-[280px] items-center gap-2 rounded-full border border-border bg-surface/85 px-3 py-2 text-xs text-muted sm:flex">
              <CheckCircle2 className="h-4 w-4 text-accent" />
              <span className="truncate">{dataset.filename || "Uploaded dataset"}</span>
            </div>
          ) : null}
          <button type="button" className="button-secondary hidden sm:inline-flex" onClick={onUpload}>
            <UploadCloud className="h-4 w-4" />
            Upload
          </button>
          <button
            type="button"
            className="icon-button"
            onClick={onToggleTheme}
            aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </header>
  );
}

function MobileNav({ activePage, onSelect }: { activePage: PageId; onSelect: (page: PageId) => void }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 md:hidden">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = item.id === activePage;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onSelect(item.id)}
            className={`inline-flex h-10 shrink-0 items-center gap-2 rounded-full border px-3 text-sm ${
              isActive
                ? "border-accent bg-accent text-accent-foreground"
                : "border-border bg-surface text-muted hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

function OverviewPage({
  analysis,
  chartTone,
  onUpload,
  onLoadSample,
  uploading
}: {
  analysis?: Analysis;
  chartTone: ChartTone;
  onUpload: () => void;
  onLoadSample: () => void;
  uploading: boolean;
}) {
  if (!analysis) return <EmptyState onUpload={onUpload} onLoadSample={onLoadSample} uploading={uploading} />;

  const videos = analysis.per_video || [];
  const summary = analysis.summary || {};
  const totalFollowers = sum(videos.map((item) => item.followers_gained));
  const pillarData = (analysis.pillar_performance || []).slice(0, 8).map((item) => ({
    pillar: item.content_pillar || "Uncategorized",
    score: Number(item.avg_score || 0),
    views: Number(item.total_views || 0)
  }));
  const forecastData = buildForecastData(analysis.growth_forecast?.actual, analysis.growth_forecast?.forecast);
  const topVideos = [...videos].sort(byScoreDesc).slice(0, 6);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={Video} label="Total Videos" value={formatNumber(summary.total_videos, false)} />
        <KpiCard icon={BarChart3} label="Total Views" value={formatNumber(summary.total_views)} />
        <KpiCard icon={Target} label="Total Engagement" value={formatNumber(summary.total_engagements)} />
        <KpiCard icon={Sparkles} label="Engagement Rate" value={formatPercent(summary.avg_engagement_rate)} />
        <KpiCard icon={Zap} label="Followers Gained" value={formatNumber(totalFollowers)} />
        <KpiCard icon={Clock3} label="Best Posting Time" value={summary.best_slot?.slot || "Insufficient data"} />
        <KpiCard icon={Table2} label="Best Content Pillar" value={summary.best_pillar?.content_pillar || "-"} />
        <KpiCard icon={CheckCircle2} label="Avg Performance" value={formatScore(summary.avg_performance_score)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Growth Trend" meta={analysis.growth_forecast?.outlook || summary.growth_outlook}>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forecastData}>
                <CartesianGrid stroke={chartTone.grid} vertical={false} />
                <XAxis dataKey="date" tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="actual"
                  name="Actual views"
                  stroke={chartTone.foreground}
                  fill={chartTone.foreground}
                  fillOpacity={0.08}
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="forecast"
                  name="Forecast views"
                  stroke={chartTone.accent}
                  fill={chartTone.accent}
                  fillOpacity={0.12}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Content Pillars" meta="Average performance score">
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pillarData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid stroke={chartTone.grid} horizontal={false} />
                <XAxis type="number" tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis
                  type="category"
                  dataKey="pillar"
                  width={112}
                  tick={{ fill: chartTone.axis, fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="score" name="Score" radius={[0, 4, 4, 0]}>
                  {pillarData.map((_, index) => (
                    <Cell key={index} fill={chartPalette[index % chartPalette.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <ExecutiveSummary summary={analysis.executive_summary} />
        <Panel title="Top Performing Videos" meta="Ranked by composite performance score">
          <VideoTable videos={topVideos} compact />
        </Panel>
      </div>
    </div>
  );
}

function ContentAnalysisPage({ analysis, chartTone }: { analysis?: Analysis; chartTone: ChartTone }) {
  if (!analysis) return <EmptySection label="Upload a dataset to analyze content performance." />;

  const videos = analysis.per_video || [];
  const topVideos = [...videos].sort(byScoreDesc).slice(0, 8);
  const worstVideos = [...videos].sort(byScoreAsc).slice(0, 8);
  const pillarData = (analysis.pillar_performance || []).slice(0, 10).map((item) => ({
    pillar: item.content_pillar || "Uncategorized",
    score: Number(item.avg_score || 0),
    engagement: Number(item.avg_engagement_rate || 0),
    views: Number(item.total_views || 0),
    videos: Number(item.videos || 0)
  }));
  const scatterData = videos.map((item) => ({
    title: item.title || "Untitled",
    views: Number(item.views || 0),
    engagement_rate: Number(item.engagement_rate || 0),
    score: Number(item.performance_score || 0)
  }));

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Top Performing Videos" meta="Highest scoring assets">
          <VideoTable videos={topVideos} />
        </Panel>
        <Panel title="Worst Performing Videos" meta="Lowest scoring assets">
          <VideoTable videos={worstVideos} />
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <Panel title="Content Pillar Comparison" meta="Score and engagement by pillar">
          <div className="h-[340px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pillarData}>
                <CartesianGrid stroke={chartTone.grid} vertical={false} />
                <XAxis dataKey="pillar" tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="score" name="Score" fill={chartTone.accent} radius={[4, 4, 0, 0]} />
                <Bar dataKey="engagement" name="Engagement rate" fill={chartTone.muted} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Engagement Analysis" meta="Views versus engagement rate">
          <div className="h-[340px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid stroke={chartTone.grid} />
                <XAxis
                  type="number"
                  dataKey="views"
                  name="Views"
                  tick={{ fill: chartTone.axis, fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  type="number"
                  dataKey="engagement_rate"
                  name="Engagement rate"
                  tick={{ fill: chartTone.axis, fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip content={<ChartTooltip />} />
                <Scatter name="Videos" data={scatterData} fill={chartTone.accent} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function PostingTimePage({ analysis, chartTone }: { analysis?: Analysis; chartTone: ChartTone }) {
  if (!analysis) return <EmptySection label="Upload a dataset to discover optimal posting windows." />;

  const optimalTime = analysis.optimal_time;
  const topSlots = optimalTime?.top_slots || [];
  const slotData = topSlots.map((item) => ({
    slot: item.slot || `${item.posted_weekday_label || ""} ${String(item.posted_hour || 0).padStart(2, "0")}:00`,
    score: Number(item.avg_score || 0),
    engagement: Number(item.avg_engagement_rate || 0),
    views: Number(item.median_views || 0)
  }));

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        <KpiCard icon={Clock3} label="Best Time to Post" value={analysis.summary?.best_slot?.slot || "-"} />
        <KpiCard icon={Target} label="Best Slot Score" value={formatScore(analysis.summary?.best_slot?.avg_score)} />
        <KpiCard icon={Video} label="Videos With Time Data" value={optimalTime?.sample_size_note || "No timing note"} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Performance by Time Slot" meta="Top posting windows">
          <div className="h-[340px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={slotData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid stroke={chartTone.grid} horizontal={false} />
                <XAxis type="number" tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis
                  type="category"
                  dataKey="slot"
                  width={92}
                  tick={{ fill: chartTone.axis, fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="score" name="Score" fill={chartTone.accent} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Posting Performance Heatmap" meta={optimalTime?.note || "Average score by weekday and hour"}>
          <Heatmap cells={optimalTime?.heatmap || []} chartTone={chartTone} />
        </Panel>
      </div>
    </div>
  );
}

function AIInsightsPage({
  analysis,
  chatInput,
  chatLoading,
  chatMessages,
  onChatInput,
  onSendChat
}: {
  analysis?: Analysis;
  chatInput: string;
  chatLoading: boolean;
  chatMessages: ChatMessage[];
  onChatInput: (value: string) => void;
  onSendChat: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (!analysis) return <EmptySection label="Upload a dataset to generate AI insights." />;

  const strengths = analysis.patterns?.success_patterns || [];
  const weaknesses = analysis.patterns?.failure_patterns || [];
  const opportunities = buildOpportunities(analysis);
  const recommendations = [
    ...(analysis.content_calendar?.strategy || []),
    analysis.summary?.growth_outlook ? `Growth outlook: ${analysis.summary.growth_outlook}.` : ""
  ].filter(Boolean);

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
      <div className="flex flex-col gap-6">
        <div className="grid gap-4 lg:grid-cols-2">
          <InsightGroup title="Channel Strengths" items={strengths} />
          <InsightGroup title="Channel Weaknesses" items={weaknesses} />
          <InsightGroup title="Growth Opportunities" items={opportunities} />
          <InsightGroup title="Content Direction" items={recommendations} />
        </div>
        <ExecutiveSummary summary={analysis.executive_summary} />
      </div>

      <Panel title="Ask Strategist" meta={analysis.summary?.date_range}>
        <div className="flex h-[560px] flex-col">
          <div className="flex-1 space-y-3 overflow-y-auto pr-1">
            {chatMessages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`rounded-lg border px-3 py-2 text-sm leading-6 ${
                  message.role === "user"
                    ? "border-accent/30 bg-accent/10 text-foreground"
                    : "border-border bg-surface-muted text-muted"
                }`}
              >
            <p className="mb-1 text-xs font-medium uppercase text-subtle">
                  {message.role === "user" ? "You" : "Agent"}
                </p>
                <p className="whitespace-pre-line">{message.content}</p>
              </div>
            ))}
          </div>
          <form className="mt-4 flex gap-2" onSubmit={onSendChat}>
            <input
              className="input-field min-w-0 flex-1"
              value={chatInput}
              onChange={(event) => onChatInput(event.target.value)}
              placeholder="Ask for a campaign angle..."
            />
            <button type="submit" className="button-primary" disabled={chatLoading || !chatInput.trim()}>
              <MessageSquareText className="h-4 w-4" />
              Ask
            </button>
          </form>
        </div>
      </Panel>
    </div>
  );
}

function MonthlyStrategyPage({ analysis, chartTone }: { analysis?: Analysis; chartTone: ChartTone }) {
  if (!analysis) return <EmptySection label="Upload a dataset to build next month's strategy." />;

  const calendar = analysis.content_calendar;
  const mixData = buildContentMix(analysis.pillar_performance || []);
  const targets = [
    {
      label: "Recommended Posts",
      value: formatNumber(calendar?.recommended_posts, false),
      detail: formatMonth(calendar?.month)
    },
    {
      label: "Projected Views",
      value: formatNumber(analysis.growth_forecast?.forecast_next_30_views),
      detail: "Next 30 days"
    },
    {
      label: "Growth Rate",
      value: formatPercent(analysis.growth_forecast?.growth_rate_pct),
      detail: analysis.growth_forecast?.outlook || "Forecast"
    }
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        {targets.map((target) => (
          <div key={target.label} className="panel p-5">
            <p className="text-sm text-muted">{target.label}</p>
            <p className="mt-2 text-2xl font-semibold tracking-normal">{target.value}</p>
            <p className="mt-2 line-clamp-2 text-sm text-muted">{target.detail}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <Panel title="Recommended Content Mix" meta="Based on pillar performance">
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mixData}>
                <CartesianGrid stroke={chartTone.grid} vertical={false} />
                <XAxis dataKey="pillar" tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: chartTone.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="share" name="Mix %" fill={chartTone.accent} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Suggested Content Calendar" meta={formatMonth(calendar?.month)}>
          <CalendarTable items={calendar?.items || []} />
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {(calendar?.strategy || []).map((item, index) => (
          <RecommendationCard key={`${item}-${index}`} index={index + 1} text={item} />
        ))}
      </div>
    </div>
  );
}

function DataUploadPage({
  analysis,
  dataset,
  selectedFile,
  uploading,
  uploadError,
  onFileSelect,
  onUpload,
  onLoadSample
}: {
  analysis?: Analysis;
  dataset: UploadResponse | null;
  selectedFile: File | null;
  uploading: boolean;
  uploadError: string | null;
  onFileSelect: (file: File | null) => void;
  onUpload: (file: File) => void;
  onLoadSample: () => void;
}) {
  const isValid = selectedFile ? /\.(csv|xlsx|xls)$/i.test(selectedFile.name) : false;

  return (
    <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
      <Panel title="Data Upload" meta="CSV, XLSX, or XLS">
        <div className="space-y-4">
          <label className="flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border bg-surface-muted px-6 text-center transition-colors hover:border-accent hover:bg-accent/5">
            <UploadCloud className="h-8 w-8 text-muted" />
            <span className="mt-4 text-sm font-medium text-foreground">
              {selectedFile ? selectedFile.name : "Select a content performance file"}
            </span>
            <span className="mt-2 text-xs text-muted">CSV, XLSX, XLS</span>
            <input
              className="sr-only"
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(event) => onFileSelect(event.target.files?.[0] || null)}
            />
          </label>

          {selectedFile ? (
            <div className="rounded-lg border border-border bg-surface-muted px-3 py-3 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="truncate text-foreground">{selectedFile.name}</span>
                <span className={isValid ? "text-accent" : "text-muted"}>{isValid ? "Valid" : "Unsupported"}</span>
              </div>
              <p className="mt-1 text-xs text-muted">{formatNumber(selectedFile.size, false)} bytes</p>
            </div>
          ) : null}

          {uploadError ? (
            <div className="rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-foreground">
              {uploadError}
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="button-primary"
              onClick={() => selectedFile && onUpload(selectedFile)}
              disabled={!selectedFile || !isValid || uploading}
            >
              <FileSpreadsheet className="h-4 w-4" />
              {uploading ? "Uploading" : "Analyze File"}
            </button>
            <button type="button" className="button-secondary" onClick={onLoadSample} disabled={uploading}>
              Load Sample
            </button>
          </div>

          {dataset ? (
            <div className="rounded-lg border border-border bg-surface-muted px-3 py-3 text-sm text-muted">
              <p className="font-medium text-foreground">{dataset.filename || "Dataset"}</p>
              <p>{formatNumber(dataset.rows, false)} rows processed</p>
            </div>
          ) : null}
        </div>
      </Panel>

      <Panel title="Data Preview" meta="First analyzed rows">
        {analysis ? <VideoTable videos={(analysis.per_video || []).slice(0, 10)} /> : <EmptyTable />}
      </Panel>
    </div>
  );
}

function EmptyState({
  onUpload,
  onLoadSample,
  uploading
}: {
  onUpload: () => void;
  onLoadSample: () => void;
  uploading: boolean;
}) {
  return (
    <div className="panel flex min-h-[560px] items-center justify-center p-6">
      <div className="max-w-md text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
          <UploadCloud className="h-5 w-5" />
        </div>
        <h2 className="mt-5 text-xl font-semibold tracking-normal">Upload channel data</h2>
        <p className="mt-3 text-sm leading-6 text-muted">CSV or Excel performance file.</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button type="button" className="button-primary" onClick={onUpload}>
            Upload Dataset
          </button>
          <button type="button" className="button-secondary" onClick={onLoadSample} disabled={uploading}>
            Load Sample
          </button>
        </div>
      </div>
    </div>
  );
}

function EmptySection({ label }: { label: string }) {
  return (
    <div className="panel flex min-h-[420px] items-center justify-center p-6 text-center text-sm text-muted">
      {label}
    </div>
  );
}

function EmptyTable() {
  return (
    <div className="flex h-[260px] items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted">
      No uploaded data
    </div>
  );
}

function KpiCard({ icon: Icon, label, value }: { icon: typeof Video; label: string; value: string }) {
  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted">{label}</p>
        <Icon className="h-4 w-4 text-accent" />
      </div>
      <p className="mt-4 min-h-8 truncate text-2xl font-semibold tracking-normal text-foreground">{value}</p>
    </div>
  );
}

function Panel({ title, meta, children }: { title: string; meta?: string; children: ReactNode }) {
  return (
    <section className="panel overflow-hidden">
      <div className="flex min-h-16 items-start justify-between gap-4 border-b border-border px-5 py-4">
        <div className="min-w-0">
          <h2 className="truncate text-base font-semibold tracking-normal text-accent">{title}</h2>
          {meta ? <p className="mt-1 line-clamp-2 text-sm text-muted">{meta}</p> : null}
        </div>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function VideoTable({ videos, compact = false }: { videos: VideoPerformance[]; compact?: boolean }) {
  if (!videos.length) return <EmptyTable />;

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr className="text-xs uppercase text-subtle">
            <th className="border-b border-border pb-3 pr-4 font-medium">Video</th>
            <th className="border-b border-border px-4 pb-3 font-medium">Pillar</th>
            <th className="border-b border-border px-4 pb-3 font-medium">Views</th>
            <th className="border-b border-border px-4 pb-3 font-medium">Engagement</th>
            <th className="border-b border-border px-4 pb-3 font-medium">Score</th>
            {!compact ? <th className="border-b border-border pl-4 pb-3 font-medium">Tier</th> : null}
          </tr>
        </thead>
        <tbody>
          {videos.map((video, index) => (
            <tr key={video.video_id || `${video.title}-${index}`}>
              <td className="border-b border-border/70 py-3 pr-4">
                <div className="max-w-[320px]">
                  <p className="truncate font-medium text-foreground">{video.title || "Untitled video"}</p>
                  <p className="mt-1 text-xs text-muted">{video.posted_at || video.platform || "-"}</p>
                </div>
              </td>
              <td className="border-b border-border/70 px-4 py-3 text-muted">{video.content_pillar || "-"}</td>
              <td className="border-b border-border/70 px-4 py-3 tabular-nums">{formatNumber(video.views)}</td>
              <td className="border-b border-border/70 px-4 py-3 tabular-nums">
                {formatPercent(video.engagement_rate)}
              </td>
              <td className="border-b border-border/70 px-4 py-3 tabular-nums">{formatScore(video.performance_score)}</td>
              {!compact ? (
                <td className="border-b border-border/70 py-3 pl-4">
                  <span className="badge">{video.performance_tier || "-"}</span>
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CalendarTable({ items }: { items: CalendarItem[] }) {
  if (!items.length) return <EmptyTable />;

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[820px] border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr className="text-xs uppercase text-subtle">
            <th className="border-b border-border pb-3 pr-4 font-medium">Date</th>
            <th className="border-b border-border px-4 pb-3 font-medium">Pillar</th>
            <th className="border-b border-border px-4 pb-3 font-medium">Format</th>
            <th className="border-b border-border px-4 pb-3 font-medium">Hook</th>
            <th className="border-b border-border pl-4 pb-3 font-medium">KPI</th>
          </tr>
        </thead>
        <tbody>
          {items.slice(0, 16).map((item, index) => (
            <tr key={`${item.date}-${item.time}-${index}`}>
              <td className="border-b border-border/70 py-3 pr-4">
                <p className="font-medium text-foreground">{formatDate(item.date)}</p>
                <p className="mt-1 text-xs text-muted">
                  {item.weekday || "-"} {item.time || ""}
                </p>
              </td>
              <td className="border-b border-border/70 px-4 py-3">{item.pillar || "-"}</td>
              <td className="border-b border-border/70 px-4 py-3 text-muted">{item.format || "-"}</td>
              <td className="border-b border-border/70 px-4 py-3 text-muted">{item.hook || "-"}</td>
              <td className="border-b border-border/70 py-3 pl-4 text-muted">{item.primary_kpi || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Heatmap({ cells, chartTone }: { cells: HeatmapCell[]; chartTone: ChartTone }) {
  const hours = Array.from(new Set(cells.map((cell) => cell.hour).filter((hour): hour is number => hour !== undefined)))
    .sort((a, b) => a - b)
    .slice(0, 18);
  const visibleHours = hours.length ? hours : Array.from({ length: 12 }, (_, index) => index + 8);
  const maxScore = Math.max(...cells.map((cell) => Number(cell.score || 0)), 1);
  const lookup = new Map(cells.map((cell) => [`${cell.weekday}-${cell.hour}`, Number(cell.score || 0)]));

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[720px]">
        <div
          className="grid gap-1 text-xs text-muted"
          style={{ gridTemplateColumns: `48px repeat(${visibleHours.length}, minmax(34px, 1fr))` }}
        >
          <div />
          {visibleHours.map((hour) => (
            <div key={hour} className="py-1 text-center tabular-nums">
              {String(hour).padStart(2, "0")}
            </div>
          ))}
          {heatmapWeekdays.map((weekday) => (
            <FragmentHeatmapRow
              key={weekday}
              weekday={weekday}
              hours={visibleHours}
              lookup={lookup}
              maxScore={maxScore}
              accent={chartTone.accent}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function FragmentHeatmapRow({
  weekday,
  hours,
  lookup,
  maxScore,
  accent
}: {
  weekday: string;
  hours: number[];
  lookup: Map<string, number>;
  maxScore: number;
  accent: string;
}) {
  return (
    <>
      <div className="flex h-9 items-center text-xs font-medium text-muted">{weekday}</div>
      {hours.map((hour) => {
        const value = lookup.get(`${weekday}-${hour}`);
        const opacity = value ? 0.12 + (value / maxScore) * 0.68 : 0;
        return (
          <div
            key={`${weekday}-${hour}`}
            className="flex h-9 items-center justify-center rounded-md border border-border text-[11px] tabular-nums text-foreground"
            style={{
              backgroundColor: value ? hexToRgba(accent, opacity) : "transparent"
            }}
            title={value ? `${weekday} ${hour}:00 - ${formatScore(value)}` : `${weekday} ${hour}:00`}
          >
            {value ? formatScore(value) : ""}
          </div>
        );
      })}
    </>
  );
}

function InsightGroup({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold tracking-normal">{title}</h2>
      <div className="mt-4 space-y-3">
        {items.length ? (
          items.map((item, index) => (
            <div key={`${title}-${index}`} className="flex gap-3 text-sm leading-6 text-muted">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              <p>{item}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted">Not enough signal yet.</p>
        )}
      </div>
    </section>
  );
}

function RecommendationCard({ index, text }: { index: number; text: string }) {
  return (
    <div className="panel p-5">
      <p className="text-xs font-medium uppercase text-subtle">Action {index}</p>
      <p className="mt-3 text-sm leading-6 text-muted">{text}</p>
    </div>
  );
}

function ExecutiveSummary({ summary }: { summary?: string }) {
  const lines = (summary || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 14);

  return (
    <Panel title="Executive Summary" meta="Generated strategic readout">
      {lines.length ? (
        <div className="space-y-3 text-sm leading-6 text-muted">
          {lines.map((line, index) => {
            const cleanLine = normalizeSummaryLine(line);
            const isHeading = /^#{1,6}\s/.test(line);
            const isHighlight = isSummaryHighlight(cleanLine);
            return (
              <p
                key={`${line}-${index}`}
                className={
                  isHighlight
                    ? "rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 font-semibold text-foreground"
                    : isHeading
                      ? "font-semibold text-accent"
                      : "text-muted"
                }
              >
                {renderSummaryText(cleanLine)}
              </p>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-muted">Executive summary will appear after upload.</p>
      )}
    </Panel>
  );
}

function normalizeSummaryLine(line: string) {
  return line.replace(/^#{1,6}\s*/, "").replace(/^[-*]\s*/, "").trim();
}

function isSummaryHighlight(line: string) {
  return /xu hướng|rủi ro|ưu tiên|tăng trưởng|giảm|dự báo|kpi|score|views|followers|engagement|er/i.test(line);
}

function renderSummaryText(line: string) {
  const tokens = line.split(/(\*\*[^*]+\*\*|\b\d[\d.,]*(?:\s?(?:triệu|nghìn|k|m|%|views|followers|điểm|score|video|ngày))?|\~\d[\d.,]*(?:\s?(?:triệu|nghìn|k|m|%|views|followers))?)/gi);
  return tokens.map((token, index) => {
    if (!token) return null;
    if (token.startsWith("**") && token.endsWith("**")) {
      return (
        <strong key={`${token}-${index}`} className="font-semibold text-foreground">
          {token.slice(2, -2)}
        </strong>
      );
    }
    if (/^\~?\d[\d.,]*(?:\s?(?:triệu|nghìn|k|m|%|views|followers|điểm|score|video|ngày))?$/i.test(token)) {
      return (
        <strong key={`${token}-${index}`} className="font-semibold tabular-nums text-foreground">
          {token}
        </strong>
      );
    }
    return token;
  });
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: Array<Record<string, any>>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-xs shadow-panel">
      {label ? <p className="mb-1 font-medium text-foreground">{label}</p> : null}
      {payload.map((item, index) => (
        <p key={`${item.name}-${index}`} className="text-muted">
          <span className="font-medium text-foreground">{item.name || item.dataKey}:</span>{" "}
          {typeof item.value === "number" ? formatNumber(item.value) : item.value}
        </p>
      ))}
    </div>
  );
}

type ChartTone = {
  grid: string;
  axis: string;
  foreground: string;
  muted: string;
  accent: string;
};

function byScoreDesc(a: VideoPerformance, b: VideoPerformance) {
  return Number(b.performance_score || 0) - Number(a.performance_score || 0);
}

function byScoreAsc(a: VideoPerformance, b: VideoPerformance) {
  return Number(a.performance_score || 0) - Number(b.performance_score || 0);
}

function buildForecastData(actual: ForecastPoint[] = [], forecast: ForecastPoint[] = []) {
  const actualPoints = actual.map((point) => ({
    date: formatDate(point.date),
    actual: Number(point.views || 0),
    forecast: null as number | null
  }));
  const forecastPoints = forecast.map((point) => ({
    date: formatDate(point.date),
    actual: null as number | null,
    forecast: Number(point.views || 0)
  }));
  return [...actualPoints.slice(-30), ...forecastPoints.slice(0, 30)];
}

function buildOpportunities(analysis: Analysis) {
  const bestPillar = analysis.summary?.best_pillar?.content_pillar;
  const bestSlot = analysis.summary?.best_slot?.slot;
  const forecastViews = analysis.growth_forecast?.forecast_next_30_views;
  return [
    bestPillar ? `Scale the strongest pillar, ${bestPillar}, into repeatable series formats.` : "",
    bestSlot ? `Reserve the highest-intent launches for ${bestSlot}.` : "",
    forecastViews ? `Set the next 30-day view target near ${formatNumber(forecastViews)}.` : "",
    "Keep 20-30% of the calendar for controlled creative experiments."
  ].filter(Boolean);
}

function buildContentMix(pillars: PillarPerformance[]) {
  const top = pillars.slice(0, 6);
  const total = sum(top.map((item) => item.score_per_video || item.avg_score));
  return top.map((item) => {
    const score = Number(item.score_per_video || item.avg_score || 0);
    return {
      pillar: item.content_pillar || "Uncategorized",
      share: total ? Math.round((score / total) * 100) : 0
    };
  });
}

function hexToRgba(hex: string, opacity: number) {
  const normalized = hex.replace("#", "");
  const bigint = parseInt(normalized, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}
