#!/usr/bin/env python3
"""
Script para probar el flujo completo con reintentos hasta que el servicio esté listo
"""

import requests
import json
import time

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
PIPE_ID = "306294445"
TARGET_PHASE_ID = "338000020"  # Agent - Open Banking
CARD_ID = "1131156124"  # Card de prueba que ya tiene documentos
WEBHOOK_URL = "https://pipefy-render-supabase-ingestion.onrender.com"

def wait_for_service(max_attempts=10, delay=30):
    """Espera a que el servicio esté disponible"""
    print(f"⏳ Esperando a que el servicio esté disponible...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"   Intento {attempt}/{max_attempts}...")
            response = requests.get(f"{WEBHOOK_URL}/health", timeout=20)
            response.raise_for_status()
            
            data = response.json()
            print("✅ Servicio disponible!")
            print(f"   Status: {data.get('status')}")
            print(f"   Supabase configurado: {data.get('supabase_configured')}")
            print(f"   Pipefy configurado: {data.get('pipefy_configured')}")
            return True
            
        except Exception as e:
            print(f"   ❌ Intento {attempt} falló: {str(e)[:100]}...")
            if attempt < max_attempts:
                print(f"   ⏱️  Esperando {delay} segundos antes del siguiente intento...")
                time.sleep(delay)
    
    print("💥 El servicio no respondió después de todos los intentos")
    return False

def get_card_info(card_id):
    """Obtiene información del card"""
    query = """
    query GetCard($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            current_phase {
                id
                name
            }
            fields {
                name
                value
            }
        }
    }
    """
    
    variables = {"cardId": card_id}
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print(f"❌ Error al obtener card: {data['errors']}")
            return None
        
        return data.get("data", {}).get("card")
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")
        return None

def move_card_to_phase(card_id, phase_id):
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
            print(f"✅ Card movido exitosamente:")
            print(f"   ID: {card_data.get('id')}")
            print(f"   Título: {card_data.get('title')}")
            print(f"   Fase actual: {card_data.get('current_phase', {}).get('name')}")
            return True
        
        return False
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando prueba completa del flujo con reintentos...")
    print(f"   Card ID: {CARD_ID}")
    print(f"   Fase objetivo: {TARGET_PHASE_ID} (Agent - Open Banking)")
    print(f"   Webhook URL: {WEBHOOK_URL}")
    print()
    
    # Paso 1: Esperar a que el servicio esté disponible
    if not wait_for_service():
        print("💥 No se pudo conectar al servicio. Abortando prueba.")
        exit(1)
    
    print()
    
    # Paso 2: Obtener información del card
    print("📋 Obteniendo información del card...")
    card_info = get_card_info(CARD_ID)
    
    if not card_info:
        print("💥 Error: No se pudo obtener información del card")
        exit(1)
    
    print(f"✅ Card encontrado:")
    print(f"   ID: {card_info.get('id')}")
    print(f"   Título: {card_info.get('title')}")
    print(f"   Fase actual: {card_info.get('current_phase', {}).get('name')}")
    
    # Contar documentos en el card
    fields = card_info.get('fields', [])
    doc_count = 0
    for field in fields:
        field_value = field.get('value', '')
        if field_value and isinstance(field_value, str) and 'http' in field_value:
            doc_count += 1
    
    print(f"   Documentos detectados: {doc_count}")
    print()
    
    # Paso 3: Mover card a la fase objetivo
    print("🚀 Moviendo card a la fase 'Agent - Open Banking'...")
    
    current_phase_id = card_info.get('current_phase', {}).get('id')
    if current_phase_id == TARGET_PHASE_ID:
        print("ℹ️  El card ya está en la fase objetivo. Moviéndolo a otra fase primero...")
        # Mover a otra fase primero (asumiendo que hay una fase anterior)
        temp_phase_id = "338000019"  # Otra fase del pipe
        move_card_to_phase(CARD_ID, temp_phase_id)
        time.sleep(3)
    
    success = move_card_to_phase(CARD_ID, TARGET_PHASE_ID)
    
    if success:
        print("\n🎉 ¡Card movido exitosamente!")
        print("⏳ Esperando 10 segundos para que el webhook se procese...")
        time.sleep(10)
        
        print("\n📝 Ahora puedes:")
        print("1. Revisar los logs de Render: https://dashboard.render.com/web/srv-d0rm9cre5dus73ahn2n0/logs")
        print("2. Ejecutar 'python3 verify_processing.py' para verificar si se procesaron los documentos")
        print("3. Revisar Supabase para ver los documentos almacenados")
    else:
        print("\n💥 Error al mover el card") 