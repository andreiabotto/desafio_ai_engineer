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

Se você me passar o **código de rastreio**, ou o **número do pedido + e-mail/telefone** da compra, eu confiro o status. Usamos a data/hora atual da loja e a estimativa de entrega (quando `delivered`) para orientar o prazo — sem data real de recebimento no sistema, aviso essa limitação.

**Cliente:** Pode olhar o pedido 1? Meu e-mail é pedro.oliveira@jmail.com

**Agente:** (consulta `get_order_status` com order_id=1 e email; usa contexto temporal injetado)

O pedido **1** está como **delivered**, com rastreio `BRAB1234567BR` e estimativa de entrega em 25/10/2025. Com a data de hoje no fuso da loja, oriento se os 7 dias corridos ainda fariam sentido a partir dessa estimativa — se já passou, ainda podemos avaliar troca por defeito (até 30 dias) conforme a política.

## Requisitos cobertos

- Situação não trivial: política + dados de pedido
- Tools `search_policies` e `get_order_status`