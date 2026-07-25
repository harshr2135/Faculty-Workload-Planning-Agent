const LOADER_SRC = "/loaders/timetable-loader.mp4";

export function TimetableGenerationLoader({
  message = "Assigning workload and building timetable…",
}: {
  message?: string;
}) {
  return (
    <div
      className="ui-card flex flex-col items-center justify-center gap-5 px-6 py-14 text-center"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <video
        src={LOADER_SRC}
        autoPlay
        muted
        loop
        playsInline
        aria-hidden="true"
        className="h-40 w-40 object-contain sm:h-44 sm:w-44"
      />
      <div className="max-w-md space-y-1.5">
        <p className="text-sm font-semibold tracking-tight text-slate-900">{message}</p>
        <p className="text-xs text-slate-500">This can take a minute for larger departments.</p>
      </div>
      <span className="sr-only">Loading</span>
    </div>
  );
}
