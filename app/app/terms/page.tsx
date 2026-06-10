import PublicLayout from "@/components/PublicLayout";

export default function TermsPage() {
  return (
    <PublicLayout>
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
            Terms of Service
          </h1>
          <p className="text-text-secondary text-[1.05rem] max-w-[560px] leading-[1.7]">
            Please read carefully before subscribing.
          </p>
        </div>
      </div>

      <div className="max-w-[860px] mx-auto px-6 pb-20 space-y-6">

        <Section title="1. Agreement to Terms">
          By accessing or subscribing to Quant Bet Labs (operated by Insight Engine, LLC, a Virginia
          limited liability company), you agree to be bound by these Terms of Service. If you do not
          agree, do not use this service. These Terms apply to all visitors, subscribers, and users.
        </Section>

        <Section title="2. Nature of the Service">
          Quant Bet Labs is a sports betting <strong>information service</strong>. We provide
          statistical analysis of publicly available sports odds data. We do not place bets, accept
          wagers, operate as a sportsbook, act as a bookmaker, or provide personalized financial,
          investment, or gambling advice. Nothing on this platform — including picks, star ratings,
          EV figures, Kelly sizing suggestions, or performance data — constitutes a recommendation to
          place any specific wager. All content is provided for informational and entertainment
          purposes only. You are solely responsible for all betting decisions you make.
        </Section>

        <Section title="3. Eligibility">
          You must be at least 18 years of age (or the minimum legal age in your jurisdiction,
          whichever is higher) to subscribe. You must be located in a jurisdiction where accessing
          sports betting information services is lawful. By subscribing, you represent and warrant
          that you meet these requirements. We make no representation that the service is appropriate
          or legal for use in all locations. Compliance with local laws is your responsibility.
        </Section>

        <Section title="4. Subscriptions and Billing">
          Subscriptions are billed on a recurring monthly basis. Your first charge occurs at the time
          of signup. Subsequent charges occur on the same calendar day each month. You authorize
          Insight Engine, LLC to charge your payment method on this recurring basis until you cancel.
          Prices are stated in US dollars. We reserve the right to modify pricing with at least 30
          days' written notice to your registered email address.
        </Section>

        <Section title="5. Cancellation and Refunds">
          You may cancel your subscription at any time through the Account page. Upon cancellation,
          your access continues until the end of the current billing period. No partial refunds are
          issued for unused days within a billing cycle. All subscription fees are non-refundable
          except where required by applicable law. If you believe you were charged in error, contact{" "}
          <a href="mailto:support@quantbetlabs.com" className="text-accent hover:underline">
            support@quantbetlabs.com
          </a>{" "}
          within 7 days of the charge.
        </Section>

        <Section title="6. Disclaimer of Warranties">
          The service is provided &quot;as is&quot; and &quot;as available&quot; without warranties
          of any kind, express or implied, including but not limited to warranties of merchantability,
          fitness for a particular purpose, or non-infringement. We do not warrant that picks will be
          profitable, that the model will continue to perform at any historical level, that the
          service will be uninterrupted or error-free, or that odds data will be accurate at the time
          you view it. Past performance does not guarantee future results.
        </Section>

        <Section title="7. Limitation of Liability">
          To the maximum extent permitted by applicable law, Insight Engine, LLC, its members,
          officers, employees, contractors, and affiliates shall not be liable for: (a) any betting
          or gambling losses you incur based on information from this service; (b) any indirect,
          incidental, consequential, special, exemplary, or punitive damages; (c) any loss of
          profits, revenue, data, or business opportunity; or (d) any damages arising from your
          reliance on picks, odds, or performance data displayed on the platform. In no event shall
          our total aggregate liability to you exceed the total amount you paid us in the twelve (12)
          months immediately preceding the claim.
        </Section>

        <Section title="8. No Guarantee of Results">
          Sports betting involves substantial financial risk. Even bets with a positive expected
          value will lose frequently due to variance. Subscribing to this service does not guarantee
          any profit. The model&apos;s historical performance is not a guarantee or prediction of
          future performance. You should never bet more than you can afford to lose.
        </Section>

        <Section title="9. User Conduct">
          You agree not to: share your account credentials with others; resell, redistribute, or
          republish picks or data from this platform; use automated tools to scrape or extract data;
          use the service for any unlawful purpose; or attempt to reverse-engineer the model or
          underlying algorithms. We reserve the right to suspend or terminate accounts that violate
          these restrictions without refund.
        </Section>

        <Section title="10. Intellectual Property">
          All content, models, algorithms, software, design, and branding on this platform are the
          property of Insight Engine, LLC or its licensors. Your subscription grants you a limited,
          non-exclusive, non-transferable right to access the service for personal use only. No
          ownership interest is transferred.
        </Section>

        <Section title="11. Third-Party Services">
          This service uses Stripe for payment processing, Clerk for authentication, Supabase for
          data storage, and Vercel for hosting. Your use of these services is also governed by their
          respective terms and privacy policies. We are not responsible for the practices of these
          third parties.
        </Section>

        <Section title="12. Governing Law and Dispute Resolution">
          These Terms are governed by the laws of the Commonwealth of Virginia, without regard to
          its conflict of law provisions. Any dispute arising from or relating to these Terms or the
          service shall be resolved through binding individual arbitration administered by the
          American Arbitration Association (AAA) under its Commercial Arbitration Rules. YOU WAIVE
          THE RIGHT TO PARTICIPATE IN A CLASS ACTION LAWSUIT OR CLASS-WIDE ARBITRATION. Nothing in
          this section prevents either party from seeking emergency injunctive relief in a court of
          competent jurisdiction.
        </Section>

        <Section title="13. Changes to These Terms">
          We may update these Terms at any time. We will notify you of material changes by email or
          by posting a notice on the platform. Continued use of the service after changes take effect
          constitutes acceptance of the updated Terms. If you do not agree to updated Terms, you must
          cancel your subscription before they take effect.
        </Section>

        <Section title="14. Termination">
          We reserve the right to suspend or terminate your account at our sole discretion, including
          for violation of these Terms, fraudulent activity, or abuse of the service. In the event of
          termination for cause, no refund will be issued. In the event of termination without cause,
          we will provide a pro-rated refund for the unused portion of your billing period.
        </Section>

        <div className="text-text-muted text-xs border-t border-qbl-border pt-6 space-y-1">
          <p>Insight Engine, LLC d/b/a Quant Bet Labs · Virginia Limited Liability Company</p>
          <p>Last updated: June 2026. For questions, contact{" "}
            <a href="mailto:support@quantbetlabs.com" className="text-accent hover:underline">
              support@quantbetlabs.com
            </a>.
          </p>
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
