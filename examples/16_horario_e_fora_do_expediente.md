# Exemplo 16 — Horário e fora do expediente

**Cenário:** cliente pergunta horário / precisa de humano fora do expediente.

## Conversa

**Cliente:** Vocês estão abertos agora? Preciso falar com um atendente humano sobre um boleto.

**Agente:** (consulta `search_policies` sobre horário)

Nosso atendimento presencial e WhatsApp segue:
- **Seg–sex:** 09:00–18:00  
- **Sábado:** 09:00–13:00  
- **Domingo e feriados:** fechado  

Fora desse horário eu continuo te ajudando no que for automático (catálogo, políticas, status de pedido com identificador). Para assuntos que exigem humano (ex.: boleto específico / financeiro), o time retorna no **próximo expediente**.

Se quiser, já deixa o número do pedido ou e-mail da compra que eu organizo o contexto para eles.

## Requisitos cobertos

- RAG de horário (§2)
- Comportamento “fora do expediente” sem inventar plantão
- Separação do que o bot resolve vs. humano
