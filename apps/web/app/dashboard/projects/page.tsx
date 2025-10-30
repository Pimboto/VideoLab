"use client";

import type { Selection } from "@heroui/table";
import type { Project } from "@/lib/api/client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { Button } from "@heroui/button";
import { Card, CardBody } from "@heroui/card";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
} from "@heroui/modal";
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
} from "@heroui/table";
import { Chip } from "@heroui/chip";
import {
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
} from "@heroui/dropdown";
import { Pagination } from "@heroui/pagination";
import Image from "next/image";

import {
  useProjects,
  useProjectUrls,
  useDeleteProject,
  useDownloadProject,
} from "@/lib/hooks";

const PROJECT_COLUMNS = [
  { key: "thumbnail", label: "PREVIEW" },
  { key: "name", label: "PROJECT NAME" },
  { key: "videos", label: "VIDEOS" },
  { key: "size", label: "SIZE" },
  { key: "created", label: "CREATED" },
  { key: "actions", label: "ACTIONS" },
];

function ProjectsPageContent() {
  // Fetch projects using TanStack Query
  const { data: projects = [], isLoading, error, refetch } = useProjects();

  const [selectedProjects, setSelectedProjects] = useState<Selection>(
    new Set(),
  );
  const [previewProject, setPreviewProject] = useState<Project | null>(null);
  const [mounted, setMounted] = useState(false);

  // Ensure client-side only rendering for time-sensitive data
  useEffect(() => {
    setMounted(true);
  }, []);

  const {
    isOpen: isPreviewOpen,
    onOpen: onPreviewOpen,
    onClose: onPreviewClose,
  } = useDisclosure();

  // Mutations
  const deleteProjectMutation = useDeleteProject();
  const downloadProjectMutation = useDownloadProject();

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 20;
  const totalPages = Math.ceil(projects.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const visibleProjects = projects.slice(startIndex, endIndex);

  const handlePreview = (project: Project) => {
    setPreviewProject(project);
    onPreviewOpen();
  };

  const handleDownload = async (project: Project) => {
    try {
      await downloadProjectMutation.mutateAsync({
        projectId: project.id,
        projectName: project.name,
      });
    } catch {
      // Error already handled by mutation
    }
  };

  const handleDelete = async (project: Project) => {
    if (!confirm(`Delete project "${project.name}"?`)) return;

    try {
      await deleteProjectMutation.mutateAsync({
        projectId: project.id,
        hardDelete: false, // Soft delete by default
      });
    } catch {
      // Error already handled by mutation
    }
  };

  const handleBulkDelete = async () => {
    const selection =
      selectedProjects === "all"
        ? visibleProjects.map((p) => p.id)
        : Array.from(selectedProjects);

    if (selection.length === 0) return;
    if (!confirm(`Delete ${selection.length} selected projects?`)) return;

    try {
      await Promise.all(
        selection.map((projectId) =>
          deleteProjectMutation.mutateAsync({ projectId: projectId as string }),
        ),
      );
      setSelectedProjects(new Set<string>());
    } catch {
      // Error already handled
    }
  };

  const getSelectedCount = () => {
    return selectedProjects === "all"
      ? visibleProjects.length
      : selectedProjects.size;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;

    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    // Use consistent UTC-based formatting to avoid hydration errors
    const year = date.getUTCFullYear();
    const month = date.toLocaleString("en-US", {
      month: "short",
      timeZone: "UTC",
    });
    const day = date.getUTCDate();
    const hours = date.getUTCHours().toString().padStart(2, "0");
    const minutes = date.getUTCMinutes().toString().padStart(2, "0");

    return `${month} ${day}, ${year} ${hours}:${minutes}`;
  };

  const getTimeUntilExpiration = (expiresAt: string | undefined) => {
    if (!expiresAt) return null;

    const now = new Date().getTime();
    const expiration = new Date(expiresAt).getTime();
    const diff = expiration - now;

    if (diff <= 0) return "Expired";

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `Expires in ${hours}h ${minutes}m`;
    } else {
      return `Expires in ${minutes}m`;
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Projects</h1>
          <p className="text-default-500">
            View and download your completed batch processing projects
          </p>
        </div>
        <Button isLoading={isLoading} variant="flat" onPress={() => refetch()}>
          Refresh
        </Button>
      </div>

      {/* Bulk Actions Bar */}
      {getSelectedCount() > 0 && (
        <div className="mb-4 flex gap-2 items-center bg-default-100 p-3 rounded-lg">
          <Chip color="primary">{getSelectedCount()} selected</Chip>
          <Button
            color="danger"
            isLoading={deleteProjectMutation.isPending}
            size="sm"
            variant="flat"
            onPress={handleBulkDelete}
          >
            Delete Selected
          </Button>
          <Button
            size="sm"
            variant="flat"
            onPress={() => setSelectedProjects(new Set<string>())}
          >
            Clear Selection
          </Button>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="mb-4 bg-danger-50 border-danger">
          <CardBody>
            <p className="text-danger">
              Error loading projects: {error.message}
            </p>
          </CardBody>
        </Card>
      )}

      {/* Projects Table */}
      <Table
        aria-label="Projects table"
        classNames={{
          wrapper: "min-h-[400px]",
        }}
        selectedKeys={selectedProjects}
        selectionMode="multiple"
        onSelectionChange={setSelectedProjects}
      >
        <TableHeader columns={PROJECT_COLUMNS}>
          {(column) => (
            <TableColumn key={column.key}>{column.label}</TableColumn>
          )}
        </TableHeader>
        <TableBody
          emptyContent={isLoading ? "Loading projects..." : "No projects found"}
          isLoading={isLoading}
          items={visibleProjects}
        >
          {(project) => (
            <TableRow key={project.id}>
              <TableCell>
                <ProjectThumbnail
                  project={project}
                  onClick={() => handlePreview(project)}
                />
              </TableCell>
              <TableCell>
                <div className="max-w-xs">
                  <p className="text-sm font-medium truncate">{project.name}</p>
                  {project.description && (
                    <p className="text-xs text-default-500 truncate">
                      {project.description}
                    </p>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <Chip color="secondary" size="sm" variant="flat">
                  {project.video_count} videos
                </Chip>
              </TableCell>
              <TableCell>
                <p className="text-sm text-default-500">
                  {formatFileSize(project.total_size_bytes)}
                </p>
              </TableCell>
              <TableCell>
                <div>
                  <p className="text-sm text-default-500">
                    {formatDate(project.created_at)}
                  </p>
                  {mounted &&
                    project.expires_at &&
                    getTimeUntilExpiration(project.expires_at) && (
                      <p className="text-xs text-warning mt-1">
                        {getTimeUntilExpiration(project.expires_at)}
                      </p>
                    )}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="flat"
                    onPress={() => handlePreview(project)}
                  >
                    Preview
                  </Button>
                  <Dropdown>
                    <DropdownTrigger>
                      <Button size="sm" variant="flat">
                        ⋮
                      </Button>
                    </DropdownTrigger>
                    <DropdownMenu>
                      <DropdownItem
                        key="download"
                        isDisabled={!project.zip_url}
                        onPress={() => handleDownload(project)}
                      >
                        Download ZIP
                      </DropdownItem>
                      <DropdownItem
                        key="delete"
                        className="text-danger"
                        color="danger"
                        onPress={() => handleDelete(project)}
                      >
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
      {projects.length > 0 && (
        <div className="text-center text-sm text-default-500 mt-4">
          Showing {startIndex + 1}-{Math.min(endIndex, projects.length)} of{" "}
          {projects.length} projects
        </div>
      )}

      {/* Preview Modal */}
      {mounted && previewProject && (
        <PreviewModal
          isOpen={isPreviewOpen}
          mounted={mounted}
          project={previewProject}
          onClose={onPreviewClose}
          onDownload={() => handleDownload(previewProject)}
        />
      )}
    </div>
  );
}

// Export with SSR disabled to prevent hydration errors
export default dynamic(() => Promise.resolve(ProjectsPageContent), {
  ssr: false,
  loading: () => (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Projects</h1>
          <p className="text-default-500">Loading projects...</p>
        </div>
      </div>
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    </div>
  ),
});

/**
 * Project Thumbnail Component
 * Loads thumbnail image using signed CloudFront URLs
 */
function ProjectThumbnail({
  project,
  onClick,
}: {
  project: Project;
  onClick: () => void;
}) {
  const { data: urls, isLoading } = useProjectUrls(project.id);

  return (
    <div
      className="w-20 h-12 bg-black rounded overflow-hidden cursor-pointer hover:opacity-80 transition"
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {isLoading ? (
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        </div>
      ) : urls?.preview_thumbnail_url ? (
        <Image
          alt={project.name}
          className="w-full h-full object-cover"
          height={48}
          src={urls.preview_thumbnail_url}
          width={80}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-white text-xs">
          No preview
        </div>
      )}
    </div>
  );
}

/**
 * Preview Modal Component
 * Shows preview video with download button
 */
function PreviewModal({
  project,
  isOpen,
  onClose,
  onDownload,
  mounted,
}: {
  project: Project;
  isOpen: boolean;
  onClose: () => void;
  onDownload: () => void;
  mounted: boolean;
}) {
  const { data: urls, isLoading } = useProjectUrls(project.id);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;

    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    // Use consistent UTC-based formatting to avoid hydration errors
    const year = date.getUTCFullYear();
    const month = date.toLocaleString("en-US", {
      month: "short",
      timeZone: "UTC",
    });
    const day = date.getUTCDate();
    const hours = date.getUTCHours().toString().padStart(2, "0");
    const minutes = date.getUTCMinutes().toString().padStart(2, "0");

    return `${month} ${day}, ${year} ${hours}:${minutes}`;
  };

  const getTimeUntilExpiration = (expiresAt: string | undefined) => {
    if (!expiresAt || !mounted) return null;

    const now = new Date().getTime();
    const expiration = new Date(expiresAt).getTime();
    const diff = expiration - now;

    if (diff <= 0) return "Expired";

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `Expires in ${hours}h ${minutes}m`;
    } else {
      return `Expires in ${minutes}m`;
    }
  };

  return (
    <Modal isOpen={isOpen} scrollBehavior="inside" size="5xl" onClose={onClose}>
      <ModalContent>
        <ModalHeader>{project.name}</ModalHeader>
        <ModalBody>
          {isLoading ? (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-default-500">Loading preview...</p>
              </div>
            </div>
          ) : urls?.preview_video_url ? (
            <video
              autoPlay
              controls
              className="w-full max-h-[70vh] object-contain bg-black rounded-lg"
              src={urls.preview_video_url}
            >
              <track kind="captions" />
              Your browser does not support video playback.
            </video>
          ) : (
            <div className="flex items-center justify-center min-h-[400px]">
              <p className="text-default-500">No preview available</p>
            </div>
          )}

          {/* Project Info */}
          <div className="mt-4 space-y-2">
            {project.description && (
              <p className="text-sm text-default-600">{project.description}</p>
            )}
            <div className="flex gap-4 text-sm text-default-500">
              <span>{project.video_count} videos</span>
              <span>•</span>
              <span>{formatFileSize(project.total_size_bytes)}</span>
              <span>•</span>
              <span>Created {formatDate(project.created_at)}</span>
            </div>
            {mounted &&
              project.expires_at &&
              getTimeUntilExpiration(project.expires_at) && (
                <p className="text-sm text-warning">
                  {getTimeUntilExpiration(project.expires_at)}
                </p>
              )}
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="light" onPress={onClose}>
            Close
          </Button>
          <Button
            color="primary"
            isDisabled={!project.zip_url}
            onPress={onDownload}
          >
            Download ZIP
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
