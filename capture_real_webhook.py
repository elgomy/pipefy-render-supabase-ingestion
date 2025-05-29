#!/usr/bin/env python3
"""
Script para capturar y analizar el payload real que Pipefy envía
"""

import requests
import json
import time
from datetime import datetime

def check_render_logs():
    """Verifica los logs de Render para encontrar el payload real"""
    print("🔍 ANÁLISIS DE LOGS DE RENDER")
    print("=" * 80)
    
    print("Para capturar el payload real que Pipefy envía:")
    print("1. Ve a los logs de Render: https://dashboard.render.com/web/srv-d0rm9cre5dus73ahn2n0/logs")
    print("2. Mueve un card manualmente en Pipefy")
    print("3. Busca en los logs el payload que causó el error 422")
    print("4. Copia el payload completo aquí")
    
    print(f"\n📋 ESTRUCTURA ESPERADA POR EL WEBHOOK:")
    print("El webhook espera esta estructura según Pydantic:")
    print("""
    {
        "data": {
            "card": {
                "id": "string",
                "title": "string" (opcional),
                "current_phase": {...} (opcional),
                "fields": [...] (opcional)
            },
            "action": "string" (opcional)
        }
    }
    """)
    
    print(f"\n⚠️  CAMPOS REQUERIDOS:")
    print("- data (requerido)")
    print("- data.card (requerido)")
    print("- data.card.id (requerido)")
    
    print(f"\n🔧 POSIBLES PROBLEMAS:")
    print("1. Pipefy envía 'card_id' en lugar de 'data.card.id'")
    print("2. Pipefy envía estructura diferente para movimientos manuales")
    print("3. Pipefy incluye campos adicionales que causan conflicto")
    print("4. Problemas de codificación de caracteres")

def simulate_common_pipefy_formats():
    """Simula diferentes formatos que Pipefy podría enviar"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    print(f"\n🧪 PROBANDO FORMATOS ALTERNATIVOS DE PIPEFY")
    print("=" * 80)
    
    # Formato alternativo 1: card_id en lugar de data.card.id
    test_cases = [
        {
            "name": "Formato con card_id directo",
            "payload": {
                "card_id": "1131156124",
                "action": "card.move",
                "data": {
                    "card": {
                        "id": "1131156124",
                        "title": "pepe"
                    }
                }
            }
        },
        {
            "name": "Formato sin data wrapper",
            "payload": {
                "card": {
                    "id": "1131156124",
                    "title": "pepe"
                },
                "action": "card.move"
            }
        },
        {
            "name": "Formato con event wrapper",
            "payload": {
                "event": "card.move",
                "data": {
                    "card": {
                        "id": "1131156124",
                        "title": "pepe"
                    }
                }
            }
        },
        {
            "name": "Formato con timestamp",
            "payload": {
                "data": {
                    "card": {
                        "id": "1131156124",
                        "title": "pepe"
                    }
                },
                "timestamp": datetime.now().isoformat(),
                "webhook_id": "300520495"
            }
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}:")
        try:
            response = requests.post(webhook_url, json=test_case['payload'], headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Éxito: {result.get('message', 'Sin mensaje')}")
            elif response.status_code == 422:
                try:
                    error_detail = response.json()
                    print(f"   ❌ Error 422: {error_detail}")
                except:
                    print(f"   ❌ Error 422 (texto): {response.text[:200]}")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")

def analyze_webhook_signature():
    """Analiza si el problema podría estar en la validación de firma"""
    print(f"\n🔐 ANÁLISIS DE VALIDACIÓN DE FIRMA")
    print("=" * 80)
    
    print("El webhook valida la firma HMAC-SHA256 si está configurada.")
    print("Si Pipefy envía una firma incorrecta, podría causar errores.")
    
    print(f"\n🔧 PASOS PARA VERIFICAR:")
    print("1. Verifica si PIPEFY_WEBHOOK_SECRET está configurado en Render")
    print("2. Si está configurado, verifica que coincida con el secreto en Pipefy")
    print("3. Si no coincide, el webhook rechazará las solicitudes")
    
    print(f"\n💡 SOLUCIÓN TEMPORAL:")
    print("Puedes deshabilitar temporalmente la validación de firma")
    print("comentando la sección de validación en fastAPI.py")

def create_debug_webhook():
    """Crea un webhook de debug que capture todo el payload"""
    print(f"\n🛠️  WEBHOOK DE DEBUG RECOMENDADO")
    print("=" * 80)
    
    debug_code = '''
@app.post("/webhook/pipefy/debug")
async def debug_pipefy_webhook(request: Request):
    """Webhook de debug que captura todo el payload sin validaciones"""
    try:
        # Capturar el cuerpo raw
        raw_body = await request.body()
        
        # Capturar headers
        headers = dict(request.headers)
        
        # Intentar parsear como JSON
        try:
            json_body = await request.json()
        except:
            json_body = "No se pudo parsear como JSON"
        
        # Log completo
        logger.info("=== WEBHOOK DEBUG ===")
        logger.info(f"Headers: {headers}")
        logger.info(f"Raw body: {raw_body.decode('utf-8', errors='ignore')}")
        logger.info(f"JSON body: {json_body}")
        logger.info("=== FIN DEBUG ===")
        
        return {"status": "debug_captured", "message": "Payload capturado en logs"}
        
    except Exception as e:
        logger.error(f"Error en debug webhook: {e}")
        return {"status": "error", "message": str(e)}
'''
    
    print("Agrega este código a fastAPI.py para capturar el payload real:")
    print(debug_code)
    
    print(f"\n📋 INSTRUCCIONES:")
    print("1. Agrega el código de debug a fastAPI.py")
    print("2. Redeploya en Render")
    print("3. Configura un webhook temporal en Pipefy apuntando a /webhook/pipefy/debug")
    print("4. Mueve un card y revisa los logs")
    print("5. Compara el payload real con nuestras simulaciones")

if __name__ == "__main__":
    print("🚨 CAPTURA DE PAYLOAD REAL DE PIPEFY")
    print("=" * 80)
    
    # Verificar logs de Render
    check_render_logs()
    
    # Probar formatos alternativos
    simulate_common_pipefy_formats()
    
    # Analizar validación de firma
    analyze_webhook_signature()
    
    # Recomendar webhook de debug
    create_debug_webhook()
    
    print(f"\n🎯 PRÓXIMOS PASOS RECOMENDADOS:")
    print("=" * 80)
    print("1. Implementar el webhook de debug para capturar el payload real")
    print("2. Mover un card manualmente y revisar los logs")
    print("3. Comparar el payload real con nuestras simulaciones")
    print("4. Ajustar el modelo Pydantic según el formato real")
    print("5. Verificar la configuración del secreto del webhook")
    
    print(f"\n💡 HIPÓTESIS PRINCIPAL:")
    print("Pipefy envía un formato de payload diferente para movimientos manuales")
    print("vs. movimientos programáticos, causando que falle la validación Pydantic.") 