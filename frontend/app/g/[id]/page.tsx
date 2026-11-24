"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AddExpenseForm } from "@/components/AddExpenseForm";
import { ShareButtons } from "@/components/ShareButtons";
import { EmptyState, ErrorState, FormError, LoadingState } from "@/components/States";
import { UpiIdEditor } from "@/components/UpiIdEditor";
import { api, type Expense, type Group } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import { rememberGroup } from "@/lib/recent";
import { useLoad } from "@/lib/useLoad";

export default function GroupPage() {
  const { id } = useParams<{ id: string }>();
  const { data: group, error, slow, reload, retry } = useLoad(() => api.getGroup(id));

  const groupId = group?.id;
  const groupName = group?.name;
  useEffect(() => {
    if (groupId !== undefined && groupName !== undefined) {
      rememberGroup({ id: groupId, name: groupName });
    }
  }, [groupId, groupName]);

  if (error !== null) {
    return <ErrorState message={error} onRetry={retry} />;
  }
  if (group === null) {
    return <LoadingState slow={slow} what="your group" />;
  }
  return <GroupView group={group} reload={reload} />;
}

function GroupView({ group, reload }: { group: Group; reload: () => void }) {
  const [adding, setAdding] = useState(false);
  const hasExpenses = group.expenses.length > 0;

  function expenseAdded() {
    setAdding(false);
    reload();
  }

  return (
    <main className="flex flex-1 flex-col gap-9">
      <header>
        <Link href="/" className="inline-flex min-h-11 items-center font-medium text-brand">
          Hostel Splitwise
        </Link>
        <h1 className="mt-2 font-display text-4xl font-extrabold leading-tight tracking-tight">{group.name}</h1>
        {group.is_demo && (
          <p className="mt-2 rounded-xl bg-brand-soft px-3 py-2 text-sm">
            This is a demo group with made-up people and UPI IDs. Nobody can be paid from it.
          </p>
        )}
        <div className="mt-4">
          <ShareButtons groupName={group.name} />
        </div>
      </header>

      <section aria-labelledby="balances">
        <h2 id="balances" className="font-display text-2xl font-bold">
          Balances
        </h2>
        {hasExpenses ? (
          <ul className="mt-3 divide-y divide-line rounded-2xl bg-surface">
            {group.balances.map((balance) => (
              <li key={balance.member_id} className="flex min-h-16 items-center justify-between gap-3 px-4">
                <span className="min-w-0 truncate font-medium">{balance.name}</span>
                <BalanceAmount balance={balance.balance} />
              </li>
            ))}
          </ul>
        ) : (
          <div className="mt-3">
            <EmptyState title="Nobody owes anything yet">
              Add the first bill and everyone’s balance shows up here.
            </EmptyState>
          </div>
        )}
      </section>

      <section aria-labelledby="expenses">
        <div className="flex items-center justify-between gap-3">
          <h2 id="expenses" className="font-display text-2xl font-bold">
            Expenses
          </h2>
          {!adding && (
            <button type="button" className="btn btn-primary" onClick={() => setAdding(true)}>
              Add expense
            </button>
          )}
        </div>

        {adding && (
          <div className="mt-3">
            <AddExpenseForm group={group} onAdded={expenseAdded} onCancel={() => setAdding(false)} />
          </div>
        )}

        <div className="mt-3">
          {hasExpenses ? (
            <ul className="divide-y divide-line rounded-2xl bg-surface">
              {group.expenses.map((expense) => (
                <ExpenseRow key={expense.id} group={group} expense={expense} onDeleted={reload} />
              ))}
            </ul>
          ) : (
            !adding && (
              <EmptyState title="No expenses yet">
                Add a bill someone paid for: rent, food, a cab. Pick who shares it.
              </EmptyState>
            )
          )}
        </div>
      </section>

      <PeopleSection group={group} reload={reload} />

      {hasExpenses && (
        <div className="sticky bottom-4 z-10">
          <Link
            href={`/g/${group.id}/settle`}
            className="btn btn-primary w-full shadow-lg shadow-brand/30"
          >
            Settle up
          </Link>
        </div>
      )}
    </main>
  );
}

