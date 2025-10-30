"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";

interface BulkActionsProps {
  selectedCount: number;
  onClear: () => void;
  actions: {
    label: string;
    onClick: () => void;
    color?:
      | "primary"
      | "danger"
      | "default"
      | "secondary"
      | "success"
      | "warning";
    variant?:
      | "solid"
      | "flat"
      | "bordered"
      | "light"
      | "faded"
      | "shadow"
      | "ghost";
  }[];
}

export default function BulkActions({
  selectedCount,
  onClear,
  actions,
}: BulkActionsProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="mb-4 flex gap-3 items-center bg-default-100 px-4 py-3 rounded-xl border border-default-200">
      <Chip color="primary" size="lg" variant="flat">
        {selectedCount} selected
      </Chip>
      <div className="flex gap-2 flex-1">
        {actions.map((action, index) => (
          <Button
            key={index}
            color={action.color || "default"}
            size="sm"
            variant={action.variant || "flat"}
            onPress={action.onClick}
          >
            {action.label}
          </Button>
        ))}
      </div>
      <Button className="ml-auto" size="sm" variant="light" onPress={onClear}>
        Clear Selection
      </Button>
    </div>
  );
}
