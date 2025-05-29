# Configuración de Supabase Storage

Este documento explica cómo configurar el bucket de almacenamiento necesario en Supabase Storage para el sistema de ingestión de documentos.

## Creación del Bucket

1. Inicia sesión en el panel de control de Supabase
2. Ve a la sección "Storage" en el menú lateral
3. Haz clic en "Crear nuevo bucket"
4. Introduce los siguientes datos:
   - **Nombre del bucket**: `documents` (o el nombre que hayas configurado en las variables de entorno)
   - **Tipo de acceso público**: Desactivado (para control de acceso)
   - **CORS**: Configuración por defecto es adecuada

## Configuración de Políticas de Acceso

Para permitir que nuestra aplicación suba, lea y administre archivos, necesitamos configurar las políticas de acceso adecuadas:

### 1. Política para Subir Archivos

1. En el bucket recién creado, ve a "Políticas"
2. Haz clic en "Crear política"
3. Selecciona "Personalizado" y configura:
   - **Nombre**: `documents_upload_policy`
   - **Permitido para**: `INSERT`
   - **Roles**: `authenticated`
   - **Condición SQL**: `true` (o usa una condición más restrictiva según tus necesidades)

### 2. Política para Leer Archivos

1. Haz clic en "Crear política" nuevamente
2. Configura:
   - **Nombre**: `documents_read_policy`
   - **Permitido para**: `SELECT`
   - **Roles**: `authenticated, anon` (si quieres que los archivos sean accesibles públicamente)
   - **Condición SQL**: `true`

### 3. Política para Actualizar y Eliminar (Opcional)

1. Crea políticas adicionales para `UPDATE` y `DELETE` si es necesario para tu caso de uso

## Estructura de Carpetas Recomendada

La aplicación usará la siguiente estructura de carpetas dentro del bucket:

```
documents/
├── casos_clientes/
│   ├── [case_id_1]/
│   │   ├── documento1.pdf
│   │   ├── documento2.docx
│   │   └── ...
│   ├── [case_id_2]/
│   │   └── ...
│   └── ...
└── ...
```

## Tokens y Permisos

Asegúrate de que el `SUPABASE_SERVICE_KEY` que uses tenga permisos completos sobre el bucket de Storage. El token de servicio se encuentra en la sección "Configuración del proyecto" > "API" en el panel de control de Supabase. 