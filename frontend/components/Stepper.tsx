"use client";

import { useState } from "react";

import type { PersonLeft, Step } from "@/lib/api";
import { formatPaise } from "@/lib/money";

function peopleText(people: PersonLeft[]): string {
  return people.map((person) => `${person.name} ${formatPaise(person.amount)}`).join(", ");
}

// "Show me how": walks through the algorithm one payment at a time.
export function Stepper({ steps }: { steps: Step[] }) {
  const [index, setIndex] = useState(0);
  if (steps.length === 0) {
    return null;
  }

  const step = steps[index];
  const nobodyLeft = step.debtors_left.length === 0 && step.creditors_left.length === 0;

  return (
    <details className="rounded-2xl bg-surface p-4">
      <summary className="min-h-11 cursor-pointer font-display text-lg font-bold">
        Show me how this was worked out
      </summary>

      <p className="mt-3 text-muted">
        First we add up what each person paid and what they should have paid. Then, again and again, the person
        who owes the most pays the person who is owed the most.
      </p>

      <div className="mt-4 rounded-xl bg-paper p-4" aria-live="polite">
        <p className="font-semibold">
          Step {index + 1} of {steps.length}
        </p>
        <p className="mt-2">
          {step.from_name} owes the most and {step.to_name} is owed the most. So {step.from_name} pays{" "}
          {step.to_name} <strong>{formatPaise(step.amount)}</strong>, the smaller of the two amounts. At least one
          of them is now fully settled.
        </p>
        <div className="mt-3 text-sm text-muted">
          {nobodyLeft ? (
            <p className="font-medium text-owed">Nobody is left. Everyone is settled.</p>
          ) : (
            <>
              <p>Still owe: {step.debtors_left.length > 0 ? peopleText(step.debtors_left) : "nobody"}</p>
              <p>Still to get back: {step.creditors_left.length > 0 ? peopleText(step.creditors_left) : "nobody"}</p>
            </>
          )}
        </div>
      </div>

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          className="btn btn-quiet flex-1"
          disabled={index === 0}
          onClick={() => setIndex(index - 1)}
        >
          Back
        </button>
        <button
          type="button"
          className="btn btn-primary flex-1"
          disabled={index === steps.length - 1}
          onClick={() => setIndex(index + 1)}
        >
          Next step
        </button>
      </div>
    </details>
  );
}
