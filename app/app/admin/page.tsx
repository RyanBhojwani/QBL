import { currentUser } from "@clerk/nextjs/server";
import { createClient } from "@supabase/supabase-js";
import { redirect } from "next/navigation";
import AdminPanel from "./AdminPanel";

function serviceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  );
}

export default async function AdminPage() {
  const user = await currentUser();
  const email = user?.primaryEmailAddress?.emailAddress;

  if (!user || email !== process.env.ADMIN_EMAIL) {
    redirect("/");
  }

  const { data } = await serviceClient()
    .from("worker_config")
    .select("key, value");

  const config: Record<string, string> = {};
  for (const row of data ?? []) config[row.key] = row.value;

  return (
    <div
      className="min-h-screen bg-bg-primary pt-[72px]"
      style={{ background: "var(--color-bg-primary, #060912)" }}
    >
      <div className="max-w-[1440px] mx-auto px-6 py-8">
        <AdminPanel initialConfig={config} />
      </div>
    </div>
  );
}
