from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from bson import ObjectId
import logging

from app.database.mongo_client import get_db
from app.database.models import (
    UserModel,
    RedacaoModel,
    AnaliseModel,
    EmbeddingModel,
    CorpusExemploModel,
    FeedbackModel
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseRepository:
    """Repositório base com operações comuns para todas as coleções"""
    
    def __init__(self, collection_name: str):
        self.db = get_db()
        self.collection = self.db[collection_name]
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Busca documento por ID"""
        try:
            result = self.collection.find_one({"_id": ObjectId(id)})
            return result
        except Exception as e:
            logger.error(f"Erro ao buscar documento por ID: {e}")
            return None
    
    async def find_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca um documento que corresponda ao filtro"""
        try:
            return self.collection.find_one(filter)
        except Exception as e:
            logger.error(f"Erro na busca find_one: {e}")
            return None
    
    async def find_many(self, filter: Dict[str, Any], limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Busca múltiplos documentos que correspondam ao filtro"""
        try:
            cursor = self.collection.find(filter).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Erro na busca find_many: {e}")
            return []
    
    async def insert_one(self, document: Dict[str, Any]) -> Optional[str]:
        """Insere um documento e retorna o ID"""
        try:
            result = self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao inserir documento: {e}")
            return None
    
    async def update_one(self, id: str, update_data: Dict[str, Any]) -> bool:
        """Atualiza um documento por ID"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erro ao atualizar documento: {e}")
            return False
    
    async def delete_one(self, id: str) -> bool:
        """Deleta um documento por ID"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erro ao deletar documento: {e}")
            return False
    
    async def count(self, filter: Dict[str, Any] = None) -> int:
        """Conta documentos que correspondem ao filtro"""
        try:
            return self.collection.count_documents(filter or {})
        except Exception as e:
            logger.error(f"Erro ao contar documentos: {e}")
            return 0


class UserRepository(BaseRepository):
    """Repositório para operações de usuário"""
    
    def __init__(self):
        super().__init__("users")
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        return await self.find_one({"email": email})
    
    async def update_last_access(self, user_id: str) -> bool:
        """Atualiza a data de último acesso"""
        return await self.update_one(user_id, {"ultimo_acesso": datetime.now()})


class RedacaoRepository(BaseRepository):
    """Repositório para operações de redação"""
    
    def __init__(self):
        super().__init__("redacoes")
    
    async def find_by_user(self, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """Busca redações de um usuário"""
        return await self.find_many({"usuario_id": ObjectId(user_id)}, limit=limit, skip=skip)
    
    async def update_status(self, redacao_id: str, status: str) -> bool:
        """Atualiza o status da redação"""
        update_data = {"status": status}
        
        # Se status for concluída, atualizar data_conclusao
        if status == "concluida":
            update_data["data_conclusao"] = datetime.now()
            
        return await self.update_one(redacao_id, update_data)
    
    async def find_pendentes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca redações pendentes para processamento"""
        return await self.find_many({"status": "pendente"}, limit=limit)


class AnaliseRepository(BaseRepository):
    """Repositório para operações de análise"""
    
    def __init__(self):
        super().__init__("analises")
    
    async def find_by_redacao(self, redacao_id: str) -> Optional[Dict[str, Any]]:
        """Busca análise por ID da redação"""
        return await self.find_one({"redacao_id": ObjectId(redacao_id)})
    
    async def find_by_user(self, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """Busca análises de um usuário"""
        return await self.find_many({"usuario_id": ObjectId(user_id)}, limit=limit, skip=skip)


class EmbeddingRepository(BaseRepository):
    """Repositório para operações de embedding"""
    
    def __init__(self):
        super().__init__("embeddings")
    
    async def find_by_redacao(self, redacao_id: str) -> Optional[Dict[str, Any]]:
        """Busca embedding por ID da redação"""
        return await self.find_one({"redacao_id": ObjectId(redacao_id)})


class CorpusExemploRepository(BaseRepository):
    """Repositório para operações de corpus de exemplos"""
    
    def __init__(self):
        super().__init__("corpus_exemplos")
    
    async def find_by_categoria(self, categoria: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca exemplos por categoria"""
        return await self.find_many({"categoria": categoria}, limit=limit)
    
    async def find_by_temas(self, temas: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Busca exemplos por temas"""
        return await self.find_many({"temas": {"$in": temas}}, limit=limit)
    
    async def find_high_quality(self, min_nivel: float = 8.0, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca exemplos de alta qualidade"""
        return await self.find_many({"nivel_qualidade": {"$gte": min_nivel}}, limit=limit)


class FeedbackRepository(BaseRepository):
    """Repositório para operações de feedback"""
    
    def __init__(self):
        super().__init__("feedbacks")
    
    async def find_by_analise(self, analise_id: str) -> List[Dict[str, Any]]:
        """Busca feedbacks por ID da análise"""
        return await self.find_many({"analise_id": ObjectId(analise_id)})


# Instâncias dos repositórios para uso na aplicação
user_repository = UserRepository()
redacao_repository = RedacaoRepository()
analise_repository = AnaliseRepository()
embedding_repository = EmbeddingRepository()
corpus_repository = CorpusExemploRepository()
feedback_repository = FeedbackRepository()
