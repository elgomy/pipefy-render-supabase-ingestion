#!/usr/bin/env python3
"""
Script para verificar específicamente el card 1130856215
"""

from supabase import create_client, Client
from datetime import datetime

SUPABASE_URL = 'https://aguoqgqbdbyipztgrmbd.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 VERIFICACIÓN ESPECÍFICA DEL CARD 1130856215")
print("=" * 60)

# Buscar documentos para este card
response = supabase.table('documents').select('*').eq('case_id', '1130856215').execute()
print(f"📄 Documentos encontrados: {len(response.data)}")

if response.data:
    for doc in response.data:
        print(f"  - Nombre: {doc['name']}")
        print(f"    ID: {doc['id']}")
        print(f"    Creado: {doc['created_at']}")
        print(f"    URL: {doc['file_url'][:80]}...")
        print()
else:
    print("❌ No se encontraron documentos para este card")

# Buscar todos los documentos recientes (últimas 24 horas)
print("\n📅 DOCUMENTOS RECIENTES (últimas 24 horas)")
print("-" * 60)
response_recent = supabase.table('documents').select('*').gte('created_at', '2025-01-28T00:00:00').execute()
print(f"Total documentos recientes: {len(response_recent.data)}")

for doc in response_recent.data:
    print(f"  - Card: {doc['case_id']} | Nombre: {doc['name']} | Creado: {doc['created_at']}")

# Verificar si hay algún error en el procesamiento
print(f"\n🔍 ANÁLISIS DEL PROBLEMA")
print("-" * 60)
print("Posibles causas:")
print("1. Error en la descarga del documento desde Pipefy")
print("2. Error en la subida a Supabase Storage")
print("3. Error en el guardado de metadatos en la base de datos")
print("4. El documento ya existe y el UPSERT no está funcionando correctamente")
print("5. Problema con el formato de la URL del documento") 