#!/usr/bin/env python3
"""
Script para diagnosticar por qué el webhook manual no funciona
"""

import requests
import json
import time

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
PIPE_ID = "306294445"
TARGET_PHASE_ID = "338000020"  # Agent - Open Banking

def check_webhook_configuration():
    """Verifica la configuración actual del webhook"""
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
                filters {
                    field
                    operator
                    value
                }
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
            return {"error": data['errors']}
        
        pipe_data = data.get("data", {}).get("pipe", {})
        webhooks = pipe_data.get("webhooks", [])
        
        return {
            "pipe_name": pipe_data.get("name"),
            "total_webhooks": len(webhooks),
            "webhooks": webhooks
        }
    except Exception as e:
        return {"error": str(e)}

def check_phase_configuration():
    """Verifica la configuración de las fases del pipe"""
    query = """
    query GetPipePhases($pipeId: ID!) {
        pipe(id: $pipeId) {
            id
            name
            phases {
                id
                name
                cards_count
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
            return {"error": data['errors']}
        
        pipe_data = data.get("data", {}).get("pipe", {})
        phases = pipe_data.get("phases", [])
        
        return {
            "pipe_name": pipe_data.get("name"),
            "phases": phases,
            "target_phase": next((p for p in phases if p["id"] == TARGET_PHASE_ID), None)
        }
    except Exception as e:
        return {"error": str(e)}

def test_render_webhook_endpoint():
    """Prueba el endpoint del webhook en Render"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    # Test 1: GET request (debería devolver 405 Method Not Allowed)
    try:
        response = requests.get(webhook_url, timeout=10)
        get_result = {
            "status_code": response.status_code,
            "response": response.text[:200] if response.text else "No response"
        }
    except Exception as e:
        get_result = {"error": str(e)}
    
    # Test 2: POST sin datos (debería devolver error de validación)
    try:
        response = requests.post(webhook_url, json={}, timeout=10)
        post_empty_result = {
            "status_code": response.status_code,
            "response": response.text[:200] if response.text else "No response"
        }
    except Exception as e:
        post_empty_result = {"error": str(e)}
    
    # Test 3: POST con datos mínimos
    minimal_payload = {
        "data": {
            "card": {
                "id": "test",
                "title": "Test",
                "current_phase": {"id": "test", "name": "Test"},
                "fields": []
            }
        }
    }
    
    try:
        response = requests.post(webhook_url, json=minimal_payload, timeout=10)
        post_minimal_result = {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text[:200]
        }
    except Exception as e:
        post_minimal_result = {"error": str(e)}
    
    return {
        "get_test": get_result,
        "post_empty_test": post_empty_result,
        "post_minimal_test": post_minimal_result
    }

