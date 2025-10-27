/**
 * Custom hook for folder operations
 * Handles listing and creating folders in different categories
 */
import { useAuth } from "@clerk/nextjs";
import { useState, useCallback } from "react";
import { apiClient, API_ENDPOINTS } from "@/lib/api/client";

export interface Folder {
  name: string;
  path: string;
  file_count: number;
  total_size_mb: number;
}

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

  return {
    isLoading,
    error,
    listFolders,
    createFolder,
  };
}
