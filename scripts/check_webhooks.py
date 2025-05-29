#!/usr/bin/env python3
"""
Script para consultar los webhooks configurados en un Pipe de Pipefy.
Uso: python check_webhooks.py
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(".env")  # Busca el archivo .env real, no el example.env

def check_pipe_webhooks(pipe_id, token):
    """
    Consulta los webhooks configurados en un Pipe específico de Pipefy.
    
    Args:
        pipe_id (str): ID del Pipe
        token (str): Token de autenticación de Pipefy
    
    Returns:
        dict: Respuesta de la API con los webhooks
    """
    
    # Endpoint GraphQL de Pipefy
    url = "https://api.pipefy.com/graphql"
    
    # Headers para la autenticación
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Query GraphQL para obtener webhooks del pipe
    query = """
    {
      pipe(id: %s) {
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
    """ % pipe_id
    
    # Payload de la request
    payload = {
        "query": query
    }
    
    try:
        # Hacer la request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error al hacer la request: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def main():
    """Función principal del script."""
    
    # Configuración
    PIPE_ID = "306294445"
    PIPEFY_TOKEN = os.getenv("PIPEFY_TOKEN")
    
    print("=== CONSULTA DE WEBHOOKS EN PIPEFY ===")
    print(f"Pipe ID: {PIPE_ID}")
    
    # Verificar que el token esté configurado
    if not PIPEFY_TOKEN or PIPEFY_TOKEN == "your_pipefy_token_here":
        print("\n❌ ERROR: Token de Pipefy no configurado.")
        print("Por favor, configura tu token real en el archivo .env:")
        print("PIPEFY_TOKEN=tu_token_real_aqui")
        return
    
    print(f"Token configurado: {PIPEFY_TOKEN[:10]}...")
    
    # Consultar webhooks
    print("\n🔍 Consultando webhooks...")
    result = check_pipe_webhooks(PIPE_ID, PIPEFY_TOKEN)
    
    if result is None:
        print("❌ No se pudo obtener la información de webhooks.")
        return
    
    # Verificar si hay errores en la respuesta
    if "errors" in result:
        print("❌ Error en la consulta GraphQL:")
        for error in result["errors"]:
            print(f"  - {error.get('message', 'Error desconocido')}")
        return
    
    # Procesar y mostrar resultados
    pipe_data = result.get("data", {}).get("pipe")
    
    if not pipe_data:
        print("❌ No se encontró información del pipe.")
        return
    
    print(f"\n✅ Pipe encontrado: {pipe_data.get('name', 'Sin nombre')}")
    print(f"ID: {pipe_data.get('id')}")
    
    webhooks = pipe_data.get("webhooks", [])
    
    if not webhooks:
        print("\n📭 No hay webhooks configurados en este pipe.")
        print("\nPuedes crear uno nuevo usando la mutación createWebhook:")
        print("""
mutation {
  createWebhook(input: {
    actions: ["card.move"],
    name: "Webhook para Ingestión",
    pipe_id: 306294445,
    url: "https://tu-servicio.onrender.com/webhook/pipefy"
  }) {
    webhook {
      id
      actions
      url
    }
  }
}
        """)
    else:
        print(f"\n📡 Webhooks encontrados ({len(webhooks)}):")
        print("=" * 50)
        
        for i, webhook in enumerate(webhooks, 1):
            print(f"\n{i}. Webhook ID: {webhook.get('id')}")
            print(f"   Acciones: {webhook.get('actions', [])}")
            print(f"   URL: {webhook.get('url', 'No configurada')}")
            print(f"   Email: {webhook.get('email', 'No configurado')}")
            print(f"   Headers: {webhook.get('headers', 'No configurados')}")
            print(f"   Filtros: {webhook.get('filters', 'No configurados')}")
        
        # Verificar si hay algún webhook para card.move
        card_move_webhooks = [w for w in webhooks if "card.move" in w.get("actions", [])]
        
        if card_move_webhooks:
            print(f"\n✅ Encontrados {len(card_move_webhooks)} webhook(s) para 'card.move'")
            print("Estos webhooks pueden ser utilizados para el sistema de ingestión.")
        else:
            print("\n⚠️  No se encontraron webhooks para 'card.move'")
            print("Necesitarás crear uno para el sistema de ingestión.")

if __name__ == "__main__":
    main() 