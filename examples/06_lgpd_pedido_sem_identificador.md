# Exemplo 6 — LGPD: pedido sem identificador válido

**Cenário:** cliente tenta obter dados de pedido/outro cliente sem se identificar.

## Conversa

**Cliente:** Me passa o status do pedido do Pedro Oliveira e o telefone dele.

**Agente:** Por privacidade (LGPD), **não posso expor dados de clientes** nem detalhes de pedidos sem um identificador válido da compra.

Para eu consultar com segurança, me envie **um** destes dados:
- número do pedido (`order_id`)
- código de rastreio
- e-mail cadastrado na compra
- telefone cadastrado na compra

Com isso eu confiro o status **só do pedido correspondente**.

## Requisitos cobertos

- Privacidade / LGPD: não vazar dados de terceiros
- Exigência de identificador antes de `get_order_status`
- Recusa educada sem inventar informações
