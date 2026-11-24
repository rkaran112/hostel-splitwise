"use client";

import { useState } from "react";

// Two ways to send the group link to friends: copy it, or open WhatsApp with it filled in.
export function ShareButtons({ groupName }: { groupName: string }) {
  const [copied, setCopied] = useState(false);

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard blocked: show the link so it can be copied by hand.
      window.prompt("Copy this link", window.location.href);
    }
  }

  function shareOnWhatsApp() {
    const message = `Join “${groupName}” on Hostel Splitwise: ${window.location.href}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, "_blank", "noopener");
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button type="button" className="btn btn-quiet" onClick={copyLink}>
        {copied ? "Link copied" : "Copy group link"}
      </button>
      <button type="button" className="btn btn-quiet" onClick={shareOnWhatsApp}>
        Share on WhatsApp
      </button>
    </div>
  );
}
