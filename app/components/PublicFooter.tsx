import Link from "next/link";

const links = [
  { label: "Performance", href: "/performance" },
  { label: "How It Works", href: "/how-it-works" },
  { label: "Pricing", href: "/pricing" },
  { label: "FAQ", href: "/faq" },
  { label: "Rules & Disclaimer", href: "/rules" },
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
        <div className="pt-6 border-t border-qbl-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <p className="text-text-muted text-[0.8rem]">
            &copy; 2026 Quant Bet Labs. All rights reserved.
          </p>
          <p className="text-text-muted text-[0.75rem] sm:text-right max-w-[480px] leading-[1.5]">
            Not financial or legal advice. Sports betting involves risk. Must be 21+ and in a legal
            jurisdiction. Past performance does not guarantee future results.
          </p>
        </div>
      </div>
    </footer>
  );
}
