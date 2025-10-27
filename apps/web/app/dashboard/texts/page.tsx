"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Card, CardBody } from "@heroui/card";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Chip } from "@heroui/chip";
import { Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from "@heroui/table";
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from "@heroui/dropdown";
import type { Selection } from "@heroui/table";
import { useFiles, useUpload, useToast } from "@/lib/hooks";

interface CSVFile {
  filename: string;
  filepath: string;
  size: number;
  modified: string;
  type: string;
  metadata?: {
    original_filename?: string;
  };
}

export default function TextsPage() {
  const { getToken } = useAuth();
  const { listFiles, deleteFile, getCsvPreviewUrl } = useFiles();
  const { uploadFile, uploadProgress, isUploading } = useUpload();
  const toast = useToast();

  const [csvFiles, setCsvFiles] = useState<CSVFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCSVs, setSelectedCSVs] = useState<Selection>(new Set());
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [combinations, setCombinations] = useState<string[][]>([]);
  const [previewCSV, setPreviewCSV] = useState<CSVFile | null>(null);
  const [previewContent, setPreviewContent] = useState<string[][]>([]);
  const [loadingPreviewPath, setLoadingPreviewPath] = useState<string | null>(null);

  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();

  useEffect(() => {
    loadCSVFiles();
  }, []);

  const loadCSVFiles = async () => {
    setLoading(true);
    const response = await listFiles("csv");
    setLoading(false);

    if (response) {
      setCsvFiles(response.files as unknown as CSVFile[]);
      setSelectedCSVs(new Set<string>());
    } else {
      toast.error("Failed to load CSV files");
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const result = await uploadFile(selectedFile, "csv");

    if (result.success) {
      toast.success("CSV file uploaded successfully");
      setSelectedFile(null);
      onClose();
      loadCSVFiles();
    } else {
      toast.error(result.error || "Failed to upload CSV file");
    }
  };

  const handleDelete = async (csv: CSVFile) => {
    if (!confirm(`Delete ${getDisplayName(csv)}?`)) return;

    const success = await deleteFile(csv.filepath);

    if (success) {
      toast.success("CSV file deleted successfully");
      loadCSVFiles();
    } else {
      toast.error("Failed to delete CSV file");
    }
  };

  const handleBulkDelete = async () => {
    const selection = selectedCSVs === "all" ? csvFiles.map(c => c.filepath) : Array.from(selectedCSVs);
    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected CSV files?`)) return;

    let successCount = 0;
    for (const filepath of selection) {
      const success = await deleteFile(filepath as string);
      if (success) successCount++;
    }

    setSelectedCSVs(new Set<string>());

    if (successCount === selection.length) {
      toast.success(`Deleted ${successCount} CSV files successfully`);
    } else if (successCount > 0) {
      toast.warning(`Deleted ${successCount} of ${selection.length} CSV files`);
    } else {
      toast.error("Failed to delete CSV files");
    }

    loadCSVFiles();
  };

  const openPreview = async (csv: CSVFile) => {
    setLoadingPreviewPath(csv.filepath);
    try {
      const url = getCsvPreviewUrl(csv.filepath);

      // Get auth token
      const token = await getToken();

      if (!token) {
        toast.error("Not authenticated");
        return;
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewContent(data.combinations || []);
        setPreviewCSV(csv);
        onPreviewOpen();
      } else {
        const errorText = await response.text();
        console.error("Preview error:", errorText);
        toast.error("Failed to load CSV preview");
      }
    } catch (error) {
      console.error("Preview exception:", error);
      toast.error("Error loading CSV preview");
    } finally {
      setLoadingPreviewPath(null);
    }
  };

  const getSelectedCount = () => {
    return selectedCSVs === "all" ? csvFiles.length : selectedCSVs.size;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
  };

  const getDisplayName = (csv: CSVFile) => {
    return csv.metadata?.original_filename || csv.filename;
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Text Combinations</h1>
          <p className="text-default-500">Manage your CSV text files</p>
        </div>
        <div className="flex gap-2">
          <Button onPress={onOpen} color="primary">
            Upload CSV
          </Button>
        </div>
      </div>

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
            variant="flat"
            onPress={() => setSelectedCSVs(new Set<string>())}
          >
            Clear Selection
          </Button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">
          <p className="text-default-500">Loading CSV files...</p>
        </div>
      ) : csvFiles.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-default-400 mb-4">No CSV files uploaded yet</p>
          <Button onPress={onOpen} color="primary" variant="flat">
            Upload Your First CSV
          </Button>
        </div>
      ) : (
        <Table
          aria-label="CSV files table"
          selectionMode="multiple"
          selectedKeys={selectedCSVs}
          onSelectionChange={setSelectedCSVs}
          classNames={{
            wrapper: "min-h-[400px]",
          }}
        >
          <TableHeader>
            <TableColumn>NAME</TableColumn>
            <TableColumn>SIZE</TableColumn>
            <TableColumn>MODIFIED</TableColumn>
            <TableColumn>ACTIONS</TableColumn>
          </TableHeader>
          <TableBody items={csvFiles}>
            {(csv) => (
              <TableRow key={csv.filepath}>
                <TableCell>
                  <div className="max-w-xs">
                    <p className="text-sm font-medium truncate">{getDisplayName(csv)}</p>
                  </div>
                </TableCell>
                <TableCell>
                  <p className="text-sm text-default-500">{formatFileSize(csv.size)}</p>
                </TableCell>
                <TableCell>
                  <p className="text-sm text-default-500">{formatDate(csv.modified)}</p>
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="flat"
                      onPress={() => openPreview(csv)}
                      isLoading={loadingPreviewPath === csv.filepath}
                      isDisabled={loadingPreviewPath !== null && loadingPreviewPath !== csv.filepath}
                    >
                      Preview
                    </Button>
                    <Dropdown>
                      <DropdownTrigger>
                        <Button size="sm" variant="flat">⋮</Button>
                      </DropdownTrigger>
                      <DropdownMenu>
                        <DropdownItem onPress={() => handleDelete(csv)} className="text-danger" color="danger">
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

      {combinations.length > 0 && (
        <div className="mt-8">
          <Card>
            <CardBody>
              <h3 className="font-semibold mb-4">
                Last Upload: {combinations.length} text combinations
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {combinations.slice(0, 10).map((combo, i) => (
                  <div key={i} className="p-2 bg-default-100 rounded text-sm">
                    {combo[0]}
                  </div>
                ))}
                {combinations.length > 10 && (
                  <p className="text-xs text-default-400">
                    And {combinations.length - 10} more...
                  </p>
                )}
              </div>
            </CardBody>
          </Card>
        </div>
      )}

      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalContent>
          <ModalHeader>Upload CSV File</ModalHeader>
          <ModalBody>
            <p className="text-sm text-default-500 mb-2">
              Upload a CSV file with text combinations. Each row will be used as a text segment.
            </p>
            <Input
              type="file"
              accept=".csv"
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
            <Button variant="light" onPress={onClose} isDisabled={isUploading}>
              Cancel
            </Button>
            <Button
              color="primary"
              onPress={handleUpload}
              isLoading={isUploading}
              isDisabled={!selectedFile}
            >
              Upload
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="3xl">
        <ModalContent>
          <ModalHeader>{previewCSV ? getDisplayName(previewCSV) : ""}</ModalHeader>
          <ModalBody>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {previewContent.slice(0, 20).map((combo, i) => (
                <div key={i} className="p-2 bg-default-100 rounded text-sm">
                  {combo[0]}
                </div>
              ))}
              {previewContent.length > 20 && (
                <p className="text-xs text-default-400">
                  And {previewContent.length - 20} more combinations...
                </p>
              )}
            </div>
          </ModalBody>
          <ModalFooter>
            <Button onPress={onPreviewClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
