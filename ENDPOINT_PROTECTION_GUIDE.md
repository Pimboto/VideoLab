# 🔐 Endpoint Protection Guide

## ✅ Authentication Setup Complete

La autenticación está completamente configurada. Ahora necesitas proteger cada endpoint agregando el dependency `get_current_user`.

---

## 📝 Patrón de Implementación

### Antes (Sin Autenticación)
```python
@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    subfolder: str | None = Form(default=None),
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.upload_video(file, subfolder)
```

### Después (Con Autenticación)
```python
from core.dependencies import get_current_user

@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    subfolder: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),  # ✅ AGREGAR ESTO
    file_service: FileService = Depends(get_file_service),
):
    # Ahora tienes acceso a current_user
    user_id = current_user["id"]  # UUID from database
    clerk_id = current_user["clerk_id"]  # Clerk user ID

    return await file_service.upload_video(file, subfolder, user_id)
```

---

## 📋 Archivos a Modificar

### 1. `routers/files.py`

**Paso 1: Importar dependency**
```python
from core.dependencies import get_current_user
```

**Paso 2: Proteger cada endpoint**

Agregar `current_user: dict = Depends(get_current_user)` a cada función:

- ✅ `upload_video()` - Línea 25
- ✅ `upload_audio()` - Línea 39
- ✅ `upload_csv()` - Línea 54
- ✅ `list_videos()` - Línea 69
- ✅ `list_audios()` - Línea 82
- ✅ `list_csvs()` - Línea 95
- ✅ `list_outputs()` - Línea 103
- ✅ `delete_file()` - Buscar en el archivo
- ✅ `move_file()` - Buscar en el archivo
- ✅ `stream_video()` - Buscar en el archivo
- ✅ `stream_audio()` - Buscar en el archivo
- ✅ `preview_csv()` - Buscar en el archivo

### 2. `routers/folders.py`

**Importar:**
```python
from core.dependencies import get_current_user
```

**Proteger todos los endpoints:**
- ✅ `list_folders()`
- ✅ `create_folder()`
- ✅ Cualquier otro endpoint

### 3. `routers/processing.py`

**Importar:**
```python
from core.dependencies import get_current_user
```

**Proteger todos los endpoints:**
- ✅ `list_videos()`
- ✅ `list_audios()`
- ✅ `get_default_config()`
- ✅ `process_single_video()`
- ✅ `process_batch_videos()`
- ✅ `get_job_status()`
- ✅ `list_jobs()`
- ✅ `delete_job()`

---

## 🔧 Ejemplo Completo: Upload Video

### Archivo: `routers/files.py`

```python
# En el import al inicio del archivo
from core.dependencies import get_current_user

# Modificar el endpoint
@router.post("/upload/video", response_model=FileUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    subfolder: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),  # ✅ AGREGAR
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload a video file.

    Requires authentication.

    - **file**: Video file to upload
    - **subfolder**: Optional subfolder for organization
    """
    user_id = current_user["id"]
    return await file_service.upload_video(file, subfolder, user_id)
```

**IMPORTANTE**: También necesitarás modificar `services/file_service.py` para aceptar `user_id` y guardar metadata en Supabase.

---

## 🛠️ Modificar Services

Los services también necesitan actualizarse para:
1. Aceptar `user_id` como parámetro
2. Guardar metadata en Supabase
3. Filtrar resultados por usuario

### Ejemplo: FileService.upload_video()

**Antes:**
```python
async def upload_video(self, file: UploadFile, subfolder: str | None = None):
    # Solo guarda en disco local
    path = self.storage_service.save_file(file, "videos", subfolder)
    return {"filename": file.filename, "path": path}
```

**Después:**
```python
async def upload_video(
    self,
    file: UploadFile,
    subfolder: str | None = None,
    user_id: str = None  # ✅ AGREGAR
):
    # 1. Guardar en Supabase Storage (en lugar de disco local)
    storage_path = await self.supabase_storage.upload(
        bucket="videos",
        user_id=user_id,
        file=file,
        subfolder=subfolder
    )

    # 2. Guardar metadata en Supabase DB
    file_record = await self.supabase.table("files").insert({
        "user_id": user_id,
        "filename": file.filename,
        "filepath": storage_path,
        "file_type": "video",
        "size_bytes": file.size,
        "mime_type": file.content_type,
        "subfolder": subfolder
    }).execute()

    return {"filename": file.filename, "path": storage_path, "id": file_record.data[0]["id"]}
```

---

## ⚡ Quick Start

### Paso 1: Proteger un endpoint de ejemplo

```bash
# Editar apps/api/routers/files.py
# 1. Agregar import
# 2. Agregar current_user dependency a upload_video
# 3. Pasar user_id al service
```

### Paso 2: Probar

```bash
# Iniciar backend
cd apps/api
python app.py

# Iniciar frontend
cd apps/web
pnpm dev

# Visita http://localhost:3000
# Sign in
# Intenta subir un archivo
```

### Paso 3: Verificar

Deberías ver:
- ✅ Usuario autenticado correctamente
- ✅ Endpoint recibe el user_id
- ✅ Si no envías token → Error 401

---

## 📊 Checklist de Endpoints

### routers/files.py
- [ ] upload_video
- [ ] upload_audio
- [ ] upload_csv
- [ ] list_videos
- [ ] list_audios
- [ ] list_csvs
- [ ] list_outputs
- [ ] delete_file
- [ ] move_file
- [ ] stream_video
- [ ] stream_audio
- [ ] preview_csv

### routers/folders.py
- [ ] list_folders
- [ ] create_folder

### routers/processing.py
- [ ] list_videos
- [ ] list_audios
- [ ] get_default_config
- [ ] process_single_video
- [ ] process_batch_videos
- [ ] get_job_status
- [ ] list_jobs
- [ ] delete_job

---

## 🚨 Endpoints Públicos (Opcional)

Si quieres que algunos endpoints sean públicos (sin autenticación), usa `get_optional_user` en lugar de `get_current_user`:

```python
from core.dependencies import get_optional_user

@router.get("/public-info")
async def public_info(
    current_user: dict | None = Depends(get_optional_user)
):
    if current_user:
        # Usuario autenticado - mostrar info personalizada
        return {"message": f"Hello {current_user['email']}"}
    else:
        # Usuario no autenticado - mostrar info pública
        return {"message": "Hello guest"}
```

---

## 🎯 Próximos Pasos

1. **Proteger upload_video como ejemplo** (5 min)
2. **Probar con frontend** (5 min)
3. **Si funciona, aplicar a todos los demás endpoints** (30 min)
4. **Actualizar services para usar Supabase** (1-2 horas)

---

## 💡 Tips

1. **No olvides el import**: `from core.dependencies import get_current_user`
2. **current_user es un dict** con: `id`, `clerk_id`, `email`, `first_name`, `last_name`, `avatar_url`, `created_at`, `updated_at`
3. **Siempre usa `current_user["id"]`** para operaciones de base de datos (es el UUID)
4. **Usa `current_user["clerk_id"]`** solo si necesitas interactuar con Clerk API
5. **FastAPI maneja los errores 401** automáticamente si el token es inválido

---

**¡Listo para proteger tus endpoints! 🔐**
