# Video Monorepo

Un monorepo con Turborepo que incluye un frontend Next.js y un backend FastAPI.

## Estructura del Proyecto

```
.
├── apps/
│   ├── web/          # Frontend Next.js
│   └── api/          # Backend FastAPI (Python)
├── packages/         # Librerías compartidas (futuro)
├── turbo.json        # Configuración de Turborepo
└── package.json      # Configuración raíz del monorepo
```

## Tecnologías

- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS, HeroUI
- **Backend**: FastAPI, Python 3.11+, Pydantic, Uvicorn
- **Monorepo**: Turborepo, pnpm workspaces
- **Herramientas**: ESLint, Prettier, Ruff, Black, MyPy

## Instalación

1. Instalar dependencias del monorepo:
```bash
pnpm install
```

2. Configurar el backend Python:
```bash
pnpm --filter api run setup
```

## Desarrollo

Ejecutar ambos servicios en paralelo:
```bash
pnpm dev
```

Esto iniciará:
- Frontend Next.js en http://localhost:3000
- Backend FastAPI en http://localhost:8000

### Comandos Individuales

**Frontend (Next.js):**
```bash
pnpm --filter web dev
pnpm --filter web build
pnpm --filter web lint
```

**Backend (FastAPI):**
```bash
pnpm --filter api dev
pnpm --filter api build
pnpm --filter api lint
pnpm --filter api test
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Scripts Disponibles

- `pnpm dev` - Ejecutar ambos servicios en modo desarrollo
- `pnpm build` - Construir todos los proyectos
- `pnpm lint` - Ejecutar linting en todos los proyectos
- `pnpm test` - Ejecutar tests en todos los proyectos
- `pnpm clean` - Limpiar archivos generados

## Configuración

### Variables de Entorno

Copia el archivo de ejemplo en el backend:
```bash
cp apps/api/env.example apps/api/.env
```

### Caché de Turborepo

Turborepo utiliza caché inteligente basado en archivos para optimizar las construcciones. Los archivos de dependencias están configurados en `turbo.json` para invalidar la caché cuando sea necesario.
