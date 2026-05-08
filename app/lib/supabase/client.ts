import { createClient as _createClient } from "@supabase/supabase-js";

// Singleton — one client per browser session so Realtime uses a single WebSocket.
let _client: ReturnType<typeof _createClient> | null = null;

export function createClient() {
  if (!_client) {
    _client = _createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
  }
  return _client;
}
