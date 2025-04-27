from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class ProblemaGramatical(BaseModel):
    tipo: str
    texto_original: str
    sugestao: str
    explicacao: str
    posicao: tuple = Field(..., description="Posição (início, fim) do problema no texto")

class AnaliseEstrutural(BaseModel):
    introducao: Dict[str, Any] = Field(..., description="Análise da introdução")
    desenvolvimento: Dict[str, Any] = Field(..., description="Análise do desenvolvimento")
    conclusao: Dict[str, Any] = Field(..., description="Análise da conclusão")
    proporcao: Dict[str, float] = Field(..., description="Proporção de cada parte do texto")

class AnaliseCoesao(BaseModel):
    conectivos_utilizados: List[Dict[str, Any]] = Field(..., description="Conectivos utilizados no texto")
    repeticoes_excessivas: List[Dict[str, Any]] = Field(..., description="Repetições excessivas identificadas")
    qualidade_transicao: Dict[str, Any] = Field(..., description="Qualidade das transições entre parágrafos")

class AnaliseVocabulario(BaseModel):
    riqueza_lexical: float = Field(..., description="Índice de riqueza lexical")
    palavras_incomuns: List[str] = Field(..., description="Palavras menos comuns utilizadas")
    registro_linguistico: str = Field(..., description="Classificação do registro linguístico")
    sugestoes_vocabulario: List[Dict[str, Any]] = Field(..., description="Sugestões de enriquecimento vocabular")

class AnaliseArgumentativa(BaseModel):
    argumentos_identificados: List[Dict[str, Any]] = Field(..., description="Argumentos identificados")
    qualidade_argumentativa: Dict[str, Any] = Field(..., description="Avaliação da qualidade argumentativa")
    fontes_citadas: List[str] = Field(..., description="Possíveis fontes ou referências citadas")

class NotaAvaliacao(BaseModel):
    competencia: str
    nota: float
    justificativa: str
    pontos_fortes: List[str]
    pontos_melhorar: List[str]

class MetricasTexto(BaseModel):
    num_palavras: int
    num_sentencas: int
    num_paragrafos: int
    tamanho_medio_sentencas: float
    tamanho_medio_palavras: float
    tipo_palavras: Dict[str, int]

class Correcao(BaseModel):
    texto_original: str
    texto_corrigido: str
    problemas: List[ProblemaGramatical]

class RedacaoInput(BaseModel):
    texto: str
    titulo: Optional[str] = None

class RedacaoAnalise(BaseModel):
    id: Optional[str] = None
    titulo: Optional[str] = None
    texto_original: str
    texto_corrigido: str
    resumo_executivo: str = Field(..., description="Resumo dos principais pontos da análise")
    metricas: MetricasTexto
    problemas_gramaticais: List[ProblemaGramatical] = Field(..., description="Lista de problemas gramaticais identificados")
    analise_estrutural: AnaliseEstrutural
    analise_coesao: AnaliseCoesao
    analise_vocabulario: AnaliseVocabulario
    analise_argumentativa: AnaliseArgumentativa
    notas: List[NotaAvaliacao] = Field(..., description="Notas por competência")
    nota_geral: float
    recomendacoes: List[str] = Field(..., description="Recomendações para melhoria")
