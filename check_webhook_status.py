#!/usr/bin/env python3
"""
Script para verificar el estado del webhook en Pipefy
"""

import requests
import json

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"

def check_webhooks():
    """Verifica los webhooks configurados"""
    query = """
    query {
        webhooks {
            id
            url
            actions
            filters {
                field
                condition
                value
            }
        }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post("https://api.pipefy.com/graphql", 
                               json={"query": query}, 
                               headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"❌ Error al consultar webhooks: {data['errors']}")
            return []
        
        webhooks = data.get("data", {}).get("webhooks", [])
        return webhooks
        
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")
        return []

def test_webhook_manually():
    """Envía una prueba manual al webhook"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    # Payload de prueba basado en el movimiento real del card
    payload = {
        "data": {
            "card": {
                "id": "1131156124",
                "title": "pepe",
                "current_phase": {
                    "id": "338000020",
                    "name": "Agent - Open Banking"
                },
                "fields": [
                    {
                        "name": "Contrato Social",
                        "value": "[\"https://app.pipefy.com/storage/v1/signed/uploads/f7ebb04f-200a-4ae8-9e22-2ef031d1940e/2-ContratoSocial_12.2021.pdf?expires_on=1748463474&signature=ucXDd5Z%2FHvCue3v1yeX0kv4gtrPqbCWtj6effY99G20%3D\"]"
                    }
                ]
            },
            "action": "card.move"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    try:
        print("🚀 Enviando prueba manual al webhook...")
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Respuesta del webhook:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        
        if 'crewai_trigger_response' in result:
            crewai = result['crewai_trigger_response']
            print(f"   CrewAI Status: {crewai.get('status')}")
            print(f"   Documents processed: {crewai.get('documents_processed')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al probar webhook: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando configuración de webhooks...")
    print("=" * 60)
    
    # Verificar webhooks configurados
    webhooks = check_webhooks()
    
    print(f"📋 Webhooks encontrados: {len(webhooks)}")
    
    for webhook in webhooks:
        print(f"\n🔗 Webhook ID: {webhook.get('id')}")
        print(f"   URL: {webhook.get('url')}")
        print(f"   Acciones: {webhook.get('actions')}")
        
        filters = webhook.get('filters', [])
        if filters:
            print(f"   Filtros:")
            for filter_item in filters:
                print(f"     - {filter_item.get('field')}: {filter_item.get('condition')} {filter_item.get('value')}")
        else:
            print(f"   Filtros: Ninguno")
    
    print("\n" + "=" * 60)
    
    # Probar webhook manualmente
    print("\n🧪 Probando webhook manualmente...")
    test_result = test_webhook_manually()
    
    if test_result:
        print("\n🎉 ¡Webhook responde correctamente!")
    else:
        print("\n💥 Error en la prueba del webhook") 