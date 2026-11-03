# Empório da Música — Agente de Atendimento

Protótipo em Python de um agente de mensagens para a loja fictícia **Empório da Música** (Campo Grande/MS), desenvolvido como desafio técnico de AI Engineer (Artefact).

O agente combina **tool calling** (dados operacionais em SQLite) com **RAG** (manual de políticas em PDF) e usa um **LLM gratuito** via Groq.

## Funcionalidades

- Persona alinhada ao tom da loja (informal-profissional)
- Consulta de catálogo, preços, estoque e promoções ativas
- Status de pedido por `order_id`, rastreio, e-mail ou telefone
- Políticas: horário, endereço, pagamento, trocas/devoluções, frete, garantia, LGPD
- Recusa educada de pedidos fora de escopo (acessórios)
- Histórico de conversa na sessão CLI
- Testes automatizados (unitários + integração com LLM mockado)
- Execução local ou via Docker Compose

## Arquitetura

```
Usuário (CLI)
    → LangGraph ReAct
        → Groq llama-3.3-70b-versatile
        → Tools → SQLite (CSVs)
        → Tool RAG → Chroma + sentence-transformers (local)
```

## Stack

| Peça | Tecnologia |
|------|------------|
| Linguagem | Python 3.11+ |
| Agente | LangChain + LangGraph |
| LLM | Groq `llama-3.3-70b-versatile` (tier gratuito) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| Vector store | ChromaDB |
| Dados | pandas + SQLite |
| CLI | Typer + Rich |
| Testes | pytest + pytest-mock |
| Containers | Docker + Compose |

## Pré-requisitos

1. Conta gratuita em [console.groq.com](https://console.groq.com) e uma API key
2. Python 3.11+ **ou** Docker

## Setup local

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .

cp .env.example .env
# edite .env e cole GROQ_API_KEY=...
```

### Ingestão e chat

```bash
python -m emporio_agent ingest
python -m emporio_agent chat
# ou simplesmente:
python -m emporio_agent
```

Comandos no chat: `/nova` (limpa histórico), `/sair`.

Modo verbose (mostra tool calls):

```bash
python -m emporio_agent chat --verbose
```

## Setup com Docker

```bash
cp .env.example .env
# preencha GROQ_API_KEY

docker compose up --build agent
```

A primeira subida baixa o modelo de embeddings e indexa as políticas (pode demorar). Volumes persistem SQLite (`.data/`), Chroma (`.chroma/`) e cache HuggingFace.

Rodar testes no container:

```bash
docker compose run --rm test
```

## Testes

```bash
# padrão: unit + integration (sem live / sem rede Groq)
pytest

# só unitários
pytest -m unit

# smoke opcional com API real
pytest -m live
```

Os testes de integração usam um LLM **mockado** que emite `tool_calls` controlados, garantindo CI determinística sem custo de API.

## Estrutura

```
src/emporio_agent/
  agent/          # prompts, LangGraph, memória
  data/           # ingestão CSV → SQLite e PDF → Chroma
  tools/          # products, orders, promotions, policies
  cli.py
data/             # CSVs e políticas_da_loja.pdf
examples/         # 5 conversas de exemplo
tests/
Dockerfile
docker-compose.yml
```

## Decisões técnicas

1. **Híbrido RAG + tools** — preços/estoque/pedidos são estruturados (SQL é mais confiável); políticas são texto livre (RAG).
2. **LangGraph ReAct** — loop explícito de raciocínio + ferramentas, adequado a atendimento multi-intenção.
3. **Groq gratuito** — sem custo para o avaliador; boa latência e suporte a tool calling. Alternativa futura: Ollama 100% local.
4. **Embeddings locais** — evita segunda API paga; o trade-off é imagem Docker maior e download inicial do modelo.
5. **SQLite** — zero infra, suficiente para o volume do desafio; fácil de inspecionar.
6. **CLI Typer/Rich** — foco no agente funcionando, interface mínima e clara.
7. **Testes em camadas** — tools sem LLM; agente com LLM fake; live opcional.

## Limitações e próximos passos

- Rate limits do tier gratuito Groq podem exigir espera/retry
- Match de produto é `LIKE` (não fuzzy avançado)
- Sem autenticação de cliente (identificação por order_id/e-mail/telefone)
- RAG com chunking simples; poderia melhorar com parent-document ou re-ranker
- Com mais tempo: canal WhatsApp, evals online, UI web, cache de respostas frequentes

## Exemplos de interação

Veja a pasta [`examples/`](examples/):

1. Violões até R$ 1000
2. Endereço da loja
3. Preço Takamine GD20
4. Devolução por arrependimento (política + pedido)
5. Fora de escopo (cordas/pedais)

## Uso de assistentes de código

Este projeto foi construído com auxílio do **Cursor** (agente de código): leitura do PDF do desafio, scaffold da arquitetura híbrida, implementação de tools/RAG/CLI/Docker/testes e redação do README. O fluxo foi: entender requisitos → planejar stack → implementar por etapas → validar com pytest.

## Dados

Os arquivos em `data/` foram fornecidos pelo desafio. Nem todos os campos precisam ser usados; o agente prioriza o que melhora o atendimento (produtos, pedidos, clientes, promoções ativas e políticas).
