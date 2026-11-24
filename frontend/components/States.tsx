// The three states every page needs besides "it worked":
//   loading  -> LoadingState   (with a longer message if the free server is waking up)
//   failed   -> ErrorState     (says what went wrong, offers Try again)
//   empty    -> EmptyState     (tells the person what to do next)

export function LoadingState({ slow, what }: { slow: boolean; what: string }) {
  return (
    <div role="status" className="flex flex-col items-center gap-3 py-16 text-center">
      <div
        aria-hidden="true"
        className="h-8 w-8 animate-spin rounded-full border-4 border-line border-t-brand motion-reduce:animate-none"
      />
      <p className="font-medium">Loading {what}…</p>
      {slow && (
        <p className="max-w-xs text-sm text-muted">
          The free server is waking up after a quiet spell. This can take up to a minute the first time.
        </p>
      )}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-4 py-16 text-center">
      <p className="font-display text-xl font-semibold">That didn’t load</p>
      <p className="max-w-xs text-muted">{message}</p>
      <button type="button" className="btn btn-primary" onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border-2 border-dashed border-line px-5 py-8 text-center">
      <p className="font-display text-lg font-semibold">{title}</p>
      <p className="mx-auto mt-1 max-w-xs text-muted">{children}</p>
    </div>
  );
}

export function FormError({ message }: { message: string | null }) {
  if (message === null) {
    return null;
  }
  return (
    <p role="alert" className="rounded-xl bg-red-50 px-3 py-2 text-sm font-medium text-owes">
      {message}
    </p>
  );
}
