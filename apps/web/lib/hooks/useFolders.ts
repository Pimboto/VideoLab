/**
 * Custom hook for folder operations
 * Handles listing and creating folders in different categories
 */
import { useAuth } from "@clerk/nextjs";
import { useState, useCallback } from "react";
import { apiClient, API_ENDPOINTS } from "@/lib/api/client";
import type { Folder } from "@/lib/types";

export interface FolderListResponse {
  folders: Folder[];
  total_count: number;
}

export interface FolderCreateRequest {
  parent_category: string;
  folder_name: string;
}

export interface FolderCreateResponse {
  message: string;
  folder_path: string;
}

export interface FolderDeleteRequest {
  parent_category: string;
  folder_name: string;
}

export interface FolderDeleteResponse {
  message: string;
  folder_name: string;
  files_deleted: number;
}

export type FolderCategory = "videos" | "audios" | "csv" | "output";

export function useFolders() {
  const { getToken } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * List folders in a category
   */
  const listFolders = useCallback(
    async (category: FolderCategory): Promise<FolderListResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        const response = await apiClient.get<FolderListResponse>(
          API_ENDPOINTS.FOLDERS.LIST(category),
          token
        );
        return response;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to list folders";
        setError(message);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken]
  );

  /**
   * Create a new folder
   */
  const createFolder = useCallback(
    async (
      category: FolderCategory,
      folderName: string
    ): Promise<FolderCreateResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        const response = await apiClient.post<FolderCreateResponse>(
          API_ENDPOINTS.FOLDERS.CREATE,
          {
            parent_category: category,
            folder_name: folderName,
          },
          token
        );
        return response;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to create folder";
        setError(message);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken]
  );

  /**
   * Delete a folder and all its files
   */
  const deleteFolder = useCallback(
    async (
      category: FolderCategory,
      folderName: string
    ): Promise<FolderDeleteResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        // Use DELETE method with body
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}${API_ENDPOINTS.FOLDERS.DELETE}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({
            parent_category: category,
            folder_name: folderName,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({
            detail: `HTTP ${response.status}: ${response.statusText}`,
          }));
          throw new Error(errorData.detail || `Delete failed: ${response.statusText}`);
        }

        const data = await response.json();
        return data as FolderDeleteResponse;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to delete folder";
        setError(message);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken]
  );

  return {
    isLoading,
    error,
    listFolders,
    createFolder,
    deleteFolder,
  };
}
