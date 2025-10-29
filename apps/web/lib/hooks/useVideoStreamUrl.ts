/**
 * Custom hook for lazy loading video stream URLs
 *
 * Optimized for performance:
 * - Only loads URLs for VISIBLE videos (not all at once)
 * - Caches CloudFront URLs for 1 hour (they have long expiration)
 * - Uses React Query for automatic caching and deduplication
 * - Loads URLs in parallel (not sequentially)
 *
 * Usage:
 * ```tsx
 * const { data: urls, isLoading } = useVideoStreamUrls(visibleVideos);
 * const videoUrl = urls[video.filepath];
 * ```
 */

import { useQueries, useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";

/**
 * Get CloudFront URL for a single video
 */
export function useVideoStreamUrl(filepath: string | null) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["video-stream-url", filepath],
    queryFn: async () => {
      if (!filepath) return null;

      const token = await getToken();
      if (!token) return null;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const endpoint = `/api/video-processor/files/stream-url/video?filepath=${encodeURIComponent(filepath)}`;

      const response = await fetch(`${apiUrl}${endpoint}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) return null;

      const data = await response.json();
      return data.url as string;
    },
    enabled: !!filepath, // Only run if filepath exists
    staleTime: 60 * 60 * 1000, // 1 hour (CloudFront URLs are valid for 1 hour)
    gcTime: 2 * 60 * 60 * 1000, // 2 hours (keep in cache longer)
    retry: 1,
  });
}

/**
 * Get CloudFront URLs for multiple videos in parallel
 *
 * This is optimized for loading ONLY visible videos, not all videos.
 *
 * @param filepaths - Array of filepaths to load URLs for (typically first 20)
 * @returns Object with URLs mapped by filepath
 */
export function useVideoStreamUrls(filepaths: string[]) {
  const { getToken } = useAuth();

  // Load all URLs in parallel using useQueries
  const queries = useQueries({
    queries: filepaths.map((filepath) => ({
      queryKey: ["video-stream-url", filepath],
      queryFn: async () => {
        const token = await getToken();
        if (!token) return null;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const endpoint = `/api/video-processor/files/stream-url/video?filepath=${encodeURIComponent(filepath)}`;

        const response = await fetch(`${apiUrl}${endpoint}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) return null;

        const data = await response.json();
        return data.url as string;
      },
      staleTime: 60 * 60 * 1000, // 1 hour
      gcTime: 2 * 60 * 60 * 1000, // 2 hours
      retry: 1,
    })),
  });

  // Convert results to a Map for easy lookup
  const urls: Record<string, string | null> = {};
  queries.forEach((query, index) => {
    urls[filepaths[index]] = query.data || null;
  });

  // Check if any query is loading
  const isLoading = queries.some((query) => query.isLoading);
  const isError = queries.some((query) => query.isError);

  return {
    urls,
    isLoading,
    isError,
  };
}

/**
 * Get CloudFront URL for audio file
 */
export function useAudioStreamUrl(filepath: string | null) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["audio-stream-url", filepath],
    queryFn: async () => {
      if (!filepath) return null;

      const token = await getToken();
      if (!token) return null;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const endpoint = `/api/video-processor/files/stream-url/audio?filepath=${encodeURIComponent(filepath)}`;

      const response = await fetch(`${apiUrl}${endpoint}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) return null;

      const data = await response.json();
      return data.url as string;
    },
    enabled: !!filepath,
    staleTime: 60 * 60 * 1000, // 1 hour
    gcTime: 2 * 60 * 60 * 1000, // 2 hours
    retry: 1,
  });
}

/**
 * Get CloudFront URLs for multiple audios in parallel
 *
 * @param filepaths - Array of filepaths to load URLs for (typically first 20)
 * @returns Object with URLs mapped by filepath
 */
export function useAudioStreamUrls(filepaths: string[]) {
  const { getToken } = useAuth();

  // Load all URLs in parallel using useQueries
  const queries = useQueries({
    queries: filepaths.map((filepath) => ({
      queryKey: ["audio-stream-url", filepath],
      queryFn: async () => {
        const token = await getToken();
        if (!token) return null;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const endpoint = `/api/video-processor/files/stream-url/audio?filepath=${encodeURIComponent(filepath)}`;

        const response = await fetch(`${apiUrl}${endpoint}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) return null;

        const data = await response.json();
        return data.url as string;
      },
      staleTime: 60 * 60 * 1000, // 1 hour
      gcTime: 2 * 60 * 60 * 1000, // 2 hours
      retry: 1,
    })),
  });

  // Convert results to a Map for easy lookup
  const urls: Record<string, string | null> = {};
  queries.forEach((query, index) => {
    urls[filepaths[index]] = query.data || null;
  });

  const isLoading = queries.some((query) => query.isLoading);
  const isError = queries.some((query) => query.isError);

  return {
    urls,
    isLoading,
    isError,
  };
}

/**
 * Helper to prefetch video URL in background
 * Useful for preloading next page of videos
 */
export function usePrefetchVideoUrl() {
  const { getToken } = useAuth();

  return useCallback(
    async (filepath: string) => {
      const token = await getToken();
      if (!token) return;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const endpoint = `/api/video-processor/files/stream-url/video?filepath=${encodeURIComponent(filepath)}`;

      // Prefetch in background (won't trigger loading state)
      await fetch(`${apiUrl}${endpoint}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    },
    [getToken]
  );
}
