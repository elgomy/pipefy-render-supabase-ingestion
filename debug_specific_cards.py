#!/usr/bin/env python3
"""
Script para diagnosticar por qué el card 1131156124 no funciona mientras que 1130856215 sí
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"

WORKING_CARD = "1130856215"  # Funciona
BROKEN_CARD = "1131156124"   # No funciona

def get_detailed_card_info(card_id):
    """Obtiene información detallada del card incluyendo todos los campos"""
    query = """
    query GetDetailedCard($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            current_phase {
                id
                name
            }
            pipe {
                id
                name
            }
            fields {
                name
                value
                field {
                    id
                    label
                    type
                    options
                }
            }
            assignees {
                id
                name
                email
            }
            labels {
                id
                name
                color
            }
            created_at
            updated_at
            due_date
            url
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
            return {"error": data['errors']}
        
        return data.get("data", {}).get("card")
    except Exception as e:
        return {"error": str(e)}

def check_card_attachments(card_id):
    """Verifica específicamente los archivos adjuntos del card"""
    query = """
    query GetCardAttachments($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            fields {
                name
                value
                field {
                    id
                    label
                    type
                }
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
            return {"error": data['errors']}
        
        card = data.get("data", {}).get("card")
        if not card:
            return {"error": "Card not found"}
        
        # Buscar campos de tipo attachment
        attachment_fields = []
        for field in card.get("fields", []):
            field_type = field.get("field", {}).get("type", "").lower()
            field_value = field.get("value")
            
            if field_type == "attachment" or (field_value and "pipefy.com/storage" in str(field_value)):
                attachment_fields.append({
                    "name": field.get("name"),
                    "value": field_value,
                    "type": field_type,
                    "field_id": field.get("field", {}).get("id")
                })
        
        return {
            "card_id": card["id"],
            "title": card["title"],
            "attachment_fields": attachment_fields,
            "total_attachments": len(attachment_fields)
        }
    except Exception as e:
        return {"error": str(e)}

def check_supabase_processing(card_id):
    """Verifica si el card ha sido procesado en Supabase"""
    try:
        from supabase import create_client, Client
        
        SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Buscar documentos de este card
        response = supabase.table("documents").select("*").eq("case_id", card_id).execute()
        documents = response.data
        
        return {
            "card_id": card_id,
            "documents_found": len(documents),
            "documents": documents
        }
    except Exception as e:
        return {"error": str(e)}

def simulate_webhook_payload(card_id):
    """Simula el payload del webhook para este card específico"""
    card_info = get_detailed_card_info(card_id)
    
    if "error" in card_info:
        return {"error": card_info["error"]}
    
    # Crear payload simulado
    webhook_payload = {
        "data": {
            "card": {
                "id": card_info["id"],
                "title": card_info["title"],
                "current_phase": card_info["current_phase"],
                "fields": card_info["fields"]
            }
        }
    }
    
    return webhook_payload

def test_webhook_with_card(card_id):
    """Prueba el webhook con el payload específico de este card"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    payload = simulate_webhook_payload(card_id)
    if "error" in payload:
        return {"error": payload["error"]}
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    try:
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text[:500],
            "success": response.status_code == 200
        }
    except Exception as e:
        return {"error": str(e)}

