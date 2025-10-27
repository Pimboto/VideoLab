# 🧪 Testing Authentication

## Quick Test - Endpoint de Prueba

Vamos a crear un endpoint simple para probar que la autenticación funciona antes de modificar todos los endpoints existentes.

---

## 1. Crear Endpoint de Prueba

Crea un nuevo archivo: `apps/api/routers/auth.py`

```python
"""
Authentication test routes
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from core.dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user information.

    This endpoint requires authentication.

    Returns:
        User information from database
    """
    return {
        "id": current_user["id"],
        "clerk_id": current_user["clerk_id"],
        "email": current_user["email"],
        "first_name": current_user.get("first_name"),
        "last_name": current_user.get("last_name"),
        "avatar_url": current_user.get("avatar_url"),
        "created_at": str(current_user["created_at"]),
    }


@router.get("/test-public")
async def test_public() -> Dict[str, str]:
    """
    Public endpoint - no authentication required.

    Anyone can access this endpoint.
    """
    return {"message": "This is a public endpoint"}


@router.get("/test-optional")
async def test_optional_auth(
    current_user: Dict[str, Any] | None = Depends(get_optional_user)
) -> Dict[str, Any]:
    """
    Optional authentication endpoint.

    Returns different responses for authenticated vs unauthenticated users.
    """
    if current_user:
        return {
            "authenticated": True,
            "message": f"Hello {current_user['email']}!",
            "user_id": current_user["id"],
        }
    else:
        return {
            "authenticated": False,
            "message": "Hello guest! Sign in for personalized experience.",
        }
```

---

## 2. Registrar el Router

Edita `apps/api/app.py` y agrega:

```python
from routers import files, folders, processing, auth  # ✅ Agregar auth

# Luego en el código donde registras los routers:
app.include_router(files.router, prefix=settings.api_prefix)
app.include_router(folders.router, prefix=settings.api_prefix)
app.include_router(processing.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)  # ✅ Agregar esta línea
```

---

## 3. Iniciar el Backend

```bash
cd apps/api
python app.py
```

Deberías ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 4. Iniciar el Frontend

```bash
cd apps/web
pnpm dev
```

Deberías ver:
```
  ▲ Next.js 15.3.1
  - Local:        http://localhost:3000
```

---

## 5. Probar con el Frontend

### A. Abrir el navegador

1. Ve a: http://localhost:3000
2. Deberías ser redirigido a `/sign-in`
3. Crea una cuenta de prueba (o usa Sign in si ya tienes una)

### B. Obtener el token de Clerk

1. Después de sign in, abre DevTools (F12)
2. Ve a la pestaña **Application** (o **Storage** en Firefox)
3. En la sección **Cookies**, busca cookies que empiecen con `__clerk`
4. O ve a **Console** y escribe:
   ```javascript
   // Get Clerk token
   window.__clerk_loaded.then(() => {
     window.Clerk.session.getToken().then(token => console.log(token))
   })
   ```

O más fácil, crea un botón en el frontend:

### C. Crear componente de test

Crea: `apps/web/app/dashboard/test-auth/page.tsx`

