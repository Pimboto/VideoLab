

# Video Processor API - Arquitectura Profesional

## 🏗️ Arquitectura Overview

Esta API sigue las mejores prácticas de FastAPI con arquitectura limpia, separación de concerns, y código altamente mantenible.

## 📁 Estructura del Proyecto

```
apps/api/
├── app_v2.py                    # Entry point con lifespan manager
├── core/                        # Core application
│   ├── __init__.py
│   ├── config.py               # Settings con Pydantic
│   ├── dependencies.py         # Dependency injection
│   └── exceptions.py           # Custom exceptions
├── schemas/                     # Pydantic models (DTOs)
│   ├── __init__.py
│   ├── file_schemas.py        # File-related schemas
│   ├── processing_schemas.py  # Processing-related schemas
│   └── job_schemas.py         # Job-related schemas
├── services/                    # Business logic
│   ├── __init__.py
│   ├── storage_service.py     # Storage operations
│   ├── file_service.py        # File management
│   ├── job_service.py         # Job state management
│   └── processing_service.py  # Video processing
├── middleware/                  # Middleware
│   ├── __init__.py
│   └── error_handler.py       # Error handling
├── routers_v2/                 # Route handlers
│   ├── __init__.py
│   ├── files.py               # File routes
│   ├── folders.py             # Folder routes
│   └── processing.py          # Processing routes
└── utils/                      # Utilities (future)
```

## 🎯 Principios de Arquitectura

### 1. **Separation of Concerns**
Cada capa tiene una responsabilidad única:
- **Routers**: Manejo de HTTP, validación de entrada
- **Services**: Lógica de negocio
- **Schemas**: Validación y serialización de datos
- **Core**: Configuración y utilities

### 2. **Dependency Injection**
Usamos el sistema de DI de FastAPI:

```python
from core.dependencies import get_file_service

@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.upload_video(file)
```

### 3. **Error Handling**
Excepciones personalizadas con handlers específicos:

```python
# En service
if not file_path.exists():
    raise FileNotFoundError(f"File not found: {file_path}")

# Automáticamente convertido a:
# HTTP 404 con JSON response
```

### 4. **Type Safety**
Type hints en todo el código:

```python
async def upload_video(
    self, file: UploadFile, subfolder: str | None = None
) -> FileUploadResponse:
    ...
```

### 5. **Configuration Management**
Settings centralizadas con Pydantic:

```python
class Settings(BaseSettings):
    app_name: str = "Video Processor API"
    max_video_size: int = 500 * 1024 * 1024
    ...
```

## 🔄 Flujo de Request

```
Client Request
    ↓
FastAPI Router (validation)
    ↓
Dependency Injection (services)
    ↓
Service Layer (business logic)
    ↓
Exception Handling (if error)
    ↓
Response (Pydantic schema)
```

## 📦 Componentes Principales

### Core Components

#### `core/config.py` - Settings
```python
@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
```

**Características:**
- Environment variables support
- Validation con Pydantic
- Cached singleton
- Type-safe

#### `core/dependencies.py` - DI Container
```python
@lru_cache
def get_file_service() -> FileService:
    settings = get_settings()
    storage_service = get_storage_service()
    return FileService(settings, storage_service)
```

**Características:**
- Lazy loading
- Singleton pattern
- Composición de dependencias

#### `core/exceptions.py` - Custom Exceptions
```python
class FileNotFoundError(VideoProcessorException):
    """Raised when a file is not found"""
    pass
```

**Características:**
- Jerarquía de excepciones
- Context-aware messages
- Auto-handled por middleware

### Services Layer

#### `services/storage_service.py`
Manejo de bajo nivel de almacenamiento:
- Validación de archivos
- Operaciones CRUD de archivos
- Gestión de paths

#### `services/file_service.py`
Lógica de negocio para archivos:
- Upload de archivos
- Listado con metadata
- Operaciones de gestión

#### `services/job_service.py`
Gestión de estado de jobs:
- CRUD de jobs
- Tracking de progreso
- Estado en memoria (singleton)

#### `services/processing_service.py`
Procesamiento de videos:
- Integración con batch_core
- Background processing
- Progress tracking

### Routers Layer

#### Características Comunes
```python
@router.post("/upload/video", response_model=FileUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    subfolder: str | None = Query(default=None),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """Upload a video file."""
    return await file_service.upload_video(file, subfolder)
```

