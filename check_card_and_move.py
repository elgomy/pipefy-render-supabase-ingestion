#!/usr/bin/env python3
"""
Script para verificar el card y moverlo para activar el webhook real
"""

import requests
import json
import time

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
CARD_ID = "1131156124"
TARGET_PHASE_ID = "338000020"  # Agent - Open Banking

def get_card_info():
    """Obtiene información detallada del card"""
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
    
    variables = {"cardId": CARD_ID}
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post("https://api.pipefy.com/graphql", 
                           json={"query": query, "variables": variables}, 
                           headers=headers)
    
    data = response.json()
    return data.get("data", {}).get("card")

def move_card():
    """Mueve el card a la fase objetivo"""
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
        "cardId": CARD_ID,
        "phaseId": TARGET_PHASE_ID
    }
    
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post("https://api.pipefy.com/graphql", 
                           json={"query": mutation, "variables": variables}, 
                           headers=headers)
    
    data = response.json()
    return data.get("data", {}).get("moveCardToPhase", {}).get("card")

if __name__ == "__main__":
    print("🔍 Verificando estado actual del card...")
    
    # Obtener información del card
    card = get_card_info()
    if not card:
        print("❌ No se pudo obtener información del card")
        exit(1)
    
    print(f"📋 Card encontrado:")
    print(f"   ID: {card.get('id')}")
    print(f"   Título: {card.get('title')}")
    print(f"   Fase actual: {card.get('current_phase', {}).get('name')}")
    
    # Mostrar documentos
    print(f"\n📎 Documentos en el card:")
    doc_count = 0
    for field in card.get('fields', []):
        field_value = field.get('value', '')
        if field_value and 'http' in str(field_value):
            doc_count += 1
            print(f"   - {field.get('name')}: {field_value}")
    
    if doc_count == 0:
        print("   ⚠️  No se encontraron documentos con URLs")
    else:
        print(f"   ✅ Total de documentos: {doc_count}")
    
    # Verificar si ya está en la fase objetivo
    current_phase_id = card.get('current_phase', {}).get('id')
    if current_phase_id == TARGET_PHASE_ID:
        print(f"\n⚠️  El card ya está en la fase objetivo 'Agent - Open Banking'")
        print("   Necesita estar en otra fase para activar el webhook")
        exit(0)
    
    print(f"\n🚀 Moviendo card a la fase 'Agent - Open Banking'...")
    
    # Mover el card
    moved_card = move_card()
    if moved_card:
        print(f"✅ Card movido exitosamente:")
        print(f"   Nueva fase: {moved_card.get('current_phase', {}).get('name')}")
        print(f"\n⏱️  Esperando 5 segundos para que se procese el webhook...")
        time.sleep(5)
        print(f"🎉 ¡Movimiento completado! El webhook debería haberse activado.")
    else:
        print("❌ Error al mover el card") 