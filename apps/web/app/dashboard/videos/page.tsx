"use client";

import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Chip } from "@heroui/chip";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface VideoFile {
  filename: string;
  filepath: string;
  size: number;
  modified: string;
  type: string;
}

interface Folder {
  name: string;
  path: string;
  file_count: number;
  total_size: number;
}

export default function VideosPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [videos, setVideos] = useState<VideoFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onClose: onUploadClose } = useDisclosure();
  const { isOpen: isFolderOpen, onOpen: onFolderOpen, onClose: onFolderClose } = useDisclosure();

  const [newFolderName, setNewFolderName] = useState("");
  const [uploadFolder, setUploadFolder] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadFolders();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadVideos(selectedFolder);
    }
  }, [selectedFolder]);

  const loadFolders = async () => {
    try {
      const res = await fetch(`${API_URL}/api/video-processor/folders/videos`);
      const data = await res.json();
      setFolders(data.folders || []);
      if (data.folders?.length > 0 && !selectedFolder) {
        setSelectedFolder(data.folders[0].name);
      }
    } catch (error) {
      console.error("Error loading folders:", error);
    }
  };

  const loadVideos = async (folder: string) => {
    setLoading(true);
    try {
      const params = folder ? `?subfolder=${folder}` : "";
      const res = await fetch(`${API_URL}/api/video-processor/files/videos${params}`);
      const data = await res.json();
      setVideos(data.files || []);
    } catch (error) {
      console.error("Error loading videos:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      const res = await fetch(`${API_URL}/api/video-processor/folders/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          parent_category: "videos",
          folder_name: newFolderName
        })
      });

      if (res.ok) {
        setNewFolderName("");
        onFolderClose();
        loadFolders();
      }
    } catch (error) {
      console.error("Error creating folder:", error);
    }
  };

  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isRenameOpen, onOpen: onRenameOpen, onClose: onRenameClose } = useDisclosure();

  const [previewVideo, setPreviewVideo] = useState<VideoFile | null>(null);
  const [renameVideo, setRenameVideo] = useState<VideoFile | null>(null);
  const [newName, setNewName] = useState("");

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (uploadFolder) {
        formData.append("subfolder", uploadFolder);
      }

      const res = await fetch(`${API_URL}/api/video-processor/files/upload/video`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        setSelectedFile(null);
        onUploadClose();
        loadFolders();
        if (uploadFolder) {
          loadVideos(uploadFolder);
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
        loadVideos(selectedFolder);
      }
    } catch (error) {
      console.error("Error deleting video:", error);
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
        loadVideos(selectedFolder);
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

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Videos</h1>
          <p className="text-default-500">Manage your video files</p>
        </div>
        <div className="flex gap-2">
          <Button onPress={onFolderOpen} variant="flat">
            New Folder
          </Button>
          <Button onPress={onUploadOpen} color="primary">
            Upload Video
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h3 className="font-semibold">Folders</h3>
            </CardHeader>
            <CardBody className="gap-2">
              {folders.map((folder) => (
                <Button
                  key={folder.name}
                  variant={selectedFolder === folder.name ? "flat" : "light"}
                  color={selectedFolder === folder.name ? "primary" : "default"}
                  className="justify-start"
                  onPress={() => setSelectedFolder(folder.name)}
                >
                  {folder.name}
                  <Chip size="sm" variant="flat" className="ml-auto">
                    {folder.file_count}
                  </Chip>
                </Button>
              ))}
            </CardBody>
          </Card>
        </div>

        <div className="lg:col-span-3">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <p>Loading...</p>
            ) : videos.length === 0 ? (
              <p className="text-default-400">No videos in this folder</p>
            ) : (
              videos.map((video) => (
                <Card key={video.filepath}>
                  <CardBody className="gap-3">
                    <div
                      className="aspect-video bg-gradient-to-br from-primary/20 to-secondary/20 rounded-lg flex items-center justify-center cursor-pointer hover:opacity-80 transition"
                      onClick={() => openPreview(video)}
                    >
                      <span className="text-4xl">🎬</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm truncate">{video.filename}</h4>
                      <p className="text-xs text-default-500">
                        {(video.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="flat" className="flex-1" onPress={() => openPreview(video)}>
                        Preview
                      </Button>
                      <Button size="sm" variant="flat" onPress={() => openRename(video)}>
                        Rename
                      </Button>
                      <Button size="sm" color="danger" variant="flat" onPress={() => handleDelete(video)}>
                        Delete
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      <Modal isOpen={isUploadOpen} onClose={onUploadClose}>
        <ModalContent>
          <ModalHeader>Upload Video</ModalHeader>
          <ModalBody>
            <Select
              label="Select Folder"
              placeholder="Choose folder"
              selectedKeys={uploadFolder ? [uploadFolder] : []}
              onSelectionChange={(keys) => setUploadFolder(Array.from(keys)[0] as string)}
            >
              {folders.map((folder) => (
                <SelectItem key={folder.name}>{folder.name}</SelectItem>
              ))}
            </Select>
            <Input
              type="file"
              accept=".mp4,.mov,.m4v,.avi,.mkv"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onUploadClose}>
              Cancel
            </Button>
            <Button color="primary" onPress={handleUpload} isLoading={uploading}>
              Upload
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal isOpen={isFolderOpen} onClose={onFolderClose}>
        <ModalContent>
          <ModalHeader>Create Folder</ModalHeader>
          <ModalBody>
            <Input
              label="Folder Name"
              placeholder="Enter folder name"
              value={newFolderName}
              onValueChange={setNewFolderName}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onFolderClose}>
              Cancel
            </Button>
            <Button color="primary" onPress={handleCreateFolder}>
              Create
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="3xl">
        <ModalContent>
          <ModalHeader>{previewVideo?.filename}</ModalHeader>
          <ModalBody>
            {previewVideo && (
              <video
                controls
                className="w-full rounded-lg"
                src={`file://${previewVideo.filepath}`}
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

      <Modal isOpen={isRenameOpen} onClose={onRenameClose}>
        <ModalContent>
          <ModalHeader>Rename Video</ModalHeader>
          <ModalBody>
            <Input
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
    </div>
  );
}
