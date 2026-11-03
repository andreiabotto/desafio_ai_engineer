# Empório da Música — Agente de Atendimento

Protótipo em Python de um agente de mensagens para a loja fictícia **Empório da Música** (Campo Grande/MS), desenvolvido como desafio técnico de AI Engineer (Artefact).

O agente combina **tool calling** (dados operacionais em SQLite) com **RAG** (manual de políticas em PDF) e usa um **LLM gratuito** via Groq.

## Funcionalidades

- Persona alinhada ao tom da loja (informal-profissional)
- Consulta de catálogo, preços, estoque e promoções ativas
- Status de pedido por `order_id`, rastreio, e-mail ou telefone (LGPD minimizado)
- Políticas: horário, endereço, pagamento, trocas/devoluções, frete, garantia, LGPD
- Data/hora da loja (`get_current_datetime`) para “estamos abertos agora?”
- Recusa educada de pedidos fora de escopo (acessórios), com gate na tool de catálogo
- Histórico de conversa na sessão com resumo dos fatos das tools
- Interface gráfica com Streamlit
- Testes automatizados (unitários + integração + evals ligados aos examples)
- CI (GitHub Actions) e execução local ou via Docker Compose

## Arquitetura

```
Usuário (CLI ou Streamlit)
    → LangGraph ReAct (limite de passos + retry Groq)
        → Groq openai/gpt-oss-120b
        → Tools → SQLite (CSVs)
        → Tool RAG → Chroma + sentence-transformers multilingual (local)
        → get_current_datetime (America/Campo_Grande)
```

## Stack

| Peça | Tecnologia |
|------|------------|
| Linguagem | Python 3.11+ |
| Agente | LangChain + LangGraph |
| LLM | Groq `openai/gpt-oss-120b` (tier gratuito) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (local) |
| Vector store | ChromaDB (MMR) |
| Dados | pandas + SQLite |
| CLI | Typer + Rich |
| UI | Streamlit |
| Testes | pytest (+ evals YAML) |
| Containers | Docker multi-stage + Compose |

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

Comandos no chat CLI: `/nova` (limpa histórico), `/sair`, `/help`.

Modo verbose (mostra tool calls):

```bash
python -m emporio_agent chat --verbose
```

### Interface gráfica (Streamlit)

```bash
python -m emporio_agent ui
# ou com porta customizada:
python -m emporio_agent ui --port 8501
```

