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

  const [position, setPosition] = useState("center");
  const [preset, setPreset] = useState("bold");
  const [fitMode, setFitMode] = useState("cover");
  const [uniqueMode, setUniqueMode] = useState(true);
  const [uniqueAmount, setUniqueAmount] = useState("50");

  const [processing, setProcessing] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (jobStatus && (jobStatus.status === "pending" || jobStatus.status === "processing")) {
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
        fetch(`${API_URL}/api/video-processor/files/csv`)
      ]);

      const [vData, aData, cData] = await Promise.all([
        vRes.json(),
        aRes.json(),
        cRes.json()
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

  const checkJobStatus = async (jobId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/video-processor/processing/status/${jobId}`);
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
      // Use preview endpoint to get CSV combinations
      const res = await fetch(`${API_URL}/api/video-processor/files/preview/csv?filepath=${encodeURIComponent(selectedCSV)}`);

      const csvData = await res.json();
      const combinations = csvData.combinations || [];

      const batchRes = await fetch(`${API_URL}/api/video-processor/processing/process-batch`, {
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
            fit_mode: fitMode
          }
        })
      });

      const batchData = await batchRes.json();
      setJobStatus({
        job_id: batchData.job_id,
        status: "pending",
        progress: 0,
        message: batchData.message,
        output_files: []
      });
    } catch (error) {
      console.error("Error starting batch:", error);
      setProcessing(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Batch Video Processing</h1>
        <p className="text-default-500">
          Create multiple videos with different combinations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Select Sources</h2>
            </CardHeader>
            <Divider />
            <CardBody className="gap-4">
              <Select
                label="Video Folder"
                placeholder="Choose video folder"
                selectedKeys={selectedVideoFolder ? [selectedVideoFolder] : []}
                onSelectionChange={(keys) => setSelectedVideoFolder(Array.from(keys)[0] as string)}
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
                onSelectionChange={(keys) => setSelectedAudioFolder(Array.from(keys)[0] as string)}
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
                onSelectionChange={(keys) => setSelectedCSV(Array.from(keys)[0] as string)}
              >
                {csvFiles.map((csv) => (
                  <SelectItem key={csv.filepath} textValue={csv.filename}>
                    {csv.filename}
                  </SelectItem>
                ))}
              </Select>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Processing Options</h2>
            </CardHeader>
            <Divider />
            <CardBody className="gap-4">
              <div className="grid grid-cols-2 gap-4">
                <Select
                  label="Text Position"
                  selectedKeys={[position]}
                  onSelectionChange={(keys) => setPosition(Array.from(keys)[0] as string)}
                >
                  <SelectItem key="center">Center</SelectItem>
                  <SelectItem key="top">Top</SelectItem>
                  <SelectItem key="bottom">Bottom</SelectItem>
                </Select>

                <Select
                  label="Text Preset"
                  selectedKeys={[preset]}
                  onSelectionChange={(keys) => setPreset(Array.from(keys)[0] as string)}
                >
                  <SelectItem key="bold">Bold</SelectItem>
                  <SelectItem key="clean">Clean</SelectItem>
                  <SelectItem key="subtle">Subtle</SelectItem>
                  <SelectItem key="yellow">Yellow</SelectItem>
                  <SelectItem key="shadow">Shadow</SelectItem>
                </Select>

                <Select
                  label="Fit Mode"
                  selectedKeys={[fitMode]}
                  onSelectionChange={(keys) => setFitMode(Array.from(keys)[0] as string)}
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
                />
              </div>

              <Switch
                isSelected={uniqueMode}
                onValueChange={setUniqueMode}
              >
                Unique Mode (Diverse combinations)
              </Switch>
            </CardBody>
          </Card>
        </div>

        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Start Processing</h2>
            </CardHeader>
            <Divider />
            <CardBody className="gap-4">
              <Button
                color="primary"
                size="lg"
                className="w-full"
                onPress={handleStartBatch}
                isLoading={processing}
                isDisabled={!selectedVideoFolder || !selectedAudioFolder || !selectedCSV}
              >
                Start Batch Processing
              </Button>

              {jobStatus && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Status:</span>
                    <Chip
                      color={
                        jobStatus.status === "completed" ? "success" :
                        jobStatus.status === "failed" ? "danger" :
                        jobStatus.status === "processing" ? "primary" : "default"
                      }
                      size="sm"
                    >
                      {jobStatus.status}
                    </Chip>
                  </div>

                  <Progress
                    value={jobStatus.progress}
                    color={
                      jobStatus.status === "completed" ? "success" :
                      jobStatus.status === "failed" ? "danger" : "primary"
                    }
                  />

                  <p className="text-xs text-default-500">{jobStatus.message}</p>

                  {jobStatus.output_files.length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-semibold mb-2">
                        Output Files ({jobStatus.output_files.length}):
                      </p>
                      <div className="text-xs text-default-500 max-h-32 overflow-y-auto">
                        {jobStatus.output_files.slice(0, 5).map((file, i) => (
                          <div key={i}>{file.split("/").pop()}</div>
                        ))}
                        {jobStatus.output_files.length > 5 && (
                          <div>... and {jobStatus.output_files.length - 5} more</div>
                        )}
                      </div>
                    </div>
                  )}

                  {jobStatus.status === "completed" && (
                    <Button
                      color="success"
                      variant="flat"
                      className="w-full mt-4"
                      onPress={() => router.push("/dashboard/projects")}
                    >
                      View Projects
                    </Button>
                  )}
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
