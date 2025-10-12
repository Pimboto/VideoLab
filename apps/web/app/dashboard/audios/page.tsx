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
import type { AudioFile, Folder } from "@/lib/types";

const AUDIO_COLUMNS = [
  { key: "name", label: "NAME" },
  { key: "size", label: "SIZE" },
  { key: "modified", label: "MODIFIED" },
  { key: "actions", label: "ACTIONS" }
] as const;

export default function AudiosPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [audios, setAudios] = useState<AudioFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedAudios, setSelectedAudios] = useState<Selection>(new Set());

  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onClose: onUploadClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isRenameOpen, onOpen: onRenameOpen, onClose: onRenameClose } = useDisclosure();
  const { isOpen: isMoveOpen, onOpen: onMoveOpen, onClose: onMoveClose } = useDisclosure();

  const [uploadFolder, setUploadFolder] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewAudio, setPreviewAudio] = useState<AudioFile | null>(null);
  const [renameAudio, setRenameAudio] = useState<AudioFile | null>(null);
  const [newName, setNewName] = useState("");
  const [moveToFolder, setMoveToFolder] = useState("");

  useEffect(() => {
    loadFolders();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadAudios(selectedFolder);
    } else {
      loadAllAudios();
    }
  }, [selectedFolder]);

  const loadFolders = async () => {
    try {
      const res = await fetch(`${API_URL}/api/video-processor/folders/audios`);
      const data = await res.json();
      setFolders(data.folders || []);
    } catch (error) {
      console.error("Error loading folders:", error);
    }
  };

  const loadAllAudios = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/audios`);
      const data = await res.json();
      setAudios(data.files || []);
      setSelectedAudios(new Set<string>());
    } catch (error) {
      console.error("Error loading audios:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadAudios = async (folder: string) => {
    setLoading(true);
    try {
      const params = `?subfolder=${folder}`;
      const res = await fetch(`${API_URL}/api/video-processor/files/audios${params}`);
      const data = await res.json();
      setAudios(data.files || []);
      setSelectedAudios(new Set<string>());
    } catch (error) {
      console.error("Error loading audios:", error);
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
          parent_category: "audios",
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
    console.log("Rename folder:", oldName, "to", newName);
    await delay(500);
    loadFolders();
  };

  const handleDeleteFolder = async (folderName: string) => {
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

      const res = await fetch(`${API_URL}/api/video-processor/files/upload/audio`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        setSelectedFile(null);
        setUploadFolder("");
        onUploadClose();
        loadFolders();
        if (selectedFolder) {
          loadAudios(selectedFolder);
        } else {
          loadAllAudios();
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
        if (selectedFolder) {
          loadAudios(selectedFolder);
        } else {
          loadAllAudios();
        }
      }
    } catch (error) {
      console.error("Error deleting audio:", error);
    }
  };

  const handleBulkDelete = async () => {
    const selection = selectedAudios === "all" ? audios.map(a => a.filepath) : Array.from(selectedAudios);
    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected audios?`)) return;

    try {
      const deletePromises = selection.map(filepath =>
        fetch(`${API_URL}/api/video-processor/files/delete`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filepath })
        })
      );

      await Promise.all(deletePromises);
      setSelectedAudios(new Set<string>());
      loadFolders();
      if (selectedFolder) {
        loadAudios(selectedFolder);
      } else {
        loadAllAudios();
      }
    } catch (error) {
      console.error("Error deleting audios:", error);
    }
  };

  const handleBulkMove = async () => {
    const selection = selectedAudios === "all" ? audios.map(a => a.filepath) : Array.from(selectedAudios);
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
      setSelectedAudios(new Set<string>());
      setMoveToFolder("");
      onMoveClose();
      loadFolders();
      if (selectedFolder) {
        loadAudios(selectedFolder);
      } else {
        loadAllAudios();
      }
    } catch (error) {
      console.error("Error moving audios:", error);
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
        if (selectedFolder) {
          loadAudios(selectedFolder);
        } else {
          loadAllAudios();
        }
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
    return selectedAudios === "all" ? audios.length : selectedAudios.size;
  };

  const getTotalCount = () => {
    return folders.reduce((sum, folder) => sum + folder.file_count, 0);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Audios</h1>
          <p className="text-default-500">Manage your audio files</p>
        </div>
        <Button onPress={onUploadOpen} color="primary">
          Upload Audio
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
            title="Audio Folders"
          />
        </div>

        <div className="lg:col-span-3">
          <BulkActions
            selectedCount={getSelectedCount()}
            onClear={() => setSelectedAudios(new Set<string>())}
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
            files={audios}
            columns={AUDIO_COLUMNS}
            selectedKeys={selectedAudios}
            onSelectionChange={setSelectedAudios}
            loading={loading}
            emptyMessage="No audios in this folder"
            primaryAction={{
              label: "Play",
              onClick: openPreview
            }}
            rowActions={rowActions}
          />
        </div>
      </div>

      {/* Upload Modal */}
      <Modal isOpen={isUploadOpen} onClose={onUploadClose}>
        <ModalContent>
          <ModalHeader>Upload Audio</ModalHeader>
          <ModalBody>
            <Select
              id="upload-audio-folder"
              name="uploadFolder"
              label="Select Folder"
              placeholder="Choose folder"
              selectedKeys={uploadFolder ? [uploadFolder] : []}
              onSelectionChange={(keys) => setUploadFolder(Array.from(keys)[0] as string)}
              isRequired
              description="Audios will be uploaded to this folder"
            >
              {folders.map((folder) => (
                <SelectItem key={folder.name}>{folder.name}</SelectItem>
              ))}
            </Select>
            <Input
              id="upload-audio-file"
              name="audioFile"
              type="file"
              accept=".mp3,.wav,.m4a"
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
      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="2xl">
        <ModalContent>
          <ModalHeader>{previewAudio?.filename}</ModalHeader>
          <ModalBody>
            {previewAudio && (
              <audio
                controls
                className="w-full"
                src={`${API_URL}/api/video-processor/files/stream/audio?filepath=${encodeURIComponent(previewAudio.filepath)}`}
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

      {/* Rename Modal */}
      <Modal isOpen={isRenameOpen} onClose={onRenameClose}>
        <ModalContent>
          <ModalHeader>Rename Audio</ModalHeader>
          <ModalBody>
            <Input
              id="rename-audio-name"
              name="newAudioName"
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
          <ModalHeader>Move {getSelectedCount()} Audios</ModalHeader>
          <ModalBody>
            <Select
              id="move-audio-destination"
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
