# Exemplo 17 — Política ambígua → escala para gerência

**Cenário:** caso cinza não coberto de forma explícita; agente não inventa regra.

## Conversa

**Cliente:** Comprei um saxofone em liquidação “venda final”, mas quero trocar por preferência de cor. Dá?

**Agente:** (consulta `search_policies` sobre trocas / itens não elegíveis)

Pela política, produtos de **liquidação com aviso de “venda final”** entram em **itens não elegíveis para troca**. Troca por preferência (cor/modelo) em regra vale em até 7 dias **fora** desses casos.

Como seu pedido mistura “venda final” + preferência de cor, **não vou garantir a troca por conta própria**. Vou orientar a **gerência/equipe** a avaliar o caso com o número do pedido.

Me passa o `order_id`, rastreio ou e-mail da compra que eu localizo o pedido e deixo o encaminhamento preparado. Retorno humano em até **24h úteis** nesses casos especiais.

## Requisitos cobertos

- Não inventar exceção de política
- Escala para gerência em dúvida ambígua
- Continua pedindo identificador para agir com dados reais
