"use client";

/**
 * React Query Provider
 *
 * Provides global caching, state management, and data synchronization
 * for all file operations with AWS S3.
 *
 * Configuration optimized for:
 * - Long-lived CloudFront URLs (1 hour cache)
 * - Thumbnail URLs (very long cache since they don't change)
 * - Optimistic UI updates for mutations
 * - Automatic background refetching disabled to prevent unnecessary API calls
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // Create query client instance (one per component tree)
  // This ensures server/client don't share state
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Cache Configuration
            staleTime: 5 * 60 * 1000, // 5 minutes - data is considered fresh
            gcTime: 10 * 60 * 1000, // 10 minutes - garbage collection time (formerly cacheTime)

            // Refetch Configuration
            refetchOnWindowFocus: false, // Don't refetch on tab focus (saves API calls)
            refetchOnMount: true, // Refetch on component mount if data is stale
            refetchOnReconnect: true, // Refetch when internet reconnects

            // Retry Configuration
            retry: 1, // Retry failed queries once
            retryDelay: (attemptIndex) =>
              Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff

            // Network Mode
            networkMode: "online", // Only run queries when online
          },
          mutations: {
            // Mutation Configuration
            retry: 0, // Don't retry mutations automatically (user can retry manually)
            networkMode: "online",
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* DevTools only shown in development */}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools
          buttonPosition="bottom-left"
          initialIsOpen={false}
          position="bottom"
        />
      )}
    </QueryClientProvider>
  );
}
