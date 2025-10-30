/**
 * Custom hook for file operations
 * Handles listing, deleting, and moving files with AWS S3 storage
 */
import { useAuth } from "@clerk/nextjs";
import { useState, useCallback } from "react";

import { apiClient, API_ENDPOINTS } from "@/lib/api/client";

export interface FileItem {
  filename: string;
  filepath: string;
  size: number;
  size_bytes?: number;
  modified: string;
  file_type: string;
  metadata?: Record<string, any>;
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
    async (
      category: FileCategory,
      subfolder?: string | null,
    ): Promise<FileListResponse | null> => {
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

        // Add subfolder query parameter if provided
        if (subfolder) {
          endpoint = `${endpoint}?subfolder=${encodeURIComponent(subfolder)}`;
        }

        const response = await apiClient.get<FileListResponse>(endpoint, token);

        return response;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to list files";

        setError(message);

        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken],
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
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}${API_ENDPOINTS.FILES.DELETE}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ filepath }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({
            detail: `HTTP ${response.status}: ${response.statusText}`,
          }));

          throw new Error(
            errorData.detail || `Delete failed: ${response.statusText}`,
          );
        }

        return true;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to delete file";

        setError(message);

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken],
  );

  /**
   * Delete multiple files in a single request (bulk delete)
   * Best practice: Use this instead of looping deleteFile for better performance
   */
  const bulkDeleteFiles = useCallback(
    async (
      filepaths: string[],
    ): Promise<{ deleted: number; failed: number; success: boolean }> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();

        if (!token) {
          throw new Error("Not authenticated");
        }

        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(
          `${apiUrl}${API_ENDPOINTS.FILES.BULK_DELETE}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ filepaths }),
          },
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({
            detail: `HTTP ${response.status}: ${response.statusText}`,
          }));

          throw new Error(
            errorData.detail || `Bulk delete failed: ${response.statusText}`,
          );
        }

        const data = await response.json();

        return {
          deleted: data.deleted_count,
          failed: data.failed_count,
          success: data.deleted_count > 0,
        };
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to delete files";

        setError(message);

        return { deleted: 0, failed: filepaths.length, success: false };
      } finally {
        setIsLoading(false);
      }
    },
    [getToken],
  );

  /**
   * Move multiple files to a folder in a single request (bulk move)
   * Best practice: Use this instead of looping moveFile for better performance
   */
  const bulkMoveFiles = useCallback(
    async (
      filepaths: string[],
      destinationFolder: string,
    ): Promise<{ moved: number; failed: number; success: boolean }> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();

        if (!token) {
          throw new Error("Not authenticated");
        }

        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(
          `${apiUrl}${API_ENDPOINTS.FILES.BULK_MOVE}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              filepaths,
              destination_folder: destinationFolder,
            }),
          },
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({
            detail: `HTTP ${response.status}: ${response.statusText}`,
          }));

          throw new Error(
            errorData.detail || `Bulk move failed: ${response.statusText}`,
          );
        }

        const data = await response.json();

        return {
          moved: data.moved_count,
          failed: data.failed_count,
          success: data.moved_count > 0,
        };
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to move files";

        setError(message);

        return { moved: 0, failed: filepaths.length, success: false };
      } finally {
        setIsLoading(false);
      }
    },
    [getToken],
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
          token,
        );

        return true;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to move file";

        setError(message);

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken],
  );

  /**
   * Get CloudFront stream URL for video file from AWS S3
   * Must be called before rendering video tag
   */
  const getVideoStreamUrl = useCallback(
    async (filepath: string): Promise<string | null> => {
      try {
        const token = await getToken();

        if (!token) return null;

        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const endpoint = `/api/video-processor/files/stream-url/video?filepath=${encodeURIComponent(filepath)}`;

        const response = await fetch(`${apiUrl}${endpoint}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) return null;

        const data = await response.json();

        return data.url;
      } catch {
        // Silent fail for stream URL

        return null;
      }
    },
    [getToken],
  );

  /**
   * Get CloudFront stream URL for audio file from AWS S3
   * Must be called before rendering audio tag
   */
  const getAudioStreamUrl = useCallback(
    async (filepath: string): Promise<string | null> => {
      try {
        const token = await getToken();

        if (!token) return null;

        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const endpoint = `/api/video-processor/files/stream-url/audio?filepath=${encodeURIComponent(filepath)}`;

        const response = await fetch(`${apiUrl}${endpoint}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) return null;

        const data = await response.json();

        return data.url;
      } catch {
        // Silent fail for stream URL

        return null;
      }
    },
    [getToken],
  );

  /**
   * Get CSV preview URL (with full API URL)
   */
  const getCsvPreviewUrl = useCallback((filepath: string): string => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    return `${apiUrl}${API_ENDPOINTS.FILES.PREVIEW_CSV(filepath)}`;
  }, []);

  /**
   * Rename a file (display name only)
   */
  const renameFile = useCallback(
    async (filepath: string, newName: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();

        if (!token) {
          throw new Error("Not authenticated");
        }

        await apiClient.request(
          API_ENDPOINTS.FILES.RENAME,
          {
            method: "PATCH",
            body: JSON.stringify({ filepath, new_name: newName }),
          },
          token,
        );

        return true;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to rename file";

        setError(message);

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken],
  );

  return {
    isLoading,
    error,
    listFiles,
    deleteFile,
    bulkDeleteFiles,
    bulkMoveFiles,
    renameFile,
    moveFile,
    getVideoStreamUrl,
    getAudioStreamUrl,
    getCsvPreviewUrl,
  };
}
