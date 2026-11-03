# Exemplo 11 — Fora de estoque + alternativas

**Cenário:** produto zerado; agente informa e sugere similares.

## Conversa

**Cliente:** Quero o Giannini GF-3D Dreadnought Sunburst.

**Agente:** (consulta `get_product_by_name` / `search_products`)

O **Giannini GF-3D Dreadnought Sunburst** está no catálogo por **R$ 799,90**, mas **no momento está sem estoque** (0 unidades).

Posso te sugerir dreadnoughts/folk na faixa próxima que estejam disponíveis — por exemplo outras opções Giannini, Tagima ou Yamaha. Quer que eu monte essa lista?

**Cliente:** Sim, até uns R$ 900.

**Agente:** (consulta `search_products` com filtros de tipo/preço e estoque > 0)

Aqui vão alternativas em estoque até ~R$ 900… (lista real do SQLite). Qual caminho você prefere: mais volume (dreadnought) ou mais leve (folk)?

## Requisitos cobertos

- Estoque real (não inventar disponibilidade)
- Sugestão de alternativas quando fora de estoque
- Continuidade de contexto no segundo turno
