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
    tier === "vip" ? "VIP (1–5★)" : tier === "premium" ? "Premium (1–4★)" : "Basic (1–2★)";

  return (
    <div className="mb-6 rounded-[12px] border border-[rgba(0,212,170,0.35)] bg-[rgba(0,212,170,0.06)] px-5 py-4 flex items-start gap-4">
      <span className="text-accent text-xl shrink-0 mt-0.5">✓</span>
      <div className="flex-1 min-w-0">
        <p className="font-display font-semibold text-text-primary text-sm mb-0.5">
          You&apos;re subscribed — {tierLabel} access is active.
        </p>
        <p className="text-text-secondary text-sm leading-[1.6]">
          Picks update every 15 minutes. Stars indicate model confidence — higher is stronger.
          For real-time alerts the moment a pick is found,{" "}
          <a
            href={DISCORD_INVITE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:text-accent-hover underline underline-offset-2 transition-colors"
          >
            join the Discord
          </a>
          {" "}and your channel access will match your plan.
        </p>
        <div className="mt-3">
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
