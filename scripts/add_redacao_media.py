#!/usr/bin/env python
import sys
import os
from pathlib import Path
import json
import asyncio
from datetime import datetime
import logging
from bson import ObjectId

# Adicionar diretório raiz ao path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar repositórios
from app.database.repositories import (
    user_repository,
    redacao_repository, 
    analise_repository,
    corpus_repository
)

# Importar RAG Manager
from app.database.rag_manager import rag_manager

# Redação de qualidade média (nota 7.0)
REDACAO_MEDIA = {
    "titulo": "Desigualdade social no Brasil",
    "texto": """
    A desigualdade social no Brasil é um problema historico que permanece até os dias atuais. Desde a colonização, existe uma concentração de renda nas mãos de poucos, o que gerou um grande abismo entre as classes sociais, dificultando o acesso de muitos cidadoes a direitos básicos.

    Em primeiro lugar, é preciso entender que a desigualdade econômica esta diretamente relacionada com a má distribuição de oportunidades. Segundo dados do IBGE, os 10% mais ricos concentram mais de 40% da renda do país, enquanto os 10% mais pobres detêm menos de 1%. Esta disparidade reflete-se no acesso à educação de qualidade, saúde e moradia, perpetuando um ciclo de pobreza que é dificil de ser quebrado.

    Além disso, fatores históricos como a escravidão e a falta de políticas efetivas de inclusão contribuiram para que grupos marginalizados, especialmente a população negra, enfrentassem barreiras ainda maiores para a ascenção social. Estudos mostram que pessoas negras recebem salarios menores e ocupam menos cargos de liderança, mesmo quando possuem a mesma qualificação que pessoas brancas, evidenciando um racismo estrutural que agrava a desigualdade.

    O Brasil tambem apresenta disparidades regionais significativas. O Nordeste e o Norte do país têm indices de desenvolvimento humano inferiores aos do Sul e Sudeste, demonstrando que a desigualdade não se expressa apenas entre individuos, mas também entre regiões. Investimentos públicos desproporcionais ao longo da história contribuiram para essa configuração.

    Para enfrentar esse cenário, é necessário implementar políticas públicas que combinem crescimento econômico com distribuição de renda. Programas de transferência de renda, como o Bolsa Família, representaram avanços, mas precisam ser complementados com investimentos em educação pública de qualidade, que é o principal mecanismo de mobilidade social.

    Portanto, a redução da desigualdade social no Brasil requer um esforço coletivo que envolva governo, empresas e sociedade civil. Somente com políticas consistentes de inclusão, valorizacão da diversidade e distribuição justa de oportunidades será possível construir um país mais equilibrado e justo para todos os cidadãos.
    """
}

