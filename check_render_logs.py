#!/usr/bin/env python3
"""
Script para probar el webhook directamente y ver los logs
"""

import requests
import json
import time

# Configuración
WEBHOOK_URL = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"

def test_webhook_direct():
    """Prueba el webhook directamente con datos simulados"""
    
    # Payload simulado basado en la estructura real de Pipefy
    test_payload = {
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
                        "value": "https://app.pipefy.com/pipes/306294445/cards/1131156124/attachments/download/1234567890"
                    }
                ]
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    try:
        print("🔍 Enviando solicitud de prueba al webhook...")
        print(f"URL: {WEBHOOK_URL}")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        
        response = requests.post(WEBHOOK_URL, json=test_payload, headers=headers, timeout=30)
        
        print(f"\n📊 Respuesta del webhook:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"   Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"   Response Body (text): {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook respondió correctamente")
            return True
        else:
            print(f"❌ Webhook respondió con error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar webhook: {e}")
        return False

def check_health():
    """Verifica el estado del servicio"""
    try:
        response = requests.get("https://pipefy-render-supabase-ingestion.onrender.com/health", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("✅ Estado del servicio:")
        print(f"   Status: {data.get('status')}")
        print(f"   Supabase configurado: {data.get('supabase_configured')}")
        print(f"   Pipefy configurado: {data.get('pipefy_configured')}")
        print(f"   Storage bucket: {data.get('storage_bucket')}")
        
        return True
    except Exception as e:
        print(f"❌ Error al verificar estado: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando webhook directamente...")
    print("=" * 60)
    
    # Verificar estado del servicio
    print("\n1️⃣ Verificando estado del servicio...")
    check_health()
    
    # Probar webhook directamente
    print("\n2️⃣ Probando webhook con datos simulados...")
    test_webhook_direct()
    
    print("\n" + "=" * 60)
    print("📝 Revisa los logs de Render para ver detalles del procesamiento:")
    print("🔗 https://dashboard.render.com/web/srv-d0rm9cre5dus73ahn2n0/logs") 