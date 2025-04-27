# Elysia - Sistema RAG para Correção de Redações

Este repositório contém a implementação do backend para o sistema Elysia de correção automática de redações utilizando técnicas de RAG (Retrieval Augmented Generation).

## Funcionalidades

- Análise linguística utilizando spaCy
- Processamento de redações com TF-IDF para recuperação de informações relevantes
- Verificação de:
  - Sintaxe e gramática
  - Verbos e conjunções
  - Estrutura textual
  - Coesão e coerência
- API REST para integração com o frontend

## Estrutura do Projeto

```
RAG_Thiago/
├── app/
│   ├── api/          # Endpoints da API FastAPI
│   ├── models/       # Modelos e esquemas de dados
│   └── utils/        # Utilitários e processadores de texto
├── data/
│   └── redacoes/     # Base de redações para treinamento
└── scripts/          # Scripts para processamento de dados
```

## Instalação

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Baixe o modelo do spaCy:
   ```
   python -m spacy download pt_core_news_lg
   ```

## Execução

Para iniciar o servidor API:

```
uvicorn app.api.main:app --reload
```

## Integração

A API pode ser integrada ao frontend existente, modificando o endpoint no arquivo `script.js`.
