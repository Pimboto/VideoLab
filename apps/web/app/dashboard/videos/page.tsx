"use client";

import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Chip } from "@heroui/chip";
import { Skeleton } from "@heroui/skeleton";
import { Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from "@heroui/table";
import { Checkbox } from "@heroui/checkbox";
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from "@heroui/dropdown";
import type { Selection } from "@heroui/table";

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
  const [selectedVideos, setSelectedVideos] = useState<Selection>(new Set());

  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onClose: onUploadClose } = useDisclosure();
  const { isOpen: isFolderOpen, onOpen: onFolderOpen, onClose: onFolderClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isRenameOpen, onOpen: onRenameOpen, onClose: onRenameClose } = useDisclosure();
  const { isOpen: isMoveOpen, onOpen: onMoveOpen, onClose: onMoveClose } = useDisclosure();

  const [newFolderName, setNewFolderName] = useState("");
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
      setSelectedVideos(new Set<string>());
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
      loadVideos(selectedFolder);
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
      loadVideos(selectedFolder);
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

  const getSelectedCount = () => {
    return selectedVideos === "all" ? videos.length : selectedVideos.size;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
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
          {getSelectedCount() > 0 && (
            <div className="mb-4 flex gap-2 items-center bg-default-100 p-3 rounded-lg">
              <Chip color="primary">{getSelectedCount()} selected</Chip>
              <Button
                size="sm"
                color="danger"
                variant="flat"
                onPress={handleBulkDelete}
              >
                Delete Selected
              </Button>
              <Button
                size="sm"
                color="primary"
                variant="flat"
                onPress={onMoveOpen}
              >
                Move Selected
              </Button>
              <Button
                size="sm"
                variant="flat"
                onPress={() => setSelectedVideos(new Set<string>())}
              >
                Clear Selection
              </Button>
            </div>
          )}

          <Table
            aria-label="Videos table"
            selectionMode="multiple"
            selectedKeys={selectedVideos}
            onSelectionChange={setSelectedVideos}
            classNames={{
              wrapper: "min-h-[400px]",
            }}
          >
              <TableHeader>
                <TableColumn>PREVIEW</TableColumn>
                <TableColumn>NAME</TableColumn>
                <TableColumn>SIZE</TableColumn>
                <TableColumn>MODIFIED</TableColumn>
                <TableColumn>ACTIONS</TableColumn>
              </TableHeader>
              <TableBody
                items={videos}
                emptyContent={loading ? "Loading..." : "No videos in this folder"}
              >
                {(video) => (
                  <TableRow key={video.filepath}>
                    <TableCell>
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
                    </TableCell>
                    <TableCell>
                      <div className="max-w-xs">
                        <p className="text-sm font-medium truncate">{video.filename}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-default-500">{formatFileSize(video.size)}</p>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-default-500">{formatDate(video.modified)}</p>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button size="sm" variant="flat" onPress={() => openPreview(video)}>
                          Preview
                        </Button>
                        <Dropdown>
                          <DropdownTrigger>
                            <Button size="sm" variant="flat">⋮</Button>
                          </DropdownTrigger>
                          <DropdownMenu>
                            <DropdownItem onPress={() => openRename(video)}>Rename</DropdownItem>
                            <DropdownItem onPress={() => handleDelete(video)} className="text-danger" color="danger">
                              Delete
                            </DropdownItem>
                          </DropdownMenu>
                        </Dropdown>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
          </Table>
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
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onUploadClose}>
              Cancel
            </Button>
            <Button color="primary" onPress={handleUpload} isLoading={uploading} isDisabled={!uploadFolder || !selectedFile}>
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
