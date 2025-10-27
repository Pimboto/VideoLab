import { createBrowserClient } from "@supabase/ssr";
import type { Database } from "./types";

/**
 * Create a Supabase client for use in the browser
 * This client will automatically handle authentication and cookies
 */
export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing Supabase environment variables. Please check your .env.local file."
    );
  }

  return createBrowserClient<Database>(supabaseUrl, supabaseAnonKey);
}

// Export a singleton instance for use throughout the app
export const supabase = createClient();
