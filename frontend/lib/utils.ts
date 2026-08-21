export function formatPct(val: number | null): string {
  if (val == null) return "—";
  return val < 1 ? `${(val * 100).toFixed(1)}%` : `${val.toFixed(1)}%`;
}

export function formatRating(val: number): string {
  return val.toFixed(1);
}

export function ratingColor(val: number): string {
  if (val >= 90) return "text-court-gold font-bold";
  if (val >= 80) return "text-court-green font-bold";
  if (val >= 70) return "text-white";
  return "text-court-muted";
}

export function resultColor(result: string): string {
  return result === "W" ? "text-court-green" : "text-court-red";
}

export function resultBg(result: string): string {
  return result === "W"
    ? "bg-court-green/10 border-court-green/30"
    : "bg-court-red/10 border-court-red/30";
}
