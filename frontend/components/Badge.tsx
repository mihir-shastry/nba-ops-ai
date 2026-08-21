import { resultColor, resultBg } from "@/lib/utils";

interface BadgeProps {
  value: string;
  type?: "result" | "rating";
}

export default function Badge({ value, type = "result" }: BadgeProps) {
  if (type === "result") {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${resultBg(value)} ${resultColor(value)}`}
      >
        {value}
      </span>
    );
  }

  const num = parseFloat(value);
  let colorClass = "text-court-muted";
  if (num >= 90) colorClass = "text-white font-bold";
  else if (num >= 80) colorClass = "text-white";
  else if (num >= 70) colorClass = "text-neutral-400";

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-white/[0.04] border border-court-border ${colorClass}`}
    >
      {value}
    </span>
  );
}
