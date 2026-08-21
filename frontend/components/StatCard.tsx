interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
}

export default function StatCard({ label, value, subtext }: StatCardProps) {
  return (
    <div className="bg-court-card border border-court-border rounded-xl p-4">
      <p className="text-court-muted text-xs font-medium uppercase tracking-wide">
        {label}
      </p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {subtext && (
        <p className="text-court-muted text-xs mt-1">{subtext}</p>
      )}
    </div>
  );
}
