/**
 * useToast - Toast notification hook using @heroui/toast
 */

import { addToast } from "@heroui/toast";

export type ToastType =
  | "default"
  | "primary"
  | "secondary"
  | "success"
  | "warning"
  | "danger";

export interface ToastOptions {
  title?: string;
  description: string;
  type?: ToastType;
  duration?: number;
}

export function useToast() {
  const showToast = ({
    title,
    description,
    type = "default",
    duration = 5000,
  }: ToastOptions) => {
    addToast({
      title: title || undefined,
      description,
      color: type,
      timeout: duration,
      shouldShowTimeoutProgress: true,
    });
  };

  const success = (description: string, title?: string) => {
    showToast({ description, title, type: "success" });
  };

  const error = (description: string, title?: string) => {
    showToast({ description, title, type: "danger" });
  };

  const warning = (description: string, title?: string) => {
    showToast({ description, title, type: "warning" });
  };

  const info = (description: string, title?: string) => {
    showToast({ description, title, type: "primary" });
  };

  return {
    showToast,
    success,
    error,
    warning,
    info,
  };
}
