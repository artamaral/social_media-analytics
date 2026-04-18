# 🧠 DECISÕES TÉCNICAS

---

## 📌 Estrutura de dados

### Uso de histórico (post_metrics_history)

Motivo:
- Permitir análise temporal
- Calcular crescimento real

---

## 📌 Estratégia de pipeline

- Pipeline A → novos posts
- Pipeline B → atualização de métricas

Motivo:
- Redução de custo
- Escalabilidade

---

## 📌 Classificação de vídeo

- Regra: <= 270s → short
- > 270s → long

Motivo:
- Padronização

---

## 📌 Prioridade de sistema

1. Pipeline funcionando
2. Qualidade dos dados
3. Analytics

Motivo:
- Evitar decisões com dados ruins
---

## Fatiamento da fila de rechecagem

Decisao:

- a fila deixa de ser consumida diretamente por `priority_score desc`
- o sistema passa a usar bandas de prioridade com cotas por faixa
- a selecao do lote passa a ser feita por uma view SQL

Motivo:

- evitar starvation dos posts de faixas intermediarias
- manter prioridade para posts mais relevantes sem bloquear todo o restante
- centralizar a regra de negocio no banco para facilitar manutencao

Implementacao:

- `calculate_priority_band(...)`
- `calculate_next_check(...)`
- `v_post_update_queue_batch`

Impacto esperado:

- maior cobertura da fila
- rechecagem mais equilibrada
- menor dependencia do worker para regras de selecao
