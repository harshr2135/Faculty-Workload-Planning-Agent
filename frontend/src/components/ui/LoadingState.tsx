export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="ui-card flex items-center justify-center px-4 py-16 text-slate-500">
      <div className="flex items-center gap-3">
        <span
          className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-emerald-600"
          aria-hidden
        />
        <span className="text-sm font-medium tracking-tight">{message}</span>
      </div>
    </div>
  );
}
