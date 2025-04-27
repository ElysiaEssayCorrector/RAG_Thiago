import spacy
from typing import List, Dict, Any, Optional, Tuple
import re
import os
from pathlib import Path
import string
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Garantir que recursos NLTK estejam baixados
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class TextProcessor:
    def __init__(self):
        # Carregar modelo spaCy para português
        try:
            self.nlp = spacy.load("pt_core_news_lg")
        except OSError:
            # Caso o modelo não esteja instalado
            print("Modelo spaCy pt_core_news_lg não encontrado. Instalando...")
            os.system("python -m spacy download pt_core_news_lg")
            self.nlp = spacy.load("pt_core_news_lg")
        
        # Configurar stop words
        self.stopwords = set(stopwords.words('portuguese'))
        
        # Inicializar o vetorizador TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents='unicode',
            stop_words=list(self.stopwords),
            ngram_range=(1, 3)
        )
        
        # Carregar corpus de redações (se existir)
        self.corpus = self._load_corpus()
        
        # Treinar vetorizador se houver corpus
        if self.corpus:
            self._train_tfidf()
    
    def _load_corpus(self) -> List[str]:
        """Carrega o corpus de redações existentes"""
        corpus = []
        redacoes_dir = Path("data/redacoes")
        
        if not redacoes_dir.exists():
            return corpus
        
        # Carregar redações de exemplo
        for filepath in redacoes_dir.glob("*.json"):
            try:
                import json
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "texto_original" in data:
                        corpus.append(data["texto_original"])
            except Exception as e:
                print(f"Erro ao carregar {filepath}: {e}")
        
        return corpus
    
    def _train_tfidf(self):
        """Treina o vetorizador TF-IDF com o corpus disponível"""
        if not self.corpus:
            return
        
        try:
            self.tfidf_vectorizer.fit(self.corpus)
            print(f"TF-IDF treinado com {len(self.corpus)} documentos")
        except Exception as e:
            print(f"Erro ao treinar TF-IDF: {e}")
    
    def extract_text_from_file(self, file_path: str, content_type: str) -> str:
        """
        Extrai texto de diferentes formatos de arquivo
        
        Args:
            file_path: Caminho para o arquivo
            content_type: Tipo MIME do arquivo
        
        Returns:
            Texto extraído
        """
        if content_type == "text/plain":
            # Arquivo TXT
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        
        elif content_type == "application/pdf":
            # Arquivo PDF
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                print("PyPDF2 não está instalado. Instale com: pip install PyPDF2")
                return ""
        
        elif content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # Arquivos DOC/DOCX
            try:
                import docx
                doc = docx.Document(file_path)
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
            except ImportError:
                print("python-docx não está instalado. Instale com: pip install python-docx")
                return ""
        
        return ""
    
    def preprocess_text(self, text: str) -> str:
        """Pré-processa o texto removendo caracteres especiais e normalizando"""
        # Remover múltiplos espaços em branco
        text = re.sub(r'\s+', ' ', text)
        
        # Remover URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Normalizar quebras de linha
        text = re.sub(r'\n+', '\n', text)
        
        # Normalizar espaços após pontuação
        for punct in string.punctuation:
            text = text.replace(f"{punct} ", f"{punct} ")
        
        return text.strip()
    
    def get_paragraphs(self, text: str) -> List[str]:
        """Divide o texto em parágrafos"""
        # Usar quebras de linha como separador de parágrafos
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        return paragraphs
    
    def get_sentences(self, text: str) -> List[str]:
        """Divide o texto em sentenças usando NLTK"""
        return sent_tokenize(text, language='portuguese')
    
    def analyze_with_spacy(self, text: str) -> Any:
        """Processa o texto com SpaCy e retorna o documento processado"""
        return self.nlp(text)
    
    def extract_noun_phrases(self, doc) -> List[str]:
        """Extrai sintagmas nominais do texto"""
        return [chunk.text for chunk in doc.noun_chunks]
    
    def calculate_tfidf(self, text: str) -> Dict[str, float]:
        """
        Calcula TF-IDF para termos do texto em relação ao corpus
        
        Returns:
            Dicionário com termos e seus valores TF-IDF
        """
        if not self.corpus:
            # Se não tiver corpus treinado, usa apenas o texto atual
            vectorizer = TfidfVectorizer(lowercase=True, strip_accents='unicode')
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
        else:
            # Usar o vetorizador treinado com o corpus
            tfidf_matrix = self.tfidf_vectorizer.transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
        
        # Converter para dicionário de termo -> score
        dense = tfidf_matrix.todense()
        dense_list = dense.tolist()[0]
        
        return {feature_names[i]: dense_list[i] for i in range(len(feature_names)) if dense_list[i] > 0}
    
    def get_most_important_terms(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Retorna os termos mais importantes de acordo com TF-IDF"""
        tfidf_scores = self.calculate_tfidf(text)
        sorted_terms = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_terms[:top_n]
    
    def calculate_text_metrics(self, text: str) -> Dict[str, Any]:
        """
        Calcula métricas básicas do texto
        
        Returns:
            Dicionário com métricas calculadas
        """
        # Pré-processar o texto
        clean_text = self.preprocess_text(text)
        
        # Processar com spaCy
        doc = self.analyze_with_spacy(clean_text)
        
        # Obter parágrafos e sentenças
        paragraphs = self.get_paragraphs(clean_text)
        sentences = self.get_sentences(clean_text)
        
        # Calcular métricas
        words = [token.text for token in doc if not token.is_punct and not token.is_space]
        
        # Contagem de tipos de palavras
        pos_counts = Counter([token.pos_ for token in doc if not token.is_punct and not token.is_space])
        
        # Comprimento médio das sentenças
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Comprimento médio das palavras
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        return {
            "num_palavras": len(words),
            "num_sentencas": len(sentences),
            "num_paragrafos": len(paragraphs),
            "tamanho_medio_sentencas": avg_sentence_length,
            "tamanho_medio_palavras": avg_word_length,
            "tipo_palavras": dict(pos_counts)
        }
