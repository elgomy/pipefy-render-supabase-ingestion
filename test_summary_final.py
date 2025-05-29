#!/usr/bin/env python3
"""
Resumen final de todas las pruebas del flujo Pipefy -> Render -> Supabase -> CrewAI
"""

import requests
import json
import time
from datetime import datetime

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
CARD_ID = "1131156124"
WEBHOOK_URL = "https://pipefy-render-supabase-ingestion.onrender.com"

def test_render_service():
    """Prueba el servicio en Render"""
    try:
        response = requests.get(f"{WEBHOOK_URL}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "status": "✅ ACTIVO",
            "details": {
                "status": data.get('status'),
                "supabase_configured": data.get('supabase_configured'),
                "pipefy_configured": data.get('pipefy_configured'),
                "storage_bucket": data.get('storage_bucket')
            }
        }
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "error": str(e)
        }

def test_webhook_endpoint():
    """Prueba el endpoint del webhook directamente"""
    test_payload = {
        "data": {
            "card": {
                "id": CARD_ID,
                "title": "Test Card",
                "current_phase": {
                    "id": "338000020",
                    "name": "Agent - Open Banking"
                },
                "fields": [
                    {
                        "name": "Test Document",
                        "value": "https://app.pipefy.com/test/document.pdf"
                    }
                ]
            }
        }
    }
    
    try:
        response = requests.post(f"{WEBHOOK_URL}/webhook/pipefy", json=test_payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return {
            "status": "✅ FUNCIONAL",
            "response_code": response.status_code,
            "message": data.get('message', 'Sin mensaje'),
            "crewai_triggered": 'crewai_trigger_response' in data
        }
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "error": str(e)
        }

def check_supabase_data():
    """Verifica datos en Supabase"""
    try:
        from supabase import create_client, Client
        
        SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Verificar documentos
        docs_response = supabase.table("documents").select("*").eq("case_id", CARD_ID).execute()
        documents = docs_response.data
        
        # Verificar configuración del checklist
        config_response = supabase.table("app_configs").select("*").eq("key", "checklist_cadastro_pj").execute()
        checklist_config = config_response.data
        
        return {
            "status": "✅ CONECTADO",
            "documents_count": len(documents),
            "documents": [
                {
                    "name": doc['name'],
                    "created_at": doc['created_at'],
                    "file_url": doc['file_url'][:80] + "..." if len(doc['file_url']) > 80 else doc['file_url']
                }
                for doc in documents
            ],
            "checklist_configured": len(checklist_config) > 0,
            "checklist_url": checklist_config[0]['file_url'] if checklist_config else None
        }
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "error": str(e)
        }

def check_pipefy_card():
    """Verifica el estado del card en Pipefy"""
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
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            return {
                "status": "❌ ERROR",
                "error": data['errors']
            }
        
        card = data.get("data", {}).get("card")
        if not card:
            return {
                "status": "❌ NO ENCONTRADO",
                "error": "Card no encontrado"
            }
        
        # Contar documentos en el card
        fields = card.get('fields', [])
        doc_count = 0
        documents = []
        for field in fields:
            field_value = field.get('value', '')
            if field_value and isinstance(field_value, str) and 'http' in field_value:
                doc_count += 1
                documents.append({
                    "name": field.get('name'),
                    "url": field_value[:50] + "..." if len(field_value) > 50 else field_value
                })
        
        return {
            "status": "✅ ENCONTRADO",
            "title": card.get('title'),
            "current_phase": card.get('current_phase', {}).get('name'),
            "phase_id": card.get('current_phase', {}).get('id'),
            "documents_count": doc_count,
            "documents": documents
        }
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "error": str(e)
        }

def check_webhook_configuration():
    """Verifica la configuración del webhook en Pipefy"""
    query = """
    query GetWebhooks($pipeId: ID!) {
        pipe(id: $pipeId) {
            webhooks {
                id
                url
                actions
            }
        }
    }
    """
    
    variables = {"pipeId": "306294445"}
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
            return {
                "status": "❌ ERROR",
                "error": data['errors']
            }
        
        webhooks = data.get("data", {}).get("pipe", {}).get("webhooks", [])
        render_webhooks = [w for w in webhooks if "pipefy-render-supabase-ingestion" in w.get('url', '')]
        
        return {
            "status": "✅ CONFIGURADO" if render_webhooks else "⚠️ NO CONFIGURADO",
            "total_webhooks": len(webhooks),
            "render_webhooks": len(render_webhooks),
            "webhook_details": render_webhooks[0] if render_webhooks else None
        }
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "error": str(e)
        }

