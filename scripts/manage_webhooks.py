#!/usr/bin/env python3
"""
Script para gestionar webhooks en Pipefy:
- Eliminar todos los webhooks existentes
- Crear un nuevo webhook para el endpoint de Render
"""

import os
import requests
import json
import sys

def make_graphql_request(query, variables=None, token=None):
    """
    Hace una petición GraphQL a Pipefy.
    
    Args:
        query (str): Query GraphQL
        variables (dict): Variables para la query
        token (str): Token de autenticación
    
    Returns:
        dict: Respuesta de la API
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

def get_pipe_webhooks(pipe_id, token):
    """
    Obtiene todos los webhooks de un Pipe.
    """
    query = """
    query GetPipeWebhooks($pipeId: ID!) {
        pipe(id: $pipeId) {
            id
            name
            webhooks {
                id
                actions
                url
                email
                headers
                filters
            }
        }
    }
    """
    
    variables = {"pipeId": str(pipe_id)}
    return make_graphql_request(query, variables, token)

def delete_webhook(webhook_id, token):
    """
    Elimina un webhook específico.
    """
    query = """
    mutation DeleteWebhook($webhookId: ID!) {
        deleteWebhook(input: {id: $webhookId}) {
            success
        }
    }
    """
    
    variables = {"webhookId": str(webhook_id)}
    return make_graphql_request(query, variables, token)

def create_webhook(pipe_id, token, endpoint_url):
    """
    Crea un nuevo webhook para el Pipe.
    """
    query = """
    mutation CreateWebhook($input: CreateWebhookInput!) {
        createWebhook(input: $input) {
            webhook {
                id
                actions
                url
                name
                headers
                filters
            }
        }
    }
    """
    
    # Configuración básica del webhook
    variables = {
        "input": {
            "pipe_id": pipe_id,
            "url": endpoint_url,
            "actions": ["card.move"],
            "name": "Render Integration Webhook"
        }
    }
    
    return make_graphql_request(query, variables, token)

def main():
    """
    Función principal para gestionar los webhooks.
    """
    # Configuración
    PIPE_ID = "306294445"
    TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
    ENDPOINT_URL = "https://pipefy-render-supabase-ingestion.onrender.com/webhook"
    
    print("🚀 Iniciando gestión de webhooks...")
    print(f"📍 Pipe ID: {PIPE_ID}")
    print(f"🌐 Endpoint: {ENDPOINT_URL}")
    print("-" * 50)
    
    # 1. Obtener webhooks existentes
    print("📡 Obteniendo webhooks existentes...")
    response = get_pipe_webhooks(PIPE_ID, TOKEN)
    
    if not response or "errors" in response:
        print(f"❌ Error al obtener webhooks: {response}")
        return
    
    webhooks = response["data"]["pipe"]["webhooks"]
    print(f"✅ Encontrados {len(webhooks)} webhooks existentes")
    
    # 2. Eliminar webhooks existentes
    if webhooks:
        print("\n🗑️  Eliminando webhooks existentes...")
        for webhook in webhooks:
            webhook_id = webhook["id"]
            print(f"   Eliminando webhook {webhook_id}...")
            
            delete_response = delete_webhook(webhook_id, TOKEN)
            
            if delete_response and "errors" not in delete_response:
                if delete_response["data"]["deleteWebhook"]["success"]:
                    print(f"   ✅ Webhook {webhook_id} eliminado exitosamente")
                else:
                    print(f"   ❌ Error al eliminar webhook {webhook_id}")
            else:
                print(f"   ❌ Error en la petición para eliminar webhook {webhook_id}")
    
    # 3. Crear nuevo webhook
    print(f"\n🔧 Creando nuevo webhook...")
    print(f"   URL: {ENDPOINT_URL}")
    print(f"   Acción: card.move")
    print(f"   Filtro: to_phase_id = [338000020] (Agent - Open Banking)")
    
    create_response = create_webhook(PIPE_ID, TOKEN, ENDPOINT_URL)
    
    if create_response and "errors" not in create_response:
        new_webhook = create_response["data"]["createWebhook"]["webhook"]
        print(f"✅ Nuevo webhook creado exitosamente!")
        print(f"   ID: {new_webhook['id']}")
        print(f"   URL: {new_webhook['url']}")
        print(f"   Acciones: {new_webhook['actions']}")
        print(f"   Filtros: {new_webhook['filters']}")
    else:
        print(f"❌ Error al crear webhook: {create_response}")
        return
    
    print("\n🎉 ¡Gestión de webhooks completada exitosamente!")
    print("\n📋 Resumen:")
    print(f"   • Webhooks eliminados: {len(webhooks)}")
    print(f"   • Webhooks creados: 1")
    print(f"   • Endpoint configurado: {ENDPOINT_URL}")
    print(f"   • Trigger: Cuando un card se mueve A la fase 'Agent - Open Banking'")

if __name__ == "__main__":
    main() 