import { supabase } from "./client";

export type StorageBucket = "videos" | "audios" | "csv" | "output";

/**
 * Upload a file to Supabase Storage
 *
 * @param bucket - The storage bucket to upload to
 * @param userId - The user ID (used for folder organization)
 * @param file - The file to upload
 * @param subfolder - Optional subfolder within the user's folder
 * @returns The path of the uploaded file
 */
export async function uploadFile(
  bucket: StorageBucket,
  userId: string,
  file: File,
  subfolder?: string,
): Promise<{ path: string; url: string }> {
  // Construct the file path: {userId}/{subfolder?}/{filename}
  const path = subfolder
    ? `${userId}/${subfolder}/${file.name}`
    : `${userId}/${file.name}`;

  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file, {
      cacheControl: "3600",
      upsert: false, // Don't overwrite existing files
    });

  if (error) {
    throw new Error(`Failed to upload file: ${error.message}`);
  }

  // Get the public URL for the uploaded file
  const {
    data: { publicUrl },
  } = supabase.storage.from(bucket).getPublicUrl(path);

  return {
    path: data.path,
    url: publicUrl,
  };
}

/**
 * Download a file from Supabase Storage
 *
 * @param bucket - The storage bucket to download from
 * @param path - The file path in storage
 * @returns The file blob
 */
export async function downloadFile(
  bucket: StorageBucket,
  path: string,
): Promise<Blob> {
  const { data, error } = await supabase.storage.from(bucket).download(path);

  if (error) {
    throw new Error(`Failed to download file: ${error.message}`);
  }

  return data;
}

/**
 * Delete a file from Supabase Storage
 *
 * @param bucket - The storage bucket
 * @param path - The file path to delete
 */
export async function deleteFile(
  bucket: StorageBucket,
  path: string,
): Promise<void> {
  const { error } = await supabase.storage.from(bucket).remove([path]);

  if (error) {
    throw new Error(`Failed to delete file: ${error.message}`);
  }
}

/**
 * List files in a Supabase Storage bucket
 *
 * @param bucket - The storage bucket
 * @param path - The folder path to list files from (default: root)
 * @returns Array of file metadata
 */
export async function listFiles(
  bucket: StorageBucket,
  path: string = "",
): Promise<any[]> {
  const { data, error } = await supabase.storage.from(bucket).list(path, {
    limit: 100,
    offset: 0,
    sortBy: { column: "created_at", order: "desc" },
  });

  if (error) {
    throw new Error(`Failed to list files: ${error.message}`);
  }

  return data || [];
}

/**
 * Get a signed URL for a private file (valid for 1 hour)
 *
 * @param bucket - The storage bucket
 * @param path - The file path
 * @param expiresIn - Expiration time in seconds (default: 3600 = 1 hour)
 * @returns The signed URL
 */
export async function getSignedUrl(
  bucket: StorageBucket,
  path: string,
  expiresIn: number = 3600,
): Promise<string> {
  const { data, error } = await supabase.storage
    .from(bucket)
    .createSignedUrl(path, expiresIn);

  if (error) {
    throw new Error(`Failed to create signed URL: ${error.message}`);
  }

  return data.signedUrl;
}

/**
 * Get the public URL for a file
 * Note: This only works if the bucket is public or RLS allows access
 *
 * @param bucket - The storage bucket
 * @param path - The file path
 * @returns The public URL
 */
export function getPublicUrl(bucket: StorageBucket, path: string): string {
  const {
    data: { publicUrl },
  } = supabase.storage.from(bucket).getPublicUrl(path);

  return publicUrl;
}

/**
 * Upload file with progress tracking
 *
 * @param bucket - The storage bucket to upload to
 * @param userId - The user ID
 * @param file - The file to upload
 * @param onProgress - Progress callback (0-100)
 * @param subfolder - Optional subfolder
 * @returns The path of the uploaded file
 */
export async function uploadFileWithProgress(
  bucket: StorageBucket,
  userId: string,
  file: File,
  onProgress?: (progress: number) => void,
  subfolder?: string,
): Promise<{ path: string; url: string }> {
  const path = subfolder
    ? `${userId}/${subfolder}/${file.name}`
    : `${userId}/${file.name}`;

  // Create a FormData object for chunked upload
  const formData = new FormData();

  formData.append("file", file);

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

    xhr.addEventListener("load", async () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        // Get the public URL
        const {
          data: { publicUrl },
        } = supabase.storage.from(bucket).getPublicUrl(path);

        resolve({ path, url: publicUrl });
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Upload failed"));
    });

    // Use Supabase storage upload
    supabase.storage
      .from(bucket)
      .upload(path, file, {
        cacheControl: "3600",
        upsert: false,
      })
      .then(({ data, error }) => {
        if (error) {
          reject(error);
        } else if (data) {
          const {
            data: { publicUrl },
          } = supabase.storage.from(bucket).getPublicUrl(path);

          resolve({ path: data.path, url: publicUrl });
        }
      })
      .catch(reject);
  });
}