if __name__ == "__main__":
    print("🧪 RESUMEN FINAL DE PRUEBAS DEL FLUJO")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Card de prueba: {CARD_ID}")
    print()
    
    # 1. Verificar servicio Render
    print("1️⃣ SERVICIO RENDER")
    print("-" * 40)
    render_status = test_render_service()
    print(f"Estado: {render_status['status']}")
    if 'details' in render_status:
        for key, value in render_status['details'].items():
            print(f"   {key}: {value}")
    elif 'error' in render_status:
        print(f"   Error: {render_status['error']}")
    print()
    
    # 2. Verificar webhook endpoint
    print("2️⃣ WEBHOOK ENDPOINT")
    print("-" * 40)
    webhook_status = test_webhook_endpoint()
    print(f"Estado: {webhook_status['status']}")
    if 'response_code' in webhook_status:
        print(f"   Código de respuesta: {webhook_status['response_code']}")
        print(f"   Mensaje: {webhook_status['message']}")
        print(f"   CrewAI activado: {webhook_status['crewai_triggered']}")
    elif 'error' in webhook_status:
        print(f"   Error: {webhook_status['error']}")
    print()
    
    # 3. Verificar datos en Supabase
    print("3️⃣ SUPABASE DATABASE")
    print("-" * 40)
    supabase_status = check_supabase_data()
    print(f"Estado: {supabase_status['status']}")
    if 'documents_count' in supabase_status:
        print(f"   Documentos almacenados: {supabase_status['documents_count']}")
        print(f"   Checklist configurado: {supabase_status['checklist_configured']}")
        if supabase_status['documents']:
            print("   Documentos:")
            for doc in supabase_status['documents']:
                print(f"     - {doc['name']} ({doc['created_at']})")
    elif 'error' in supabase_status:
        print(f"   Error: {supabase_status['error']}")
    print()
    
    # 4. Verificar card en Pipefy
    print("4️⃣ CARD EN PIPEFY")
    print("-" * 40)
    card_status = check_pipefy_card()
    print(f"Estado: {card_status['status']}")
    if 'title' in card_status:
        print(f"   Título: {card_status['title']}")
        print(f"   Fase actual: {card_status['current_phase']}")
        print(f"   Documentos en card: {card_status['documents_count']}")
        if card_status['documents']:
            print("   Documentos:")
            for doc in card_status['documents']:
                print(f"     - {doc['name']}")
    elif 'error' in card_status:
        print(f"   Error: {card_status['error']}")
    print()
    
    # 5. Verificar configuración webhook
    print("5️⃣ CONFIGURACIÓN WEBHOOK")
    print("-" * 40)
    webhook_config = check_webhook_configuration()
    print(f"Estado: {webhook_config['status']}")
    if 'total_webhooks' in webhook_config:
        print(f"   Total webhooks: {webhook_config['total_webhooks']}")
        print(f"   Webhooks de Render: {webhook_config['render_webhooks']}")
        if webhook_config['webhook_details']:
            details = webhook_config['webhook_details']
            print(f"   ID: {details['id']}")
            print(f"   URL: {details['url']}")
            print(f"   Acciones: {details['actions']}")
    elif 'error' in webhook_config:
        print(f"   Error: {webhook_config['error']}")
    print()
    
    # Resumen final
    print("📋 RESUMEN FINAL")
    print("=" * 80)
    
    all_systems_ok = (
        render_status['status'].startswith('✅') and
        webhook_status['status'].startswith('✅') and
        supabase_status['status'].startswith('✅') and
        card_status['status'].startswith('✅') and
        webhook_config['status'].startswith('✅')
    )
    
    if all_systems_ok:
        print("🎉 ¡TODOS LOS SISTEMAS FUNCIONANDO CORRECTAMENTE!")
        print("✅ El flujo Pipefy -> Render -> Supabase -> CrewAI está operativo")
        print()
        print("📝 Próximos pasos:")
        print("   1. El sistema está listo para procesar cards reales")
        print("   2. Cuando muevas cards a 'Agent - Open Banking', se activará automáticamente")
        print("   3. Los documentos se descargarán y almacenarán en Supabase")
        print("   4. CrewAI se activará para análisis (actualmente simulado)")
    else:
        print("⚠️  ALGUNOS SISTEMAS REQUIEREN ATENCIÓN")
        print("   Revisa los detalles arriba para identificar problemas")
    
    print()
    print("🔗 Enlaces útiles:")
    print(f"   - Logs de Render: https://dashboard.render.com/web/srv-d0rm9cre5dus73ahn2n0/logs")
    print(f"   - Supabase Dashboard: https://supabase.com/dashboard/project/aguoqgqbdbyipztgrmbd")
    print(f"   - Card de prueba: https://app.pipefy.com/pipes/306294445/cards/{CARD_ID}") 