def check_recent_webhook_activity():
    """Verifica actividad reciente del webhook consultando Supabase"""
    try:
        from supabase import create_client, Client
        
        SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Buscar documentos procesados en las últimas 2 horas
        from datetime import datetime, timedelta
        two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
        
        response = supabase.table("documents").select("*").gte("created_at", two_hours_ago).execute()
        recent_docs = response.data
        
        return {
            "recent_documents": len(recent_docs),
            "documents": [
                {
                    "case_id": doc["case_id"],
                    "name": doc["name"],
                    "created_at": doc["created_at"]
                }
                for doc in recent_docs
            ]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DE WEBHOOK MANUAL")
    print("=" * 80)
    
    # 1. Verificar configuración del webhook
    print("1️⃣ CONFIGURACIÓN DEL WEBHOOK EN PIPEFY")
    print("-" * 50)
    webhook_config = check_webhook_configuration()
    
    if "error" in webhook_config:
        print(f"❌ Error: {webhook_config['error']}")
    else:
        print(f"✅ Pipe: {webhook_config['pipe_name']}")
        print(f"✅ Total webhooks: {webhook_config['total_webhooks']}")
        
        for webhook in webhook_config['webhooks']:
            print(f"\n📡 Webhook ID: {webhook['id']}")
            print(f"   URL: {webhook['url']}")
            print(f"   Acciones: {webhook['actions']}")
            print(f"   Headers: {webhook.get('headers', 'Ninguno')}")
            print(f"   Filtros: {webhook.get('filters', 'Ninguno')}")
    
    # 2. Verificar configuración de fases
    print(f"\n2️⃣ CONFIGURACIÓN DE FASES")
    print("-" * 50)
    phase_config = check_phase_configuration()
    
    if "error" in phase_config:
        print(f"❌ Error: {phase_config['error']}")
    else:
        print(f"✅ Pipe: {phase_config['pipe_name']}")
        print(f"✅ Total fases: {len(phase_config['phases'])}")
        
        target_phase = phase_config['target_phase']
        if target_phase:
            print(f"✅ Fase objetivo encontrada: {target_phase['name']} (ID: {target_phase['id']})")
            print(f"   Cards en esta fase: {target_phase['cards_count']}")
        else:
            print(f"❌ Fase objetivo {TARGET_PHASE_ID} no encontrada")
    
    # 3. Probar endpoint de Render
    print(f"\n3️⃣ PRUEBAS DEL ENDPOINT DE RENDER")
    print("-" * 50)
    endpoint_tests = test_render_webhook_endpoint()
    
    print("GET Request:")
    if "error" in endpoint_tests['get_test']:
        print(f"   ❌ Error: {endpoint_tests['get_test']['error']}")
    else:
        print(f"   Status: {endpoint_tests['get_test']['status_code']}")
        print(f"   Response: {endpoint_tests['get_test']['response']}")
    
    print("\nPOST Empty:")
    if "error" in endpoint_tests['post_empty_test']:
        print(f"   ❌ Error: {endpoint_tests['post_empty_test']['error']}")
    else:
        print(f"   Status: {endpoint_tests['post_empty_test']['status_code']}")
        print(f"   Response: {endpoint_tests['post_empty_test']['response']}")
    
    print("\nPOST Minimal:")
    if "error" in endpoint_tests['post_minimal_test']:
        print(f"   ❌ Error: {endpoint_tests['post_minimal_test']['error']}")
    else:
        print(f"   Status: {endpoint_tests['post_minimal_test']['status_code']}")
        print(f"   Response: {endpoint_tests['post_minimal_test']['response']}")
    
    # 4. Verificar actividad reciente
    print(f"\n4️⃣ ACTIVIDAD RECIENTE")
    print("-" * 50)
    recent_activity = check_recent_webhook_activity()
    
    if "error" in recent_activity:
        print(f"❌ Error: {recent_activity['error']}")
    else:
        print(f"📊 Documentos procesados (últimas 2 horas): {recent_activity['recent_documents']}")
        for doc in recent_activity['documents']:
            print(f"   - Card {doc['case_id']}: {doc['name']} ({doc['created_at']})")
    
    # 5. Diagnóstico y recomendaciones
    print(f"\n5️⃣ DIAGNÓSTICO Y RECOMENDACIONES")
    print("-" * 50)
    
    print("🔍 Posibles causas del problema:")
    print("1. El webhook no está configurado para activarse en movimientos manuales")
    print("2. Los filtros del webhook son demasiado restrictivos")
    print("3. El webhook se activa pero Render no recibe la solicitud")
    print("4. Hay un problema de conectividad entre Pipefy y Render")
    print("5. El webhook se activa solo para ciertas acciones específicas")
    
    print(f"\n💡 Pasos para resolver:")
    print("1. Verifica los logs de Render durante el movimiento manual")
    print("2. Confirma que el card se mueve exactamente a la fase 'Agent - Open Banking'")
    print("3. Revisa si hay filtros adicionales en el webhook")
    print("4. Considera recrear el webhook si es necesario")
    print("5. Verifica que no hay problemas de red o firewall")
    
    print(f"\n🔗 Enlaces para verificar:")
    print("   - Logs de Render: https://dashboard.render.com/web/srv-d0rm9cre5dus73ahn2n0/logs")
    print("   - Webhooks de Pipefy: https://app.pipefy.com/pipes/306294445/settings/webhooks")
    print("   - Fases del Pipe: https://app.pipefy.com/pipes/306294445") 