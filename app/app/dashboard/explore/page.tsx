import { currentUser } from "@clerk/nextjs/server";
import Link from "next/link";
import ExploreTab from "@/components/ExploreTab";

function UpgradeWall({ hasSubscription }: { hasSubscription: boolean }) {
  return (
    <div className="rounded-[12px] border border-qbl-border bg-bg-surface px-8 py-14 text-center max-w-[520px] mx-auto mt-20">
      <div className="text-3xl mb-4 opacity-60">🔍</div>
      <h2 className="font-display text-xl font-semibold text-text-primary mb-2">
        Explore is a Premium feature
      </h2>
      <p className="text-text-secondary text-sm leading-[1.7] mb-6">
        {hasSubscription
          ? "Upgrade to Premium or VIP to search any team or sportsbook and see what the model finds — even for lines that didn't make the picks threshold."
          : "Subscribe to Premium or VIP to access the Explore tab — search teams and sportsbooks to see full model output on any game."}
      </p>
      <Link
        href="/pricing"
        className="inline-block font-display font-semibold text-sm px-6 py-3 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px]"
      >
        {hasSubscription ? "Upgrade to Premium" : "View Plans"}
      </Link>
    </div>
  );
}

export default async function ExplorePage() {
  const user = await currentUser();
  const tier = user?.publicMetadata?.tier as string | undefined;

  if (!tier || tier === "basic") {
    return (
      <div>
        <div className="mb-8">
          <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Explore</h1>
          <p className="text-text-secondary text-sm">
            Search any team or sportsbook to see full model output.
          </p>
        </div>
        <UpgradeWall hasSubscription={tier === "basic"} />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Explore</h1>
        <p className="text-text-secondary text-sm">
          Search any team or sportsbook to see what the model finds — including lines below the picks threshold.
        </p>
      </div>
      <ExploreTab />
    </div>
  );
}
