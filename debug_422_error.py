#!/usr/bin/env python3
"""
Script para diagnosticar el error 422 Unprocessable Entity en Render
"""

import requests
import json
from datetime import datetime

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"

def get_card_full_data(card_id):
    """Obtiene todos los datos del card tal como los enviaría Pipefy"""
    query = """
    query GetFullCard($cardId: ID!) {
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

def create_realistic_webhook_payload(card_id):
    """Crea un payload realista que simule exactamente lo que Pipefy envía"""
    card_data = get_card_full_data(card_id)
    
    if "error" in card_data:
        return {"error": card_data["error"]}
    
    # Simular el payload exacto que Pipefy envía
    webhook_payload = {
        "data": {
            "card": card_data
        }
    }
    
    return webhook_payload

def test_webhook_with_different_payloads(card_id):
    """Prueba el webhook con diferentes variaciones del payload"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    print(f"🧪 PROBANDO WEBHOOK CON CARD {card_id}")
    print("=" * 60)
    
    # Test 1: Payload completo realista
    print("1️⃣ Payload completo realista:")
    realistic_payload = create_realistic_webhook_payload(card_id)
    
    if "error" in realistic_payload:
        print(f"   ❌ Error creando payload: {realistic_payload['error']}")
        return
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    try:
        response = requests.post(webhook_url, json=realistic_payload, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Éxito: {result.get('message', 'Sin mensaje')}")
        elif response.status_code == 422:
            print(f"   ❌ Error 422: {response.text[:300]}")
            
            # Intentar obtener detalles del error
            try:
                error_detail = response.json()
                print(f"   📋 Detalles del error: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   📋 Respuesta de error (texto): {response.text}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # Test 2: Payload mínimo
    print(f"\n2️⃣ Payload mínimo:")
    minimal_payload = {
        "data": {
            "card": {
                "id": card_id,
                "title": "Test",
                "current_phase": {
                    "id": "338000020",
                    "name": "Agent - Open Banking"
                },
                "fields": []
            }
        }
    }
    
    try:
        response = requests.post(webhook_url, json=minimal_payload, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Éxito: {result.get('message', 'Sin mensaje')}")
        elif response.status_code == 422:
            print(f"   ❌ Error 422: {response.text[:300]}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # Test 3: Payload vacío
    print(f"\n3️⃣ Payload vacío:")
    try:
        response = requests.post(webhook_url, json={}, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Respuesta: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")

def analyze_payload_structure(card_id):
    """Analiza la estructura del payload para identificar problemas"""
    print(f"\n🔍 ANÁLISIS DE ESTRUCTURA DEL PAYLOAD")
    print("=" * 60)
    
    card_data = get_card_full_data(card_id)
    
    if "error" in card_data:
        print(f"❌ Error obteniendo datos: {card_data['error']}")
        return
    
    print(f"📋 Estructura del card {card_id}:")
    print(f"   ID: {card_data.get('id')}")
    print(f"   Título: {card_data.get('title')}")
    print(f"   Fase actual: {card_data.get('current_phase', {}).get('name')} (ID: {card_data.get('current_phase', {}).get('id')})")
    print(f"   Total campos: {len(card_data.get('fields', []))}")
    
    # Analizar campos problemáticos
    print(f"\n📄 Campos del card:")
    for i, field in enumerate(card_data.get('fields', []), 1):
        field_name = field.get('name', 'Sin nombre')
        field_value = field.get('value')
        field_type = field.get('field', {}).get('type', 'Desconocido')
        
        print(f"   {i}. {field_name} ({field_type})")
        
        # Verificar si el valor puede causar problemas
        if field_value is None:
            print(f"      ⚠️  Valor: None (puede causar problemas)")
        elif isinstance(field_value, str) and len(field_value) > 200:
            print(f"      ⚠️  Valor muy largo: {len(field_value)} caracteres")
        elif isinstance(field_value, list):
            print(f"      📋 Lista con {len(field_value)} elementos")
            if field_value and "pipefy.com/storage" in str(field_value[0]):
                print(f"      📎 Contiene archivos adjuntos")
        else:
            print(f"      ✅ Valor: {str(field_value)[:50]}{'...' if len(str(field_value)) > 50 else ''}")

def check_webhook_validation():
    """Verifica qué validaciones espera el webhook"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    print(f"\n🔧 VERIFICACIÓN DE VALIDACIONES DEL WEBHOOK")
    print("=" * 60)
    
    # Test con diferentes estructuras para ver qué falla
    test_cases = [
        {
            "name": "Sin 'data'",
            "payload": {"card": {"id": "test"}}
        },
        {
            "name": "Sin 'card'",
            "payload": {"data": {"id": "test"}}
        },
        {
            "name": "Card sin 'id'",
            "payload": {"data": {"card": {"title": "test"}}}
        },
        {
            "name": "Card sin 'current_phase'",
            "payload": {"data": {"card": {"id": "test", "title": "test"}}}
        },
        {
            "name": "Card sin 'fields'",
            "payload": {"data": {"card": {"id": "test", "title": "test", "current_phase": {"id": "test", "name": "test"}}}}
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}:")
        try:
            response = requests.post(webhook_url, json=test_case['payload'], headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 422:
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error (texto): {response.text[:200]}")
            elif response.status_code == 200:
                print(f"   ✅ Éxito inesperado")
            else:
                print(f"   Otro error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")

if __name__ == "__main__":
    print("🚨 DIAGNÓSTICO DEL ERROR 422 EN RENDER")
    print("=" * 80)
    
    # Probar con ambos cards
    cards_to_test = ["1130856215", "1131156124"]
    
    for card_id in cards_to_test:
        print(f"\n{'='*20} CARD {card_id} {'='*20}")
        
        # Analizar estructura
        analyze_payload_structure(card_id)
        
        # Probar webhook
        test_webhook_with_different_payloads(card_id)
    
    # Verificar validaciones
    check_webhook_validation()
    
    print(f"\n💡 POSIBLES CAUSAS DEL ERROR 422:")
    print("=" * 80)
    print("1. Estructura del payload incorrecta")
    print("2. Campos faltantes requeridos por el webhook")
    print("3. Tipos de datos incorrectos")
    print("4. Valores nulos o vacíos en campos requeridos")
    print("5. Formato incorrecto de archivos adjuntos")
    print("6. Problemas de codificación de caracteres")
    print("7. Payload demasiado grande")
    
    print(f"\n🔧 PRÓXIMOS PASOS:")
    print("1. Revisar los detalles específicos del error 422 arriba")
    print("2. Comparar con el código del webhook en main.py")
    print("3. Verificar las validaciones de Pydantic")
    print("4. Probar con payloads simplificados") 