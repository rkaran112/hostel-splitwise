"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { DebtDiagram } from "@/components/DebtDiagram";
import { PaymentTicket } from "@/components/PaymentTicket";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { Stepper } from "@/components/Stepper";
import { api, type Settlement } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";

export default function SettlePage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, slow, reload, retry } = useLoad(() => api.settle(id));

  if (error !== null) {
    return <ErrorState message={error} onRetry={retry} />;
  }
  if (data === null) {
    return <LoadingState slow={slow} what="the settle-up plan" />;
  }
  return <SettleView groupId={id} settlement={data} reload={reload} />;
}

function SettleView({
  groupId,
  settlement,
  reload,
}: {
  groupId: string;
  settlement: Settlement;
  reload: () => void;
}) {
  const nothingToPay = settlement.payments.length === 0;
  const savedPayments = settlement.before_debts - settlement.after_payments;

  return (
    <main className="flex flex-1 flex-col gap-8">
      <header>
        <Link href={`/g/${groupId}`} className="inline-flex min-h-11 items-center font-medium text-brand">
          Back to the group
        </Link>
        <h1 className="mt-2 font-display text-4xl font-extrabold leading-tight tracking-tight">Settle up</h1>

        {!nothingToPay && (
          <div className="mt-5 flex items-end gap-4">
            <Count value={settlement.before_debts} label="debts" muted />
            <span className="pb-2 font-display text-3xl font-bold text-muted" aria-label="becomes">
              to
            </span>
            <Count value={settlement.after_payments} label="payments" />
          </div>
        )}
        {!nothingToPay && (
          <p className="mt-3 max-w-md text-muted">
            {savedPayments > 0
              ? `Instead of paying every debt one by one, ${settlement.after_payments} payments settle the whole group.`
              : `${settlement.after_payments} payments settle the whole group.`}
          </p>
        )}
      </header>

      {nothingToPay ? (
        <EmptyState title="Everyone is even">
          Nobody owes anything right now. Add an expense and the plan appears here.
        </EmptyState>
      ) : (
        <>
          <DebtDiagram
            before={settlement.debts.map((debt) => ({ from: debt.from_name, to: debt.to_name, amount: debt.amount }))}
            after={settlement.payments.map((payment) => ({
              from: payment.from_name,
              to: payment.to_name,
              amount: payment.amount,
            }))}
          />

          <section aria-labelledby="who-pays">
            <h2 id="who-pays" className="font-display text-2xl font-bold">
              Who pays whom
            </h2>
            <ul className="mt-3 flex flex-col gap-4">
              {settlement.payments.map((payment) => (
                <PaymentTicket
                  key={`${payment.from_id}-${payment.to_id}`}
                  payment={payment}
                  groupId={groupId}
                  onChanged={reload}
                />
              ))}
            </ul>
            <p className="mt-4 text-sm text-muted">
              A pay button opens your UPI app with the amount filled in, and you confirm the payment there. This app
              never touches money.
            </p>
          </section>

          <Stepper steps={settlement.steps} />
        </>
      )}
    </main>
  );
}

function Count({ value, label, muted = false }: { value: number; label: string; muted?: boolean }) {
  return (
    <p>
      <span
        className={`block font-display text-7xl font-extrabold leading-none ${muted ? "text-muted" : "text-brand"}`}
      >
        {value}
      </span>
      <span className="mt-1 block font-medium">{label}</span>
    </p>
  );
}
