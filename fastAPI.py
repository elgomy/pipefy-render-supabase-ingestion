#!/usr/bin/env python3
"""
FastAPI corregido para manejar el checklist de forma más robusta.
El checklist es un documento de referencia que ya está en Supabase.
El foco principal es procesar los documentos anexos del card de Pipefy.
"""

# Importaciones y configuración inicial (igual que el original)
import os
import asyncio
import tempfile
import httpx
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel, field_validator, model_validator
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_STORAGE_BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET_NAME", "documents")
PIPEFY_TOKEN = os.getenv("PIPEFY_TOKEN")
PIPEFY_WEBHOOK_SECRET = os.getenv("PIPEFY_WEBHOOK_SECRET")

# Cliente Supabase global
supabase_client: Optional[Client] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação FastAPI."""
    global supabase_client
    
    # Startup
    logger.info("INFO: Iniciando aplicação FastAPI...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("ERRO: Variáveis SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórias.")
        raise RuntimeError("Configuração Supabase incompleta.")
    
    if not PIPEFY_TOKEN:
        logger.error("ERRO: Variável PIPEFY_TOKEN é obrigatória.")
        raise RuntimeError("Token Pipefy não configurado.")
    
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("INFO: Cliente Supabase inicializado com sucesso.")
    except Exception as e:
        logger.error(f"ERRO ao inicializar cliente Supabase: {e}")
        raise RuntimeError(f"Falha na inicialização do Supabase: {e}")
    
    yield
    
    # Shutdown
    logger.info("INFO: Encerrando aplicação FastAPI...")

app = FastAPI(lifespan=lifespan, title="Pipefy-Supabase-CrewAI Integration")

# Modelos Pydantic (iguales al original)
class PipefyCard(BaseModel):
    model_config = {"extra": "allow"}  # Permitir campos adicionales
    
    id: str  # Mantener como string pero convertir en el validator
    title: Optional[str] = None
    current_phase: Optional[Dict[str, Any]] = None
    fields: Optional[List[Dict[str, Any]]] = None
    
    @model_validator(mode='before')
    @classmethod
    def convert_id_to_string(cls, data):
        """Convierte el ID a string sin importar si viene como int o str"""
        if isinstance(data, dict) and 'id' in data:
            data['id'] = str(data['id'])
        return data

class PipefyEventData(BaseModel):
    model_config = {"extra": "allow"}  # Permitir campos adicionales
    
    card: PipefyCard
    action: Optional[str] = None

class PipefyWebhookPayload(BaseModel):
    model_config = {"extra": "allow"}  # Permitir campos adicionales
    
    data: PipefyEventData

class PipefyAttachment(BaseModel):
    name: str
    path: str

class CrewAIInput(BaseModel):
    case_id: str
    checklist_url: str  # Cambiado de checklist_content a checklist_url
    current_date: str
    documents: List[Dict[str, Any]]

# Funciones auxiliares (iguales al original)
async def get_pipefy_card_attachments(card_id: str) -> List[PipefyAttachment]:
    """Obtém anexos de um card do Pipefy via GraphQL."""
    if not PIPEFY_TOKEN:
        logger.error("ERRO: Token Pipefy não configurado.")
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
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"ERRO GraphQL Pipefy: {data['errors']}")
                return []
            
            card_data = data.get("data", {}).get("card")
            if not card_data:
                logger.warning(f"ALERTA: Card {card_id} não encontrado ou sem dados.")
                return []
            
            attachments = []
            fields = card_data.get("fields", [])
            
            for field in fields:
                field_value = field.get("value", "")
                if field_value and isinstance(field_value, str):
                    try:
                        import json
                        urls = json.loads(field_value)
                        if isinstance(urls, list):
                            for url in urls:
                                if isinstance(url, str) and url.startswith("http"):
                                    filename = url.split("/")[-1].split("?")[0]
                                    if not filename or filename == "":
                                        filename = f"{field.get('name', 'documento')}.pdf"
                                    
                                    attachments.append(PipefyAttachment(
                                        name=filename,
                                        path=url
                                    ))
                    except (json.JSONDecodeError, TypeError):
                        if field_value.startswith("http"):
                            filename = field_value.split("/")[-1].split("?")[0]
                            if not filename or filename == "":
                                filename = f"{field.get('name', 'documento')}.pdf"
                            
                            attachments.append(PipefyAttachment(
                                name=filename,
                                path=field_value
                            ))
            
            logger.info(f"INFO: {len(attachments)} anexos encontrados para card {card_id}.")
            return attachments
            
    except Exception as e:
        logger.error(f"ERRO ao buscar anexos do card {card_id}: {e}")
        return []

async def download_file_to_temp(url: str, original_filename: str) -> Optional[str]:
    """Baixa um arquivo de uma URL para um arquivo temporário."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{original_filename}") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            logger.info(f"INFO: Arquivo '{original_filename}' baixado para: {temp_file_path}")
            return temp_file_path
            
    except Exception as e:
        logger.error(f"ERRO ao baixar arquivo '{original_filename}' de {url}: {e}")
        return None

