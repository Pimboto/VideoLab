# Frontend Refactoring Status

## ✅ Completed

### 1. Backend Authentication Fix
- **File**: `apps/api/core/security.py:99`
- **Change**: Added `"verify_iat": False` to JWT decode options
- **Reason**: Fixes "Invalid token: The token is not yet valid (iat)" error caused by clock skew

### 2. Custom Hooks Created
All hooks follow React best practices with proper error handling:

#### `useFiles` - File Operations
**Location**: `apps/web/lib/hooks/useFiles.ts`
```typescript
const { listFiles, deleteFile, moveFile, getVideoStreamUrl, getAudioStreamUrl, getCsvPreviewUrl, isLoading, error } = useFiles();
```
- ✅ List files by category (videos, audios, csv, outputs)
- ✅ Delete files
- ✅ Move files
- ✅ Get stream URLs for media files
- ✅ Automatic auth token injection
- ✅ Error state management

#### `useFolders` - Folder Operations
**Location**: `apps/web/lib/hooks/useFolders.ts`
```typescript
const { listFolders, createFolder, isLoading, error } = useFolders();
```
- ✅ List folders by category
- ✅ Create new folders
- ✅ Type-safe category selection

#### `useUpload` - File Uploads with Progress
**Location**: `apps/web/lib/hooks/useUpload.ts`
```typescript
const { uploadFile, uploadMultipleFiles, uploadProgress, isUploading, error, resetUpload } = useUpload();
```
- ✅ Upload files with progress tracking (0-100%)
- ✅ Support for videos, audios, and CSV files
- ✅ Multiple file uploads
- ✅ XMLHttpRequest-based for accurate progress

#### `useJobs` - Job Polling
**Location**: `apps/web/lib/hooks/useJobs.ts`
```typescript
const { jobs, fetchJobs, getJobStatus, deleteJob, startPolling, stopPolling, pollJobUntilComplete, isLoading, error } = useJobs();
```
- ✅ Fetch all jobs
- ✅ Get specific job status
- ✅ Delete jobs
- ✅ Automatic polling with cleanup
- ✅ Poll single job until completion

#### `useProcessing` - Video Processing
**Location**: `apps/web/lib/hooks/useProcessing.ts`
```typescript
const { listVideos, listAudios, getDefaultConfig, processSingle, processBatch, isLoading, error } = useProcessing();
```
- ✅ List available videos and audios
- ✅ Get default processing configuration
- ✅ Process single video
- ✅ Process batch of videos

#### `useToast` - User Notifications
**Location**: `apps/web/lib/hooks/useToast.ts`
```typescript
const toast = useToast();
toast.success("Operation completed!");
toast.error("Something went wrong");
toast.warning("Please review this");
toast.info("Information message");
```
- ✅ Success, error, warning, info toasts
- ✅ Integrated with HeroUI toast component
- ✅ Automatic color mapping

### 3. Toast Provider Setup
**File**: `apps/web/app/providers.tsx`
- Added `ToastProvider` wrapper for app-wide toast notifications

### 4. Central Hooks Export
**File**: `apps/web/lib/hooks/index.ts`
- All hooks exported from single location for easy imports

### 5. Pages Refactored
#### ✅ Texts Page (`app/dashboard/texts/page.tsx`)
**Changes**:
- Replaced direct API calls with `useFiles` hook
- Replaced manual uploads with `useUpload` hook
- Added toast notifications for all operations
- Added upload progress indicator
- Proper error handling throughout
- Removed hardcoded API_URL

**Before**:
```typescript
const res = await authFetch(`${API_URL}/api/video-processor/files/csv`);
const data = await res.json();
```

**After**:
```typescript
const { listFiles, deleteFile } = useFiles();
const response = await listFiles("csv");
if (response) {
  setCsvFiles(response.files);
} else {
  toast.error("Failed to load CSV files");
}
```

## 🔄 In Progress

### Pages Still Using Direct API Calls
These pages need refactoring to use the new hooks:

