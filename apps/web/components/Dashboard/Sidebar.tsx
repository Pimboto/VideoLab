"use client";

import { Avatar } from "@heroui/avatar";
import { Divider } from "@heroui/divider";
import { Link } from "@heroui/link";
import { Button } from "@heroui/button";
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from "@heroui/dropdown";
import { usePathname } from "next/navigation";
import { useUser, useClerk } from "@clerk/nextjs";
import Image from "next/image";
import {
  VideoPlay,
  Folder,
  VideoSquare,
  AudioSquare,
  DocumentText,
  Setting2,
  MessageQuestion,
  VideoVertical,
  Star1,
  Home2,
  LogoutCurve
} from "iconsax-reactjs";

const libraryItems = [
  { name: "Projects", icon: Folder, href: "/dashboard/projects" },
  { name: "Videos", icon: VideoSquare, href: "/dashboard/videos" },
  { name: "Audios", icon: AudioSquare, href: "/dashboard/audios" },
  { name: "Texts", icon: DocumentText, href: "/dashboard/texts" },
/*   { name: "Community", icon: Star1, href: "/dashboard/community" }, */
];

const generateItems = [
  { name: "Image To Video", icon: VideoVertical, href: "/dashboard/image-to-video" },
];

const bottomItems = [
  { name: "Help", icon: MessageQuestion, href: "/dashboard/help" },
  { name: "Settings", icon: Setting2, href: "/dashboard/settings" },
];

export const Sidebar = () => {
  const pathname = usePathname();
  const { user, isLoaded } = useUser();
  const { signOut } = useClerk();

  const renderNavItem = (item: any) => {
    const Icon = item.icon;
    const isActive = pathname === item.href;

    return (
      <Link
        key={item.name}
        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all w-full no-underline ${
          isActive
            ? "bg-default-100 text-foreground"
            : "text-default-600 hover:bg-default-50 hover:text-foreground"
        }`}
        href={item.href}
      >
        <Icon
          size={20}
          variant={isActive ? "Bold" : "Linear"}
          className={isActive ? "text-foreground" : "text-default-500"}
        />
        <span className={`text-sm font-medium ${isActive ? "text-foreground" : ""}`}>
          {item.name}
        </span>
      </Link>
    );
  };

  return (
    <aside className="w-64 border-r border-divider flex flex-col bg-background h-screen">
      {/* Brand */}
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center">
            <Image
              src="/videolab-logo.png"
              alt="VideoLab"
              width={40}
              height={40}
              className="object-cover"
            />
          </div>
          <div>
            <h1 className="text-lg font-bold">VideoLab</h1>
            <p className="text-xs text-default-500">Pro Plan</p>
          </div>
        </div>
      </div>
      <Divider />

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-6 overflow-y-auto pb-4">
        {/* Home & Create Section */}
        <div className="space-y-1 pt-4">
          <p className="px-3 text-xs font-semibold text-default-400 uppercase tracking-wider mb-2">
            Home
          </p>
          <Link
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all w-full no-underline ${
              pathname === "/dashboard"
                ? "bg-default-100 text-foreground"
                : "text-default-600 hover:bg-default-50 hover:text-foreground"
            }`}
            href="/dashboard"
          >
            <Home2
              size={20}
              variant={pathname === "/dashboard" ? "Bold" : "Linear"}
              className={pathname === "/dashboard" ? "text-foreground" : "text-default-500"}
            />
            <span className={`text-sm font-medium ${pathname === "/dashboard" ? "text-foreground" : ""}`}>
              Dashboard
            </span>
          </Link>

          <p className="px-3 text-xs font-semibold text-default-400 uppercase tracking-wider mt-4 mb-2">
            Create
          </p>
          <Link
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all w-full no-underline ${
              pathname === "/dashboard/create"
                ? "bg-default-100 text-foreground"
                : "text-default-600 hover:bg-default-50 hover:text-foreground"
            }`}
            href="/dashboard/create"
          >
            <VideoPlay
              size={20}
              variant={pathname === "/dashboard/create" ? "Bold" : "Linear"}
              className={pathname === "/dashboard/create" ? "text-foreground" : "text-default-500"}
            />
            <span className={`text-sm font-medium ${pathname === "/dashboard/create" ? "text-foreground" : ""}`}>
              Batch Processing
            </span>
          </Link>
        </div>


        {/* Library Section */}
        <div className="space-y-1">
          <p className="px-3 text-xs font-semibold text-default-400 uppercase tracking-wider mb-2">
            Library
          </p>
          {libraryItems.map(renderNavItem)}
        </div>

{/*         <Divider /> */}

        {/* Generate Section */}
{/*         <div className="space-y-1">
          <p className="px-3 text-xs font-semibold text-default-400 uppercase tracking-wider mb-2">
            Generate
          </p>
          {generateItems.map(renderNavItem)}
        </div> */}
      </nav>


      {/* Bottom Navigation */}
      <div className="px-4 py-3 space-y-1">
        {bottomItems.map(renderNavItem)}
      </div>

      <Divider />

      {/* User Profile */}
      <div className="p-4">
        {isLoaded && user ? (
          <Dropdown placement="top">
            <DropdownTrigger>
              <div className="flex items-center gap-3 cursor-pointer hover:bg-default-50 p-2 rounded-lg transition-colors">
                <Avatar
                  isBordered
                  color="primary"
                  name={user.fullName || user.username || "User"}
                  size="sm"
                  src={user.imageUrl}
                />
                <div className="flex-1">
                  <p className="text-sm font-medium truncate">
                    {user.firstName || user.username || "User"}
                  </p>
                  <p className="text-xs text-default-500 truncate">
                    {user.primaryEmailAddress?.emailAddress || "No email"}
                  </p>
                </div>
              </div>
            </DropdownTrigger>
            <DropdownMenu aria-label="User actions">
              <DropdownItem 
                key="profile" 
                className="h-14 gap-2"
                textValue="Profile"
              >
                <p className="font-semibold">Signed in as</p>
                <p className="font-semibold">{user.primaryEmailAddress?.emailAddress}</p>
              </DropdownItem>
              <DropdownItem 
                key="settings"
                textValue="Settings"
                startContent={<Setting2 size={18} />}
                href="/dashboard/settings"
              >
                Settings
              </DropdownItem>
              <DropdownItem 
                key="logout" 
                color="danger"
                textValue="Log out"
                startContent={<LogoutCurve size={18} />}
                onPress={() => signOut()}
              >
                Log out
              </DropdownItem>
            </DropdownMenu>
          </Dropdown>
        ) : (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-default-200 animate-pulse" />
            <div className="flex-1">
              <div className="h-4 bg-default-200 rounded animate-pulse mb-1" />
              <div className="h-3 bg-default-200 rounded animate-pulse w-3/4" />
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
