#!/usr/bin/env python3
"""
Script para verificar si el card 1131156124 ahora tiene documentos procesados
"""

from supabase import create_client, Client
from datetime import datetime, timedelta

# Configuración
SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"

CARDS_TO_CHECK = ["1130856215", "1131156124"]

def check_card_documents(card_id):
    """Verifica documentos de un card específico"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Buscar todos los documentos de este card
        response = supabase.table("documents").select("*").eq("case_id", card_id).order("created_at", desc=True).execute()
        documents = response.data
        
        return {
            "card_id": card_id,
            "total_documents": len(documents),
            "documents": documents
        }
    except Exception as e:
        return {"error": str(e)}

def check_recent_activity():
    """Verifica actividad reciente en los últimos 10 minutos"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Buscar documentos procesados en los últimos 10 minutos
        ten_minutes_ago = (datetime.now() - timedelta(minutes=10)).isoformat()
        
        response = supabase.table("documents").select("*").gte("created_at", ten_minutes_ago).order("created_at", desc=True).execute()
        recent_docs = response.data
        
        return recent_docs
    except Exception as e:
        return []

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN DE PROCESAMIENTO DE CARDS")
    print("=" * 80)
    
    # Verificar cada card
    for card_id in CARDS_TO_CHECK:
        print(f"\n📋 CARD {card_id}:")
        print("-" * 40)
        
        result = check_card_documents(card_id)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"📊 Total documentos: {result['total_documents']}")
            
            if result['documents']:
                print("📄 Documentos encontrados:")
                for i, doc in enumerate(result['documents'], 1):
                    print(f"   {i}. {doc['name']}")
                    print(f"      Creado: {doc['created_at']}")
                    print(f"      Tamaño: {doc.get('size', 'N/A')} bytes")
                    print(f"      Tipo: {doc.get('content_type', 'N/A')}")
                    print(f"      URL: {doc.get('storage_path', 'N/A')}")
            else:
                print("📄 No hay documentos procesados para este card")
    
    # Verificar actividad reciente
    print(f"\n⏰ ACTIVIDAD RECIENTE (últimos 10 minutos):")
    print("-" * 50)
    
    recent_docs = check_recent_activity()
    
    if recent_docs:
        print(f"📊 Documentos procesados recientemente: {len(recent_docs)}")
        for doc in recent_docs:
            print(f"   - Card {doc['case_id']}: {doc['name']} ({doc['created_at']})")
    else:
        print("📊 No hay documentos procesados recientemente")
    
    print(f"\n💡 ANÁLISIS:")
    print("=" * 80)
    
    # Verificar si el card problemático ahora tiene documentos
    card_1131156124_result = check_card_documents("1131156124")
    
    if "error" not in card_1131156124_result:
        if card_1131156124_result['total_documents'] > 0:
            print("✅ ¡ÉXITO! El card 1131156124 ahora SÍ tiene documentos procesados")
            print("   Esto confirma que el webhook está funcionando correctamente")
            print("   El problema era que no había sido procesado antes")
        else:
            print("❌ El card 1131156124 aún no tiene documentos procesados")
            print("   Esto sugiere que hay un problema real con este card")
    
    print(f"\n🎯 CONCLUSIÓN:")
    print("Si el card 1131156124 ahora tiene documentos, significa que:")
    print("1. El webhook SÍ funciona para este card")
    print("2. El problema era que no había sido procesado antes")
    print("3. Ambos cards funcionan correctamente")
    print("4. La diferencia inicial era solo el estado de procesamiento") 