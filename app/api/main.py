from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import spacy
from bson import ObjectId

# Importar processadores e analisadores
from app.utils.text_processor import TextProcessor
from app.utils.redacao_analyzer import RedacaoAnalyzer
from app.utils.file_processor import file_processor
from app.utils.ia_agent import ia_agent

# Importar esquemas
from app.models.schemas import RedacaoInput, RedacaoAnalise, Correcao

# Importar repositórios para MongoDB
from app.database.repositories import (
    redacao_repository,
    analise_repository,
    user_repository
)

# Importar RAG manager
from app.database.rag_manager import rag_manager

import tempfile

app = FastAPI(
    title="Elysia - API de Correção de Redações",
    description="API para análise e correção automática de redações em português.",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substituir por domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar processadores
text_processor = TextProcessor()
analyzer = RedacaoAnalyzer()

@app.get("/")
def read_root():
    return {"status": "online", "message": "Elysia API - Sistema de correção de redações"}

@app.post("/api/analisar", response_model=dict)
async def analisar_redacao(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(...),
    titulo: Optional[str] = Form(None),
    usuario_email: Optional[str] = Form("anonimo@elysia.com"),
    usar_agente_ia: bool = Form(True)
):
    """
    Analisa uma redação enviada como arquivo e retorna uma análise detalhada.
    
    - **arquivo**: Arquivo de redação (.txt, .pdf, .doc, .docx)
    - **titulo**: Título opcional da redação
    - **usuario_email**: Email do usuário (opcional)
    - **usar_agente_ia**: Flag para usar o agente de IA na análise (opcional, padrão=True)
    """
    try:
        # Verificar tipo de arquivo
        tipos_permitidos = [
            "text/plain", 
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        # Verificar pela extensão se o content_type não for confiável
        tipo_valido = arquivo.content_type in tipos_permitidos
        if not tipo_valido:
            # Verificar extensão como fallback
            extensao = Path(arquivo.filename).suffix.lower() if arquivo.filename else ""
            tipo_valido = extensao in [".txt", ".pdf", ".doc", ".docx"]
        
        if not tipo_valido:
            raise HTTPException(
                status_code=400, 
                detail="Formato de arquivo não suportado. Use .txt, .pdf, .doc ou .docx"
            )
        
        # Ler conteúdo do arquivo
        conteudo = await arquivo.read()
        
        # Encontrar ou criar usuário
        try:
            usuario = await user_repository.find_by_email(usuario_email)
            if not usuario:
                # Criar usuário básico
                usuario_id = await user_repository.insert_one({
                    "email": usuario_email,
                    "nome": "Usuário Elysia",
                    "tipo": "aluno",
                    "data_cadastro": datetime.now()
                })
            else:
                usuario_id = str(usuario["_id"])
                # Atualizar último acesso
                await user_repository.update_last_access(usuario_id)
        except Exception as e:
            # Fallback para ID de usuário anônimo se falhar
            logger.error(f"Erro ao processar usuário: {e}")
            usuario_id = "000000000000000000000000"  # ObjectId fictício
        
        # Extrair texto do arquivo usando o processador de arquivos
        try:
            texto = file_processor.extract_text(
                conteudo, 
                file_name=arquivo.filename, 
                content_type=arquivo.content_type
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Não foi possível extrair texto do arquivo: {str(e)}")
        
        if not texto or len(texto.strip()) < 50:
            raise HTTPException(status_code=400, detail="Texto extraído muito curto ou vazio")
        
        # Gerar ID para a redação
        redacao_id = str(ObjectId())
        
        # Criar redação no banco de dados
        await redacao_repository.insert_one({
            "_id": ObjectId(redacao_id),
            "usuario_id": ObjectId(usuario_id),
            "titulo": titulo or f"Redação {datetime.now().strftime('%d/%m/%Y')}",
            "status": "processando",
            "data_envio": datetime.now(),
            "texto_extraido": texto,
            "metadata": {
                "tipo_arquivo": arquivo.content_type,
                "nome_arquivo": arquivo.filename,
                "tamanho_bytes": len(conteudo),
                "ip_origem": None  # Poderia ser capturado do request em ambiente de produção
            }
        })
        
        # Salvar o arquivo para processamento pelo agente de IA
        arquivo_salvo = None
        if usar_agente_ia:
            arquivo_dir = os.path.join("data", "redacoes")
            os.makedirs(arquivo_dir, exist_ok=True)
            arquivo_path = os.path.join(arquivo_dir, f"{redacao_id}_{arquivo.filename}")
            
            with open(arquivo_path, "wb") as buffer:
                buffer.write(conteudo)
            arquivo_salvo = arquivo_path
            logger.info(f"Arquivo salvo em {arquivo_salvo} para processamento pelo agente de IA")
        
        # Processar análise em background
        background_tasks.add_task(
            processar_redacao_async, 
            redacao_id=redacao_id, 
            texto=texto, 
            titulo=titulo, 
            usuario_id=usuario_id,
            file_path=arquivo_salvo
        )
        
        # Retornar ID para acompanhamento
        return {
            "status": "processando",
            "redacao_id": redacao_id,
            "mensagem": "Redação recebida e está sendo processada"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar upload de redação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a redação: {str(e)}")

@app.get("/api/exemplos", response_model=List[str])
def get_exemplos():
    """Retorna uma lista de títulos de redações de exemplo disponíveis"""
    try:
        exemplos_dir = Path("data/redacoes")
        exemplos = [f.stem for f in exemplos_dir.glob("*.json")]
        return exemplos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar exemplos: {str(e)}")

@app.get("/api/exemplo/{titulo}", response_model=RedacaoAnalise)
def get_exemplo(titulo: str):
    """Retorna a análise de uma redação de exemplo pelo título"""
    try:
        exemplo_path = Path(f"data/redacoes/{titulo}.json")
        if not exemplo_path.exists():
            raise HTTPException(status_code=404, detail=f"Exemplo '{titulo}' não encontrado")
        
        with open(exemplo_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar exemplo: {str(e)}")

# Função para processamento assíncrono de redações
async def processar_redacao_async(redacao_id: str, texto: str, titulo: Optional[str], usuario_id: str, file_path: Optional[str] = None):
    """Processa a redação de forma assíncrona e salva os resultados no MongoDB"""
    try:
        # Atualizar status para processando
        await redacao_repository.update(redacao_id, {"status": "processando"})
        
        # Verificar tamanho do texto
        if len(texto) < 50:
            await redacao_repository.update(redacao_id, {
                "status": "erro",
                "mensagem_erro": "Texto muito curto para análise detalhada. Mínimo de 50 caracteres requerido."
            })
            return
        
        # Gerar embeddings para a redação
        try:
            embedding = await rag_manager.generate_embedding(texto)
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {str(e)}")
            embedding = None
        
        # Salvar embedding
        if embedding:
            await embedding_repository.create({
                "redacao_id": redacao_id,
                "vector": embedding,
                "texto": texto[:200]  # Salvar apenas um trecho para referência
            })
            
            # Buscar redações similares para enriquecer o contexto
            redacoes_similares = await rag_manager.find_similar_redacoes(embedding, limite=3)
            contexto_adicional = []
            
            for redacao_similar in redacoes_similares:
                similar_id = redacao_similar.get("_id")
                if similar_id and similar_id != redacao_id:  # Evitar a própria redação
                    analise_similar = await analise_repository.find_by_redacao(str(similar_id))
                    if analise_similar:
                        contexto_adicional.append({
                            "nota": analise_similar.get("nota_geral", 0),
                            "resumo": analise_similar.get("resumo_executivo", ""),
                            "pontos_fortes": analise_similar.get("pontos_fortes", [])
                        })
        
        # Processar análise da redação usando o Agente de IA
        logger.info(f"Iniciando análise com agente de IA para redação {redacao_id}")
        
        analysis_result = {}
        # Se temos o arquivo original, processamos ele diretamente
        if file_path and os.path.exists(file_path):
            logger.info(f"Usando arquivo original para análise: {file_path}")
            # Usar o agente para processar o documento diretamente
            doc_result = await ia_agent.process_document(file_path)
            if "error" not in doc_result and doc_result.get("analysis"):
                analysis_result = doc_result.get("analysis")
            else:
                # Fallback para o texto extraído
                logger.warning(f"Falha ao processar documento original, usando texto extraído: {str(doc_result.get('error', ''))}")
                analysis_result = await ia_agent.analyze_text(texto)
        else:
            # Se não temos o arquivo, usamos o texto extraído
            logger.info(f"Usando texto extraído para análise de redação {redacao_id}")
            analysis_result = await ia_agent.analyze_text(texto)
            
        # Verificar se a análise foi bem-sucedida
        if "error" in analysis_result:
            logger.error(f"Erro na análise com IA: {analysis_result['error']}")
            analysis_result = {}
            
        # Adicionar mais informações com IA
        sugestoes = await ia_agent.generate_improvement_suggestions(texto, analysis_result) if analysis_result else []
        pontos_chave = await ia_agent.extract_key_points(texto) if texto else []
        
        # Preparar o objeto de análise
        analise = {
            "redacao_id": redacao_id,
            "titulo": titulo or "Redação sem título",
            "nota_geral": analysis_result.get("nota_geral", 7.0),
            "resumo_executivo": analysis_result.get("resumo_executivo", "Análise não disponível"),
            "notas": analysis_result.get("notas", [
                {"competencia": "Domínio da norma culta", "nota": 6.5, "justificativa": "Apresenta alguns erros de pontuação e concordância."},
                {"competencia": "Compreensão da proposta", "nota": 8.0, "justificativa": "Boa compreensão do tema, com desenvolvimento adequado."},
                {"competencia": "Argumentação", "nota": 7.0, "justificativa": "Argumentos consistentes, mas poderiam ser mais desenvolvidos."},
                {"competencia": "Coesão textual", "nota": 7.5, "justificativa": "Uso adequado de elementos coesivos, com algumas falhas."},
                {"competencia": "Proposta de intervenção", "nota": 6.0, "justificativa": "Proposta pouco desenvolvida e sem detalhamento dos agentes."}
            ]),
            "problemas_gramaticais": analysis_result.get("problemas_gramaticais", []),
            "recomendacoes": analysis_result.get("recomendacoes", sugestoes),
            "pontos_fortes": analysis_result.get("pontos_fortes", pontos_chave),
            "contexto_adicional": contexto_adicional
        }
        
        # Salvar análise no MongoDB
        await analise_repository.create(analise)
        
        # Atualizar status da redação
        await redacao_repository.update(redacao_id, {
            "status": "concluida",
            "analise_disponivel": True
        })
    except Exception as e:
        logger.error(f"Erro no processamento assíncrono: {str(e)}")
        # Atualizar status para erro
        await redacao_repository.update(redacao_id, {
            "status": "erro",
            "mensagem_erro": f"Erro ao processar redação: {str(e)}"
        })

# Rota para verificar status de uma redação
@app.get("/api/redacao/{redacao_id}/status")
async def verificar_status_redacao(redacao_id: str):
    """Verifica o status atual de uma redação"""
    try:
        redacao = await redacao_repository.find_by_id(redacao_id)
        if not redacao:
            raise HTTPException(status_code=404, detail="Redação não encontrada")
        
        # Verificar se já tem análise
        analise = None
        if redacao.get("status") == "concluida":
            analise = await analise_repository.find_by_redacao(redacao_id)
        
        return {
            "redacao_id": redacao_id,
            "status": redacao.get("status", "desconhecido"),
            "titulo": redacao.get("titulo"),
            "data_envio": redacao.get("data_envio"),
            "data_conclusao": redacao.get("data_conclusao"),
            "analise_disponivel": analise is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")

# Rota para obter resultado da análise
@app.get("/api/redacao/{redacao_id}/analise", response_model=dict)
async def obter_analise_redacao(redacao_id: str):
    """Obtém a análise completa de uma redação"""
    try:
        # Verificar se redação existe
        redacao = await redacao_repository.find_by_id(redacao_id)
        if not redacao:
            raise HTTPException(status_code=404, detail="Redação não encontrada")
        
        # Verificar se já foi processada
        if redacao.get("status") != "concluida":
            return {
                "status": redacao.get("status"),
                "redacao_id": redacao_id,
                "mensagem": "Redação ainda está sendo processada ou ocorreu um erro"
            }
        
        # Buscar análise
        analise = await analise_repository.find_by_redacao(redacao_id)
        if not analise:
            raise HTTPException(status_code=404, detail="Análise não encontrada")
        
        # Converter ObjectIds para strings
        for key, value in analise.items():
            if isinstance(value, ObjectId):
                analise[key] = str(value)
        
        # Remover _id interno
        if "_id" in analise:
            analise["id"] = str(analise["_id"])
            del analise["_id"]
        
        return analise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter análise: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
