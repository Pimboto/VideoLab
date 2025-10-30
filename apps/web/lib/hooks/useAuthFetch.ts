/**
 * Custom hook for authenticated API calls
 * Automatically includes Clerk JWT token in requests
 */
import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";

export function useAuthFetch() {
  const { getToken } = useAuth();

  const authFetch = useCallback(
    async (url: string, options: RequestInit = {}) => {
      const token = await getToken();

      if (!token) {
        throw new Error("Not authenticated");
      }

      const headers = new Headers(options.headers);

      headers.set("Authorization", `Bearer ${token}`);

      return fetch(url, {
        ...options,
        headers,
      });
    },
    [getToken],
  );

  return authFetch;
}