async def upload_to_supabase_storage_async(local_file_path: str, case_id: str, original_filename: str) -> Optional[str]:
    """Faz upload de um arquivo local para o Supabase Storage."""
    if not supabase_client:
        logger.error("ERRO: Cliente Supabase não inicializado.")
        return None
    
    try:
        storage_path = f"{case_id}/{original_filename}"
        
        def sync_upload_and_get_url():
            with open(local_file_path, 'rb') as file:
                upload_response = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET_NAME).upload(
                    storage_path, file, file_options={"upsert": "true"}
                )
                
                if hasattr(upload_response, 'error') and upload_response.error:
                    raise Exception(f"Erro no upload: {upload_response.error}")
                
                public_url_response = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET_NAME).get_public_url(storage_path)
                return public_url_response
        
        public_url = await asyncio.to_thread(sync_upload_and_get_url)
        
        # Limpar arquivo temporário
        try:
            os.unlink(local_file_path)
        except:
            pass
        
        logger.info(f"INFO: Upload concluído para '{original_filename}'. URL: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"ERRO no upload de '{original_filename}': {e}")
        try:
            os.unlink(local_file_path)
        except:
            pass
        return None

async def determine_document_tag(filename: str, card_fields: Optional[List[Dict]] = None) -> str:
    """Determina a tag do documento baseada no nome do arquivo."""
    filename_lower = filename.lower()
    
    tag_keywords = {
        "contrato_social": ["contrato", "social", "estatuto"],
        "comprovante_residencia": ["comprovante", "residencia", "endereco"],
        "documento_identidade": ["rg", "identidade", "cnh"],
        "declaracao_impostos": ["declaracao", "imposto", "ir"],
        "certificado_registro": ["certificado", "registro"],
        "procuracao": ["procuracao"],
        "balanco_patrimonial": ["balanco", "patrimonial", "demonstracao"],
        "faturamento": ["faturamento", "receita"]
    }
    
    for tag, keywords in tag_keywords.items():
        if any(keyword in filename_lower for keyword in keywords):
            return tag
    
    return "outro_documento"

async def register_document_in_db(case_id: str, document_name: str, document_tag: str, file_url: str):
    """Registra um documento na tabela 'documents' do Supabase."""
    if not supabase_client:
        logger.error("ERRO: Cliente Supabase não inicializado.")
        return False
    
    try:
        data_to_insert = {
            "case_id": case_id,
            "name": document_name,
            "document_tag": document_tag,
            "file_url": file_url,
            "status": "uploaded"
        }
        
        response = await asyncio.to_thread(
            supabase_client.table("documents").upsert(data_to_insert, on_conflict="case_id, name").execute
        )
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"ERRO Supabase DB (upsert) para {document_name}: {response.error.message}")
            return False
        if response.data:
            logger.info(f"INFO: Documento '{document_name}' registrado/atualizado no DB para case_id '{case_id}'.")
            return True
        logger.warning(f"AVISO: Upsert do documento '{document_name}' no DB não retornou dados nem erro explícito.")
        return False
    except Exception as e:
        logger.error(f"ERRO ao registrar documento '{document_name}' no Supabase DB: {e}")
        return False