def compare_cards():
    """Compara ambos cards en detalle"""
    print("🔍 COMPARACIÓN DETALLADA DE CARDS")
    print("=" * 80)
    
    # Obtener información de ambos cards
    working_info = get_detailed_card_info(WORKING_CARD)
    broken_info = get_detailed_card_info(BROKEN_CARD)
    
    print(f"📊 INFORMACIÓN BÁSICA")
    print("-" * 50)
    
    if "error" not in working_info:
        print(f"✅ Card {WORKING_CARD} (FUNCIONA):")
        print(f"   Título: {working_info['title']}")
        print(f"   Fase: {working_info['current_phase']['name']} (ID: {working_info['current_phase']['id']})")
        print(f"   Campos: {len(working_info['fields'])}")
        print(f"   Creado: {working_info['created_at']}")
        print(f"   Actualizado: {working_info['updated_at']}")
    else:
        print(f"❌ Error obteniendo card {WORKING_CARD}: {working_info['error']}")
    
    if "error" not in broken_info:
        print(f"\n❌ Card {BROKEN_CARD} (NO FUNCIONA):")
        print(f"   Título: {broken_info['title']}")
        print(f"   Fase: {broken_info['current_phase']['name']} (ID: {broken_info['current_phase']['id']})")
        print(f"   Campos: {len(broken_info['fields'])}")
        print(f"   Creado: {broken_info['created_at']}")
        print(f"   Actualizado: {broken_info['updated_at']}")
    else:
        print(f"❌ Error obteniendo card {BROKEN_CARD}: {broken_info['error']}")
    
    # Comparar archivos adjuntos
    print(f"\n📎 ARCHIVOS ADJUNTOS")
    print("-" * 50)
    
    working_attachments = check_card_attachments(WORKING_CARD)
    broken_attachments = check_card_attachments(BROKEN_CARD)
    
    print(f"✅ Card {WORKING_CARD} (FUNCIONA):")
    if "error" not in working_attachments:
        print(f"   Total adjuntos: {working_attachments['total_attachments']}")
        for att in working_attachments['attachment_fields']:
            print(f"   - {att['name']}: {att['value'][:100]}...")
    else:
        print(f"   Error: {working_attachments['error']}")
    
    print(f"\n❌ Card {BROKEN_CARD} (NO FUNCIONA):")
    if "error" not in broken_attachments:
        print(f"   Total adjuntos: {broken_attachments['total_attachments']}")
        for att in broken_attachments['attachment_fields']:
            print(f"   - {att['name']}: {att['value'][:100]}...")
    else:
        print(f"   Error: {broken_attachments['error']}")
    
    # Verificar procesamiento en Supabase
    print(f"\n💾 PROCESAMIENTO EN SUPABASE")
    print("-" * 50)
    
    working_supabase = check_supabase_processing(WORKING_CARD)
    broken_supabase = check_supabase_processing(BROKEN_CARD)
    
    print(f"✅ Card {WORKING_CARD} (FUNCIONA):")
    if "error" not in working_supabase:
        print(f"   Documentos en Supabase: {working_supabase['documents_found']}")
        for doc in working_supabase['documents']:
            print(f"   - {doc['name']} (creado: {doc['created_at']})")
    else:
        print(f"   Error: {working_supabase['error']}")
    
    print(f"\n❌ Card {BROKEN_CARD} (NO FUNCIONA):")
    if "error" not in broken_supabase:
        print(f"   Documentos en Supabase: {broken_supabase['documents_found']}")
        for doc in broken_supabase['documents']:
            print(f"   - {doc['name']} (creado: {doc['created_at']})")
    else:
        print(f"   Error: {broken_supabase['error']}")
    
    # Probar webhook con ambos cards
    print(f"\n🧪 PRUEBA DE WEBHOOK")
    print("-" * 50)
    
    print(f"✅ Probando card {WORKING_CARD} (FUNCIONA):")
    working_test = test_webhook_with_card(WORKING_CARD)
    if "error" not in working_test:
        print(f"   Status: {working_test['status_code']}")
        print(f"   Éxito: {working_test['success']}")
        if working_test['success']:
            response = working_test['response']
            print(f"   Mensaje: {response.get('message', 'Sin mensaje')}")
            print(f"   Anexos procesados: {response.get('anexos_procesados', 0)}")
    else:
        print(f"   Error: {working_test['error']}")
    
    print(f"\n❌ Probando card {BROKEN_CARD} (NO FUNCIONA):")
    broken_test = test_webhook_with_card(BROKEN_CARD)
    if "error" not in broken_test:
        print(f"   Status: {broken_test['status_code']}")
        print(f"   Éxito: {broken_test['success']}")
        if broken_test['success']:
            response = broken_test['response']
            print(f"   Mensaje: {response.get('message', 'Sin mensaje')}")
            print(f"   Anexos procesados: {response.get('anexos_procesados', 0)}")
        else:
            print(f"   Respuesta de error: {broken_test['response'][:200]}")
    else:
        print(f"   Error: {broken_test['error']}")
    
    # Análisis de diferencias
    print(f"\n🔍 ANÁLISIS DE DIFERENCIAS")
    print("-" * 50)
    
    if "error" not in working_info and "error" not in broken_info:
        # Comparar campos
        working_fields = {f['name']: f['value'] for f in working_info['fields']}
        broken_fields = {f['name']: f['value'] for f in broken_info['fields']}
        
        print("Campos únicos en card que FUNCIONA:")
        for name, value in working_fields.items():
            if name not in broken_fields:
                print(f"   - {name}: {str(value)[:100]}")
        
        print("\nCampos únicos en card que NO FUNCIONA:")
        for name, value in broken_fields.items():
            if name not in working_fields:
                print(f"   - {name}: {str(value)[:100]}")
        
        print("\nCampos con valores diferentes:")
        for name in working_fields:
            if name in broken_fields and working_fields[name] != broken_fields[name]:
                print(f"   - {name}:")
                print(f"     FUNCIONA: {str(working_fields[name])[:100]}")
                print(f"     NO FUNCIONA: {str(broken_fields[name])[:100]}")

if __name__ == "__main__":
    compare_cards()
    
    print(f"\n💡 POSIBLES CAUSAS DEL PROBLEMA:")
    print("=" * 80)
    print("1. Diferencias en los campos de archivos adjuntos")
    print("2. Formato diferente de URLs de archivos")
    print("3. Permisos diferentes en los archivos")
    print("4. Campos faltantes o con valores nulos")
    print("5. Problemas de codificación en el contenido")
    print("6. Diferencias en metadatos del card")
    
    print(f"\n🔧 PRÓXIMOS PASOS:")
    print("1. Revisar las diferencias específicas encontradas arriba")
    print("2. Verificar los logs de Render durante el movimiento del card problemático")
    print("3. Comparar el formato exacto de los archivos adjuntos")
    print("4. Probar mover el card problemático manualmente mientras monitoreamos los logs") 