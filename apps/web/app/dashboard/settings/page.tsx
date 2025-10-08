"use client";

import { Modal, ModalContent, ModalHeader, ModalBody } from "@heroui/modal";
import { Switch } from "@heroui/switch";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Settings</h1>
      <p className="text-default-500 mb-8">Manage your preferences</p>

      <div className="max-w-md">
        <div className="flex items-center justify-between p-4 border rounded-lg border-divider">
          <div>
            <p className="font-medium">Dark Mode</p>
            <p className="text-sm text-default-500">Toggle theme</p>
          </div>
          <Switch
            isSelected={theme === "dark"}
            onValueChange={(checked) => setTheme(checked ? "dark" : "light")}
          />
        </div>
      </div>
    </div>
  );
}