async def get_checklist_url_from_supabase(config_name: str = "checklist_cadastro_pj") -> str:
    """
    Obtém a URL do checklist de forma robusta.
    Se não conseguir, retorna uma URL padrão ou vazia, mas NÃO falha.
    """
    if not supabase_client:
        logger.warning("AVISO: Cliente Supabase não inicializado para buscar checklist. Usando URL padrão.")
        return "https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf"
    
    try:
        logger.info(f"INFO: Buscando URL do checklist '{config_name}' de app_configs...")
        
        def sync_get_checklist_url():
            return supabase_client.table("app_configs").select("file_url").eq("config_name", config_name).single().execute()
        
        response = await asyncio.to_thread(sync_get_checklist_url)

        if response.data and response.data.get("file_url"):
            checklist_url = response.data["file_url"]
            logger.info(f"INFO: URL do checklist obtida: {checklist_url}")
            return checklist_url
        else:
            logger.warning(f"AVISO: URL do checklist '{config_name}' não encontrada. Usando URL padrão.")
            return "https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf"
            
    except Exception as e:
        logger.warning(f"AVISO: Erro ao buscar URL do checklist '{config_name}': {e}. Usando URL padrão.")
        return "https://aguoqgqbdbyipztgrmbd.supabase.co/storage/v1/object/public/checklist/checklist.pdf"

async def trigger_crewai_analysis(case_id: str, checklist_url: str, documents_for_crew: List[Dict]):
    """Simula la análisis de CrewAI registrando la información en logs."""
    # Crear el payload que se enviaría a CrewAI
    payload = CrewAIInput(
        case_id=case_id,
        checklist_url=checklist_url,  # Ahora usa URL en lugar de contenido
        current_date=datetime.now().strftime('%Y-%m-%d'),
        documents=documents_for_crew
    )
    
    # Registrar toda la información en logs para análisis posterior
    logger.info(f"=== ANÁLISIS CREWAI SIMULADO ===")
    logger.info(f"Case ID: {case_id}")
    logger.info(f"Fecha actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Número de documentos: {len(documents_for_crew)}")
    logger.info(f"Checklist URL: {checklist_url}")
    
    # Registrar detalles de cada documento
    for i, doc in enumerate(documents_for_crew, 1):
        logger.info(f"Documento {i}:")
        logger.info(f"  - Nombre: {doc.get('name', 'N/A')}")
        logger.info(f"  - Tag: {doc.get('document_tag', 'N/A')}")
        logger.info(f"  - URL: {doc.get('file_url', 'N/A')}")
    
    # Registrar el payload completo para referencia
    logger.info(f"Payload completo para CrewAI: {payload.model_dump_json(indent=2)}")
    logger.info(f"=== FIN ANÁLISIS CREWAI SIMULADO ===")
    
    # Retornar una respuesta simulada de éxito
    return {
        "status": "success",
        "message": f"Análisis CrewAI simulado completado para case_id: {case_id}",
        "case_id": case_id,
        "documents_processed": len(documents_for_crew),
        "checklist_url": checklist_url,
        "timestamp": datetime.now().isoformat(),
        "simulation": True,
        "note": "Esta es una respuesta simulada. CrewAI no fue llamado realmente."
    }

