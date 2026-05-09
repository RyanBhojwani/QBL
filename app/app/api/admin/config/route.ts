import { auth, clerkClient } from "@clerk/nextjs/server";
import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

function serviceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  );
}

async function isAdmin(userId: string): Promise<boolean> {
  const client = await clerkClient();
  const user = await client.users.getUser(userId);
  const email = user.primaryEmailAddress?.emailAddress;
  return email === process.env.ADMIN_EMAIL;
}

export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({}, { status: 401 });
  if (!(await isAdmin(userId))) return NextResponse.json({}, { status: 403 });

  const { data } = await serviceClient()
    .from("worker_config")
    .select("key, value");

  const config: Record<string, string> = {};
  for (const row of data ?? []) config[row.key] = row.value;

  return NextResponse.json(config);
}

export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({}, { status: 401 });
  if (!(await isAdmin(userId))) return NextResponse.json({}, { status: 403 });

  const body: Record<string, string> = await request.json();
  const now = new Date().toISOString();

  const rows = Object.entries(body).map(([key, value]) => ({
    key,
    value: String(value),
    updated_at: now,
  }));

  await serviceClient()
    .from("worker_config")
    .upsert(rows, { onConflict: "key" });

  return NextResponse.json({ ok: true });
}
