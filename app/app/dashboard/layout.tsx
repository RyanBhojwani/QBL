"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useUser, useClerk, UserButton } from "@clerk/nextjs";

const navItems = [
  { label: "Picks", href: "/dashboard/picks" },
  { label: "Performance", href: "/dashboard/performance" },
  { label: "Education", href: "/dashboard/education" },
  { label: "How To Use", href: "/dashboard/how-to-use" },
  { label: "FAQ", href: "/dashboard/faq" },
  { label: "Account", href: "/dashboard/account" },
];

const ADMIN_EMAIL = process.env.NEXT_PUBLIC_ADMIN_EMAIL ?? "";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user } = useUser();
  const { signOut } = useClerk();
  const tier = (user?.publicMetadata?.tier as string | undefined) ?? "free";
  const isAdmin = user?.primaryEmailAddress?.emailAddress === ADMIN_EMAIL && ADMIN_EMAIL !== "";

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Top bar */}
      <header
        className="fixed top-0 left-0 right-0 z-50 border-b border-qbl-border h-[72px] flex items-center"
        style={{
          background: "rgba(10,14,23,0.95)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
        }}
      >
        <div className="max-w-[1440px] w-full mx-auto px-6 flex items-center gap-4">
          {/* Logo */}
          <Link
            href="/"
            className="font-display text-xl font-bold tracking-[0.08em] text-text-primary shrink-0"
          >
            QUANT<span className="text-accent">BET</span>LABS
          </Link>

          {/* Desktop tab nav */}
          <nav className="hidden lg:flex flex-1 items-center justify-center gap-1">
            {navItems.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`font-display font-semibold text-sm px-4 py-2 rounded-[8px] transition-all duration-200 ${
                    active
                      ? "bg-[rgba(0,212,170,0.12)] text-accent"
                      : "text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.04)]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
            {isAdmin && (
              <Link
                href="/dashboard/admin"
                className={`font-display font-semibold text-sm px-4 py-2 rounded-[8px] transition-all duration-200 ${
                  pathname.startsWith("/dashboard/admin")
                    ? "bg-[rgba(0,212,170,0.12)] text-accent"
                    : "text-text-muted hover:text-text-secondary hover:bg-[rgba(255,255,255,0.04)]"
                }`}
              >
                Admin
              </Link>
            )}
          </nav>

          {/* Desktop account actions */}
          <div className="hidden lg:flex items-center gap-3 shrink-0">
            <span className="text-text-muted text-sm hidden xl:block">
              {user?.primaryEmailAddress?.emailAddress}
            </span>
            <span className="inline-flex items-center gap-1 font-display text-xs font-semibold px-2 py-1 rounded-full bg-[rgba(0,212,170,0.08)] border border-[rgba(0,212,170,0.18)] text-accent uppercase tracking-[0.06em]">
              {tier}
            </span>
            <UserButton />
          </div>

          {/* Mobile hamburger */}
          <div className="lg:hidden flex items-center gap-3 ml-auto">
            <UserButton />
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileOpen}
              className="flex flex-col justify-center gap-[5px] p-2 text-text-secondary"
            >
              <span
                className={`block w-5 h-0.5 bg-current origin-center transition-all duration-200 ${
                  mobileOpen ? "rotate-45 translate-y-[7px]" : ""
                }`}
              />
              <span
                className={`block w-5 h-0.5 bg-current transition-all duration-200 ${
                  mobileOpen ? "opacity-0" : ""
                }`}
              />
              <span
                className={`block w-5 h-0.5 bg-current origin-center transition-all duration-200 ${
                  mobileOpen ? "-rotate-45 -translate-y-[7px]" : ""
                }`}
              />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile dropdown */}
      <div
        className={`fixed top-[72px] left-0 right-0 z-40 border-b border-qbl-border lg:hidden transition-all duration-200 ${
          mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        style={{
          background: "rgba(10,14,23,0.97)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
        }}
      >
        <div className="px-6 py-4 flex flex-col gap-1">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`font-display font-semibold text-sm py-3 px-3 rounded-[8px] transition-colors ${
                  active
                    ? "bg-[rgba(0,212,170,0.08)] text-accent"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
          {isAdmin && (
            <Link
              href="/dashboard/admin"
              onClick={() => setMobileOpen(false)}
              className={`font-display font-semibold text-sm py-3 px-3 rounded-[8px] transition-colors ${
                pathname.startsWith("/dashboard/admin")
                  ? "bg-[rgba(0,212,170,0.08)] text-accent"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              Admin
            </Link>
          )}
          <div className="pt-3 mt-1 border-t border-qbl-border">
            <button
              onClick={() => { setMobileOpen(false); signOut({ redirectUrl: "/" }); }}
              className="font-display font-semibold text-sm py-2.5 text-text-muted hover:text-text-secondary transition-colors cursor-pointer"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Page content */}
      <main className="flex-1 pt-[72px]">
        <div className="max-w-[1440px] mx-auto px-6 py-8">{children}</div>
      </main>

      {/* Footer */}
      <footer className="border-t border-qbl-border py-5">
        <div className="max-w-[1440px] mx-auto px-6 flex items-center justify-between flex-wrap gap-3">
          <span className="font-display text-sm font-bold tracking-[0.08em] text-text-muted">
            QUANT<span className="text-accent">BET</span>LABS
          </span>
          <p className="text-text-muted text-xs">&copy; 2026 Quant Bet Labs.</p>
        </div>
      </footer>
    </div>
  );
}
