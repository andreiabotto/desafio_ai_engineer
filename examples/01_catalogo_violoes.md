# Exemplo 1 — Catálogo de violões até R$ 1000

**Cenário:** consulta ao catálogo com filtro de preço.

## Conversa

**Cliente:** Quais opções de violões disponíveis custando até R$ 1000?

**Agente:** (consulta `search_products` com query="violão" e max_price=1000)

Oi! Separei alguns violões ativos no catálogo até R$ 1.000. Entre eles:

- **Yamaha C40 Nylon Natural** — R$ 599,90 (em estoque)
- **Yamaha C70 Nylon Natural** — R$ 849,00 (em estoque)

Se quiser, posso filtrar por nylon/aço, elétrico ou só acústico. Qual estilo você curte?

## Requisitos cobertos

- Consulta a dados estruturados (CSV/SQLite) em tempo real
- Filtro por preço
- Persona alinhada à loja