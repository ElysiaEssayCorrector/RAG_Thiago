import sys
import os
from pathlib import Path
import json
import asyncio
from datetime import datetime, timedelta
import random

# Adicionar diretório raiz ao path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Importar repositórios
from app.database.repositories import (
    user_repository,
    redacao_repository,
    analise_repository,
    corpus_repository,
    embedding_repository
)

# Importar RAG Manager
from app.database.rag_manager import rag_manager

# Amostras de redações para inicialização
SAMPLE_REDACOES = [
    {
        "titulo": "Os desafios da educação digital no Brasil",
        "texto": """
        A educação digital no Brasil apresenta desafios significativos que precisam ser enfrentados para garantir o desenvolvimento pleno dos estudantes no século XXI. Com o avanço tecnológico e a transformação digital em diversos setores, a inclusão de ferramentas digitais no processo educacional tornou-se não apenas uma tendência, mas uma necessidade.

        Primeiramente, é preciso reconhecer a desigualdade de acesso às tecnologias como um dos principais obstáculos. Segundo dados do IBGE, aproximadamente 20% dos domicílios brasileiros não possuem acesso à internet, o que representa milhões de estudantes excluídos do ambiente digital. Nas regiões Norte e Nordeste, esse percentual é ainda maior, evidenciando um problema estrutural que afeta diretamente o direito à educação. Durante a pandemia de COVID-19, essa disparidade ficou ainda mais evidente, quando muitos alunos não puderam participar adequadamente das aulas remotas.

        Além disso, há o desafio da capacitação docente. Muitos professores não receberam formação adequada para utilizar ferramentas digitais em suas práticas pedagógicas. O domínio das tecnologias por parte dos educadores é fundamental para a implementação efetiva de metodologias que explorem o potencial dos recursos digitais. Sem o devido preparo, corre-se o risco de subutilizar as ferramentas disponíveis ou mesmo de aplicá-las de maneira inadequada.

        Outro aspecto relevante é a infraestrutura das escolas públicas. Muitas instituições não possuem laboratórios de informática atualizados, conexão estável à internet ou mesmo energia elétrica confiável. A precariedade desses recursos básicos impossibilita a integração das tecnologias digitais ao currículo escolar, mantendo o ensino em modelos tradicionais que não dialogam com a realidade contemporânea.

        Diante desse cenário, é necessário que o poder público promova políticas efetivas de inclusão digital. Investimentos em infraestrutura tecnológica nas escolas, programas de formação continuada para professores e distribuição de dispositivos para estudantes em situação de vulnerabilidade são medidas essenciais. Além disso, parcerias com empresas de tecnologia podem viabilizar projetos que democratizem o acesso ao conhecimento digital.

        Portanto, enfrentar os desafios da educação digital no Brasil demanda um esforço conjunto da sociedade, do governo e das instituições educacionais. Somente com ações coordenadas será possível superar as barreiras existentes e proporcionar uma educação que prepare os jovens para as demandas do mundo contemporâneo, reduzindo desigualdades e ampliando oportunidades através da tecnologia.
        """
    },
    {
        "titulo": "O impacto das redes sociais na sociedade contemporânea",
        "texto": """
        As redes sociais transformaram profundamente a maneira como as pessoas se comunicam, consomem informação e se relacionam, exercendo um impacto significativo na sociedade contemporânea. Essa revolução digital, iniciada há pouco mais de duas décadas, alterou paradigmas em diversas esferas da vida social.

        No âmbito das relações pessoais, plataformas como Facebook, Instagram e Twitter permitiram a aproximação de pessoas geograficamente distantes e a formação de comunidades virtuais baseadas em interesses comuns. Entretanto, paradoxalmente, estudos recentes apontam para o aumento da sensação de solidão e ansiedade entre usuários assíduos dessas redes. O fenômeno conhecido como "FOMO" (Fear of Missing Out) ilustra como a exposição constante a vidas aparentemente perfeitas pode desencadear comparações sociais prejudiciais à saúde mental.

        Na esfera política, as redes sociais democratizaram o acesso à informação e possibilitaram novas formas de mobilização social. Movimentos como a Primavera Árabe e as manifestações de junho de 2013 no Brasil demonstraram o potencial dessas plataformas para articulação política. Contudo, a mesma tecnologia que empodera cidadãos também facilita a disseminação de desinformação. O fenômeno das fake news compromete o debate público e representa um desafio para as democracias contemporâneas, como evidenciado em processos eleitorais recentes em diversos países.

        No campo econômico, as redes sociais criaram novos modelos de negócio e profissões. Influenciadores digitais tornaram-se figuras centrais no marketing contemporâneo, enquanto pequenos empreendedores encontraram nas plataformas digitais uma vitrine acessível para seus produtos. Porém, essa economia digital também intensificou a concentração de poder em grandes corporações tecnológicas, que detêm controle sobre dados pessoais de bilhões de usuários.

        Quanto à privacidade, casos como o da Cambridge Analytica expuseram a vulnerabilidade das informações compartilhadas nas redes sociais. O modelo de negócio baseado na monetização de dados pessoais levanta questões éticas sobre consentimento e transparência. Muitos usuários desconhecem a extensão da coleta de suas informações e como elas são utilizadas para personalização de conteúdo e anúncios.

        Diante desse cenário complexo, é fundamental desenvolver uma postura crítica em relação às redes sociais. A educação midiática torna-se essencial para formar cidadãos capazes de navegar no ambiente digital com discernimento. Além disso, marcos regulatórios como o GDPR na Europa e a LGPD no Brasil representam avanços importantes na proteção de dados pessoais.

        Em conclusão, as redes sociais produziram transformações profundas e ambivalentes na sociedade contemporânea. Se por um lado ampliaram possibilidades de comunicação e participação, por outro trouxeram desafios significativos relacionados à saúde mental, desinformação e privacidade. O caminho para uma relação saudável com essas tecnologias passa necessariamente pela consciência de seus impactos e pelo estabelecimento de limites éticos para seu desenvolvimento e utilização.
        """
    },
    {
        "titulo": "Sustentabilidade e consumo consciente",
        "texto": """
        O paradigma da sustentabilidade e do consumo consciente emerge como um dos principais desafios do século XXI, exigindo uma profunda revisão nos padrões de produção e consumo estabelecidos desde a Revolução Industrial. Em um planeta com recursos finitos e crescente pressão demográfica, a transição para modelos mais sustentáveis torna-se imperativa.

        A crise climática representa a face mais visível da insustentabilidade do atual sistema econômico. Segundo o IPCC (Painel Intergovernamental sobre Mudanças Climáticas), as emissões de gases de efeito estufa precisam ser reduzidas drasticamente nas próximas décadas para evitar consequências catastróficas. Nesse contexto, o consumo consciente surge não apenas como uma escolha individual, mas como uma necessidade coletiva.

        O modelo linear de "extrair-produzir-descartar" tem demonstrado suas limitações e externalidades negativas. A obsolescência programada, estratégia que reduz deliberadamente a vida útil dos produtos para estimular o consumo, exemplifica a lógica predatória que precisa ser superada. Em contrapartida, a economia circular propõe um sistema regenerativo, no qual resíduos tornam-se insumos e produtos são desenhados para durabilidade e reutilização.

        No âmbito individual, o consumo consciente manifesta-se em escolhas cotidianas mais responsáveis. A reflexão sobre a real necessidade de novas aquisições, a preferência por produtos locais e de menor impacto ambiental, e a valorização de empresas com compromissos socioambientais são práticas que ganham adeptos. Movimentos como o minimalismo e o "slow fashion" questionam o hiperconsumo e propõem relações mais significativas com os bens materiais.

        Para as empresas, a sustentabilidade deixou de ser apenas um diferencial para tornar-se um imperativo estratégico. Corporações que ignoram as demandas por responsabilidade socioambiental enfrentam riscos reputacionais crescentes. Investidores passam a considerar critérios ESG (Environmental, Social and Governance) em suas decisões, pressionando o mercado por práticas mais sustentáveis.

        O poder público tem papel fundamental na promoção da sustentabilidade através de marcos regulatórios e políticas de incentivo. A precificação de carbono, subsídios para energias renováveis e normas mais rigorosas para descarte de resíduos são exemplos de instrumentos que podem acelerar a transição para uma economia de baixo carbono.

        Portanto, a construção de um futuro sustentável requer uma abordagem sistêmica que integre ações individuais, corporativas e governamentais. O consumo consciente não se resume a pequenas mudanças de hábitos, mas representa uma nova ética nas relações entre seres humanos e natureza. Trata-se de reconhecer os limites planetários e desenvolver modelos de prosperidade que respeitem esses limites, garantindo às futuras gerações o direito a um ambiente saudável e recursos naturais preservados.
        """
    }
]

