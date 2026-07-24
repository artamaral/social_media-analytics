# DATA QUALITY CHECKS

## Coleta de posts

- Todos os posts devem ter pelo menos 1 registro em `post_metrics_history`.
- `collected_at` nunca pode ser `NULL`.

## Atualizacao

- Cada post deve ser atualizado ao menos 1 vez por dia.

## Integridade

- Nenhum creator deve ficar sem posts.
- Nenhum post deve ficar sem creator.

Auditoria detalhada para Sprint 1:

- `sql/dml/audit_creator_post_integrity.sql`
- `sql/dml/audit_creator_post_integrity_summary.sql`

Objetivo:

- listar creators ativos sem posts
- listar posts sem `creator_id`
- listar posts apontando para creator inexistente ou inativo
- sinalizar creators ativos sem posts inseridos nos ultimos `30` dias como possivel alerta de discovery

## Queries de validacao

### Posts sem historico

```sql
SELECT p.id, p.post_id
FROM public.posts p
LEFT JOIN public.post_metrics_history h ON p.post_id = h.post_id
WHERE h.post_id IS NULL;
```

Auditoria detalhada para Sprint 1:

- `sql/dml/audit_posts_without_snapshots.sql`

Objetivo:

- listar apenas posts com `0` snapshots em `post_metrics_history`
- separar posts ativos de `unavailable_candidate` e `unavailable`
- trazer contexto de creator, idade do video, fila e revisao humana

### Ultima coleta por post

```sql
SELECT *
FROM public.posts
WHERE collected_at IS NULL;
```

Auditoria detalhada para Sprint 1:

- `sql/dml/audit_posts_collected_at_sync.sql`

Objetivo:

- listar posts com `posts.collected_at` nulo
- comparar `posts.collected_at` com o ultimo snapshot em `post_metrics_history`
- separar inconsistencias por `failure_status` e idade do video
- identificar casos em que ha snapshot, mas o campo corrente em `posts` nao foi sincronizado

### Gaps de coleta nas ultimas 24h

```sql
SELECT post_id
FROM public.post_metrics_history
GROUP BY post_id
HAVING MAX(collected_at) < NOW() - INTERVAL '24 hours';
```

Auditoria detalhada para Sprint 1:

- `sql/dml/audit_post_collection_gaps.sql`

Objetivo:

- detectar gaps de coleta por post
- separar atraso por `next_check` de frescor bruto do ultimo snapshot
- classificar posts novos/recentes por janela de `24h`
- classificar posts warm/old por janela conservadora de `72h`
- excluir `unavailable` da leitura principal e manter esses casos como auditoria separada

## Checks obrigatorios para o dashboard

Antes de usar rankings ou graficos como sinal de negocio, consultar:

```sql
SELECT *
FROM public.v_dashboard_data_quality_status;
```

Regra:

- se `is_analytics_ready = false`, o dashboard pode abrir, mas deve mostrar alerta de confiabilidade
- rankings devem ser interpretados como exploratorios ate os problemas serem corrigidos
- nenhuma decisao de marketing deve ser tomada sem validar os indicadores de qualidade

## Videos unavailable

Auditoria detalhada para Sprint 1:

- `sql/dml/audit_unavailable_posts_in_queue.sql`

Objetivo:

- confirmar que `status = unavailable` nao aparece em `v_post_update_queue_batch`
- confirmar que `status = unavailable` nao aparece em `v_dashboard_post_update_queue_batch`
- garantir que videos indisponiveis fiquem fora da fila ativa e aparecam apenas em contextos de auditoria

Resultado validado em 2026-06-16:

| checked_view | total_unavailable_in_queue | audit_status |
| --- | ---: | --- |
| `v_dashboard_post_update_queue_batch` | 0 | `ok` |
| `v_post_update_queue_batch` | 0 | `ok` |

Leitura:

- nao ha evidencia de vazamento de videos `unavailable` na fila operacional
- a fila do worker e a fila exibida no dashboard estao coerentes com a regra de isolamento
- a validacao de views analiticas de ranking, crescimento e cobertura deve continuar separada desta auditoria operacional

## Carros na Web - CSVs recorrentes de catalogo

Status:

- contrato definido em 2026-07-15
- fichas tecnicas por scraping ficam em `on_hold`
- catalogo inicial de fabricantes, modelos e anos/modelo modelado para
  Supabase em 2026-07-23
- carga inicial validada no Supabase em 2026-07-23 com `127` fabricantes,
  `1458` modelos e `8914` anos/modelo

Antes de publicar dados do Carros na Web em view consumida pelo Streamlit,
validar:

- origem/caminho de download dos CSVs
- data de download e hash/versao de cada arquivo
- schema esperado por CSV
- campos obrigatorios de fabricante, modelo e ano do modelo
- duplicidades pela chave natural definida para o catalogo
- `params` parseavel como JSON nos CSVs que trazem parametros de URL
- ausencia de carga de `aplicacoes_modelo_ano_test.csv`, pois esse arquivo
  pertence a exploracao de ficha tecnica
- novas entradas em relacao ao ultimo arquivo validado
- registros removidos ou alterados em relacao a versao anterior
- status de validacao da carga antes de expor a view analitica

Regra:

- a view do Streamlit so deve consumir dados com carga validada
- novas entradas devem ser destacadas como mudanca de catalogo, nao como venda
  ou emplacamento
- dados do Carros na Web devem ser rotulados como catalogo/oferta tecnica,
  separados de Fenabrave e SENATRAN/RENAVAM
- `v_carrosnaweb_vehicle_catalog` deve ser usada para homogeneizar marca,
  modelo e ano extraidos de descricao/transcricao, sem alterar `topic_path`
  nem contexto tecnico

## Classificacao GPT - Taxonomia Video V2

Status:

- contrato de banco e harness definidos em 2026-07-23
- a execucao futura deve usar Taxonomia V2, schema JSON e validacao antes de
  gravar resultados

Antes de aceitar resultados do classificador GPT, validar:

- `topic_path` e `topic_path_secondary` existem em
  `video_taxonomy_topic_paths`
- cada linha de `technical_context[]` tem apenas uma combinacao coerente de
  sistema, componente e problema
- nenhum campo tecnico usa `;` para concatenar valores
- contexto tecnico de video `fora_escopo` nao aparece como `primary`
- `barulho` nao aparece como `problem` canonico; usar `ruido`
- marca, modelo, ano e geracao possuem evidencia textual no input
- entidades de veiculo ficam preservadas em valor bruto antes do match contra
  catalogos externos
- `confidence_score` fica entre `0` e `1` e reflete evidencia disponivel, nao
  plausibilidade externa
- `transcript_quality_score` fica entre `0` e `1` no estagio `transcript_90s`
- `transcript_quality_status` e coerente com a faixa do score
- impacto textual `medium` ou `high` aciona revisao humana e limita a confianca
- transcripts `poor` ou `empty` acionam `needs_retranscription`
- `input_payload` nao preserva o texto completo de `transcript_90s`
- registros com termo fora da taxonomia devem preencher `taxonomy_gaps` ou
  `needs_human_review`, sem criar codigo canonico silenciosamente

Consultas de apoio:

- `sql/ddl/tests/011_test_video_taxonomy_classification.sql`
- `sql/ddl/tables/023_add_transcript_quality_to_video_classification.sql`
- `public.v_video_classification_quality`
