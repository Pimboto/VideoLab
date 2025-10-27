# 🏗️ VideoLab - Arquitectura & Plan de Desarrollo MVP

> **Documento Maestro de Arquitectura para Producción Profesional**
>
> Este documento define la arquitectura completa, patrones de desarrollo, reglas inquebrantables y plan de acción para construir un MVP escalable que permita crecer hacia un SaaS con IA generativa (Nano, Kling, Wan Animate).

---

## 📋 Tabla de Contenidos

1. [Análisis del Estado Actual](#análisis-del-estado-actual)
2. [Arquitectura Objetivo MVP](#arquitectura-objetivo-mvp)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Arquitectura del Backend](#arquitectura-del-backend)
5. [Arquitectura del Frontend](#arquitectura-del-frontend)
6. [Integración Supabase](#integración-supabase)
7. [Integración Clerk](#integración-clerk)
8. [Sistema de Colas y Jobs](#sistema-de-colas-y-jobs)
9. [Plan para IA Generativa (Futuro)](#plan-para-ia-generativa-futuro)
10. [Reglas Inquebrantables](#reglas-inquebrantables)
11. [Convenciones de Código](#convenciones-de-código)
12. [Plan de Acción MVP](#plan-de-acción-mvp)
13. [Guía de Llamadas API desde Frontend](#guía-de-llamadas-api-desde-frontend)

---

## 🔍 Análisis del Estado Actual

### ✅ Lo que YA tienes (Estado Actual)

#### **Monorepo Setup**
```
video-monorepo/
├── apps/
│   ├── web/          # Next.js 15 + React 18
│   └── api/          # FastAPI (Python)
├── packages/         # (vacío por ahora)
└── turbo.json        # Turborepo configurado
```

#### **Frontend (apps/web)**
- ✅ **Next.js 15.3.1** con App Router
- ✅ **HeroUI** (componentes UI profesionales)
- ✅ **Tailwind CSS 4** + PostCSS
- ✅ **GSAP** para animaciones
- ✅ **Three.js / React Three Fiber** (3D graphics)
- ✅ Estructura de páginas:
  - `/dashboard` - Dashboard principal
  - `/dashboard/create` - Batch processing UI
  - `/dashboard/videos` - Gestión de videos
  - `/dashboard/audios` - Gestión de audios
  - `/dashboard/texts` - Gestión de CSV
  - `/dashboard/projects` - Ver outputs
- ✅ Componentes reutilizables (FileTable, Sidebar)

#### **Backend (apps/api)**
- ✅ **FastAPI** con arquitectura limpia profesional
- ✅ **Arquitectura en capas**:
  - `core/` - Config, dependencies, exceptions
  - `services/` - Business logic
  - `routers/` - HTTP handlers
  - `schemas/` - Pydantic models
  - `middleware/` - Error handling
- ✅ **Batch video processing** (`batch_core.py`)
- ✅ **Job service** (in-memory state management)
- ✅ **File management** (upload, storage, streaming)
- ✅ **Background tasks** con FastAPI
- ✅ **CORS** configurado
- ✅ **OpenCV, MoviePy, Pillow** para procesamiento

#### **Procesamiento de Video**
- ✅ Batch processing de múltiples videos
- ✅ Overlay de texto con múltiples presets
- ✅ Mixing de audio
- ✅ Diferentes fit modes (cover/contain)
- ✅ Posicionamiento de texto (top/center/bottom)
- ✅ Modo único (combinaciones diversas)

### ❌ Lo que FALTA para MVP

1. **🔐 Autenticación**
   - ❌ Clerk no está integrado
   - ❌ No hay rutas protegidas
   - ❌ No hay gestión de sesiones

2. **🗄️ Base de Datos**
   - ❌ Supabase no está integrado
   - ❌ No hay persistencia de usuarios
   - ❌ No hay persistencia de archivos/metadata
   - ❌ Jobs solo en memoria (se pierden al reiniciar)
   - ❌ No hay historial de procesamiento

3. **☁️ Storage**
   - ⚠️ Archivos en disco local (`D:/Work/video`)
   - ❌ No hay Supabase Storage integrado
   - ❌ No hay gestión de cuotas por usuario

4. **⚙️ Queue System**
   - ⚠️ BackgroundTasks básico (no escalable)
   - ❌ No hay sistema de colas robusto (Redis/BullMQ)
   - ❌ No hay retry logic
   - ❌ No hay priority queues

5. **📊 Monitoreo**
   - ❌ No hay logs estructurados
   - ❌ No hay métricas
   - ❌ No hay error tracking (Sentry)

---

## 🎯 Arquitectura Objetivo MVP

### Principios de Arquitectura

1. **Separation of Concerns** - Cada capa tiene una responsabilidad única
2. **API-First Design** - Backend expone API RESTful, frontend la consume
3. **Stateless Backend** - Toda la sesión en Clerk, estado en Supabase
4. **Event-Driven Processing** - Jobs asíncronos con colas
5. **Multi-Tenancy** - Cada usuario tiene sus propios recursos aislados
6. **Scalability Ready** - Preparado para Serverless AI (RunPod)

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────┐
│                         USUARIO                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Clerk SDK (Auth) + Supabase Client (Direct Access)  │   │
│  └──────────────────────────────────────────────────────┘   │
│  • Autenticación (Clerk)                                     │
│  • UI/UX Components (HeroUI)                                 │
│  • State Management (React Query / SWR)                      │
│  • Direct File Uploads a Supabase Storage                    │
└────────────┬────────────────────────────────────────┬────────┘
             │                                        │
             │ API Calls                             │ Direct Upload
             ▼                                        ▼
┌────────────────────────────┐        ┌─────────────────────────┐
│   BACKEND API (FastAPI)    │        │   SUPABASE STORAGE      │
│                            │        │                         │
│  ┌──────────────────────┐  │        │  • videos/{user_id}/    │
│  │ Middleware           │  │        │  • audios/{user_id}/    │
│  │ - Clerk Auth Verify  │  │        │  • csv/{user_id}/       │
│  │ - Error Handler      │  │        │  • output/{user_id}/    │
│  └──────────────────────┘  │        └─────────────────────────┘
│                            │
│  ┌──────────────────────┐  │
│  │ Services Layer       │  │
│  │ - UserService        │  │
│  │ - FileService        │◄─┼───────► SUPABASE (PostgreSQL)
│  │ - ProcessingService  │  │           • users
│  │ - JobService         │  │           • files
│  └──────────────────────┘  │           • jobs
│                            │           • projects
│  ┌──────────────────────┐  │
│  │ Background Workers   │  │
│  │ - Video Processing   │  │
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │
             ▼
┌─────────────────────────────┐
│   PROCESSING QUEUE          │
│   (Redis + BullMQ - Futuro) │
│                             │
│   • video-processing        │
│   • ai-generation (Futuro)  │
└─────────────────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   AI SERVICES (Futuro)      │
│                             │
│   • RunPod (Serverless)     │
│     - Nano (Image Gen)      │
│     - Kling (Video Gen)     │
│     - Wan Animate           │
└─────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Frontend Stack

```typescript
{
  "framework": "Next.js 15.3.1",
  "runtime": "React 18.3.1",
  "styling": "Tailwind CSS 4.1.11",
  "components": "HeroUI 2.x",
  "auth": "Clerk",
  "database": "Supabase Client",
  "storage": "Supabase Storage",
  "state": "React Query / SWR (recomendado)",
  "animations": "GSAP + Framer Motion",
  "3d": "Three.js + React Three Fiber",
  "forms": "React Hook Form + Zod",
  "http": "Fetch API + Next.js",
  "env": ".env.local"
}
```

### Backend Stack

```python
{
  "framework": "FastAPI 0.115.0",
  "runtime": "Python 3.11+",
  "server": "Uvicorn",
  "validation": "Pydantic 2.9.2",
  "auth": "Clerk (JWT verification)",
  "database": "Supabase (PostgreSQL via supabase-py)",
  "storage": "Supabase Storage (supabase-py)",
  "video": "OpenCV + MoviePy",
  "tasks": "BackgroundTasks (MVP) → Redis + BullMQ (Escala)",
  "env": "python-dotenv"
}
```

### Infrastructure Stack

```yaml
Database: Supabase PostgreSQL
Storage: Supabase Storage
Auth: Clerk
Queue: BackgroundTasks (MVP) → Redis + Celery/BullMQ (Prod)
AI Processing: RunPod Serverless (Futuro)
Monitoring: (Futuro - Sentry, LogRocket)
Deployment: Vercel (Frontend) + Railway/Render (Backend)
```

---

## 🐍 Arquitectura del Backend

### Estructura de Directorios

```
apps/api/
├── app.py                      # Entry point
├── batch_core.py               # Video processing core (legacy)
├── requirements.txt
├── .env
│
├── core/                       # Core application
│   ├── __init__.py
│   ├── config.py              # Settings con Pydantic
│   ├── dependencies.py        # DI Container
│   ├── exceptions.py          # Custom exceptions
│   └── security.py            # 🆕 Clerk JWT verification
│
├── models/                     # 🆕 SQLAlchemy/Supabase models
│   ├── __init__.py
│   ├── user.py                # User model
│   ├── file.py                # File metadata model
│   ├── job.py                 # Job model
│   └── project.py             # Project model
│
├── schemas/                    # Pydantic DTOs
│   ├── __init__.py
│   ├── user_schemas.py        # 🆕
│   ├── file_schemas.py
│   ├── processing_schemas.py
│   └── job_schemas.py
│
├── services/                   # Business Logic
│   ├── __init__.py
│   ├── auth_service.py        # 🆕 Clerk integration
│   ├── user_service.py        # 🆕 User CRUD
│   ├── storage_service.py     # 🆕 Supabase Storage
│   ├── file_service.py        # File metadata CRUD
│   ├── job_service.py         # Job CRUD (con DB)
│   ├── processing_service.py  # Video processing
│   └── ai_service.py          # 🔮 Futuro - AI integrations
│
├── routers/                    # HTTP Routes
│   ├── __init__.py
│   ├── auth.py                # 🆕 Auth endpoints
│   ├── users.py               # 🆕 User endpoints
│   ├── files.py               # File endpoints
│   ├── folders.py             # Folder endpoints
│   ├── processing.py          # Processing endpoints
│   └── ai.py                  # 🔮 Futuro - AI endpoints
│
├── middleware/                 # Middleware
│   ├── __init__.py
│   ├── error_handler.py
│   └── auth_middleware.py     # 🆕 Clerk auth middleware
│
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── supabase_client.py     # 🆕 Supabase singleton
│   ├── logger.py              # Structured logging
│   └── helpers.py
│
└── workers/                    # 🔮 Futuro - Background workers
    ├── __init__.py
    ├── video_worker.py
    └── ai_worker.py
```

### Principios de Arquitectura Backend

#### 1. **Layered Architecture**

```
Request → Middleware → Router → Service → Model/Supabase → Response
```

- **Routers**: Solo reciben requests, validan input, llaman services
- **Services**: Lógica de negocio pura, agnósticos de HTTP
- **Models**: Representación de datos (Pydantic para validación)
- **Supabase Client**: Acceso a base de datos

#### 2. **Dependency Injection**

```python
# core/dependencies.py
from functools import lru_cache
from supabase import Client
from .security import verify_clerk_token

# Supabase client (singleton)
@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)

# Auth dependency
async def get_current_user(
    authorization: str = Header(...),
    supabase: Client = Depends(get_supabase)
):
    """Extract and verify Clerk JWT, return user"""
    token = authorization.replace("Bearer ", "")
    payload = verify_clerk_token(token)  # Clerk JWT verification
    user_id = payload["sub"]

    # Get or create user in Supabase
    user = await get_user_service().get_or_create(user_id, payload)
    return user

# Service dependencies
@lru_cache
def get_file_service() -> FileService:
    return FileService(get_supabase(), get_storage_service())
```

#### 3. **Error Handling**

```python
# core/exceptions.py
class VideoLabException(Exception):
    """Base exception"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class UnauthorizedError(VideoLabException):
    """401 - Unauthorized"""
    pass

class ForbiddenError(VideoLabException):
    """403 - Forbidden (user doesn't own resource)"""
    pass

class NotFoundError(VideoLabException):
    """404 - Not Found"""
    pass

class ValidationError(VideoLabException):
    """400 - Validation Error"""
    pass

# middleware/error_handler.py
exception_handlers = {
    UnauthorizedError: lambda req, exc: JSONResponse(
        status_code=401,
        content={"detail": exc.message, "details": exc.details}
    ),
    ForbiddenError: lambda req, exc: JSONResponse(
        status_code=403,
        content={"detail": exc.message}
    ),
    NotFoundError: lambda req, exc: JSONResponse(
        status_code=404,
        content={"detail": exc.message}
    ),
    # ...
}
```

#### 4. **Type Safety**

```python
# SIEMPRE usar type hints
from typing import List, Optional
from pathlib import Path

async def process_video(
    video_path: Path,
    audio_path: Optional[Path],
    text_segments: List[str],
    config: ProcessingConfig,
    user_id: str
) -> JobStatus:
    """Type hints en TODO"""
    pass
```

---

## ⚛️ Arquitectura del Frontend

### Estructura de Directorios

```
apps/web/
├── app/                        # Next.js App Router
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Landing page
│   ├── providers.tsx          # Context providers
│   │
│   ├── (auth)/                # 🆕 Auth routes (public)
│   │   ├── sign-in/
│   │   │   └── [[...sign-in]]/
│   │   │       └── page.tsx   # Clerk SignIn
│   │   └── sign-up/
│   │       └── [[...sign-up]]/
│   │           └── page.tsx   # Clerk SignUp
│   │
│   └── dashboard/             # Protected routes
│       ├── layout.tsx         # Dashboard layout + auth
│       ├── page.tsx           # Dashboard home
│       ├── create/
│       ├── videos/
│       ├── audios/
│       ├── texts/
│       ├── projects/
│       └── settings/
│
├── components/                 # React components
│   ├── ui/                    # 🆕 Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Table.tsx
│   │   └── Modal.tsx
│   │
│   ├── Dashboard/             # Dashboard-specific
│   │   ├── Sidebar.tsx
│   │   ├── FileTable.tsx
│   │   └── FolderSidebar.tsx
│   │
│   ├── Upload/                # 🆕 Upload components
│   │   ├── FileUploader.tsx
│   │   └── ProgressBar.tsx
│   │
│   └── shared/                # Shared components
│       ├── Navbar.tsx
│       └── ThemeSwitch.tsx
│
├── lib/                        # Utilities and clients
│   ├── api/                   # 🆕 API client
│   │   ├── client.ts          # Axios/Fetch wrapper
│   │   ├── endpoints.ts       # API endpoints
│   │   └── types.ts           # API types
│   │
│   ├── supabase/              # 🆕 Supabase client
│   │   ├── client.ts          # Supabase browser client
│   │   ├── storage.ts         # Storage helpers
│   │   └── types.ts           # Database types
│   │
│   ├── hooks/                 # 🆕 Custom React hooks
│   │   ├── useUser.ts
│   │   ├── useFiles.ts
│   │   ├── useUpload.ts
│   │   └── useJobs.ts
│   │
│   ├── utils.ts
│   └── types.ts
│
├── config/                     # Configuration
│   ├── site.ts
│   └── fonts.ts
│
├── styles/
│   └── globals.css
│
├── middleware.ts              # 🆕 Clerk auth middleware
├── next.config.js
└── .env.local                 # 🆕 Environment variables
```

### Principios de Arquitectura Frontend

#### 1. **Component Architecture**

```
Page (Route) → Layout → Feature Components → UI Components
```

- **Pages**: Solo routing y layout
- **Feature Components**: Lógica de negocio, data fetching
- **UI Components**: Presentational, sin lógica

#### 2. **Data Fetching Pattern**

```typescript
// ❌ NO hacer fetch directo en componentes
const Component = () => {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('/api/data').then(r => r.json()).then(setData);
  }, []);
}

// ✅ SÍ usar custom hooks + React Query/SWR
const Component = () => {
  const { data, isLoading, error } = useFiles();
  // ...
}
```

#### 3. **Authentication Flow**

```typescript
// middleware.ts - Protege rutas
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/',
])

export default clerkMiddleware((auth, request) => {
  if (!isPublicRoute(request)) {
    auth().protect()
  }
})

// dashboard/layout.tsx - Get user
import { currentUser } from '@clerk/nextjs/server'

export default async function DashboardLayout({ children }) {
  const user = await currentUser()

  return (
    <div>
      <Sidebar user={user} />
      {children}
    </div>
  )
}
```

#### 4. **API Client Pattern**

```typescript
// lib/api/client.ts
import { useAuth } from '@clerk/nextjs'

export const apiClient = {
  async request(endpoint: string, options: RequestInit = {}) {
    const { getToken } = useAuth()
    const token = await getToken()

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  },

  get: (url: string) => apiClient.request(url),
  post: (url: string, data: any) => apiClient.request(url, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  // ...
}

// Usage
const files = await apiClient.get('/api/video-processor/files/videos')
```

---

## 🗄️ Integración Supabase

### Setup de Supabase

#### 1. **Schema de Base de Datos**

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (synced with Clerk)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clerk_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Files table
CREATE TABLE files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL, -- Supabase Storage path
  file_type TEXT NOT NULL, -- 'video', 'audio', 'csv'
  size_bytes BIGINT NOT NULL,
  mime_type TEXT,
  subfolder TEXT, -- optional subfolder
  metadata JSONB, -- extra metadata
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects table (output folders)
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  output_folder TEXT, -- Supabase Storage folder
  video_count INT DEFAULT 0,
  total_size_bytes BIGINT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ, -- auto-cleanup after 24h
  deleted_at TIMESTAMPTZ
);

-- Jobs table (processing jobs)
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  job_type TEXT NOT NULL, -- 'single', 'batch', 'ai-generation'
  status TEXT NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
  progress FLOAT DEFAULT 0,
  message TEXT,
  config JSONB, -- processing config
  input_files JSONB, -- array of file IDs
  output_files JSONB, -- array of output paths
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_type ON files(file_type);
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);

-- Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can only see their own data
CREATE POLICY "Users can view own data" ON users
  FOR SELECT USING (auth.jwt() ->> 'sub' = clerk_id);

CREATE POLICY "Users can view own files" ON files
  FOR ALL USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can view own projects" ON projects
  FOR ALL USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));

CREATE POLICY "Users can view own jobs" ON jobs
  FOR ALL USING (user_id IN (
    SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub'
  ));
```

#### 2. **Supabase Storage Buckets**

```sql
-- Create storage buckets
INSERT INTO storage.buckets (id, name, public)
VALUES
  ('videos', 'videos', false),
  ('audios', 'audios', false),
  ('csv', 'csv', false),
  ('output', 'output', false);

-- Storage policies (usuarios solo acceden a sus archivos)
CREATE POLICY "Users can upload own files" ON storage.objects
  FOR INSERT TO authenticated
  WITH CHECK (
    bucket_id IN ('videos', 'audios', 'csv') AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can view own files" ON storage.objects
  FOR SELECT TO authenticated
  USING (
    bucket_id IN ('videos', 'audios', 'csv', 'output') AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );

CREATE POLICY "Users can delete own files" ON storage.objects
  FOR DELETE TO authenticated
  USING (
    bucket_id IN ('videos', 'audios', 'csv', 'output') AND
    (storage.foldername(name))[1] = auth.jwt() ->> 'sub'
  );
```

#### 3. **Backend Integration**

```python
# utils/supabase_client.py
from functools import lru_cache
from supabase import create_client, Client
from core.config import get_settings

@lru_cache
def get_supabase_client() -> Client:
    """Get Supabase client singleton"""
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key  # Service role key for backend
    )

# services/storage_service.py
class StorageService:
    """Supabase Storage operations"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def upload_file(
        self,
        bucket: str,
        path: str,
        file_data: bytes,
        content_type: str
    ) -> str:
        """Upload file to Supabase Storage"""
        result = self.supabase.storage.from_(bucket).upload(
            path,
            file_data,
            {"content-type": content_type}
        )

        # Get public URL (signed if private bucket)
        url = self.supabase.storage.from_(bucket).get_public_url(path)
        return url

    async def download_file(self, bucket: str, path: str) -> bytes:
        """Download file from Supabase Storage"""
        result = self.supabase.storage.from_(bucket).download(path)
        return result

    async def delete_file(self, bucket: str, path: str) -> None:
        """Delete file from Supabase Storage"""
        self.supabase.storage.from_(bucket).remove([path])

    async def list_files(self, bucket: str, path: str = "") -> List[dict]:
        """List files in Supabase Storage"""
        result = self.supabase.storage.from_(bucket).list(path)
        return result

# services/file_service.py
class FileService:
    """File metadata CRUD with Supabase"""

    def __init__(self, supabase: Client, storage: StorageService):
        self.supabase = supabase
        self.storage = storage

    async def create_file_record(
        self,
        user_id: str,
        filename: str,
        filepath: str,
        file_type: str,
        size_bytes: int,
        mime_type: str = None,
        subfolder: str = None
    ) -> dict:
        """Create file metadata record"""
        result = self.supabase.table("files").insert({
            "user_id": user_id,
            "filename": filename,
            "filepath": filepath,
            "file_type": file_type,
            "size_bytes": size_bytes,
            "mime_type": mime_type,
            "subfolder": subfolder
        }).execute()

        return result.data[0]

    async def get_user_files(
        self,
        user_id: str,
        file_type: str = None,
        subfolder: str = None
    ) -> List[dict]:
        """Get user's files"""
        query = self.supabase.table("files").select("*").eq("user_id", user_id)

        if file_type:
            query = query.eq("file_type", file_type)
        if subfolder:
            query = query.eq("subfolder", subfolder)

        result = query.order("created_at", desc=True).execute()
        return result.data
```

#### 4. **Frontend Integration**

```typescript
// lib/supabase/client.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// lib/supabase/storage.ts
export const uploadFile = async (
  bucket: 'videos' | 'audios' | 'csv',
  userId: string,
  file: File,
  subfolder?: string
) => {
  const path = subfolder
    ? `${userId}/${subfolder}/${file.name}`
    : `${userId}/${file.name}`

  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file, {
      cacheControl: '3600',
      upsert: false
    })

  if (error) throw error

  return data.path
}

// Usage in component
const handleUpload = async (file: File) => {
  const { userId } = useAuth()

  // 1. Upload to Supabase Storage
  const path = await uploadFile('videos', userId!, file)

  // 2. Create metadata record via API
  await apiClient.post('/api/video-processor/files/videos', {
    filename: file.name,
    filepath: path,
    size_bytes: file.size,
    mime_type: file.type
  })
}
```

---

## 🔐 Integración Clerk

### Setup de Clerk

#### 1. **Instalación**

```bash
# Frontend
cd apps/web
pnpm add @clerk/nextjs

# Backend
cd apps/api
pip install pyjwt cryptography requests
```

#### 2. **Frontend Setup**

```typescript
// .env.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

// app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  )
}

// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
])

export default clerkMiddleware((auth, request) => {
  if (!isPublicRoute(request)) {
    auth().protect()
  }
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}

// app/(auth)/sign-in/[[...sign-in]]/page.tsx
import { SignIn } from '@clerk/nextjs'

export default function Page() {
  return <SignIn />
}

// app/dashboard/layout.tsx
import { currentUser } from '@clerk/nextjs/server'

export default async function DashboardLayout({ children }) {
  const user = await currentUser()

  if (!user) redirect('/sign-in')

  return <DashboardLayoutContent user={user}>{children}</DashboardLayoutContent>
}
```

#### 3. **Backend Setup**

```python
# requirements.txt
pyjwt==2.8.0
cryptography==41.0.7
requests==2.32.3

# core/config.py
class Settings(BaseSettings):
    # Clerk settings
    clerk_secret_key: str = Field(..., alias="CLERK_SECRET_KEY")
    clerk_publishable_key: str = Field(..., alias="CLERK_PUBLISHABLE_KEY")
    clerk_jwks_url: str = "https://api.clerk.com/v1/jwks"

# core/security.py
import jwt
import requests
from functools import lru_cache
from core.config import get_settings
from core.exceptions import UnauthorizedError

@lru_cache
def get_clerk_jwks():
    """Get Clerk JWKS (cached)"""
    settings = get_settings()
    response = requests.get(settings.clerk_jwks_url)
    return response.json()

def verify_clerk_token(token: str) -> dict:
    """Verify Clerk JWT token"""
    try:
        # Get JWKS
        jwks = get_clerk_jwks()

        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find matching key
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise UnauthorizedError("Invalid token: key not found")

        # Convert JWK to PEM
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

        # Verify and decode token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expired")
    except jwt.InvalidTokenError as e:
        raise UnauthorizedError(f"Invalid token: {str(e)}")

# core/dependencies.py
from fastapi import Depends, Header
from core.security import verify_clerk_token
from services.user_service import UserService

async def get_current_user(
    authorization: str = Header(...),
    user_service: UserService = Depends(get_user_service),
):
    """Extract user from Clerk JWT"""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = verify_clerk_token(token)

    # Get or create user in Supabase
    clerk_id = payload["sub"]
    email = payload.get("email", "")

    user = await user_service.get_or_create_user(
        clerk_id=clerk_id,
        email=email,
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
    )

    return user

# routers/files.py
from core.dependencies import get_current_user

@router.post("/upload/video")
async def upload_video(
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service)
):
    """Upload video (protected route)"""
    # current_user contiene info del usuario autenticado
    return await file_service.upload_video(file, current_user["id"])
```

---

## ⚙️ Sistema de Colas y Jobs

### Estado Actual vs Futuro

#### **MVP (Actual) - FastAPI BackgroundTasks**

```python
# Pros: Simple, sin dependencias extra
# Cons: No escalable, no retry, se pierde al reiniciar

@router.post("/process-batch")
async def process_batch(
    request: BatchRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    job_id = await job_service.create_job(current_user["id"], "batch")

    background_tasks.add_task(
        processing_service.process_batch_videos,
        job_id,
        request.video_folder,
        # ...
    )

    return {"job_id": job_id, "status": "queued"}
```

#### **Producción (Futuro) - Redis + Celery/BullMQ**

```python
# Pros: Escalable, retry, persistencia, priority queues
# Cons: Requiere Redis, más complejo

# Opción 1: Celery (Python workers)
from celery import Celery

celery_app = Celery('videolab', broker='redis://localhost:6379/0')

@celery_app.task(bind=True, max_retries=3)
def process_batch_task(self, job_id: str, config: dict):
    try:
        # Processing logic
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# Opción 2: BullMQ (Node.js workers - más común para video)
# Worker en Node.js consume jobs y llama a Python scripts
```

**Recomendación MVP**: Usar BackgroundTasks ahora, migrar a Redis+Celery cuando escales.

---

## 🔮 Plan para IA Generativa (Futuro)

### Arquitectura de IA (Nano, Kling, Wan Animate)

```
Frontend                Backend API              RunPod Serverless
   │                        │                          │
   │  POST /ai/generate     │                          │
   ├───────────────────────►│                          │
   │                        │  Create job in DB        │
   │                        ├─────────────────┐        │
   │                        │                 │        │
   │  Job ID + Status       │                 ▼        │
   │◄───────────────────────┤          Queue job       │
   │                        │          (Redis)         │
   │                        │                 │        │
   │  Poll /ai/jobs/{id}    │                 │        │
   ├───────────────────────►│                 │        │
   │                        │                 │        │
   │                        │                 ▼        │
   │                        │          Worker picks    │
   │                        │          job from queue  │
   │                        │                 │        │
   │                        │                 │        │
   │                        │  POST /run      │        │
   │                        │─────────────────────────►│
   │                        │                          │ Run AI model
   │                        │                          │ (Nano/Kling/Wan)
   │                        │  Response with URL       │
   │                        │◄─────────────────────────┤
   │                        │                          │
   │                        │  Update job status       │
   │                        │  Save output to Supabase │
   │                        │                          │
   │  Job completed         │                          │
   │◄───────────────────────┤                          │
```

### RunPod Integration

```python
# services/ai_service.py
import httpx
from core.config import get_settings

class AIService:
    """AI Generation service (RunPod integration)"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.settings = get_settings()

    async def generate_image(
        self,
        user_id: str,
        prompt: str,
        model: str = "nano"
    ) -> str:
        """Generate image using RunPod serverless"""

        # 1. Create job in DB
        job = await self.create_ai_job(user_id, "image-generation", {
            "prompt": prompt,
            "model": model
        })

        # 2. Queue job (Redis) - worker picks it up
        await self.queue_ai_job(job["id"])

        return job["id"]

    async def _run_image_generation(self, job_id: str, config: dict):
        """Worker function - runs in background"""
        try:
            # Update job status
            await self.update_job(job_id, "processing")

            # Call RunPod API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.settings.runpod_url}/run",
                    json={
                        "input": {
                            "prompt": config["prompt"],
                            "model": config["model"]
                        }
                    },
                    headers={
                        "Authorization": f"Bearer {self.settings.runpod_api_key}"
                    },
                    timeout=300  # 5 min timeout
                )

            result = response.json()
            output_url = result["output"]["image_url"]

            # Download image and upload to Supabase Storage
            async with httpx.AsyncClient() as client:
                image_response = await client.get(output_url)
                image_data = image_response.content

            # Upload to Supabase
            user_id = await self.get_job_user_id(job_id)
            path = f"{user_id}/ai-generated/{job_id}.png"

            await self.storage_service.upload_file(
                "output",
                path,
                image_data,
                "image/png"
            )

            # Update job as completed
            await self.update_job(job_id, "completed", output_files=[path])

        except Exception as e:
            await self.update_job(job_id, "failed", error=str(e))

# routers/ai.py
@router.post("/ai/generate/image")
async def generate_image(
    request: ImageGenerationRequest,
    current_user: dict = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """Generate image with AI"""
    job_id = await ai_service.generate_image(
        current_user["id"],
        request.prompt,
        request.model
    )

    return {"job_id": job_id, "status": "queued"}
```

### Estrategia de Implementación IA

**Fase 1 - MVP (SIN IA)**
- ✅ Solo video processing actual
- ✅ Arquitectura preparada para IA

**Fase 2 - Image Generation (Nano)**
- Integrar RunPod Serverless
- Endpoint `/ai/generate/image`
- Queue system (Redis + Celery)

**Fase 3 - Video Generation (Kling)**
- Endpoint `/ai/generate/video`
- Mismo patrón que image gen

**Fase 4 - Wan Animate**
- Endpoint `/ai/animate`
- Image → Animated video

**Clave**: La arquitectura actual YA está lista. Solo necesitas:
1. Agregar `routers/ai.py`
2. Agregar `services/ai_service.py`
3. Configurar RunPod
4. Usar el mismo patrón de jobs

---

## 🚫 Reglas Inquebrantables

### Backend (Python/FastAPI)

#### ✅ SIEMPRE

1. **Type Hints en TODO**
   ```python
   # ✅ CORRECTO
   def process_video(video_path: Path, config: dict) -> JobStatus:
       pass

   # ❌ INCORRECTO
   def process_video(video_path, config):
       pass
   ```

2. **Dependency Injection**
   ```python
   # ✅ CORRECTO
   @router.get("/files")
   async def get_files(
       current_user: dict = Depends(get_current_user),
       file_service: FileService = Depends(get_file_service)
   ):
       return await file_service.get_user_files(current_user["id"])

   # ❌ INCORRECTO - instanciar service directamente
   @router.get("/files")
   async def get_files():
       service = FileService()  # NO!
       return service.get_files()
   ```

3. **Pydantic para Validación**
   ```python
   # ✅ CORRECTO
   class VideoUploadRequest(BaseModel):
       subfolder: Optional[str] = None

       @field_validator("subfolder")
       @classmethod
       def validate_subfolder(cls, v):
           if v and ".." in v:
               raise ValueError("Invalid folder")
           return v

   @router.post("/upload")
   async def upload(request: VideoUploadRequest):
       pass

   # ❌ INCORRECTO - validar manualmente
   @router.post("/upload")
   async def upload(subfolder: str = None):
       if subfolder and ".." in subfolder:
           raise HTTPException(400, "Invalid")
   ```

4. **Custom Exceptions**
   ```python
   # ✅ CORRECTO
   if not file.exists():
       raise NotFoundError(f"File not found: {file}")

   # ❌ INCORRECTO
   if not file.exists():
       raise HTTPException(status_code=404, detail="Not found")
   ```

5. **Async cuando sea posible**
   ```python
   # ✅ CORRECTO
   async def get_files(self, user_id: str) -> List[File]:
       result = self.supabase.table("files").select("*").eq("user_id", user_id).execute()
       return result.data

   # ⚠️ SOLO usar sync si la operación es genuinamente bloqueante (OpenCV, etc)
   ```

6. **Logging estructurado**
   ```python
   # ✅ CORRECTO
   logger.info(f"File uploaded: {filename}", extra={
       "user_id": user_id,
       "file_size": size,
       "file_type": file_type
   })

   # ❌ INCORRECTO
   print(f"File uploaded: {filename}")
   ```

#### ❌ NUNCA

1. **❌ NUNCA hardcodear paths**
   ```python
   # ❌ INCORRECTO
   VIDEO_DIR = "D:/Work/video/videos"

   # ✅ CORRECTO
   class Settings(BaseSettings):
       storage_base_dir: Path = Field(..., alias="STORAGE_DIR")
   ```

2. **❌ NUNCA exponer errores internos**
   ```python
   # ❌ INCORRECTO
   except Exception as e:
       raise HTTPException(500, detail=str(e))  # Expone stacktrace

   # ✅ CORRECTO
   except Exception as e:
       logger.error(f"Processing error: {e}", exc_info=True)
       raise ProcessingError("Failed to process video")
   ```

3. **❌ NUNCA ignorar autenticación**
   ```python
   # ❌ INCORRECTO
   @router.post("/upload")
   async def upload(file: UploadFile):
       pass  # Sin auth!

   # ✅ CORRECTO
   @router.post("/upload")
   async def upload(
       file: UploadFile,
       current_user: dict = Depends(get_current_user)
   ):
       pass
   ```

4. **❌ NUNCA mezclar lógica de negocio en routers**
   ```python
   # ❌ INCORRECTO
   @router.post("/process")
   async def process(video_path: str):
       # 50 líneas de lógica de procesamiento aquí
       video = cv2.VideoCapture(video_path)
       # ...

   # ✅ CORRECTO
   @router.post("/process")
   async def process(
       request: ProcessRequest,
       service: ProcessingService = Depends(get_processing_service)
   ):
       return await service.process_video(request)
   ```

5. **❌ NUNCA usar global state mutable**
   ```python
   # ❌ INCORRECTO
   JOBS = {}  # Global dict

   def create_job(job_id: str):
       JOBS[job_id] = {...}  # Not thread-safe!

   # ✅ CORRECTO - usar Supabase o al menos un singleton con locks
   class JobService:
       def __init__(self, supabase: Client):
           self.supabase = supabase
   ```

### Frontend (Next.js/React)

#### ✅ SIEMPRE

1. **TypeScript estricto**
   ```typescript
   // ✅ CORRECTO
   interface User {
     id: string
     email: string
   }

   const getUser = async (id: string): Promise<User> => {
     const response = await fetch(`/api/users/${id}`)
     return response.json()
   }

   // ❌ INCORRECTO
   const getUser = async (id) => {
     const response = await fetch(`/api/users/${id}`)
     return response.json()
   }
   ```

2. **Custom Hooks para lógica**
   ```typescript
   // ✅ CORRECTO
   // hooks/useFiles.ts
   export const useFiles = (type: 'video' | 'audio' | 'csv') => {
     const { userId } = useAuth()
     const { data, error, isLoading } = useSWR(
       userId ? `/api/files/${type}` : null,
       fetcher
     )
     return { files: data, error, isLoading }
   }

   // Component
   const Component = () => {
     const { files, isLoading } = useFiles('video')
     if (isLoading) return <Spinner />
     return <FileList files={files} />
   }

   // ❌ INCORRECTO - fetch en componente
   const Component = () => {
     const [files, setFiles] = useState([])
     useEffect(() => {
       fetch('/api/files/video').then(r => r.json()).then(setFiles)
     }, [])
   }
   ```

3. **Environment Variables**
   ```typescript
   // ✅ CORRECTO
   const API_URL = process.env.NEXT_PUBLIC_API_URL!

   // ❌ INCORRECTO
   const API_URL = "http://localhost:8000"
   ```

4. **Error Boundaries**
   ```typescript
   // ✅ CORRECTO - wrap async components
   <Suspense fallback={<Loading />}>
     <ErrorBoundary fallback={<ErrorUI />}>
       <DashboardContent />
     </ErrorBoundary>
   </Suspense>
   ```

5. **Server Components cuando sea posible**
   ```typescript
   // ✅ CORRECTO - fetch data on server
   // app/dashboard/page.tsx (Server Component)
   export default async function DashboardPage() {
     const user = await currentUser()
     const stats = await getStats(user.id)

     return <DashboardClient stats={stats} />
   }

   // ❌ INCORRECTO - fetch todo en cliente
   'use client'
   export default function DashboardPage() {
     const [stats, setStats] = useState(null)
     useEffect(() => {
       fetch('/api/stats').then(r => r.json()).then(setStats)
     }, [])
   }
   ```

#### ❌ NUNCA

1. **❌ NUNCA guardar secrets en cliente**
   ```typescript
   // ❌ INCORRECTO
   const SUPABASE_SERVICE_KEY = "..." // NUNCA en frontend!

   // ✅ CORRECTO - solo anon key
   const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
   ```

2. **❌ NUNCA confiar en cliente**
   ```typescript
   // ❌ INCORRECTO
   const deleteFile = async (fileId: string) => {
     // Solo validar en frontend
     if (fileId) {
       await fetch(`/api/files/${fileId}`, { method: 'DELETE' })
     }
   }

   // ✅ CORRECTO - SIEMPRE validar en backend también
   // Backend verifica que el usuario sea dueño del archivo
   ```

3. **❌ NUNCA usar `any`**
   ```typescript
   // ❌ INCORRECTO
   const processData = (data: any) => {
     return data.map((item: any) => item.name)
   }

   // ✅ CORRECTO
   interface Item {
     id: string
     name: string
   }

   const processData = (data: Item[]) => {
     return data.map(item => item.name)
   }
   ```

4. **❌ NUNCA hacer fetch sin auth**
   ```typescript
   // ❌ INCORRECTO
   const getFiles = async () => {
     const response = await fetch('/api/files')
     return response.json()
   }

   // ✅ CORRECTO
   const getFiles = async () => {
     const { getToken } = useAuth()
     const token = await getToken()

     const response = await fetch('/api/files', {
       headers: {
         'Authorization': `Bearer ${token}`
       }
     })
     return response.json()
   }
   ```

---

## 📝 Convenciones de Código

### Naming Conventions

#### Python (Backend)

```python
# Files: snake_case
file_service.py
processing_service.py

# Classes: PascalCase
class FileService:
    pass

class ProcessingConfig(BaseModel):
    pass

# Functions/Methods: snake_case
def upload_video(file: UploadFile) -> FileUploadResponse:
    pass

async def process_batch_videos(job_id: str) -> None:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_VIDEO_SIZE = 500 * 1024 * 1024
DEFAULT_CONFIG = {...}

# Private methods: _leading_underscore
def _build_output_path(self, video_name: str) -> Path:
    pass
```

#### TypeScript (Frontend)

```typescript
// Files: kebab-case or PascalCase for components
file-uploader.tsx
FileUploader.tsx
use-files.ts

// Components: PascalCase
const FileUploader = () => {
  return <div>...</div>
}

// Functions/Variables: camelCase
const uploadFile = async (file: File) => {
  // ...
}

const isUploading = false

// Constants: UPPER_SNAKE_CASE
const MAX_FILE_SIZE = 500 * 1024 * 1024
const API_URL = process.env.NEXT_PUBLIC_API_URL

// Types/Interfaces: PascalCase
interface User {
  id: string
  email: string
}

type FileType = 'video' | 'audio' | 'csv'
```

### File Organization

```python
# Backend - cada archivo debe tener:
"""
Module docstring explaining purpose
"""
import standard_library
import third_party
from local_module import something

# Constants
CONSTANT_VALUE = 123

# Classes
class MyClass:
    """Class docstring"""

    def __init__(self):
        """Constructor docstring"""
        pass

    def public_method(self) -> ReturnType:
        """Method docstring"""
        pass

    def _private_method(self) -> ReturnType:
        """Private method docstring"""
        pass

# Functions
def helper_function() -> ReturnType:
    """Function docstring"""
    pass
```

```typescript
// Frontend - cada archivo debe tener:
import React from 'react'
import { thirdPartyLib } from 'library'
import { LocalComponent } from '@/components'

// Types
interface Props {
  // ...
}

// Constants
const CONSTANT = 'value'

// Component
export const MyComponent: React.FC<Props> = ({ prop }) => {
  // Hooks
  const [state, setState] = useState()

  // Handlers
  const handleClick = () => {
    // ...
  }

  // Render
  return <div>...</div>
}
```

### Git Commit Messages

```bash
# Formato: <type>(<scope>): <subject>

# Types:
feat: Nueva feature
fix: Bug fix
refactor: Refactorización
docs: Documentación
style: Formatting
test: Tests
chore: Build/config

# Ejemplos:
git commit -m "feat(auth): integrate Clerk authentication"
git commit -m "fix(upload): handle large file uploads correctly"
git commit -m "refactor(services): move business logic to services layer"
git commit -m "docs(api): add API documentation for processing endpoints"
```

---

## 🚀 Plan de Acción MVP

### Fase 1: Setup Básico (Semana 1)

#### 1.1 Configuración de Supabase

**Prioridad: ALTA**

```bash
# Tareas:
□ Crear proyecto en Supabase
□ Ejecutar schema SQL (tablas + RLS + storage buckets)
□ Obtener credenciales (URL, anon key, service key)
□ Configurar variables de entorno
```

**Archivos a crear/modificar:**

```bash
# Backend
apps/api/.env
apps/api/utils/supabase_client.py
apps/api/models/user.py
apps/api/models/file.py
apps/api/models/job.py
apps/api/models/project.py

# Frontend
apps/web/.env.local
apps/web/lib/supabase/client.ts
apps/web/lib/supabase/storage.ts
apps/web/lib/supabase/types.ts  # Generate with supabase gen types
```

**Comandos:**

```bash
# Backend
cd apps/api
pip install supabase

# Frontend
cd apps/web
pnpm add @supabase/supabase-js
pnpm add @supabase/auth-helpers-nextjs
```

#### 1.2 Configuración de Clerk

**Prioridad: ALTA**

```bash
# Tareas:
□ Crear aplicación en Clerk Dashboard
□ Configurar OAuth providers (Google, GitHub, etc)
□ Obtener API keys
□ Configurar variables de entorno
```

**Archivos a crear/modificar:**

```bash
# Frontend
apps/web/.env.local (agregar Clerk keys)
apps/web/middleware.ts
apps/web/app/layout.tsx (wrap con ClerkProvider)
apps/web/app/(auth)/sign-in/[[...sign-in]]/page.tsx
apps/web/app/(auth)/sign-up/[[...sign-up]]/page.tsx
apps/web/app/dashboard/layout.tsx (proteger rutas)

# Backend
apps/api/.env (agregar Clerk secret key)
apps/api/core/security.py
apps/api/core/dependencies.py (get_current_user)
apps/api/services/user_service.py
apps/api/routers/auth.py
```

**Comandos:**

```bash
# Backend
cd apps/api
pip install pyjwt cryptography requests

# Frontend
cd apps/web
pnpm add @clerk/nextjs
```

#### 1.3 Migrar Storage a Supabase

**Prioridad: MEDIA**

```bash
# Tareas:
□ Actualizar FileService para usar Supabase Storage
□ Crear StorageService con Supabase
□ Migrar uploads de disco local a Supabase
□ Actualizar endpoints de streaming
□ Crear metadata records en DB
```

**Archivos a modificar:**

```bash
apps/api/services/storage_service.py  # Reescribir
apps/api/services/file_service.py     # Usar Supabase
apps/api/routers/files.py              # Actualizar uploads
apps/web/lib/supabase/storage.ts       # Upload helpers
apps/web/components/Upload/FileUploader.tsx  # Frontend upload
```

---

### Fase 2: Autenticación & Usuarios (Semana 2)

#### 2.1 Implementar Auth en Backend

```bash
# Tareas:
□ Implementar verify_clerk_token()
□ Crear dependency get_current_user()
□ Proteger todos los endpoints con auth
□ Crear UserService (get_or_create_user)
□ Sync Clerk → Supabase en login
```

**Testing:**

```bash
# Test auth flow
curl -X POST http://localhost:8000/api/video-processor/files/upload/video \
  -H "Authorization: Bearer <clerk-jwt>" \
  -F "file=@test.mp4"
```

#### 2.2 Implementar Auth en Frontend

```bash
# Tareas:
□ Configurar ClerkProvider
□ Crear middleware de autenticación
□ Proteger rutas /dashboard
□ Crear páginas de sign-in/sign-up
□ Agregar user menu en navbar
□ Crear useAuth hook
```

**Testing:**

```bash
# Verificar:
- Redirección a /sign-in si no autenticado
- Sign-up funciona correctamente
- Usuario aparece en Supabase tras login
- Dashboard muestra info del usuario
```

---

### Fase 3: Migración a Supabase Storage (Semana 2-3)

#### 3.1 Backend Storage Migration

```bash
# Tareas:
□ Reescribir StorageService con Supabase
□ Actualizar FileService para crear metadata
□ Modificar upload endpoints
□ Modificar download/stream endpoints
□ Implementar file deletion
□ Agregar validación de ownership (user solo accede a sus archivos)
```

#### 3.2 Frontend Upload Migration

```bash
# Tareas:
□ Crear componente FileUploader
□ Upload directo a Supabase Storage desde frontend
□ Crear metadata via API después de upload
□ Progress bar para uploads
□ Error handling
```

**Ejemplo de flujo:**

```typescript
// Frontend upload flow
const handleUpload = async (file: File) => {
  const { userId } = useAuth()

  // 1. Upload to Supabase Storage (direct from browser)
  const { data, error } = await supabase.storage
    .from('videos')
    .upload(`${userId}/${file.name}`, file, {
      cacheControl: '3600',
      upsert: false,
      onUploadProgress: (progress) => {
        setProgress((progress.loaded / progress.total) * 100)
      }
    })

  if (error) throw error

  // 2. Create metadata record via API
  await apiClient.post('/api/video-processor/files/videos', {
    filename: file.name,
    filepath: data.path,
    size_bytes: file.size,
    mime_type: file.type
  })

  // 3. Refresh file list
  mutate('/api/video-processor/files/videos')
}
```

---

### Fase 4: Job System con Persistencia (Semana 3)

#### 4.1 Migrar JobService a Supabase

```bash
# Tareas:
□ Reescribir JobService para usar Supabase DB
□ Crear job records en DB
□ Actualizar job status en DB
□ Queries para get_user_jobs()
□ Cleanup de jobs antiguos
```

**Cambios:**

```python
# Antes (in-memory)
class JobService:
    def __init__(self):
        self.jobs = {}  # Lost on restart!

# Después (persistent)
class JobService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_job(self, user_id: str, job_type: str, config: dict) -> dict:
        result = self.supabase.table("jobs").insert({
            "user_id": user_id,
            "job_type": job_type,
            "status": "pending",
            "config": config
        }).execute()
        return result.data[0]
```

#### 4.2 Frontend Job Polling

```bash
# Tareas:
□ Crear useJob hook
□ Polling automático de job status
□ Job history page
□ Cancel job functionality
```

```typescript
// hooks/useJob.ts
export const useJob = (jobId: string) => {
  const { data: job } = useSWR(
    jobId ? `/api/video-processor/processing/status/${jobId}` : null,
    fetcher,
    {
      refreshInterval: (data) => {
        // Poll every 2s if job is running
        if (data?.status === 'pending' || data?.status === 'processing') {
          return 2000
        }
        return 0 // Stop polling if completed/failed
      }
    }
  )

  return { job }
}
```

---

### Fase 5: Projects & Output Management (Semana 4)

#### 5.1 Projects System

```bash
# Tareas:
□ Crear ProjectService
□ Auto-create project on batch processing
□ List user projects
□ Project details (list output videos)
□ Delete project (+ cleanup storage)
□ Auto-delete projects after 24h (cron job)
```

#### 5.2 Output Gallery

```bash
# Tareas:
□ Projects page (/dashboard/projects)
□ Project detail view
□ Video grid con thumbnails
□ Download individual videos
□ Download all as zip (futuro)
□ Share project (futuro)
```

---

### Fase 6: Polish & UX (Semana 4-5)

#### 6.1 Error Handling

```bash
# Tareas:
□ Toast notifications (sonner/react-hot-toast)
□ Error boundaries
□ Retry logic en uploads
□ User-friendly error messages
```

#### 6.2 Loading States

```bash
# Tareas:
□ Skeleton loaders
□ Suspense boundaries
□ Progress indicators
□ Optimistic updates
```

#### 6.3 Responsive Design

```bash
# Tareas:
□ Mobile-responsive dashboard
□ Tablet layouts
□ Touch-friendly controls
```

---

### Fase 7: Testing & Deployment (Semana 5-6)

#### 7.1 Testing

```bash
# Backend
□ Unit tests para services
□ Integration tests para endpoints
□ Test auth flow

# Frontend
□ Component tests (Vitest/Jest)
□ E2E tests (Playwright)
□ Test upload flow
```

#### 7.2 Deployment

```bash
# Frontend (Vercel)
□ Deploy a Vercel
□ Configurar env variables
□ Custom domain

# Backend (Railway/Render)
□ Deploy API
□ Configurar env variables
□ Custom domain
□ HTTPS + CORS

# Database (Supabase)
□ Production database
□ Backups configurados
```

---

## 📡 Guía de Llamadas API desde Frontend

### Pattern Recomendado: API Client + React Query/SWR

#### Setup de API Client

```typescript
// lib/api/client.ts
import { useAuth } from '@clerk/nextjs'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class APIClient {
  private async getToken(): Promise<string | null> {
    // This needs to be called in a component/hook context
    // We'll handle this differently
    return null
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    token?: string
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Helper methods
  get<T>(url: string, token?: string) {
    return this.request<T>(url, { method: 'GET' }, token)
  }

  post<T>(url: string, data?: any, token?: string) {
    return this.request<T>(
      url,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      token
    )
  }

  put<T>(url: string, data?: any, token?: string) {
    return this.request<T>(
      url,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      token
    )
  }

  delete<T>(url: string, token?: string) {
    return this.request<T>(url, { method: 'DELETE' }, token)
  }

  // File upload with auth
  async upload<T>(
    url: string,
    formData: FormData,
    token: string,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      xhr.open('POST', `${API_URL}${url}`)
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)

      if (onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            onProgress((e.loaded / e.total) * 100)
          }
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText))
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`))
        }
      }

      xhr.onerror = () => reject(new Error('Network error'))
      xhr.send(formData)
    })
  }
}

export const apiClient = new APIClient()
```

#### Custom Hooks con SWR

```typescript
// lib/hooks/useFiles.ts
import useSWR from 'swr'
import { useAuth } from '@clerk/nextjs'
import { apiClient } from '@/lib/api/client'

interface File {
  id: string
  filename: string
  filepath: string
  file_type: string
  size_bytes: number
  created_at: string
}

export const useFiles = (type: 'video' | 'audio' | 'csv', subfolder?: string) => {
  const { getToken } = useAuth()

  const fetcher = async (url: string) => {
    const token = await getToken()
    return apiClient.get<{ files: File[]; count: number }>(url, token || undefined)
  }

  const params = subfolder ? `?subfolder=${subfolder}` : ''
  const { data, error, mutate } = useSWR(
    `/api/video-processor/files/${type}${params}`,
    fetcher
  )

  return {
    files: data?.files || [],
    count: data?.count || 0,
    isLoading: !error && !data,
    isError: error,
    mutate, // For manual revalidation
  }
}

// Usage in component
const VideosList = () => {
  const { files, isLoading, isError } = useFiles('video')

  if (isLoading) return <Spinner />
  if (isError) return <ErrorMessage />

  return <FileTable files={files} />
}
```

#### Upload Hook

```typescript
// lib/hooks/useUpload.ts
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { apiClient } from '@/lib/api/client'
import { supabase } from '@/lib/supabase/client'

export const useUpload = () => {
  const { userId, getToken } = useAuth()
  const [progress, setProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const uploadFile = async (
    file: File,
    bucket: 'videos' | 'audios' | 'csv',
    subfolder?: string
  ) => {
    setIsUploading(true)
    setError(null)
    setProgress(0)

    try {
      // 1. Upload to Supabase Storage
      const path = subfolder
        ? `${userId}/${subfolder}/${file.name}`
        : `${userId}/${file.name}`

      const { data: uploadData, error: uploadError } = await supabase.storage
        .from(bucket)
        .upload(path, file, {
          cacheControl: '3600',
          upsert: false,
        })

      if (uploadError) throw uploadError

      setProgress(50)

      // 2. Create metadata record via API
      const token = await getToken()
      if (!token) throw new Error('Not authenticated')

      await apiClient.post(
        `/api/video-processor/files/${bucket}`,
        {
          filename: file.name,
          filepath: uploadData.path,
          size_bytes: file.size,
          mime_type: file.type,
          subfolder,
        },
        token
      )

      setProgress(100)
      return uploadData.path
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setIsUploading(false)
    }
  }

  return {
    uploadFile,
    progress,
    isUploading,
    error,
  }
}

// Usage
const Uploader = () => {
  const { uploadFile, progress, isUploading } = useUpload()
  const { mutate } = useFiles('video') // Revalidate after upload

  const handleUpload = async (file: File) => {
    try {
      await uploadFile(file, 'videos')
      mutate() // Refresh file list
      toast.success('File uploaded!')
    } catch (err) {
      toast.error('Upload failed')
    }
  }

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files![0])} />
      {isUploading && <Progress value={progress} />}
    </div>
  )
}
```

#### Job Status Hook

```typescript
// lib/hooks/useJob.ts
import useSWR from 'swr'
import { useAuth } from '@clerk/nextjs'
import { apiClient } from '@/lib/api/client'

interface Job {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  output_files: string[]
}

export const useJob = (jobId: string | null) => {
  const { getToken } = useAuth()

  const fetcher = async (url: string) => {
    const token = await getToken()
    return apiClient.get<Job>(url, token || undefined)
  }

  const { data: job, error } = useSWR(
    jobId ? `/api/video-processor/processing/status/${jobId}` : null,
    fetcher,
    {
      refreshInterval: (data) => {
        // Auto-poll every 2s if job is running
        if (data?.status === 'pending' || data?.status === 'processing') {
          return 2000
        }
        return 0 // Stop polling when done
      },
    }
  )

  return {
    job,
    isLoading: !error && !job && jobId !== null,
    isError: error,
  }
}

// Usage
const BatchProcessing = () => {
  const [jobId, setJobId] = useState<string | null>(null)
  const { job } = useJob(jobId)

  const startProcessing = async () => {
    const token = await getToken()
    const result = await apiClient.post<{ job_id: string }>(
      '/api/video-processor/processing/process-batch',
      { /* config */ },
      token!
    )
    setJobId(result.job_id)
  }

  return (
    <div>
      <button onClick={startProcessing}>Start</button>
      {job && (
        <div>
          <p>Status: {job.status}</p>
          <Progress value={job.progress} />
        </div>
      )}
    </div>
  )
}
```

### Ejemplo Completo de Flujo

```typescript
// components/Dashboard/CreateProject.tsx
'use client'

import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useFiles } from '@/lib/hooks/useFiles'
import { useJob } from '@/lib/hooks/useJob'
import { apiClient } from '@/lib/api/client'
import { Button, Select, Progress } from '@heroui/react'

export const CreateProject = () => {
  const { getToken } = useAuth()
  const { files: videoFolders } = useFiles('video')
  const { files: audioFolders } = useFiles('audio')

  const [selectedVideo, setSelectedVideo] = useState('')
  const [selectedAudio, setSelectedAudio] = useState('')
  const [jobId, setJobId] = useState<string | null>(null)

  const { job, isLoading: jobLoading } = useJob(jobId)

  const startProcessing = async () => {
    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated')

      const result = await apiClient.post<{ job_id: string }>(
        '/api/video-processor/processing/process-batch',
        {
          video_folder: selectedVideo,
          audio_folder: selectedAudio,
          text_combinations: [['Sample text']],
          output_folder: 'output',
          unique_mode: true,
          unique_amount: 10,
        },
        token
      )

      setJobId(result.job_id)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="space-y-4">
      <Select
        label="Video Folder"
        value={selectedVideo}
        onChange={(e) => setSelectedVideo(e.target.value)}
      >
        {videoFolders.map((folder) => (
          <option key={folder.id} value={folder.filepath}>
            {folder.filename}
          </option>
        ))}
      </Select>

      <Select
        label="Audio Folder"
        value={selectedAudio}
        onChange={(e) => setSelectedAudio(e.target.value)}
      >
        {audioFolders.map((folder) => (
          <option key={folder.id} value={folder.filepath}>
            {folder.filename}
          </option>
        ))}
      </Select>

      <Button
        onClick={startProcessing}
        disabled={!selectedVideo || !selectedAudio || jobLoading}
      >
        Start Processing
      </Button>

      {job && (
        <div>
          <p>Status: {job.status}</p>
          <Progress value={job.progress} />
          <p>{job.message}</p>
        </div>
      )}
    </div>
  )
}
```

---

## 🎓 Resumen Ejecutivo

### Lo que tienes que hacer AHORA (MVP):

1. **Integrar Clerk** (Auth)
   - Frontend: ClerkProvider + middleware
   - Backend: JWT verification

2. **Integrar Supabase** (DB + Storage)
   - Crear schema
   - Migrar storage de disco local a Supabase
   - Persistir jobs en DB

3. **Conectar todo**
   - Frontend llama API con Clerk token
   - API verifica token, accede a Supabase
   - Users solo ven sus propios archivos

4. **Polish UX**
   - Error handling
   - Loading states
   - Responsive design

### Lo que NO hacer ahora (Futuro):

- ❌ IA generativa (Nano/Kling/Wan) - Dejar arquitectura lista
- ❌ Redis + Celery - Usar BackgroundTasks por ahora
- ❌ Advanced features - Focus en MVP

### Arquitectura Final (Simplificada):

```
User → Frontend (Next.js + Clerk) → Backend API (FastAPI + Clerk verify) → Supabase (DB + Storage)
                                            ↓
                                    Background Tasks (Jobs)
```

---

## 📚 Recursos

### Documentación Oficial

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js 15](https://nextjs.org/docs)
- [Clerk](https://clerk.com/docs)
- [Supabase](https://supabase.com/docs)
- [Pydantic](https://docs.pydantic.dev/)
- [SWR](https://swr.vercel.app/)
- [HeroUI](https://www.heroui.com/)

### Tutorials Recomendados

- [FastAPI + Supabase](https://supabase.com/docs/guides/api/rest/python)
- [Next.js + Clerk + Supabase](https://clerk.com/docs/integrations/databases/supabase)
- [Clean Architecture FastAPI](https://github.com/zhanymkanov/fastapi-best-practices)

---

## 🎯 Next Steps

1. **Leer este documento completo** ✅
2. **Crear cuentas**: Clerk + Supabase
3. **Seguir Fase 1** del Plan de Acción
4. **Commit frecuentes** siguiendo convenciones
5. **Testear cada feature** antes de continuar
6. **Documentar cambios** en comments

**IMPORTANTE**: Este documento es tu biblia. Sigue las reglas inquebrantables, usa los patrones definidos, y tu código será profesional, escalable y mantenible.

---

**¡Éxito con tu MVP! 🚀**
