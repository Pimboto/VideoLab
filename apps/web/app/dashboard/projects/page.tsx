"use client";

import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from "@heroui/table";
import { Chip } from "@heroui/chip";
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from "@heroui/dropdown";
import type { Selection } from "@heroui/table";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PROJECT_COLUMNS = [
  { key: "preview", label: "PREVIEW" },
  { key: "name", label: "NAME" },
  { key: "folder", label: "FOLDER" },
  { key: "size", label: "SIZE" },
  { key: "modified", label: "MODIFIED" },
  { key: "actions", label: "ACTIONS" }
] as const;

interface OutputFile {
  filename: string;
  filepath: string;
  size: number;
  modified: string;
  folder: string;
}

export default function ProjectsPage() {
  const [outputs, setOutputs] = useState<OutputFile[]>([]);
  const [folders, setFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>("all");
  const [loading, setLoading] = useState(false);
  const [previewVideo, setPreviewVideo] = useState<OutputFile | null>(null);
  const [selectedOutputs, setSelectedOutputs] = useState<Selection>(new Set());
  const [mounted, setMounted] = useState(false);

  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();

  useEffect(() => {
    setMounted(true);
    loadOutputs();
  }, []);

  useEffect(() => {
    // Extract unique folders from outputs
    const uniqueFolders = Array.from(new Set(outputs.map(o => o.folder).filter(Boolean)));
    setFolders(uniqueFolders);
  }, [outputs]);

  const loadOutputs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/outputs`);
      if (res.ok) {
        const data = await res.json();
        setOutputs(data.files || []);
        setSelectedOutputs(new Set<string>());
      }
    } catch (error) {
      console.error("Error loading projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredOutputs = selectedFolder === "all"
    ? outputs
    : outputs.filter(o => o.folder === selectedFolder);

  const handleDownload = (output: OutputFile) => {
    const link = document.createElement("a");
    link.href = `${API_URL}/api/video-processor/files/stream/video?filepath=${encodeURIComponent(output.filepath)}`;
    link.download = output.filename;
    link.click();
  };

  const handleBulkDownload = async () => {
    const selection = selectedOutputs === "all" ? filteredOutputs.map(o => o.filepath) : Array.from(selectedOutputs);
    if (selection.length === 0) return;

    // Download each file one by one
    for (const filepath of selection) {
      const output = outputs.find(o => o.filepath === filepath);
      if (output) {
        handleDownload(output);
        // Small delay between downloads
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  const handleDownloadFolder = async () => {
    if (selectedFolder === "all") return;

    const folderOutputs = outputs.filter(o => o.folder === selectedFolder);
    if (folderOutputs.length === 0) return;

    if (!confirm(`Download all ${folderOutputs.length} files from "${selectedFolder}" folder?`)) return;

    for (const output of folderOutputs) {
      handleDownload(output);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  const handleDelete = async (output: OutputFile) => {
    if (!confirm(`Delete ${output.filename}?`)) return;

    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/delete`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filepath: output.filepath })
      });

      if (res.ok) {
        loadOutputs();
      }
    } catch (error) {
      console.error("Error deleting output:", error);
    }
  };

  const handleBulkDelete = async () => {
    const selection = selectedOutputs === "all" ? filteredOutputs.map(o => o.filepath) : Array.from(selectedOutputs);
    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected projects?`)) return;

    try {
      const deletePromises = selection.map(filepath =>
        fetch(`${API_URL}/api/video-processor/files/delete`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filepath })
        })
      );

      await Promise.all(deletePromises);
      setSelectedOutputs(new Set<string>());
      loadOutputs();
    } catch (error) {
      console.error("Error deleting outputs:", error);
    }
  };

  const openPreview = (output: OutputFile) => {
    setPreviewVideo(output);
    onPreviewOpen();
  };

  const getSelectedCount = () => {
    return selectedOutputs === "all" ? filteredOutputs.length : selectedOutputs.size;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Projects</h1>
          <p className="text-default-500">View and download your processed videos</p>
        </div>
        <Button onPress={loadOutputs} variant="flat">
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - Folders Filter */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h3 className="font-semibold">Folders</h3>
            </CardHeader>
            <CardBody className="gap-2">
              <Button
                variant={selectedFolder === "all" ? "flat" : "light"}
                color={selectedFolder === "all" ? "primary" : "default"}
                className="justify-start"
                onPress={() => setSelectedFolder("all")}
              >
                All Projects
                <Chip size="sm" variant="flat" className="ml-auto">
                  {outputs.length}
                </Chip>
              </Button>
              {folders.map((folder) => {
                const count = outputs.filter(o => o.folder === folder).length;
                return (
                  <div key={folder} className="flex items-center gap-2">
                    <Button
                      variant={selectedFolder === folder ? "flat" : "light"}
                      color={selectedFolder === folder ? "primary" : "default"}
                      className="justify-start flex-1"
                      onPress={() => setSelectedFolder(folder)}
                    >
                      {folder}
                      <Chip size="sm" variant="flat" className="ml-auto">
                        {count}
                      </Chip>
                    </Button>
                    <Dropdown>
                      <DropdownTrigger>
                        <Button size="sm" variant="light" isIconOnly>
                          ⋮
                        </Button>
                      </DropdownTrigger>
                      <DropdownMenu>
                        <DropdownItem
                          onPress={() => {
                            setSelectedFolder(folder);
                            setTimeout(handleDownloadFolder, 100);
                          }}
                        >
                          Download All ({count})
                        </DropdownItem>
                      </DropdownMenu>
                    </Dropdown>
                  </div>
                );
              })}
            </CardBody>
          </Card>
        </div>

        {/* Main Content - Table */}
        <div className="lg:col-span-3">
          {getSelectedCount() > 0 && (
            <div className="mb-4 flex gap-2 items-center bg-default-100 p-3 rounded-lg">
              <Chip color="primary">{getSelectedCount()} selected</Chip>
              <Button
                size="sm"
                color="primary"
                variant="flat"
                onPress={handleBulkDownload}
              >
                Download Selected
              </Button>
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
                variant="flat"
                onPress={() => setSelectedOutputs(new Set<string>())}
              >
                Clear Selection
              </Button>
            </div>
          )}

          {!mounted ? (
            <div className="flex items-center justify-center min-h-[400px]">
              <p className="text-default-500">Loading...</p>
            </div>
          ) : (
            <Table
              aria-label="Projects table"
              selectionMode="multiple"
              selectedKeys={selectedOutputs}
              onSelectionChange={setSelectedOutputs}
              classNames={{
                wrapper: "min-h-[400px]",
              }}
            >
              <TableHeader columns={PROJECT_COLUMNS}>
                {(column) => (
                  <TableColumn key={column.key}>
                    {column.label}
                  </TableColumn>
                )}
              </TableHeader>
              <TableBody
                items={filteredOutputs}
                emptyContent={loading ? "Loading..." : "No projects in this folder"}
              >
                {(output) => (
                  <TableRow key={output.filepath}>
                    <TableCell>
                      <div
                        className="w-20 h-12 bg-black rounded overflow-hidden cursor-pointer hover:opacity-80 transition"
                        onClick={() => openPreview(output)}
                      >
                        <video
                          className="w-full h-full object-cover"
                          src={`${API_URL}/api/video-processor/files/stream/video?filepath=${encodeURIComponent(output.filepath)}#t=0.1`}
                          preload="metadata"
                          muted
                          playsInline
                        />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="max-w-xs">
                        <p className="text-sm font-medium truncate">{output.filename}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Chip size="sm" variant="flat" color="secondary">
                        {output.folder || "No folder"}
                      </Chip>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-default-500">{formatFileSize(output.size)}</p>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-default-500">{formatDate(output.modified)}</p>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button size="sm" variant="flat" onPress={() => openPreview(output)}>
                          Preview
                        </Button>
                        <Dropdown>
                          <DropdownTrigger>
                            <Button size="sm" variant="flat">⋮</Button>
                          </DropdownTrigger>
                          <DropdownMenu>
                            <DropdownItem onPress={() => handleDownload(output)}>Download</DropdownItem>
                            <DropdownItem onPress={() => handleDelete(output)} className="text-danger" color="danger">
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
          )}
        </div>
      </div>

      {mounted && (
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
              <Button variant="light" onPress={onPreviewClose}>
                Close
              </Button>
              <Button color="primary" onPress={() => previewVideo && handleDownload(previewVideo)}>
                Download
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      )}
    </div>
  );
}
