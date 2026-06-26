import type { ReactNode } from "react";
import { cn } from "@/utils/formatters";

const variants = {
  default: "bg-slate-100 text-slate-700",
  success: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-800",
  info: "bg-sky-100 text-sky-800",
} as const;

interface BadgeProps {
  children: ReactNode;
  variant?: keyof typeof variants;
}

export function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
      )}
    >
      {children}
    </span>
  );
}
