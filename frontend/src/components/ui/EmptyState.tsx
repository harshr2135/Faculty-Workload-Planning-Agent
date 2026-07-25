import type { ReactNode } from "react";
import { IconInbox } from "@/components/ui/icons";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="ui-card flex flex-col items-center px-6 py-14 text-center">
      <span className="rounded-2xl bg-slate-100 p-3 text-slate-500 ring-1 ring-slate-200/80">
        <IconInbox className="h-6 w-6" />
      </span>
      <h2 className="mt-4 text-base font-semibold tracking-tight text-slate-900">{title}</h2>
      {description && (
        <p className="mt-1.5 max-w-md text-sm leading-relaxed text-slate-500">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
