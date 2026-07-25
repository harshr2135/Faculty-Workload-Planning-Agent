import type { ReactNode } from "react";
import { cn } from "@/utils/formatters";

const variants = {
  default: "bg-slate-100 text-slate-700 ring-slate-200/80",
  success: "bg-emerald-50 text-emerald-800 ring-emerald-200/80",
  warning: "bg-amber-50 text-amber-900 ring-amber-200/80",
  info: "bg-sky-50 text-sky-800 ring-sky-200/80",
} as const;

interface BadgeProps {
  children: ReactNode;
  variant?: keyof typeof variants;
}

export function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1",
        variants[variant],
      )}
    >
      {children}
    </span>
  );
}
