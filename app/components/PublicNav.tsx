"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { useAuth, useUser, useClerk, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";

const ADMIN_EMAIL = process.env.NEXT_PUBLIC_ADMIN_EMAIL ?? "";

const publicLinks = [
  { label: "Home", href: "/" },
  { label: "Performance", href: "/performance" },
  { label: "How to Use", href: "/how-to-use" },
  { label: "Pricing", href: "/pricing" },
  { label: "FAQ", href: "/faq" },
  { label: "Rules", href: "/rules" },
];

const dashLinks = [
  { label: "Home", href: "/" },
  { label: "Current Picks", href: "/dashboard/picks" },
  { label: "Performance", href: "/dashboard/performance" },
  { label: "How to Use", href: "/how-to-use" },
  { label: "Education", href: "/dashboard/education" },
  { label: "Pricing", href: "/pricing" },
];

const moreLinks = [
  { label: "FAQ", href: "/dashboard/faq" },
  { label: "Rules", href: "/rules" },
];

export default function PublicNav() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [moreExpanded, setMoreExpanded] = useState(false);
  const { isSignedIn } = useAuth();
  const { user } = useUser();
  const { signOut } = useClerk();
  const moreRef = useRef<HTMLDivElement>(null);

  const isAdmin = user?.primaryEmailAddress?.emailAddress === ADMIN_EMAIL && ADMIN_EMAIL !== "";
  const isMoreActive = moreLinks.some((l) => pathname === l.href || pathname.startsWith(l.href + "/"));

  useEffect(() => {
    if (!moreOpen) return;
    function handleOutside(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [moreOpen]);

  useEffect(() => {
    setMobileOpen(false);
    setMoreOpen(false);
    setMoreExpanded(false);
  }, [pathname]);

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
        <div className="max-w-[1440px] mx-auto px-6 flex items-center h-[72px] gap-4">
          {/* Logo */}
          <Link
            href={isSignedIn ? "/dashboard/picks" : "/"}
            className="font-display text-xl font-bold tracking-[0.08em] text-text-primary shrink-0"
          >
            QUANT<span className="text-accent">BET</span>LABS
          </Link>

          {/* Desktop nav links */}
          <div className="hidden lg:flex flex-1 items-center justify-center gap-1">
            {isSignedIn ? (
              <>
                {dashLinks.map((l) => {
                  const active = pathname === l.href || pathname.startsWith(l.href + "/");
                  return (
                    <Link
                      key={l.href}
                      href={l.href}
                      className={`font-display font-semibold text-sm px-4 py-2 rounded-[8px] transition-all duration-200 ${
                        active
                          ? "bg-[rgba(0,212,170,0.12)] text-accent"
                          : "text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.04)]"
                      }`}
                    >
                      {l.label}
                    </Link>
                  );
                })}

                {/* More dropdown */}
                <div className="relative" ref={moreRef}>
                  <button
                    onClick={() => setMoreOpen((v) => !v)}
                    className={`font-display font-semibold text-sm px-4 py-2 rounded-[8px] transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
                      isMoreActive || moreOpen
                        ? "bg-[rgba(0,212,170,0.12)] text-accent"
                        : "text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.04)]"
                    }`}
                  >
                    More
                    <svg
                      className={`w-3 h-3 transition-transform duration-200 ${moreOpen ? "rotate-180" : ""}`}
                      fill="none"
                      viewBox="0 0 12 12"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2 4l4 4 4-4" />
                    </svg>
                  </button>
                  {moreOpen && (
                    <div
                      className="absolute top-full mt-2 right-0 min-w-[140px] rounded-[10px] border border-qbl-border py-1 z-50"
                      style={{ background: "rgba(10,14,23,0.98)", backdropFilter: "blur(16px)" }}
                    >
                      {moreLinks.map((l) => (
                        <Link
                          key={l.href}
                          href={l.href}
                          onClick={() => setMoreOpen(false)}
                          className={`block px-4 py-2.5 font-display font-semibold text-sm transition-colors ${
                            pathname === l.href ? "text-accent" : "text-text-secondary hover:text-text-primary"
                          }`}
                        >
                          {l.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

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
              </>
            ) : (
              publicLinks.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`text-[0.9rem] px-3 py-2 transition-colors duration-200 ${
                    pathname === l.href
                      ? "text-text-primary"
                      : "text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {l.label}
                </Link>
              ))
            )}
          </div>

          {/* Desktop right */}
          <div className="hidden lg:flex items-center gap-3 shrink-0">
            {isSignedIn ? (
              <>
                <Link
                  href="/dashboard/account"
                  className={`font-display font-semibold text-sm px-4 py-2 rounded-[8px] transition-all duration-200 ${
                    pathname === "/dashboard/account" || pathname.startsWith("/dashboard/account/")
                      ? "bg-[rgba(0,212,170,0.12)] text-accent"
                      : "text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.04)]"
                  }`}
                >
                  Account
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

          {/* Mobile right — UserButton + hamburger */}
          <div className="lg:hidden flex items-center gap-3 ml-auto">
            {isSignedIn && <UserButton />}
          </div>
          <button
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
            className="lg:hidden flex flex-col justify-center gap-[5px] p-2 text-text-secondary"
          >
            <span className={`block w-6 h-0.5 bg-current origin-center transition-all duration-200 ${mobileOpen ? "rotate-45 translate-y-[7px]" : ""}`} />
            <span className={`block w-6 h-0.5 bg-current transition-all duration-200 ${mobileOpen ? "opacity-0 scale-x-0" : ""}`} />
            <span className={`block w-6 h-0.5 bg-current origin-center transition-all duration-200 ${mobileOpen ? "-rotate-45 -translate-y-[7px]" : ""}`} />
          </button>
        </div>
      </nav>

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
          {isSignedIn ? (
            <>
              {dashLinks.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  onClick={() => setMobileOpen(false)}
                  className={`font-display font-semibold text-sm py-3 px-3 rounded-[8px] transition-colors ${
                    pathname === l.href
                      ? "bg-[rgba(0,212,170,0.08)] text-accent"
                      : "text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {l.label}
                </Link>
              ))}

              {/* More — expands inline on mobile */}
              <button
                onClick={() => setMoreExpanded((v) => !v)}
                className={`font-display font-semibold text-sm py-3 px-3 rounded-[8px] transition-colors flex items-center justify-between cursor-pointer w-full ${
                  isMoreActive ? "text-accent" : "text-text-secondary hover:text-text-primary"
                }`}
              >
                More
                <svg
                  className={`w-3.5 h-3.5 transition-transform duration-200 ${moreExpanded ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 12 12"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2 4l4 4 4-4" />
                </svg>
              </button>
              {moreExpanded && (
                <div className="pl-4 flex flex-col gap-0.5">
                  {moreLinks.map((l) => (
                    <Link
                      key={l.href}
                      href={l.href}
                      onClick={() => setMobileOpen(false)}
                      className={`font-display font-semibold text-sm py-2.5 px-3 rounded-[8px] transition-colors ${
                        pathname === l.href ? "text-accent" : "text-text-muted hover:text-text-secondary"
                      }`}
                    >
                      {l.label}
                    </Link>
                  ))}
                </div>
              )}

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

              <Link
                href="/dashboard/account"
                onClick={() => setMobileOpen(false)}
                className={`font-display font-semibold text-sm py-3 px-3 rounded-[8px] transition-colors ${
                  pathname === "/dashboard/account"
                    ? "bg-[rgba(0,212,170,0.08)] text-accent"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                Account
              </Link>

              <div className="pt-3 mt-1 border-t border-qbl-border">
                <button
                  onClick={() => { setMobileOpen(false); signOut({ redirectUrl: "/" }); }}
                  className="font-display font-semibold text-sm py-2.5 text-text-muted hover:text-text-secondary transition-colors cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            </>
          ) : (
            <>
              {publicLinks.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  onClick={() => setMobileOpen(false)}
                  className={`text-[0.95rem] py-2.5 px-2 transition-colors ${
                    pathname === l.href
                      ? "text-text-primary font-medium"
                      : "text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {l.label}
                </Link>
              ))}
              <div className="flex gap-3 mt-4 pt-4 border-t border-qbl-border">
                <SignInButton mode="redirect">
                  <button
                    onClick={() => setMobileOpen(false)}
                    className="flex-1 text-center font-display font-semibold text-sm py-2.5 rounded-[8px] border border-qbl-border text-text-secondary cursor-pointer"
                  >
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton mode="redirect">
                  <button
                    onClick={() => setMobileOpen(false)}
                    className="flex-1 text-center font-display font-semibold text-sm py-2.5 rounded-[8px] bg-accent text-bg-primary cursor-pointer"
                  >
                    Get Started
                  </button>
                </SignUpButton>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
