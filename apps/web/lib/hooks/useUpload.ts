/**
 * Custom hook for file uploads with progress tracking
 * Handles video, audio, and CSV file uploads
 */
import { useAuth } from "@clerk/nextjs";
import { useState, useCallback } from "react";
import { apiClient, API_ENDPOINTS } from "@/lib/api/client";

export type UploadCategory = "video" | "audio" | "csv";

export interface UploadProgress {
  progress: number;
  isUploading: boolean;
}

export interface UploadResult {
  success: boolean;
  message?: string;
  filename?: string;
  error?: string;
}

export function useUpload() {
  const { getToken } = useAuth();
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Upload a file with progress tracking
   */
  const uploadFile = useCallback(
    async (
      file: File,
      category: UploadCategory,
      folderName?: string
    ): Promise<UploadResult> => {
      setIsUploading(true);
      setUploadProgress(0);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        // Determine endpoint based on category
        let endpoint: string;
        switch (category) {
          case "video":
            endpoint = API_ENDPOINTS.FILES.UPLOAD_VIDEO;
            break;
          case "audio":
            endpoint = API_ENDPOINTS.FILES.UPLOAD_AUDIO;
            break;
          case "csv":
            endpoint = API_ENDPOINTS.FILES.UPLOAD_CSV;
            break;
          default:
            throw new Error(`Invalid upload category: ${category}`);
        }

        // Create FormData
        const formData = new FormData();
        formData.append("file", file);
        if (folderName) {
          formData.append("subfolder", folderName);  // Backend expects 'subfolder'
        }

        // Upload with progress tracking
        const response = await apiClient.upload<UploadResult>(
          endpoint,
          formData,
          token,
          (progress) => {
            setUploadProgress(Math.round(progress));
          }
        );

        return {
          success: true,
          ...response,
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Upload failed";
        setError(message);
        return {
          success: false,
          error: message,
        };
      } finally {
        setIsUploading(false);
        setUploadProgress(0);
      }
    },
    [getToken]
  );

  /**
   * Upload multiple files sequentially
   */
  const uploadMultipleFiles = useCallback(
    async (
      files: File[],
      category: UploadCategory,
      folderName?: string
    ): Promise<UploadResult[]> => {
      const results: UploadResult[] = [];

      for (const file of files) {
        const result = await uploadFile(file, category, folderName);
        results.push(result);

        // Stop on first error if needed
        if (!result.success) {
          break;
        }
      }

      return results;
    },
    [uploadFile]
  );

  /**
   * Reset upload state
   */
  const resetUpload = useCallback(() => {
    setUploadProgress(0);
    setIsUploading(false);
    setError(null);
  }, []);

  return {
    uploadProgress,
    isUploading,
    error,
    uploadFile,
    uploadMultipleFiles,
    resetUpload,
  };
}
