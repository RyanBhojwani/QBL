import PublicLayout from "@/components/PublicLayout";

export default function RulesPage() {
  return (
    <PublicLayout>
      {/* Header */}
      <div className="relative pt-[72px] py-16 overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at 50% 0%, rgba(0,212,170,0.04) 0%, transparent 60%)",
          }}
        />
        <div className="relative max-w-[1140px] mx-auto px-6">
          <h1 className="font-display text-[clamp(1.8rem,4vw,3rem)] font-bold tracking-[-0.02em] mb-3">
            Rules & Disclaimer
          </h1>
          <p className="text-text-secondary text-[1.05rem] max-w-[560px] leading-[1.7]">
            Please read before using Quant Bet Labs.
          </p>
        </div>
      </div>

      <div className="max-w-[860px] mx-auto px-6 pb-20 space-y-8">
        <Section title="Not Financial Advice">
          Quant Bet Labs is an informational service. Nothing on this platform constitutes financial,
          legal, or investment advice. All content is provided for entertainment and educational
          purposes only. You are solely responsible for your own betting decisions.
        </Section>

        <Section title="Age and Jurisdiction">
          Sports betting is only legal in certain jurisdictions and for individuals who meet the
          minimum legal age requirement (typically 21+ in the United States). It is your
          responsibility to confirm that sports betting is legal in your location before using this
          service. Quant Bet Labs does not facilitate, process, or accept wagers.
        </Section>

        <Section title="No Guarantee of Results">
          Past performance does not guarantee future results. Even bets with a positive expected
          value can and will lose. Sports betting involves significant financial risk. Do not bet
          more than you can afford to lose. Variance is real — a statistically positive strategy
          can experience long losing streaks.
        </Section>

        <Section title="Bankroll Management">
          We strongly recommend using a structured bankroll management approach. Our model provides
          Kelly criterion sizing suggestions, but these are guidelines only. Never chase losses.
          Treat sports betting as a long-term, data-driven activity — not a get-rich-quick scheme.
        </Section>

        <Section title="Model Accuracy">
          Our models are built with best-effort accuracy using publicly available odds data from The
          Odds API. Prices shown may differ from actual available prices due to line movement, data
          delays, or book-specific restrictions. Always verify odds at the sportsbook before placing
          a wager.
        </Section>

        <Section title="Account Restrictions">
          Consistently winning at sportsbooks may result in account limits or restrictions imposed
          by the sportsbooks themselves. Quant Bet Labs has no control over sportsbook account
          management policies. This is a known risk of +EV betting.
        </Section>

        <Section title="Data and Privacy">
          We collect only the minimum data necessary to provide the service. Payment processing is
          handled by Stripe. Authentication is handled by Clerk. We do not sell your data to third
          parties.
        </Section>

        <Section title="Subscription Terms">
          All subscriptions are billed monthly and can be cancelled at any time. Refunds are
          evaluated on a case-by-case basis. By subscribing, you agree to our Terms of Service and
          Privacy Policy.
        </Section>

        <div className="text-text-muted text-xs border-t border-qbl-border pt-6">
          Last updated: May 2026. For questions, contact{" "}
          <a
            href="mailto:support@quantbetlabs.com"
            className="text-accent hover:underline"
          >
            support@quantbetlabs.com
          </a>
          .
        </div>
      </div>
    </PublicLayout>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 sm:p-8">
      <h2 className="font-display text-base font-semibold text-text-primary mb-3">{title}</h2>
      <p className="text-text-secondary text-sm leading-[1.75]">{children}</p>
    </section>
  );
}
