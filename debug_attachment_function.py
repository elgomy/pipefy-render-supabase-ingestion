#!/usr/bin/env python3
"""
Script para debuggear la función get_pipefy_card_attachments
"""

import requests
import json
import asyncio
import httpx
from typing import List, Dict, Any

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
CARD_ID = "1131156124"

class PipefyAttachment:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
    
    def __repr__(self):
        return f"PipefyAttachment(name='{self.name}', path='{self.path}')"

async def debug_get_pipefy_card_attachments(card_id: str) -> List[PipefyAttachment]:
    """Versión debug de la función get_pipefy_card_attachments"""
    print(f"🔍 Iniciando debug para card_id: {card_id}")
    
    if not PIPEFY_TOKEN:
        print("❌ Token Pipefy no configurado")
        return []
    
    query = """
    query GetCardAttachments($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            fields {
                name
                value
            }
        }
    }
    """
    
    variables = {"cardId": card_id}
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        print("📡 Enviando consulta GraphQL a Pipefy...")
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            print(f"📦 Respuesta recibida:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if "errors" in data:
                print(f"❌ Error GraphQL: {data['errors']}")
                return []
            
            card_data = data.get("data", {}).get("card")
            if not card_data:
                print(f"⚠️  Card {card_id} no encontrado o sin datos")
                return []
            
            print(f"\n📋 Datos del card:")
            print(f"   ID: {card_data.get('id')}")
            print(f"   Título: {card_data.get('title')}")
            
            attachments = []
            fields = card_data.get("fields", [])
            print(f"\n📎 Procesando {len(fields)} campos...")
            
            for i, field in enumerate(fields):
                field_name = field.get("name", "")
                field_value = field.get("value", "")
                
                print(f"\n   Campo {i+1}: {field_name}")
                print(f"     Tipo de valor: {type(field_value)}")
                print(f"     Valor: {repr(field_value)}")
                
                if field_value and isinstance(field_value, str):
                    print(f"     ✅ Es string no vacío")
                    
                    # Intentar parsear como JSON
                    try:
                        print(f"     🔄 Intentando parsear como JSON...")
                        urls = json.loads(field_value)
                        print(f"     ✅ JSON parseado exitosamente: {type(urls)}")
                        print(f"     📄 Contenido: {urls}")
                        
                        if isinstance(urls, list):
                            print(f"     ✅ Es una lista con {len(urls)} elementos")
                            for j, url in enumerate(urls):
                                print(f"       URL {j+1}: {type(url)} - {repr(url)}")
                                if isinstance(url, str) and url.startswith("http"):
                                    print(f"       ✅ URL válida encontrada!")
                                    filename = url.split("/")[-1].split("?")[0]
                                    if not filename or filename == "":
                                        filename = f"{field_name}.pdf"
                                    
                                    attachment = PipefyAttachment(name=filename, path=url)
                                    attachments.append(attachment)
                                    print(f"       📎 Attachment creado: {attachment}")
                                else:
                                    print(f"       ❌ No es URL válida")
                        else:
                            print(f"     ❌ No es una lista")
                            
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"     ⚠️  No es JSON válido: {e}")
                        print(f"     🔄 Verificando si es URL directa...")
                        
                        if field_value.startswith("http"):
                            print(f"     ✅ Es URL directa!")
                            filename = field_value.split("/")[-1].split("?")[0]
                            if not filename or filename == "":
                                filename = f"{field_name}.pdf"
                            
                            attachment = PipefyAttachment(name=filename, path=field_value)
                            attachments.append(attachment)
                            print(f"     📎 Attachment creado: {attachment}")
                        else:
                            print(f"     ❌ No es URL directa")
                else:
                    print(f"     ❌ No es string válido")
            
            print(f"\n📊 RESUMEN:")
            print(f"   Total de attachments encontrados: {len(attachments)}")
            for i, att in enumerate(attachments):
                print(f"   {i+1}. {att}")
            
            return attachments
            
    except Exception as e:
        print(f"❌ Error en la consulta: {e}")
        return []

async def main():
    print("🐛 DEBUG: Función get_pipefy_card_attachments")
    print("=" * 70)
    
    attachments = await debug_get_pipefy_card_attachments(CARD_ID)
    
    print("\n" + "=" * 70)
    print(f"🎯 RESULTADO FINAL:")
    print(f"   Attachments encontrados: {len(attachments)}")
    
    if attachments:
        print("   ✅ ¡Función funcionando correctamente!")
        for att in attachments:
            print(f"     - {att.name}: {att.path}")
    else:
        print("   ❌ No se encontraron attachments")
        print("   🔍 Revisa el debug anterior para identificar el problema")

if __name__ == "__main__":
    asyncio.run(main()) 