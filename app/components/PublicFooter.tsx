import Link from "next/link";

const links = [
  { label: "Performance", href: "/performance" },
  { label: "How It Works", href: "/how-it-works" },
  { label: "Pricing", href: "/pricing" },
  { label: "FAQ", href: "/faq" },
  { label: "Rules & Disclaimer", href: "/rules" },
  { label: "Terms of Service", href: "/terms" },
  { label: "Privacy Policy", href: "/privacy" },
];

export default function PublicFooter() {
  return (
    <footer className="border-t border-qbl-border bg-bg-primary">
      <div className="max-w-[1140px] mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-8">
          <Link
            href="/"
            className="font-display font-bold text-lg tracking-[0.08em] text-text-primary"
          >
            QUANT<span className="text-accent">BET</span>LABS
          </Link>
          <nav className="flex flex-wrap gap-x-6 gap-y-2">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="text-text-muted text-sm hover:text-text-secondary transition-colors"
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="pt-6 border-t border-qbl-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <p className="text-text-muted text-[0.8rem] shrink-0">
            &copy; 2026 Insight Engine, LLC d/b/a Quant Bet Labs. All rights reserved.
          </p>
          <div className="flex flex-col gap-1 sm:text-right text-[0.75rem] text-text-muted leading-snug">
            <p>For informational and entertainment purposes only. Not financial or gambling advice.</p>
            <p>Must be 18+ or legal age in your jurisdiction. Past performance does not guarantee future results.</p>
            <p>
              Gambling problem?{" "}
              <a href="tel:18004262537" className="text-text-secondary hover:text-accent transition-colors">
                Call or text 1-800-GAMBLER (1-800-426-2537)
              </a>{" "}
              &mdash; free, confidential help 24/7.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
