from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


# Classe auxiliar para lidar com ObjectId do MongoDB
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("ObjectId inválido")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# Modelo Base com ID MongoDB
class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }


# Modelo de Usuário
class UserModel(MongoBaseModel):
    email: EmailStr
    nome: str
    tipo: str = Field(..., description="professor|aluno|admin")
    instituicao: Optional[str] = None
    data_cadastro: datetime = Field(default_factory=datetime.now)
    ultimo_acesso: Optional[datetime] = None
    configuracoes: Dict[str, Any] = Field(default_factory=dict)


# Modelo de Metadados
class MetadataModel(BaseModel):
    tipo_arquivo: Optional[str] = None
    tamanho_bytes: Optional[int] = None
    origem: Optional[str] = None
    ip_origem: Optional[str] = None
    sessao_id: Optional[str] = None


# Modelo de Redação
class RedacaoModel(MongoBaseModel):
    usuario_id: PyObjectId
    titulo: Optional[str] = None
    status: str = "pendente"  # pendente|processando|concluida|erro
    data_envio: datetime = Field(default_factory=datetime.now)
    data_conclusao: Optional[datetime] = None
    objeto_url: Optional[str] = None
    texto_extraido: str
    metadata: Optional[MetadataModel] = Field(default_factory=MetadataModel)


# Modelos para análise de redações
class ProblemaGramaticalModel(BaseModel):
    tipo: str
    texto_original: str
    sugestao: str
    explicacao: str
    posicao: List[int]


class AnaliseEstruturalModel(BaseModel):
    introducao: Dict[str, Any]
    desenvolvimento: Dict[str, Any]
    conclusao: Dict[str, Any]
    proporcao: Dict[str, float]


class AnaliseCoesaoModel(BaseModel):
    conectivos_utilizados: List[Dict[str, Any]]
    repeticoes_excessivas: List[Dict[str, Any]]
    qualidade_transicao: Dict[str, Any]


class AnaliseVocabularioModel(BaseModel):
    riqueza_lexical: float
    palavras_incomuns: List[str]
    registro_linguistico: str
    sugestoes_vocabulario: List[Dict[str, Any]]


class AnaliseArgumentativaModel(BaseModel):
    argumentos_identificados: List[Dict[str, Any]]
    qualidade_argumentativa: Dict[str, Any]
    fontes_citadas: List[str]


class MetricasTextoModel(BaseModel):
    num_palavras: int
    num_sentencas: int
    num_paragrafos: int
    tamanho_medio_sentencas: float
    tamanho_medio_palavras: float
    tipo_palavras: Dict[str, int]


class NotaAvaliacaoModel(BaseModel):
    competencia: str
    nota: float
    justificativa: str
    pontos_fortes: List[str]
    pontos_melhorar: List[str]


# Modelo completo de Análise
class AnaliseModel(MongoBaseModel):
    redacao_id: PyObjectId
    usuario_id: PyObjectId
    texto_original: str
    texto_corrigido: str
    resumo_executivo: str
    metricas: MetricasTextoModel
    problemas_gramaticais: List[ProblemaGramaticalModel]
    analise_estrutural: AnaliseEstruturalModel
    analise_coesao: AnaliseCoesaoModel
    analise_vocabulario: AnaliseVocabularioModel
    analise_argumentativa: AnaliseArgumentativaModel
    notas: List[NotaAvaliacaoModel]
    nota_geral: float
    recomendacoes: List[str]
    data_analise: datetime = Field(default_factory=datetime.now)
    tempo_processamento_ms: Optional[int] = None


# Modelo de Embedding para RAG
class EmbeddingModel(MongoBaseModel):
    redacao_id: PyObjectId
    titulo: Optional[str] = None
    texto_snippet: str  # Primeiros 1000 caracteres para exibição
    vector_embedding: List[float]
    modelo_embedding: str = "text-embedding-3-small"  # Modelo usado para gerar o embedding
    data_criacao: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Modelo de Corpus de Exemplos
class CorpusExemploModel(MongoBaseModel):
    titulo: str
    texto: str
    analise_id: Optional[PyObjectId] = None
    categoria: str = "comum"  # exemplar|comum|problematico
    temas: List[str] = Field(default_factory=list)
    nivel_qualidade: float
    vector_embedding: Optional[List[float]] = None
    data_adicao: datetime = Field(default_factory=datetime.now)


# Modelo de Feedback
class FeedbackModel(MongoBaseModel):
    analise_id: PyObjectId
    usuario_id: PyObjectId
    avaliacao: str  # util|parcial|inutil
    comentario: Optional[str] = None
    data_feedback: datetime = Field(default_factory=datetime.now)
