"use client";

import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Card, CardBody } from "@heroui/card";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Chip } from "@heroui/chip";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CSVFile {
  filename: string;
  filepath: string;
  size: number;
  modified: string;
  type: string;
}

export default function TextsPage() {
  const [csvFiles, setCsvFiles] = useState<CSVFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [combinations, setCombinations] = useState<string[][]>([]);
  const [previewCSV, setPreviewCSV] = useState<CSVFile | null>(null);
  const [previewContent, setPreviewContent] = useState<string[][]>([]);

  useEffect(() => {
    loadCSVFiles();
  }, []);

  const loadCSVFiles = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/csv`);
      const data = await res.json();
      setCsvFiles(data.files || []);
    } catch (error) {
      console.error("Error loading CSV files:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("save_file", "true");

      const res = await fetch(`${API_URL}/api/video-processor/files/upload/csv`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setCombinations(data.combinations || []);
        setSelectedFile(null);
        onClose();
        loadCSVFiles();
      }
    } catch (error) {
      console.error("Error uploading CSV:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (csv: CSVFile) => {
    if (!confirm(`Delete ${csv.filename}?`)) return;

    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/delete`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filepath: csv.filepath })
      });

      if (res.ok) {
        loadCSVFiles();
      }
    } catch (error) {
      console.error("Error deleting CSV:", error);
    }
  };

  const openPreview = async (csv: CSVFile) => {
    try {
      const formData = new FormData();
      const blob = await fetch(`file://${csv.filepath}`).then(r => r.blob());
      formData.append("file", blob, csv.filename);
      formData.append("save_file", "false");

      const res = await fetch(`${API_URL}/api/video-processor/files/upload/csv`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setPreviewContent(data.combinations || []);
        setPreviewCSV(csv);
        onPreviewOpen();
      }
    } catch (error) {
      console.error("Error loading CSV preview:", error);
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Text Combinations</h1>
          <p className="text-default-500">Manage your CSV text files</p>
        </div>
        <Button onPress={onOpen} color="primary">
          Upload CSV
        </Button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : csvFiles.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-default-400 mb-4">No CSV files uploaded yet</p>
          <Button onPress={onOpen} color="primary" variant="flat">
            Upload Your First CSV
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {csvFiles.map((csv) => (
            <Card key={csv.filepath}>
              <CardBody className="gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-warning/20 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">📝</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-sm truncate">{csv.filename}</h4>
                    <p className="text-xs text-default-500">
                      {(csv.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="flat" className="flex-1" onPress={() => openPreview(csv)}>
                    Preview
                  </Button>
                  <Button size="sm" color="danger" variant="flat" onPress={() => handleDelete(csv)}>
                    Delete
                  </Button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
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
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onClose}>
              Cancel
            </Button>
            <Button color="primary" onPress={handleUpload} isLoading={uploading}>
              Upload
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="3xl">
        <ModalContent>
          <ModalHeader>{previewCSV?.filename}</ModalHeader>
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
