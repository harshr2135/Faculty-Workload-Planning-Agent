import type { ReactNode } from "react";

interface DataTableProps {
  children: ReactNode;
}

export function DataTable({ children }: DataTableProps) {
  return (
    <div className="ui-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">{children}</table>
      </div>
    </div>
  );
}

export function DataTableHead({ children }: { children: ReactNode }) {
  return (
    <thead className="bg-slate-50/90">
      <tr>{children}</tr>
    </thead>
  );
}

export function DataTableHeaderCell({ children }: { children: ReactNode }) {
  return (
    <th className="px-4 py-3.5 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
      {children}
    </th>
  );
}

export function DataTableBody({ children }: { children: ReactNode }) {
  return <tbody className="divide-y divide-slate-100 bg-white">{children}</tbody>;
}

export function DataTableCell({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <td className={`px-4 py-3.5 align-top text-slate-700 ${className ?? ""}`}>{children}</td>
  );
}

export function EmptyRow({ colSpan, message }: { colSpan: number; message: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-4 py-12 text-center text-sm text-slate-500">
        {message}
      </td>
    </tr>
  );
}
