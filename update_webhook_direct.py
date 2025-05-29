#!/usr/bin/env python3
"""
Script para actualizar directamente la URL del webhook en Pipefy
"""

import requests
import json

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
WEBHOOK_ID = "300520495"
NEW_URL = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"

def update_webhook_url():
    """Actualiza directamente la URL del webhook"""
    
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
    
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    try:
        print("🔧 Actualizando webhook...")
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
    print(f"   Webhook ID: {WEBHOOK_ID}")
    print(f"   Nueva URL: {NEW_URL}")
    print()
    
    success = update_webhook_url()
    
    if success:
        print("\n🎉 ¡Webhook actualizado correctamente!")
    else:
        print("\n💥 Error al actualizar el webhook") 