"use client";

import { useState, useEffect, useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@heroui/button";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Input } from "@heroui/input";
import { Pagination } from "@heroui/pagination";
import type { Selection } from "@heroui/table";

import FileTable from "@/components/Dashboard/FileTable";
import FolderSidebar from "@/components/Dashboard/FolderSidebar";
import BulkActions from "@/components/Dashboard/BulkActions";
import type { VideoFile, Folder } from "@/lib/types";
import { useFiles, useFolders, useUpload, useToast } from "@/lib/hooks";
import { useVideoStreamUrls } from "@/lib/hooks/useVideoStreamUrl";

const VIDEO_COLUMNS = [
  { key: "preview", label: "PREVIEW" },
  { key: "name", label: "NAME" },
  { key: "size", label: "SIZE" },
  { key: "modified", label: "MODIFIED" },
  { key: "actions", label: "ACTIONS" }
] as const;

export default function VideosPage() {
  const { getToken } = useAuth();
  const { listFiles, deleteFile, bulkDeleteFiles, bulkMoveFiles, renameFile } = useFiles();
  const { listFolders, createFolder, deleteFolder } = useFolders();
  const { uploadFile, uploadMultipleFiles, uploadProgress, isUploading } = useUpload();
  const toast = useToast();

  const [folders, setFolders] = useState<Folder[]>([]);
  const [videos, setVideos] = useState<VideoFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedVideos, setSelectedVideos] = useState<Selection>(new Set());

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 20;

  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onClose: onUploadClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isRenameOpen, onOpen: onRenameOpen, onClose: onRenameClose } = useDisclosure();
  const { isOpen: isMoveOpen, onOpen: onMoveOpen, onClose: onMoveClose } = useDisclosure();

  const [uploadFolder, setUploadFolder] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewVideo, setPreviewVideo] = useState<VideoFile | null>(null);
  const [renameVideo, setRenameVideo] = useState<VideoFile | null>(null);
  const [newName, setNewName] = useState("");
  const [fileExtension, setFileExtension] = useState("");
  const [moveToFolder, setMoveToFolder] = useState("");

  useEffect(() => {
    loadFolders();
  }, []);

  useEffect(() => {
    loadAllVideos();
  }, [selectedFolder]);

  const loadFolders = async () => {
    const response = await listFolders("videos");
    if (response) {
      setFolders(response.folders);
    } else {
      toast.error("Failed to load folders");
    }
  };

  const loadAllVideos = async () => {
    setLoading(true);
    setCurrentPage(1); // Reset to first page when changing folders
    const response = await listFiles("videos", selectedFolder);
    setLoading(false);

    if (response) {
      const files = response.files as unknown as VideoFile[];
      setVideos(files);
      setSelectedVideos(new Set<string>());
    } else {
      toast.error("Failed to load video files");
    }
  };

  // Calculate pagination
  const totalPages = Math.ceil(videos.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const visibleVideos = videos.slice(startIndex, endIndex);

  // Load stream URLs ONLY for visible videos (huge performance improvement!)
  const visibleFilepaths = visibleVideos.map(v => v.filepath);
  const { urls: videoUrls, isLoading: urlsLoading } = useVideoStreamUrls(visibleFilepaths);

  const handleCreateFolder = async (folderName: string) => {
    const result = await createFolder("videos", folderName);
    if (result) {
      toast.success("Folder created successfully");
      loadFolders();
    } else {
      toast.error("Failed to create folder");
    }
  };

  const handleRenameFolder = async (oldName: string, newName: string) => {
    toast.info("Folder rename not yet implemented");
  };

  const handleDeleteFolder = async (folderName: string) => {
    const result = await deleteFolder("videos", folderName);
    if (result) {
      toast.success(`Folder "${folderName}" deleted successfully. ${result.files_deleted} file(s) removed.`);
      loadFolders();
      loadAllVideos();
    } else {
      toast.error("Failed to delete folder");
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || !uploadFolder) return;

    // Upload multiple files sequentially with progress
    const results = await uploadMultipleFiles(selectedFiles, "video", uploadFolder);

    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    if (successCount === selectedFiles.length) {
      toast.success(`Successfully uploaded ${successCount} video${successCount > 1 ? 's' : ''}`);
    } else if (successCount > 0) {
      toast.warning(`Uploaded ${successCount} video(s), ${failCount} failed`);
    } else {
      toast.error("Failed to upload videos");
    }

    setSelectedFiles([]);
    setUploadFolder("");
    onUploadClose();
    loadFolders();
    loadAllVideos();
  };

  const handleDelete = async (video: VideoFile) => {
    if (!confirm(`Delete ${getDisplayName(video)}?`)) return;

    const success = await deleteFile(video.filepath);

    if (success) {
      toast.success("Video deleted successfully");
      loadFolders();
      loadAllVideos();
    } else {
      toast.error("Failed to delete video");
    }
  };

  const handleBulkDelete = async () => {
    const selection = selectedVideos === "all" ? videos.map(v => v.filepath) : Array.from(selectedVideos);
    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected videos?`)) return;

    // Use bulk delete endpoint (best practice - single request instead of loop)
    const result = await bulkDeleteFiles(selection as string[]);

    setSelectedVideos(new Set<string>());

    if (result.deleted === selection.length) {
      toast.success(`Deleted ${result.deleted} video files successfully`);
    } else if (result.deleted > 0) {
      toast.warning(`Deleted ${result.deleted} of ${selection.length} video files. ${result.failed} failed.`);
    } else {
      toast.error("Failed to delete video files");
    }

    loadFolders();
    loadAllVideos();
  };

  const handleBulkMove = async () => {
    const selection = selectedVideos === "all" ? videos.map(v => v.filepath) : Array.from(selectedVideos);
    if (selection.length === 0 || !moveToFolder) return;

    const result = await bulkMoveFiles(selection as string[], moveToFolder);

    setSelectedVideos(new Set<string>());
    setMoveToFolder("");
    onMoveClose();

    if (result.moved === selection.length) {
      toast.success(`Moved ${result.moved} video files successfully to "${moveToFolder}"`);
    } else if (result.moved > 0) {
      toast.warning(`Moved ${result.moved} of ${selection.length} video files. ${result.failed} failed.`);
    } else {
      toast.error("Failed to move video files");
    }

    loadFolders();
    loadAllVideos();
  };

  const handleRename = async () => {
    if (!renameVideo || !newName.trim()) return;

    // Add extension back to the new name
    const newNameWithExtension = newName + fileExtension;
    const success = await renameFile(renameVideo.filepath, newNameWithExtension);

    if (success) {
      toast.success("Video renamed successfully");
      setRenameVideo(null);
      setNewName("");
      setFileExtension("");
      onRenameClose();
      // Reload videos to show updated name
      loadAllVideos();
    } else {
      toast.error("Failed to rename video");
    }
  };

  const openPreview = (video: VideoFile) => {
    setPreviewVideo(video);
    onPreviewOpen();
  };

  const openRename = (video: VideoFile) => {
    setRenameVideo(video);

    // Get display name (without timestamp if it's metadata)
    const displayName = getDisplayName(video);

    // Extract name without extension
    const extensionMatch = displayName.match(/\.[^/.]+$/);
    const extension = extensionMatch ? extensionMatch[0] : ".mp4";
    const nameWithoutExt = displayName.replace(/\.[^/.]+$/, "");

    setNewName(nameWithoutExt);
    setFileExtension(extension);
    onRenameOpen();
  };

  const getDisplayName = (video: VideoFile): string => {
    return (video as any).metadata?.original_filename || video.filename;
  };

  const rowActions = useMemo(() => [
    {
      label: "Rename",
      onClick: openRename,
      color: "default" as const
    },
    {
      label: "Delete",
      onClick: handleDelete,
      color: "danger" as const
    }
  ], []);

  const getSelectedCount = () => {
    return selectedVideos === "all" ? videos.length : selectedVideos.size;
  };

  const getTotalCount = () => {
    return folders.reduce((sum, folder) => sum + folder.file_count, 0);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Videos</h1>
          <p className="text-default-500">Manage your video files</p>
        </div>
        <Button onPress={onUploadOpen} color="primary">
          Upload Video
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <FolderSidebar
            folders={folders}
            selectedFolder={selectedFolder}
            onSelectFolder={setSelectedFolder}
            onCreateFolder={handleCreateFolder}
            onRenameFolder={handleRenameFolder}
            onDeleteFolder={handleDeleteFolder}
            totalCount={getTotalCount()}
            title="Video Folders"
          />
        </div>

        <div className="lg:col-span-3">
          <BulkActions
            selectedCount={getSelectedCount()}
            onClear={() => setSelectedVideos(new Set<string>())}
            actions={[
              {
                label: "Move Selected",
                onClick: onMoveOpen,
                color: "primary"
              },
              {
                label: "Delete Selected",
                onClick: handleBulkDelete,
                color: "danger"
              }
            ]}
          />

          <FileTable
            files={visibleVideos}
            columns={VIDEO_COLUMNS}
            selectedKeys={selectedVideos}
            onSelectionChange={setSelectedVideos}
            loading={loading || urlsLoading}
            emptyMessage="No videos in this folder"
            primaryAction={{
              label: "Preview",
              onClick: openPreview
            }}
            rowActions={rowActions}
            renderCell={(file, columnKey) => {
              const video = file as VideoFile;

              if (columnKey === "preview") {
                // Use thumbnail if available, otherwise fall back to video stream
                const thumbnailUrl = video.metadata?.thumbnail_url;
                const streamUrl = videoUrls[video.filepath];

                return (
                  <div
                    className="w-20 h-12 bg-black rounded overflow-hidden cursor-pointer hover:opacity-80 transition"
                    onClick={() => openPreview(video)}
                  >
                    {thumbnailUrl ? (
                      <img
                        className="w-full h-full object-cover"
                        src={thumbnailUrl}
                        alt="Video thumbnail"
                        loading="lazy"
                        decoding="async"
                      />
                    ) : streamUrl ? (
                      <video
                        className="w-full h-full object-contain bg-black"
                        src={`${streamUrl}#t=0.1`}
                        preload="metadata"
                        muted
                        playsInline
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gray-800 animate-pulse">
                        <div className="w-8 h-8 border-2 border-gray-600 border-t-gray-400 rounded-full animate-spin" />
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center mt-6">
              <Pagination
                total={totalPages}
                page={currentPage}
                onChange={setCurrentPage}
                showControls
                color="primary"
                size="lg"
              />
            </div>
          )}

          {/* Stats */}
          <div className="text-center text-sm text-default-500 mt-4">
            Showing {startIndex + 1}-{Math.min(endIndex, videos.length)} of {videos.length} videos
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <Modal isOpen={isUploadOpen} onClose={onUploadClose}>
        <ModalContent>
          <ModalHeader>Upload Video</ModalHeader>
          <ModalBody>
            <Select
              label="Select Folder"
              placeholder="Choose folder"
              selectedKeys={uploadFolder ? [uploadFolder] : []}
              onSelectionChange={(keys) => setUploadFolder(Array.from(keys)[0] as string)}
              isRequired
              description="Videos will be uploaded to this folder"
            >
              {folders.map((folder) => (
                <SelectItem key={folder.name}>{folder.name}</SelectItem>
              ))}
            </Select>
            <Input
              type="file"
              accept=".mp4,.mov,.m4v,.avi,.mkv"
              onChange={(e) => {
                const files = e.target.files;
                if (files) {
                  setSelectedFiles(Array.from(files));
                }
              }}
              // @ts-ignore - multiple attribute is valid
              multiple
            />
            {selectedFiles.length > 0 && (
              <div className="text-sm text-default-500">
                {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected
              </div>
            )}
            {isUploading && (
              <div className="mt-2">
                <p className="text-sm text-default-500 mb-1">
                  Uploading: {uploadProgress}%
                  {uploadProgress >= 80 && uploadProgress < 100 && " (Processing on server...)"}
                </p>
                <div className="w-full bg-default-200 rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onUploadClose} isDisabled={isUploading}>
              Cancel
            </Button>
            <Button
              color="primary"
              onPress={handleUpload}
              isLoading={isUploading}
              isDisabled={!uploadFolder || selectedFiles.length === 0}
            >
              Upload {selectedFiles.length > 1 ? `${selectedFiles.length} Files` : ''}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Preview Modal */}
      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="5xl" scrollBehavior="inside">
        <ModalContent>
          <ModalHeader>{previewVideo ? getDisplayName(previewVideo) : ""}</ModalHeader>
          <ModalBody>
            {previewVideo && videoUrls[previewVideo.filepath] ? (
              <video
                controls
                className="w-full max-h-[70vh] rounded-lg object-contain bg-black"
                src={videoUrls[previewVideo.filepath]}
                autoPlay
              >
                Your browser does not support video playback.
              </video>
            ) : (
              <div className="flex items-center justify-center min-h-[400px]">
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                  <p className="text-default-500">Loading video...</p>
                </div>
              </div>
            )}
          </ModalBody>
          <ModalFooter>
            <Button onPress={onPreviewClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Rename Modal */}
      <Modal isOpen={isRenameOpen} onClose={onRenameClose}>
        <ModalContent>
          <ModalHeader>Rename Video</ModalHeader>
          <ModalBody>
            <Input
              label="New Name"
              placeholder="Enter new name (without extension)"
              value={newName}
              onValueChange={setNewName}
              endContent={
                <span className="text-default-400 text-sm whitespace-nowrap">
                  {fileExtension}
                </span>
              }
              description="File extension cannot be changed"
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onRenameClose}>
              Cancel
            </Button>
            <Button color="primary" onPress={handleRename}>
              Rename
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Move Modal */}
      <Modal isOpen={isMoveOpen} onClose={onMoveClose}>
        <ModalContent>
          <ModalHeader>Move {getSelectedCount()} Videos</ModalHeader>
          <ModalBody>
            <Select
              label="Destination Folder"
              placeholder="Choose folder"
              selectedKeys={moveToFolder ? [moveToFolder] : []}
              onSelectionChange={(keys) => setMoveToFolder(Array.from(keys)[0] as string)}
            >
              {folders.filter(f => f.name !== selectedFolder).map((folder) => (
                <SelectItem key={folder.name}>{folder.name}</SelectItem>
              ))}
            </Select>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onMoveClose}>
              Cancel
            </Button>
            <Button color="primary" onPress={handleBulkMove} isDisabled={!moveToFolder}>
              Move
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
