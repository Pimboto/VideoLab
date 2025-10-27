/**
 * Database types for Supabase
 *
 * These types should ideally be auto-generated using:
 * npx supabase gen types typescript --project-id ywiusirueusmvwiytxnz > lib/supabase/types.ts
 *
 * For now, we define them manually based on our schema
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string;
          clerk_id: string;
          email: string;
          username: string | null;
          first_name: string | null;
          last_name: string | null;
          avatar_url: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          clerk_id: string;
          email: string;
          username?: string | null;
          first_name?: string | null;
          last_name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          clerk_id?: string;
          email?: string;
          username?: string | null;
          first_name?: string | null;
          last_name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      files: {
        Row: {
          id: string;
          user_id: string;
          filename: string;
          filepath: string;
          file_type: "video" | "audio" | "csv" | "output";
          size_bytes: number;
          mime_type: string | null;
          subfolder: string | null;
          metadata: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          filename: string;
          filepath: string;
          file_type: "video" | "audio" | "csv" | "output";
          size_bytes: number;
          mime_type?: string | null;
          subfolder?: string | null;
          metadata?: Json | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          filename?: string;
          filepath?: string;
          file_type?: "video" | "audio" | "csv" | "output";
          size_bytes?: number;
          mime_type?: string | null;
          subfolder?: string | null;
          metadata?: Json | null;
          created_at?: string;
        };
      };
      projects: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          description: string | null;
          output_folder: string | null;
          video_count: number;
          total_size_bytes: number;
          created_at: string;
          expires_at: string | null;
          deleted_at: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          name: string;
          description?: string | null;
          output_folder?: string | null;
          video_count?: number;
          total_size_bytes?: number;
          created_at?: string;
          expires_at?: string | null;
          deleted_at?: string | null;
        };
        Update: {
          id?: string;
          user_id?: string;
          name?: string;
          description?: string | null;
          output_folder?: string | null;
          video_count?: number;
          total_size_bytes?: number;
          created_at?: string;
          expires_at?: string | null;
          deleted_at?: string | null;
        };
      };
      jobs: {
        Row: {
          id: string;
          user_id: string;
          project_id: string | null;
          job_type: "single" | "batch" | "ai-generation";
          status: "pending" | "processing" | "completed" | "failed";
          progress: number;
          message: string | null;
          config: Json | null;
          input_files: Json | null;
          output_files: Json | null;
          error: string | null;
          created_at: string;
          started_at: string | null;
          completed_at: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          project_id?: string | null;
          job_type: "single" | "batch" | "ai-generation";
          status?: "pending" | "processing" | "completed" | "failed";
          progress?: number;
          message?: string | null;
          config?: Json | null;
          input_files?: Json | null;
          output_files?: Json | null;
          error?: string | null;
          created_at?: string;
          started_at?: string | null;
          completed_at?: string | null;
        };
        Update: {
          id?: string;
          user_id?: string;
          project_id?: string | null;
          job_type?: "single" | "batch" | "ai-generation";
          status?: "pending" | "processing" | "completed" | "failed";
          progress?: number;
          message?: string | null;
          config?: Json | null;
          input_files?: Json | null;
          output_files?: Json | null;
          error?: string | null;
          created_at?: string;
          started_at?: string | null;
          completed_at?: string | null;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
  };
}

// Helper types for easier use
export type User = Database["public"]["Tables"]["users"]["Row"];
export type UserInsert = Database["public"]["Tables"]["users"]["Insert"];
export type UserUpdate = Database["public"]["Tables"]["users"]["Update"];

export type FileRecord = Database["public"]["Tables"]["files"]["Row"];
export type FileInsert = Database["public"]["Tables"]["files"]["Insert"];
export type FileUpdate = Database["public"]["Tables"]["files"]["Update"];

export type Project = Database["public"]["Tables"]["projects"]["Row"];
export type ProjectInsert = Database["public"]["Tables"]["projects"]["Insert"];
export type ProjectUpdate = Database["public"]["Tables"]["projects"]["Update"];

export type Job = Database["public"]["Tables"]["jobs"]["Row"];
export type JobInsert = Database["public"]["Tables"]["jobs"]["Insert"];
export type JobUpdate = Database["public"]["Tables"]["jobs"]["Update"];

export type FileType = "video" | "audio" | "csv" | "output";
export type JobType = "single" | "batch" | "ai-generation";
export type JobStatus = "pending" | "processing" | "completed" | "failed";
