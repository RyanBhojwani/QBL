"use client";

import { SignUpButton } from "@clerk/nextjs";

export default function GetStartedButton() {
  return (
    <SignUpButton mode="redirect">
      <button className="inline-flex items-center gap-2.5 font-display font-semibold text-[1.15rem] px-10 py-[18px] rounded-[12px] bg-transparent text-accent border-2 border-accent transition-all duration-250 hover:bg-[rgba(0,212,170,0.1)] hover:-translate-y-[2px] hover:shadow-[0_4px_20px_rgba(0,212,170,0.15)] max-sm:w-full max-sm:max-w-[340px] max-sm:justify-center cursor-pointer">
        Get Early Access
      </button>
    </SignUpButton>
  );
}
