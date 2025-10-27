/**
 * Custom hook for file operations
 * Handles listing, deleting, and moving files with Supabase storage
 */
import { useAuth } from "@clerk/nextjs";
import { useState, useCallback } from "react";
import { apiClient, API_ENDPOINTS } from "@/lib/api/client";

export interface FileItem {
  filename: string;
  size_mb: number;
  size_bytes: number;
  created_at: string;
  mime_type?: string;
}

export interface FileListResponse {
  files: FileItem[];
  count: number;
}

export type FileCategory = "videos" | "audios" | "csv" | "outputs";

export function useFiles() {
  const { getToken } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * List files by category
   */
  const listFiles = useCallback(
    async (category: FileCategory): Promise<FileListResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        let endpoint: string;
        switch (category) {
          case "videos":
            endpoint = API_ENDPOINTS.FILES.LIST_VIDEOS;
            break;
          case "audios":
            endpoint = API_ENDPOINTS.FILES.LIST_AUDIOS;
            break;
          case "csv":
            endpoint = API_ENDPOINTS.FILES.LIST_CSV;
            break;
          case "outputs":
            endpoint = API_ENDPOINTS.FILES.LIST_OUTPUTS;
            break;
          default:
            throw new Error(`Invalid category: ${category}`);
        }

        const response = await apiClient.get<FileListResponse>(endpoint, token);
        return response;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to list files";
        setError(message);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken]
  );

  /**
   * Delete a file
   */
  const deleteFile = useCallback(
    async (filepath: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        // Send filepath in body, not as query parameter
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}${API_ENDPOINTS.FILES.DELETE}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({ filepath }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({
            detail: `HTTP ${response.status}: ${response.statusText}`,
          }));
          throw new Error(errorData.detail || `Delete failed: ${response.statusText}`);
        }

        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to delete file";
        setError(message);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken]
  );

  /**
   * Move a file to a different location
   */
  const moveFile = useCallback(
    async (sourcePath: string, destinationPath: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        await apiClient.post(
          API_ENDPOINTS.FILES.MOVE,
          {
            source: sourcePath,
            destination: destinationPath,
          },
          token
        );
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to move file";
        setError(message);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken]
  );

  /**
   * Get stream URL for video file
   */
  const getVideoStreamUrl = useCallback((filename: string): string => {
    return API_ENDPOINTS.FILES.STREAM_VIDEO(filename);
  }, []);

  /**
   * Get stream URL for audio file
   */
  const getAudioStreamUrl = useCallback((filename: string): string => {
    return API_ENDPOINTS.FILES.STREAM_AUDIO(filename);
  }, []);

  /**
   * Get CSV preview URL (with full API URL)
   */
  const getCsvPreviewUrl = useCallback((filepath: string): string => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return `${apiUrl}${API_ENDPOINTS.FILES.PREVIEW_CSV(filepath)}`;
  }, []);

  return {
    isLoading,
    error,
    listFiles,
    deleteFile,
    moveFile,
    getVideoStreamUrl,
    getAudioStreamUrl,
    getCsvPreviewUrl,
  };
}
