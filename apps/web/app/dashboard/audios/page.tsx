"use client";

import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Chip } from "@heroui/chip";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AudioFile {
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

export default function AudiosPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [audios, setAudios] = useState<AudioFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onClose: onUploadClose } = useDisclosure();
  const { isOpen: isFolderOpen, onOpen: onFolderOpen, onClose: onFolderClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isRenameOpen, onOpen: onRenameOpen, onClose: onRenameClose } = useDisclosure();

  const [newFolderName, setNewFolderName] = useState("");
  const [uploadFolder, setUploadFolder] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewAudio, setPreviewAudio] = useState<AudioFile | null>(null);
  const [renameAudio, setRenameAudio] = useState<AudioFile | null>(null);
  const [newName, setNewName] = useState("");

  useEffect(() => {
    loadFolders();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadAudios(selectedFolder);
    }
  }, [selectedFolder]);

  const loadFolders = async () => {
    try {
      const res = await fetch(`${API_URL}/api/video-processor/folders/audios`);
      const data = await res.json();
      setFolders(data.folders || []);
      if (data.folders?.length > 0 && !selectedFolder) {
        setSelectedFolder(data.folders[0].name);
      }
    } catch (error) {
      console.error("Error loading folders:", error);
    }
  };

  const loadAudios = async (folder: string) => {
    setLoading(true);
    try {
      const params = folder ? `?subfolder=${folder}` : "";
      const res = await fetch(`${API_URL}/api/video-processor/files/audios${params}`);
      const data = await res.json();
      setAudios(data.files || []);
    } catch (error) {
      console.error("Error loading audios:", error);
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
          parent_category: "audios",
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

      const res = await fetch(`${API_URL}/api/video-processor/files/upload/audio`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        setSelectedFile(null);
        onUploadClose();
        loadFolders();
        if (uploadFolder) {
          loadAudios(uploadFolder);
        }
      }
    } catch (error) {
      console.error("Error uploading audio:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (audio: AudioFile) => {
    if (!confirm(`Delete ${audio.filename}?`)) return;

    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/delete`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filepath: audio.filepath })
      });

      if (res.ok) {
        loadFolders();
        loadAudios(selectedFolder);
      }
    } catch (error) {
      console.error("Error deleting audio:", error);
    }
  };

  const handleRename = async () => {
    if (!renameAudio || !newName.trim()) return;

    try {
      const newPath = renameAudio.filepath.replace(renameAudio.filename, newName);
      const res = await fetch(`${API_URL}/api/video-processor/files/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_path: renameAudio.filepath,
          destination_folder: newPath
        })
      });

      if (res.ok) {
        setNewName("");
        setRenameAudio(null);
        onRenameClose();
        loadFolders();
        loadAudios(selectedFolder);
      }
    } catch (error) {
      console.error("Error renaming audio:", error);
    }
  };

  const openPreview = (audio: AudioFile) => {
    setPreviewAudio(audio);
    onPreviewOpen();
  };

  const openRename = (audio: AudioFile) => {
    setRenameAudio(audio);
    setNewName(audio.filename);
    onRenameOpen();
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Audios</h1>
          <p className="text-default-500">Manage your audio files</p>
        </div>
        <div className="flex gap-2">
          <Button onPress={onFolderOpen} variant="flat">
            New Folder
          </Button>
          <Button onPress={onUploadOpen} color="primary">
            Upload Audio
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
            ) : audios.length === 0 ? (
              <p className="text-default-400">No audios in this folder</p>
            ) : (
              audios.map((audio) => (
                <Card key={audio.filepath}>
                  <CardBody className="gap-3">
                    <div
                      className="aspect-video bg-gradient-to-br from-secondary/20 to-primary/20 rounded-lg flex items-center justify-center cursor-pointer hover:opacity-80 transition"
                      onClick={() => openPreview(audio)}
                    >
                      <span className="text-4xl">🎵</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm truncate">{audio.filename}</h4>
                      <p className="text-xs text-default-500">
                        {(audio.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="flat" className="flex-1" onPress={() => openPreview(audio)}>
                        Play
                      </Button>
                      <Button size="sm" variant="flat" onPress={() => openRename(audio)}>
                        Rename
                      </Button>
                      <Button size="sm" color="danger" variant="flat" onPress={() => handleDelete(audio)}>
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
          <ModalHeader>Upload Audio</ModalHeader>
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
              accept=".mp3,.wav,.m4a"
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

      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="2xl">
        <ModalContent>
          <ModalHeader>{previewAudio?.filename}</ModalHeader>
          <ModalBody>
            {previewAudio && (
              <audio
                controls
                className="w-full"
                src={`file://${previewAudio.filepath}`}
              >
                Your browser does not support audio playback.
              </audio>
            )}
          </ModalBody>
          <ModalFooter>
            <Button onPress={onPreviewClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal isOpen={isRenameOpen} onClose={onRenameClose}>
        <ModalContent>
          <ModalHeader>Rename Audio</ModalHeader>
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
