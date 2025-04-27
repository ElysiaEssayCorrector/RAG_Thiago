from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

class MongoDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
            cls._instance.initialize_connection()
        return cls._instance
    
    def initialize_connection(self):
        """Inicializa a conexão com MongoDB"""
        try:
            # Obter URI de conexão das variáveis de ambiente ou usar padrão local
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.getenv("MONGODB_DBNAME", "elysia")
            
            # Conectar ao MongoDB
            self.client = MongoClient(mongo_uri)
            
            # Verificar conexão
            self.client.admin.command('ping')
            
            # Acessar o banco de dados
            self.db = self.client[db_name]
            
            logger.info(f"Conexão com MongoDB estabelecida: {db_name}")
            
            # Inicializar índices e coleções
            self._setup_collections()
            
        except ConnectionFailure as e:
            logger.error(f"Falha ao conectar ao MongoDB: {e}")
            raise
    
    def _setup_collections(self):
        """Configura coleções e índices necessários"""
        # Coleção de usuários
        if "users" not in self.db.list_collection_names():
            self.db.create_collection("users")
        
        # Índices para usuários
        self.db.users.create_index("email", unique=True)
        
        # Coleção de redações
        if "redacoes" not in self.db.list_collection_names():
            self.db.create_collection("redacoes")
        
        # Índices para redações
        self.db.redacoes.create_index("usuario_id")
        self.db.redacoes.create_index("data_envio")
        self.db.redacoes.create_index("status")
        
        # Coleção de análises
        if "analises" not in self.db.list_collection_names():
            self.db.create_collection("analises")
        
        # Índices para análises
        self.db.analises.create_index("redacao_id")
        self.db.analises.create_index("usuario_id")
        
        # Coleção de embeddings para RAG
        if "embeddings" not in self.db.list_collection_names():
            self.db.create_collection("embeddings")
        
        # Índices para embeddings - incluindo índice vetorial se disponível
        self.db.embeddings.create_index("redacao_id", unique=True)
        
        try:
            # Criar índice vetorial (MongoDB 5.0+ com Atlas)
            self.db.command({
                "createIndexes": "embeddings",
                "indexes": [{
                    "name": "vector_index",
                    "key": {"vector_embedding": "vector"},
                    "vectorOptions": {"dimension": 1536, "similarity": "cosine"}
                }]
            })
            logger.info("Índice vetorial criado com sucesso")
        except OperationFailure as e:
            logger.warning(f"Não foi possível criar índice vetorial: {e}")
            logger.info("Índice vetorial não disponível - usando busca alternativa")
        
        # Coleção de corpus de exemplos
        if "corpus_exemplos" not in self.db.list_collection_names():
            self.db.create_collection("corpus_exemplos")
        
        # Índices para corpus
        self.db.corpus_exemplos.create_index("categoria")
        self.db.corpus_exemplos.create_index([("texto", "text")])
        
        # Coleção de feedback
        if "feedbacks" not in self.db.list_collection_names():
            self.db.create_collection("feedbacks")
        
        # Índices para feedback
        self.db.feedbacks.create_index("analise_id")
        
        logger.info("Configuração de coleções e índices concluída")
    
    def get_db(self):
        """Retorna a referência ao banco de dados"""
        if not self.db:
            self.initialize_connection()
        return self.db
    
    def close(self):
        """Fecha a conexão com o MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Conexão com MongoDB fechada")

# Singleton para uso em toda a aplicação
mongo_client = MongoDB()

# Função auxiliar para obter o banco de dados
def get_db():
    return mongo_client.get_db()
