"use client";

import { Input } from "@heroui/input";
import { Avatar } from "@heroui/avatar";
import { Divider } from "@heroui/divider";
import { Link } from "@heroui/link";
import { usePathname } from "next/navigation";
import {
  SearchIcon,
  PlusIcon,
  AudioIcon,
  VideoIcon,
  DocumentIcon,
  FolderIcon,
  SettingsIcon,
  QuestionIcon,
} from "@/components/icons";

const navigationItems = [
  { name: "Create", icon: PlusIcon, href: "/dashboard/create" },
  { name: "Audios", icon: AudioIcon, href: "/dashboard/audios" },
  { name: "Videos", icon: VideoIcon, href: "/dashboard/videos" },
  { name: "Texts", icon: DocumentIcon, href: "/dashboard/texts" },
  { name: "Projects", icon: FolderIcon, href: "/dashboard/projects" },
  { name: "Settings", icon: SettingsIcon, href: "/dashboard/settings" },
  { name: "Help", icon: QuestionIcon, href: "/dashboard/help" },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-divider flex flex-col bg-background">
      {/* Brand */}
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <VideoIcon className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-lg font-bold">VideoLab</h1>
            <p className="text-xs text-default-500">Dev Plan</p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="px-4 pb-4">
        <Input
          classNames={{
            base: "w-full",
            inputWrapper: "h-10",
          }}
          placeholder="Search"
          startContent={<SearchIcon className="text-default-400" size={18} />}
          type="search"
        />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.name}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors w-full no-underline ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-default-700 hover:bg-default-100"
              }`}
              href={item.href}
            >
              <Icon size={20} />
              <span className="text-sm font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <Divider className="my-4" />

      {/* User Profile */}
      <div className="p-4">
        <div className="flex items-center gap-3">
          <Avatar
            isBordered
            color="primary"
            name="Francisco"
            size="sm"
            src="https://i.pravatar.cc/150?u=francisco"
          />
          <div className="flex-1">
            <p className="text-sm font-medium">Francisco</p>
            <p className="text-xs text-default-500">francisco@email.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
