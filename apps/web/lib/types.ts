// Shared types for the application

export interface BaseFile {
  filename: string;
  filepath: string;
  size: number;
  modified: string;
  type: string;
}

export interface VideoFile extends BaseFile {
  type: "video";
}

export interface AudioFile extends BaseFile {
  type: "audio";
}

export interface CSVFile extends BaseFile {
  type: "csv";
}

export interface OutputFile extends BaseFile {
  folder: string;
}

export interface Folder {
  name: string;
  path: string;
  file_count: number;
  total_size: number;
}

export type FileType = "video" | "audio" | "csv" | "output";
