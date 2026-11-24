"use client";

import { useState } from "react";

import { FormError } from "@/components/States";
import { api, type Group } from "@/lib/api";
import { formatPaise, parseRupees } from "@/lib/money";

// The "add a bill" form. Two ways to split:
//   Equally    -> tick who shares it; the server splits it (and hands out leftover paise)
//   By amounts -> type each person's share; they must add up to the bill
export function AddExpenseForm({
  group,
  onAdded,
  onCancel,
}: {
  group: Group;
  onAdded: () => void;
  onCancel: () => void;
}) {
  const everyone = group.members.map((member) => member.id);

  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [paidBy, setPaidBy] = useState(everyone[0]);
  const [splitType, setSplitType] = useState<"equal" | "exact">("equal");
  const [participants, setParticipants] = useState<number[]>(everyone);
  const [shares, setShares] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = parseRupees(amount);

  function toggleParticipant(memberId: number) {
    if (participants.includes(memberId)) {
      setParticipants(participants.filter((id) => id !== memberId));
    } else {
      setParticipants([...participants, memberId]);
    }
  }

  // How much of the bill is still not given to anyone (exact split only).
  function amountLeft(): number | null {
    if (total === null) {
      return null;
    }
    let assigned = 0;
    for (const memberId of everyone) {
      assigned += parseRupees(shares[memberId] ?? "") ?? 0;
    }
    return total - assigned;
  }

  function equalHint(): string | null {
    if (total === null || total === 0 || participants.length === 0) {
      return null;
    }
    const each = Math.floor(total / participants.length);
    const hasLeftover = total % participants.length !== 0;
    return `${formatPaise(each)} each${hasLeftover ? ", with a few paise shared out so it adds up exactly" : ""}`;
  }

  function checkBeforeSending(): string | null {
    if (description.trim() === "") {
      return "Say what the bill was for, like “Dinner”.";
    }
    if (total === null || total === 0) {
      return "Enter the amount, like 450 or 450.50.";
    }
    if (splitType === "equal" && participants.length === 0) {
      return "Pick at least one person to share the bill.";
    }
    if (splitType === "exact" && amountLeft() !== 0) {
      return "The shares must add up to the full amount.";
    }
    return null;
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const problem = checkBeforeSending();
    if (problem !== null) {
      setError(problem);
      return;
    }

    setBusy(true);
    setError(null);
    try {
      await api.addExpense(group.id, {
        description,
        paid_by: paidBy,
        amount,
        split_type: splitType,
        // Send the people in group order so leftover paise always go to the same people first.
        participants: everyone.filter((id) => participants.includes(id)),
        shares,
      });
      onAdded();
    } catch (failure) {
      setError((failure as Error).message);
      setBusy(false);
    }
  }

  const left = amountLeft();

  return (
    <form onSubmit={submit} className="flex flex-col gap-4 rounded-2xl bg-surface p-4" noValidate>
      <label className="flex flex-col gap-1.5">
        <span className="font-medium">What was it for?</span>
        <input
          className="field"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Dinner"
          maxLength={80}
        />
      </label>

      <div className="grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-1.5">
          <span className="font-medium">Amount (₹)</span>
          <input
            className="field"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            placeholder="450"
            inputMode="decimal"
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="font-medium">Paid by</span>
          <select className="field" value={paidBy} onChange={(event) => setPaidBy(Number(event.target.value))}>
            {group.members.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div role="group" aria-label="How to split" className="grid grid-cols-2 gap-1 rounded-full bg-paper p-1">
        {(["equal", "exact"] as const).map((kind) => (
          <button
            key={kind}
            type="button"
            aria-pressed={splitType === kind}
            onClick={() => setSplitType(kind)}
            className={`min-h-11 rounded-full font-semibold ${
              splitType === kind ? "bg-surface shadow-sm" : "text-muted"
            }`}
          >
            {kind === "equal" ? "Split equally" : "Split by amounts"}
          </button>
        ))}
      </div>

      {splitType === "equal" ? (
        <fieldset className="flex flex-col">
          <legend className="mb-1 font-medium">Who shares it?</legend>
          {group.members.map((member) => (
            <label key={member.id} className="flex min-h-12 items-center gap-3 border-b border-line last:border-0">
              <input
                type="checkbox"
                className="h-5 w-5 accent-brand"
                checked={participants.includes(member.id)}
                onChange={() => toggleParticipant(member.id)}
              />
              {member.name}
            </label>
          ))}
          {equalHint() !== null && <p className="mt-2 text-sm text-muted">{equalHint()}</p>}
        </fieldset>
      ) : (
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 font-medium">Each person’s share (₹)</legend>
          {group.members.map((member) => (
            <label key={member.id} className="flex items-center justify-between gap-3">
              <span className="min-w-0 truncate">{member.name}</span>
              <input
                className="field !w-32 text-right"
                aria-label={`${member.name}’s share`}
                value={shares[member.id] ?? ""}
                onChange={(event) => setShares({ ...shares, [member.id]: event.target.value })}
                placeholder="0"
                inputMode="decimal"
              />
            </label>
          ))}
          <p
            className={`text-sm font-medium ${left === 0 ? "text-owed" : "text-muted"}`}
            aria-live="polite"
          >
            {left === null && "Enter the amount first."}
            {left !== null && left === 0 && "All assigned."}
            {left !== null && left > 0 && `${formatPaise(left)} left to assign`}
            {left !== null && left < 0 && `${formatPaise(-left)} over the amount`}
          </p>
        </fieldset>
      )}

      <FormError message={error} />

      <div className="flex gap-2">
        <button type="submit" className="btn btn-primary flex-1" disabled={busy}>
          {busy ? "Adding…" : "Add expense"}
        </button>
        <button type="button" className="btn btn-quiet" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
