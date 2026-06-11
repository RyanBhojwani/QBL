import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const email = typeof body.email === "string" ? body.email.toLowerCase().trim() : "";

    if (!email || !email.includes("@") || !email.includes(".")) {
      return NextResponse.json({ error: "Invalid email address" }, { status: 400 });
    }

    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    );

    const { error } = await supabase.from("waitlist").insert({ email });

    if (error) {
      if (error.code === "23505") {
        // Already on the list — treat as success so we don't leak whether an email exists
        return NextResponse.json({ ok: true });
      }
      console.error("waitlist insert error:", error);
      return NextResponse.json({ error: "Server error" }, { status: 500 });
    }

    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("waitlist route error:", e);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
