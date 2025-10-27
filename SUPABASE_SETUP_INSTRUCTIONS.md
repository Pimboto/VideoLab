# 🗄️ Supabase Setup Instructions

## Step 1: Execute Database Schema

1. Go to your Supabase Dashboard: https://app.supabase.com/project/ywiusirueusmvwiytxnz
2. Navigate to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy the entire contents of `supabase-schema.sql`
5. Paste into the SQL Editor
6. Click **Run** (or press `Ctrl+Enter`)

This will create:
- ✅ 4 tables: `users`, `files`, `projects`, `jobs`
- ✅ Indexes for performance
- ✅ Row Level Security (RLS) policies
- ✅ Storage policies
- ✅ Helper functions and triggers

## Step 2: Create Storage Buckets

Go to **Storage** in Supabase Dashboard and create the following buckets:

### Bucket 1: `videos`
- **Name**: `videos`
- **Public**: ❌ No (Private)
- **File size limit**: 500 MB (optional)
- **Allowed MIME types**: `video/*` (optional)

### Bucket 2: `audios`
- **Name**: `audios`
- **Public**: ❌ No (Private)
- **File size limit**: 50 MB (optional)
- **Allowed MIME types**: `audio/*` (optional)

### Bucket 3: `csv`
- **Name**: `csv`
- **Public**: ❌ No (Private)
- **File size limit**: 5 MB (optional)
- **Allowed MIME types**: `text/csv, text/plain` (optional)

### Bucket 4: `output`
- **Name**: `output`
- **Public**: ❌ No (Private)
- **File size limit**: 500 MB (optional)
- **Allowed MIME types**: `video/*` (optional)

## Step 3: Verify Setup

Run this query in SQL Editor to verify tables were created:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('users', 'files', 'projects', 'jobs');
```

You should see 4 rows.

## Step 4: Verify Storage Buckets

Go to **Storage** and verify you see all 4 buckets:
- ✅ videos
- ✅ audios
- ✅ csv
- ✅ output

## Step 5: Test RLS Policies

The RLS policies are automatically enabled. They will:
- Allow users to only access their own data
- Isolate files per user using Clerk user ID
- Enforce multi-tenancy at the database level

## Troubleshooting

### Error: "relation already exists"
If you see this error, it means the tables already exist. You can either:
1. Drop the existing tables first (⚠️ WARNING: This deletes all data!)
2. Skip to the next step

### Error: "storage bucket already exists"
If buckets already exist, you can skip bucket creation and just verify they exist.

### Error: "policy already exists"
This is safe to ignore. The policies are already in place.

## Next Steps

After completing the database setup:
1. ✅ Install frontend dependencies (Clerk + Supabase)
2. ✅ Install backend dependencies (Clerk + Supabase)
3. ✅ Configure authentication
4. ✅ Test the integration

---

## 📝 Notes

- **RLS is enabled**: All tables have Row Level Security enabled
- **Multi-tenancy**: Users can only access their own data
- **Clerk Integration**: Uses `auth.jwt() ->> 'sub'` to get Clerk user ID
- **Storage Security**: Files are organized by user ID: `{user_id}/{category}/{filename}`
- **Automatic Timestamps**: `created_at` and `updated_at` are automatically managed
