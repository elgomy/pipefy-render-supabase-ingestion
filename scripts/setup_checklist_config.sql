-- Script para configurar el checklist en la tabla app_configs
-- Ejecutar en el SQL Editor de Supabase después de subir el archivo checklist.pdf al bucket 'checklist'

-- Paso 1: Verificar que la tabla app_configs tiene la columna file_url
-- Si no la tiene, ejecutar primero: ALTER TABLE public.app_configs ADD COLUMN IF NOT EXISTS file_url TEXT;

-- Paso 2: Insertar o actualizar la configuración del checklist
-- IMPORTANTE: Reemplazar la URL con la URL real de tu archivo checklist.pdf
INSERT INTO public.app_configs (config_name, content, file_url)
VALUES (
    'checklist_cadastro_pj',
    '# CHECK LIST PARA HABILITAÇÃO DE CONTA PJ
1. Verificar CNPJ ativo na Receita Federal
2. Verificar Contrato Social registrado
3. Verificar Alterações Contratuais
4. Verificar documentos de identidade dos sócios
5. Verificar comprovantes de endereço dos sócios
6. Verificar documentação de faturamento dos últimos 12 meses
7. Verificar certidões negativas de débitos
8. Verificar procurações de representação (se aplicável)',
    'https://aguoqqgbdbypztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf'
) ON CONFLICT (config_name) DO UPDATE
SET 
    content = EXCLUDED.content,
    file_url = EXCLUDED.file_url,
    updated_at = NOW();

-- Paso 3: Verificar que la configuración se guardó correctamente
SELECT * FROM public.app_configs WHERE config_name = 'checklist_cadastro_pj';

-- Nota: Para obtener la URL correcta de tu archivo checklist.pdf:
-- 1. Ve a Storage > checklist en tu panel de Supabase
-- 2. Haz clic en el archivo checklist.pdf
-- 3. Copia la URL pública que aparece
-- 4. Reemplaza la URL en este script y ejecuta nuevamente 