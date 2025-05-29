# Módulo de Ingestión Pipefy-Supabase

Este servicio backend implementado en Python/FastAPI actúa como un puente entre Pipefy y Supabase, permitiendo la ingestión automática de documentos para análisis posterior.

## Funcionalidades

- Recibe notificaciones de Pipefy vía webhooks cuando un card se mueve a una fase específica
- Obtiene documentos adjuntos del card a través de la API GraphQL de Pipefy
- Almacena los documentos en Supabase Storage con una estructura organizada
- Registra metadatos en Supabase Database
- Clasifica automáticamente los documentos según su nombre/contenido
- Simula el análisis de documentos registrando toda la información en logs detallados

## Requisitos

- Python 3.9+
- Cuenta en Pipefy con acceso a API
- Proyecto en Supabase (con Storage y Database)
- Cuenta en Render para despliegue

## Configuración

1. Clone este repositorio:
```
git clone <repository-url>
cd <repository-directory>
```

2. Instale las dependencias:
```
pip install -r requirements.txt
```

3. Configure las variables de entorno copiando el archivo de ejemplo:
```
cp example.env .env
```
- Edite `.env` con sus credenciales de Pipefy y Supabase

4. Estructura de Supabase Database requerida:
   - Tabla `documents` con los campos:
     - `case_id` (texto)
     - `name` (texto)
     - `document_tag` (texto)
     - `file_url` (texto)
     - `created_at` (timestamp con zona horaria)
     - `updated_at` (timestamp con zona horaria)
   - Tabla `app_configs` con los campos:
     - `config_name` (texto)
     - `content` (texto, opcional)
     - `file_url` (texto)
     - `created_at` (timestamp con zona horaria)
     - `updated_at` (timestamp con zona horaria)

5. Configure los buckets en Supabase Storage:
   - Bucket `documents` (o el que defina en .env) para almacenar documentos procesados
   - Bucket `checklist` para almacenar el archivo de checklist de criterios

6. Configure el checklist en la tabla app_configs:
   - Suba su archivo de checklist al bucket `checklist`
   - Obtenga la URL pública del archivo
   - Inserte/actualice el registro en `app_configs` con:
     - `config_name`: "checklist_cadastro_pj"
     - `file_url`: URL pública del archivo checklist

## Desarrollo Local

Para ejecutar el servicio localmente:

```
uvicorn scripts.fastAPI:app --reload
```

Para pruebas de webhook locales, use ngrok:

```
ngrok http 8000
```

## Despliegue en Render

1. Agregue su repositorio a Render
2. Seleccione la opción "Blueprint" y use el archivo `render.yaml`
3. Configure las variables de entorno en el dashboard de Render
4. Despliegue la aplicación

## Configuración en Pipefy

1. Vaya a la configuración de su Pipeline en Pipefy
2. Configure un webhook para el evento "card.move"
3. Establezca la URL del webhook al endpoint `/webhook/pipefy` de su aplicación desplegada
4. Si configuró un secreto, agregue este valor en la configuración del webhook

## Estructura de Archivos

- `scripts/fastAPI.py` - Aplicación principal FastAPI
- `requirements.txt` - Dependencias del proyecto
- `render.yaml` - Configuración para despliegue en Render
- `example.env` - Ejemplo de variables de entorno
- `tests/` - Scripts de prueba para desarrollo local

## Análisis de Documentos

El sistema actualmente simula el análisis de documentos registrando toda la información en logs detallados. Esto incluye:

- ID del caso
- Lista completa de documentos procesados
- Clasificación automática de cada documento
- URLs de almacenamiento en Supabase
- Contenido del checklist de configuración
- Timestamp del procesamiento

Los logs pueden ser monitoreados en tiempo real en Render para seguimiento del procesamiento. 