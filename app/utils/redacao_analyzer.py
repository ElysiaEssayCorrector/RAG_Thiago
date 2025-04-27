import spacy
from typing import List, Dict, Any, Optional, Tuple
import json
import re
import os
from pathlib import Path
import uuid
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import Counter

from app.utils.text_processor import TextProcessor
from app.models.schemas import (
    RedacaoAnalise,
    ProblemaGramatical,
    AnaliseEstrutural,
    AnaliseCoesao,
    AnaliseVocabulario,
    AnaliseArgumentativa,
    NotaAvaliacao,
    MetricasTexto
)

class RedacaoAnalyzer:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.nlp = self.text_processor.nlp
        
        # Carregar base de conhecimento (regras gramaticais, conectivos, etc.)
        self.base_conhecimento = self._carregar_base_conhecimento()
        
        # Carregar exemplos de redações para RAG
        self.exemplos = self._carregar_exemplos()
    
    def _carregar_base_conhecimento(self) -> Dict[str, Any]:
        """Carrega base de conhecimento com regras gramaticais e padrões textuais"""
        # Em um sistema real, isto seria carregado de um arquivo ou banco de dados
        return {
            "conectivos": {
                "adição": ["além disso", "ademais", "outrossim", "também", "e", "bem como"],
                "conclusão": ["portanto", "logo", "assim", "dessa forma", "por conseguinte"],
                "contraste": ["entretanto", "contudo", "todavia", "no entanto", "porém", "mas"],
                "causa": ["porque", "visto que", "já que", "uma vez que", "pois"],
                "consequência": ["de modo que", "de forma que", "tanto que", "por isso"],
                "condição": ["se", "caso", "desde que", "contanto que", "a menos que"],
                "finalidade": ["para que", "a fim de que", "com o intuito de", "com o propósito de"],
                "tempo": ["quando", "enquanto", "assim que", "logo que", "antes que", "depois que"],
                "explicação": ["isto é", "ou seja", "em outras palavras", "a saber"]
            },
            "problemas_comuns": {
                "concordância": [
                    {"padrão": r"os ([a-zà-ú]+ção)", "correção": "as", "explicação": "Substantivos terminados em -ção são femininos"},
                    {"padrão": r"as ([a-zà-ú]+mento)", "correção": "os", "explicação": "Substantivos terminados em -mento são masculinos"}
                ],
                "regência": [
                    {"padrão": r"assistir (o|a|os|as) ", "correção": "assistir a ", "explicação": "O verbo assistir no sentido de ver requer preposição 'a'"},
                    {"padrão": r"visar (o|a|os|as) ", "correção": "visar a ", "explicação": "O verbo visar no sentido de almejar requer preposição 'a'"}
                ],
                "crase": [
                    {"padrão": r"a (a|as) ", "correção": "à ", "explicação": "Ocorre crase quando há fusão da preposição 'a' com artigo feminino 'a'"},
                    {"padrão": r"refere-se a (a|as) ", "correção": "refere-se à ", "explicação": "Verbos com complemento indireto exigem preposição 'a', formando crase com artigo feminino"}
                ]
            },
            "estrutura_redacao": {
                "introdução": {
                    "tamanho_ideal": (1, 1),  # (min, max) em parágrafos
                    "elementos": ["contextualização", "tese", "apresentação dos argumentos"]
                },
                "desenvolvimento": {
                    "tamanho_ideal": (2, 3),  # (min, max) em parágrafos
                    "elementos": ["tópico frasal", "argumento", "exemplo", "conclusão parcial"]
                },
                "conclusão": {
                    "tamanho_ideal": (1, 1),  # (min, max) em parágrafos
                    "elementos": ["retomada da tese", "resumo dos argumentos", "solução", "projeção futura"]
                }
            }
        }
    
    def _carregar_exemplos(self) -> List[Dict[str, Any]]:
        """Carrega exemplos de redações para RAG"""
        exemplos = []
        redacoes_dir = Path("data/redacoes")
        
        if not redacoes_dir.exists():
            return exemplos
        
        for filepath in redacoes_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    exemplos.append(json.load(f))
            except Exception as e:
                print(f"Erro ao carregar exemplo {filepath}: {e}")
        
        return exemplos
