"use client";

import type { Selection } from "@heroui/table";
import type { AudioFile, BaseFile, Folder } from "@/lib/types";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@heroui/button";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
} from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Input } from "@heroui/input";
import { Pagination } from "@heroui/pagination";

import FileTable from "@/components/Dashboard/FileTable";
import FolderSidebar from "@/components/Dashboard/FolderSidebar";
import BulkActions from "@/components/Dashboard/BulkActions";
import { useFiles, useFolders, useUpload, useToast } from "@/lib/hooks";
import { useAudioStreamUrls } from "@/lib/hooks/useVideoStreamUrl";

const AUDIO_COLUMNS = [
  { key: "name", label: "NAME" },
  { key: "size", label: "SIZE" },
  { key: "modified", label: "MODIFIED" },
  { key: "actions", label: "ACTIONS" },
];

export default function AudiosPage() {
  const { listFiles, deleteFile, bulkDeleteFiles, bulkMoveFiles, renameFile } =
    useFiles();
  const { listFolders, createFolder, deleteFolder } = useFolders();
  const { uploadMultipleFiles, uploadProgress, isUploading } = useUpload();
  const toast = useToast();

  const [folders, setFolders] = useState<Folder[]>([]);
  const [audios, setAudios] = useState<AudioFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedAudios, setSelectedAudios] = useState<Selection>(new Set());

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 20;

  const {
    isOpen: isUploadOpen,
    onOpen: onUploadOpen,
    onClose: onUploadClose,
  } = useDisclosure();
  const {
    isOpen: isPreviewOpen,
    onOpen: onPreviewOpen,
    onClose: onPreviewClose,
  } = useDisclosure();
  const {
    isOpen: isRenameOpen,
    onOpen: onRenameOpen,
    onClose: onRenameClose,
  } = useDisclosure();
  const {
    isOpen: isMoveOpen,
    onOpen: onMoveOpen,
    onClose: onMoveClose,
  } = useDisclosure();

  const [uploadFolder, setUploadFolder] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewAudio, setPreviewAudio] = useState<AudioFile | null>(null);
  const [renameAudio, setRenameAudio] = useState<AudioFile | null>(null);
  const [newName, setNewName] = useState("");
  const [fileExtension, setFileExtension] = useState("");
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
    setCurrentPage(1); // Reset to first page when changing folders
    const response = await listFiles("audios", selectedFolder);

    setLoading(false);

    if (response) {
      setAudios(response.files as unknown as AudioFile[]);
      setSelectedAudios(new Set<string>());
    } else {
      toast.error("Failed to load audio files");
    }
  };

  // Calculate pagination
  const totalPages = Math.ceil(audios.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const visibleAudios = audios.slice(startIndex, endIndex);

  // Load stream URLs ONLY for visible audios (huge performance improvement!)
  const visibleFilepaths = visibleAudios.map((a) => a.filepath);
  const { urls: audioUrls, isLoading: urlsLoading } =
    useAudioStreamUrls(visibleFilepaths);

  const handleCreateFolder = async (folderName: string) => {
    const result = await createFolder("audios", folderName);

    if (result) {
      toast.success("Folder created successfully");
      loadFolders();
    } else {
      toast.error("Failed to create folder");
    }
  };

  const handleRenameFolder = async (_oldName: string, _newName: string) => {
    toast.info("Folder rename not yet implemented");
  };

  const handleDeleteFolder = async (folderName: string) => {
    const result = await deleteFolder("audios", folderName);

    if (result) {
      toast.success(
        `Folder "${folderName}" deleted successfully. ${result.files_deleted} file(s) removed.`,
      );
      loadFolders();
      loadAllAudios();
    } else {
      toast.error("Failed to delete folder");
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || !uploadFolder) return;

    // Upload multiple files sequentially with progress
    const results = await uploadMultipleFiles(
      selectedFiles,
      "audio",
      uploadFolder,
    );

    const successCount = results.filter((r) => r.success).length;
    const failCount = results.filter((r) => !r.success).length;

    if (successCount === selectedFiles.length) {
      toast.success(
        `Successfully uploaded ${successCount} audio file${successCount > 1 ? "s" : ""}`,
      );
    } else if (successCount > 0) {
      toast.warning(
        `Uploaded ${successCount} audio file(s), ${failCount} failed`,
      );
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
    const selection =
      selectedAudios === "all"
        ? audios.map((a) => a.filepath)
        : Array.from(selectedAudios);

    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected audios?`)) return;

    // Use bulk delete endpoint (best practice - single request instead of loop)
    const result = await bulkDeleteFiles(selection as string[]);

    setSelectedAudios(new Set<string>());

    if (result.deleted === selection.length) {
      toast.success(`Deleted ${result.deleted} audio files successfully`);
    } else if (result.deleted > 0) {
      toast.warning(
        `Deleted ${result.deleted} of ${selection.length} audio files. ${result.failed} failed.`,
      );
    } else {
      toast.error("Failed to delete audio files");
    }

    loadFolders();
    loadAllAudios();
  };

  const handleBulkMove = async () => {
    const selection =
      selectedAudios === "all"
        ? audios.map((a) => a.filepath)
        : Array.from(selectedAudios);

    if (selection.length === 0 || !moveToFolder) return;

    const result = await bulkMoveFiles(selection as string[], moveToFolder);

    setSelectedAudios(new Set<string>());
    setMoveToFolder("");
    onMoveClose();

    if (result.moved === selection.length) {
      toast.success(
        `Moved ${result.moved} audio files successfully to "${moveToFolder}"`,
      );
    } else if (result.moved > 0) {
      toast.warning(
        `Moved ${result.moved} of ${selection.length} audio files. ${result.failed} failed.`,
      );
    } else {
      toast.error("Failed to move audio files");
    }

    loadFolders();
    loadAllAudios();
  };

  const handleRename = async () => {
    if (!renameAudio || !newName.trim()) return;

    // Add extension back to the new name
    const newNameWithExtension = newName + fileExtension;
    const success = await renameFile(
      renameAudio.filepath,
      newNameWithExtension,
    );

    if (success) {
      toast.success("Audio renamed successfully");
      setRenameAudio(null);
      setNewName("");
      setFileExtension("");
      onRenameClose();
      // Reload audios to show updated name
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

    // Get display name (without timestamp if it's metadata)
    const displayName = getDisplayName(audio);

    // Extract name without extension
    const extensionMatch = displayName.match(/\.[^/.]+$/);
    const extension = extensionMatch ? extensionMatch[0] : ".mp3";
    const nameWithoutExt = displayName.replace(/\.[^/.]+$/, "");

    setNewName(nameWithoutExt);
    setFileExtension(extension);
    onRenameOpen();
  };

  const getDisplayName = (audio: AudioFile): string => {
    return (audio as any).metadata?.original_filename || audio.filename;
  };

  const rowActions = useMemo(
    () => [
      {
        label: "Rename",
        onClick: (file: BaseFile) => openRename(file as AudioFile),
        color: "default" as const,
      },
      {
        label: "Delete",
        onClick: (file: BaseFile) => handleDelete(file as AudioFile),
        color: "danger" as const,
      },
    ],
    [],
  );

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
        <Button color="primary" onPress={onUploadOpen}>
          Upload Audio
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <FolderSidebar
            folders={folders}
            selectedFolder={selectedFolder}
            title="Audio Folders"
            totalCount={getTotalCount()}
            onCreateFolder={handleCreateFolder}
            onDeleteFolder={handleDeleteFolder}
            onRenameFolder={handleRenameFolder}
            onSelectFolder={setSelectedFolder}
          />
        </div>

        <div className="lg:col-span-3">
          <BulkActions
            actions={[
              {
                label: "Move Selected",
                onClick: onMoveOpen,
                color: "primary",
              },
              {
                label: "Delete Selected",
                onClick: handleBulkDelete,
                color: "danger",
              },
            ]}
            selectedCount={getSelectedCount()}
            onClear={() => setSelectedAudios(new Set<string>())}
          />

          <FileTable
            columns={AUDIO_COLUMNS}
            emptyMessage="No audios in this folder"
            files={visibleAudios}
            loading={loading || urlsLoading}
            primaryAction={{
              label: "Play",
              onClick: (file: BaseFile) => openPreview(file as AudioFile),
            }}
            rowActions={rowActions}
            selectedKeys={selectedAudios}
            onSelectionChange={setSelectedAudios}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center mt-6">
              <Pagination
                showControls
                color="primary"
                page={currentPage}
                size="lg"
                total={totalPages}
                onChange={setCurrentPage}
              />
            </div>
          )}

          {/* Stats */}
          <div className="text-center text-sm text-default-500 mt-4">
            Showing {startIndex + 1}-{Math.min(endIndex, audios.length)} of{" "}
            {audios.length} audios
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <Modal isOpen={isUploadOpen} onClose={onUploadClose}>
        <ModalContent>
          <ModalHeader>Upload Audio</ModalHeader>
          <ModalBody>
            <Select
              isRequired
              description="Audios will be uploaded to this folder"
              label="Select Folder"
              placeholder="Choose folder"
              selectedKeys={uploadFolder ? [uploadFolder] : []}
              onSelectionChange={(keys) =>
                setUploadFolder(Array.from(keys)[0] as string)
              }
            >
              {folders.map((folder) => (
                <SelectItem key={folder.name}>{folder.name}</SelectItem>
              ))}
            </Select>
            <Input
              multiple
              accept=".mp3,.wav,.m4a,.aac,.flac"
              onChange={(e) => {
                const files = e.target.files;
                if (files) {
                  setSelectedFiles(Array.from(files));
                }
              }}
              // @ts-ignore - multiple attribute is valid
              type="file"
            />
            {selectedFiles.length > 0 && (
              <div className="text-sm text-default-500">
                {selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""}{" "}
                selected
              </div>
            )}
            {isUploading && (
              <div className="mt-2">
                <p className="text-sm text-default-500 mb-1">
                  Uploading: {uploadProgress}%
                  {uploadProgress >= 80 &&
                    uploadProgress < 100 &&
                    " (Processing on server...)"}
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
            <Button
              isDisabled={isUploading}
              variant="light"
              onPress={onUploadClose}
            >
              Cancel
            </Button>
            <Button
              color="primary"
              isDisabled={!uploadFolder || selectedFiles.length === 0}
              isLoading={isUploading}
              onPress={handleUpload}
            >
              Upload{" "}
              {selectedFiles.length > 1 ? `${selectedFiles.length} Files` : ""}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Preview Modal */}
      <Modal isOpen={isPreviewOpen} size="3xl" onClose={onPreviewClose}>
        <ModalContent>
          <ModalHeader>
            {previewAudio ? getDisplayName(previewAudio) : ""}
          </ModalHeader>
          <ModalBody>
            {previewAudio && audioUrls[previewAudio.filepath] ? (
              <div className="flex flex-col items-center gap-4 p-8">
                <div className="text-6xl">🎵</div>
                <audio
                  autoPlay
                  controls
                  className="w-full"
                  src={audioUrls[previewAudio.filepath] ?? undefined}
                >
                  <track kind="captions" />
                  Your browser does not support audio playback.
                </audio>
              </div>
            ) : (
              <div className="flex items-center justify-center min-h-[200px]">
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                  <p className="text-default-500">Loading audio...</p>
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
          <ModalHeader>Rename Audio</ModalHeader>
          <ModalBody>
            <Input
              description="File extension cannot be changed"
              endContent={
                <span className="text-default-400 text-sm whitespace-nowrap">
                  {fileExtension}
                </span>
              }
              label="New Name"
              placeholder="Enter new name (without extension)"
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
              onSelectionChange={(keys) =>
                setMoveToFolder(Array.from(keys)[0] as string)
              }
            >
              {folders
                .filter((f) => f.name !== selectedFolder)
                .map((folder) => (
                  <SelectItem key={folder.name}>{folder.name}</SelectItem>
                ))}
            </Select>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onMoveClose}>
              Cancel
            </Button>
            <Button
              color="primary"
              isDisabled={!moveToFolder}
              onPress={handleBulkMove}
            >
              Move
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
