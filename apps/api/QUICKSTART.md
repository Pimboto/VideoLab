# 🚀 Quick Start Guide - API v2

## Paso 1: Iniciar el Servidor

### Opción A: Usando el script (Recomendado)
```bash
# Windows
start_server.bat

# O directamente
python app_v2.py
```

### Opción B: Configuración manual
```bash
# 1. Crear .env
cp .env.example .env

# 2. Editar .env si es necesario
# (por defecto está configurado para D:/Work/video)

# 3. Iniciar servidor
python app_v2.py
```

Deberías ver:
```
INFO:     Starting Video Processor API v2.0.0
INFO:     Storage directories initialized
INFO:     Job service initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Paso 2: Verificar que Funciona

Abre tu navegador:
- Health Check: http://localhost:8000/health
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

O usa curl:
```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "message": "API is running",
  "version": "2.0.0"
}
```

## Paso 3: Ejecutar Tests Completos

### Opción A: Usar el script
```bash
# Windows (asegúrate que el servidor esté corriendo)
run_tests.bat
```

### Opción B: Ejecutar manualmente
```bash
# En otra terminal (mientras el servidor corre)
python test_api_v2.py
```

## 🧪 Qué Prueban los Tests

El test completo (`test_api_v2.py`) ejecuta:

### Phase 1: Folder Management
- ✅ Crear carpetas de prueba
- ✅ Listar carpetas existentes

### Phase 2: File Uploads
- ✅ Subir un video real desde `D:/Work/video/videos/`
- ✅ Subir un audio real desde `D:/Work/video/audios/`
- ✅ Subir y parsear CSV desde `D:/Work/video/texts.csv`

### Phase 3: File Management
- ✅ Listar videos subidos
- ✅ Listar audios subidos
- ✅ Obtener información de archivos

### Phase 4: Configuration
- ✅ Obtener configuración por defecto
- ✅ Verificar presets disponibles

### Phase 5: Single Video Processing (Interactivo)
- ✅ Procesar 1 video con texto y audio
- ✅ Monitorear progreso en tiempo real
- ✅ Verificar output

### Phase 6: Batch Processing (Interactivo)
- ✅ Procesar 3 videos en batch
- ✅ Usar textos del CSV
- ✅ Modo "unique" para diversidad
- ✅ Monitorear progreso

### Phase 7: Job Management
- ✅ Listar todos los jobs
- ✅ Ver estados y progreso

## 📊 Output Esperado

### Creación de Archivos

Los tests crean:
```
D:/Work/video/
├── videos/
│   └── test_uploads/          # Videos subidos en tests
│       └── video_*_*.mp4
├── audios/
│   └── test_uploads/          # Audios subidos en tests
│       └── audio_*_*.mp3
├── csv/
│   └── texts_*_*.csv          # CSV guardado
└── output_test_v2/            # Videos procesados
    ├── test_single_output.mp4
    └── video (1)/
        ├── ReelAudio-2148__combo1_when.mp4
        ├── ReelAudio-25445__combo2_when.mp4
        └── ...
```

### Console Output

```
╔════════════════════════════════════════════════════════════════════╗
║          VIDEO PROCESSOR API V2 - COMPREHENSIVE TEST SUITE         ║
║                  Professional Architecture Edition                 ║
╚════════════════════════════════════════════════════════════════════╝

======================================================================
  CHECKING SERVER
======================================================================
✅ Server is running: API is running
ℹ️  Version: 2.0.0

======================================================================
  PHASE 1: FOLDER MANAGEMENT
======================================================================
✅ Created folder: videos/test_uploads
✅ Created folder: audios/test_uploads
...

======================================================================
  PHASE 2: FILE UPLOADS
======================================================================
ℹ️  Uploading: video (1).mp4 (5.23 MB)
✅ Video uploaded: video_20250107_143022_a3f4b2c8.mp4
...

======================================================================
  MONITORING JOB: 550e8400-e29b-41d4-a716-446655440000
