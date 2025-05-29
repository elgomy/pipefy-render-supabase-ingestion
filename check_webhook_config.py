#!/usr/bin/env python3
"""
Script simplificado para verificar la configuración del webhook
"""

import requests
import json

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
PIPE_ID = "306294445"

def check_webhooks():
    """Verifica la configuración de webhooks"""
    query = """
    query GetWebhooks($pipeId: ID!) {
        pipe(id: $pipeId) {
            id
            name
            webhooks {
                id
                url
                actions
                headers
                filters
            }
        }
    }
    """
    
    variables = {"pipeId": PIPE_ID}
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
            print(f"❌ Error en GraphQL: {data['errors']}")
            return None
        
        pipe_data = data.get("data", {}).get("pipe", {})
        webhooks = pipe_data.get("webhooks", [])
        
        print(f"🔍 CONFIGURACIÓN DE WEBHOOKS")
        print("=" * 60)
        print(f"Pipe: {pipe_data.get('name')}")
        print(f"Total webhooks: {len(webhooks)}")
        
        for i, webhook in enumerate(webhooks, 1):
            print(f"\n📡 Webhook {i}:")
            print(f"   ID: {webhook['id']}")
            print(f"   URL: {webhook['url']}")
            print(f"   Acciones: {webhook['actions']}")
            print(f"   Headers: {webhook.get('headers', 'Ninguno')}")
            print(f"   Filtros: {webhook.get('filters', 'Ninguno')}")
            
            # Verificar si es nuestro webhook
            if "pipefy-render-supabase-ingestion" in webhook['url']:
                print(f"   ✅ Este es nuestro webhook de Render")
                
                # Analizar filtros
                filters = webhook.get('filters')
                if filters:
                    print(f"   🔍 Filtros detectados: {filters}")
                    if isinstance(filters, dict) or isinstance(filters, list):
                        print(f"   ⚠️  POSIBLE PROBLEMA: Filtros pueden estar limitando la activación")
                else:
                    print(f"   ✅ Sin filtros - debería activarse para todas las acciones")
        
        return webhooks
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_webhook_manually():
    """Simula el payload que Pipefy enviaría en un movimiento manual"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    # Payload que simula un movimiento real de card
    real_payload = {
        "data": {
            "card": {
                "id": "1130856215",
                "title": "shdgfsh",
                "current_phase": {
                    "id": "338000020",
                    "name": "Agent - Open Banking"
                },
                "fields": [
                    {
                        "name": "Contrato Social",
                        "value": "[\"https://app.pipefy.com/storage/v1/signed/uploads/edfbcde6-test.pdf\"]"
                    }
                ]
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    print(f"\n🧪 PRUEBA DE WEBHOOK MANUAL")
    print("=" * 60)
    print(f"URL: {webhook_url}")
    print(f"Payload: Card {real_payload['data']['card']['id']}")
    
    try:
        response = requests.post(webhook_url, json=real_payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Respuesta exitosa:")
            print(f"   Mensaje: {result.get('message', 'Sin mensaje')}")
            print(f"   CrewAI activado: {'crewai_trigger_response' in result}")
        else:
            print(f"❌ Error en respuesta:")
            print(f"   Texto: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error en solicitud: {e}")

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN DE WEBHOOK")
    print("=" * 80)
    
    # Verificar configuración
    webhooks = check_webhooks()
    
    # Probar webhook manualmente
    test_webhook_manually()
    
    print(f"\n📋 ANÁLISIS:")
    print("=" * 60)
    
    if webhooks:
        render_webhooks = [w for w in webhooks if "pipefy-render-supabase-ingestion" in w['url']]
        
        if render_webhooks:
            webhook = render_webhooks[0]
            print(f"✅ Webhook de Render encontrado (ID: {webhook['id']})")
            
            # Verificar acciones
            actions = webhook.get('actions', [])
            if 'card.move' in actions:
                print(f"✅ Acción 'card.move' configurada")
            else:
                print(f"❌ Acción 'card.move' NO configurada")
                print(f"   Acciones actuales: {actions}")
            
            # Verificar filtros
            filters = webhook.get('filters')
            if filters and filters != "null" and filters != {}:
                print(f"⚠️  Filtros detectados: {filters}")
                print(f"   Esto puede estar limitando cuándo se activa el webhook")
            else:
                print(f"✅ Sin filtros restrictivos")
                
        else:
            print(f"❌ No se encontró webhook de Render")
    
    print(f"\n💡 RECOMENDACIONES:")
    print("1. Si el webhook manual no funciona, verifica los logs de Render en tiempo real")
    print("2. Asegúrate de mover el card exactamente a 'Agent - Open Banking'")
    print("3. Si hay filtros, considera eliminarlos temporalmente para pruebas")
    print("4. Verifica que no hay problemas de conectividad de red") 