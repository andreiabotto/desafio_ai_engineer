# Exemplo 10 — Promoções ativas e regra do PIX

**Cenário:** só promoções ativas + PIX não cumulativo com preço promocional.

## Conversa

**Cliente:** Quais promoções estão valendo agora?

**Agente:** (consulta `get_active_promotions`)

No momento temos **4 promoções ativas**, por exemplo:
- **Ohana CK-20 Concert Natural** — de R$ 549,00 por **R$ 439,20** (20%, Desconto Exclusivo)
- **Crafter HT-100 Folk Aço Natural** — de R$ 2.399,00 por **R$ 1.967,18** (18%)
- **Kalani KAL-700T Tenor Natural** — de R$ 359,00 por **R$ 323,10** (10%)
- **Taylor 110e Dreadnought Natural** — de R$ 5.999,00 por **R$ 5.519,08** (8%)

**Cliente:** No Ohana CK-20 eu ainda ganho os 5% do PIX em cima dessa promo?

**Agente:** (consulta `search_policies` sobre promoções / PIX)

Não. Pela política da loja, **promoções não são cumulativas** e o **desconto de PIX (5%) não se aplica sobre preços já promocionais**.  
No CK-20 vale o preço promo **R$ 439,20**.

## Requisitos cobertos

- Tool `get_active_promotions` (somente `is_active`)
- Transparência: preço original + % + preço final
- Regra de não cumulatividade PIX × promoção