#### 1. Videos Page (`app/dashboard/videos/page.tsx`)
**Needs**:
- Replace `authFetch` with `useFiles` and `useFolders`
- Add `useUpload` for file uploads with progress
- Add `useToast` for user feedback
- Remove `API_URL` hardcoding

#### 2. Audios Page (`app/dashboard/audios/page.tsx`)
**Needs**: Same as Videos Page

#### 3. Create Page (`app/dashboard/create/page.tsx`)
**Needs**:
- Use `useProcessing` for video/audio listing
- Use `useJobs` for job status polling
- Add `useToast` for feedback
- Replace direct API calls

#### 4. Projects Page (`app/dashboard/projects/page.tsx`)
**Needs**:
- Assessment required (read file first)

## 📋 Refactoring Pattern

For any page with direct API calls, follow this pattern:

### Before (Old Pattern ❌):
```typescript
const loadFiles = async () => {
  try {
    const res = await authFetch(`${API_URL}/api/video-processor/files/videos`);
    const data = await res.json();  // No response.ok check!
    setFiles(data.files || []);
  } catch (error) {
    console.error("Error:", error);  // No user feedback!
  }
};
```

### After (New Pattern ✅):
```typescript
const { listFiles } = useFiles();
const toast = useToast();

const loadFiles = async () => {
  const response = await listFiles("videos");

  if (response) {
    setFiles(response.files);
  } else {
    toast.error("Failed to load video files");
  }
};
```

### File Upload Before (Old ❌):
```typescript
const handleUpload = async () => {
  setUploading(true);
  try {
    const formData = new FormData();
    formData.append("file", selectedFile);

    const res = await authFetch(`${API_URL}/api/video-processor/files/upload/video`, {
      method: "POST",
      body: formData
    });

    if (res.ok) {  // Manual check
      loadFiles();
    }
  } catch (error) {
    console.error(error);  // No user feedback!
  } finally {
    setUploading(false);
  }
};
```

### File Upload After (New ✅):
```typescript
const { uploadFile, uploadProgress, isUploading } = useUpload();
const toast = useToast();

const handleUpload = async () => {
  const result = await uploadFile(selectedFile, "video", folderName);

  if (result.success) {
    toast.success("Video uploaded successfully");
    loadFiles();
  } else {
    toast.error(result.error || "Failed to upload video");
  }
};

// In JSX: Show progress
{isUploading && (
  <div>Uploading: {uploadProgress}%</div>
)}
```

## 🎯 Benefits of New Architecture

### 1. Centralized Logic
- All API calls in reusable hooks
- Consistent error handling across app
- Single source of truth for endpoints

### 2. Better UX
- Toast notifications for all operations
- Upload progress indicators
- Loading states managed by hooks

### 3. Type Safety
- TypeScript interfaces for all responses
- Autocomplete for hook methods
- Compile-time error checking

### 4. Maintainability
- Change API endpoint once in `lib/api/client.ts`
- Update auth logic once in hooks
- Easy to test hooks in isolation

### 5. No Hallucinations
- Uses existing backend routes
- All endpoints defined in `API_ENDPOINTS`
- Matches backend schemas

## 🔧 Next Steps

1. Refactor remaining pages (videos, audios, create, projects)
2. Test complete authentication flow
3. Verify all toast notifications work
4. Test upload progress indicators
5. Ensure all errors show user-friendly messages

## 📝 Important Notes

- **No Local Storage**: Everything uses Supabase via backend API
- **Authentication**: All hooks automatically inject Clerk JWT token
- **Error Handling**: Hooks return null on error and set error state
- **Success States**: Check return values for null to detect failures
- **User Feedback**: Always show toast for operations (success/error)

## 🚀 Testing Checklist

Once all pages are refactored:

- [ ] Sign in/sign up flow
- [ ] Upload video with progress
- [ ] Upload audio with progress
- [ ] Upload CSV with progress
- [ ] List files (videos, audios, CSV)
- [ ] Delete files with toast confirmation
- [ ] Move files between folders
- [ ] Create folders
- [ ] Start processing job
- [ ] Poll job status
- [ ] View job results
- [ ] Error handling (network errors, auth errors, validation errors)
- [ ] Toast notifications appear for all operations
