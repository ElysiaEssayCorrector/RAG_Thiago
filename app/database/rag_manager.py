import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from bson import ObjectId

# OpenAI para geração de embeddings
from openai import OpenAI

# Importar cliente MongoDB
from app.database.mongo_client import get_db
from app.database.models import (
    EmbeddingModel,
    RedacaoModel,
    CorpusExemploModel
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGManager:
    def __init__(self):
        # Obter conexão com MongoDB
        self.db = get_db()
        
        # Inicializar cliente OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY não encontrada. Algumas funcionalidades RAG estarão limitadas.")
        
        self.openai_client = OpenAI(api_key=api_key) if api_key else None
        
        # Verificar se há suporte a índice vetorial
        self.has_vector_search = self._check_vector_search()
    
    def _check_vector_search(self) -> bool:
        """Verifica se o MongoDB suporta busca vetorial"""
        try:
            # Tenta uma consulta simples para verificar se o índice vetorial está disponível
            _ = self.db.command({
                "listSearchIndexes": "embeddings",
                "name": "vector_index"
            })
            return True
        except Exception as e:
            logger.warning(f"Busca vetorial não disponível: {e}")
            return False
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para o texto usando OpenAI API
        
        Args:
            text: Texto para gerar embedding
        
        Returns:
            Lista de floats representando o embedding
        """
        if not self.openai_client:
            raise ValueError("OpenAI API não configurada. Defina OPENAI_API_KEY.")
        
        try:
            # Processar texto para embedding (limitar tamanho para evitar tokens excessivos)
            text = text[:8000]  # Limitar para evitar exceder limite de tokens
            
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            # Fallback: embedding de zeros (não ideal, apenas para evitar falhas completas)
            return [0.0] * 1536  # Dimensão do modelo text-embedding-3-small
    
    async def store_redacao_embedding(self, redacao_id: str, texto: str, titulo: Optional[str] = None) -> str:
        """
        Gera e armazena embedding para uma redação
        
        Args:
            redacao_id: ID da redação no MongoDB
            texto: Texto completo da redação
            titulo: Título opcional da redação
        
        Returns:
            ID do embedding armazenado
        """
        try:
            # Converter string para ObjectId
            redacao_obj_id = ObjectId(redacao_id)
            
            # Verificar se já existe embedding para esta redação
            existing = self.db.embeddings.find_one({"redacao_id": redacao_obj_id})
            if existing:
                logger.info(f"Embedding já existe para redação {redacao_id}. Atualizando...")
                # Atualizar com novo embedding
                embedding_vector = self.generate_embedding(texto)
                
                self.db.embeddings.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "vector_embedding": embedding_vector,
                        "texto_snippet": texto[:1000],
                        "titulo": titulo,
                        "data_criacao": datetime.now()
                    }}
                )
                
                return str(existing["_id"])
            
            # Criar novo embedding
            embedding_vector = self.generate_embedding(texto)
            
            # Criar documento de embedding
            embedding_doc = {
                "redacao_id": redacao_obj_id,
                "titulo": titulo,
                "texto_snippet": texto[:1000],  # Primeiros 1000 caracteres para exibição
                "vector_embedding": embedding_vector,
                "modelo_embedding": "text-embedding-3-small",
                "data_criacao": datetime.now(),
                "metadata": {}
            }
            
            # Inserir no MongoDB
            result = self.db.embeddings.insert_one(embedding_doc)
            
            logger.info(f"Embedding armazenado para redação {redacao_id}")
            return str(result.inserted_id)
        
        except Exception as e:
            logger.error(f"Erro ao armazenar embedding: {e}")
            raise
    
    async def vector_search(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Realiza busca vetorial por similaridade
        
        Args:
            query_text: Texto da consulta
            limit: Número máximo de resultados
        
        Returns:
            Lista de documentos similares
        """
        # Gerar embedding para a consulta
        query_embedding = self.generate_embedding(query_text)
        
        results = []
        
        # Se tiver índice vetorial disponível, usar busca nativa
        if self.has_vector_search:
            try:
                # Consulta usando o operador $vectorSearch
                pipeline = [
                    {
                        "$vectorSearch": {
                            "index": "vector_index",
                            "queryVector": query_embedding,
                            "path": "vector_embedding",
                            "numCandidates": limit * 10,
                            "limit": limit
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "redacao_id": 1,
                            "titulo": 1,
                            "texto_snippet": 1,
                            "score": {"$meta": "vectorSearchScore"}
                        }
                    }
                ]
                
                results = list(self.db.embeddings.aggregate(pipeline))
                
            except Exception as e:
                logger.error(f"Erro na busca vetorial: {e}")
                # Fallback para busca alternativa
        
        # Se não tiver índice vetorial ou falhar, usar método alternativo
        if not results:
            # Buscar todos os embeddings
            all_embeddings = list(self.db.embeddings.find({}, {
                "_id": 1,
                "redacao_id": 1, 
                "titulo": 1,
                "texto_snippet": 1,
                "vector_embedding": 1
            }))
            
            # Calcular similaridade manualmente
            similarities = []
            for doc in all_embeddings:
                if "vector_embedding" in doc:
                    # Calcular similaridade de cosseno
                    doc_vector = doc["vector_embedding"]
                    similarity = self._cosine_similarity(query_embedding, doc_vector)
                    
                    similarities.append({
                        "_id": doc["_id"],
                        "redacao_id": doc["redacao_id"],
                        "titulo": doc.get("titulo"),
                        "texto_snippet": doc.get("texto_snippet", ""),
                        "score": similarity
                    })
            
            # Ordenar por similaridade e pegar os top N
            similarities.sort(key=lambda x: x["score"], reverse=True)
            results = similarities[:limit]
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        
        return dot_product / (norm_vec1 * norm_vec2)
    
    async def get_similar_redacoes(self, texto: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Busca redações similares baseadas no texto fornecido
        
        Args:
            texto: Texto para comparar
            limit: Número máximo de resultados
        
        Returns:
            Lista de redações similares com análises
        """
        # Buscar embeddings similares
        similar_embeddings = await self.vector_search(texto, limit=limit)
        
        result_redacoes = []
        
        for emb in similar_embeddings:
            try:
                redacao_id = emb["redacao_id"]
                
                # Buscar redação
                redacao = self.db.redacoes.find_one({"_id": redacao_id})
                
                if not redacao:
                    continue
                
                # Buscar análise da redação
                analise = self.db.analises.find_one({"redacao_id": redacao_id})
                
                # Montar resultado
                result = {
                    "id": str(redacao["_id"]),
                    "titulo": redacao.get("titulo", "Sem título"),
                    "texto_snippet": emb.get("texto_snippet", ""),
                    "similarity_score": emb.get("score", 0),
                }
                
                # Adicionar análise se disponível
                if analise:
                    result["analise"] = {
                        "nota_geral": analise.get("nota_geral", 0),
                        "resumo": analise.get("resumo_executivo", ""),
                        "principais_recomendacoes": analise.get("recomendacoes", [])[:3]
                    }
                
                result_redacoes.append(result)
                
            except Exception as e:
                logger.error(f"Erro ao processar redação similar: {e}")
        
        return result_redacoes
    
    async def enrich_with_rag(self, texto: str) -> Dict[str, Any]:
        """
        Enriquece a análise de uma redação usando técnicas RAG
        
        Args:
            texto: Texto da redação
        
        Returns:
            Dicionário com informações contextuais baseadas em RAG
        """
        # Buscar redações similares
        similares = await self.get_similar_redacoes(texto, limit=5)
        
        # Buscar exemplos de alta qualidade do corpus
        exemplos_query = {
            "nivel_qualidade": {"$gte": 8.0},
            "categoria": "exemplar"
        }
        
        exemplos = list(self.db.corpus_exemplos.find(exemplos_query).limit(2))
        
        # Preparar contexto RAG
        rag_context = {
            "redacoes_similares": similares,
            "exemplos_alta_qualidade": [
                {
                    "id": str(ex["_id"]),
                    "titulo": ex.get("titulo", ""),
                    "nivel_qualidade": ex.get("nivel_qualidade", 0),
                    "temas": ex.get("temas", [])
                }
                for ex in exemplos
            ],
            "recomendacoes_contextuais": self._gerar_recomendacoes_contextuais(similares)
        }
        
        return rag_context
    
    def _gerar_recomendacoes_contextuais(self, similares: List[Dict[str, Any]]) -> List[str]:
        """Gera recomendações baseadas nas redações similares"""
        all_recomendacoes = []
        
        for similar in similares:
            if "analise" in similar and "principais_recomendacoes" in similar["analise"]:
                all_recomendacoes.extend(similar["analise"]["principais_recomendacoes"])
        
        # Remover duplicatas
        unique_recomendacoes = list(set(all_recomendacoes))
        
        # Retornar as 5 principais recomendações
        return unique_recomendacoes[:5]

# Instância única para uso na aplicação
rag_manager = RAGManager()
