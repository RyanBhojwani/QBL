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
    redirect("/dashboard/picks");
  }

  const { data } = await serviceClient()
    .from("worker_config")
    .select("key, value");

  const config: Record<string, string> = {};
  for (const row of data ?? []) config[row.key] = row.value;

  return <AdminPanel initialConfig={config} />;
}
