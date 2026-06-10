"use client";

import { usePathname } from "next/navigation";
import PublicFooter from "./PublicFooter";

export default function DashboardFooter() {
  const pathname = usePathname();
  if (pathname === "/dashboard/picks") return null;
  return <PublicFooter />;
}
