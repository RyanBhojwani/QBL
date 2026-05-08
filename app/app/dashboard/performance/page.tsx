import { fetchModelResults } from "@/lib/performance";
import PerformanceDashboard from "@/components/PerformanceDashboard";

export const revalidate = 3600;

export default async function DashboardPerformancePage() {
  const results = await fetchModelResults();

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Performance</h1>
        <p className="text-text-secondary text-sm">
          Verified win/loss record across all tracked picks. Updates daily after settlement.
        </p>
      </div>
      <PerformanceDashboard results={results} />
    </div>
  );
}