function BalanceAmount({ balance }: { balance: number }) {
  if (balance === 0) {
    return <span className="text-muted">All even</span>;
  }
  const isOwed = balance > 0;
  return (
    <span className="text-right">
      <span className={`block font-display text-xl font-bold ${isOwed ? "text-owed" : "text-owes"}`}>
        {formatPaise(Math.abs(balance))}
      </span>
      <span className="block text-sm text-muted">{isOwed ? "gets back" : "owes"}</span>
    </span>
  );
}

// The API sends UTC times; SQLite leaves off the time zone, so add it when it is missing.
function shortDate(isoText: string): string {
  const hasZone = /Z$|[+-]\d\d:\d\d$/.test(isoText);
  const date = new Date(hasZone ? isoText : isoText + "Z");
  return date.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function ExpenseRow({ group, expense, onDeleted }: { group: Group; expense: Expense; onDeleted: () => void }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const payer = group.members.find((member) => member.id === expense.paid_by);
  const splitText =
    expense.split_type === "equal" ? `split between ${expense.shares.length}` : "split by amounts";

  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await api.deleteExpense(group.id, expense.id);
      onDeleted();
    } catch (problem) {
      setError((problem as Error).message);
      setBusy(false);
    }
  }

  return (
    <li className="flex flex-col gap-2 px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{expense.description}</p>
          <p className="text-sm text-muted">
            {payer?.name ?? "Someone"} paid, {splitText}, {shortDate(expense.created_at)}
          </p>
        </div>
        <p className="shrink-0 font-display text-xl font-bold">{formatPaise(expense.amount)}</p>
      </div>

      {confirming ? (
        <div className="flex flex-col gap-2">
          <FormError message={error} />
          <div className="flex items-center gap-2">
            <button type="button" className="btn btn-quiet !min-h-10 text-sm text-owes" onClick={remove} disabled={busy}>
              {busy ? "Deleting…" : "Delete this expense"}
            </button>
            <button type="button" className="btn btn-quiet !min-h-10 text-sm" onClick={() => setConfirming(false)}>
              Keep it
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          className="self-start text-sm font-medium text-muted underline underline-offset-2"
          onClick={() => setConfirming(true)}
        >
          Delete
        </button>
      )}
    </li>
  );
}

function PeopleSection({ group, reload }: { group: Group; reload: () => void }) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [upi, setUpi] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function addPerson(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.addMember(group.id, { name, upi_id: upi });
      setName("");
      setUpi("");
      setAdding(false);
      reload();
    } catch (problem) {
      setError((problem as Error).message);
    }
    setBusy(false);
  }

  return (
    <section aria-labelledby="people">
      <h2 id="people" className="font-display text-2xl font-bold">
        People
      </h2>
      <p className="mt-1 text-muted">A UPI ID is needed to build payment links for the person being paid.</p>

      <ul className="mt-3 divide-y divide-line rounded-2xl bg-surface">
        {group.members.map((member) => (
          <li key={member.id} className="flex flex-col gap-2 px-4 py-3">
            <p className="font-medium">{member.name}</p>
            <UpiIdEditor groupId={group.id} member={member} onSaved={reload} />
          </li>
        ))}
      </ul>

      {adding ? (
        <form onSubmit={addPerson} className="mt-3 flex flex-col gap-2 rounded-2xl bg-surface p-3" noValidate>
          <input
            className="field"
            aria-label="New person’s name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Name"
            maxLength={40}
            autoFocus
          />
          <input
            className="field"
            aria-label="New person’s UPI ID (optional)"
            value={upi}
            onChange={(event) => setUpi(event.target.value)}
            placeholder="UPI ID (optional)"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
          />
          <FormError message={error} />
          <div className="flex gap-2">
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Adding…" : "Add person"}
            </button>
            <button type="button" className="btn btn-quiet" onClick={() => setAdding(false)}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button type="button" className="btn btn-quiet mt-3" onClick={() => setAdding(true)}>
          Add a person
        </button>
      )}
    </section>
  );
}
