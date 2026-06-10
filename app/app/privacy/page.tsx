import PublicLayout from "@/components/PublicLayout";

export default function PrivacyPage() {
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
            Privacy Policy
          </h1>
          <p className="text-text-secondary text-[1.05rem] max-w-[560px] leading-[1.7]">
            How Insight Engine, LLC collects, uses, and protects your information.
          </p>
        </div>
      </div>

      <div className="max-w-[860px] mx-auto px-6 pb-20 space-y-6">

        <Section title="1. Who We Are">
          Quant Bet Labs is operated by Insight Engine, LLC, a Virginia limited liability company.
          References to &quot;we,&quot; &quot;us,&quot; or &quot;our&quot; in this policy refer to
          Insight Engine, LLC. This Privacy Policy describes how we collect, use, store, and share
          information when you use our website and subscription service at quantbetlabs.com.
        </Section>

        <Section title="2. Information We Collect">
          <span>We collect the following categories of information:</span>
          <ul className="mt-3 space-y-2 list-none">
            <Li><strong>Account information:</strong> Your name and email address, collected when you create an account via Clerk.</Li>
            <Li><strong>Payment information:</strong> Payment card details are collected and processed by Stripe. We do not store or have direct access to your full card number, CVV, or bank account details.</Li>
            <Li><strong>Subscription data:</strong> Your current plan tier, subscription status, and billing history as reported by Stripe.</Li>
            <Li><strong>Filter preferences:</strong> Your saved sport, book, and star-range filter settings, stored in our database to persist across sessions.</Li>
            <Li><strong>Usage data:</strong> Pages visited, features used, and general interaction patterns, collected through server logs and any analytics tools we operate.</Li>
            <Li><strong>Communications:</strong> Any messages you send to us via email or Discord.</Li>
          </ul>
        </Section>

        <Section title="3. How We Use Your Information">
          <span>We use the information we collect to:</span>
          <ul className="mt-3 space-y-2 list-none">
            <Li>Provide and operate the subscription service</Li>
            <Li>Process payments and manage billing</Li>
            <Li>Send transactional emails (subscription confirmations, receipts, service notices)</Li>
            <Li>Save your filter preferences across sessions</Li>
            <Li>Respond to support requests</Li>
            <Li>Detect and prevent fraud or abuse</Li>
            <Li>Improve and develop the service</Li>
          </ul>
          <span className="block mt-3">
            We do not use your information for targeted advertising. We do not sell your personal
            data to third parties.
          </span>
        </Section>

        <Section title="4. Third-Party Service Providers">
          We share your information with the following service providers solely to the extent
          necessary to deliver the service:
          <ul className="mt-3 space-y-3 list-none">
            <Li><strong>Clerk</strong> — authentication and account management. Stores your name, email, and subscription tier. <a href="https://clerk.com/privacy" className="text-accent hover:underline" target="_blank" rel="noopener noreferrer">Clerk Privacy Policy</a>.</Li>
            <Li><strong>Stripe</strong> — payment processing and subscription billing. Stores your payment method and billing history. <a href="https://stripe.com/privacy" className="text-accent hover:underline" target="_blank" rel="noopener noreferrer">Stripe Privacy Policy</a>.</Li>
            <Li><strong>Supabase</strong> — database hosting for picks data and user preferences. <a href="https://supabase.com/privacy" className="text-accent hover:underline" target="_blank" rel="noopener noreferrer">Supabase Privacy Policy</a>.</Li>
            <Li><strong>Vercel</strong> — website hosting and deployment. <a href="https://vercel.com/legal/privacy-policy" className="text-accent hover:underline" target="_blank" rel="noopener noreferrer">Vercel Privacy Policy</a>.</Li>
            <Li><strong>Discord</strong> — optional community and alert channel. If you join our Discord server, Discord&apos;s own privacy policy governs your data there. <a href="https://discord.com/privacy" className="text-accent hover:underline" target="_blank" rel="noopener noreferrer">Discord Privacy Policy</a>.</Li>
          </ul>
          <span className="block mt-3">
            We do not share your information with any other third parties except as required by law.
          </span>
        </Section>

        <Section title="5. Data Retention">
          We retain your account information for as long as your account is active. If you delete
          your account, we will delete or anonymize your personal data within 30 days, except where
          we are required to retain it for legal or financial compliance purposes (e.g., payment
          records required by tax law). Filter preferences are deleted immediately upon account
          deletion.
        </Section>

        <Section title="6. Your Privacy Rights">
          Depending on your location, you may have the following rights regarding your personal data:
          <ul className="mt-3 space-y-2 list-none">
            <Li><strong>Access:</strong> Request a copy of the personal data we hold about you.</Li>
            <Li><strong>Correction:</strong> Request correction of inaccurate data.</Li>
            <Li><strong>Deletion:</strong> Request deletion of your personal data (&quot;right to be forgotten&quot;).</Li>
            <Li><strong>Portability:</strong> Request your data in a portable format.</Li>
            <Li><strong>Opt-out of sale:</strong> We do not sell personal data, so no opt-out is needed.</Li>
          </ul>
          <span className="block mt-3">
            These rights apply to residents of Virginia (under the Virginia CDPA), California (under
            the CCPA/CPRA), and the European Union (under GDPR), among others. To exercise any of
            these rights, email{" "}
            <a href="mailto:support@quantbetlabs.com" className="text-accent hover:underline">
              support@quantbetlabs.com
            </a>{" "}
            with your request. We will respond within 45 days.
          </span>
        </Section>

        <Section title="7. Cookies and Tracking">
          We use cookies and similar technologies to maintain your session (authentication) and
          remember your preferences. We do not use third-party advertising cookies or tracking pixels.
          Essential session cookies cannot be disabled without breaking authentication. If analytics
          tools are added in the future, this policy will be updated.
        </Section>

        <Section title="8. Data Security">
          We implement industry-standard security measures including encrypted data transmission
          (TLS/HTTPS), access controls limiting who can access personal data, and use of reputable
          third-party infrastructure providers. No method of transmission or storage is 100% secure.
          In the event of a data breach affecting your personal information, we will notify you as
          required by applicable law.
        </Section>

        <Section title="9. Children's Privacy">
          This service is not directed to individuals under the age of 18. We do not knowingly
          collect personal information from anyone under 18. If you believe a minor has provided us
          with personal information, contact us at{" "}
          <a href="mailto:support@quantbetlabs.com" className="text-accent hover:underline">
            support@quantbetlabs.com
          </a>{" "}
          and we will delete it promptly.
        </Section>

        <Section title="10. Changes to This Policy">
          We may update this Privacy Policy from time to time. We will notify you of material changes
          by email or by posting a notice on the platform. The date at the bottom of this page
          reflects when this policy was last updated. Continued use of the service after updates
          constitutes acceptance of the revised policy.
        </Section>

        <Section title="11. Contact">
          For privacy questions, data requests, or to report a concern, contact us at:{" "}
          <a href="mailto:support@quantbetlabs.com" className="text-accent hover:underline">
            support@quantbetlabs.com
          </a>
          <br />
          <span className="block mt-1">Insight Engine, LLC d/b/a Quant Bet Labs · Virginia, United States</span>
        </Section>

        <div className="text-text-muted text-xs border-t border-qbl-border pt-6">
          Last updated: June 2026.
        </div>
      </div>
    </PublicLayout>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 sm:p-8">
      <h2 className="font-display text-base font-semibold text-text-primary mb-3">{title}</h2>
      <div className="text-text-secondary text-sm leading-[1.75]">{children}</div>
    </section>
  );
}

function Li({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex gap-2">
      <span className="text-accent shrink-0 mt-0.5">·</span>
      <span>{children}</span>
    </li>
  );
}
