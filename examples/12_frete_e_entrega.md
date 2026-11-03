# Exemplo 12 — Frete e entrega

**Cenário:** política de frete via RAG.

## Conversa

**Cliente:** Como funciona o frete? Moro em Campo Grande.

**Agente:** (consulta `search_policies` sobre frete / entrega região metropolitana)

Para a **região metropolitana de Campo Grande**:
- **Frete grátis** em pedidos acima de **R$ 500,00**
- Abaixo de R$ 500,00: taxa fixa de **R$ 35,00**
- Prazo: **1 a 3 dias úteis** (motoboy próprio; ligam antes da entrega)

Para **outras cidades**, usamos Correios (PAC/SEDEX) ou Jadlog, com prazo e valor conforme CEP/peso. Todos os envios vão com seguro, e o rastreio no padrão `BR…BR` sai por e-mail/WhatsApp quando despachamos.

Quer que eu estime pensando em um instrumento específico do catálogo?

## Requisitos cobertos

- RAG de políticas (§5 Frete)
- Valores/prazos sem inventar fora do manual