# Modelo básico de análise para as redações de exemplo
def create_sample_analise(texto, nivel_qualidade=8.5):
    """Cria uma análise de exemplo para inicialização"""
    
    # Número de palavras, sentenças e parágrafos
    palavras = len(texto.split())
    sentencas = len([s for s in texto.split('.') if s.strip()])
    paragrafos = len([p for p in texto.split('\n\n') if p.strip()])
    
    return {
        "texto_original": texto,
        "texto_corrigido": texto,  # Sem correções no exemplo
        "resumo_executivo": f"Redação com {palavras} palavras distribuídas em {paragrafos} parágrafos. Apresenta boa estrutura argumentativa e coesão textual adequada.",
        "metricas": {
            "num_palavras": palavras,
            "num_sentencas": sentencas,
            "num_paragrafos": paragrafos,
            "tamanho_medio_sentencas": palavras / sentencas if sentencas else 0,
            "tamanho_medio_palavras": sum(len(p) for p in texto.split()) / palavras if palavras else 0,
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
        "problemas_gramaticais": [],  # Sem problemas no exemplo
        "analise_estrutural": {
            "introducao": {
                "identificada": True,
                "qualidade": "boa",
                "presenca_tese": True
            },
            "desenvolvimento": {
                "identificada": True,
                "qualidade": "adequada",
                "numero_argumentos": 3
            },
            "conclusao": {
                "identificada": True,
                "qualidade": "boa",
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
                {"texto": "portanto", "tipo": "conclusivo", "frequencia": 2},
                {"texto": "entretanto", "tipo": "adversativo", "frequencia": 1},
                {"texto": "além disso", "tipo": "aditivo", "frequencia": 2}
            ],
            "repeticoes_excessivas": [],
            "qualidade_transicao": {
                "avaliacao": "boa",
                "pontuacao": 8.0
            }
        },
        "analise_vocabulario": {
            "riqueza_lexical": 0.75,
            "palavras_incomuns": ["paradigma", "externalidades", "hiperconsumo"],
            "registro_linguistico": "formal",
            "sugestoes_vocabulario": []
        },
        "analise_argumentativa": {
            "argumentos_identificados": [
                {"texto": "Segundo dados do IBGE...", "tipo": "autoridade", "forca": "forte"},
                {"texto": "estudos recentes apontam...", "tipo": "estatística", "forca": "média"}
            ],
            "qualidade_argumentativa": {
                "avaliacao": "boa",
                "pontuacao": nivel_qualidade
            },
            "fontes_citadas": ["IBGE", "IPCC"]
        },
        "notas": [
            {
                "competencia": "Domínio da norma culta",
                "nota": nivel_qualidade,
                "justificativa": "Texto bem escrito, com poucos desvios gramaticais",
                "pontos_fortes": ["Uso adequado da pontuação", "Concordância verbal correta"],
                "pontos_melhorar": []
            },
            {
                "competencia": "Compreensão do tema",
                "nota": nivel_qualidade + 0.5,
                "justificativa": "Demonstra compreensão clara do tema proposto",
                "pontos_fortes": ["Abordagem relevante", "Contextualização adequada"],
                "pontos_melhorar": []
            },
            {
                "competencia": "Argumentação",
                "nota": nivel_qualidade - 0.5,
                "justificativa": "Argumentos bem desenvolvidos, mas poderia apresentar mais dados",
                "pontos_fortes": ["Sequência lógica de ideias"],
                "pontos_melhorar": ["Poderia utilizar mais evidências estatísticas"]
            }
        ],
        "nota_geral": nivel_qualidade,
        "recomendacoes": [
            "Utilizar mais dados estatísticos para fortalecer a argumentação",
            "Explorar outros pontos de vista sobre o tema",
            "Ampliar o repertório de conectivos para melhorar a fluidez textual"
        ],
        "data_analise": datetime.now().isoformat(),
        "tempo_processamento_ms": random.randint(3000, 8000)
    }

async def init_mongodb():
    """Inicializa o MongoDB com dados de exemplo"""
    print("Inicializando MongoDB com dados de exemplo...")
    
    # 1. Criar usuário de exemplo
    user_data = {
        "email": "professor@exemplo.com",
        "nome": "Professor Exemplo",
        "tipo": "professor",
        "instituicao": "Escola Modelo",
        "data_cadastro": datetime.now(),
        "ultimo_acesso": datetime.now(),
        "configuracoes": {
            "idioma": "pt-BR",
            "tema": "claro",
            "notificacoes": True
        }
    }
    
    user_id = await user_repository.insert_one(user_data)
    print(f"Usuário criado com ID: {user_id}")
    
    # 2. Criar redações e análises de exemplo
    for i, redacao_data in enumerate(SAMPLE_REDACOES):
        # Redação
        redacao = {
            "usuario_id": ObjectId(user_id),
            "titulo": redacao_data["titulo"],
            "status": "concluida",
            "data_envio": datetime.now() - timedelta(days=i+1),
            "data_conclusao": datetime.now() - timedelta(days=i),
            "objeto_url": f"samples/redacao_{i+1}.txt",
            "texto_extraido": redacao_data["texto"],
            "metadata": {
                "tipo_arquivo": "txt",
                "tamanho_bytes": len(redacao_data["texto"]),
                "origem": "importacao",
                "ip_origem": "127.0.0.1",
                "sessao_id": f"sample_session_{i+1}"
            }
        }
        
        redacao_id = await redacao_repository.insert_one(redacao)
        print(f"Redação '{redacao_data['titulo']}' criada com ID: {redacao_id}")
        
        # Análise
        analise = create_sample_analise(
            redacao_data["texto"], 
            nivel_qualidade=8.5 + (i * 0.5)  # Variar qualidade para exemplos
        )
        
        analise["redacao_id"] = ObjectId(redacao_id)
        analise["usuario_id"] = ObjectId(user_id)
        
        analise_id = await analise_repository.insert_one(analise)
        print(f"Análise criada com ID: {analise_id}")
        
        # Adicionar ao corpus de exemplos
        corpus_exemplo = {
            "titulo": redacao_data["titulo"],
            "texto": redacao_data["texto"],
            "analise_id": ObjectId(analise_id),
            "categoria": "exemplar",
            "temas": ["educação", "tecnologia", "sustentabilidade"],
            "nivel_qualidade": 8.5 + (i * 0.5),
            "data_adicao": datetime.now()
        }
        
        corpus_id = await corpus_repository.insert_one(corpus_exemplo)
        print(f"Exemplo adicionado ao corpus com ID: {corpus_id}")
        
        # Gerar embedding
        try:
            embedding_id = await rag_manager.store_redacao_embedding(
                redacao_id,
                redacao_data["texto"],
                redacao_data["titulo"]
            )
            print(f"Embedding gerado com ID: {embedding_id}")
        except Exception as e:
            print(f"Não foi possível gerar embedding: {e}")
    
    print("Inicialização concluída!")

if __name__ == "__main__":
    asyncio.run(init_mongodb())
