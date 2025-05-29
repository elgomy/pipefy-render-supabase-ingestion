#!/usr/bin/env python3
"""
Script para probar el flujo real con el webhook de Pipefy
"""

import requests
import json
import time

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
CARD_ID = "1131156124"
TARGET_PHASE_ID = "338000020"  # Agent - Open Banking
TEMP_PHASE_ID = "338000019"    # Fase temporal para mover primero

def move_card_to_phase(card_id, phase_id, phase_name=""):
    """Mueve un card a una fase específica"""
    mutation = """
    mutation MoveCard($cardId: ID!, $phaseId: ID!) {
        moveCardToPhase(input: {
            card_id: $cardId
            destination_phase_id: $phaseId
        }) {
            card {
                id
                title
                current_phase {
                    id
                    name
                }
            }
        }
    }
    """
    
    variables = {
        "cardId": card_id,
        "phaseId": phase_id
    }
    
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    try:
        response = requests.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print(f"❌ Error al mover card: {data['errors']}")
            return False
        
        card_data = data.get("data", {}).get("moveCardToPhase", {}).get("card", {})
        if card_data:
            print(f"✅ Card movido a {phase_name}:")
            print(f"   Fase actual: {card_data.get('current_phase', {}).get('name')}")
            return True
        
        return False
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")
        return False

def count_documents_in_db():
    """Cuenta documentos en la base de datos"""
    try:
        from supabase import create_client, Client
        
        SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("documents").select("*").eq("case_id", CARD_ID).execute()
        
        return len(response.data)
    except Exception as e:
        print(f"❌ Error al consultar DB: {e}")
        return 0

if __name__ == "__main__":
    print("🧪 Probando flujo real con webhook de Pipefy...")
    print(f"   Card ID: {CARD_ID}")
    print()
    
    # Contar documentos antes
    docs_before = count_documents_in_db()
    print(f"📊 Documentos en DB antes: {docs_before}")
    
    # Paso 1: Mover a fase temporal
    print("\n🔄 Paso 1: Moviendo card a fase temporal...")
    if not move_card_to_phase(CARD_ID, TEMP_PHASE_ID, "fase temporal"):
        print("💥 Error al mover a fase temporal")
        exit(1)
    
    time.sleep(3)
    
    # Paso 2: Mover a fase objetivo (esto debería activar el webhook)
    print("\n🚀 Paso 2: Moviendo card a 'Agent - Open Banking' (activará webhook)...")
    if not move_card_to_phase(CARD_ID, TARGET_PHASE_ID, "Agent - Open Banking"):
        print("💥 Error al mover a fase objetivo")
        exit(1)
    
    # Esperar procesamiento
    print("\n⏳ Esperando 15 segundos para que el webhook se procese...")
    time.sleep(15)
    
    # Contar documentos después
    docs_after = count_documents_in_db()
    print(f"\n📊 Documentos en DB después: {docs_after}")
    
    if docs_after > docs_before:
        print(f"🎉 ¡Éxito! Se procesaron {docs_after - docs_before} documentos nuevos")
        print("✅ El webhook real de Pipefy está funcionando correctamente")
    else:
        print("⚠️  No se detectaron documentos nuevos")
        print("   Esto puede ser normal si el documento ya fue procesado anteriormente")
    
    print("\n📝 Para más detalles:")
    print("1. Revisa los logs de Render: https://dashboard.render.com/web/srv-d0rm9cre5dus73ahn2n0/logs")
    print("2. Ejecuta 'python3 verify_processing.py' para ver todos los documentos")
    print("3. Revisa Supabase para ver los documentos almacenados") 