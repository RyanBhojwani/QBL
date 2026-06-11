"use client";

import { useState } from "react";

export default function GetStartedButton() {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  function handleClose() {
    setOpen(false);
    setStatus("idle");
    setEmail("");
    setErrorMsg("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMsg("");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error ?? "Something went wrong");
      }
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Something went wrong");
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2.5 font-display font-semibold text-[1.15rem] px-10 py-[18px] rounded-[12px] bg-transparent text-accent border-2 border-accent transition-all duration-250 hover:bg-[rgba(0,212,170,0.1)] hover:-translate-y-[2px] hover:shadow-[0_4px_20px_rgba(0,212,170,0.15)] max-sm:w-full max-sm:max-w-[340px] max-sm:justify-center cursor-pointer"
      >
        Join the Waitlist
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
          onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
        >
          <div className="relative bg-bg-surface border border-qbl-border rounded-[16px] p-8 w-full max-w-[420px] shadow-[0_24px_80px_rgba(0,0,0,0.5)]">
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 text-text-muted hover:text-text-primary transition-colors text-2xl leading-none w-8 h-8 flex items-center justify-center"
            >
              ×
            </button>

            {status === "success" ? (
              <div className="text-center py-4">
                <div className="text-[2.5rem] text-accent mb-4">✓</div>
                <h2 className="font-display text-xl font-semibold text-text-primary mb-2">
                  You&apos;re on the list!
                </h2>
                <p className="text-text-secondary text-sm leading-[1.7]">
                  We&apos;ll reach out when spots open up.
                </p>
                <button
                  onClick={handleClose}
                  className="mt-6 font-display font-semibold text-sm text-accent hover:text-accent-hover transition-colors"
                >
                  Close
                </button>
              </div>
            ) : (
              <>
                <h2 className="font-display text-xl font-semibold text-text-primary mb-2">
                  Join the Waitlist
                </h2>
                <p className="text-text-secondary text-sm leading-[1.7] mb-6">
                  Get early access when we open new spots. No spam, ever.
                </p>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="w-full bg-bg-primary border border-qbl-border rounded-[8px] px-4 py-3 text-text-primary text-sm focus:outline-none focus:border-accent transition-colors placeholder:text-text-muted"
                  />
                  {status === "error" && (
                    <p className="text-red-400 text-xs">{errorMsg}</p>
                  )}
                  <button
                    type="submit"
                    disabled={status === "loading"}
                    className="w-full font-display font-semibold text-sm px-6 py-3 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {status === "loading" ? "Joining…" : "Join the Waitlist"}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
