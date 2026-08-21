import { resultColor, resultBg } from "@/lib/utils";

interface BadgeProps {
  value: string;
  type?: "result" | "rating";
}

export default function Badge({ value, type = "result" }: BadgeProps) {
  if (type === "result") {
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${resultBg(value)} ${resultColor(value)}`}
      >
        {value}
      </span>
    );
  }

  const num = parseFloat(value);
  let colorClass = "text-court-muted";
  if (num >= 90) colorClass = "text-court-gold font-bold";
  else if (num >= 80) colorClass = "text-court-green font-bold";
  else if (num >= 70) colorClass = "text-white";

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-white/5 border border-white/10 ${colorClass}`}
    >
      {value}
    </span>
  );
}
