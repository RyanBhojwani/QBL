"use client";

import { useAuth } from "@clerk/nextjs";
import { DISCORD_INVITE_URL } from "@/lib/constants";
import { useRouter } from "next/navigation";
import { useState } from "react";
import PublicLayout from "@/components/PublicLayout";
import DiscordCTA from "@/components/DiscordCTA";

const tiers = [
  {
    name: "Basic",
    price: "$25",
    period: "/mo",
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC!,
    description: "Entry-level access to the model. Solid volume of picks across all markets.",
    features: [
      "1–2 star picks",
      "Real-time Discord alerts",
      "All sports & markets",
    ],
    cta: "Get Started",
    highlight: false,
  },
  {
    name: "Premium",
    price: "$50",
    period: "/mo",
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_PREMIUM!,
    description: "Higher-confidence picks plus education to understand the edge behind every bet.",
    features: [
      "1–4 star picks",
      "Real-time Discord alerts",
      "All sports & markets",
      "Educational content",
    ],
    cta: "Get Premium",
    highlight: true,
  },
  {
    name: "VIP",
    price: "$100",
    period: "/mo",
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_VIP!,
    description: "Full access. Every pick the model finds, including our highest-confidence plays.",
    features: [
      "All picks — 1 through 5 stars",
      "Real-time Discord alerts",
      "All sports & markets",
      "Educational content",
    ],
    cta: "Go VIP",
    highlight: false,
  },
];

export default function PricingPage() {
  const { isSignedIn } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  const handleCheckout = async (priceId: string) => {
    if (!isSignedIn) {
      router.push("/sign-in");
      return;
    }

    setLoading(priceId);
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priceId }),
      });
      const { url, error } = await res.json();
      if (error) throw new Error(error);
      window.location.href = url;
    } catch (err) {
      console.error("Checkout failed:", err);
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <PublicLayout>
      {/* Header */}
      <div className="relative pt-[72px] py-20 overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at 50% 0%, rgba(0,212,170,0.07) 0%, transparent 60%)",
          }}
        />
        <div className="relative max-w-[1140px] mx-auto px-6 text-center">
          <h1 className="font-display text-[clamp(2rem,4vw,3.5rem)] font-bold tracking-[-0.02em] mb-4">
            Simple, <span className="text-accent">Transparent</span> Pricing
          </h1>
          <p className="text-text-secondary text-lg max-w-[520px] mx-auto leading-[1.7]">
            Choose your tier. Higher tiers surface higher-confidence picks.
            All plans include real-time Discord alerts.
          </p>
        </div>
      </div>

      {/* Tier cards */}
      <div className="max-w-[1140px] mx-auto px-6 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`relative rounded-[12px] p-8 border transition-all ${
                tier.highlight
                  ? "bg-bg-surface border-accent shadow-[0_0_40px_rgba(0,212,170,0.1)]"
                  : "bg-bg-surface border-qbl-border hover:border-[rgba(0,212,170,0.25)]"
              }`}
            >
              {tier.highlight && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <span className="font-display text-xs font-semibold tracking-[0.1em] uppercase px-4 py-1.5 bg-accent text-bg-primary rounded-full">
                    Most Popular
                  </span>
                </div>
              )}
              <div className="mb-6">
                <h3 className="font-display text-xl font-semibold text-text-primary mb-2">
                  {tier.name}
                </h3>
                <div className="flex items-end gap-1 mb-3">
                  <span className="font-display text-4xl font-bold text-accent">{tier.price}</span>
                  <span className="text-text-muted mb-1.5">{tier.period}</span>
                </div>
                <p className="text-text-secondary text-sm leading-[1.6]">{tier.description}</p>
              </div>
              <ul className="space-y-3 mb-8">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-text-secondary">
                    <span className="text-accent font-bold mt-0.5 shrink-0">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleCheckout(tier.priceId)}
                disabled={loading === tier.priceId}
                className={`w-full text-center font-display font-semibold py-3.5 px-6 rounded-[8px] border-2 transition-all duration-250 hover:-translate-y-[2px] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0 cursor-pointer ${
                  tier.highlight
                    ? "bg-accent text-bg-primary border-accent hover:bg-accent-hover hover:border-accent-hover hover:shadow-[0_6px_30px_rgba(0,212,170,0.4)]"
                    : "bg-transparent text-accent border-accent hover:bg-[rgba(0,212,170,0.1)]"
                }`}
              >
                {loading === tier.priceId ? "Loading…" : tier.cta}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-text-muted text-sm mt-10">
          Cancel anytime.
          <span className="mx-2 opacity-40">·</span>
          Questions?{" "}
          <a href="mailto:support@quantbetlabs.com" className="text-accent hover:underline">
            Contact us
          </a>
        </p>
      </div>

      {/* Discord CTA */}
      <div className="max-w-[1140px] mx-auto px-6 pb-20">
        <DiscordCTA
          variant="compact"
          heading="Not ready to subscribe? Start with Discord."
          subtext="Our free Discord channel posts select picks. No credit card, no commitment."
          href={DISCORD_INVITE_URL}
        />
      </div>
    </PublicLayout>
  );
}
