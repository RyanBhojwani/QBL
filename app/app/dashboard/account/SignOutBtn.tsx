"use client";

import { useClerk } from "@clerk/nextjs";

export default function SignOutBtn() {
  const { signOut } = useClerk();
  return (
    <button
      onClick={() => signOut({ redirectUrl: "/" })}
      className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] border border-qbl-border text-text-secondary hover:border-[rgba(239,68,68,0.4)] hover:text-red-400 transition-all inline-block cursor-pointer"
    >
      Sign Out
    </button>
  );
}
