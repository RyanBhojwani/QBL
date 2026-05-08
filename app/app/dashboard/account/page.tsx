import Link from "next/link";
import { currentUser } from "@clerk/nextjs/server";
import DiscordCTA from "@/components/DiscordCTA";

export default async function AccountPage() {
  const user = await currentUser();
  const tier = (user?.publicMetadata?.tier as string | undefined) ?? "basic";
  const email = user?.primaryEmailAddress?.emailAddress ?? "—";
  const memberSince = user?.createdAt
    ? new Date(user.createdAt).toLocaleDateString("en-US", { month: "long", year: "numeric" })
    : "—";
  return (
    <div className="max-w-[640px]">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Account</h1>
        <p className="text-text-secondary text-sm">Manage your subscription and profile.</p>
      </div>

      {/* Profile */}
      <section className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 mb-4">
        <h2 className="font-display text-base font-semibold text-text-primary mb-4">Profile</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-qbl-border">
            <span className="text-text-secondary text-sm">Email</span>
            <span className="text-text-primary text-sm font-medium">{email}</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-text-secondary text-sm">Member since</span>
            <span className="text-text-primary text-sm font-medium">{memberSince}</span>
          </div>
        </div>
      </section>

      {/* Subscription */}
      <section className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 mb-4">
        <h2 className="font-display text-base font-semibold text-text-primary mb-4">
          Subscription
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-qbl-border">
            <span className="text-text-secondary text-sm">Current plan</span>
            <span className="inline-flex items-center gap-1.5 text-accent text-sm font-display font-semibold capitalize">
              <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block" />
              {tier}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-qbl-border">
            <span className="text-text-secondary text-sm">Status</span>
            <span className="text-text-muted text-sm">—</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-text-secondary text-sm">Next billing date</span>
            <span className="text-text-muted text-sm">—</span>
          </div>
        </div>
        <div className="flex gap-3 mt-5">
          <Link
            href="/pricing"
            className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] bg-accent text-bg-primary border-2 border-accent transition-all hover:bg-accent-hover hover:border-accent-hover hover:-translate-y-[2px]"
          >
            Upgrade Plan
          </Link>
          <button
            disabled
            className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] border border-qbl-border text-text-muted cursor-not-allowed opacity-50"
          >
            Cancel Subscription
          </button>
        </div>
        <p className="text-text-muted text-xs mt-3">Billing managed via Stripe — coming soon.</p>
      </section>

      {/* Notifications */}
      <section className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 mb-4">
        <h2 className="font-display text-base font-semibold text-text-primary mb-4">
          Notifications
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-qbl-border">
            <div>
              <p className="text-text-secondary text-sm">Discord alerts</p>
              <p className="text-text-muted text-xs mt-0.5">Picks posted to your tier channel</p>
            </div>
            <span className="text-text-muted text-xs">Configure in Discord</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-text-secondary text-sm">Email notifications</p>
              <p className="text-text-muted text-xs mt-0.5">Daily summary</p>
            </div>
            <span className="text-text-muted text-xs opacity-50">Coming soon</span>
          </div>
        </div>
      </section>

      {/* Discord */}
      <div className="mb-4">
        <DiscordCTA
          variant="compact"
          heading="Connect your Discord"
          subtext="Alerts fire to your tier's channel the moment picks are found."
          href="#"
        />
      </div>

      {/* Sign out */}
      <section className="bg-bg-surface border border-[rgba(239,68,68,0.2)] rounded-[12px] p-6">
        <h2 className="font-display text-base font-semibold text-text-primary mb-4">Sign Out</h2>
        <p className="text-text-secondary text-sm mb-4">
          You&apos;ll be returned to the landing page.
        </p>
        <Link
          href="/"
          className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] border border-qbl-border text-text-secondary hover:border-[rgba(239,68,68,0.4)] hover:text-red-400 transition-all inline-block"
        >
          Sign Out
        </Link>
      </section>
    </div>
  );
}
