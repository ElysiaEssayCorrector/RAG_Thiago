"""
Agente de IA para processamento inteligente de documentos e redações
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
import asyncio
from pathlib import Path

import openai
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

from app.utils.file_processor import file_processor

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OpenAI API Key não está configurada. O agente terá funcionalidade limitada.")

class IAAgent:
    """
    Agente de IA para processamento avançado de documentos e redações
    usando modelos de linguagem e extração inteligente de conteúdo.
    """
    
    def __init__(self, model: str = "gpt-4"):
        """
        Inicializa o agente de IA
        
        Args:
            model: Modelo da OpenAI a ser utilizado (padrão: gpt-4)
        """
        self.model = model
        self.max_tokens = 4000
        self.temperature = 0.2
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Define o sistema prompt para o agente de IA"""
        return """
        Você é um agente especializado em análise e correção de redações.
        Seu objetivo é:
        
        1. Extrair o conteúdo textual de documentos em formato .pdf, .doc, .docx e .txt
        2. Analisar a estrutura, gramática, coesão e coerência do texto
        3. Fornecer feedback detalhado e construtivo
        4. Identificar pontos fortes e fracos de acordo com as competências da redação
        5. Atribuir notas objetivas em diferentes categorias
        
        Responda sempre em formato JSON estruturado.
        """
        
    @retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(5))
    async def process_document(self, file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa um documento usando IA para extrair e analisar o conteúdo
        
        Args:
            file_path: Caminho para o arquivo a ser processado
            file_type: Tipo do arquivo (opcional, será detectado automaticamente)
            
        Returns:
            Dict com o resultado da análise
        """
        try:
            # Extrair texto do documento
            with open(file_path, 'rb') as file:
                file_content = file.read()
                
            file_name = Path(file_path).name
            text = file_processor.extract_text(file_content, file_name, file_type)
            
            if not text:
                return {"error": "Não foi possível extrair texto do documento."}
            
            # Realizar análise com IA
            analysis_result = await self.analyze_text(text)
            
            return {
                "success": True,
                "text_extracted": text[:300] + "..." if len(text) > 300 else text,
                "analysis": analysis_result
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar documento: {str(e)}")
            return {"error": f"Falha ao processar documento: {str(e)}"}
    
    @retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(3))
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analisa o texto da redação usando IA
        
        Args:
            text: Texto da redação
            
        Returns:
            Dict com análise detalhada
        """
        # Limitar o tamanho do texto para evitar tokens excessivos
        max_chars = 14000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            
        try:
            user_prompt = f"""
            Analise a seguinte redação de acordo com as competências de clareza,
            coesão, coerência, norma culta e proposta de intervenção.
            
            Redação:
            {text}
            
            Forneça a análise completa em formato JSON com os seguintes campos:
            - nota_geral (float entre 0-10)
            - notas (array de objetos com competência, nota, justificativa)
            - resumo_executivo (string com resumo da análise)
            - problemas_gramaticais (array de problemas encontrados)
            - recomendacoes (array de recomendações)
            - pontos_fortes (array de pontos fortes)
            """
            
            response = await openai.chat.completions.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            try:
                # Extrair resposta como JSON
                result_text = response.choices[0].message.content
                analysis = json.loads(result_text)
                return analysis
            except json.JSONDecodeError:
                logger.error("Falha ao decodificar JSON da resposta da IA")
                return {"error": "Resposta da IA não está em formato JSON válido"}
                
        except Exception as e:
            logger.error(f"Erro ao analisar texto com IA: {str(e)}")
            return {"error": f"Falha na análise: {str(e)}"}
    
    async def extract_key_points(self, text: str, max_points: int = 5) -> List[str]:
        """
        Extrai pontos-chave do texto usando IA
        
        Args:
            text: Texto a ser analisado
            max_points: Número máximo de pontos a serem extraídos
            
        Returns:
            Lista de pontos-chave
        """
        try:
            prompt = f"""
            Extraia os {max_points} pontos-chave mais importantes do seguinte texto:
            
            {text[:8000]}
            
            Forneça apenas a lista de pontos em JSON.
            """
            
            response = await openai.chat.completions.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em extrair pontos-chave de textos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if isinstance(result, dict) and "pontos" in result:
                return result["pontos"]
            elif isinstance(result, dict) and "points" in result:
                return result["points"]
            else:
                # Tentar identificar a lista no resultado
                for key, value in result.items():
                    if isinstance(value, list) and len(value) > 0:
                        return value[:max_points]
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao extrair pontos-chave: {str(e)}")
            return []
    
    async def generate_improvement_suggestions(self, text: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Gera sugestões de melhoria específicas com base na análise
        
        Args:
            text: Texto original da redação
            analysis: Análise prévia do texto
            
        Returns:
            Lista de sugestões detalhadas
        """
        try:
            # Extrair pontos fracos da análise
            weak_points = []
            if "notas" in analysis:
                for competencia in analysis["notas"]:
                    if competencia.get("nota", 10) < 7.0:
                        weak_points.append(f"Melhorar {competencia['competencia']}: {competencia.get('justificativa', '')}")
            
            prompt = f"""
            Com base na análise da redação, gere 3-5 sugestões específicas e acionáveis para melhorar o texto.
            Foque nos seguintes pontos fracos:
            
            {json.dumps(weak_points, ensure_ascii=False)}
            
            Forneça sugestões diretas, específicas e práticas em formato JSON.
            """
            
            response = await openai.chat.completions.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em redação e fornecer feedback construtivo e acionável."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if isinstance(result, dict) and "sugestoes" in result:
                return result["sugestoes"]
            elif isinstance(result, dict) and "suggestions" in result:
                return result["suggestions"]
            else:
                # Tentar identificar a lista no resultado
                for key, value in result.items():
                    if isinstance(value, list) and len(value) > 0:
                        return value
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestões de melhoria: {str(e)}")
            return []


# Instância global para reutilização
ia_agent = IAAgent(model="gpt-4")
