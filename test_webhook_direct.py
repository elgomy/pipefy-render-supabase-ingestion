#!/usr/bin/env python3
"""
Script para probar el webhook directamente enviando un payload simulado
"""

import requests
import json

# Configuración
WEBHOOK_URL = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
CARD_ID = "1131156124"  # Card que ya tiene documentos

def test_webhook_direct():
    """Envía un payload simulado al webhook"""
    
    # Payload simulado de Pipefy
    payload = {
        "data": {
            "card": {
                "id": CARD_ID,
                "title": "pepe",
                "current_phase": {
                    "id": "338000020",
                    "name": "Agent - Open Banking"
                },
                "fields": [
                    {
                        "name": "Contrato Social",
                        "value": "[\"https://app.pipefy.com/pipes/306294445/cards/1131156124/attachments/download/1234567890\"]"
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
        print("🚀 Enviando payload simulado al webhook...")
        print(f"   URL: {WEBHOOK_URL}")
        print(f"   Card ID: {CARD_ID}")
        print()
        
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        print("✅ Webhook procesado exitosamente:")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
        
        if 'crewai_trigger_response' in data:
            crewai_response = data['crewai_trigger_response']
            print(f"   CrewAI Response:")
            print(f"     - Status: {crewai_response.get('status')}")
            print(f"     - Documents processed: {crewai_response.get('documents_processed')}")
            print(f"     - Checklist URL: {crewai_response.get('checklist_url')}")
            print(f"     - Simulation: {crewai_response.get('simulation')}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("⏰ Timeout: El webhook tardó más de 60 segundos en responder")
        print("   Esto puede ser normal si el servicio está procesando archivos grandes")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"   Status code: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error details: {error_data}")
        except:
            print(f"   Response text: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando webhook directamente...")
    print("=" * 50)
    
    success = test_webhook_direct()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Prueba del webhook exitosa!")
        print("📝 Revisa los logs de Render para ver el procesamiento completo.")
    else:
        print("💥 Error en la prueba del webhook")
        print("🔍 Revisa los logs de Render para más detalles.") 