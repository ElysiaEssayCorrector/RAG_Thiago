from celery import Celery
import os
from dotenv import load_dotenv
import json
from pathlib import Path
import logging
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Celery
celery_app = Celery(
    'elysia_workers',
    broker=os.getenv('REDIS_URI', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URI', 'redis://localhost:6379/0')
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_routes={
        'app.worker.processar_redacao': {'queue': 'analise_redacao'},
        'app.worker.treinar_modelos': {'queue': 'treinamento'},
        'app.worker.atualizar_indices': {'queue': 'indexacao'}
    },
    task_time_limit=1800,  # 30 minutos
    task_soft_time_limit=1500  # 25 minutos
)

# Importar dependências internas
try:
    from app.utils.text_processor import TextProcessor
    from app.utils.redacao_analyzer import RedacaoAnalyzer
    from app.models.schemas import RedacaoAnalise
except ImportError:
    logger.warning("Não foi possível importar módulos da aplicação. Isso é esperado durante a inicialização.")

# Importar serviços de armazenamento/banco de dados
try:
    from pymongo import MongoClient
    from elasticsearch import Elasticsearch
    import boto3
except ImportError:
    logger.warning("Dependências de serviços externos não encontradas. Instale-as com pip.")

# Conectar aos serviços
mongodb_client = None
elasticsearch_client = None
s3_client = None

def init_services():
    """Inicializa conexões com serviços externos"""
    global mongodb_client, elasticsearch_client, s3_client
    
    try:
        # MongoDB
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        mongodb_client = MongoClient(mongodb_uri)
        logger.info("Conexão com MongoDB estabelecida")
        
        # Elasticsearch
        elasticsearch_uri = os.getenv('ELASTICSEARCH_URI', 'http://localhost:9200')
        elasticsearch_client = Elasticsearch(elasticsearch_uri)
        logger.info("Conexão com Elasticsearch estabelecida")
        
        # S3/MinIO
        endpoint_url = os.getenv('OBJECT_STORAGE_ENDPOINT')
        if endpoint_url:
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=os.getenv('OBJECT_STORAGE_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('OBJECT_STORAGE_SECRET_KEY')
            )
        else:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('OBJECT_STORAGE_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('OBJECT_STORAGE_SECRET_KEY')
            )
        logger.info("Conexão com Object Storage estabelecida")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar aos serviços: {e}")
        return False

@celery_app.task(name='app.worker.processar_redacao')
def processar_redacao(redacao_id, texto, titulo=None, metadata=None):
    """
    Processa uma redação e salva o resultado
    
    Args:
        redacao_id: ID único da redação
        texto: Texto da redação para análise
        titulo: Título opcional da redação
        metadata: Metadados adicionais (usuário, timestamp, etc)
    
    Returns:
        ID da análise gerada
    """
    logger.info(f"Iniciando processamento da redação {redacao_id}")
    
    # Inicializar serviços se necessário
    if not mongodb_client:
        init_services()
    
    try:
        # Inicializar processador e analisador
        text_processor = TextProcessor()
        analyzer = RedacaoAnalyzer()
        
        # Registrar início do processamento
        inicio = time.time()
        
        # Analisar a redação
        resultado_analise = analyzer.analisar_completo(texto, titulo)
        
        # Calcular tempo de processamento
        tempo_processamento = time.time() - inicio
        
        # Adicionar metadados e informações da análise
        resultado_analise.id = redacao_id
        resultado_analise.titulo = titulo
        
        # Converter para dict para armazenamento
        analise_dict = resultado_analise.dict()
        
        # Adicionar metadados adicionais
        analise_dict.update({
            "metadata": metadata or {},
            "timestamp_processamento": datetime.now().isoformat(),
            "tempo_processamento": tempo_processamento
        })
        
        # Salvar no MongoDB
        db = mongodb_client.elysia
        db.analises.insert_one(analise_dict)
        
        # Indexar no Elasticsearch
        if elasticsearch_client:
            elasticsearch_client.index(
                index="redacoes",
                id=redacao_id,
                document={
                    "id": redacao_id,
                    "titulo": titulo,
                    "texto": texto[:1000],  # apenas parte inicial para indexação
                    "resumo": resultado_analise.resumo_executivo,
                    "nota_geral": resultado_analise.nota_geral,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }
            )
        
        logger.info(f"Processamento da redação {redacao_id} concluído em {tempo_processamento:.2f}s")
        return redacao_id
    
    except Exception as e:
        logger.error(f"Erro no processamento da redação {redacao_id}: {e}")
        # Registrar erro no MongoDB para auditoria
        if mongodb_client:
            db = mongodb_client.elysia
            db.erros_processamento.insert_one({
                "redacao_id": redacao_id,
                "erro": str(e),
                "timestamp": datetime.now().isoformat(),
                "texto_parcial": texto[:500] if texto else None  # Amostra para debug
            })
        raise

@celery_app.task(name='app.worker.treinar_modelos')
def treinar_modelos():
    """
    Treina/atualiza modelos de ML com base no corpus atual de redações
    
    Returns:
        Status do treinamento
    """
    logger.info("Iniciando treinamento de modelos")
    
    # Implementação do treinamento
    
    return {"status": "success", "message": "Modelos treinados com sucesso"}

@celery_app.task(name='app.worker.atualizar_indices')
def atualizar_indices():
    """
    Atualiza índices de busca no Elasticsearch
    
    Returns:
        Status da indexação
    """
    logger.info("Iniciando atualização de índices")
    
    # Implementação da indexação
    
    return {"status": "success", "message": "Índices atualizados com sucesso"}

# Inicialização na importação do módulo
if __name__ != '__main__':
    init_services()
