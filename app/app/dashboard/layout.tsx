import PublicNav from "@/components/PublicNav";
import PublicFooter from "@/components/PublicFooter";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <PublicNav />
      <main className="flex-1 pt-[72px]">
        <div className="max-w-[1440px] mx-auto px-6 py-8">{children}</div>
      </main>
      <PublicFooter />
    </div>
  );
}
