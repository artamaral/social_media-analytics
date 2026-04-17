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