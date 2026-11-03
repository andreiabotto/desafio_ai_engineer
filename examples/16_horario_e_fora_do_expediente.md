# Exemplo 16 — Horário e fora do expediente

**Cenário:** cliente pergunta horário / precisa de humano fora do expediente.

## Conversa

**Cliente:** Vocês estão abertos agora? Preciso falar com um atendente humano sobre um boleto.

**Agente:** (usa o contexto temporal injetado no turno e/ou `get_current_datetime` — que já traz `is_open_now` — e confirma detalhes com `search_policies`)

Agora são **[hora do contexto]** em Campo Grande. Pelo expediente estamos **[abertos/fechados]**.

Nosso atendimento presencial e WhatsApp segue:
- **Seg–sex:** 09:00–18:00  
- **Sábado:** 09:00–13:00  
- **Domingo e feriados:** fechado  

Fora desse horário eu continuo te ajudando no que for automático (catálogo, políticas, status de pedido com identificação adequada). Para assuntos que exigem humano (ex.: boleto específico / financeiro), o time retorna no **próximo expediente** (o contexto temporal também indica a próxima abertura).

Se quiser, já deixa o número do pedido **e** o e-mail da compra (ou o rastreio) que eu organizo o contexto para eles.

## Requisitos cobertos

- Contexto temporal injetado + tool `get_current_datetime` (`is_open_now`)
- RAG de horário (§2) para texto da política
- Comportamento “fora do expediente” sem inventar plantão
- Separação do que o bot resolve vs. humano