```typescript
"use client";

import { useAuth } from "@clerk/nextjs";
import { useState } from "react";
import { Button } from "@heroui/button";
import { Card, CardBody, CardHeader } from "@heroui/card";

export default function TestAuthPage() {
  const { getToken } = useAuth();
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testEndpoint = async (endpoint: string) => {
    setLoading(true);
    setResult(null);

    try {
      const token = await getToken();

      const response = await fetch(`http://localhost:8000/api/video-processor${endpoint}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();
      setResult({
        success: response.ok,
        status: response.status,
        data,
      });
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Test Authentication</h1>

      <div className="grid gap-4">
        {/* Test /auth/me */}
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Test: GET /auth/me</h2>
          </CardHeader>
          <CardBody>
            <p className="mb-4">
              This endpoint requires authentication and returns current user info.
            </p>
            <Button
              color="primary"
              onClick={() => testEndpoint("/auth/me")}
              isLoading={loading}
            >
              Test Authenticated Endpoint
            </Button>
          </CardBody>
        </Card>

        {/* Test /auth/test-public */}
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Test: GET /auth/test-public</h2>
          </CardHeader>
          <CardBody>
            <p className="mb-4">This endpoint is public (no authentication required).</p>
            <Button
              color="secondary"
              onClick={() => testEndpoint("/auth/test-public")}
              isLoading={loading}
            >
              Test Public Endpoint
            </Button>
          </CardBody>
        </Card>

        {/* Test /auth/test-optional */}
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Test: GET /auth/test-optional</h2>
          </CardHeader>
          <CardBody>
            <p className="mb-4">
              This endpoint works with or without authentication.
            </p>
            <Button
              color="success"
              onClick={() => testEndpoint("/auth/test-optional")}
              isLoading={loading}
            >
              Test Optional Auth Endpoint
            </Button>
          </CardBody>
        </Card>
      </div>

      {/* Results */}
      {result && (
        <Card className="mt-8">
          <CardHeader>
            <h2 className="text-xl font-semibold">
              Result {result.success ? "✅" : "❌"}
            </h2>
          </CardHeader>
          <CardBody>
            <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
```

---

## 6. Probar

1. Ve a: http://localhost:3000/dashboard/test-auth
2. Click en "Test Authenticated Endpoint"
3. Deberías ver tu información de usuario

**Resultado esperado:**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": "uuid-here",
    "clerk_id": "user_xxxxx",
    "email": "tu@email.com",
    "first_name": "Tu",
    "last_name": "Nombre",
    "created_at": "2025-01-27T..."
  }
}
```

---

## 7. Probar con cURL

### A. Sin token (debe fallar con 401)

```bash
curl -X GET http://localhost:8000/api/video-processor/auth/me
```

**Resultado esperado:**
```json
{
  "detail": "Invalid authorization header format. Expected 'Bearer <token>'"
}
```

### B. Con token (debe funcionar)

Primero obtén el token del frontend, luego:

```bash
curl -X GET http://localhost:8000/api/video-processor/auth/me \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

**Resultado esperado:**
```json
{
  "id": "uuid-here",
  "clerk_id": "user_xxxxx",
  "email": "tu@email.com",
  ...
}
```

---

## 8. Verificar en Supabase

1. Ve a Supabase Dashboard
2. Table Editor > users
3. Deberías ver tu usuario creado automáticamente con:
   - `clerk_id` - ID de Clerk
   - `email` - Tu email
   - `first_name`, `last_name` - Si los proporcionaste

---

## ✅ Checklist de Pruebas

- [ ] Backend inicia sin errores
- [ ] Frontend inicia sin errores
- [ ] Puedes hacer sign in
- [ ] `/auth/me` devuelve tu información de usuario
- [ ] `/auth/test-public` funciona sin token
- [ ] `/auth/test-optional` funciona con y sin token
- [ ] Usuario aparece en Supabase table `users`
- [ ] Recibir 401 cuando no envías token a `/auth/me`

---

## 🐛 Troubleshooting

### Error: "Failed to fetch Clerk JWKS"
- Verifica `CLERK_JWKS_URL` en `.env`
- Asegúrate de tener conexión a internet

### Error: "User not found in database"
- Verifica que las tablas de Supabase existan
- Verifica las credenciales de Supabase en `.env`

### Error: "Module not found: models.user"
- Verifica que `apps/api/models/__init__.py` existe
- Reinicia el servidor Python

### Error: Token expired
- Los tokens de Clerk expiran
- Refresh la página o haz sign out/sign in

---

**Si todos los tests pasan ✅, la autenticación está funcionando perfectamente!**

Ahora puedes aplicar el mismo patrón a todos los demás endpoints usando la guía en `ENDPOINT_PROTECTION_GUIDE.md`.
