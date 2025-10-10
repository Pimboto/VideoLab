"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Divider } from "@heroui/divider";
import { Chip } from "@heroui/chip";
import Link from "next/link";
import gsap from "gsap";
import {
  VideoSquare,
  AudioSquare,
  DocumentText,
  VideoPlay,
  Folder,
  ArrowRight,
  DocumentDownload,
  Clock,
  InfoCircle,
  Star1,
  Image,
  VideoVertical
} from "iconsax-reactjs";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    videosCount: 0,
    audiosCount: 0,
    csvCount: 0,
    videosSize: 0,
    audiosSize: 0,
    csvSize: 0
  });

  const heroRef = useRef(null);
  const statsRef = useRef(null);
  const cardsRef = useRef<(HTMLDivElement | null)[]>([]);
  const actionsRef = useRef(null);
  const viralRef = useRef(null);
  const generateRef = useRef(null);
  const storageRef = useRef(null);
  const notificationsRef = useRef(null);

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    // GSAP animations on mount
    const ctx = gsap.context(() => {
      // Hero animation
      gsap.from(heroRef.current, {
        opacity: 0,
        y: -20,
        duration: 0.8,
        ease: "power2.out"
      });

      // Stats cards stagger animation
      gsap.from(cardsRef.current, {
        opacity: 0,
        y: 30,
        duration: 0.6,
        stagger: 0.1,
        ease: "power2.out",
        delay: 0.2
      });

      // Actions section
      gsap.from(actionsRef.current, {
        opacity: 0,
        y: 20,
        duration: 0.6,
        ease: "power2.out",
        delay: 0.4
      });

      // Viral and Generate sections
      gsap.from([viralRef.current, generateRef.current], {
        opacity: 0,
        y: 20,
        duration: 0.6,
        stagger: 0.1,
        ease: "power2.out",
        delay: 0.5
      });

      // Storage and notifications
      gsap.from([storageRef.current, notificationsRef.current], {
        opacity: 0,
        y: 20,
        duration: 0.6,
        stagger: 0.15,
        ease: "power2.out",
        delay: 0.6
      });
    });

    return () => ctx.revert();
  }, []);

  const loadStats = async () => {
    try {
      const [vRes, aRes, cRes] = await Promise.all([
        fetch(`${API_URL}/api/video-processor/files/videos`),
        fetch(`${API_URL}/api/video-processor/files/audios`),
        fetch(`${API_URL}/api/video-processor/files/csv`)
      ]);

      const [vData, aData, cData] = await Promise.all([
        vRes.json(),
        aRes.json(),
        cRes.json()
      ]);

      const videosSize = vData.files?.reduce((acc: number, f: any) => acc + f.size, 0) || 0;
      const audiosSize = aData.files?.reduce((acc: number, f: any) => acc + f.size, 0) || 0;
      const csvSize = cData.files?.reduce((acc: number, f: any) => acc + f.size, 0) || 0;

      setStats({
        videosCount: vData.count || 0,
        audiosCount: aData.count || 0,
        csvCount: cData.count || 0,
        videosSize,
        audiosSize,
        csvSize
      });
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  };

  const getTotalStorage = () => {
    const totalBytes = stats.videosSize + stats.audiosSize + stats.csvSize;
    return (totalBytes / (1024 * 1024 * 1024)).toFixed(2); // Convert to GB
  };

  const getStoragePercentage = () => {
    const totalGB = parseFloat(getTotalStorage());
    const maxGB = 20; // 20GB limit
    return Math.min((totalGB / maxGB) * 100, 100);
  };

  return (
    <div className="p-8">
      {/* Hero Section */}
      <div ref={heroRef} className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Welcome back, Francisco</h1>
        <p className="text-default-500">Ready to create something amazing?</p>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column - Library Stats & Quick Actions */}
        <div className="lg:col-span-3 space-y-6">
          <div>
            <h2 className="text-lg font-bold mb-4">Your Library</h2>
            <div className="grid grid-cols-3 gap-4">
              {/* Videos Card */}
              <div ref={(el) => { cardsRef.current[0] = el; }} className="w-full">
                <Link href="/dashboard/videos" className="block w-full">
                  <Card
                    isPressable
                    isHoverable
                    className="transition-all hover:shadow-md w-full"
                  >
                    <CardBody className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-default-100 rounded-lg">
                          <VideoSquare size={20} variant="Bold" className="text-foreground" />
                        </div>
                        <div>
                          <p className="text-xs text-default-500">Videos</p>
                          <h3 className="text-xl font-bold">{stats.videosCount}</h3>
                        </div>
                      </div>
                      <p className="text-xs text-default-400">{formatSize(stats.videosSize)}</p>
                    </CardBody>
                  </Card>
                </Link>
              </div>

              {/* Audios Card */}
              <div ref={(el) => { cardsRef.current[1] = el; }} className="w-full">
                <Link href="/dashboard/audios" className="block w-full">
                  <Card
                    isPressable
                    isHoverable
                    className="transition-all hover:shadow-md w-full"
                  >
                    <CardBody className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-default-100 rounded-lg">
                          <AudioSquare size={20} variant="Bold" className="text-foreground" />
                        </div>
                        <div>
                          <p className="text-xs text-default-500">Audios</p>
                          <h3 className="text-xl font-bold">{stats.audiosCount}</h3>
                        </div>
                      </div>
                      <p className="text-xs text-default-400">{formatSize(stats.audiosSize)}</p>
                    </CardBody>
                  </Card>
                </Link>
              </div>

              {/* Text Files Card */}
              <div ref={(el) => { cardsRef.current[2] = el; }} className="w-full">
                <Link href="/dashboard/texts" className="block w-full">
                  <Card
                    isPressable
                    isHoverable
                    className="transition-all hover:shadow-md w-full"
                  >
                    <CardBody className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-default-100 rounded-lg">
                          <DocumentText size={20} variant="Bold" className="text-foreground" />
                        </div>
                        <div>
                          <p className="text-xs text-default-500">Text Files</p>
                          <h3 className="text-xl font-bold">{stats.csvCount}</h3>
                        </div>
                      </div>
                      <p className="text-xs text-default-400">{formatSize(stats.csvSize)}</p>
                    </CardBody>
                  </Card>
                </Link>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div ref={actionsRef}>
            <h2 className="text-lg font-bold mb-4">Quick Actions</h2>
            <div className="grid grid-cols-2 gap-3">
              <Link href="/dashboard/create" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="flex-row items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <VideoPlay size={20} variant="Bold" className="text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">Batch Processing</p>
                        <p className="text-xs text-default-500">Create multiple videos</p>
                      </div>
                    </div>
                    <ArrowRight size={16} className="text-default-400" />
                  </CardBody>
                </Card>
              </Link>

              <Link href="/dashboard/projects" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="flex-row items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-default-100 rounded-lg">
                        <Folder size={20} variant="Bold" className="text-foreground" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">View Projects</p>
                        <p className="text-xs text-default-500">Browse processed videos</p>
                      </div>
                    </div>
                    <ArrowRight size={16} className="text-default-400" />
                  </CardBody>
                </Card>
              </Link>

              <Link href="/dashboard/videos" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="flex-row items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-default-100 rounded-lg">
                        <VideoSquare size={20} variant="Bold" className="text-foreground" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">Manage Videos</p>
                        <p className="text-xs text-default-500">Upload and organize</p>
                      </div>
                    </div>
                    <ArrowRight size={16} className="text-default-400" />
                  </CardBody>
                </Card>
              </Link>

              <Link href="/dashboard/audios" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="flex-row items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-default-100 rounded-lg">
                        <AudioSquare size={20} variant="Bold" className="text-foreground" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">Manage Audios</p>
                        <p className="text-xs text-default-500">Upload and organize</p>
                      </div>
                    </div>
                    <ArrowRight size={16} className="text-default-400" />
                  </CardBody>
                </Card>
              </Link>
            </div>
          </div>

          {/* Trending / Viral Content */}
          <div ref={viralRef}>
            <h2 className="text-lg font-bold mb-4">Trending Content</h2>
            <div className="grid grid-cols-3 gap-3">
              <Link href="/dashboard/community?filter=viral-audios" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="p-4 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <div className="p-2 bg-warning/10 rounded-lg">
                        <Star1 size={20} variant="Bold" className="text-warning" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">Viral Audios</p>
                        <p className="text-xs text-default-500">Top trending</p>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              </Link>

              <Link href="/dashboard/community?filter=viral-texts" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="p-4 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <div className="p-2 bg-warning/10 rounded-lg">
                        <Star1 size={20} variant="Bold" className="text-warning" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">Viral Texts</p>
                        <p className="text-xs text-default-500">Most popular</p>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              </Link>

              <Link href="/dashboard/community?filter=model-videos" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="p-4 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <div className="p-2 bg-default-100 rounded-lg">
                        <VideoSquare size={20} variant="Bold" className="text-foreground" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">Model Videos</p>
                        <p className="text-xs text-default-500">Templates</p>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              </Link>
            </div>
          </div>

          {/* Generate / AI Tools */}
          <div ref={generateRef}>
            <h2 className="text-lg font-bold mb-4">Generate</h2>
            <div className="grid grid-cols-1 gap-3">
              <Link href="/dashboard/image-to-video" className="block w-full">
                <Card
                  isPressable
                  isHoverable
                  className="transition-all hover:shadow-md w-full"
                >
                  <CardBody className="flex-row items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-success/10 rounded-lg">
                        <VideoVertical size={20} variant="Bold" className="text-success" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">Image to Video</p>
                        <p className="text-xs text-default-500">Convert images to videos with AI</p>
                      </div>
                    </div>
                    <ArrowRight size={16} className="text-default-400" />
                  </CardBody>
                </Card>
              </Link>
            </div>
          </div>
        </div>

        {/* Right Column - Storage & Notifications */}
        <div className="lg:col-span-1 space-y-4">
          {/* Storage Card */}
          <div ref={storageRef}>
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <DocumentDownload size={18} variant="Bold" className="text-foreground" />
                  <h3 className="font-bold text-sm">Storage</h3>
                </div>
              </CardHeader>
              <Divider />
              <CardBody className="gap-3 pt-3">
                <div>
                  <div className="flex items-end justify-between mb-2">
                    <span className="text-xl font-bold">{getTotalStorage()} GB</span>
                    <span className="text-xs text-default-500">of 20 GB</span>
                  </div>
                  <div className="w-full bg-default-200 rounded-full h-1.5">
                    <div
                      className="bg-primary rounded-full h-1.5 transition-all duration-500"
                      style={{ width: `${getStoragePercentage()}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-default-500">Videos</span>
                    <span className="font-medium">{formatSize(stats.videosSize)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-default-500">Audios</span>
                    <span className="font-medium">{formatSize(stats.audiosSize)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-default-500">Texts</span>
                    <span className="font-medium">{formatSize(stats.csvSize)}</span>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Notifications Card */}
          <div ref={notificationsRef}>
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <InfoCircle size={18} variant="Bold" className="text-warning" />
                  <h3 className="font-bold text-sm">Notifications</h3>
                </div>
              </CardHeader>
              <Divider />
              <CardBody className="gap-3 pt-3">
                <div>
                  <p className="text-sm font-semibold mb-1">Projects Auto-Cleanup</p>
                  <p className="text-xs text-default-500 mb-2">
                    Projects are automatically deleted after 24 hours to save storage space.
                  </p>
                  <div className="flex items-center gap-2 text-xs">
                    <Folder size={14} className="text-default-400" />
                    <span className="text-default-500">Next cleanup:</span>
                    <Chip size="sm" color="warning" variant="flat" className="h-5">
                      in 2h
                    </Chip>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
