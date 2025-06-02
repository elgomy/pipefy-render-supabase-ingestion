-- Script para agregar columnas de cache del checklist parseado
-- Esto optimiza el rendimiento evitando parsear el mismo checklist múltiples veces

-- Agregar columnas para cache del contenido parseado
ALTER TABLE checklist_config 
ADD COLUMN IF NOT EXISTS checklist_content TEXT,
ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS parsing_version VARCHAR(10) DEFAULT '1.0';

-- Crear índice para búsquedas rápidas por URL
CREATE INDEX IF NOT EXISTS idx_checklist_config_url ON checklist_config(checklist_url);

-- Comentarios para documentar las nuevas columnas
COMMENT ON COLUMN checklist_config.checklist_content IS 'Contenido del checklist parseado con LlamaParse (cache)';
COMMENT ON COLUMN checklist_config.parsed_at IS 'Timestamp de cuando se parseó el checklist por última vez';
COMMENT ON COLUMN checklist_config.parsing_version IS 'Versión del parser utilizado para invalidar cache si es necesario';

-- Función para limpiar cache cuando se actualiza la URL del checklist
CREATE OR REPLACE FUNCTION clear_checklist_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Si la URL del checklist cambió, limpiar el cache
    IF OLD.checklist_url IS DISTINCT FROM NEW.checklist_url THEN
        NEW.checklist_content := NULL;
        NEW.parsed_at := NULL;
        NEW.parsing_version := '1.0';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para limpiar automáticamente el cache cuando cambia la URL
DROP TRIGGER IF EXISTS trigger_clear_checklist_cache ON checklist_config;
CREATE TRIGGER trigger_clear_checklist_cache
    BEFORE UPDATE ON checklist_config
    FOR EACH ROW
    EXECUTE FUNCTION clear_checklist_cache();

-- Verificar la estructura actualizada
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'checklist_config' 
ORDER BY ordinal_position; 