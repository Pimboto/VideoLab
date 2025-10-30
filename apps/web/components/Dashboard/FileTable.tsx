"use client";

import type { Selection } from "@heroui/table";
import type { BaseFile } from "@/lib/types";

import { useState, useEffect } from "react";
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
} from "@heroui/table";
import { Button } from "@heroui/button";
import {
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
} from "@heroui/dropdown";

import { formatFileSize, formatDate } from "@/lib/utils";

export interface Column {
  key: string;
  label: string;
  sortable?: boolean;
}

export interface RowAction {
  label: string;
  onClick: (file: BaseFile) => void;
  color?:
    | "default"
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "danger";
  icon?: React.ReactNode;
}

interface FileTableProps {
  files: BaseFile[];
  columns: Column[];
  selectedKeys: Selection;
  onSelectionChange: (keys: Selection) => void;
  loading?: boolean;
  emptyMessage?: string;
  renderCell?: (file: BaseFile, columnKey: string) => React.ReactNode;
  primaryAction?: {
    label: string;
    onClick: (file: BaseFile) => void;
  };
  rowActions?: RowAction[];
}

export default function FileTable({
  files,
  columns,
  selectedKeys,
  onSelectionChange,
  loading = false,
  emptyMessage = "No files found",
  renderCell,
  primaryAction,
  rowActions = [],
}: FileTableProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Get display name from metadata if available, otherwise use filename
  const getDisplayName = (file: BaseFile): string => {
    if (
      (file as any).metadata &&
      typeof (file as any).metadata === "object" &&
      "original_filename" in (file as any).metadata
    ) {
      return (file as any).metadata.original_filename;
    }

    return file.filename;
  };

  const defaultRenderCell = (
    file: BaseFile,
    columnKey: string,
  ): React.ReactNode => {
    switch (columnKey) {
      case "filename":
      case "name":
        return (
          <div className="max-w-xs">
            <p className="text-sm font-medium truncate">
              {getDisplayName(file)}
            </p>
          </div>
        );
      case "size":
        return (
          <p className="text-sm text-default-500">
            {formatFileSize(file.size)}
          </p>
        );
      case "modified":
      case "date":
        return (
          <p className="text-sm text-default-500">
            {formatDate(file.modified)}
          </p>
        );
      case "actions":
        return (
          <div className="flex gap-2">
            {primaryAction && (
              <Button
                size="sm"
                variant="flat"
                onPress={() => primaryAction.onClick(file)}
              >
                {primaryAction.label}
              </Button>
            )}
            {rowActions.length > 0 && (
              <Dropdown>
                <DropdownTrigger>
                  <Button size="sm" variant="flat">
                    ⋮
                  </Button>
                </DropdownTrigger>
                <DropdownMenu>
                  {rowActions.map((action, idx) => (
                    <DropdownItem
                      key={idx}
                      className={action.color === "danger" ? "text-danger" : ""}
                      color={action.color}
                      startContent={action.icon}
                      onPress={() => action.onClick(file)}
                    >
                      {action.label}
                    </DropdownItem>
                  ))}
                </DropdownMenu>
              </Dropdown>
            )}
          </div>
        );
      default:
        return <span className="text-sm text-default-500">-</span>;
    }
  };

  if (!mounted) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-default-500">Loading...</p>
      </div>
    );
  }

  return (
    <Table
      aria-label="Files table"
      classNames={{
        wrapper: "min-h-[400px]",
      }}
      selectedKeys={selectedKeys}
      selectionMode="multiple"
      onSelectionChange={onSelectionChange}
    >
      <TableHeader columns={columns}>
        {(column) => <TableColumn key={column.key}>{column.label}</TableColumn>}
      </TableHeader>
      <TableBody
        emptyContent={loading ? "Loading..." : emptyMessage}
        items={files}
      >
        {(file) => (
          <TableRow key={file.filepath}>
            {columns.map((column) => {
              const cellContent = renderCell
                ? renderCell(file, column.key)
                : defaultRenderCell(file, column.key);

              return (
                <TableCell key={column.key}>
                  {cellContent || defaultRenderCell(file, column.key)}
                </TableCell>
              );
            })}
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
