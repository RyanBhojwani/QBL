"use client";

import { useState } from "react";

export type FaqItem = { q: string; a: string };

export default function FaqAccordion({ items }: { items: FaqItem[] }) {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div
          key={i}
          className="border border-qbl-border rounded-[10px] overflow-hidden bg-bg-surface"
        >
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-[rgba(255,255,255,0.02)] transition-colors"
            aria-expanded={open === i}
          >
            <span className="font-display font-semibold text-sm text-text-primary pr-6">
              {item.q}
            </span>
            <span
              className={`text-accent text-xl font-bold transition-transform duration-200 shrink-0 leading-none ${
                open === i ? "rotate-45" : ""
              }`}
            >
              +
            </span>
          </button>
          {open === i && (
            <div className="border-t border-qbl-border px-6 pb-5 pt-4 text-text-secondary text-sm leading-[1.75]">
              {item.a}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
