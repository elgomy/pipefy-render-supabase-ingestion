-- Este script inicializa las tablas necesarias en Supabase Database
-- para el funcionamiento del sistema de ingestión de documentos

-- Tabla para almacenar metadatos de documentos
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL,
    name TEXT NOT NULL,
    document_tag TEXT NOT NULL,
    file_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice para búsqueda rápida por case_id
CREATE INDEX IF NOT EXISTS idx_documents_case_id ON public.documents (case_id);

-- Restricción de unicidad para evitar duplicados del mismo documento para un caso
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_case_document ON public.documents (case_id, name);

-- Tabla para configuraciones de la aplicación
CREATE TABLE IF NOT EXISTS public.app_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_name TEXT NOT NULL UNIQUE,
    content TEXT,
    file_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insertar configuración predeterminada para el checklist
-- Nota: Actualizar la file_url con la URL real de tu bucket checklist
INSERT INTO public.app_configs (config_name, content, file_url)
VALUES (
    'checklist_cadastro_pj',
    '# CHECK LIST PARA HABILITAÇÃO DE CONTA PJ
1. Verificar CNPJ activo en Receita Federal
2. Verificar Contrato Social registrado
3. Verificar Alteraciones Contractuales
4. Verificar documentos de identidad de los socios
5. Verificar comprobantes de domicilio de los socios
6. Verificar documentación de facturación de los últimos 12 meses
7. Verificar certificados negativos de deudas
8. Verificar poderes de representación (si aplica)',
    'https://aguoqqgbdbypztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf'
) ON CONFLICT (config_name) DO UPDATE
SET content = EXCLUDED.content, file_url = EXCLUDED.file_url, updated_at = NOW();

-- Función y trigger para actualizar 'updated_at' automáticamente
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_modtime
BEFORE UPDATE ON public.documents
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER update_app_configs_modtime
BEFORE UPDATE ON public.app_configs
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column(); 