# --- Endpoint Principal ---
@app.post("/webhook/pipefy")
async def handle_pipefy_webhook(payload: PipefyWebhookPayload, request: Request, x_pipefy_signature: Optional[str] = Header(None)):
    """
    Recebe webhooks do Pipefy, processa anexos, armazena no Supabase e aciona CrewAI.
    VERSIÓN ROBUSTA: No falla por problemas del checklist.
    """
    logger.info(f"INFO: Webhook Pipefy recevido. Ação: {payload.data.action if payload.data else 'N/A'}")

    # Validación del webhook (TEMPORALMENTE DESHABILITADA PARA DEBUG)
    # if PIPEFY_WEBHOOK_SECRET and x_pipefy_signature:
    #     try:
    #         import hmac
    #         import hashlib
    #         
    #         raw_body = await request.body()
    #         signature_calculated = hmac.new(
    #             PIPEFY_WEBHOOK_SECRET.encode(),
    #             raw_body,
    #             hashlib.sha256
    #         ).hexdigest()
    #         
    #         if not hmac.compare_digest(signature_calculated, x_pipefy_signature):
    #             logger.warning(f"ALERTA: Assinatura do webhook inválida! Acesso não autorizado.")
    #             raise HTTPException(status_code=401, detail="Assinatura de webhook inválida")
    #         
    #         logger.info("INFO: Validação de assinatura do webhook bem-sucedida.")
    #     except Exception as e:
    #         logger.error(f"ERRO ao validar assinatura do webhook: {e}")
    #         raise HTTPException(status_code=500, detail=f"Erro na validação: {str(e)}")

    if not payload.data or not payload.data.card or not payload.data.card.id:
        logger.error("ERRO: Payload do webhook inválido ou sem ID do card.")
        raise HTTPException(status_code=400, detail="Payload inválido ou ID do card ausente.")
    
    card_id_str = str(payload.data.card.id)
    logger.info(f"INFO: Processando card_id: {card_id_str}")

    # Procesar documentos anexos del card
    attachments_from_pipefy = await get_pipefy_card_attachments(card_id_str)
    processed_documents_for_crewai: List[Dict[str, Any]] = []

    if not attachments_from_pipefy:
        logger.info(f"INFO: Nenhum anexo encontrado para o card {card_id_str}.")
    else:
        logger.info(f"INFO: {len(attachments_from_pipefy)} anexos encontrados para o card {card_id_str}.")
        for att in attachments_from_pipefy:
            logger.info(f"INFO: Processando anexo: {att.name}...")
            
            temp_file = await download_file_to_temp(att.path, att.name)
            if temp_file:
                storage_url = await upload_to_supabase_storage_async(temp_file, card_id_str, att.name)
                if storage_url:
                    document_tag = await determine_document_tag(att.name)
                    success_db = await register_document_in_db(card_id_str, att.name, document_tag, storage_url)
                    if success_db:
                        processed_documents_for_crewai.append({
                            "name": att.name,
                            "file_url": storage_url,
                            "document_tag": document_tag
                        })
                else:
                    logger.warning(f"ALERTA: Falha ao fazer upload do anexo '{att.name}' para Supabase Storage.")
            else:
                logger.warning(f"ALERTA: Falha ao baixar o anexo '{att.name}' do Pipefy.")
    
    logger.info(f"INFO: {len(processed_documents_for_crewai)} documentos preparados para CrewAI.")

    # Obtener URL del checklist de forma robusta (NO falla)
    logger.info("INFO: Buscando URL do checklist...")
    checklist_url = await get_checklist_url_from_supabase()
    logger.info(f"INFO: URL do checklist: {checklist_url}")
    
    # Activar CrewAI (simulado)
    logger.info(f"INFO: Acionando CrewAI para o case_id: {card_id_str}")
    crewai_response = await trigger_crewai_analysis(card_id_str, checklist_url, processed_documents_for_crewai)

    return {
        "status": "success",
        "message": f"Webhook para card {card_id_str} processado. {len(processed_documents_for_crewai)} anexos manuseados e enviados para CrewAI.",
        "crewai_trigger_response": crewai_response
    }

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

