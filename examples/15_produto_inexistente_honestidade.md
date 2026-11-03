# Exemplo 15 — Produto inexistente / honestidade

**Cenário:** tool não encontra o item; agente admite e oferece caminho.

## Conversa

**Cliente:** Vocês têm a Gibson Les Paul Custom Shop Dragon 2099 Edição Intergaláctica?

**Agente:** (consulta `get_product_by_name` / `search_products` — sem resultado confiável)

Não encontrei esse modelo no nosso catálogo atual. Prefiro não inventar preço nem prazo.

Posso:
- buscar **Les Paul / Gibson** (ou similares) que temos em estoque
- ou anotar o interesse para a equipe humana verificar se dá para encomendar

O que prefere?

## Requisitos cobertos

- Não inventar produto/preço/estoque
- Honestidade quando a tool não retorna dado
- Oferta de alternativa ou encaminhamento humano
