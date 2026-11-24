"use client";

import { useState } from "react";

import { FormError } from "@/components/States";
import { api, type Member } from "@/lib/api";

// Shows a person's UPI ID and lets you add or change it.
// Used on the group page (People) and on the settle page when a receiver has no UPI ID yet.
export function UpiIdEditor({
  groupId,
  member,
  onSaved,
  compact = false,
}: {
  groupId: string;
  member: Pick<Member, "id" | "name" | "upi_id">;
  onSaved: () => void;
  compact?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(member.upi_id ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.setUpiId(groupId, member.id, text);
      setEditing(false);
      onSaved();
    } catch (problem) {
      setError((problem as Error).message);
    }
    setBusy(false);
  }

  if (!editing) {
    return (
      <div className="flex items-center justify-between gap-3">
        {!compact && (
          <span className="min-w-0 truncate text-sm text-muted">{member.upi_id ?? "No UPI ID yet"}</span>
        )}
        <button type="button" className="btn btn-quiet shrink-0 !min-h-10 text-sm" onClick={() => setEditing(true)}>
          {member.upi_id ? "Change UPI ID" : `Add ${member.name}’s UPI ID`}
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={save} className="flex flex-col gap-2">
      <input
        className="field"
        aria-label={`${member.name}’s UPI ID`}
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="name@bank"
        autoCapitalize="none"
        autoCorrect="off"
        spellCheck={false}
        autoFocus
      />
      <FormError message={error} />
      <div className="flex gap-2">
        <button type="submit" className="btn btn-primary !min-h-10 text-sm" disabled={busy}>
          {busy ? "Saving…" : "Save"}
        </button>
        <button type="button" className="btn btn-quiet !min-h-10 text-sm" onClick={() => setEditing(false)}>
          Cancel
        </button>
      </div>
    </form>
  );
}
