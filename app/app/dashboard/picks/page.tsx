import Link from "next/link";
import { DISCORD_INVITE_URL } from "@/lib/constants";
import { currentUser } from "@clerk/nextjs/server";
import PicksTable from "./PicksTable";
import DiscordCTA from "@/components/DiscordCTA";

function maxStars(tier: string | undefined): number | null {
  if (tier === "vip") return 5;
  if (tier === "premium") return 4;
  if (tier === "basic") return 2;
  return null; // no subscription
}

function tierLabel(tier: string | undefined) {
  if (tier === "vip") return "1–5★";
  if (tier === "premium") return "1–4★";
  if (tier === "basic") return "1–2★";
  return null;
}

export default async function PicksPage() {
  const user = await currentUser();
  const tier = user?.publicMetadata?.tier as string | undefined;
  const stars = maxStars(tier);
  const label = tierLabel(tier);

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Current Picks</h1>
        <p className="text-text-secondary text-sm">
          Live +EV opportunities — model runs every 15 minutes.
        </p>
      </div>

      {stars === null ? (
        /* No subscription — upgrade wall */
        <div className="rounded-[12px] border border-qbl-border bg-bg-surface px-8 py-16 text-center max-w-[520px] mx-auto mt-8">
          <div className="text-3xl mb-4 opacity-60">🔒</div>
          <h2 className="font-display text-xl font-semibold text-text-primary mb-2">
            Subscribe to access picks
          </h2>
          <p className="text-text-secondary text-sm leading-[1.7] mb-6">
            You&apos;re signed in but don&apos;t have an active subscription yet. Choose a plan to
            start seeing live +EV picks.
          </p>
          <Link
            href="/pricing"
            className="inline-block font-display font-semibold text-sm px-6 py-3 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px]"
          >
            View Plans
          </Link>
        </div>
      ) : (
        <>
          <PicksTable maxStars={stars} />

          <div className="mt-8">
            <DiscordCTA
              variant="compact"
              heading="Get alerts the moment picks are found"
              subtext="Discord pings fire before the dashboard updates. Don't miss a line."
              href={DISCORD_INVITE_URL}
            />
          </div>
        </>
      )}
    </div>
  );
}
