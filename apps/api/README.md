# 🏛️ Video Processor API v2.0

API profesional para procesamiento de videos con FastAPI, arquitectura modular y mejores prácticas.

## 🚀 Quick Start

```bash
cd apps/api
pip install -r requirements.txt
python app.py
```

Documentación: http://localhost:8000/docs

## 📁 Arquitectura Modular

```
apps/api/
├── core/               # Configuración, dependencias, excepciones
├── routers/            # Endpoints REST (auth, files, folders, processing)
├── services/           # Lógica de negocio (9 servicios especializados)
├── schemas/            # Modelos Pydantic para validación
├── models/             # Modelos de base de datos
├── utils/              # Utilidades (S3, FFmpeg, Supabase)
└── middleware/         # Manejo de errores global
```

## 🎯 Módulos y Features

### Core (`core/`)
- **config.py**: Settings con Pydantic v2, validación de paths, propiedades calculadas
- **dependencies.py**: Dependency injection con `@lru_cache`, servicios singleton
- **exceptions.py**: Jerarquía de excepciones personalizadas (11 tipos)
- **security.py**: Verificación JWT Clerk, extracción de user info

### Routers (`routers/`)
- **auth.py**: Autenticación (3 endpoints: `/me`, `/test-public`, `/test-optional`)
- **files.py**: Gestión de archivos (15 endpoints: upload, list, delete, rename, move, bulk ops)
- **folders.py**: Gestión de carpetas (3 endpoints: list, create, delete)
- **processing.py**: Procesamiento de videos (8 endpoints: batch, single, jobs, status)
- **webhooks.py**: Webhooks Clerk para sincronización de usuarios

### Services (`services/`)
- **FileService**: Listado, eliminación, renombrado, movimiento (bulk operations)
- **MediaUploadService**: Subida de videos y audios a S3
- **CSVService**: Subida y parsing de CSVs
- **FolderService**: CRUD de carpetas con metadata
- **ProcessingService**: Lógica de procesamiento batch y single
- **JobService**: Tracking de jobs con Supabase
- **StorageService**: Operaciones S3 (upload, download, move, rename, signed URLs)
- **VideoRenderService**: Renderizado de videos con FFmpeg
- **UserService**: Gestión de usuarios (CRUD)

### Utils (`utils/`)
- **aws_s3_client.py**: Cliente S3 con CloudFront
- **ffmpeg_helper.py**: Funciones FFmpeg (probe, run commands)
- **supabase_client.py**: Cliente Supabase singleton
- **text_renderer.py**: Renderizado de textos en videos
- **font_manager.py**: Gestión de fuentes

### Middleware (`middleware/`)
- **error_handler.py**: Manejo global de excepciones con mapeo a HTTP status codes

## ✅ Principios de Diseño Aplicados

### ✅ Funcional y Declarativo
- Funciones puras en utils (`check_ffmpeg_installed`, `probe_video`)
- Evita clases innecesarias (preferencia por funciones)
- Código declarativo en routers (endpoints limpios)

### ✅ RORO Pattern (Receive Object, Return Object)
- Todos los endpoints reciben Pydantic models y retornan schemas
- Ejemplo: `upload_video(file: UploadFile, ...) -> FileUploadResponse`

### ✅ Error Handling First
- Guard clauses al inicio de funciones
- Early returns para casos de error
- Happy path al final
- Custom exceptions con mapeo automático a HTTP codes

### ✅ Dependency Injection
- FastAPI DI system con `@lru_cache`
- Servicios singleton y composables
- Separación de concerns clara

### ✅ Type Safety
- Type hints en todas las funciones
- Pydantic v2 para validación I/O
- Type coverage: ~100%

### ✅ Async/Await
- Operaciones I/O async (S3, Supabase, file operations)
- Background tasks para processing
- Non-blocking operations

### ✅ Separación de Concerns
- Routers: Solo routing y validación
- Services: Lógica de negocio
- Utils: Funciones puras reutilizables
- Models: Estructura de datos

## 📊 Endpoints por Módulo

- **Auth**: 3 endpoints
- **Files**: 15 endpoints (upload, list, delete, bulk ops, rename, move, stream URLs)
- **Folders**: 3 endpoints
- **Processing**: 8 endpoints (batch, single, jobs, status)
- **Webhooks**: 1 endpoint

**Total: 30 endpoints**

## 🛡️ Características

- ✅ Autenticación Clerk JWT
- ✅ Storage AWS S3 + CloudFront
- ✅ Base de datos Supabase
- ✅ Procesamiento batch con FFmpeg
- ✅ Tracking de jobs con estado
- ✅ Validación Pydantic v2
- ✅ Manejo de errores profesional
- ✅ Logging estructurado
- ✅ CORS configurado
- ✅ Async/await para I/O

## 📝 Convenciones

- Nombres descriptivos con verbos auxiliares (`is_active`, `has_permission`)
- Archivos y directorios en lowercase con underscores
- Type hints obligatorios
- Docstrings en funciones públicas
- Early returns para error handling
- Guard clauses para precondiciones

## 🚀 Deploy

```bash
# Development
python app.py

# Production
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

**Version**: 2.0.0  
**Status**: ✅ Production Ready  
**Framework**: FastAPI + Pydantic v2 + Supabase + AWS S3
