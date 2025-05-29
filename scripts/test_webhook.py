#!/usr/bin/env python3
"""
Script para probar el webhook moviendo un card específico a la fase "Agent - Open Banking"
"""

import requests
import json
import time

def make_graphql_request(query, variables=None, token=None):
    """
    Hace una petición GraphQL a Pipefy.
    """
    url = "https://api.pipefy.com/graphql"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "query": query
    }
    
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la petición: {e}")
        return None

def get_card_info(card_id, token):
    """
    Obtiene información del card.
    """
    query = """
    query GetCard($id: ID!) {
        card(id: $id) {
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
    
    variables = {"id": card_id}
    return make_graphql_request(query, variables, token)

def move_card_to_phase(card_id, phase_id, token):
    """
    Mueve un card a una fase específica.
    """
    query = """
    mutation MoveCardToPhase($input: MoveCardToPhaseInput!) {
        moveCardToPhase(input: $input) {
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
        "input": {
            "card_id": card_id,
            "destination_phase_id": phase_id
        }
    }
    
    return make_graphql_request(query, variables, token)

def main():
    """
    Función principal para probar el webhook.
    """
    # Configuración
    CARD_ID = "1131156124"  # ID del card "pepe" que mencionaste
    TARGET_PHASE_ID = "338000020"  # Fase "Agent - Open Banking"
    TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
    
    print("🧪 PRUEBA DEL WEBHOOK")
    print("=" * 50)
    print(f"📍 Card ID: {CARD_ID}")
    print(f"🎯 Fase destino: {TARGET_PHASE_ID} (Agent - Open Banking)")
    print(f"🌐 Webhook URL: https://pipefy-render-supabase-ingestion.onrender.com/webhook")
    print("-" * 50)
    
    # 1. Obtener información actual del card
    print("1️⃣ Obteniendo información actual del card...")
    card_info = get_card_info(CARD_ID, TOKEN)
    
    if card_info and "errors" not in card_info:
        card = card_info["data"]["card"]
        current_phase = card["current_phase"]
        print(f"   ✅ Card encontrado: '{card['title']}'")
        print(f"   📍 Fase actual: {current_phase['name']} (ID: {current_phase['id']})")
        
        # Verificar si tiene documentos adjuntos
        for field in card["fields"]:
            if "contrato" in field["name"].lower() and field["value"] and field["value"] != "[]":
                print(f"   📎 Documento encontrado en '{field['name']}': {field['value']}")
        
        # 2. Verificar si ya está en la fase objetivo
        if current_phase["id"] == TARGET_PHASE_ID:
            print(f"   ⚠️  El card ya está en la fase objetivo")
            print(f"   🔄 Moviendo a otra fase primero para poder probar...")
            # Aquí podrías mover a otra fase primero si quieres
        
        print("\n2️⃣ Moviendo card a la fase 'Agent - Open Banking'...")
        print("   ⏳ Esto debería activar el webhook...")
        
        # 3. Mover el card
        move_result = move_card_to_phase(CARD_ID, TARGET_PHASE_ID, TOKEN)
        
        if move_result and "errors" not in move_result:
            moved_card = move_result["data"]["moveCardToPhase"]["card"]
            new_phase = moved_card["current_phase"]
            print(f"   ✅ Card movido exitosamente!")
            print(f"   📍 Nueva fase: {new_phase['name']} (ID: {new_phase['id']})")
            print(f"\n🎉 ¡El webhook debería haberse activado!")
            print(f"   🔍 Revisa los logs de Render para ver si recibió el webhook")
            print(f"   🔍 Revisa Supabase para ver si se procesó el documento")
        else:
            print(f"   ❌ Error al mover card: {move_result}")
    else:
        print(f"   ❌ Error al obtener card: {card_info}")

if __name__ == "__main__":
    main() 