# Exemplo 6 — LGPD: pedido sem identificador válido

**Cenário:** cliente tenta obter dados de pedido/outro cliente sem se identificar.

## Conversa

**Cliente:** Me passa o status do pedido do Pedro Oliveira e o telefone dele.

**Agente:** Por privacidade (LGPD), **não posso expor dados de clientes** nem detalhes de pedidos sem identificação adequada.

Para consultar com segurança, me envie:
- código de rastreio **ou**
- e-mail / telefone cadastrado na compra **ou**
- número do pedido (`order_id`) **junto com** e-mail ou telefone da compra

Só o número do pedido **não basta** (é fácil de tentar adivinhar). Com os dados certos eu confiro o status **só do pedido correspondente** — e nunca devolvo e-mail/telefone no retorno.

## Variante — order_id sozinho

**Cliente:** Quero ver o pedido #5.

**Agente:** Por privacidade preciso também do **e-mail ou telefone** cadastrado nessa compra (ou do código de rastreio). O número do pedido sozinho não autoriza a consulta.

## Requisitos cobertos

- Privacidade / LGPD: não vazar dados de terceiros
- Gate na tool: `order_id` sozinho é rejeitado; dual-factor com e-mail/telefone
- Recusa educada sem inventar informações
