# ✅ DATA QUALITY CHECKS

## 📌 Coleta de Posts

- Todos os posts devem ter pelo menos 1 registro em post_metrics_history
- collected_at nunca pode ser NULL

## 📌 Atualização

- Cada post deve ser atualizado ao menos 1x por dia

## 📌 Integridade

- Nenhum creator sem posts
- Nenhum post sem creator

## 📌 Queries de validação

### Posts sem histórico

```sql
SELECT p.id
FROM posts p
LEFT JOIN post_metrics_history h ON p.id = h.post_id
WHERE h.post_id IS NULL;

### Última coleta por post

```sql
SELECT *
FROM posts
WHERE collected_at IS NULL;


### Gaps de coleta (últimas 24h)

```sql
SELECT post_id
FROM post_metrics_history
GROUP BY post_id
HAVING MAX(collected_at) < NOW() - INTERVAL '24 hours';

