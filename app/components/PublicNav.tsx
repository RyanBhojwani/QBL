"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";

const links = [
  { label: "Performance", href: "/performance" },
  { label: "How It Works", href: "/how-it-works" },
  { label: "Pricing", href: "/pricing" },
  { label: "FAQ", href: "/faq" },
  { label: "Rules", href: "/rules" },
];

export default function PublicNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { isSignedIn } = useAuth();

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-50 border-b border-qbl-border"
        style={{
          background: "rgba(10,14,23,0.88)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
        }}
      >
        <div className="max-w-[1140px] mx-auto px-6 flex items-center justify-between h-[72px]">
          <Link
            href="/"
            className="font-display text-xl font-bold tracking-[0.08em] text-text-primary"
          >
            QUANT<span className="text-accent">BET</span>LABS
          </Link>

          {/* Desktop nav links */}
          <div className="hidden lg:flex items-center gap-6">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`text-[0.9rem] transition-colors duration-200 ${
                  pathname === l.href
                    ? "text-text-primary"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </div>

          {/* Desktop CTAs */}
          <div className="hidden lg:flex items-center gap-3">
            {isSignedIn ? (
              <>
                <Link
                  href="/dashboard/picks"
                  className="font-display font-semibold text-[0.9rem] px-5 py-[9px] rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all duration-200"
                >
                  Dashboard
                </Link>
                <UserButton />
              </>
            ) : (
              <>
                <SignInButton mode="redirect">
                  <button className="font-display font-semibold text-[0.9rem] px-5 py-[9px] rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all duration-200 cursor-pointer">
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton mode="redirect">
                  <button className="font-display font-semibold text-[0.9rem] px-[20px] py-[9px] rounded-[8px] bg-accent text-bg-primary border-2 border-accent transition-all duration-250 hover:bg-accent-hover hover:border-accent-hover hover:-translate-y-[1px] hover:shadow-[0_4px_20px_rgba(0,212,170,0.35)] cursor-pointer">
                    Get Started
                  </button>
                </SignUpButton>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setOpen(!open)}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            className="lg:hidden flex flex-col justify-center gap-[5px] p-2 text-text-secondary"
          >
            <span
              className={`block w-6 h-0.5 bg-current origin-center transition-all duration-200 ${
                open ? "rotate-45 translate-y-[7px]" : ""
              }`}
            />
            <span
              className={`block w-6 h-0.5 bg-current transition-all duration-200 ${
                open ? "opacity-0 scale-x-0" : ""
              }`}
            />
            <span
              className={`block w-6 h-0.5 bg-current origin-center transition-all duration-200 ${
                open ? "-rotate-45 -translate-y-[7px]" : ""
              }`}
            />
          </button>
        </div>
      </nav>

      {/* Mobile dropdown */}
      <div
        className={`fixed top-[72px] left-0 right-0 z-40 border-b border-qbl-border lg:hidden transition-all duration-200 ${
          open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        style={{
          background: "rgba(10,14,23,0.97)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
        }}
      >
        <div className="px-6 py-5 flex flex-col gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className={`text-[0.95rem] py-2.5 transition-colors ${
                pathname === l.href
                  ? "text-text-primary font-medium"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {l.label}
            </Link>
          ))}
          <div className="flex gap-3 mt-4 pt-4 border-t border-qbl-border">
            {isSignedIn ? (
              <Link
                href="/dashboard/picks"
                onClick={() => setOpen(false)}
                className="flex-1 text-center font-display font-semibold text-sm py-2.5 rounded-[8px] bg-accent text-bg-primary"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <SignInButton mode="redirect">
                  <button
                    onClick={() => setOpen(false)}
                    className="flex-1 text-center font-display font-semibold text-sm py-2.5 rounded-[8px] border border-qbl-border text-text-secondary cursor-pointer"
                  >
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton mode="redirect">
                  <button
                    onClick={() => setOpen(false)}
                    className="flex-1 text-center font-display font-semibold text-sm py-2.5 rounded-[8px] bg-accent text-bg-primary cursor-pointer"
                  >
                    Get Started
                  </button>
                </SignUpButton>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
