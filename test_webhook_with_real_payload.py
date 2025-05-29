#!/usr/bin/env python3
"""
Script para probar el webhook con el payload real que Pipefy envía
"""

import requests
import json
import time

def test_webhook_with_minimal_payload():
    """
    Prueba el webhook con el payload mínimo que Pipefy realmente envía.
    Pipefy NO envía los fields en el webhook, solo información básica del card.
    """
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    # Este es el payload real que Pipefy envía (sin fields)
    payload = {
        "data": {
            "card": {
                "id": "1131156124",
                "title": "pepe",
                "current_phase": {
                    "id": "338000020",
                    "name": "Agent - Open Banking"
                }
                # NOTA: Pipefy NO incluye 'fields' en el webhook
                # El código debe hacer una consulta GraphQL adicional para obtenerlos
            },
            "action": "card.move"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    try:
        print("🚀 Probando webhook con payload real de Pipefy...")
        print("📝 IMPORTANTE: Este payload NO incluye 'fields' (como el real de Pipefy)")
        print(f"   URL: {webhook_url}")
        
        print("\n📦 Payload enviado:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        print("\n⏱️  Enviando request...")
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        print("\n✅ Respuesta del webhook:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        
        if 'crewai_trigger_response' in result:
            crewai = result['crewai_trigger_response']
            print(f"\n📊 Respuesta de CrewAI:")
            print(f"   Status: {crewai.get('status')}")
            print(f"   Documents processed: {crewai.get('documents_processed')}")
            print(f"   Checklist URL: {crewai.get('checklist_url')}")
            print(f"   Simulation: {crewai.get('simulation')}")
        
        # Extraer información clave
        documents_processed = result.get('crewai_trigger_response', {}).get('documents_processed', 0)
        
        print(f"\n🎯 RESULTADO:")
        if documents_processed > 0:
            print(f"   ✅ ¡ÉXITO! Se procesaron {documents_processed} documentos")
            return True
        else:
            print(f"   ❌ PROBLEMA: Se procesaron 0 documentos")
            print(f"   🔍 Esto indica que get_pipefy_card_attachments() no está funcionando")
            return False
        
    except requests.exceptions.Timeout:
        print("⏰ Timeout: El webhook tardó más de 120 segundos")
        return False
    except Exception as e:
        print(f"❌ Error al probar webhook: {e}")
        if hasattr(e, 'response'):
            try:
                error_data = e.response.json()
                print(f"   Detalles del error: {error_data}")
            except:
                print(f"   Respuesta del servidor: {e.response.text}")
        return False

def wait_and_check_supabase():
    """Espera y verifica si los documentos aparecen en Supabase"""
    print("\n⏱️  Esperando 30 segundos para que se complete el procesamiento...")
    time.sleep(30)
    
    try:
        # Usar el script de verificación existente
        import subprocess
        result = subprocess.run(['python3', 'verify_processing.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print("\n📊 Verificación en Supabase:")
        print(result.stdout)
        
        # Verificar si se encontraron documentos
        if "Documentos en DB: 0" in result.stdout:
            return False
        else:
            return True
            
    except Exception as e:
        print(f"❌ Error al verificar Supabase: {e}")
        return False

if __name__ == "__main__":
    print("🧪 PRUEBA COMPLETA DEL WEBHOOK")
    print("=" * 70)
    print("📝 Esta prueba simula exactamente lo que Pipefy envía:")
    print("   - Payload sin 'fields'")
    print("   - El código debe hacer consulta GraphQL adicional")
    print("   - Debe encontrar y procesar el documento")
    print("=" * 70)
    
    # Probar webhook
    webhook_success = test_webhook_with_minimal_payload()
    
    if webhook_success:
        # Verificar en Supabase
        supabase_success = wait_and_check_supabase()
        
        print("\n" + "=" * 70)
        print("🏁 RESULTADO FINAL:")
        print(f"   Webhook responde: {'✅' if webhook_success else '❌'}")
        print(f"   Documentos en Supabase: {'✅' if supabase_success else '❌'}")
        
        if webhook_success and supabase_success:
            print("\n🎉 ¡FLUJO COMPLETO FUNCIONANDO!")
        elif webhook_success and not supabase_success:
            print("\n⚠️  Webhook funciona pero documentos no llegan a Supabase")
            print("   🔍 Revisar logs de Render para errores de procesamiento")
        else:
            print("\n💥 Problema en el webhook")
    else:
        print("\n💥 Error en el webhook - no se puede continuar") 