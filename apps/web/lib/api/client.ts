/**
 * API Client for making authenticated requests to the FastAPI backend
 *
 * This client automatically includes the Clerk authentication token
 * in all requests to the backend API.
 */

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Base API client class
 */
class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  /**
   * Make an authenticated request to the API
   *
   * @param endpoint - The API endpoint (e.g., '/api/video-processor/files/videos')
   * @param options - Fetch options
   * @param token - Optional Clerk auth token (if not provided, request will be unauthenticated)
   * @returns The response data
   */
  async request<T = any>(
    endpoint: string,
    options: RequestInit = {},
    token?: string | null
  ): Promise<T> {
    const headers: HeadersInit = {
      ...options.headers,
    };

    // Add Content-Type header if body is present and not FormData
    if (options.body && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    // Add authentication token if provided
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle non-OK responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));

        throw new Error(errorData.detail || `Request failed: ${response.statusText}`);
      }

      // Parse JSON response
      const data = await response.json();
      return data as T;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("An unknown error occurred");
    }
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, token?: string | null): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" }, token);
  }

  /**
   * POST request
   */
  async post<T = any>(
    endpoint: string,
    data?: any,
    token?: string | null
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "POST",
        body: data ? JSON.stringify(data) : undefined,
      },
      token
    );
  }

  /**
   * PUT request
   */
  async put<T = any>(
    endpoint: string,
    data?: any,
    token?: string | null
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "PUT",
        body: data ? JSON.stringify(data) : undefined,
      },
      token
    );
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string, token?: string | null): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" }, token);
  }

  /**
   * Upload file with FormData
   *
   * @param endpoint - The API endpoint
   * @param formData - FormData object containing the file(s)
   * @param token - Clerk auth token
   * @param onProgress - Optional progress callback (0-100)
   * @returns The response data
   */
  async upload<T = any>(
    endpoint: string,
    formData: FormData,
    token: string,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const progress = (e.loaded / e.total) * 100;
            onProgress(progress);
          }
        });
      }

      // Handle completion
      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve(data);
          } catch {
            resolve(xhr.responseText as any);
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.detail || `Upload failed: ${xhr.statusText}`));
          } catch {
            reject(new Error(`Upload failed: ${xhr.statusText}`));
          }
        }
      });

      // Handle errors
      xhr.addEventListener("error", () => {
        reject(new Error("Network error during upload"));
      });

      xhr.addEventListener("abort", () => {
        reject(new Error("Upload aborted"));
      });

      // Open connection and set auth header
      xhr.open("POST", `${this.baseURL}${endpoint}`);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      // Send the request
      xhr.send(formData);
    });
  }
}

// Export singleton instance
export const apiClient = new APIClient(API_URL);

/**
 * API endpoints constants
 * Centralized endpoint definitions for easy maintenance
 */
export const API_ENDPOINTS = {
  // Files
  FILES: {
    LIST_VIDEOS: "/api/video-processor/files/videos",
    LIST_AUDIOS: "/api/video-processor/files/audios",
    LIST_CSV: "/api/video-processor/files/csv",
    LIST_OUTPUTS: "/api/video-processor/files/outputs",
    UPLOAD_VIDEO: "/api/video-processor/files/upload/video",
    UPLOAD_AUDIO: "/api/video-processor/files/upload/audio",
    UPLOAD_CSV: "/api/video-processor/files/upload/csv",
    DELETE: "/api/video-processor/files/delete",
    MOVE: "/api/video-processor/files/move",
    STREAM_VIDEO: (filename: string) =>
      `/api/video-processor/files/stream/video?filename=${encodeURIComponent(filename)}`,
    STREAM_AUDIO: (filename: string) =>
      `/api/video-processor/files/stream/audio?filename=${encodeURIComponent(filename)}`,
    PREVIEW_CSV: (filepath: string) =>
      `/api/video-processor/files/preview/csv?filepath=${encodeURIComponent(filepath)}`,
  },
  // Folders
  FOLDERS: {
    LIST: (category: string) =>
      `/api/video-processor/folders/${category}`,
    CREATE: "/api/video-processor/folders/create",
  },
  // Processing
  PROCESSING: {
    LIST_VIDEOS: "/api/video-processor/processing/list-videos",
    LIST_AUDIOS: "/api/video-processor/processing/list-audios",
    DEFAULT_CONFIG: "/api/video-processor/processing/default-config",
    PROCESS_SINGLE: "/api/video-processor/processing/process-single",
    PROCESS_BATCH: "/api/video-processor/processing/process-batch",
    STATUS: (jobId: string) =>
      `/api/video-processor/processing/status/${jobId}`,
    JOBS: "/api/video-processor/processing/jobs",
    DELETE_JOB: (jobId: string) =>
      `/api/video-processor/processing/jobs/${jobId}`,
  },
  // Health
  HEALTH: "/health",
} as const;

/**
 * Type-safe API response types
 */
export interface APIResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface FileListResponse {
  files: Array<{
    filename: string;
    size_mb: number;
    size_bytes: number;
    created_at: string;
    mime_type?: string;
  }>;
  count: number;
}

export interface JobStatusResponse {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  message: string;
  output_files?: string[];
  error?: string;
}

export interface ProcessingConfigResponse {
  config: {
    num_videos: number;
    num_audios: number;
    output_folder: string;
    unique_mode: boolean;
    unique_amount: number;
    mode: string;
    text_position: string;
    preset_name: string;
  };
}
