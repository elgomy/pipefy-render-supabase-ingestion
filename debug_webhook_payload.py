#!/usr/bin/env python3
"""
Script para crear un servidor temporal que capture el payload real del webhook
"""

from fastapi import FastAPI, Request
import uvicorn
import json
from datetime import datetime

app = FastAPI()

@app.post("/webhook/pipefy")
async def capture_webhook(request: Request):
    """Captura y muestra el payload real del webhook"""
    
    # Obtener el cuerpo raw del request
    raw_body = await request.body()
    
    # Obtener headers
    headers = dict(request.headers)
    
    # Intentar parsear como JSON
    try:
        json_payload = await request.json()
    except:
        json_payload = "No se pudo parsear como JSON"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("=" * 80)
    print(f"🕐 WEBHOOK RECIBIDO - {timestamp}")
    print("=" * 80)
    
    print("\n📋 HEADERS:")
    for key, value in headers.items():
        print(f"   {key}: {value}")
    
    print(f"\n📦 RAW BODY ({len(raw_body)} bytes):")
    print(raw_body.decode('utf-8', errors='replace'))
    
    print(f"\n🔍 JSON PAYLOAD:")
    print(json.dumps(json_payload, indent=2, ensure_ascii=False))
    
    # Analizar específicamente los fields del card
    if isinstance(json_payload, dict):
        card_data = json_payload.get('data', {}).get('card', {})
        if card_data:
            print(f"\n📄 ANÁLISIS DEL CARD:")
            print(f"   ID: {card_data.get('id')}")
            print(f"   Título: {card_data.get('title')}")
            
            fields = card_data.get('fields', [])
            print(f"   Campos ({len(fields)}):")
            
            for i, field in enumerate(fields):
                field_name = field.get('name', 'Sin nombre')
                field_value = field.get('value', '')
                
                print(f"     {i+1}. {field_name}:")
                print(f"        Tipo: {type(field_value)}")
                print(f"        Valor: {repr(field_value)}")
                
                # Verificar si contiene URLs
                if field_value and 'http' in str(field_value):
                    print(f"        ✅ Contiene URL(s)")
                    
                    # Intentar parsear como JSON
                    try:
                        if isinstance(field_value, str):
                            parsed = json.loads(field_value)
                            print(f"        JSON parseado: {parsed}")
                    except:
                        print(f"        ⚠️  No es JSON válido")
                else:
                    print(f"        ❌ No contiene URLs")
    
    print("\n" + "=" * 80)
    
    return {
        "status": "captured",
        "message": "Payload capturado y mostrado en consola",
        "timestamp": timestamp
    }

@app.get("/")
async def root():
    return {"message": "Servidor de captura de webhook activo"}

if __name__ == "__main__":
    print("🎯 Iniciando servidor de captura de webhook...")
    print("📡 El servidor estará disponible en: http://localhost:8000")
    print("🔗 URL del webhook: http://localhost:8000/webhook/pipefy")
    print("\n⚠️  IMPORTANTE: Necesitarás usar ngrok o similar para exponer este servidor")
    print("   Ejemplo: ngrok http 8000")
    print("\n🚀 Presiona Ctrl+C para detener el servidor")
    print("=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 