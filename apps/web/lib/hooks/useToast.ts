/**
 * Custom hook for toast notifications
 * Simple console-based notifications for now (can be enhanced later)
 */

export type ToastType = "success" | "error" | "warning" | "info";

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
    type = "info",
    duration = 5000,
  }: ToastOptions) => {
    // Simple console output for now
    const prefix = type === "error" ? "❌" : type === "success" ? "✅" : type === "warning" ? "⚠️" : "ℹ️";
    const message = title ? `${prefix} ${title}: ${description}` : `${prefix} ${description}`;

    if (type === "error") {
      console.error(message);
    } else if (type === "warning") {
      console.warn(message);
    } else {
      console.log(message);
    }

    // Alert for errors to ensure visibility
    if (type === "error") {
      alert(description);
    }
  };

  const success = (description: string, title?: string) => {
    showToast({ description, title, type: "success" });
  };

  const error = (description: string, title?: string) => {
    showToast({ description, title, type: "error" });
  };

  const warning = (description: string, title?: string) => {
    showToast({ description, title, type: "warning" });
  };

  const info = (description: string, title?: string) => {
    showToast({ description, title, type: "info" });
  };

  return {
    showToast,
    success,
    error,
    warning,
    info,
  };
}