@app.post("/webhook/pipefy/raw")
async def raw_pipefy_webhook(request: Request):
    """Webhook raw que acepta cualquier payload sin validación Pydantic"""
    try:
        # Capturar todo sin validación
        raw_body = await request.body()
        headers = dict(request.headers)
        
        # Intentar parsear JSON
        try:
            json_data = json.loads(raw_body.decode('utf-8'))
        except Exception as parse_error:
            logger.error(f"Error parseando JSON: {parse_error}")
            return {"status": "error", "message": f"JSON inválido: {parse_error}"}
        
        # Log detallado
        logger.info("=== WEBHOOK RAW (SIN VALIDACIÓN PYDANTIC) ===")
        logger.info(f"Headers: {headers}")
        logger.info(f"JSON recibido: {json.dumps(json_data, indent=2)}")
        
        # Intentar extraer card_id de diferentes estructuras posibles
        card_id = None
        
        # Estructura estándar: data.card.id
        if isinstance(json_data, dict):
            if "data" in json_data and isinstance(json_data["data"], dict):
                if "card" in json_data["data"] and isinstance(json_data["data"]["card"], dict):
                    card_id = json_data["data"]["card"].get("id")
            
            # Estructura alternativa: card.id directo
            if not card_id and "card" in json_data and isinstance(json_data["card"], dict):
                card_id = json_data["card"].get("id")
            
            # Estructura alternativa: card_id directo
            if not card_id:
                card_id = json_data.get("card_id")
        
        logger.info(f"Card ID extraído: {card_id}")
        
        if card_id:
            logger.info(f"✅ Webhook raw procesado exitosamente para card: {card_id}")
            return {
                "status": "success", 
                "message": f"Webhook raw procesado para card {card_id}",
                "card_id": card_id,
                "structure_detected": "valid"
            }
        else:
            logger.warning("⚠️ No se pudo extraer card_id del payload")
            return {
                "status": "warning", 
                "message": "Payload recibido pero sin card_id válido",
                "structure_detected": "unknown"
            }
        
        logger.info("=== FIN WEBHOOK RAW ===")
        
    except Exception as e:
        logger.error(f"Error en webhook raw: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"message": "API de Ingestão Pipefy-Supabase-CrewAI está operacional."}

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde."""
    return {
        "status": "healthy",
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_SERVICE_KEY),
        "pipefy_configured": bool(PIPEFY_TOKEN),
        "storage_bucket": SUPABASE_STORAGE_BUCKET_NAME
    }

@app.post("/webhook/ultimate-debug")
async def ultimate_debug_webhook(request: Request):
    """
    🔥 ULTIMATE DEBUG - Captura TODO sin validaciones
    Este endpoint NO usa Pydantic y acepta CUALQUIER cosa
    """
    try:
        # Capturar ABSOLUTAMENTE TODO
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        
        # Capturar el cuerpo raw
        raw_body = await request.body()
        raw_body_str = raw_body.decode('utf-8', errors='ignore')
        
        # Intentar parsear JSON
        json_data = None
        json_error = None
        try:
            json_data = json.loads(raw_body_str)
        except Exception as e:
            json_error = str(e)
        
        # Timestamp
        timestamp = datetime.now().isoformat()
        
        # LOG ULTRA DETALLADO
        logger.info("🔥🔥🔥 ULTIMATE DEBUG WEBHOOK 🔥🔥🔥")
        logger.info(f"Timestamp: {timestamp}")
        logger.info(f"Method: {method}")
        logger.info(f"URL: {url}")
        logger.info(f"Query Params: {query_params}")
        logger.info("=" * 50)
        logger.info("HEADERS:")
        for key, value in headers.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 50)
        logger.info(f"Raw Body Length: {len(raw_body)} bytes")
        logger.info(f"Raw Body (first 1000 chars): {raw_body_str[:1000]}")
        if len(raw_body_str) > 1000:
            logger.info(f"Raw Body (last 500 chars): ...{raw_body_str[-500:]}")
        logger.info("=" * 50)
        
        if json_data:
            logger.info("JSON PARSED SUCCESSFULLY:")
            logger.info(json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # Analizar estructura
            logger.info("=" * 50)
            logger.info("STRUCTURE ANALYSIS:")
            
            def analyze_structure(obj, path=""):
                if isinstance(obj, dict):
                    logger.info(f"  {path} (dict) - keys: {list(obj.keys())}")
                    for key, value in obj.items():
                        analyze_structure(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    logger.info(f"  {path} (list) - length: {len(obj)}")
                    if obj:
                        analyze_structure(obj[0], f"{path}[0]")
                else:
                    logger.info(f"  {path} ({type(obj).__name__}): {str(obj)[:100]}")
            
            analyze_structure(json_data)
            
        else:
            logger.info(f"JSON PARSE ERROR: {json_error}")
        
        logger.info("🔥🔥🔥 END ULTIMATE DEBUG 🔥🔥🔥")
        
        # Respuesta exitosa SIEMPRE
        return {
            "status": "ultimate_debug_success",
            "message": "Payload capturado exitosamente",
            "timestamp": timestamp,
            "data_received": json_data is not None,
            "body_length": len(raw_body),
            "headers_count": len(headers)
        }
        
    except Exception as e:
        logger.error(f"🔥 ULTIMATE DEBUG ERROR: {e}")
        import traceback
        logger.error(f"🔥 TRACEBACK: {traceback.format_exc()}")
        
        return {
            "status": "ultimate_debug_error",
            "message": f"Error en ultimate debug: {e}",
            "timestamp": datetime.now().isoformat()
        }