async def adicionar_redacao_media():
    """Adiciona uma redação de qualidade média (nota 7.0) ao MongoDB"""
    try:
        print("Adicionando redação de qualidade média (nota 7.0) ao MongoDB...")
        
        # 1. Obter ou criar usuário para a redação
        user_data = {
            "email": "avaliador@exemplo.com",
            "nome": "Avaliador Sistema",
            "tipo": "admin",
            "instituicao": "Sistema Elysia",
            "data_cadastro": datetime.now(),
            "ultimo_acesso": datetime.now(),
            "configuracoes": {"idioma": "pt-BR"}
        }
        
        existing_user = await user_repository.find_by_email("avaliador@exemplo.com")
        if existing_user:
            user_id = str(existing_user["_id"])
            print(f"Usuário existente encontrado com ID: {user_id}")
        else:
            user_id = await user_repository.insert_one(user_data)
            print(f"Novo usuário criado com ID: {user_id}")
        
        # 2. Criar a redação no MongoDB
        redacao_data = {
            "usuario_id": ObjectId(user_id),
            "titulo": REDACAO_MEDIA["titulo"],
            "status": "concluida",
            "data_envio": datetime.now(),
            "data_conclusao": datetime.now(),
            "objeto_url": "samples/redacao_media.txt",
            "texto_extraido": REDACAO_MEDIA["texto"],
            "metadata": {
                "tipo_arquivo": "txt",
                "tamanho_bytes": len(REDACAO_MEDIA["texto"]),
                "origem": "script",
                "classificacao_qualidade": "media"
            }
        }
        
        redacao_id = await redacao_repository.insert_one(redacao_data)
        print(f"Redação média criada com ID: {redacao_id}")
        
        # 3. Criar análise com nota 7.0
        # Calcular métricas simples do texto
        palavras = len(REDACAO_MEDIA["texto"].split())
        sentencas = len([s for s in REDACAO_MEDIA["texto"].split('.') if s.strip()])
        paragrafos = len([p for p in REDACAO_MEDIA["texto"].split('\n\n') if p.strip()])
        
        # Criar análise com problemas gramaticais identificados
        analise_data = {
            "redacao_id": ObjectId(redacao_id),
            "usuario_id": ObjectId(user_id),
            "texto_original": REDACAO_MEDIA["texto"],
            "texto_corrigido": REDACAO_MEDIA["texto"].replace("historico", "histórico")
                                                  .replace("cidadoes", "cidadãos")
                                                  .replace("esta", "está")
                                                  .replace("dificil", "difícil")
                                                  .replace("contribuiram", "contribuíram")
                                                  .replace("ascenção", "ascensão")
                                                  .replace("salarios", "salários")
                                                  .replace("tambem", "também")
                                                  .replace("indices", "índices")
                                                  .replace("individuos", "indivíduos")
                                                  .replace("valorizacão", "valorização"),
            "resumo_executivo": "Redação com conteúdo adequado, mas apresenta diversos problemas de acentuação e alguns erros gramaticais. A estrutura argumentativa é satisfatória, porém a conclusão poderia ser mais impactante.",
            "metricas": {
                "num_palavras": palavras,
                "num_sentencas": sentencas,
                "num_paragrafos": paragrafos,
                "tamanho_medio_sentencas": palavras / sentencas if sentencas else 0,
                "tamanho_medio_palavras": sum(len(p) for p in REDACAO_MEDIA["texto"].split()) / palavras if palavras else 0,
                "tipo_palavras": {
                    "NOUN": int(palavras * 0.25),
                    "VERB": int(palavras * 0.2),
                    "ADJ": int(palavras * 0.1),
                    "DET": int(palavras * 0.15),
                    "PREP": int(palavras * 0.12),
                    "CONJ": int(palavras * 0.05),
                    "OTHER": int(palavras * 0.13)
                }
            },
            "problemas_gramaticais": [
                {
                    "tipo": "acentuação",
                    "texto_original": "historico",
                    "sugestao": "histórico",
                    "explicacao": "Palavra paroxítona terminada em 'o' com sílaba tônica com 'i' deve ser acentuada",
                    "posicao": [40, 49]
                },
                {
                    "tipo": "acentuação",
                    "texto_original": "cidadoes",
                    "sugestao": "cidadãos",
                    "explicacao": "Plural de palavras terminadas em 'ão' geralmente terminam em 'ãos', 'ães' ou 'ões'",
                    "posicao": [222, 230]
                },
                {
                    "tipo": "acentuação",
                    "texto_original": "esta",
                    "sugestao": "está",
                    "explicacao": "Verbo 'estar' na 3ª pessoa do singular do presente do indicativo deve ser acentuado",
                    "posicao": [304, 308]
                },
                {
                    "tipo": "concordância",
                    "texto_original": "estudos mostram",
                    "sugestao": "estudos mostram",
                    "explicacao": "Concordância adequada entre sujeito e verbo",
                    "posicao": [856, 872]
                }
            ],
            "analise_estrutural": {
                "introducao": {
                    "identificada": True,
                    "qualidade": "regular",
                    "presenca_tese": True
                },
                "desenvolvimento": {
                    "identificada": True,
                    "qualidade": "boa",
                    "numero_argumentos": 3
                },
                "conclusao": {
                    "identificada": True,
                    "qualidade": "regular",
                    "retomada_tese": True
                },
                "proporcao": {
                    "introducao": 0.15,
                    "desenvolvimento": 0.7,
                    "conclusao": 0.15
                }
            },
            "analise_coesao": {
                "conectivos_utilizados": [
                    {"texto": "além disso", "tipo": "aditivo", "frequencia": 1},
                    {"texto": "também", "tipo": "aditivo", "frequencia": 1},
                    {"texto": "portanto", "tipo": "conclusivo", "frequencia": 1}
                ],
                "repeticoes_excessivas": [
                    {"termo": "desigualdade", "frequencia": 5, "sugestoes": ["disparidade", "diferença social"]}
                ],
                "qualidade_transicao": {
                    "avaliacao": "regular",
                    "pontuacao": 6.5
                }
            },
            "analise_vocabulario": {
                "riqueza_lexical": 0.65,
                "palavras_incomuns": ["ascenção", "disparidade"],
                "registro_linguistico": "formal com falhas",
                "sugestoes_vocabulario": [
                    {"original": "grande abismo", "sugestao": "disparidade significativa"},
                    {"original": "fatores históricos", "sugestao": "contexto histórico"}
                ]
            },
            "analise_argumentativa": {
                "argumentos_identificados": [
                    {"texto": "Segundo dados do IBGE, os 10% mais ricos concentram mais de 40% da renda do país", "tipo": "estatística", "forca": "forte"},
                    {"texto": "fatores históricos como a escravidão", "tipo": "causa-efeito", "forca": "média"},
                    {"texto": "O Nordeste e o Norte do país têm indices de desenvolvimento humano inferiores", "tipo": "comparação", "forca": "média"}
                ],
                "qualidade_argumentativa": {
                    "avaliacao": "satisfatória",
                    "pontuacao": 7.0
                },
                "fontes_citadas": ["IBGE"]
            },
            "notas": [
                {
                    "competencia": "Domínio da norma culta",
                    "nota": 6.0,
                    "justificativa": "Apresenta diversos problemas de acentuação e alguns erros ortográficos",
                    "pontos_fortes": ["Estrutura sintática adequada"],
                    "pontos_melhorar": ["Revisão de regras de acentuação", "Atenção à ortografia"]
                },
                {
                    "competencia": "Compreensão do tema",
                    "nota": 8.0,
                    "justificativa": "Demonstra boa compreensão do tema da desigualdade social no Brasil",
                    "pontos_fortes": ["Abordagem histórica", "Menção a elementos econômicos e sociais"],
                    "pontos_melhorar": ["Poderia explorar mais propostas de solução"]
                },
                {
                    "competencia": "Argumentação",
                    "nota": 7.0,
                    "justificativa": "Argumentação satisfatória com uso de alguns dados",
                    "pontos_fortes": ["Uso de dados estatísticos", "Abordagem multifacetada do problema"],
                    "pontos_melhorar": ["Aprofundar a análise crítica", "Usar mais fontes de dados"]
                },
                {
                    "competencia": "Coesão textual",
                    "nota": 7.0,
                    "justificativa": "Apresenta coesão adequada, mas com algumas repetições",
                    "pontos_fortes": ["Uso de alguns conectivos adequados"],
                    "pontos_melhorar": ["Diversificar conectivos", "Evitar repetições"]
                },
                {
                    "competencia": "Proposta de intervenção",
                    "nota": 7.0,
                    "justificativa": "Apresenta proposta genérica para solução do problema",
                    "pontos_fortes": ["Menciona políticas públicas necessárias"],
                    "pontos_melhorar": ["Detalhar propostas concretas", "Especificar agentes e ações"]
                }
            ],
            "nota_geral": 7.0,
            "recomendacoes": [
                "Revisar regras de acentuação gráfica",
                "Diversificar o vocabulário para evitar repetições",
                "Usar mais dados e estatísticas para fortalecer a argumentação",
                "Elaborar uma proposta de intervenção mais detalhada e concreta",
                "Melhorar a conclusão para torná-la mais impactante"
            ],
            "data_analise": datetime.now(),
            "tempo_processamento_ms": 3500
        }
        
        analise_id = await analise_repository.insert_one(analise_data)
        print(f"Análise criada com ID: {analise_id}")
        
        # 4. Adicionar ao corpus de exemplos com nota 7.0
        corpus_data = {
            "titulo": REDACAO_MEDIA["titulo"],
            "texto": REDACAO_MEDIA["texto"],
            "analise_id": ObjectId(analise_id),
            "categoria": "comum",
            "temas": ["desigualdade", "problemas sociais", "Brasil"],
            "nivel_qualidade": 7.0,
            "data_adicao": datetime.now()
        }
        
        corpus_id = await corpus_repository.insert_one(corpus_data)
        print(f"Exemplo adicionado ao corpus com ID: {corpus_id}")
        
        # 5. Gerar embedding para a redação
        try:
            embedding_id = await rag_manager.store_redacao_embedding(
                redacao_id,
                REDACAO_MEDIA["texto"],
                REDACAO_MEDIA["titulo"]
            )
            print(f"Embedding gerado com ID: {embedding_id}")
        except Exception as e:
            print(f"Aviso: Não foi possível gerar embedding (requer OpenAI API): {e}")
        
        print("\nRedação de qualidade média (nota 7.0) adicionada com sucesso!")
        print(f"ID da redação: {redacao_id}")
        print(f"ID da análise: {analise_id}")
        
        return redacao_id, analise_id
        
    except Exception as e:
        print(f"Erro ao adicionar redação média: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(adicionar_redacao_media())
