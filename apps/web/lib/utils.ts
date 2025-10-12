// Shared utility functions

export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
};

export const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  // Use toLocaleDateString with consistent format to avoid hydration mismatch
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric"
  });
};

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
