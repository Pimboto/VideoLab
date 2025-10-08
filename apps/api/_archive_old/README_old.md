# Video Processor API

Backend API para procesamiento batch de videos con texto y audio. Convierte la funcionalidad de Tkinter UI (`batch_core.py` y `ui.py`) en endpoints HTTP REST para integración con Next.js y otras aplicaciones.

## 🚀 Características

- ✅ **Procesamiento batch de videos** con texto overlay y música
- ✅ **Endpoints REST** para todas las funcionalidades de la UI
- ✅ **Background tasks** para procesamiento asíncrono
- ✅ **Tracking de jobs** con progreso en tiempo real
- ✅ **Selección diversa** de combinaciones (mode unique)
- ✅ **Configuración flexible** (presets, posición, fit mode, etc.)
- ✅ **Documentación interactiva** con Swagger UI
- ✅ **CORS habilitado** para integración con Next.js

## 📋 Requisitos

- Python 3.9+
- FFmpeg (debe estar en PATH)
- Windows/Linux/Mac

## 🔧 Instalación Rápida (Windows)

```bash
# 1. Clonar y navegar a la carpeta
cd apps/api

# 2. Ejecutar setup (crea venv e instala dependencias)
setup.bat

# 3. Editar .env con tu configuración (opcional)
notepad .env

# 4. Iniciar servidor
start_server.bat
```

## 🔧 Instalación Manual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env
copy .env.example .env

# Iniciar servidor
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentación

Una vez iniciado el servidor:

- **API Interactiva (Swagger)**: http://localhost:8000/docs
- **Documentación (ReDoc)**: http://localhost:8000/redoc
- **Guía de Endpoints**: Ver [README_VIDEO_PROCESSOR.md](./README_VIDEO_PROCESSOR.md)

## 🎯 Endpoints Principales

### Exploración
- `POST /api/video-processor/list-videos` - Lista videos en carpeta
- `POST /api/video-processor/list-audios` - Lista audios en carpeta
- `POST /api/video-processor/parse-csv` - Parsea CSV de textos

### Procesamiento
- `POST /api/video-processor/process-single` - Procesa un video individual
- `POST /api/video-processor/process-batch` - Procesa batch (múltiples combos)

### Monitoreo
- `GET /api/video-processor/status/{job_id}` - Estado de un job
- `GET /api/video-processor/jobs` - Lista todos los jobs

### Configuración
- `GET /api/video-processor/default-config` - Config por defecto

## 🧪 Testing

```bash
# Ejecutar tests
python test_api.py
```

Asegúrate de editar las rutas en `test_api.py` antes de ejecutar:
```python
VIDEO_FOLDER = "D:/Work/video/videos"
AUDIO_FOLDER = "D:/Work/video/audios"
CSV_FILE = "D:/Work/video/texts.csv"
OUTPUT_FOLDER = "D:/Work/video/output_test"
```

## 📖 Ejemplo de Uso

### 1. Listar recursos

```bash
curl -X POST http://localhost:8000/api/video-processor/list-videos \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "D:/Work/video/videos"}'
```

### 2. Procesar batch

```bash
curl -X POST http://localhost:8000/api/video-processor/process-batch \
  -H "Content-Type: application/json" \
  -d '{
    "video_folder": "D:/Work/video/videos",
    "audio_folder": "D:/Work/video/audios",
    "text_combinations": [
      ["Texto 1", "Texto 2"],
      ["Otro texto", "Más texto"]
    ],
    "output_folder": "D:/Work/video/output",
    "unique_mode": true,
    "unique_amount": 50,
    "config": {
      "position": "bottom",
      "preset": "bold",
      "fit_mode": "cover"
    }
  }'
```

Respuesta:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_jobs": 50,
  "message": "Batch job started with 50 videos to process"
}
```

### 3. Monitorear progreso

```bash
curl http://localhost:8000/api/video-processor/status/550e8400-e29b-41d4-a716-446655440000
```

Respuesta:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "message": "Processing 23/50",
  "output_files": ["D:/Work/video/output/video1/audio1__combo1_texto.mp4"]
}
```

## 🎨 Configuración del Procesamiento

### Presets de Texto
- `clean` - Texto blanco sin borde
- `bold` - Texto blanco con borde negro grueso (default)
- `subtle` - Texto blanco con borde gris fino
- `yellow` - Texto amarillo con borde negro
- `shadow` - Texto blanco con sombra

