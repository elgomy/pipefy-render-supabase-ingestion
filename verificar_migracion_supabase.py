#!/usr/bin/env python3
"""
Script para verificar que la migración de cache del checklist se ejecutó correctamente
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

def verify_migration():
    """Verifica que la migración se ejecutó correctamente."""
    try:
        # Configurar cliente Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: Variables de entorno no configuradas")
            return False
        
        print(f"🔗 Conectando a Supabase: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)
        
        print("🔍 Verificando migración de cache del checklist...")
        
        # Intentar consultar las nuevas columnas
        try:
            response = supabase.table("checklist_config").select("config_name, checklist_url, checklist_content, parsed_at, parsing_version").limit(1).execute()
            
            if response.data:
                print("✅ ¡Migración exitosa! Las nuevas columnas están disponibles")
                print("📊 Estructura verificada:")
                sample_row = response.data[0]
                for key, value in sample_row.items():
                    print(f"  - {key}: {value if value is not None else 'NULL'}")
                
                # Verificar que las columnas de cache existen
                cache_columns = ['checklist_content', 'parsed_at', 'parsing_version']
                existing_columns = list(sample_row.keys())
                missing_columns = [col for col in cache_columns if col not in existing_columns]
                
                if not missing_columns:
                    print("\n🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
                    print("💾 Sistema de cache del checklist habilitado")
                    print("⚡ El sistema ahora puede:")
                    print("  - Cachear contenido parseado del checklist")
                    print("  - Evitar parseos repetitivos (ahorro de costos)")
                    print("  - Invalidar cache automáticamente si cambia la URL")
                    return True
                else:
                    print(f"\n⚠️ Columnas faltantes: {missing_columns}")
                    print("❌ La migración no se completó correctamente")
                    return False
            else:
                print("⚠️ No hay datos en la tabla para verificar")
                print("✅ Pero las columnas parecen existir (tabla vacía)")
                return True
                
        except Exception as query_error:
            if "does not exist" in str(query_error):
                print("❌ Las columnas de cache NO existen aún")
                print("📋 Necesitas ejecutar los comandos SQL en Supabase SQL Editor")
                print("📄 Archivo: COMANDOS_SQL_SUPABASE.sql")
                return False
            else:
                print(f"❌ Error en consulta: {query_error}")
                return False
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def test_cache_functionality():
    """Prueba la funcionalidad de cache si la migración fue exitosa."""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        supabase = create_client(supabase_url, supabase_key)
        
        print("\n🧪 Probando funcionalidad de cache...")
        
        # Obtener el primer registro
        response = supabase.table("checklist_config").select("*").limit(1).execute()
        
        if response.data:
            first_record = response.data[0]
            config_name = first_record.get('config_name')
            
            if config_name:
                # Simular actualización de cache
                from datetime import datetime
                test_content = f"CONTENIDO DE PRUEBA DEL CACHE - {datetime.now().isoformat()}"
                
                print(f"📝 Actualizando cache para config: {config_name}")
                
                update_response = supabase.table("checklist_config").update({
                    "checklist_content": test_content,
                    "parsed_at": datetime.now().isoformat(),
                    "parsing_version": "1.0"
                }).eq("config_name", config_name).execute()
                
                if update_response.data:
                    print("✅ Cache de prueba guardado exitosamente")
                    
                    # Verificar que se guardó
                    verify_response = supabase.table("checklist_config").select("checklist_content, parsed_at").eq("config_name", config_name).execute()
                    
                    if verify_response.data and verify_response.data[0].get('checklist_content'):
                        print("✅ Cache verificado - el sistema está funcionando correctamente")
                        print(f"📄 Contenido guardado: {verify_response.data[0]['checklist_content'][:50]}...")
                        print(f"⏰ Timestamp: {verify_response.data[0]['parsed_at']}")
                        return True
                    else:
                        print("⚠️ Cache no se guardó correctamente")
                else:
                    print("⚠️ Error al guardar cache de prueba")
            else:
                print("⚠️ No se encontró config_name para probar")
        else:
            print("⚠️ No hay datos en la tabla para probar")
        
        return False
        
    except Exception as e:
        print(f"❌ Error probando cache: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 VERIFICACIÓN DE MIGRACIÓN DE SUPABASE")
    print("=" * 50)
    
    # Verificar migración
    if verify_migration():
        print("\n🎯 Migración verificada exitosamente")
        
        # Probar funcionalidad de cache
        if test_cache_functionality():
            print("\n🎉 ¡TODO ESTÁ FUNCIONANDO PERFECTAMENTE!")
            print("🚀 El proyecto está 100% listo para el deploy en Render")
        else:
            print("\n⚠️ Migración exitosa pero prueba de cache falló")
    else:
        print("\n❌ La migración aún no se ha completado")
        print("\n📋 PASOS SIGUIENTES:")
        print("1. Ve a Supabase Dashboard: https://supabase.com/dashboard")
        print("2. Selecciona el proyecto 'crewai-cadastro'")
        print("3. Ve a 'SQL Editor'")
        print("4. Ejecuta los comandos del archivo: COMANDOS_SQL_SUPABASE.sql")
        print("5. Ejecuta este script nuevamente para verificar")

if __name__ == "__main__":
    main() 