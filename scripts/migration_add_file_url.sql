-- Migración para agregar el campo file_url a la tabla app_configs
-- Ejecutar este script en el SQL Editor de Supabase

-- Agregar la columna file_url si no existe
ALTER TABLE public.app_configs 
ADD COLUMN IF NOT EXISTS file_url TEXT;

-- Actualizar el registro existente con la URL del checklist
-- Reemplaza la URL con la URL real de tu bucket checklist
UPDATE public.app_configs 
SET file_url = 'https://aguoqqgbdbypztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf'
WHERE config_name = 'checklist_cadastro_pj_v1';

-- Si necesitas cambiar el nombre del config_name también:
UPDATE public.app_configs 
SET config_name = 'checklist_cadastro_pj'
WHERE config_name = 'checklist_cadastro_pj_v1';

-- Verificar los cambios
SELECT * FROM public.app_configs; 