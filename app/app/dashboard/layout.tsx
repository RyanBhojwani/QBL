import PublicNav from "@/components/PublicNav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <PublicNav />
      <main className="flex-1 pt-[72px]">
        <div className="max-w-[1440px] mx-auto px-6 py-8">{children}</div>
      </main>
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
