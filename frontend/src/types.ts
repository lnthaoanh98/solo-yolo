export type Summary = {
  total_videos?: number;
  date_range?: string;
  total_views?: number;
  total_engagements?: number;
  avg_engagement_rate?: number;
  avg_performance_score?: number;
  best_video?: {
    title?: string;
    score?: number;
    views?: number;
    pillar?: string;
  };
  best_pillar?: PillarPerformance | null;
  best_slot?: TimeSlot | null;
  growth_outlook?: string;
  next_calendar_month?: string;
  recommended_posts?: number;
};

export type VideoPerformance = {
  rank?: number;
  video_id?: string;
  title?: string;
  platform?: string;
  content_pillar?: string;
  posted_at?: string;
  views?: number;
  likes?: number;
  comments?: number;
  shares?: number;
  saves?: number;
  followers_gained?: number;
  engagements?: number;
  engagement_rate?: number;
  completion_rate?: number;
  duration_bucket?: string;
  performance_score?: number;
  performance_tier?: string;
};

export type PillarPerformance = {
  content_pillar?: string;
  videos?: number;
  total_views?: number;
  median_views?: number;
  total_engagements?: number;
  avg_engagement_rate?: number;
  total_followers_gained?: number;
  avg_completion_rate?: number;
  avg_score?: number;
  median_score?: number;
  top_video?: string;
  score_per_video?: number;
};

export type TimeSlot = {
  posted_weekday?: string;
  posted_weekday_label?: string;
  posted_hour?: number;
  videos?: number;
  avg_score?: number;
  median_views?: number;
  avg_engagement_rate?: number;
  slot?: string;
};

export type HeatmapCell = {
  weekday?: string;
  hour?: number;
  score?: number;
};

export type OptimalTime = {
  available?: boolean;
  top_slots?: TimeSlot[];
  heatmap?: HeatmapCell[];
  sample_size_note?: string;
  note?: string;
};

export type Patterns = {
  success_patterns?: string[];
  failure_patterns?: string[];
  diagnostics?: Record<string, unknown>;
};

export type ForecastPoint = {
  date?: string;
  views?: number;
  followers_gained?: number;
  engagements?: number;
};

export type GrowthForecast = {
  available?: boolean;
  outlook?: string;
  actual?: ForecastPoint[];
  forecast?: ForecastPoint[];
  growth_rate_pct?: number;
  forecast_next_30_views?: number;
  actual_last_30_views?: number;
};

export type CalendarItem = {
  date?: string;
  time?: string;
  weekday?: string;
  platform?: string;
  pillar?: string;
  format?: string;
  hook?: string;
  goal?: string;
  primary_kpi?: string;
};

export type ContentCalendar = {
  month?: string;
  recommended_posts?: number;
  strategy?: string[];
  items?: CalendarItem[];
};

export type Analysis = {
  summary?: Summary;
  per_video?: VideoPerformance[];
  pillar_performance?: PillarPerformance[];
  optimal_time?: OptimalTime;
  patterns?: Patterns;
  growth_forecast?: GrowthForecast;
  content_calendar?: ContentCalendar;
  executive_summary?: string;
};

export type UploadResponse = {
  dataset_id: string;
  filename?: string;
  rows: number;
  llm_configured: boolean;
  analysis: Analysis;
};