### Posición
- `center` - Centrado (default)
- `top` - Parte superior
- `bottom` - Parte inferior

### Fit Mode
- `cover` - Cubre todo el canvas, crop si es necesario (default para portrait)
- `contain` - Contiene el video completo con letterbox
- `zoom` - Zoom (alias de cover)

### Duration Policy
- `shortest` - Duración del más corto entre video y audio (default)
- `audio` - Duración del audio
- `video` - Duración del video
- `fixed` - Duración fija (especificar `fixed_seconds`)

## 🔀 Integración con Next.js

### Ejemplo básico con fetch

```typescript
// pages/api/video-processor.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function processBatch(data: BatchJobRequest) {
  const response = await fetch(`${API_BASE}/api/video-processor/process-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return response.json()
}

export async function getJobStatus(jobId: string) {
  const response = await fetch(`${API_BASE}/api/video-processor/status/${jobId}`)
  return response.json()
}
```

### Ejemplo con React Query (polling)

```typescript
import { useQuery } from '@tanstack/react-query'

function JobMonitor({ jobId }: { jobId: string }) {
  const { data: status } = useQuery({
    queryKey: ['job-status', jobId],
    queryFn: () => getJobStatus(jobId),
    refetchInterval: (data) => {
      // Stop polling when completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false
      }
      return 2000 // Poll every 2 seconds
    }
  })

  return (
    <div>
      <p>Status: {status?.status}</p>
      <progress value={status?.progress} max={100} />
      <p>{status?.message}</p>
    </div>
  )
}
```

## 📁 Estructura del Proyecto

```
apps/api/
├── app.py                      # FastAPI app principal
├── batch_core.py              # Núcleo de procesamiento (original)
├── ui.py                      # UI Tkinter (original)
├── routers/
│   ├── __init__.py
│   └── video_processor.py     # Router con endpoints HTTP
├── requirements.txt           # Dependencias Python
├── .env                       # Variables de entorno
├── .env.example              # Template de .env
├── setup.bat                 # Script de setup (Windows)
├── start_server.bat          # Script para iniciar servidor
├── test_api.py              # Tests de endpoints
├── README.md                # Este archivo
└── README_VIDEO_PROCESSOR.md # Documentación detallada de endpoints
```

## 🚦 Estado de Jobs

- `pending` - Job en cola
- `processing` - Procesando
- `completed` - Completado exitosamente
- `failed` - Falló con error

## ⚙️ Variables de Entorno

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Default paths (optional)
DEFAULT_VIDEO_FOLDER=
DEFAULT_AUDIO_FOLDER=
DEFAULT_OUTPUT_FOLDER=
```

## ⚠️ Notas Importantes

1. **FFmpeg requerido**: Asegúrate de que `ffprobe` esté en PATH
2. **Paths absolutos**: Usa paths absolutos en todas las requests
3. **Jobs en memoria**: Los jobs se almacenan en memoria (usar Redis/DB en producción)
4. **Background tasks**: Los jobs NO se detienen al eliminarlos del tracking
5. **Sin límites de concurrencia**: Implementar cola con Celery para producción

## 🔜 Próximos Pasos

### Para el Backend (Producción)
- [ ] Implementar Redis para job storage
- [ ] Agregar Celery para queue management
- [ ] WebSockets para updates en tiempo real
- [ ] Autenticación y autorización
- [ ] Rate limiting
- [ ] File upload directo (no solo paths)
- [ ] Cleanup automático de archivos antiguos

### Para el Frontend (Next.js)
- [ ] Componente de file browser
- [ ] CSV uploader con preview
- [ ] Form de configuración
- [ ] Job monitor con progress bar
- [ ] Lista de jobs con filtros
- [ ] Download de archivos procesados
- [ ] Preview de videos procesados

## 📝 Changelog

### v0.1.0 - Initial Release
- Conversión de UI Tkinter a API REST
- Endpoints completos para batch processing
- Background tasks con FastAPI
- Job tracking básico
- Documentación interactiva

## 🤝 Contribuir

Este proyecto es parte de un monorepo Turborepo. Para contribuir:

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/amazing`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing`)
5. Abre un Pull Request

## 📄 Licencia

[Especificar licencia]

## 🆘 Soporte

- **Documentación**: Ver `README_VIDEO_PROCESSOR.md`
- **API Docs**: http://localhost:8000/docs
- **Issues**: [GitHub Issues]

---

Made with ❤️ for video processing automation
