"use client";

import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Card, CardBody } from "@heroui/card";
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from "@heroui/modal";
import { Skeleton } from "@heroui/skeleton";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface OutputFile {
  filename: string;
  filepath: string;
  size: number;
  modified: string;
  folder: string;
}

export default function ProjectsPage() {
  const [outputs, setOutputs] = useState<OutputFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewVideo, setPreviewVideo] = useState<OutputFile | null>(null);

  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();

  useEffect(() => {
    loadOutputs();
  }, []);

  const loadOutputs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/video-processor/files/outputs`);
      if (res.ok) {
        const data = await res.json();
        setOutputs(data.files || []);
      }
    } catch (error) {
      console.error("Error loading projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (output: OutputFile) => {
    // Trigger download
    const link = document.createElement("a");
    link.href = `${API_URL}/api/video-processor/files/stream/video?filepath=${encodeURIComponent(output.filepath)}`;
    link.download = output.filename;
    link.click();
  };

  const openPreview = (output: OutputFile) => {
    setPreviewVideo(output);
    onPreviewOpen();
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

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardBody className="gap-3">
                <Skeleton className="aspect-video rounded-lg" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-3/4 rounded" />
                  <Skeleton className="h-3 w-1/2 rounded" />
                </div>
                <div className="flex gap-2">
                  <Skeleton className="h-8 flex-1 rounded" />
                  <Skeleton className="h-8 w-20 rounded" />
                  <Skeleton className="h-8 w-20 rounded" />
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      ) : outputs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-default-400 mb-4">No projects yet</p>
          <p className="text-sm text-default-500">Create your first batch from the Create page</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {outputs.map((output) => (
            <Card key={output.filepath}>
              <CardBody className="gap-3">
                <div
                  className="aspect-video bg-black rounded-lg overflow-hidden cursor-pointer hover:opacity-90 transition relative group"
                  onClick={() => openPreview(output)}
                >
                  <video
                    className="w-full h-full object-cover"
                    src={`${API_URL}/api/video-processor/files/stream/video?filepath=${encodeURIComponent(output.filepath)}#t=0.1`}
                    preload="metadata"
                    muted
                    playsInline
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/30 group-hover:bg-black/50 transition pointer-events-none">
                    <div className="bg-success/90 rounded-full p-3 group-hover:scale-110 transition">
                      <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-sm truncate">{output.filename}</h4>
                  <p className="text-xs text-default-500">
                    {(output.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  {output.folder && (
                    <p className="text-xs text-default-400 mt-1">
                      📁 {output.folder}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="flat" className="flex-1" onPress={() => openPreview(output)}>
                    Preview
                  </Button>
                  <Button size="sm" color="primary" variant="flat" onPress={() => handleDownload(output)}>
                    Download
                  </Button>
                  <Button size="sm" color="danger" variant="flat" onPress={() => handleDelete(output)}>
                    Delete
                  </Button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

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
    </div>
  );
}
