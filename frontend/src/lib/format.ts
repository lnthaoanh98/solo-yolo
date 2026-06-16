export function formatNumber(value?: number | null, compact = true) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("en-US", {
    notation: compact && Math.abs(value) >= 10000 ? "compact" : "standard",
    maximumFractionDigits: compact ? 1 : 0
  }).format(value);
}

export function formatPercent(value?: number | null, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  return `${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: value > 0 && value < 1 ? 2 : 0
  }).format(value)}%`;
}

export function formatScore(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
}

export function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
}

export function formatMonth(value?: string | null) {
  if (!value) return "-";
  const [year, month] = value.split("-");
  if (!year || !month) return value;
  return new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" }).format(
    new Date(Number(year), Number(month) - 1, 1)
  );
}

export function sum(values: Array<number | undefined | null>) {
  return values.reduce<number>((total, value) => total + (Number(value) || 0), 0);
}
