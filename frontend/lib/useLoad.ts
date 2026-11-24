"use client";

import { useEffect, useRef, useState } from "react";

// Loads data when the page opens and tells the page what state it is in:
//   data === null && error === null  -> still loading
//   error !== null                   -> it failed (show the message and a Try again button)
//   data !== null                    -> done
// `slow` becomes true after 4 seconds. The free server sleeps when nobody uses it,
// so the first request can take about 30-50 seconds; the page uses `slow` to explain.
export function useLoad<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [slow, setSlow] = useState(false);
  const [attempt, setAttempt] = useState(0);

  // Keep the newest `load` function in a ref so the effect below only re-runs on `attempt`.
  const loadRef = useRef(load);
  useEffect(() => {
    loadRef.current = load;
  });

  useEffect(() => {
    let cancelled = false;
    const slowTimer = setTimeout(() => setSlow(true), 4000);

    loadRef
      .current()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch((problem: Error) => {
        if (!cancelled) {
          setError(problem.message);
        }
      })
      .finally(() => {
        clearTimeout(slowTimer);
        if (!cancelled) {
          setSlow(false);
        }
      });

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
  }, [attempt]);

  // Call this after a change (new expense, deleted expense...) to fetch fresh data.
  // The old data stays on screen while the new data loads.
  function reload() {
    setAttempt((count) => count + 1);
  }

  // Call this after a failure: clears the error so the loading state shows again.
  function retry() {
    setError(null);
    setAttempt((count) => count + 1);
  }

  return { data, error, slow, reload, retry };
}
