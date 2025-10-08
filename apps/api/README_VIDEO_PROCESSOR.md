# Video Processor API

API REST completa para procesamiento batch de videos con texto y audio. Incluye gestión de archivos, uploads, y procesamiento. Convierte la funcionalidad de `batch_core.py` y `ui.py` en endpoints HTTP.

## 🎯 Características Principales

- ✅ **Upload de Archivos**: Videos, audios y CSV
- ✅ **Gestión de Archivos**: Listar, eliminar, mover archivos
- ✅ **Gestión de Carpetas**: Crear y organizar carpetas
- ✅ **Procesamiento de Videos**: Individual y batch
- ✅ **Validación**: Límites de tamaño y formatos permitidos
- ✅ **Tracking de Jobs**: Monitoreo de progreso en tiempo real
- ✅ **100% Preparado para Next.js**: CORS configurado, respuestas JSON

## 📋 Índice de Endpoints

### File Upload
- [POST /upload/video](#upload-video) - Subir video
- [POST /upload/audio](#upload-audio) - Subir audio
- [POST /upload/csv](#upload-csv) - Subir y parsear CSV

### File Management
- [GET /files/videos](#list-video-files) - Listar videos con detalles
- [GET /files/audios](#list-audio-files) - Listar audios con detalles
- [GET /files/csv](#list-csv-files) - Listar CSV con detalles
- [DELETE /files/delete](#delete-file) - Eliminar archivo
- [POST /files/move](#move-file) - Mover archivo

### Folder Management
- [GET /folders/{category}](#list-folders) - Listar carpetas
- [POST /folders/create](#create-folder) - Crear carpeta

### Processing (Original)
- [POST /list-videos](#list-videos) - Listar videos de carpeta
- [POST /list-audios](#list-audios) - Listar audios de carpeta
- [POST /parse-csv](#parse-csv) - Parsear CSV
- [POST /process-single](#process-single) - Procesar video individual
- [POST /process-batch](#process-batch) - Procesar batch
- [GET /status/{job_id}](#get-status) - Estado de job
- [GET /jobs](#list-jobs) - Listar todos los jobs
- [DELETE /jobs/{job_id}](#delete-job) - Eliminar job
- [GET /default-config](#default-config) - Configuración por defecto

---

## 🎬 Endpoints de Upload

### Upload Video

**POST** `/api/video-processor/upload/video`

Sube un archivo de video al servidor. Genera nombre único automáticamente.

**Form Data:**
- `file`: Video file (required)
- `subfolder`: Subfolder name (optional)

**Formatos permitidos:** `.mp4`, `.mov`, `.m4v`, `.avi`, `.mkv`
**Tamaño máximo:** 500 MB

**Response:**
```json
{
  "filename": "myvideo_20240115_143022_a3f4b2c8.mp4",
  "filepath": "D:/Work/video/videos/myvideo_20240115_143022_a3f4b2c8.mp4",
  "size": 15728640,
  "message": "Video uploaded successfully to videos"
}
```

**Ejemplo cURL:**
```bash
curl -X POST http://localhost:8000/api/video-processor/upload/video \
  -F "file=@/path/to/video.mp4" \
  -F "subfolder=my_project"
```

**Ejemplo Next.js:**
```typescript
const formData = new FormData();
formData.append('file', videoFile);
formData.append('subfolder', 'my_project');

const response = await fetch('/api/video-processor/upload/video', {
  method: 'POST',
  body: formData
});
```

---

### Upload Audio

**POST** `/api/video-processor/upload/audio`

Sube un archivo de audio al servidor.

**Form Data:**
- `file`: Audio file (required)
- `subfolder`: Subfolder name (optional)

**Formatos permitidos:** `.mp3`, `.wav`, `.m4a`
**Tamaño máximo:** 50 MB

**Response:**
```json
{
  "filename": "music_20240115_143022_b5e6c3d9.mp3",
  "filepath": "D:/Work/video/audios/music_20240115_143022_b5e6c3d9.mp3",
  "size": 5242880,
  "message": "Audio uploaded successfully to audios"
}
```

---

### Upload CSV

**POST** `/api/video-processor/upload/csv`

Sube y parsea un archivo CSV. Opcionalmente guarda el archivo.

**Form Data:**
- `file`: CSV file (required)
- `save_file`: Boolean, default true (optional)

**Tamaño máximo:** 5 MB

**Response:**
```json
{
  "combinations": [
    ["Texto 1 parte 1", "Texto 1 parte 2"],
    ["Texto 2 parte 1", "Texto 2 parte 2"]
  ],
  "count": 2,
  "saved": true,
  "filepath": "D:/Work/video/csv/texts_20240115_143022_c7f8d4e1.csv",
  "filename": "texts_20240115_143022_c7f8d4e1.csv"
}
```

---

## 📁 Endpoints de Gestión de Archivos

### List Video Files

**GET** `/api/video-processor/files/videos`

Lista todos los videos con información detallada.

**Query Params:**
- `subfolder`: Filter by subfolder (optional)

**Response:**
```json
{
  "files": [
    {
      "filename": "video_20240115_143022_a3f4b2c8.mp4",
      "filepath": "D:/Work/video/videos/video_20240115_143022_a3f4b2c8.mp4",
      "size": 15728640,
      "modified": "2024-01-15T14:30:22",
      "type": "video"
    }
  ],
  "count": 1
}
```

---

### List Audio Files

**GET** `/api/video-processor/files/audios`

Lista todos los audios con información detallada.

**Query Params:**
- `subfolder`: Filter by subfolder (optional)

**Response:**
```json
{
  "files": [
    {
      "filename": "music_20240115_143022_b5e6c3d9.mp3",
      "filepath": "D:/Work/video/audios/music_20240115_143022_b5e6c3d9.mp3",
      "size": 5242880,
      "modified": "2024-01-15T14:30:22",
      "type": "audio"
    }
  ],
  "count": 1
}
```

---

### List CSV Files

**GET** `/api/video-processor/files/csv`

Lista todos los archivos CSV guardados.

**Response:**
```json
{
  "files": [
    {
      "filename": "texts_20240115_143022_c7f8d4e1.csv",
      "filepath": "D:/Work/video/csv/texts_20240115_143022_c7f8d4e1.csv",
      "size": 2048,
      "modified": "2024-01-15T14:30:22",
      "type": "csv"
    }
  ],
  "count": 1
}
```

---

### Delete File

**DELETE** `/api/video-processor/files/delete`

Elimina un archivo del servidor.

**Request Body:**
```json
{
  "filepath": "D:/Work/video/videos/old_video.mp4"
}
```

**Response:**
```json
{
  "message": "File deleted successfully",
  "filepath": "D:/Work/video/videos/old_video.mp4"
}
```

---

### Move File

**POST** `/api/video-processor/files/move`

Mueve un archivo a otra carpeta.

**Request Body:**
```json
{
  "source_path": "D:/Work/video/videos/video.mp4",
  "destination_folder": "D:/Work/video/videos/archive"
}
```

**Response:**
```json
{
  "message": "File moved successfully",
  "source": "D:/Work/video/videos/video.mp4",
  "destination": "D:/Work/video/videos/archive/video.mp4"
}
```

---

## 📂 Endpoints de Gestión de Carpetas

### List Folders

**GET** `/api/video-processor/folders/{category}`

Lista todas las subcarpetas en una categoría.

**Path Params:**
- `category`: videos, audios, csv, o output

**Response:**
```json
{
  "folders": [
    {
      "name": "project_1",
      "path": "D:/Work/video/videos/project_1",
      "file_count": 15,
      "total_size": 157286400
    }
  ],
  "count": 1
}
```

---

### Create Folder

**POST** `/api/video-processor/folders/create`

Crea una nueva subcarpeta en una categoría.

**Request Body:**
```json
{
  "parent_category": "videos",
  "folder_name": "new_project"
}
```

**Response:**
```json
{
  "message": "Folder created successfully",
  "folder_name": "new_project",
  "folder_path": "D:/Work/video/videos/new_project"
}
```

---

## 🎥 Endpoints de Procesamiento (Originales)

### 1. Listar Videos
**POST** `/api/video-processor/list-videos`

Lista todos los archivos de video en una carpeta.

```json
{
  "folder_path": "D:/Work/video/videos"
}
```

**Response:**
```json
{
  "videos": ["D:/Work/video/videos/video1.mp4", "..."],
  "count": 5
}
```

---

### 2. Listar Audios
**POST** `/api/video-processor/list-audios`

Lista todos los archivos de audio en una carpeta.

```json
{
  "folder_path": "D:/Work/video/audios"
}
```

**Response:**
```json
{
  "audios": ["D:/Work/video/audios/audio1.mp3", "..."],
  "count": 3
}
```

---

### 3. Parsear CSV de Textos
**POST** `/api/video-processor/parse-csv`

Sube y parsea un archivo CSV con combinaciones de texto.

**Form Data:**
- `file`: CSV file

**Response:**
```json
{
  "combinations": [
    ["Texto 1 segmento 1", "Texto 1 segmento 2"],
    ["Texto 2 segmento 1", "Texto 2 segmento 2"]
  ],
  "count": 2
}
```

---

### 4. Procesar Video Individual
**POST** `/api/video-processor/process-single`

Procesa un solo video con texto y audio.

```json
{
  "video_path": "D:/Work/video/videos/input.mp4",
  "audio_path": "D:/Work/video/audios/music.mp3",
  "text_segments": ["Primer texto", "Segundo texto", "Tercer texto"],
  "output_path": "D:/Work/video/output/result.mp4",
  "config": {
    "position": "center",
    "margin_pct": 0.16,
    "duration_policy": "shortest",
    "canvas_size": [1080, 1920],
    "fit_mode": "cover",
    "music_gain_db": -8,
    "mix_audio": false,
    "preset": "bold"
  }
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0.0,
  "message": "Job queued",
  "output_files": []
}
```

---

### 5. Procesar Batch de Videos
**POST** `/api/video-processor/process-batch`

Procesa múltiples videos en batch (equivalente a la UI de Tkinter).

```json
{
  "video_folder": "D:/Work/video/videos",
  "audio_folder": "D:/Work/video/audios",
  "text_combinations": [
    ["Texto 1 parte 1", "Texto 1 parte 2"],
    ["Texto 2 parte 1", "Texto 2 parte 2"]
  ],
  "output_folder": "D:/Work/video/output",
  "unique_mode": true,
  "unique_amount": 50,
  "config": {
    "position": "bottom",
    "preset": "bold"
  }
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_jobs": 50,
  "message": "Batch job started with 50 videos to process"
}
```

**Parámetros:**
- `unique_mode`: Si es `true`, usa selección determinística diversa por video
- `unique_amount`: Cantidad de combinaciones únicas a generar
- Si `unique_mode` es `false`, genera todas las combinaciones posibles (Cartesiano)

---

### 6. Consultar Estado de Job
**GET** `/api/video-processor/status/{job_id}`

Consulta el estado de un job en procesamiento.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "message": "Processing 23/50",
  "output_files": [
    "D:/Work/video/output/video1/audio1__combo1_texto.mp4"
  ]
}
```

**Status posibles:**
- `pending`: En cola
- `processing`: Procesando
- `completed`: Completado
- `failed`: Falló

---

### 7. Listar Todos los Jobs
**GET** `/api/video-processor/jobs`

Lista todos los jobs y sus estados.

**Response:**
```json
[
  {
    "job_id": "...",
    "status": "completed",
    "progress": 100.0,
    "message": "Completed 50/50 files",
    "output_files": ["..."]
  }
]
```

---

### 8. Eliminar Job
**DELETE** `/api/video-processor/jobs/{job_id}`

Elimina un job del tracking (no detiene el procesamiento activo).

**Response:**
```json
{
  "message": "Job deleted",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 9. Obtener Configuración por Defecto
**GET** `/api/video-processor/default-config`

Obtiene la configuración por defecto del procesador.

**Response:**
```json
{
  "position": "center",
  "margin_pct": 0.16,
  "duration_policy": "shortest",
  "fixed_seconds": null,
  "canvas_size": [1080, 1920],
  "fit_mode": "cover",
  "music_gain_db": -8,
  "mix_audio": false,
  "preset": null,
  "outline_px": 2,
  "fontsize_ratio": 0.036
}
```

---

## Configuración del Procesamiento

### `position`
- `"center"`: Texto centrado
- `"top"`: Texto arriba
- `"bottom"`: Texto abajo

### `duration_policy`
- `"shortest"`: Duracion = min(video, audio)
- `"audio"`: Duracion del audio
- `"video"`: Duracion del video
- `"fixed"`: Duracion fija (requiere `fixed_seconds`)

### `fit_mode`
- `"cover"`: Cubre todo el canvas (crop/zoom para videos landscape)
- `"contain"`: Contiene el video completo (letterbox)
- `"zoom"`: Zoom (alias de cover)

### `preset`
Presets de estilo de texto:
- `"clean"`: Blanco sin borde
- `"bold"`: Blanco con borde negro grueso
- `"subtle"`: Blanco con borde gris fino
- `"yellow"`: Amarillo con borde negro
- `"shadow"`: Blanco con borde gris oscuro

---

## Flujo de Uso Típico

### Ejemplo 1: Batch Processing (equivalente a UI)

```bash
# 1. Listar recursos disponibles
curl -X POST http://localhost:8000/api/video-processor/list-videos \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "D:/Work/video/videos"}'

curl -X POST http://localhost:8000/api/video-processor/list-audios \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "D:/Work/video/audios"}'

# 2. Subir y parsear CSV
curl -X POST http://localhost:8000/api/video-processor/parse-csv \
  -F "file=@texts.csv"

# 3. Iniciar batch processing
curl -X POST http://localhost:8000/api/video-processor/process-batch \
  -H "Content-Type: application/json" \
  -d '{
    "video_folder": "D:/Work/video/videos",
    "audio_folder": "D:/Work/video/audios",
    "text_combinations": [
      ["Hola mundo", "Segundo texto"],
      ["Otra combinación", "Más texto"]
    ],
    "output_folder": "D:/Work/video/output",
    "unique_mode": true,
    "unique_amount": 100
  }'

# Respuesta: {"job_id": "abc-123", "total_jobs": 100, ...}

# 4. Monitorear progreso
curl http://localhost:8000/api/video-processor/status/abc-123

# 5. Ver todos los jobs
curl http://localhost:8000/api/video-processor/jobs
```

### Ejemplo 2: Procesamiento Individual

```bash
curl -X POST http://localhost:8000/api/video-processor/process-single \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "D:/Work/video/videos/myvideo.mp4",
    "audio_path": "D:/Work/video/audios/music.mp3",
    "text_segments": ["Texto 1", "Texto 2", "Texto 3"],
    "output_path": "D:/Work/video/output/result.mp4",
    "config": {
      "position": "bottom",
      "preset": "bold",
      "fit_mode": "cover"
    }
  }'
```

---

## Iniciar el Servidor

```bash
cd apps/api
python app.py
```

O con uvicorn:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Documentación Interactiva

Una vez iniciado el servidor:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Notas Importantes

1. **Storage de Jobs**: Actualmente los jobs se almacenan en memoria. Para producción, usar Redis o base de datos.

2. **Paths Absolutos**: Todos los paths deben ser absolutos. En Windows, usar formato: `D:/Work/video/...` o `D:\\Work\\video\\...`

3. **Background Tasks**: El procesamiento se ejecuta en background tasks. Los jobs NO se detienen al eliminarlos del tracking.

4. **Límites**: Sin límites de concurrencia actualmente. Para producción, implementar cola con Celery o similar.

5. **Archivos de Salida**: Los archivos se organizan en carpetas por video base:
   ```
   output/
     video1/
       audio1__combo1_texto.mp4
       audio2__combo1_texto.mp4
     video2/
       audio1__combo2_otro.mp4
   ```

---

## Equivalencia UI → API

| Funcionalidad UI | Endpoint API |
|------------------|--------------|
| Browse Videos | POST `/list-videos` |
| Browse Audios | POST `/list-audios` |
| Browse CSV | POST `/parse-csv` |
| Checkbox "Unique" | `unique_mode: true` |
| Input cantidad | `unique_amount: 100` |
| Botón "Render" | POST `/process-batch` |
| Log de progreso | GET `/status/{job_id}` (polling) |

---

---

## 🚀 Integración con Next.js

### Estructura de Cliente Recomendada

```typescript
// lib/api/video-processor.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Upload functions
export async function uploadVideo(file: File, subfolder?: string) {
  const formData = new FormData();
  formData.append('file', file);
  if (subfolder) formData.append('subfolder', subfolder);

  const response = await fetch(`${API_BASE}/api/video-processor/upload/video`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) throw new Error('Upload failed');
  return response.json();
}

export async function uploadAudio(file: File, subfolder?: string) {
  const formData = new FormData();
  formData.append('file', file);
  if (subfolder) formData.append('subfolder', subfolder);

  const response = await fetch(`${API_BASE}/api/video-processor/upload/audio`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) throw new Error('Upload failed');
  return response.json();
}

// File management
export async function listVideos(subfolder?: string) {
  const params = subfolder ? `?subfolder=${subfolder}` : '';
  const response = await fetch(`${API_BASE}/api/video-processor/files/videos${params}`);
  return response.json();
}

export async function deleteFile(filepath: string) {
  const response = await fetch(`${API_BASE}/api/video-processor/files/delete`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filepath }),
  });
  return response.json();
}

// Processing
export async function processBatch(params: BatchProcessParams) {
  const response = await fetch(`${API_BASE}/api/video-processor/process-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return response.json();
}

export async function getJobStatus(jobId: string) {
  const response = await fetch(`${API_BASE}/api/video-processor/status/${jobId}`);
  return response.json();
}
```

### Componente de Upload con React Hook Form

```typescript
// components/VideoUploader.tsx
'use client';

import { useForm } from 'react-hook-form';
import { uploadVideo } from '@/lib/api/video-processor';
import { useState } from 'react';

export function VideoUploader() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const result = await uploadVideo(file);
      console.log('Uploaded:', result);
      // Refresh file list, show success, etc.
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <input
        type="file"
        accept=".mp4,.mov,.m4v,.avi,.mkv"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleUpload(file);
        }}
        disabled={uploading}
      />
      {uploading && <div>Uploading... {progress}%</div>}
    </div>
  );
}
```

### Job Monitoring con SWR

```typescript
// hooks/useJobStatus.ts
import useSWR from 'swr';
import { getJobStatus } from '@/lib/api/video-processor';

export function useJobStatus(jobId: string | null) {
  const { data, error, mutate } = useSWR(
    jobId ? `/api/video-processor/status/${jobId}` : null,
    () => getJobStatus(jobId!),
    {
      refreshInterval: (data) => {
        // Stop polling when completed or failed
        if (data?.status === 'completed' || data?.status === 'failed') {
          return 0;
        }
        return 2000; // Poll every 2 seconds
      },
    }
  );

  return {
    job: data,
    isLoading: !error && !data,
    isError: error,
    refresh: mutate,
  };
}

// Usage in component
function ProcessingMonitor({ jobId }: { jobId: string }) {
  const { job, isLoading } = useJobStatus(jobId);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h3>Status: {job.status}</h3>
      <div className="progress-bar">
        <div style={{ width: `${job.progress}%` }} />
      </div>
      <p>{job.message}</p>
      {job.output_files.length > 0 && (
        <ul>
          {job.output_files.map((file) => (
            <li key={file}>{file}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### Batch Processing Flow

```typescript
// components/BatchProcessor.tsx
'use client';

import { useState } from 'react';
import { processBatch } from '@/lib/api/video-processor';
import { useJobStatus } from '@/hooks/useJobStatus';

export function BatchProcessor() {
  const [jobId, setJobId] = useState<string | null>(null);
  const { job } = useJobStatus(jobId);

  const handleStartBatch = async () => {
    const result = await processBatch({
      video_folder: 'D:/Work/video/videos',
      audio_folder: 'D:/Work/video/audios',
      text_combinations: [
        ['Text 1 part 1', 'Text 1 part 2'],
        ['Text 2 part 1', 'Text 2 part 2'],
      ],
      output_folder: 'D:/Work/video/output',
      unique_mode: true,
      unique_amount: 50,
      config: {
        position: 'center',
        preset: 'bold',
      },
    });

    setJobId(result.job_id);
  };

  return (
    <div>
      <button onClick={handleStartBatch}>Start Batch</button>

      {job && (
        <div>
          <h3>Progress: {job.progress.toFixed(1)}%</h3>
          <p>{job.message}</p>
        </div>
      )}
    </div>
  );
}
```

---

## 📦 Configuración de Ambiente

### Variables de Entorno

Crea un archivo `.env` en `apps/api/`:

```bash
# Storage configuration
STORAGE_DIR=D:/Work/video

# Server configuration
HOST=0.0.0.0
PORT=8000

# CORS (Next.js dev server)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Next.js `.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ⚙️ Configuración de Límites

Puedes modificar los límites en `apps/api/config.py`:

```python
MAX_FILE_SIZE = {
    "video": 500 * 1024 * 1024,  # 500 MB
    "audio": 50 * 1024 * 1024,   # 50 MB
    "csv": 5 * 1024 * 1024,      # 5 MB
}
```

---

## 🧪 Testing

### Test Endpoints Básicos
```bash
python test_api.py
```

### Test Upload y Gestión
```bash
python test_upload_api.py
```

### Swagger UI
http://localhost:8000/docs

### ReDoc
http://localhost:8000/redoc

---

## 🎯 Próximos Pasos para Next.js

### Componentes a Crear

1. **File Management**
   - `VideoLibrary` - Grid de videos con preview
   - `AudioLibrary` - Lista de audios
   - `FileUploader` - Drag & drop upload
   - `FolderBrowser` - Navegador de carpetas

2. **Processing**
   - `ConfigForm` - Formulario de configuración
   - `TextCombinationsEditor` - Editor de combinaciones de texto
   - `BatchProcessForm` - Formulario de batch processing
   - `JobMonitor` - Monitor de progreso con polling

3. **UI/UX**
   - Progress bars
   - File previews
   - Toast notifications
   - Error handling

### Recomendaciones

- ✅ Usar **React Query** o **SWR** para polling de jobs
- ✅ Implementar **optimistic updates** en file operations
- ✅ Agregar **upload progress** con XMLHttpRequest
- ✅ Usar **Zustand** o **Context** para estado global
- ✅ Implementar **WebSockets** para updates en tiempo real (opcional)
- ✅ Agregar **retry logic** para requests fallidos
- ✅ Implementar **file chunking** para uploads grandes (opcional)