======================================================================
🔄 [PROCESSING] 0.0% - Building job list...
🔄 [PROCESSING] 33.3% - Processing 1/3
🔄 [PROCESSING] 66.7% - Processing 2/3
✅ [COMPLETED] 100.0% - Completed 3/3 files
✅ Job completed!
ℹ️  Output files: 3
  1. ReelAudio-2148__combo1_when.mp4
  2. ReelAudio-25445__combo2_when.mp4
  3. ReelAudio-29390__combo3_me.mp4

======================================================================
  TEST SUITE COMPLETED
======================================================================
✅ All API endpoints tested!
ℹ️  Check output files in: D:\Work\video\output_test_v2
ℹ️  API documentation: http://localhost:8000/docs

======================================================================
  🎉 Professional Architecture - Fully Tested! 🎉
======================================================================
```

## ⚙️ Opciones de Test

### Test Rápido (Solo Uploads)
Edita `test_api_v2.py` y responde 'n' cuando te pregunte:
```
▶️  Run single video processing test? (y/n): n
▶️  Run batch processing test (3 videos)? (y/n): n
```

### Test Completo (Con Procesamiento)
Responde 'y' a ambas preguntas:
```
▶️  Run single video processing test? (y/n): y
▶️  Run batch processing test (3 videos)? (y/n): y
```

**⚠️ Nota**: El procesamiento puede tomar varios minutos dependiendo del tamaño de los videos.

## 🔧 Troubleshooting

### Error: Cannot connect to server

**Problema**: `❌ Cannot connect to server!`

**Solución**:
```bash
# Inicia el servidor primero
python app_v2.py

# En otra terminal, ejecuta los tests
python test_api_v2.py
```

### Error: ModuleNotFoundError

**Problema**: `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solución**:
```bash
pip install -r requirements.txt
```

### Error: File not found

**Problema**: `❌ No videos found!`

**Solución**: Verifica que tengas archivos en:
- `D:/Work/video/videos/*.mp4`
- `D:/Work/video/audios/*.mp3`
- `D:/Work/video/texts.csv`

### Error: CORS

**Problema**: CORS errors en browser

**Solución**: Actualiza `.env`:
```bash
ALLOWED_ORIGINS=http://localhost:3000,https://tu-dominio.com
```

## 📚 Siguiente Paso

### Prueba Individual de Endpoints

Usa Swagger UI para probar endpoints individuales:
1. Abre http://localhost:8000/docs
2. Click en cualquier endpoint
3. Click "Try it out"
4. Llena los campos
5. Click "Execute"

### Integración con Frontend

Ver [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) para integrar con Next.js.

## 🎯 Endpoints Principales

### Upload
```bash
# Upload video
curl -X POST http://localhost:8000/api/video-processor/files/upload/video \
  -F "file=@video.mp4"

# Upload audio
curl -X POST http://localhost:8000/api/video-processor/files/upload/audio \
  -F "file=@audio.mp3"

# Upload CSV
curl -X POST http://localhost:8000/api/video-processor/files/upload/csv \
  -F "file=@texts.csv"
```

### Processing
```bash
# Single video
curl -X POST http://localhost:8000/api/video-processor/processing/process-single \
  -H "Content-Type: application/json" \
  -d '{"video_path": "D:/Work/video/videos/video (1).mp4", ...}'

# Batch
curl -X POST http://localhost:8000/api/video-processor/processing/process-batch \
  -H "Content-Type: application/json" \
  -d '{"video_folder": "D:/Work/video/videos", ...}'
```

### Monitor
```bash
# Get job status
curl http://localhost:8000/api/video-processor/processing/status/{job_id}

# List all jobs
curl http://localhost:8000/api/video-processor/processing/jobs
```

## ✅ Todo Listo!

Ahora tienes:
- ✅ API profesional corriendo
- ✅ Tests comprehensivos funcionando
- ✅ Arquitectura escalable
- ✅ Listo para integrar con Next.js

**¡Disfruta tu nueva API!** 🎉
