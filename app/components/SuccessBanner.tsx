"use client";

import { useState } from "react";
import Link from "next/link";
import { DISCORD_INVITE_URL } from "@/lib/constants";

type Props = {
  tier: string;
};

export default function SuccessBanner({ tier }: Props) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const tierLabel =
    tier === "vip" ? "VIP (1–5★)" : tier === "premium" ? "Premium (1–3★)" : "Basic (1★)";

  return (
    <div className="mb-6 rounded-[12px] border border-[rgba(0,212,170,0.35)] bg-[rgba(0,212,170,0.06)] px-5 py-4 flex items-start gap-4">
      <span className="text-accent text-xl shrink-0 mt-0.5">✓</span>
      <div className="flex-1 min-w-0">
        <p className="font-display font-semibold text-text-primary text-sm mb-0.5">
          You&apos;re subscribed — {tierLabel} access is active.
        </p>
        <p className="text-text-secondary text-sm leading-[1.6]">
          There are no in-app push notifications — Discord is how you get alerted the moment a pick is found.
          Join below and your channel access will match your plan. When a pick drops, you&apos;ll get a Discord ping and can open the dashboard or bet directly from the alert.
        </p>
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <a
            href={DISCORD_INVITE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 font-display font-semibold text-xs px-3 py-1.5 rounded-[8px] bg-[#5865f2] hover:bg-[#4752c4] text-white transition-all"
          >
            Join Discord
          </a>
          <Link
            href="/how-to-use"
            className="inline-flex items-center gap-1.5 font-display font-semibold text-xs px-3 py-1.5 rounded-[8px] border border-[rgba(0,212,170,0.35)] text-accent hover:bg-[rgba(0,212,170,0.08)] transition-all"
          >
            See the guide →
          </Link>
        </div>
      </div>
      <button
        onClick={() => setDismissed(true)}
        aria-label="Dismiss"
        className="shrink-0 text-text-muted hover:text-text-secondary transition-colors text-lg leading-none mt-0.5 cursor-pointer"
      >
        ×
      </button>
    </div>
  );
}
