interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50/90 px-5 py-8 text-center shadow-soft">
      <p className="text-sm font-medium text-red-800">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="ui-btn-primary mt-4 bg-red-600 hover:bg-red-700">
          Retry
        </button>
      )}
    </div>
  );
}
