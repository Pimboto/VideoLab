"use client";

import { useState, useEffect } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Divider } from "@heroui/divider";
import { Chip } from "@heroui/chip";
import Link from "next/link";

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

  useEffect(() => {
    loadStats();
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

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-default-500">Welcome to your VideoLab workspace</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="border-l-4 border-l-primary">
          <CardBody className="gap-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-default-500">Videos</p>
                <h3 className="text-2xl font-bold">{stats.videosCount}</h3>
              </div>
              <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🎬</span>
              </div>
            </div>
            <p className="text-xs text-default-400">{formatSize(stats.videosSize)}</p>
          </CardBody>
        </Card>

        <Card className="border-l-4 border-l-secondary">
          <CardBody className="gap-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-default-500">Audios</p>
                <h3 className="text-2xl font-bold">{stats.audiosCount}</h3>
              </div>
              <div className="w-12 h-12 bg-secondary/20 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🎵</span>
              </div>
            </div>
            <p className="text-xs text-default-400">{formatSize(stats.audiosSize)}</p>
          </CardBody>
        </Card>

        <Card className="border-l-4 border-l-warning">
          <CardBody className="gap-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-default-500">Text Files</p>
                <h3 className="text-2xl font-bold">{stats.csvCount}</h3>
              </div>
              <div className="w-12 h-12 bg-warning/20 rounded-lg flex items-center justify-center">
                <span className="text-2xl">📝</span>
              </div>
            </div>
            <p className="text-xs text-default-400">{formatSize(stats.csvSize)}</p>
          </CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Quick Actions</h2>
          </CardHeader>
          <Divider />
          <CardBody className="gap-3">
            <Link href="/dashboard/create">
              <Button color="primary" className="w-full justify-start">
                <span className="text-lg mr-2">🎥</span>
                Start Batch Processing
              </Button>
            </Link>
            <Link href="/dashboard/videos">
              <Button color="default" variant="flat" className="w-full justify-start">
                <span className="text-lg mr-2">📹</span>
                Upload Videos
              </Button>
            </Link>
            <Link href="/dashboard/audios">
              <Button color="default" variant="flat" className="w-full justify-start">
                <span className="text-lg mr-2">🎧</span>
                Upload Audios
              </Button>
            </Link>
            <Link href="/dashboard/texts">
              <Button color="default" variant="flat" className="w-full justify-start">
                <span className="text-lg mr-2">📄</span>
                Upload Text CSV
              </Button>
            </Link>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Getting Started</h2>
          </CardHeader>
          <Divider />
          <CardBody className="gap-4">
            <div className="flex gap-3">
              <Chip color="primary" variant="flat">1</Chip>
              <div>
                <p className="font-semibold text-sm">Upload your media</p>
                <p className="text-xs text-default-500">Add videos and audios to folders</p>
              </div>
            </div>
            <div className="flex gap-3">
              <Chip color="primary" variant="flat">2</Chip>
              <div>
                <p className="font-semibold text-sm">Upload text combinations</p>
                <p className="text-xs text-default-500">CSV file with your text segments</p>
              </div>
            </div>
            <div className="flex gap-3">
              <Chip color="primary" variant="flat">3</Chip>
              <div>
                <p className="font-semibold text-sm">Configure and process</p>
                <p className="text-xs text-default-500">Select folders and start batch processing</p>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
