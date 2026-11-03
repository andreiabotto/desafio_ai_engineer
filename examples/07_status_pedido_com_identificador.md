# Exemplo 7 — Status de pedido com identificador válido

**Cenário:** consulta legítima de pedido (caminho seguro / autorizado).

## Conversa

**Cliente:** Pode checar meu pedido? O rastreio é BRJL5544332BR.

**Agente:** (consulta `get_order_status` com tracking_code=`BRJL5544332BR`)

Encontrei! Pedido **#8**:
- Status: **shipped** (enviado)
- Rastreio: `BRJL5544332BR`
- Cliente: Ana Carolina Ferreira (Campo Grande)

Se quiser, posso também explicar prazos de frete pela política ou te ajudar com outra dúvida do pedido.

## Requisitos cobertos

- Tool `get_order_status` com identificador válido
- Dados vindos do SQLite (não inventados)
- Atendimento alinhado à LGPD (só após identificação)
