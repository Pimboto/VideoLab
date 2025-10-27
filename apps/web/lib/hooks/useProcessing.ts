/**
 * Custom hook for video processing operations
 * Handles single and batch processing with configuration
 */
import { useAuth } from "@clerk/nextjs";
import { useState, useCallback } from "react";
import { apiClient, API_ENDPOINTS, ProcessingConfigResponse } from "@/lib/api/client";

export interface ProcessingVideo {
  filename: string;
  size_mb: number;
  size_bytes: number;
  created_at: string;
  mime_type?: string;
}

export interface ProcessingAudio {
  filename: string;
  size_mb: number;
  size_bytes: number;
  created_at: string;
  mime_type?: string;
}

export interface ProcessingConfig {
  num_videos: number;
  num_audios: number;
  output_folder: string;
  unique_mode: boolean;
  unique_amount: number;
  mode: string;
  text_position: string;
  preset_name: string;
}

export interface ProcessingRequest {
  video_files: string[];
  audio_files: string[];
  csv_file: string;
  output_folder: string;
  num_videos: number;
  num_audios: number;
  unique_mode: boolean;
  unique_amount: number;
  mode: string;
  text_position: string;
  preset_name: string;
}

export interface ProcessingResponse {
  job_id: string;
  message: string;
  status: string;
}

export function useProcessing() {
  const { getToken } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * List available videos for processing
   */
  const listVideos = useCallback(async (): Promise<ProcessingVideo[] | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await apiClient.get<{ videos: ProcessingVideo[] }>(
        API_ENDPOINTS.PROCESSING.LIST_VIDEOS,
        token
      );
      return response.videos || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to list videos";
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  /**
   * List available audios for processing
   */
  const listAudios = useCallback(async (): Promise<ProcessingAudio[] | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await apiClient.get<{ audios: ProcessingAudio[] }>(
        API_ENDPOINTS.PROCESSING.LIST_AUDIOS,
        token
      );
      return response.audios || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to list audios";
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  /**
   * Get default processing configuration
   */
  const getDefaultConfig = useCallback(async (): Promise<ProcessingConfig | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await apiClient.get<ProcessingConfigResponse>(
        API_ENDPOINTS.PROCESSING.DEFAULT_CONFIG,
        token
      );
      return response.config;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to get default config";
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  /**
   * Process a single video
   */
  const processSingle = useCallback(
    async (request: ProcessingRequest): Promise<ProcessingResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        const response = await apiClient.post<ProcessingResponse>(
          API_ENDPOINTS.PROCESSING.PROCESS_SINGLE,
          request,
          token
        );
        return response;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to start processing";
        setError(message);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [getToken]
  );

  /**
   * Process batch of videos
   */
  const processBatch = useCallback(
    async (request: ProcessingRequest): Promise<ProcessingResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }

        const response = await apiClient.post<ProcessingResponse>(
          API_ENDPOINTS.PROCESSING.PROCESS_BATCH,
          request,
          token
        );
        return response;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to start batch processing";
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
    listVideos,
    listAudios,
    getDefaultConfig,
    processSingle,
    processBatch,
  };
}
