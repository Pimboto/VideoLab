-- =====================================================
-- VideoLab - Supabase Database Schema
-- =====================================================
-- This script creates all necessary tables, indexes,
-- RLS policies, and storage buckets for the VideoLab MVP
--
-- Execute this in Supabase SQL Editor
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLES
-- =====================================================

-- Users table (synced with Clerk)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clerk_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Files table (metadata for all uploaded files)
CREATE TABLE IF NOT EXISTS files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL, -- Supabase Storage path (e.g., 'user_id/videos/file.mp4')
  file_type TEXT NOT NULL, -- 'video', 'audio', 'csv', 'output'
  size_bytes BIGINT NOT NULL,
  mime_type TEXT,
  subfolder TEXT, -- optional subfolder within file_type category
  metadata JSONB, -- extra metadata (duration, resolution, etc)
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects table (output folders/batches)
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  output_folder TEXT, -- Supabase Storage folder path
  video_count INT DEFAULT 0,
  total_size_bytes BIGINT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ, -- auto-cleanup after 24h (optional)
  deleted_at TIMESTAMPTZ
);

-- Jobs table (processing jobs history)
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  job_type TEXT NOT NULL, -- 'single', 'batch', 'ai-generation'
  status TEXT NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
  progress FLOAT DEFAULT 0, -- 0-100
  message TEXT,
  config JSONB, -- processing configuration
  input_files JSONB, -- array of file IDs
  output_files JSONB, -- array of output file paths
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- =====================================================
-- INDEXES for better query performance
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_users_clerk_id ON users(clerk_id);
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_subfolder ON files(subfolder);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- RLS POLICIES
-- =====================================================

-- Users: Can only view/update their own data
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT
  USING (auth.jwt() ->> 'sub' = clerk_id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE
  USING (auth.jwt() ->> 'sub' = clerk_id);

-- Files: Users can only access their own files
CREATE POLICY "Users can view own files" ON files
  FOR SELECT
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can insert own files" ON files
  FOR INSERT
  WITH CHECK (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can update own files" ON files
  FOR UPDATE
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can delete own files" ON files
  FOR DELETE
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

-- Projects: Users can only access their own projects
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can insert own projects" ON projects
  FOR INSERT
  WITH CHECK (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

-- Jobs: Users can only access their own jobs
CREATE POLICY "Users can view own jobs" ON jobs
  FOR SELECT
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can insert own jobs" ON jobs
  FOR INSERT
  WITH CHECK (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can update own jobs" ON jobs
  FOR UPDATE
  USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

-- =====================================================
-- STORAGE BUCKETS
-- =====================================================
-- NOTE: These must be created via Supabase Dashboard or Storage API
-- You cannot create buckets via SQL directly, but you can configure policies

-- Create storage buckets (run these in Supabase Dashboard > Storage):
-- 1. Bucket: 'videos' (private)
-- 2. Bucket: 'audios' (private)
-- 3. Bucket: 'csv' (private)
-- 4. Bucket: 'output' (private)

-- =====================================================
-- STORAGE POLICIES (run after creating buckets)
-- =====================================================

-- Videos bucket policies
CREATE POLICY "Users can upload own videos" ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'videos' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can view own videos" ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'videos' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can delete own videos" ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'videos' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

-- Audios bucket policies
CREATE POLICY "Users can upload own audios" ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'audios' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can view own audios" ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'audios' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can delete own audios" ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'audios' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

-- CSV bucket policies
CREATE POLICY "Users can upload own csv" ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'csv' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can view own csv" ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'csv' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can delete own csv" ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'csv' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

-- Output bucket policies
CREATE POLICY "Users can upload own outputs" ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'output' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can view own outputs" ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'output' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can delete own outputs" ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'output' AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

-- =====================================================
-- FUNCTIONS (Helper functions)
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on users table
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- COMPLETED
-- =====================================================
--
-- Next steps:
-- 1. Execute this script in Supabase SQL Editor
-- 2. Create storage buckets in Supabase Dashboard:
--    - Go to Storage > Create new bucket
--    - Create: videos, audios, csv, output
--    - Set all to Private
-- 3. Execute the storage policies above after creating buckets
--
-- =====================================================
