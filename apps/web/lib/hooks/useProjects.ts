/**
 * Custom hook for project operations using TanStack Query
 * Handles fetching, caching, and managing project data
 */
import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, API_ENDPOINTS, type Project, type ProjectUrls } from "@/lib/api/client";

// Query keys for cache management
export const projectKeys = {
  all: ["projects"] as const,
  lists: () => [...projectKeys.all, "list"] as const,
  list: (filters?: { includeDeleted?: boolean }) =>
    [...projectKeys.lists(), filters] as const,
  details: () => [...projectKeys.all, "detail"] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
  urls: (id: string) => [...projectKeys.detail(id), "urls"] as const,
};

/**
 * Fetch all projects for the current user
 */
export function useProjects(options?: {
  includeDeleted?: boolean;
  limit?: number;
}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: projectKeys.list(options),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      let endpoint = API_ENDPOINTS.PROJECTS.LIST;
      const params = new URLSearchParams();

      if (options?.limit) params.append("limit", String(options.limit));
      if (options?.includeDeleted) params.append("include_deleted", "true");

      if (params.toString()) endpoint += `?${params.toString()}`;

      return apiClient.get<Project[]>(endpoint, token);
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
  });
}

/**
 * Fetch a single project by ID
 */
export function useProject(projectId: string | null) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: projectKeys.detail(projectId || ""),
    queryFn: async () => {
      if (!projectId) return null;

      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return apiClient.get<Project>(
        API_ENDPOINTS.PROJECTS.GET(projectId),
        token
      );
    },
    enabled: !!projectId,
    staleTime: 30 * 1000,
  });
}

/**
 * Get CloudFront signed URLs for project assets
 * These URLs are fresh and valid for 1 hour
 */
export function useProjectUrls(projectId: string | null) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: projectKeys.urls(projectId || ""),
    queryFn: async () => {
      if (!projectId) return null;

      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return apiClient.get<ProjectUrls>(
        API_ENDPOINTS.PROJECTS.GET_URLS(projectId),
        token
      );
    },
    enabled: !!projectId,
    staleTime: 50 * 60 * 1000, // 50 minutes (URLs valid for 1 hour)
    gcTime: 60 * 60 * 1000, // 1 hour
  });
}

/**
 * Delete a project
 */
export function useDeleteProject() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      projectId: string;
      hardDelete?: boolean;
    }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      let endpoint = API_ENDPOINTS.PROJECTS.DELETE(params.projectId);
      if (params.hardDelete) endpoint += "?hard_delete=true";

      return apiClient.delete(endpoint, token);
    },
    onSuccess: () => {
      // Invalidate projects list to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
}

/**
 * Download a project ZIP file
 */
export function useDownloadProject() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async (params: {
      projectId: string;
      projectName: string;
    }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      // Get fresh signed URL
      const urls = await apiClient.get<ProjectUrls>(
        API_ENDPOINTS.PROJECTS.GET_URLS(params.projectId),
        token
      );

      if (!urls.zip_url) {
        throw new Error("ZIP file not available");
      }

      // Trigger download
      const link = document.createElement("a");
      link.href = urls.zip_url;
      link.download = `${params.projectName}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
  });
}
