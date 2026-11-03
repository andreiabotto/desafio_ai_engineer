# Exemplo 9 — Memória / contexto multi-turno

**Cenário:** o agente mantém o fio da conversa sem o cliente repetir o produto.

## Conversa

**Cliente:** Estou de olho no Takamine GD20.

**Agente:** (consulta `get_product_by_name` com "Takamine GD20")

Boa escolha! O **Takamine GD20 Dreadnought Natural** está por **R$ 2.199,00**. Quer que eu veja estoque, promoções ou formas de pagamento?

**Cliente:** E tem no estoque? Se pagar no PIX fica quanto?

**Agente:** (reusa o contexto do GD20; consulta produto/estoque se necessário + `search_policies` sobre PIX)

Sim — há unidades disponíveis. No **PIX à vista** a política dá **5%** sobre o preço de tabela:

- Tabela: R$ 2.199,00  
- Com PIX: **R$ 2.089,05**

Quer reservar ou prefere ver frete para o seu CEP?

**Cliente:** Prefiro ver alternativas mais baratas no mesmo estilo.

**Agente:** (consulta `search_products` com dreadnought/folk e faixa abaixo de 2199, mantendo a intenção “alternativa ao GD20”)

Separei opções dreadnought/folk mais acessíveis… (lista com preços reais do catálogo). Alguma dessas te agrada mais?

## Requisitos cobertos

- Memória de sessão / continuidade de contexto
- Não exigir que o cliente repita o modelo a cada turno
- Combinação produto + política (PIX) no mesmo fluxo
