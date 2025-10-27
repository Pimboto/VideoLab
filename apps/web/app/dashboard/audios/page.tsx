"use client";

import { useState, useEffect, useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@heroui/button";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Input } from "@heroui/input";
import type { Selection } from "@heroui/table";

import FileTable from "@/components/Dashboard/FileTable";
import FolderSidebar from "@/components/Dashboard/FolderSidebar";
import BulkActions from "@/components/Dashboard/BulkActions";
import type { AudioFile, Folder } from "@/lib/types";
import { useFiles, useFolders, useUpload, useToast } from "@/lib/hooks";

const AUDIO_COLUMNS = [
  { key: "name", label: "NAME" },
  { key: "size", label: "SIZE" },
  { key: "modified", label: "MODIFIED" },
  { key: "actions", label: "ACTIONS" }
] as const;

export default function AudiosPage() {
  const { getToken } = useAuth();
  const { listFiles, deleteFile, getAudioStreamUrl } = useFiles();
  const { listFolders, createFolder } = useFolders();
  const { uploadFile, uploadProgress, isUploading } = useUpload();
  const toast = useToast();

  const [folders, setFolders] = useState<Folder[]>([]);
  const [audios, setAudios] = useState<AudioFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
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
    loadAllAudios();
  }, [selectedFolder]);

  const loadFolders = async () => {
    const response = await listFolders("audios");
    if (response) {
      setFolders(response.folders);
    } else {
      toast.error("Failed to load folders");
    }
  };

  const loadAllAudios = async () => {
    setLoading(true);
    const response = await listFiles("audios");
    setLoading(false);

    if (response) {
      setAudios(response.files as unknown as AudioFile[]);
      setSelectedAudios(new Set<string>());
    } else {
      toast.error("Failed to load audio files");
    }
  };

  const handleCreateFolder = async (folderName: string) => {
    const result = await createFolder("audios", folderName);
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
    toast.info("Folder delete not yet implemented");
  };

  const handleUpload = async () => {
    if (!selectedFile || !uploadFolder) return;

    const result = await uploadFile(selectedFile, "audio", uploadFolder);

    if (result.success) {
      toast.success("Audio uploaded successfully");
      setSelectedFile(null);
      setUploadFolder("");
      onUploadClose();
      loadFolders();
      loadAllAudios();
    } else {
      toast.error(result.error || "Failed to upload audio");
    }
  };

  const handleDelete = async (audio: AudioFile) => {
    if (!confirm(`Delete ${getDisplayName(audio)}?`)) return;

    const success = await deleteFile(audio.filepath);

    if (success) {
      toast.success("Audio deleted successfully");
      loadFolders();
      loadAllAudios();
    } else {
      toast.error("Failed to delete audio");
    }
  };

  const handleBulkDelete = async () => {
    const selection = selectedAudios === "all" ? audios.map(a => a.filepath) : Array.from(selectedAudios);
    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected audios?`)) return;

    let successCount = 0;
    for (const filepath of selection) {
      const success = await deleteFile(filepath as string);
      if (success) successCount++;
    }

    setSelectedAudios(new Set<string>());

    if (successCount === selection.length) {
      toast.success(`Deleted ${successCount} audio files successfully`);
    } else if (successCount > 0) {
      toast.warning(`Deleted ${successCount} of ${selection.length} audio files`);
    } else {
      toast.error("Failed to delete audio files");
    }

    loadFolders();
    loadAllAudios();
  };

  const handleBulkMove = async () => {
    toast.info("Bulk move not yet implemented");
    onMoveClose();
  };

  const handleRename = async () => {
    toast.info("Rename not yet implemented");
    onRenameClose();
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

  const getDisplayName = (audio: AudioFile): string => {
    return (audio as any).metadata?.original_filename || audio.filename;
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
              type="file"
              accept=".mp3,.wav,.m4a,.aac,.flac"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
            {isUploading && (
              <div className="mt-2">
                <p className="text-sm text-default-500 mb-1">Uploading: {uploadProgress}%</p>
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
          <ModalHeader>{previewAudio ? getDisplayName(previewAudio) : ""}</ModalHeader>
          <ModalBody>
            {previewAudio && (
              <audio
                controls
                className="w-full"
                src={getAudioStreamUrl(previewAudio.filepath)}
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
