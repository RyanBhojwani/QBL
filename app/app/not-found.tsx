import Link from "next/link";
import PublicLayout from "@/components/PublicLayout";

export default function NotFound() {
  return (
    <PublicLayout>
      <section className="min-h-[calc(100vh-72px)] flex items-center justify-center px-6">
        <div className="text-center max-w-[480px]">
          <span className="block font-display text-[clamp(5rem,15vw,9rem)] font-bold text-accent opacity-15 leading-none tracking-[-0.04em] select-none">
            404
          </span>
          <h1 className="font-display text-[clamp(1.4rem,3vw,2rem)] font-semibold text-text-primary mt-2 mb-3">
            Page not found
          </h1>
          <p className="text-text-secondary text-[1rem] leading-[1.7] mb-8">
            The page you&apos;re looking for doesn&apos;t exist or may have been moved.
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            <Link
              href="/"
              className="font-display font-semibold text-sm px-6 py-3 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px]"
            >
              Back to Home
            </Link>
            <Link
              href="/dashboard/picks"
              className="font-display font-semibold text-sm px-6 py-3 rounded-[8px] bg-transparent text-accent border-2 border-accent hover:bg-[rgba(0,212,170,0.08)] transition-all hover:-translate-y-[1px]"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
