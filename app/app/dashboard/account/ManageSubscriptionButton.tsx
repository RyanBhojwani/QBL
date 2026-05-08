"use client";

import { useState } from "react";

export default function ManageSubscriptionButton() {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/portal", { method: "POST" });
      const { url, error } = await res.json();
      if (error) throw new Error(error);
      window.location.href = url;
    } catch (err) {
      console.error("Portal failed:", err);
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
    >
      {loading ? "Loading…" : "Manage Subscription"}
    </button>
  );
}
