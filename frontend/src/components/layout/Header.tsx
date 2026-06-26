export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-900">Department Administrator</p>
          <p className="text-xs text-slate-500">Faculty workload planning &amp; allocation</p>
        </div>
        <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          AIML
        </div>
      </div>
    </header>
  );
}
