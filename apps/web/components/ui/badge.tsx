import { cn } from "@/lib/utils";

export function Badge({
  className,
  tone = "default",
  children,
}: {
  className?: string;
  tone?: "default" | "success" | "warning" | "danger" | "muted";
  children: React.ReactNode;
}) {
  const palette = {
    default: "bg-slate-100 text-slate-700",
    success: "bg-emerald-50 text-emerald-700",
    warning: "bg-amber-50 text-amber-700",
    danger: "bg-rose-50 text-rose-700",
    muted: "bg-slate-50 text-slate-500",
  }[tone];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
        palette,
        className,
      )}
    >
      {children}
    </span>
  );
}
