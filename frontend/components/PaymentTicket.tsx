"use client";

import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";

import { UpiIdEditor } from "@/components/UpiIdEditor";
import type { Payment } from "@/lib/api";
import { formatPaise } from "@/lib/money";

// One payment, drawn as a ticket. The top says who pays whom. Below the dashed tear:
// a button that opens the UPI app (phones), a QR code (to scan from a computer screen),
// and a copy button. This app only builds the link. The payment happens in the UPI app.
export function PaymentTicket({
  payment,
  groupId,
  onChanged,
}: {
  payment: Payment;
  groupId: string;
  onChanged: () => void;
}) {
  const [showQr, setShowQr] = useState(false);
  const [copied, setCopied] = useState(false);

  async function copyUpiId() {
    try {
      await navigator.clipboard.writeText(payment.to_upi_id ?? "");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      window.prompt("Copy this UPI ID", payment.to_upi_id ?? "");
    }
  }

  return (
    <li className="rounded-2xl bg-surface">
      <div className="flex items-end justify-between gap-3 p-4">
        <div className="min-w-0">
          <p className="text-muted">
            <span className="font-semibold text-ink">{payment.from_name}</span> pays{" "}
            <span className="font-semibold text-ink">{payment.to_name}</span>
          </p>
          <p className="mt-1 font-display text-4xl font-extrabold tracking-tight">{formatPaise(payment.amount)}</p>
        </div>
      </div>

      <div className="ticket-tear" aria-hidden="true" />

      <div className="flex flex-col gap-3 p-4">
        {payment.upi_link !== null ? (
          <>
            <a href={payment.upi_link} className="btn btn-primary w-full">
              Pay {formatPaise(payment.amount)} with a UPI app
            </a>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="btn btn-quiet !min-h-10 text-sm"
                aria-expanded={showQr}
                onClick={() => setShowQr(!showQr)}
              >
                {showQr ? "Hide QR code" : "Show QR code"}
              </button>
              <button type="button" className="btn btn-quiet !min-h-10 text-sm" onClick={copyUpiId}>
                {copied ? "Copied" : "Copy UPI ID"}
              </button>
            </div>
            {showQr && (
              <div className="flex flex-col items-center gap-2 rounded-xl bg-paper p-4 text-center">
                <div className="rounded-lg bg-white p-3">
                  <QRCodeSVG value={payment.upi_link} size={176} level="M" title={`UPI payment to ${payment.to_name}`} />
                </div>
                <p className="max-w-xs text-sm text-muted">
                  On a computer? Scan this with your phone’s camera or a UPI app. It pays {payment.to_upi_id}.
                </p>
              </div>
            )}
          </>
        ) : (
          <>
            <p className="text-muted">
              {payment.to_name} has no UPI ID saved, so there is no payment link yet.
            </p>
            <UpiIdEditor
              groupId={groupId}
              member={{ id: payment.to_id, name: payment.to_name, upi_id: null }}
              onSaved={onChanged}
              compact
            />
          </>
        )}
      </div>
    </li>
  );
}
