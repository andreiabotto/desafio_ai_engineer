# Exemplo 4 — Devolução por arrependimento (não trivial)

**Cenário:** aplicação de regra das políticas + possível cruzamento com pedido.

## Conversa

**Cliente:** Me arrependi da minha compra, posso devolver meu pedido?

**Agente:** (consulta `search_policies` sobre arrependimento / devolução)

Sim — para **compras online**, vale o direito de arrependimento:

- Prazo: **até 7 dias corridos** após o recebimento
- Produto na embalagem original, sem sinais de uso, com acessórios/manuais
- Reembolso na mesma forma de pagamento em até **10 dias úteis**
- Frete de devolução por conta da loja nesse caso

Se você me passar o **número do pedido**, e-mail ou código de rastreio, eu confiro o status e a data de entrega para ver se ainda está no prazo.

**Cliente:** Pode olhar o pedido 1?

**Agente:** (consulta `get_order_status` com order_id=1)

O pedido **1** está como **delivered**, com rastreio `BRAB1234567BR`. Com a data de entrega/estimativa do sistema, consigo orientar se o prazo de 7 dias ainda se aplica — se já passou, ainda podemos avaliar troca por defeito (até 30 dias) conforme a política.

## Requisitos cobertos

- Situação não trivial: política + dados de pedido
- Tools `search_policies` e `get_order_status`