"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@heroui/button";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Input } from "@heroui/input";
import type { Selection } from "@heroui/table";
import { Edit, Trash } from "iconsax-reactjs";

import FileTable from "@/components/Dashboard/FileTable";
import FolderSidebar from "@/components/Dashboard/FolderSidebar";
import BulkActions from "@/components/Dashboard/BulkActions";
import { API_URL, delay } from "@/lib/utils";
import type { VideoFile, Folder } from "@/lib/types";

const VIDEO_COLUMNS = [
  { key: "preview", label: "PREVIEW" },
  { key: "name", label: "NAME" },
  { key: "size", label: "SIZE" },
  { key: "modified", label: "MODIFIED" },
  { key: "actions", label: "ACTIONS" }
] as const;

export default function VideosPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [videos, setVideos] = useState<VideoFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedVideos, setSelectedVideos] = useState<Selection>(new Set());

  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onClose: onUploadClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isRenameOpen, onOpen: onRenameOpen, onClose: onRenameClose } = useDisclosure();
  const { isOpen: isMoveOpen, onOpen: onMoveOpen, onClose: onMoveClose } = useDisclosure();

  const [uploadFolder, setUploadFolder] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewVideo, setPreviewVideo] = useState<VideoFile | null>(null);
  const [renameVideo, setRenameVideo] = useState<VideoFile | null>(null);
  const [newName, setNewName] = useState("");
  const [moveToFolder, setMoveToFolder] = useState("");

  useEffect(() => {
    loadFolders();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadVideos(selectedFolder);
    } else {
      loadAllVideos();
    }
  }, [selectedFolder]);

  const loadFolders = async () => {
    try {
      const res = await fetch(`${API_URL}/api/video-processor/folders/videos`);
      const data = await res.json();
      setFolders(data.folders || []);
    } catch (error) {
      console.error("Error loading folders:", error);
    }
  };

  const loadAllVideos = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/videos`);
      const data = await res.json();
      setVideos(data.files || []);
      setSelectedVideos(new Set<string>());
    } catch (error) {
      console.error("Error loading videos:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadVideos = async (folder: string) => {
    setLoading(true);
    try {
      const params = `?subfolder=${folder}`;
      const res = await fetch(`${API_URL}/api/video-processor/files/videos${params}`);
      const data = await res.json();
      setVideos(data.files || []);
      setSelectedVideos(new Set<string>());
    } catch (error) {
      console.error("Error loading videos:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async (folderName: string) => {
    try {
      const res = await fetch(`${API_URL}/api/video-processor/folders/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          parent_category: "videos",
          folder_name: folderName
        })
      });

      if (res.ok) {
        loadFolders();
      }
    } catch (error) {
      console.error("Error creating folder:", error);
    }
  };

  const handleRenameFolder = async (oldName: string, newName: string) => {
    // TODO: Implement rename folder API
    console.log("Rename folder:", oldName, "to", newName);
    await delay(500);
    loadFolders();
  };

  const handleDeleteFolder = async (folderName: string) => {
    // TODO: Implement delete folder API
    console.log("Delete folder:", folderName);
    await delay(500);
    loadFolders();
  };

  const handleUpload = async () => {
    if (!selectedFile || !uploadFolder) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("subfolder", uploadFolder);

      const res = await fetch(`${API_URL}/api/video-processor/files/upload/video`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        setSelectedFile(null);
        setUploadFolder("");
        onUploadClose();
        loadFolders();
        if (selectedFolder) {
          loadVideos(selectedFolder);
        } else {
          loadAllVideos();
        }
      }
    } catch (error) {
      console.error("Error uploading video:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (video: VideoFile) => {
    if (!confirm(`Delete ${video.filename}?`)) return;

    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/delete`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filepath: video.filepath })
      });

      if (res.ok) {
        loadFolders();
        if (selectedFolder) {
          loadVideos(selectedFolder);
        } else {
          loadAllVideos();
        }
      }
    } catch (error) {
      console.error("Error deleting video:", error);
    }
  };

  const handleBulkDelete = async () => {
    const selection = selectedVideos === "all" ? videos.map(v => v.filepath) : Array.from(selectedVideos);
    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected videos?`)) return;

    try {
      const deletePromises = selection.map(filepath =>
        fetch(`${API_URL}/api/video-processor/files/delete`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filepath })
        })
      );

      await Promise.all(deletePromises);
      setSelectedVideos(new Set<string>());
      loadFolders();
      if (selectedFolder) {
        loadVideos(selectedFolder);
      } else {
        loadAllVideos();
      }
    } catch (error) {
      console.error("Error deleting videos:", error);
    }
  };

  const handleBulkMove = async () => {
    const selection = selectedVideos === "all" ? videos.map(v => v.filepath) : Array.from(selectedVideos);
    if (selection.length === 0 || !moveToFolder) return;

    try {
      const targetFolder = folders.find(f => f.name === moveToFolder);
      if (!targetFolder) return;

      const movePromises = selection.map(filepath => {
        const filename = filepath.split(/[/\\]/).pop() || "";
        const newPath = `${targetFolder.path}\\${filename}`;

        return fetch(`${API_URL}/api/video-processor/files/move`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_path: filepath,
            destination_folder: newPath
          })
        });
      });

      await Promise.all(movePromises);
      setSelectedVideos(new Set<string>());
      setMoveToFolder("");
      onMoveClose();
      loadFolders();
      if (selectedFolder) {
        loadVideos(selectedFolder);
      } else {
        loadAllVideos();
      }
    } catch (error) {
      console.error("Error moving videos:", error);
    }
  };

  const handleRename = async () => {
    if (!renameVideo || !newName.trim()) return;

    try {
      const newPath = renameVideo.filepath.replace(renameVideo.filename, newName);
      const res = await fetch(`${API_URL}/api/video-processor/files/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_path: renameVideo.filepath,
          destination_folder: newPath
        })
      });

      if (res.ok) {
        setNewName("");
        setRenameVideo(null);
        onRenameClose();
        loadFolders();
        if (selectedFolder) {
          loadVideos(selectedFolder);
        } else {
          loadAllVideos();
        }
      }
    } catch (error) {
      console.error("Error renaming video:", error);
    }
  };

  const openPreview = (video: VideoFile) => {
    setPreviewVideo(video);
    onPreviewOpen();
  };

  const openRename = (video: VideoFile) => {
    setRenameVideo(video);
    setNewName(video.filename);
    onRenameOpen();
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
            files={videos}
            columns={VIDEO_COLUMNS}
            selectedKeys={selectedVideos}
            onSelectionChange={setSelectedVideos}
            loading={loading}
            emptyMessage="No videos in this folder"
            primaryAction={{
              label: "Preview",
              onClick: openPreview
            }}
            rowActions={rowActions}
            renderCell={(file, columnKey) => {
              const video = file as VideoFile;

              if (columnKey === "preview") {
                return (
                  <div
                    className="w-20 h-12 bg-black rounded overflow-hidden cursor-pointer hover:opacity-80 transition"
                    onClick={() => openPreview(video)}
                  >
                    <video
                      className="w-full h-full object-cover"
                      src={`${API_URL}/api/video-processor/files/stream/video?filepath=${encodeURIComponent(video.filepath)}#t=0.1`}
                      preload="metadata"
                      muted
                      playsInline
                    />
                  </div>
                );
              }
              return null;
            }}
          />
        </div>
      </div>

      {/* Upload Modal */}
      <Modal isOpen={isUploadOpen} onClose={onUploadClose}>
        <ModalContent>
          <ModalHeader>Upload Video</ModalHeader>
          <ModalBody>
            <Select
              id="upload-video-folder"
              name="uploadFolder"
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
              id="upload-video-file"
              name="videoFile"
              type="file"
              accept=".mp4,.mov,.m4v,.avi,.mkv"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onUploadClose}>
              Cancel
            </Button>
            <Button
              color="primary"
              onPress={handleUpload}
              isLoading={uploading}
              isDisabled={!uploadFolder || !selectedFile}
            >
              Upload
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Preview Modal */}
      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="5xl" scrollBehavior="inside">
        <ModalContent>
          <ModalHeader>{previewVideo?.filename}</ModalHeader>
          <ModalBody>
            {previewVideo && (
              <video
                controls
                className="w-full max-h-[70vh] rounded-lg"
                src={`${API_URL}/api/video-processor/files/stream/video?filepath=${encodeURIComponent(previewVideo.filepath)}`}
              >
                Your browser does not support video playback.
              </video>
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
              id="rename-video-name"
              name="newVideoName"
              label="New Name"
              placeholder="Enter new name"
              value={newName}
              onValueChange={setNewName}
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
              id="move-video-destination"
              name="moveDestination"
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
