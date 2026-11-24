"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { FormError } from "@/components/States";
import { api } from "@/lib/api";
import { rememberGroup, useRecentGroups } from "@/lib/recent";
import { useLoad } from "@/lib/useLoad";

type PersonRow = { name: string; upi: string };

const MAX_PEOPLE = 20;

export default function HomePage() {
  const router = useRouter();
  const recent = useRecentGroups();
  const stats = useLoad(api.stats);

  const [groupName, setGroupName] = useState("");
  const [people, setPeople] = useState<PersonRow[]>([
    { name: "", upi: "" },
    { name: "", upi: "" },
    { name: "", upi: "" },
  ]);
  const [busy, setBusy] = useState<"demo" | "create" | null>(null);
  const [error, setError] = useState<string | null>(null);

  function changePerson(index: number, change: Partial<PersonRow>) {
    setPeople(people.map((person, i) => (i === index ? { ...person, ...change } : person)));
  }

  function addPerson() {
    setPeople([...people, { name: "", upi: "" }]);
  }

  function removePerson(index: number) {
    setPeople(people.filter((_, i) => i !== index));
  }

  async function startDemo() {
    setBusy("demo");
    setError(null);
    try {
      const group = await api.createDemoGroup();
      rememberGroup({ id: group.id, name: group.name });
      router.push(`/g/${group.id}`);
    } catch (problem) {
      setError((problem as Error).message);
      setBusy(null);
    }
  }

  async function createGroup(event: React.FormEvent) {
    event.preventDefault();
    const named = people.filter((person) => person.name.trim() !== "");
    if (groupName.trim() === "") {
      setError("Give the group a name, like “Room 204” or “Goa trip”.");
      return;
    }
    if (named.length < 2) {
      setError("Add at least two people.");
      return;
    }

    setBusy("create");
    setError(null);
    try {
      const members = named.map((person) => ({ name: person.name, upi_id: person.upi }));
      const group = await api.createGroup(groupName, members);
      rememberGroup({ id: group.id, name: group.name });
      router.push(`/g/${group.id}`);
    } catch (problem) {
      setError((problem as Error).message);
      setBusy(null);
    }
  }

  return (
    <main className="flex flex-1 flex-col gap-10">
      <header className="pt-6">
        <p className="font-display text-lg font-bold text-brand">Hostel Splitwise</p>
        <h1 className="mt-6 font-display text-[2.6rem] font-extrabold leading-[1.05] tracking-tight">
          Split the bill. Pay back with the fewest payments.
        </h1>
        <p className="mt-4 max-w-md text-lg text-muted">
          Add what everyone spent. We work out who should pay whom, then give each payment a link that opens
          GPay or PhonePe with the amount filled in. No sign-up: share one link with your group.
        </p>
      </header>

      <section className="rounded-3xl bg-ink p-5 text-white">
        <h2 className="font-display text-xl font-bold">See it work in 10 seconds</h2>
        <p className="mt-1 text-white/75">
          A made-up Goa trip: 5 friends, 5 bills, 9 debts between them. Settle up and watch it shrink.
        </p>
        <button
          type="button"
          onClick={startDemo}
          disabled={busy !== null}
          className="btn mt-4 w-full bg-white text-ink hover:bg-brand-soft sm:w-auto"
        >
          {busy === "demo" ? "Opening the demo…" : "Open the demo trip"}
        </button>
      </section>

      <section aria-labelledby="new-group">
        <h2 id="new-group" className="font-display text-2xl font-bold">
          Start your own group
        </h2>
        <form onSubmit={createGroup} className="mt-4 flex flex-col gap-5" noValidate>
          <label className="flex flex-col gap-1.5">
            <span className="font-medium">Group name</span>
            <input
              className="field"
              value={groupName}
              onChange={(event) => setGroupName(event.target.value)}
              placeholder="Room 204"
              maxLength={60}
            />
          </label>

          <fieldset className="flex flex-col gap-3">
            <legend className="mb-1 font-medium">People</legend>
            {people.map((person, index) => (
              <div key={index} className="flex flex-col gap-2 rounded-2xl bg-surface p-3">
                <div className="flex gap-2">
                  <input
                    className="field"
                    aria-label={`Person ${index + 1} name`}
                    value={person.name}
                    onChange={(event) => changePerson(index, { name: event.target.value })}
                    placeholder={`Person ${index + 1}`}
                    maxLength={40}
                  />
                  {people.length > 2 && (
                    <button
                      type="button"
                      className="btn btn-quiet shrink-0 px-4"
                      onClick={() => removePerson(index)}
                      aria-label={`Remove person ${index + 1}`}
                    >
                      Remove
                    </button>
                  )}
                </div>
                <input
                  className="field"
                  aria-label={`Person ${index + 1} UPI ID (optional)`}
                  value={person.upi}
                  onChange={(event) => changePerson(index, { upi: event.target.value })}
                  placeholder="UPI ID, if they want to be paid (optional)"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                />
              </div>
            ))}
            {people.length < MAX_PEOPLE && (
              <button type="button" className="btn btn-quiet self-start" onClick={addPerson}>
                Add another person
              </button>
            )}
          </fieldset>

          <FormError message={error} />

          <button type="submit" className="btn btn-primary w-full" disabled={busy !== null}>
            {busy === "create" ? "Creating…" : "Create group"}
          </button>
        </form>
      </section>

      {recent.length > 0 && (
        <section aria-labelledby="recent">
          <h2 id="recent" className="font-display text-2xl font-bold">
            Groups opened on this phone
          </h2>
          <ul className="mt-3 divide-y divide-line rounded-2xl bg-surface">
            {recent.map((group) => (
              <li key={group.id}>
                <Link href={`/g/${group.id}`} className="flex min-h-14 items-center px-4 font-medium">
                  {group.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer className="mt-auto border-t border-line pt-5 text-sm text-muted">
        <p>
          {stats.data !== null &&
            `${stats.data.groups} groups and ${stats.data.expenses} expenses split so far. `}
          Anyone with a group’s link can see and edit it, so share it only with your group. This app only builds
          payment links. It never touches your money.
        </p>
      </footer>
    </main>
  );
}
