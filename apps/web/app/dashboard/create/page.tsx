"use client";

import { useState, useEffect } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Divider } from "@heroui/divider";
import { Input } from "@heroui/input";
import { Select, SelectItem } from "@heroui/select";
import { Switch } from "@heroui/switch";
import { Progress } from "@heroui/progress";
import { Chip } from "@heroui/chip";
import { useRouter } from "next/navigation";
import { fontRoboto, fontInter } from "@/config/fonts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Folder {
  name: string;
  path: string;
  file_count: number;
  total_size: number;
}

interface CSVFile {
  filename: string;
  filepath: string;
}

interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  message: string;
  output_files: string[];
}

export default function CreatePage() {
  const router = useRouter();
  const [videoFolders, setVideoFolders] = useState<Folder[]>([]);
  const [audioFolders, setAudioFolders] = useState<Folder[]>([]);
  const [csvFiles, setCSVFiles] = useState<CSVFile[]>([]);

  const [selectedVideoFolder, setSelectedVideoFolder] = useState("");
  const [selectedAudioFolder, setSelectedAudioFolder] = useState("");
  const [selectedCSV, setSelectedCSV] = useState("");
  const [previewVideoSrc, setPreviewVideoSrc] = useState("");

  const [position, setPosition] = useState("center");
  const [preset, setPreset] = useState("instagram1");
  const [fitMode, setFitMode] = useState("cover");
  const [uniqueMode, setUniqueMode] = useState(true);
  const [uniqueAmount, setUniqueAmount] = useState("50");

  const [processing, setProcessing] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedVideoFolder) {
      loadPreviewVideo(selectedVideoFolder);
    }
  }, [selectedVideoFolder]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (
      jobStatus &&
      (jobStatus.status === "pending" || jobStatus.status === "processing")
    ) {
      interval = setInterval(() => {
        checkJobStatus(jobStatus.job_id);
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobStatus]);

  const loadData = async () => {
    try {
      const [vRes, aRes, cRes] = await Promise.all([
        fetch(`${API_URL}/api/video-processor/folders/videos`),
        fetch(`${API_URL}/api/video-processor/folders/audios`),
        fetch(`${API_URL}/api/video-processor/files/csv`),
      ]);

      const [vData, aData, cData] = await Promise.all([
        vRes.json(),
        aRes.json(),
        cRes.json(),
      ]);

      setVideoFolders(vData.folders || []);
      setAudioFolders(aData.folders || []);
      setCSVFiles(cData.files || []);

      if (vData.folders?.length) setSelectedVideoFolder(vData.folders[0].path);
      if (aData.folders?.length) setSelectedAudioFolder(aData.folders[0].path);
      if (cData.files?.length) setSelectedCSV(cData.files[0].filepath);
    } catch (error) {
      console.error("Error loading data:", error);
    }
  };

  const loadPreviewVideo = async (folderPath: string) => {
    try {
      const folderName = videoFolders.find((f) => f.path === folderPath)?.name;
      if (!folderName) return;

      const params = `?subfolder=${folderName}`;
      const res = await fetch(
        `${API_URL}/api/video-processor/files/videos${params}`
      );
      const data = await res.json();

      if (data.files && data.files.length > 0) {
        const firstVideo = data.files[0];
        setPreviewVideoSrc(
          `${API_URL}/api/video-processor/files/stream/video?filepath=${encodeURIComponent(firstVideo.filepath)}`
        );
      }
    } catch (error) {
      console.error("Error loading preview video:", error);
    }
  };

  const checkJobStatus = async (jobId: string) => {
    try {
      const res = await fetch(
        `${API_URL}/api/video-processor/processing/status/${jobId}`
      );
      const data = await res.json();
      setJobStatus(data);

      if (data.status === "completed" || data.status === "failed") {
        setProcessing(false);
      }
    } catch (error) {
      console.error("Error checking job status:", error);
    }
  };

  const handleStartBatch = async () => {
    if (!selectedVideoFolder || !selectedAudioFolder || !selectedCSV) {
      alert("Please select video folder, audio folder, and CSV file");
      return;
    }

    setProcessing(true);

    try {
      const res = await fetch(
        `${API_URL}/api/video-processor/files/preview/csv?filepath=${encodeURIComponent(selectedCSV)}`
      );

      const csvData = await res.json();
      const combinations = csvData.combinations || [];

      const batchRes = await fetch(
        `${API_URL}/api/video-processor/processing/process-batch`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_folder: selectedVideoFolder,
            audio_folder: selectedAudioFolder,
            text_combinations: combinations,
            output_folder: "D:/Work/video/output",
            unique_mode: uniqueMode,
            unique_amount: parseInt(uniqueAmount),
            config: {
              position,
              preset,
              fit_mode: fitMode,
            },
          }),
        }
      );

      const batchData = await batchRes.json();
      setJobStatus({
        job_id: batchData.job_id,
        status: "pending",
        progress: 0,
        message: batchData.message,
        output_files: [],
      });
    } catch (error) {
      console.error("Error starting batch:", error);
      setProcessing(false);
    }
  };

  const getTextPositionStyle = () => {
    switch (position) {
      case "top":
        return "items-start pt-8";
      case "bottom":
        return "items-end pb-8";
      default:
        return "items-center";
    }
  };

  const getTextPresetStyle = (preset: string = "") => {
    switch (preset) {
      // --- NUEVOS ---
      case "instagram1": // Roboto, blanco, sombra suave
        return `${fontRoboto.className} font-bold  text-white text-2xl drop-shadow-[0_1.5px_1.5px_rgba(0,0,0,0.40)]`;

      case "instagram2": // Roboto, pill negro
        return `${fontRoboto.className} font-bold text-white text-2xl bg-black/95 rounded-xl px-3 py-1 drop-shadow-[0_1.5px_2.5px_rgba(0,0,0,0.35)]`;

      case "tiktok": // Inter, caption con contorno negro
        // Outline simulado con múltiples text-shadows (Tailwind arbitrary property)
        return `${fontInter.className} font-semibold text-white text-2xl [text-shadow:_0_1px_0_#000,_0_-1px_0_#000,_1px_0_0_#000,_-1px_0_0_#000,_1px_1px_0_#000,_-1px_1px_0_#000,_1px_-1px_0_#000,_-1px_-1px_0_#000]`;

      // --- TUS EXISTENTES ---
      case "bold":
        return "font-black text-2xl text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]";
      case "clean":
        return "font-semibold text-xl text-white";
      case "subtle":
        return "font-medium text-lg text-white/90";
      case "yellow":
        return "font-black text-2xl text-yellow-400 drop-shadow-[0_2px_8px_rgba(0,0,0,0.9)]";
      case "shadow":
        return "font-black text-2xl text-white shadow-[0_0_20px_rgba(0,0,0,1)]";
      default:
        return "font-black text-2xl text-white";
    }
  };

  const getFitModeStyle = () => {
    return fitMode === "cover" ? "object-cover" : "object-contain";
  };

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Batch Video Processing</h1>
        <p className="text-default-500">
          Create multiple videos with different combinations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left side - Select Sources at top, Processing Options below */}
        <div className="lg:col-span-2 space-y-4">
          {/* Select Sources Card */}
          <Card>
            <CardHeader>
              <h2 className="font-semibold">Select Sources</h2>
            </CardHeader>
            <Divider />
            <CardBody className="gap-3">
              <Select
                label="Video Folder"
                placeholder="Choose video folder"
                selectedKeys={selectedVideoFolder ? [selectedVideoFolder] : []}
                onSelectionChange={(keys) =>
                  setSelectedVideoFolder(Array.from(keys)[0] as string)
                }
                size="sm"
              >
                {videoFolders.map((folder) => (
                  <SelectItem key={folder.path} textValue={folder.name}>
                    {folder.name} ({folder.file_count} files)
                  </SelectItem>
                ))}
              </Select>

              <Select
                label="Audio Folder"
                placeholder="Choose audio folder"
                selectedKeys={selectedAudioFolder ? [selectedAudioFolder] : []}
                onSelectionChange={(keys) =>
                  setSelectedAudioFolder(Array.from(keys)[0] as string)
                }
                size="sm"
              >
                {audioFolders.map((folder) => (
                  <SelectItem key={folder.path} textValue={folder.name}>
                    {folder.name} ({folder.file_count} files)
                  </SelectItem>
                ))}
              </Select>

              <Select
                label="Text CSV File"
                placeholder="Choose CSV file"
                selectedKeys={selectedCSV ? [selectedCSV] : []}
                onSelectionChange={(keys) =>
                  setSelectedCSV(Array.from(keys)[0] as string)
                }
                size="sm"
              >
                {csvFiles.map((csv) => (
                  <SelectItem key={csv.filepath} textValue={csv.filename}>
                    {csv.filename}
                  </SelectItem>
                ))}
              </Select>
            </CardBody>
          </Card>

          {/* Processing Options Card */}
          <Card>
            <CardHeader>
              <h2 className="font-semibold">Processing Options</h2>
            </CardHeader>
            <Divider />
            <CardBody className="gap-3">
              <div className="grid grid-cols-2 gap-3">
                <Select
                  label="Text Position"
                  selectedKeys={[position]}
                  onSelectionChange={(keys) =>
                    setPosition(Array.from(keys)[0] as string)
                  }
                  size="sm"
                >
                  <SelectItem key="center">Center</SelectItem>
                  <SelectItem key="top">Top</SelectItem>
                  <SelectItem key="bottom">Bottom</SelectItem>
                </Select>

                <Select
                  label="Text Preset"
                  selectedKeys={[preset]}
                  onSelectionChange={(keys) =>
                    setPreset(Array.from(keys)[0] as string)
                  }
                  size="sm"
                >
                  <SelectItem key="instagram1">Instagram 1</SelectItem>
                  <SelectItem key="instagram2">Instagram 2</SelectItem>
                  <SelectItem key="tiktok">Tiktok</SelectItem>
                  <SelectItem key="bold">Bold</SelectItem>
                  <SelectItem key="clean">Clean</SelectItem>
                  <SelectItem key="subtle">Subtle</SelectItem>
                  <SelectItem key="yellow">Yellow</SelectItem>
                  <SelectItem key="shadow">Shadow</SelectItem>
                </Select>

                <Select
                  label="Fit Mode"
                  selectedKeys={[fitMode]}
                  onSelectionChange={(keys) =>
                    setFitMode(Array.from(keys)[0] as string)
                  }
                  size="sm"
                >
                  <SelectItem key="cover">Cover</SelectItem>
                  <SelectItem key="contain">Contain</SelectItem>
                </Select>

                <Input
                  label="Unique Amount"
                  type="number"
                  value={uniqueAmount}
                  onValueChange={setUniqueAmount}
                  isDisabled={!uniqueMode}
                  size="sm"
                />
              </div>

              <Switch
                isSelected={uniqueMode}
                onValueChange={setUniqueMode}
                size="sm"
              >
                Unique Mode (Diverse combinations)
              </Switch>

              {jobStatus && (
                <>
                  <Divider className="my-2" />
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Status:</span>
                      <Chip
                        color={
                          jobStatus.status === "completed"
                            ? "success"
                            : jobStatus.status === "failed"
                              ? "danger"
                              : jobStatus.status === "processing"
                                ? "primary"
                                : "default"
                        }
                        size="sm"
                      >
                        {jobStatus.status}
                      </Chip>
                    </div>

                    <Progress
                      value={jobStatus.progress}
                      color={
                        jobStatus.status === "completed"
                          ? "success"
                          : jobStatus.status === "failed"
                            ? "danger"
                            : "primary"
                      }
                      size="sm"
                    />

                    <p className="text-xs text-default-500">
                      {jobStatus.message}
                    </p>

                    {jobStatus.output_files.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold mb-1">
                          Output Files ({jobStatus.output_files.length}):
                        </p>
                        <div className="text-xs text-default-500 max-h-20 overflow-y-auto">
                          {jobStatus.output_files.slice(0, 3).map((file, i) => (
                            <div key={i}>{file.split("/").pop()}</div>
                          ))}
                          {jobStatus.output_files.length > 3 && (
                            <div>
                              ... and {jobStatus.output_files.length - 3} more
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {jobStatus.status === "completed" && (
                      <Button
                        color="success"
                        variant="flat"
                        size="sm"
                        className="w-full"
                        onPress={() => router.push("/dashboard/projects")}
                      >
                        View Projects
                      </Button>
                    )}
                  </div>
                </>
              )}
            </CardBody>
          </Card>

          {/* Video Folder Name Card */}
          <Card>
            <CardHeader>
              <h2 className="font-semibold">Output Project Name</h2>
            </CardHeader>
            <Divider />
            <CardBody className="">
              <Input
                placeholder="Cute Dog Channel "
              />
            </CardBody>
          </Card>

          {/* Start Processing Button */}
          <Button
            color="primary"
            size="lg"
            className="w-full"
            onPress={handleStartBatch}
            isLoading={processing}
            isDisabled={
              !selectedVideoFolder || !selectedAudioFolder || !selectedCSV
            }
          >
            Start Batch Processing
          </Button>
        </div>

        {/* Right side - Video Preview */}
        <div className="lg:col-span-1">
          <Card className="sticky top-8">
            <CardHeader>
              <h2 className="font-semibold">Preview</h2>
            </CardHeader>
            <Divider />
            <CardBody>
              <div className="relative aspect-[9/16] max-h-[75vh] bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg overflow-hidden shadow-lg">
                {/* Video background */}
                {previewVideoSrc ? (
                  <video
                    className={`absolute inset-0 w-full h-full ${getFitModeStyle()}`}
                    src={`${previewVideoSrc}#t=0.1`}
                    preload="metadata"
                    muted
                    playsInline
                  />
                ) : (
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-orange-500/20">
                    <div className="absolute inset-0 opacity-20">
                      <div className="grid grid-cols-3 grid-rows-3 h-full">
                        {Array.from({ length: 9 }).map((_, i) => (
                          <div
                            key={i}
                            className="border border-white/10"
                            style={{
                              background: `linear-gradient(${45 + i * 20}deg, rgba(139, 92, 246, 0.3), rgba(236, 72, 153, 0.3))`,
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Text overlay with live preview */}
                <div
                  className={`absolute inset-0 flex justify-center ${getTextPositionStyle()} p-4`}
                >
                  <div className="text-center max-w-[85%]">
                    <p
                      className={`${getTextPresetStyle(preset)} leading-tight `}
                    >
                      Sample Text
                    </p>
                  </div>
                </div>

                {/* Preview label */}
                <div className="absolute top-2 right-2">
                  <Chip
                    size="sm"
                    variant="flat"
                    color="default"
                    className="text-xs"
                  >
                    Live
                  </Chip>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
