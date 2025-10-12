# Dashboard Components

Esta carpeta contiene componentes reutilizables para las páginas del dashboard.

## Componentes Disponibles

### 1. **FileTable** (`FileTable.tsx`)
Tabla genérica para mostrar archivos con selección múltiple.

**Props:**
- `files`: Array de archivos (BaseFile)
- `columns`: Configuración de columnas
- `selectedKeys`: Keys seleccionadas
- `onSelectionChange`: Callback para cambios de selección
- `loading`: Estado de carga
- `emptyMessage`: Mensaje cuando no hay archivos
- `renderCell`: Función custom para renderizar celdas
- `primaryAction`: Acción principal (botón en cada fila)
- `rowActions`: Acciones adicionales (menú dropdown)

**Ejemplo:**
```tsx
<FileTable
  files={videos}
  columns={[
    { key: "name", label: "NAME" },
    { key: "size", label: "SIZE" },
    { key: "modified", label: "MODIFIED" },
    { key: "actions", label: "ACTIONS" }
  ]}
  selectedKeys={selectedKeys}
  onSelectionChange={setSelectedKeys}
  primaryAction={{
    label: "Preview",
    onClick: handlePreview
  }}
  rowActions={[
    {
      label: "Delete",
      onClick: handleDelete,
      color: "danger"
    }
  ]}
/>
```

### 2. **FolderSidebar** (`FolderSidebar.tsx`)
Sidebar mejorado para gestión de carpetas con funcionalidades de crear, editar y eliminar.

**Features:**
- Vista de todas las carpetas con contador de archivos
- Opción "All Files" para ver todos los archivos
- Crear carpetas con modal
- Renombrar carpetas (hover para ver opciones)
- Eliminar carpetas con confirmación
- Iconos de Lucide para mejor UX
- Animaciones sutiles en hover

**Props:**
- `folders`: Array de carpetas
- `selectedFolder`: Carpeta seleccionada (null para "All")
- `onSelectFolder`: Callback para selección
- `onCreateFolder`: Callback para crear carpeta
- `onRenameFolder`: Callback para renombrar carpeta
- `onDeleteFolder`: Callback para eliminar carpeta
- `showAllOption`: Mostrar opción "All Files"
- `totalCount`: Contador total de archivos
- `title`: Título del sidebar

**Ejemplo:**
```tsx
<FolderSidebar
  folders={folders}
  selectedFolder={selectedFolder}
  onSelectFolder={setSelectedFolder}
  onCreateFolder={handleCreateFolder}
  onRenameFolder={handleRenameFolder}
  onDeleteFolder={handleDeleteFolder}
  totalCount={getTotalCount()}
  title="Video Folders"
/>
```

### 3. **BulkActions** (`BulkActions.tsx`)
Barra de acciones para operaciones masivas con archivos seleccionados.

**Props:**
- `selectedCount`: Número de items seleccionados
- `onClear`: Callback para limpiar selección
- `actions`: Array de acciones disponibles

**Ejemplo:**
```tsx
<BulkActions
  selectedCount={getSelectedCount()}
  onClear={() => setSelectedKeys(new Set())}
  actions={[
    {
      label: "Download Selected",
      onClick: handleBulkDownload,
      color: "primary"
    },
    {
      label: "Delete Selected",
      onClick: handleBulkDelete,
      color: "danger"
    }
  ]}
/>
```

## Utilidades Compartidas

### `/lib/types.ts`
Tipos TypeScript compartidos:
- `BaseFile`: Tipo base para archivos
- `VideoFile`, `AudioFile`, `CSVFile`: Tipos específicos
- `Folder`: Tipo para carpetas
- `FileType`: Tipo union para tipos de archivos

### `/lib/utils.ts`
Funciones de utilidad:
- `formatFileSize(bytes)`: Formatea tamaño de archivos
- `formatDate(dateStr)`: Formatea fechas con formato relativo
- `API_URL`: URL base de la API
- `delay(ms)`: Helper para delays con async/await

## Mejores Prácticas

### 1. **Reutilización de Componentes**
- Usa `FileTable` para cualquier listado de archivos
- Usa `FolderSidebar` para navegación por carpetas
- Usa `BulkActions` para operaciones masivas

### 2. **Personalización**
- Usa `renderCell` en FileTable para columnas custom
- Pasa iconos de Lucide React a las acciones
- Personaliza colores con props `color`

### 3. **Tipos**
- Importa tipos desde `/lib/types`
- Extiende `BaseFile` para tipos específicos
- Usa type assertions cuando sea necesario

### 4. **Estado**
- Maneja `selectedKeys` como `Selection` type
- Usa `null` para "All Files" en FolderSidebar
- Mantén el estado de carga separado

## Ejemplo de Implementación

Ver `app/dashboard/videos/page.tsx` para un ejemplo completo de cómo usar todos los componentes juntos.

## Iconos

Los componentes usan **Iconsax React** para iconos consistentes:
```tsx
import { Folder2, Edit, Trash, FolderAdd } from "iconsax-reactjs";
```

## Estilos

Todos los componentes usan HeroUI y Tailwind CSS:
- Borders: `border-default-200`
- Backgrounds: `bg-default-100`
- Radius: `rounded-xl` para cards, `rounded-lg` para elementos
- Spacing consistente con gap-2, gap-3, gap-6

## TODOs

- [ ] Implementar API para rename folder
- [ ] Implementar API para delete folder
- [ ] Agregar drag & drop para FileTable
- [ ] Agregar filtros y búsqueda a FileTable
- [ ] Agregar sorting a FileTable
