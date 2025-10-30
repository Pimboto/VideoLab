"use client";

import type { Folder } from "@/lib/types";

import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Chip } from "@heroui/chip";
import {
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
} from "@heroui/dropdown";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
} from "@heroui/modal";
import { Input } from "@heroui/input";
import { Folder2, Edit, Trash, FolderAdd } from "iconsax-reactjs";

interface FolderSidebarProps {
  folders: Folder[];
  selectedFolder: string | null;
  onSelectFolder: (folderName: string | null) => void;
  onCreateFolder?: (folderName: string) => Promise<void>;
  onRenameFolder?: (oldName: string, newName: string) => Promise<void>;
  onDeleteFolder?: (folderName: string) => Promise<void>;
  showAllOption?: boolean;
  totalCount?: number;
  title?: string;
}

export default function FolderSidebar({
  folders,
  selectedFolder,
  onSelectFolder,
  onCreateFolder,
  onRenameFolder,
  onDeleteFolder,
  showAllOption = true,
  totalCount = 0,
  title = "Folders",
}: FolderSidebarProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const {
    isOpen: isCreateOpen,
    onOpen: onCreateOpen,
    onClose: onCreateClose,
  } = useDisclosure();
  const {
    isOpen: isRenameOpen,
    onOpen: onRenameOpen,
    onClose: onRenameClose,
  } = useDisclosure();
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const [newFolderName, setNewFolderName] = useState("");
  const [renamingFolder, setRenamingFolder] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [deletingFolder, setDeletingFolder] = useState<{
    name: string;
    fileCount: number;
  } | null>(null);

  const handleCreate = async () => {
    if (!newFolderName.trim() || !onCreateFolder) return;
    await onCreateFolder(newFolderName);
    setNewFolderName("");
    onCreateClose();
  };

  const handleRename = async () => {
    if (!renameValue.trim() || !renamingFolder || !onRenameFolder) return;
    await onRenameFolder(renamingFolder, renameValue);
    setRenamingFolder(null);
    setRenameValue("");
    onRenameClose();
  };

  const openRename = (folderName: string) => {
    setRenamingFolder(folderName);
    setRenameValue(folderName);
    onRenameOpen();
  };

  const openDelete = (folderName: string, fileCount: number) => {
    setDeletingFolder({ name: folderName, fileCount });
    onDeleteOpen();
  };

  const confirmDelete = async () => {
    if (!deletingFolder || !onDeleteFolder) return;
    await onDeleteFolder(deletingFolder.name);
    setDeletingFolder(null);
    onDeleteClose();
  };

  return (
    <>
      <Card className="border border-default-200">
        <CardHeader className="flex justify-between items-center pb-3">
          <h3 className="text-base font-semibold flex items-center gap-2">
            <Folder2 size={18} />
            {title}
          </h3>
          {onCreateFolder && (
            <Button
              isIconOnly
              className="hover:bg-primary/10"
              size="sm"
              variant="light"
              onPress={onCreateOpen}
            >
              <FolderAdd size={18} />
            </Button>
          )}
        </CardHeader>
        <CardBody className="gap-1 pt-0">
          {showAllOption && (
            <Button
              className="justify-start h-10"
              color={selectedFolder === null ? "primary" : "default"}
              variant={selectedFolder === null ? "flat" : "light"}
              onPress={() => onSelectFolder(null)}
            >
              <span className="flex-1 text-left">All Files</span>
              <Chip size="sm" variant="flat">
                {totalCount}
              </Chip>
            </Button>
          )}

          <div className="space-y-1">
            {folders.map((folder) => (
              <div key={folder.name} className="group flex items-center gap-1">
                <Button
                  className="justify-start flex-1 h-10"
                  color={selectedFolder === folder.name ? "primary" : "default"}
                  variant={selectedFolder === folder.name ? "flat" : "light"}
                  onPress={() => onSelectFolder(folder.name)}
                >
                  <span className="flex-1 text-left truncate">
                    {folder.name}
                  </span>
                  <Chip size="sm" variant="flat">
                    {folder.file_count}
                  </Chip>
                </Button>

                {(onRenameFolder || onDeleteFolder) && (
                  <Dropdown>
                    <DropdownTrigger>
                      <Button
                        isIconOnly
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        size="sm"
                        variant="light"
                      >
                        ⋮
                      </Button>
                    </DropdownTrigger>
                    <DropdownMenu>
                      {onRenameFolder ? (
                        <DropdownItem
                          key="rename"
                          startContent={<Edit size={16} />}
                          onPress={() => openRename(folder.name)}
                        >
                          Rename
                        </DropdownItem>
                      ) : null}
                      {onDeleteFolder ? (
                        <DropdownItem
                          key="delete"
                          className="text-danger"
                          color="danger"
                          startContent={<Trash size={16} />}
                          onPress={() =>
                            openDelete(folder.name, folder.file_count)
                          }
                        >
                          Delete
                        </DropdownItem>
                      ) : null}
                    </DropdownMenu>
                  </Dropdown>
                )}
              </div>
            ))}
          </div>

          {folders.length === 0 && (
            <p className="text-sm text-default-400 text-center py-4">
              No folders yet
            </p>
          )}
        </CardBody>
      </Card>

      {mounted && (
        <Modal isOpen={isCreateOpen} onClose={onCreateClose}>
          <ModalContent>
            <ModalHeader>Create New Folder</ModalHeader>
            <ModalBody>
              <Input
                id="new-folder-name"
                label="Folder Name"
                name="folderName"
                placeholder="Enter folder name"
                value={newFolderName}
                onValueChange={setNewFolderName}
              />
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onCreateClose}>
                Cancel
              </Button>
              <Button
                color="primary"
                isDisabled={!newFolderName.trim()}
                onPress={handleCreate}
              >
                Create
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      )}

      {mounted && (
        <Modal isOpen={isRenameOpen} onClose={onRenameClose}>
          <ModalContent>
            <ModalHeader>Rename Folder</ModalHeader>
            <ModalBody>
              <Input
                id="rename-folder-name"
                label="New Name"
                name="renameFolderName"
                placeholder="Enter new name"
                value={renameValue}
                onValueChange={setRenameValue}
              />
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onRenameClose}>
                Cancel
              </Button>
              <Button
                color="primary"
                isDisabled={!renameValue.trim()}
                onPress={handleRename}
              >
                Rename
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      )}

      {mounted && deletingFolder && (
        <Modal isOpen={isDeleteOpen} onClose={onDeleteClose}>
          <ModalContent>
            <ModalHeader className="text-danger">Delete Folder</ModalHeader>
            <ModalBody>
              <div className="space-y-2">
                <p>
                  Are you sure you want to delete the folder{" "}
                  <strong>&quot;{deletingFolder.name}&quot;</strong>?
                </p>
                {deletingFolder.fileCount > 0 && (
                  <div className="p-3 rounded-lg bg-danger-50 border border-danger-200">
                    <p className="text-sm text-danger-600">
                      <strong>Warning:</strong> This will permanently delete{" "}
                      {deletingFolder.fileCount} file
                      {deletingFolder.fileCount !== 1 ? "s" : ""} in this
                      folder.
                    </p>
                  </div>
                )}
                <p className="text-sm text-default-500">
                  This action cannot be undone.
                </p>
              </div>
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onDeleteClose}>
                Cancel
              </Button>
              <Button color="danger" onPress={confirmDelete}>
                Delete Folder
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      )}
    </>
  );
}