Abre em [http://localhost:8501](http://localhost:8501): chat com sugestões, nova conversa, reinício do agente e toggle de tools.

## Setup com Docker

```bash
cp .env.example .env
# preencha GROQ_API_KEY

# CLI interativa
docker compose up --build agent

# UI Streamlit
docker compose up --build ui
```

A primeira subida baixa o modelo de embeddings e indexa as políticas (pode demorar). Volumes persistem SQLite (`.data/`), Chroma (`.chroma/`) e cache HuggingFace. A imagem roda como usuário não-root.

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

Camadas:

| Camada | O que prova | O que **não** prova |
|--------|-------------|---------------------|
| Unit (tools/ingest/memory) | SQL, LGPD na tool, compactação, contratos de prompt | Escolha do LLM real |
| Integration (LLM scriptado) | Loop ReAct + tools stub **e** tools reais (SQLite) | Persona / tool-choice do modelo Groq |
| Evals (`tests/eval_cases.yaml`) | Examples core ligados a asserts | Qualidade semântica do embedding real (CI usa FakeEmbeddings no RAG) |
| Live | Smoke de saudação com API | Cobertura completa de cenários |

CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda `pytest -m "unit or integration"`.

## Estrutura

```
src/emporio_agent/
  agent/          # prompts, LangGraph, memória
  data/           # ingestão CSV → SQLite e PDF → Chroma
  tools/          # products, orders, promotions, policies, datetime
  ui/             # Streamlit
  bootstrap.py    # init compartilhado CLI/UI
  cli.py
data/             # CSVs e políticas_da_loja.pdf
examples/         # conversas de exemplo (ilustrativas, não transcripts capturados)
tests/            # unit, integration, eval_cases.yaml
.github/workflows/ci.yml
Dockerfile
docker-compose.yml
```

## Decisões técnicas

1. **Híbrido RAG + tools** — preços/estoque/pedidos são estruturados (SQL é mais confiável); políticas são texto livre (RAG).
2. **LangGraph ReAct** — loop explícito de raciocínio + ferramentas, com `recursion_limit` e retry em rate limit.
3. **Groq gratuito** — sem custo para o avaliador; boa latência e suporte a tool calling. Alternativa futura: Ollama 100% local.
4. **Embeddings multilingual locais** — melhor fit PT-BR sem segunda API paga; trade-off: imagem/cache maiores.
5. **SQLite** — zero infra; fingerprint dos CSVs invalida ingestão stale; snapshot de `unit_price_brl` nos itens.
6. **Memória compacta** — remove traces brutos de tools (TPM) mas mantém um `SystemMessage` com fatos resumidos.
7. **LGPD na tool** — identificadores com AND; telefone exato; e-mail/telefone nunca no JSON; nome mascarado sem order_id/tracking.
8. **Testes em camadas** — tools sem LLM; agente com LLM fake; evals dos examples; live opcional.

## Limitações e próximos passos

- Rate limits do tier gratuito Groq podem exigir espera/retry (há backoff básico)
- Match de produto é substring com fold de acentos (não fuzzy/FTS completo)
- Identificação de pedido = posse do identificador (não é autenticação real / OTP)
- `unit_price_brl` é snapshot do catálogo na ingestão — o CSV de itens não traz preço histórico real
- RAG: chunking por seção + sub-chunk; CI de políticas usa FakeEmbeddings (ranking semântico não é gate de CI)
- Examples em `examples/` são **roteiros esperados**, não dumps verbatim de CLI
- Sem canal WhatsApp; evals online com juiz LLM ficam como evolução
- UI Streamlit sem autenticação de acesso (adequado a demo local)

## Exemplos de interação

**Core (comece por estes):** `06` LGPD, `08` segurança, `09` multi-turno, `17` política ambígua, `01` catálogo.

Lista completa em [`examples/`](examples/):

1. Violões até R$ 1000
2. Endereço da loja
3. Preço Takamine GD20
4. Devolução por arrependimento (política + pedido)
5. Fora de escopo (cordas/pedais)
6. LGPD — pedido sem identificador
7. Status de pedido com identificador válido
8. Segurança — jailbreak / prompt injection
9. Contexto multi-turno (memória de sessão)
10. Promoções ativas + PIX não cumulativo
11. Fora de estoque + alternativas
12. Frete e entrega
13. Garantia
14. Reclamação com empatia
15. Produto inexistente (honestidade)
16. Horário / fora do expediente
17. Política ambígua → escala para gerência

## Uso de assistentes de código

Este projeto foi construído com auxílio do **Cursor** (agente de código): leitura do PDF do desafio, scaffold da arquitetura híbrida, implementação de tools/RAG/CLI/Docker/testes e redação do README.

Decisões tomadas com o assistente (e mantidas após revisão humana):

- Separar fatos estruturados (SQL) de políticas (RAG), em vez de tudo-embedding
- Groq free tier + embeddings locais (custo zero para o avaliador)
- Compactar histórico por TPM, retendo resumo de tools em vez do trace completo
- Endurecer LGPD na tool (não só no prompt)
- Evals YAML ligados aos examples para o que o desafio pede julgar

## Dados

Os arquivos em `data/` foram fornecidos pelo desafio. Nem todos os campos precisam ser usados; o agente prioriza o que melhora o atendimento (produtos, pedidos, clientes, promoções ativas e políticas).
