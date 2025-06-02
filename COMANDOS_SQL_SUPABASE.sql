-- =====================================================
-- COMANDOS SQL PARA EJECUTAR EN SUPABASE SQL EDITOR
-- =====================================================
-- 
-- INSTRUCCIONES:
-- 1. Ve a tu Dashboard de Supabase: https://supabase.com/dashboard
-- 2. Selecciona el proyecto 'crewai-cadastro'
-- 3. Ve a 'SQL Editor' en el menú lateral
-- 4. Crea una nueva consulta
-- 5. Copia y pega TODOS los comandos de abajo
-- 6. Ejecuta el script completo
-- 7. Verifica que no hay errores
-- =====================================================

-- PASO 1: Agregar columnas de cache del checklist
ALTER TABLE checklist_config 
ADD COLUMN IF NOT EXISTS checklist_content TEXT,
ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS parsing_version VARCHAR(10) DEFAULT '1.0';

-- PASO 2: Crear índice para optimizar búsquedas por URL
CREATE INDEX IF NOT EXISTS idx_checklist_config_url ON checklist_config(checklist_url);

-- PASO 3: Agregar comentarios descriptivos a las columnas
COMMENT ON COLUMN checklist_config.checklist_content IS 'Contenido del checklist parseado con LlamaParse (cache)';
COMMENT ON COLUMN checklist_config.parsed_at IS 'Timestamp de cuando se parseó el checklist por última vez';
COMMENT ON COLUMN checklist_config.parsing_version IS 'Versión del parser utilizado para invalidar cache si es necesario';

-- PASO 4: Crear función para limpiar cache automáticamente cuando cambia la URL
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

-- PASO 5: Crear trigger para ejecutar la función automáticamente
DROP TRIGGER IF EXISTS trigger_clear_checklist_cache ON checklist_config;
CREATE TRIGGER trigger_clear_checklist_cache
    BEFORE UPDATE ON checklist_config
    FOR EACH ROW
    EXECUTE FUNCTION clear_checklist_cache();

-- PASO 6: Verificar que todo se creó correctamente
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'checklist_config' 
ORDER BY ordinal_position;

-- =====================================================
-- FIN DE LOS COMANDOS SQL
-- =====================================================
--
-- DESPUÉS DE EJECUTAR:
-- - Deberías ver las nuevas columnas en el resultado del SELECT final
-- - Las columnas checklist_content, parsed_at y parsing_version deben aparecer
-- - El sistema de cache estará habilitado y listo para usar
-- ===================================================== 