- Type hints completos
- Documentación en docstrings
- Response models explícitos
- Status codes semánticos

## 🛡️ Error Handling

### Custom Exceptions

```python
# En service
raise FileSizeLimitError(
    f"File too large. Maximum size: {max_mb:.0f}MB",
    details={"max_size": self.settings.max_video_size}
)
```

### Exception Handlers

```python
# Automáticamente convertido a:
{
    "detail": "File too large. Maximum size: 500MB",
    "details": {
        "max_size": 524288000
    }
}
# HTTP 400 Bad Request
```

### Middleware

```python
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(...)
```

## ⚡ Performance

### Async Operations
```python
async def save_upload_file(self, upload_file: UploadFile, destination: Path) -> int:
    """Non-blocking file save"""
    async with aiofiles.open(destination, 'wb') as buffer:
        while chunk := await upload_file.read(CHUNK_SIZE):
            await buffer.write(chunk)
```

### Caching
```python
@lru_cache
def get_settings() -> Settings:
    """Cached settings - instantiated once"""
    return Settings()
```

### Background Tasks
```python
background_tasks.add_task(
    processing_service.process_single_video,
    job_id, video_path, audio_path, ...
)
```

## 🧪 Testing

### Unit Tests
```python
def test_upload_video():
    service = FileService(settings, storage_service)
    result = await service.upload_video(mock_file)
    assert result.filename.endswith('.mp4')
```

### Integration Tests
```python
async def test_upload_endpoint():
    response = await client.post(
        "/api/video-processor/files/upload/video",
        files={"file": ("test.mp4", content)}
    )
    assert response.status_code == 201
```

## 🔐 Security

### File Validation
- Extension whitelist
- Size limits
- Path sanitization
- MIME type verification (future)

### Input Validation
```python
class FileUploadRequest(BaseModel):
    subfolder: str | None = Field(default=None)

    @field_validator("subfolder")
    @classmethod
    def validate_subfolder(cls, v):
        if v and ".." in v:
            raise ValueError("Invalid folder name")
        return v
```

## 📊 Monitoring & Logging

### Structured Logging
```python
logger.info(
    "File uploaded",
    extra={
        "filename": filename,
        "size": file_size,
        "user": user_id
    }
)
```

### Error Tracking
```python
logger.error(
    f"{exc.__class__.__name__}: {exc.message}",
    extra={"details": exc.details}
)
```

## 🚀 Deployment

### Environment Variables
```bash
# .env
APP_NAME=Video Processor API
DEBUG=False
STORAGE_DIR=/var/video_storage
MAX_VIDEO_SIZE=524288000
ALLOWED_ORIGINS=https://app.example.com
```

### Docker Ready
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app_v2:app", "--host", "0.0.0.0"]
```

## 📝 Best Practices Implementadas

### ✅ FastAPI
- [x] Lifespan context managers
- [x] Dependency injection
- [x] Async operations
- [x] Type hints
- [x] Response models
- [x] Custom exceptions
- [x] Middleware

### ✅ Python
- [x] PEP 8 compliant
- [x] Type hints (PEP 484)
- [x] Docstrings
- [x] f-strings
- [x] Context managers
- [x] Functional programming

### ✅ Architecture
- [x] Separation of concerns
- [x] Single responsibility
- [x] Dependency inversion
- [x] Error handling first
- [x] RORO pattern
- [x] Immutability where possible

## 🔄 Migration Path

### Paso 1: Testing
```bash
# Probar nueva API
python app_v2.py

# Verificar endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

### Paso 2: Comparación
```bash
# Antigua API
http://localhost:8000/api/video-processor/upload/video

# Nueva API (mismo endpoint)
http://localhost:8000/api/video-processor/files/upload/video
```

### Paso 3: Migración
1. Actualizar clientes (frontend) gradualmente
2. Mantener ambas APIs en paralelo
3. Deprecar endpoints viejos
4. Eliminar código legacy

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 🎯 Next Steps

1. **Testing Suite**: Agregar tests comprehensivos
2. **Database**: Integrar SQLAlchemy para job persistence
3. **Monitoring**: Agregar Prometheus metrics
4. **API Versioning**: Implementar versionado de API
5. **Rate Limiting**: Agregar rate limiting
6. **Authentication**: Implementar JWT auth
7. **WebSockets**: Real-time job updates
8. **Caching**: Redis para job state
