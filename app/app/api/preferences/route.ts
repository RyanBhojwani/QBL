import { auth } from "@clerk/nextjs/server";
import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

function serviceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  );
}

export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({}, { status: 401 });

  const { data } = await serviceClient()
    .from("user_preferences")
    .select("sports, books, min_stars, max_stars")
    .eq("clerk_user_id", userId)
    .maybeSingle();

  return NextResponse.json(data ?? {});
}

export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({}, { status: 401 });

  const body = await request.json();

  await serviceClient().from("user_preferences").upsert({
    clerk_user_id: userId,
    sports:    Array.isArray(body.sports)    ? body.sports    : [],
    books:     Array.isArray(body.books)     ? body.books     : [],
    min_stars: typeof body.min_stars === "number" ? Math.min(Math.max(Math.round(body.min_stars), 1), 5) : 1,
    max_stars: typeof body.max_stars === "number" ? Math.min(Math.max(Math.round(body.max_stars), 1), 5) : 5,
    updated_at: new Date().toISOString(),
  });

  return NextResponse.json({ ok: true });
}
