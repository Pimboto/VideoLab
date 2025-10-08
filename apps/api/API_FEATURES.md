# 🎉 Video Processor API - Nuevas Características

## ✅ Implementado

### 📤 Endpoints de Upload

**Todos los uploads incluyen:**
- ✅ Validación de formato de archivo
- ✅ Límites de tamaño configurables
- ✅ Generación automática de nombres únicos (timestamp + hash)
- ✅ Soporte para subcarpetas/organización
- ✅ Chunked reading para archivos grandes
- ✅ Respuestas con información completa del archivo

**Endpoints:**
1. `POST /upload/video` - Upload de videos
   - Formatos: `.mp4`, `.mov`, `.m4v`, `.avi`, `.mkv`
   - Límite: 500 MB
   - Subcarpetas opcionales

2. `POST /upload/audio` - Upload de audios
   - Formatos: `.mp3`, `.wav`, `.m4a`
   - Límite: 50 MB
   - Subcarpetas opcionales

3. `POST /upload/csv` - Upload y parseo de CSV
   - Formato: `.csv`
   - Límite: 5 MB
   - Opción de guardar archivo o solo parsear

### 📁 Gestión de Archivos

**Endpoints:**
1. `GET /files/videos` - Listar videos con detalles
   - Información: nombre, path, tamaño, fecha modificación
   - Filtro por subcarpeta
   - Ordenado por fecha (más recientes primero)

2. `GET /files/audios` - Listar audios con detalles
   - Mismas características que videos

3. `GET /files/csv` - Listar CSVs guardados
   - Información completa de archivos

4. `DELETE /files/delete` - Eliminar archivos
   - Validación de existencia
   - Manejo de errores

5. `POST /files/move` - Mover archivos entre carpetas
   - Creación automática de carpeta destino
   - Validación de duplicados

### 📂 Gestión de Carpetas

**Endpoints:**
1. `GET /folders/{category}` - Listar carpetas
   - Categorías: videos, audios, csv, output
   - Información: nombre, path, cantidad de archivos, tamaño total
   - Ordenado alfabéticamente

2. `POST /folders/create` - Crear carpetas
   - Sanitización automática de nombres
   - Validación de duplicados
   - Creación recursiva de paths

### 🔧 Sistema de Configuración

**Archivo `config.py`:**
- Paths de storage configurables via environment variables
- Límites de tamaño por tipo de archivo
- Extensiones permitidas
- Inicialización automática de directorios
- Funciones helper para validación

**Variables de entorno:**
```bash
STORAGE_DIR=D:/Work/video  # Base storage directory
```

### 📊 Modelos Pydantic

**Nuevos modelos:**
- `FileUploadResponse` - Respuesta de uploads
- `FileInfo` - Información detallada de archivos
- `FolderInfo` - Información de carpetas
- `FileListResponse` - Listas de archivos
- `FolderListResponse` - Listas de carpetas
- `DeleteFileRequest` - Request para eliminar
- `DeleteResponse` - Respuesta de eliminación
- `CreateFolderRequest` - Request para crear carpeta
- `MoveFileRequest` - Request para mover archivos

### 🧪 Testing

**Archivos de test:**
1. `test_api.py` - Tests originales de procesamiento
2. `test_upload_api.py` - Tests completos de upload y gestión
   - Tests de upload (video, audio, csv)
   - Tests de listado de archivos
   - Tests de gestión de carpetas
   - Tests de operaciones (mover, eliminar)

### 📖 Documentación

**README actualizado:**
- Índice completo de endpoints
- Ejemplos de uso con cURL
- Ejemplos de integración con Next.js
- Componentes React recomendados
- Hooks personalizados (SWR/React Query)
- Variables de entorno
- Configuración de límites
- Mejores prácticas

---

## 🚀 Listo para Next.js

### Características para Frontend

✅ **CORS configurado** para Next.js (puerto 3000)
✅ **Respuestas JSON consistentes** en todos los endpoints
✅ **Validaciones robustas** con mensajes de error claros
✅ **File metadata completo** (tamaño, fecha, tipo)
✅ **Nombres únicos automáticos** (evita colisiones)
✅ **Organización en carpetas** para proyectos
✅ **Progress tracking** para jobs de procesamiento
✅ **Error handling** consistente

### Flujo Completo en Next.js

```
1. Usuario sube videos/audios
   ↓
2. Frontend lista archivos disponibles
   ↓
3. Usuario crea/sube CSV con textos
   ↓
4. Usuario configura opciones de procesamiento
   ↓
5. Frontend inicia batch processing
   ↓
6. Polling de status cada 2s
   ↓
7. Descarga/visualización de resultados
```

### Componentes Recomendados

**File Management:**
- VideoUploader (drag & drop)
- VideoLibrary (grid con previews)
- AudioLibrary (lista con player)
- FolderBrowser (navegación)

**Processing:**
- ConfigForm (opciones de video)
- TextCombinationsEditor (CSV editor)
- BatchProcessForm (configuración batch)
- JobMonitor (progress con SWR)

**UI:**
- ProgressBar (animado)
- FilePreview (thumbnails)
- Toast notifications (success/error)
- LoadingStates (skeleton screens)

---

## 🔒 Seguridad y Validación

### Validaciones Implementadas

✅ **Tipo de archivo**
- Whitelist de extensiones permitidas
- Validación antes de guardar

✅ **Tamaño de archivo**
- Límites configurables por tipo
- Validación antes de escribir

✅ **Nombres de archivo**
- Sanitización de nombres
- Prevención de path traversal
- Generación de nombres únicos

✅ **Paths de carpetas**
- Sanitización de nombres de carpeta
- Validación de categorías
- Creación segura de directorios

### Límites por Defecto

| Tipo  | Límite | Extensiones |
|-------|--------|-------------|
| Video | 500 MB | .mp4, .mov, .m4v, .avi, .mkv |
| Audio | 50 MB  | .mp3, .wav, .m4a |
| CSV   | 5 MB   | .csv |

---

## 📝 Endpoints Resumidos

### Upload (3)
- POST `/upload/video`
- POST `/upload/audio`
- POST `/upload/csv`

### File Management (5)
- GET `/files/videos`
- GET `/files/audios`
- GET `/files/csv`
- DELETE `/files/delete`
- POST `/files/move`

### Folder Management (2)
- GET `/folders/{category}`
- POST `/folders/create`

### Processing - Originales (9)
- POST `/list-videos`
- POST `/list-audios`
- POST `/parse-csv`
- POST `/process-single`
- POST `/process-batch`
- GET `/status/{job_id}`
- GET `/jobs`
- DELETE `/jobs/{job_id}`
- GET `/default-config`

**Total: 19 endpoints**

---

## 🎯 Siguiente Paso

La API está 100% lista para integrarse con Next.js. Los siguientes pasos son:

1. **Crear proyecto Next.js** en `/apps/web`
2. **Implementar componentes** siguiendo los ejemplos del README
3. **Configurar SWR/React Query** para data fetching
4. **Implementar UI** con Tailwind/shadcn/ui
5. **Testing E2E** con Playwright/Cypress

---

## 📚 Recursos

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **README completo**: `apps/api/README_VIDEO_PROCESSOR.md`
- **Tests**: `python test_upload_api.py`
