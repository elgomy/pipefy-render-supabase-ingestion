#!/usr/bin/env python3
"""
Script para actualizar la URL del webhook existente en Pipefy
"""

import requests
import json

# Configuración - usando el token completo
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
WEBHOOK_ID = "300520495"
NEW_URL = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"

def update_webhook_url():
    """Actualiza la URL del webhook existente"""
    
    # Primero verificamos que el webhook existe
    query_webhook = """
    query {
        webhooks {
            id
            url
            actions
        }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Verificar webhooks existentes
    try:
        response = requests.post("https://api.pipefy.com/graphql", 
                               json={"query": query_webhook}, 
                               headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"❌ Error al consultar webhooks: {data['errors']}")
            return False
        
        webhooks = data.get("data", {}).get("webhooks", [])
        print(f"📋 Webhooks encontrados: {len(webhooks)}")
        
        target_webhook = None
        for webhook in webhooks:
            print(f"   - ID: {webhook.get('id')}, URL: {webhook.get('url')}")
            if webhook.get('id') == WEBHOOK_ID:
                target_webhook = webhook
                break
        
        if not target_webhook:
            print(f"❌ No se encontró el webhook con ID {WEBHOOK_ID}")
            return False
        
        print(f"\n🎯 Webhook objetivo encontrado:")
        print(f"   ID: {target_webhook.get('id')}")
        print(f"   URL actual: {target_webhook.get('url')}")
        print(f"   Nueva URL: {NEW_URL}")
        
        # Si la URL ya es correcta, no necesitamos actualizarla
        if target_webhook.get('url') == NEW_URL:
            print("✅ La URL del webhook ya está actualizada!")
            return True
        
        # Actualizar la URL del webhook
        mutation = """
        mutation UpdateWebhook($webhookId: ID!, $url: String!) {
            updateWebhook(input: {
                id: $webhookId
                url: $url
            }) {
                webhook {
                    id
                    url
                    actions
                }
            }
        }
        """
        
        variables = {
            "webhookId": WEBHOOK_ID,
            "url": NEW_URL
        }
        
        payload = {
            "query": mutation,
            "variables": variables
        }
        
        print("\n🔧 Actualizando webhook...")
        response = requests.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"❌ Error al actualizar webhook: {data['errors']}")
            return False
        
        webhook_data = data.get("data", {}).get("updateWebhook", {}).get("webhook", {})
        
        if webhook_data:
            print("✅ Webhook actualizado exitosamente:")
            print(f"   ID: {webhook_data.get('id')}")
            print(f"   URL: {webhook_data.get('url')}")
            print(f"   Acciones: {webhook_data.get('actions')}")
            return True
        else:
            print("❌ No se pudo actualizar el webhook")
            return False
            
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Actualizando URL del webhook en Pipefy...")
    print(f"   Webhook ID objetivo: {WEBHOOK_ID}")
    print(f"   Nueva URL: {NEW_URL}")
    print()
    
    success = update_webhook_url()
    
    if success:
        print("\n🎉 ¡Proceso completado exitosamente!")
    else:
        print("\n💥 Error en el proceso") 