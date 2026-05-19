import { currentUser } from "@clerk/nextjs/server";
import { DISCORD_INVITE_URL } from "@/lib/constants";
import DiscordCTA from "@/components/DiscordCTA";
import ManageSubscriptionButton from "./ManageSubscriptionButton";
import SignOutBtn from "./SignOutBtn";

export default async function AccountPage() {
  const user = await currentUser();
  const tier = (user?.publicMetadata?.tier as string | undefined) ?? null;
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
            {tier ? (
              <span className="inline-flex items-center gap-1.5 text-accent text-sm font-display font-semibold capitalize">
                <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block" />
                {tier}
              </span>
            ) : (
              <span className="text-text-muted text-sm">No active plan</span>
            )}
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-text-secondary text-sm">Status</span>
            <span className={`text-sm font-medium ${tier ? "text-accent" : "text-text-muted"}`}>
              {tier ? "Active" : "—"}
            </span>
          </div>
        </div>
        <div className="flex gap-3 mt-5">
          {tier ? (
            <ManageSubscriptionButton />
          ) : (
            <a
              href="/pricing"
              className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] bg-accent text-bg-primary border-2 border-accent transition-all hover:bg-accent-hover hover:border-accent-hover hover:-translate-y-[2px]"
            >
              View Plans
            </a>
          )}
        </div>
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
          href={DISCORD_INVITE_URL}
        />
      </div>

      {/* Sign out */}
      <section className="bg-bg-surface border border-[rgba(239,68,68,0.2)] rounded-[12px] p-6">
        <h2 className="font-display text-base font-semibold text-text-primary mb-4">Sign Out</h2>
        <p className="text-text-secondary text-sm mb-4">
          You&apos;ll be returned to the landing page.
        </p>
        <SignOutBtn />
      </section>
    </div>
  );
}
