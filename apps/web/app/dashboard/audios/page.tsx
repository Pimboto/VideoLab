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
  const { listFiles, deleteFile, bulkDeleteFiles, bulkMoveFiles, renameFile, getAudioStreamUrl } = useFiles();
  const { listFolders, createFolder, deleteFolder } = useFolders();
  const { uploadFile, uploadMultipleFiles, uploadProgress, isUploading } = useUpload();
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
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
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
    const response = await listFiles("audios", selectedFolder);
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
    const result = await deleteFolder("audios", folderName);
    if (result) {
      toast.success(`Folder "${folderName}" deleted successfully. ${result.files_deleted} file(s) removed.`);
      loadFolders();
      loadAllAudios();
    } else {
      toast.error("Failed to delete folder");
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || !uploadFolder) return;

    // Upload multiple files sequentially with progress
    const results = await uploadMultipleFiles(selectedFiles, "audio", uploadFolder);

    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    if (successCount === selectedFiles.length) {
      toast.success(`Successfully uploaded ${successCount} audio file${successCount > 1 ? 's' : ''}`);
    } else if (successCount > 0) {
      toast.warning(`Uploaded ${successCount} audio file(s), ${failCount} failed`);
    } else {
      toast.error("Failed to upload audio files");
    }

    setSelectedFiles([]);
    setUploadFolder("");
    onUploadClose();
    loadFolders();
    loadAllAudios();
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

    // Use bulk delete endpoint (best practice - single request instead of loop)
    const result = await bulkDeleteFiles(selection as string[]);

    setSelectedAudios(new Set<string>());

    if (result.deleted === selection.length) {
      toast.success(`Deleted ${result.deleted} audio files successfully`);
    } else if (result.deleted > 0) {
      toast.warning(`Deleted ${result.deleted} of ${selection.length} audio files. ${result.failed} failed.`);
    } else {
      toast.error("Failed to delete audio files");
    }

    loadFolders();
    loadAllAudios();
  };

  const handleBulkMove = async () => {
    const selection = selectedAudios === "all" ? audios.map(a => a.filepath) : Array.from(selectedAudios);
    if (selection.length === 0 || !moveToFolder) return;

    const result = await bulkMoveFiles(selection as string[], moveToFolder);

    setSelectedAudios(new Set<string>());
    setMoveToFolder("");
    onMoveClose();

    if (result.moved === selection.length) {
      toast.success(`Moved ${result.moved} audio files successfully to "${moveToFolder}"`);
    } else if (result.moved > 0) {
      toast.warning(`Moved ${result.moved} of ${selection.length} audio files. ${result.failed} failed.`);
    } else {
      toast.error("Failed to move audio files");
    }

    loadFolders();
    loadAllAudios();
  };

  const handleRename = async () => {
    if (!renameAudio || !newName.trim()) return;

    const success = await renameFile(renameAudio.filepath, newName);

    if (success) {
      toast.success("Audio renamed successfully");
      setRenameAudio(null);
      setNewName("");
      onRenameClose();
      loadAllAudios();
    } else {
      toast.error("Failed to rename audio");
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
