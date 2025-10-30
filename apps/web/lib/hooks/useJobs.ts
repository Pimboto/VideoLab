/**
 * Custom hook for job polling and status tracking
 * Handles processing job status checks and automatic polling
 */
import { useAuth } from "@clerk/nextjs";
import { useState, useCallback, useEffect, useRef } from "react";

import { apiClient, API_ENDPOINTS, JobStatusResponse } from "@/lib/api/client";

export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Job extends JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  output_files?: string[];
  error?: string;
}

export interface JobsListResponse {
  jobs: Job[];
  count: number;
}

export function useJobs() {
  const { getToken } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Fetch all jobs
   */
  const fetchJobs = useCallback(async (): Promise<Job[] | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = await getToken();

      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await apiClient.get<JobsListResponse>(
        API_ENDPOINTS.PROCESSING.JOBS,
        token,
      );

      setJobs(response.jobs || []);

      return response.jobs || [];
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch jobs";

      setError(message);

      return null;
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  /**
   * Get status of a specific job
   */
  const getJobStatus = useCallback(
    async (jobId: string): Promise<Job | null> => {
      setError(null);

      try {
        const token = await getToken();

        if (!token) {
          throw new Error("Not authenticated");
        }

        const response = await apiClient.get<Job>(
          API_ENDPOINTS.PROCESSING.STATUS(jobId),
          token,
        );

        return response;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to get job status";

        setError(message);

        return null;
      }
    },
    [getToken],
  );

  /**
   * Delete a job
   */
  const deleteJob = useCallback(
    async (jobId: string): Promise<boolean> => {
      setError(null);

      try {
        const token = await getToken();

        if (!token) {
          throw new Error("Not authenticated");
        }

        await apiClient.delete(
          API_ENDPOINTS.PROCESSING.DELETE_JOB(jobId),
          token,
        );

        // Update local state
        setJobs((prevJobs) => prevJobs.filter((job) => job.job_id !== jobId));

        return true;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to delete job";

        setError(message);

        return false;
      }
    },
    [getToken],
  );

  /**
   * Start polling for job updates
   * Polls every 2 seconds until all jobs are completed or failed
   */
  const startPolling = useCallback(
    (interval: number = 2000) => {
      // Clear existing interval if any
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }

      // Initial fetch
      fetchJobs();

      // Set up polling
      pollingIntervalRef.current = setInterval(async () => {
        const currentJobs = await fetchJobs();

        // Stop polling if all jobs are completed or failed
        if (currentJobs) {
          const hasActiveJobs = currentJobs.some(
            (job) => job.status === "pending" || job.status === "processing",
          );

          if (!hasActiveJobs && pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      }, interval);
    },
    [fetchJobs],
  );

  /**
   * Stop polling for job updates
   */
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  /**
   * Poll a specific job until completion
   */
  const pollJobUntilComplete = useCallback(
    async (
      jobId: string,
      onUpdate?: (job: Job) => void,
      interval: number = 2000,
    ): Promise<Job | null> => {
      return new Promise((resolve) => {
        const pollInterval = setInterval(async () => {
          const job = await getJobStatus(jobId);

          if (job) {
            onUpdate?.(job);

            if (job.status === "completed" || job.status === "failed") {
              clearInterval(pollInterval);
              resolve(job);
            }
          }
        }, interval);
      });
    },
    [getJobStatus],
  );

  /**
   * Poll job status (alias for getJobStatus for compatibility)
   */
  const pollJobStatus = useCallback(
    async (jobId: string): Promise<Job | null> => {
      return getJobStatus(jobId);
    },
    [getJobStatus],
  );

  /**
   * Cleanup polling on unmount
   */
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    jobs,
    isLoading,
    error,
    fetchJobs,
    getJobStatus,
    pollJobStatus, // Add pollJobStatus for compatibility
    deleteJob,
    startPolling,
    stopPolling,
    pollJobUntilComplete,
  };
}
