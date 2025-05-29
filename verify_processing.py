#!/usr/bin/env python3
"""
Script para verificar si el documento del card se procesó correctamente
"""

import requests
import time
from supabase import create_client, Client

# Configuración Supabase
SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"

CARD_ID = "1131156124"

def check_documents_in_supabase():
    """Verifica si hay documentos del card en Supabase"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Buscar documentos del card específico
        response = supabase.table("documents").select("*").eq("case_id", CARD_ID).execute()
        
        documents = response.data
        print(f"📊 Documentos encontrados para el card {CARD_ID}: {len(documents)}")
        
        if documents:
            for doc in documents:
                print(f"   - {doc['name']}")
                print(f"     URL: {doc['file_url']}")
                print(f"     Creado: {doc['created_at']}")
                print()
        
        return len(documents)
        
    except Exception as e:
        print(f"❌ Error al consultar Supabase: {e}")
        return 0

def check_storage_bucket():
    """Verifica archivos en el bucket de storage"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Listar archivos en el bucket para este case_id
        response = supabase.storage.from_("documents").list(CARD_ID)
        
        files = response if isinstance(response, list) else []
        print(f"📁 Archivos en storage para {CARD_ID}: {len(files)}")
        
        for file in files:
            print(f"   - {file.get('name', 'Sin nombre')}")
            print(f"     Tamaño: {file.get('metadata', {}).get('size', 'Desconocido')} bytes")
        
        return len(files)
        
    except Exception as e:
        print(f"❌ Error al consultar storage: {e}")
        return 0

def test_webhook_endpoint():
    """Prueba el endpoint del webhook"""
    try:
        response = requests.get("https://pipefy-render-supabase-ingestion.onrender.com/health", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("✅ Servicio en Render está activo:")
        print(f"   Status: {data.get('status')}")
        print(f"   Supabase configurado: {data.get('supabase_configured')}")
        print(f"   Pipefy configurado: {data.get('pipefy_configured')}")
        
        return True
    except Exception as e:
        print(f"❌ Error al conectar con Render: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando procesamiento del card 1131156124...")
    print("=" * 60)
    
    # Verificar servicio
    print("\n1️⃣ Verificando servicio en Render...")
    service_ok = test_webhook_endpoint()
    
    # Verificar documentos en base de datos
    print("\n2️⃣ Verificando documentos en base de datos...")
    doc_count = check_documents_in_supabase()
    
    # Verificar archivos en storage
    print("\n3️⃣ Verificando archivos en storage...")
    file_count = check_storage_bucket()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print(f"   Servicio activo: {'✅' if service_ok else '❌'}")
    print(f"   Documentos en DB: {doc_count}")
    print(f"   Archivos en storage: {file_count}")
    
    if doc_count == 0 and file_count == 0:
        print("\n⚠️  No se encontraron documentos procesados.")
        print("   Esto puede indicar que:")
        print("   - El webhook no se activó")
        print("   - Hubo un error en el procesamiento")
        print("   - El documento no se pudo descargar")
        print("\n💡 Revisa los logs de Render para más detalles.")
    else:
        print(f"\n🎉 ¡Documentos procesados exitosamente!") 