# AGENDA DE SPRINTS

## Objetivo

Organizar a execucao do projeto em sprints sequenciais, com foco em confiabilidade, entrega analitica e evolucao controlada da plataforma de inteligencia automotiva.

Este arquivo complementa o roadmap. O roadmap define as prioridades gerais; esta agenda define a ordem recomendada de execucao.

## Regra obrigatoria de execucao

Apenas atividades relacionadas ao sprint ativo devem ser executadas.

Antes de iniciar qualquer atividade, o GPT deve verificar:

1. A atividade pertence ao sprint ativo?
2. A atividade esta conectada a uma entrega prevista neste arquivo?
3. A atividade respeita o roadmap, data quality e decisoes tecnicas do projeto?

Se a atividade nao tiver relacao clara com o sprint ativo, o GPT deve perguntar antes de prosseguir:

```text
Esta atividade nao esta relacionada ao sprint ativo. Deseja prosseguir mesmo assim ou prefere registrar no backlog/roadmap?
```

Sem confirmacao explicita do usuario, a atividade deve ser tratada como ideia ou sugestao, nao como execucao.

## Sprint ativo

Status atual:

```text
Sprint ativo: Sprint 3 - Dashboard MVP analitico
Datas: a definir conforme disponibilidade do usuario
```

Enquanto o Sprint 3 estiver ativo, apenas tarefas relacionadas ao dashboard
analitico, validacao das views do Supabase, Data Quality antes dos rankings e
entregas de `Overview`, `Creators` e crescimento semanal devem ser executadas
automaticamente. Alteracoes fora deste escopo devem aguardar confirmacao.

## Visao geral

| Sprint | Tema | Estimativa | Resultado esperado |
| --- | --- | --- | --- |
| Sprint 1 | Confiabilidade da coleta social media | 1 a 2 dias | Saber se a base atual esta confiavel para analise |
| Sprint 2 | Fila, `next_check` e guardrail | 1 a 2 dias | Confirmar se a fila sustenta o crescimento da base |
| Sprint 3 | Dashboard MVP analitico | 2 a 4 dias | Overview, creators e crescimento semanal funcionando |
| Sprint 4 | Ranking `Hot Now` | 1 a 2 dias | View temporal com velocidade e aceleracao |
| Sprint 5 | Fontes externas | 2 a 4 dias | Fenabrave repetivel e decisao de viabilidade do Carros na Web |
| Sprint 6 | Enrichment e produto analitico | 2 a 3 dias | Proxima camada de classificacao e insights definida |

Estimativa total: `9` a `17` dias uteis de execucao focada.

## Ordem recomendada de blocos

### Bloco 1 - Base confiavel

Inclui:

- Sprint 1
- Sprint 2

Objetivo:

- estabilizar dados historicos, fila e cobertura antes de usar rankings como sinal de negocio.

### Bloco 2 - Entrega analitica visivel

Inclui:

- Sprint 3
- Sprint 4

Objetivo:

- transformar a base SQL em dashboard util para leitura de creators, videos em crescimento e oportunidades temporais.

### Bloco 3 - Expansao de produto

Inclui:

- Sprint 5
- Sprint 6

Objetivo:

- consolidar fontes externas e preparar enrichment com IA sem comprometer a confiabilidade operacional.

---

## Sprint 1 - Confiabilidade da coleta social media

### Objetivo

Validar se os dados historicos permitem analise sem risco operacional relevante.

### Atividades

- [x] Validar posts sem historico em `post_metrics_history`.
- [x] Validar `collected_at` nulo ou defasado.
- [x] Detectar gaps de coleta por post.
- [x] Confirmar creators sem posts ou posts sem creator.
- [x] Checar se videos `unavailable` estao isolados corretamente na fila operacional.

### Progresso

#### Atividade 1 - Posts sem historico

Status: concluida em 2026-06-16.

Query criada:

- `sql/dml/audit_posts_without_snapshots.sql`

Resultado observado:

- posts ativos sem snapshot: `0`
- posts sem snapshot por indisponibilidade confirmada: `4`
- todos os casos retornados tinham `failure_status = unavailable` e
  `human_review_status = confirmed_unavailable`

Leitura:

- nao ha evidencia de post ativo perdido sem snapshot
- os casos sem historico pertencem ao fluxo de indisponibilidade, nao a uma
  falha comum de coleta ou guardrail

#### Atividade 2 - Validar `collected_at` nulo ou defasado

Status: concluida em 2026-06-16.

Objetivo:

- confirmar se `posts.collected_at` esta preenchido para posts ativos
- confirmar se `posts.collected_at` acompanha o ultimo snapshot de
  `post_metrics_history`
- separar diferenca operacional aceitavel de inconsistencia real

Etapas:

1. Listar posts ativos com `posts.collected_at is null`.
2. Separar o resultado por `failure_status` para nao misturar videos
   indisponiveis com falha ativa de coleta.
3. Comparar `posts.collected_at` com `max(post_metrics_history.collected_at)`
   por `post_id`.
4. Identificar posts em que existe snapshot mais recente que
   `posts.collected_at`.
5. Identificar posts em que `posts.collected_at` existe, mas nao ha snapshot
   correspondente em `post_metrics_history`.
6. Agrupar inconsistencias por idade do video:
   - `new_0_3d`
   - `recent_4_7d`
   - `warm_8_30d`
   - `old_30d_plus`
7. Classificar achados:
   - bloqueador: post ativo com historico, mas `collected_at` nulo ou muito
     atrasado sem justificativa
   - atencao: diferenca pequena entre ultimo snapshot e `posts.collected_at`
   - esperado: videos `unavailable` confirmados ou candidatos em auditoria
8. Registrar a conclusao antes de avancar para gaps de coleta.

Queries esperadas:

- auditoria de `collected_at is null`
- comparacao entre `posts.collected_at` e ultimo snapshot
- resumo agregado por `failure_status` e `video_age_bucket`

Criterio de conclusao:

- posts ativos com `collected_at` nulo: `0`, ou lista justificada
- divergencias entre `posts.collected_at` e ultimo snapshot: `0`, ou lista
  classificada por severidade
- videos `unavailable` separados da leitura principal de qualidade

Query criada:

- `sql/dml/audit_posts_collected_at_sync.sql`

Resultado observado:

- inconsistencias em posts ativos: `0`
- `active` com status `ok`:
  - `new_0_3d`: `43`
  - `recent_4_7d`: `169`
  - `warm_8_30d`: `816`
  - `old_30d_plus`: `2806`
- `unavailable` com status `ok`:
  - `recent_4_7d`: `3`
  - `old_30d_plus`: `13`
- `zero_snapshots_and_post_collected_at_null` em `unavailable`:
  - `warm_8_30d`: `2`
  - `old_30d_plus`: `2`

Leitura:

- nao ha evidencia de `collected_at` nulo ou defasado em posts ativos
- a sincronizacao entre `posts.collected_at` e o ultimo snapshot esta saudavel
  para a base ativa
- os unicos casos sem `collected_at` continuam sendo videos `unavailable`,
  coerentes com a Atividade 1

#### Atividade 3 - Detectar gaps de coleta por post

Status: concluida em 2026-06-16.

Objetivo:

- identificar posts ativos com possivel gap de coleta
- separar frescor bruto do ultimo snapshot de atraso real por `next_check`
- manter videos `unavailable` fora da leitura principal da base ativa

Query criada:

- `sql/dml/audit_post_collection_gaps.sql`

Resultado observado:

- `overdue_by_next_check` em posts ativos:
  - `new_0_3d / needs_coverage`: `22`
  - `recent_4_7d / needs_coverage`: `123`
  - `recent_4_7d / covered_3_49`: `24`
  - `warm_8_30d / needs_coverage`: `5`
  - `warm_8_30d / covered_3_49`: `664`
  - `warm_8_30d / overchecked_50_199`: `3`
  - `old_30d_plus / covered_3_49`: `1944`
  - `old_30d_plus / overchecked_50_199`: `53`
  - `old_30d_plus / overchecked_200_499`: `2`
  - `old_30d_plus / overchecked_500_plus`: `3`
- casos `unavailable` fora da leitura principal:
  - `no_snapshot`: `4`
  - `non_active_failure_status`: `16`
- posts ativos com status `ok`:
  - `new_0_3d / needs_coverage`: `21`
  - `recent_4_7d`: `21`
  - `warm_8_30d`: `145`
  - `old_30d_plus`: `804`

Leitura:

- a base ativa nao apresenta problema de snapshots inexistentes ou
  `collected_at` dessincronizado, mas apresenta volume alto de posts vencidos
  pela regra de `next_check`
- o maior volume esta em `old_30d_plus / covered_3_49`, com `1944` posts
  vencidos, o que reforca a necessidade do Sprint 2 sobre fila, `next_check`
  e guardrail
- os `22` posts novos e os `123` recentes em `needs_coverage` merecem atencao
  operacional por impacto direto na cobertura minima
- os casos `unavailable` seguem segregados e nao devem contaminar a leitura
  principal de qualidade da base ativa

#### Atividade 4 - Confirmar creators sem posts ou posts sem creator

Status: concluida em 2026-06-16.

Objetivo:

- validar se creators ativos possuem posts
- validar se posts estao ligados a creators validos
- identificar sinais de discovery sem insercao recente

Queries criadas:

- `sql/dml/audit_creator_post_integrity.sql`
- `sql/dml/audit_creator_post_integrity_summary.sql`

Resultado observado:

- `post_without_creator_id`: `0`
- `post_with_missing_creator`: `0`
- `active_creator_without_posts`: `0`
- `post_with_inactive_creator`: `0`
- `creator_without_recent_discovery`: `2`
- creators `ok`: `36`
- posts `ok`: `3854`

Leitura:

- nao ha quebra de integridade entre `posts` e `creators`
- nao ha creator ativo sem nenhum post
- os `2` casos de `creator_without_recent_discovery` nao provam canal morto;
  indicam apenas creators ativos com posts historicos, mas sem posts inseridos
  nos ultimos `30` dias
- esses 2 creators devem ser tratados como candidatos para revisao de discovery:
  pode ser canal sem publicacao recente, canal realmente inativo ou falha do
  scraper em incorporar videos novos

#### Atividade 5 - Checar isolamento de videos `unavailable` na fila operacional

Status: concluida em 2026-06-16 para fila operacional.

Objetivo:

- confirmar que videos `unavailable` aparecem apenas em contextos de auditoria
- confirmar que videos `unavailable` nao entram na fila operacional
- manter a validacao de views analiticas de rankings, crescimento e cobertura
  geral como tarefa futura separada

Subcheck 1 - Fila operacional:

Query criada:

- `sql/dml/audit_unavailable_posts_in_queue.sql`

Resultado observado:

- `v_dashboard_post_update_queue_batch`: `0` posts `unavailable`, status `ok`
- `v_post_update_queue_batch`: `0` posts `unavailable`, status `ok`

Leitura:

- nao ha vazamento de videos `unavailable` na fila operacional
- a exclusao de `status = unavailable` esta funcionando para a view de lote do
  worker e para a view de dashboard da fila
- essa conclusao nao cobre rankings, crescimento ou cobertura geral; essas
  views devem ser auditadas em uma atividade propria antes de uso executivo

### Documentacao relacionada

- [03_DATA_QUALITY_CHECKS.md](../data_model/03_DATA_QUALITY_CHECKS.md)
- [04_PIPELINE_STATUS.md](04_PIPELINE_STATUS.md)
- [27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md](../social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md)

### Entregas

- Diagnostico objetivo de prontidao analitica.
- Lista curta de correcoes obrigatorias antes de usar rankings.
- Atualizacao do status operacional se houver evidencia nova.

### Estimativa

`1` a `2` dias.

---

## Sprint 2 - Fila, next_check e guardrail

### Objetivo

Confirmar se a regra atual de atualizacao dos videos esta bem calibrada para a base em crescimento.

### Atividades

- [x] Analisar `v_dashboard_queue_bottleneck_status`.
- [x] Validar atraso por banda, idade do video e numero de checagens.
- [x] Confirmar impacto da migration nova de `next_check`.
- [ ] Verificar se lote `50` com guardrail `6` esta suficiente.
- [ ] Decidir se a regra de frequencia deve ser mantida ou ajustada.

### Planejamento

#### Fase 1 - Diagnostico da fila e do `next_check`

Objetivo:

- montar o baseline operacional da Sprint 2;
- entender onde o atraso esta concentrado;
- confirmar se a migration nova de `next_check` esta produzindo o efeito
  esperado antes de discutir ajuste de capacidade ou regra.

Atividades da fase:

- [x] Atividade 1: analisar `v_dashboard_queue_bottleneck_status`.
- [x] Atividade 2: validar atraso por banda, idade do video e numero de
  checagens.
- [x] Atividade 3: confirmar impacto da migration nova de `next_check`.

Criterio de saida da fase:

- gargalos principais identificados com numeros da view;
- leitura separada entre `needs_coverage`, posts novos/recentes e posts
  `warm`/`old` ja cobertos;
- conclusao inicial sobre a migration:
  - efeito saudavel;
  - efeito insuficiente;
  - ou efeito inconclusivo, exigindo mais uma janela de observacao.

#### Atividade 1 - Analisar `v_dashboard_queue_bottleneck_status`

Status: concluida em 2026-06-16.

Objetivo:

- transformar a leitura do dashboard em evidencia objetiva sobre gargalos da
  fila;
- separar atraso real de efeito esperado da regra de desaceleracao por idade e
  cobertura;
- identificar quais grupos disputam capacidade do worker antes de qualquer
  mudanca em SQL.

Pergunta principal:

```text
A fila atual esta atrasada porque a capacidade e insuficiente, porque a regra
de next_check ainda esta agressiva, ou porque o atraso esta concentrado em
grupos que ja deveriam ser desacelerados?
```

Fonte principal:

- `public.v_dashboard_queue_bottleneck_status`

Campos-chave para leitura:

- `priority_band`
- `video_age_bucket`
- `check_band`
- `total_posts`
- `media_checagens`
- `p50_staleness_days`
- `p90_staleness_days`
- `p95_staleness_days`
- `max_staleness_days`
- `posts_acima_3_2d`
- `posts_acima_5d`
- `posts_acima_7d`
- `posts_vencidos`
- `posts_no_batch_atual`
- `next_check_mais_atrasado`

Etapas:

1. Consultar a view completa e ordenar por risco operacional:
   - `posts_acima_7d desc`
   - `p95_staleness_days desc`
   - `posts_vencidos desc`
   - `total_posts desc`
2. Separar a leitura por `video_age_bucket`:
   - `new_0_3d`: precisa ser responsivo, pois captura tracao inicial;
   - `recent_4_7d`: ainda e janela sensivel para crescimento;
   - `warm_8_30d`: deve ser avaliado junto com cobertura;
   - `old_30d_plus`: nao deve consumir cadencia curta se ja estiver coberto.
3. Separar a leitura por `check_band`:
   - `needs_coverage`: prioridade operacional por guardrail;
   - `covered_3_49`: fluxo normal;
   - `overchecked_50_199`, `overchecked_200_499` e `overchecked_500_plus`:
     possivel excesso de recorrencia, especialmente em posts antigos.
4. Comparar `posts_vencidos` com `posts_no_batch_atual`:
   - se ha muitos vencidos e poucos no batch, ha disputa de capacidade;
   - se o batch esta concentrado em grupos menos urgentes, revisar cotas/refill;
   - se o batch cobre os grupos criticos, acompanhar evolucao antes de ajustar.
5. Classificar cada grupo em uma das leituras:
   - saudavel: baixo atraso e baixa cauda de staleness;
   - observar: atraso moderado, mas sem risco em `needs_coverage`;
   - alerta: `needs_coverage` vencido ou `p95` crescendo;
   - ajuste provavel: posts `warm`/`old` ja cobertos dominando vencidos.
6. Registrar conclusao antes da Atividade 2, usando numeros da view como
   baseline da Sprint 2.

Query sugerida:

```sql
select
  priority_band,
  video_age_bucket,
  check_band,
  total_posts,
  media_checagens,
  p50_staleness_days,
  p90_staleness_days,
  p95_staleness_days,
  max_staleness_days,
  posts_acima_3_2d,
  posts_acima_5d,
  posts_acima_7d,
  posts_vencidos,
  posts_no_batch_atual,
  next_check_mais_atrasado
from public.v_dashboard_queue_bottleneck_status
order by
  posts_acima_7d desc,
  p95_staleness_days desc,
  posts_vencidos desc,
  total_posts desc;
```

Criterios de conclusao:

- identificar os grupos com maior gargalo operacional;
- confirmar se `needs_coverage` esta protegido ou acumulando atraso;
- confirmar se posts `warm_8_30d` e `old_30d_plus` ja cobertos ainda competem
  demais com posts novos/recentes;
- decidir se a Atividade 2 deve focar em capacidade, regra de frequencia,
  refill por banda ou guardrail.

Resultado esperado:

- baseline numerico da Sprint 2;
- lista curta de grupos criticos;
- decisao de leitura: manter observacao, investigar regra de `next_check` ou
  preparar ajuste controlado.

Modelo de registro do resultado:

```text
Data da leitura:
View consultada:
Total de grupos retornados:
Grupos com maior risco:
- grupo:
  prioridade:
  idade:
  checagens:
  total_posts:
  posts_vencidos:
  posts_no_batch_atual:
  p95_staleness_days:
  posts_acima_7d:

Leitura:
- gargalo principal:
- risco para guardrail:
- risco para posts novos/recentes:
- risco de excesso em posts antigos:

Decisao para proxima atividade:
- seguir para Atividade 2 com foco em:
```

Saidas obrigatorias antes de concluir a atividade:

- uma tabela resumida com os `5` grupos mais criticos;
- uma leitura executiva em texto curto;
- uma classificacao do risco operacional:
  - `baixo`: atraso concentrado em grupos ja cobertos e sem cauda acima de
    `7d`;
  - `medio`: atraso relevante, mas sem acumulacao em `needs_coverage`;
- `alto`: acumulacao em `needs_coverage`, posts novos/recentes vencidos ou
    cauda acima de `7d` em grupos sensiveis;
- recomendacao objetiva para a Atividade 2.

Resultado observado:

- total de grupos retornados: `39`
- top 5 grupos criticos:
  - `priority_band = 2 | old_30d_plus | covered_3_49`
    - `total_posts = 1020`
    - `posts_vencidos = 823`
    - `posts_no_batch_atual = 7`
    - `p95_staleness_days = 5.99`
    - `posts_acima_7d = 0`
  - `priority_band = 1 | old_30d_plus | covered_3_49`
    - `total_posts = 1002`
    - `posts_vencidos = 778`
    - `posts_no_batch_atual = 5`
    - `p95_staleness_days = 5.90`
    - `posts_acima_7d = 0`
  - `priority_band = 2 | warm_8_30d | covered_3_49`
    - `total_posts = 324`
    - `posts_vencidos = 314`
    - `posts_no_batch_atual = 0`
    - `p95_staleness_days = 4.01`
    - `posts_acima_7d = 0`
  - `priority_band = 1 | warm_8_30d | covered_3_49`
    - `total_posts = 268`
    - `posts_vencidos = 232`
    - `posts_no_batch_atual = 1`
    - `p95_staleness_days = 5.82`
    - `posts_acima_7d = 0`
  - `priority_band = 1 | recent_4_7d | needs_coverage`
    - `total_posts = 68`
    - `posts_vencidos = 61`
    - `posts_no_batch_atual = 1`
    - `p95_staleness_days = 3.81`
    - `posts_acima_7d = 0`

Leitura:

- gargalo principal: o maior atraso esta concentrado em `old_30d_plus` e
  `warm_8_30d` com `covered_3_49`, principalmente nas bandas `1` e `2`
- risco para guardrail: existe risco real em `recent_4_7d / needs_coverage`,
  com acumulacao relevante nas bandas `1`, `2` e `3`
- risco para posts novos/recentes: `new_0_3d` segue relativamente controlado,
  mas `recent_4_7d` abaixo da cobertura minima ja mostra pressao operacional
- risco de excesso em posts antigos: os grupos `overchecked_*` e bandas altas
  aparecem mais controlados, sugerindo que a desaceleracao recente ajudou

Classificacao do risco operacional:

- `alto`

Conclusao:

- a migration nova de `next_check` parece ter reduzido bem a pressao em posts
  muito checados e bandas altas
- o problema atual nao parece mais ser dominado por posts antigos superfortes
  voltando cedo demais
- o foco operacional passa a ser:
  - bandas `1` e `2` com `covered_3_49`
  - `recent_4_7d / needs_coverage`
  - avaliacao de capacidade real do lote e do refill global

Decisao para a Atividade 2:

- validar atraso por `priority_band`, `video_age_bucket` e `check_band` com
  foco explicito em:
  - bandas `1` e `2`
  - `recent_4_7d / needs_coverage`
  - `warm_8_30d` e `old_30d_plus / covered_3_49`

#### Atividade 2 - Validar atraso por banda, idade do video e checagens

Status: concluida em 2026-06-16.

Objetivo:

- explicar o atraso observado na Atividade 1;
- evitar leitura superficial baseada apenas em volume total vencido;
- separar o que e atraso critico do que e efeito esperado da desaceleracao de
  posts ja cobertos.

Perguntas de analise:

- quais `priority_band` concentram mais `posts_vencidos`?
- o atraso esta em `new_0_3d` e `recent_4_7d`, que exigem resposta rapida?
- o atraso esta em `warm_8_30d` e `old_30d_plus` ja cobertos, onde a cadencia
  pode ser mais lenta?
- existe acumulacao em `needs_coverage`, indicando risco para o guardrail?
- os posts com muitas checagens continuam ocupando espaco demais na leitura
  operacional?

Etapas:

1. Agrupar a view por `priority_band` para ver a pressao por faixa de score.
2. Agrupar por `video_age_bucket` para separar janela inicial de crescimento
   de posts antigos.
3. Agrupar por `check_band` para separar cobertura minima de recorrencia
   normal ou excesso de checagens.
4. Cruzar os tres eixos:
   - banda;
   - idade;
   - checagens.
5. Destacar grupos com:
   - `needs_coverage` vencido;
   - `posts_acima_7d` maior que zero;
   - `p95_staleness_days` alto;
   - muitos `posts_vencidos` e poucos `posts_no_batch_atual`.
6. Registrar se o problema parece ser:
   - capacidade total;
   - cota/refill por banda;
   - regra de `next_check`;
   - ou passivo residual de guardrail.

Foco desta execucao:

- medir o peso relativo das bandas `1` e `2` no atraso total;
- comparar `recent_4_7d / needs_coverage` contra `warm_8_30d` e
  `old_30d_plus / covered_3_49`;
- verificar se a fila esta falhando mais por capacidade total insuficiente ou
  por distribuicao insuficiente do batch atual.

Query sugerida:

```sql
select
  video_age_bucket,
  check_band,
  priority_band,
  sum(total_posts) as total_posts,
  sum(posts_vencidos) as posts_vencidos,
  sum(posts_no_batch_atual) as posts_no_batch_atual,
  max(p95_staleness_days) as pior_p95_staleness_days,
  max(max_staleness_days) as pior_staleness_days,
  sum(posts_acima_3_2d) as posts_acima_3_2d,
  sum(posts_acima_5d) as posts_acima_5d,
  sum(posts_acima_7d) as posts_acima_7d
from public.v_dashboard_queue_bottleneck_status
group by
  video_age_bucket,
  check_band,
  priority_band
order by
  posts_acima_7d desc,
  pior_p95_staleness_days desc,
  posts_vencidos desc,
  total_posts desc;
```

Criterios de conclusao:

- se `needs_coverage` acumular atraso, priorizar guardrail na fase seguinte;
- se `new_0_3d` ou `recent_4_7d` acumular atraso, revisar capacidade e
  responsividade;
- se o atraso estiver concentrado em `warm`/`old` ja cobertos, validar se isso
  e aceitavel pela nova regra antes de ajustar;
- se posts com `overchecked_*` dominarem os vencidos, investigar excesso de
  recorrencia em posts antigos.

Resultado esperado:

- mapa de gargalo por banda, idade e cobertura;
- leitura objetiva do risco para analytics automotivo;
- recomendacao de foco para a Atividade 3.

Resultado observado:

- o atraso total esta fortemente concentrado nas bandas `1` e `2`
- principais grupos observados:
  - `old_30d_plus | covered_3_49 | priority_band = 2`
    - `total_posts = 1020`
    - `posts_vencidos = 823`
    - `posts_no_batch_atual = 7`
    - `pior_p95_staleness_days = 5.99`
  - `old_30d_plus | covered_3_49 | priority_band = 1`
    - `total_posts = 1002`
    - `posts_vencidos = 778`
    - `posts_no_batch_atual = 5`
    - `pior_p95_staleness_days = 5.91`
  - `warm_8_30d | covered_3_49 | priority_band = 2`
    - `total_posts = 325`
    - `posts_vencidos = 314`
    - `posts_no_batch_atual = 0`
    - `pior_p95_staleness_days = 4.02`
  - `warm_8_30d | covered_3_49 | priority_band = 1`
    - `total_posts = 268`
    - `posts_vencidos = 232`
    - `posts_no_batch_atual = 1`
    - `pior_p95_staleness_days = 5.83`
  - `recent_4_7d | needs_coverage | priority_band = 1`
    - `total_posts = 68`
    - `posts_vencidos = 61`
    - `posts_no_batch_atual = 1`
    - `pior_p95_staleness_days = 3.82`
  - `recent_4_7d | needs_coverage | priority_band = 2`
    - `total_posts = 39`
    - `posts_vencidos = 39`
    - `posts_no_batch_atual = 3`
    - `pior_p95_staleness_days = 4.08`

Leitura:

- o peso do atraso esta concentrado nas bandas baixas `1` e `2`, nao nas
  bandas altas
- `old_30d_plus` e `warm_8_30d` com `covered_3_49` dominam o volume de
  vencidos, indicando fila longa de rechecagem normal
- `recent_4_7d / needs_coverage` aparece com volume menor, mas com severidade
  operacional maior por risco direto ao guardrail e a cobertura minima
- `new_0_3d / needs_coverage` continua relativamente controlado e nao e o
  principal problema desta leitura
- os grupos `overchecked_*` nao dominam atraso nem cauda, reforcando que a
  desaceleracao recente parece estar funcionando para posts muito checados

Diagnostico:

- o problema atual parece ser mais de distribuicao insuficiente do batch e
  capacidade efetiva sobre bandas `1` e `2` do que de regra agressiva para
  posts superchecados
- o caso mais chamativo e `warm_8_30d | covered_3_49 | priority_band = 2`,
  com `314` vencidos e `0` itens no batch atual, o que sugere refill/cota
  pouco aderente ao grupo
- como `recent_4_7d / needs_coverage` segue acumulando vencidos, o guardrail
  atual ainda nao esta absorvendo toda a pressao relevante

Conclusao:

- bandas `1` e `2` concentram o principal backlog operacional da fila
- o atraso em `warm` e `old` cobertos pode ser parcialmente aceitavel pela nova
  regra, mas o volume atual indica que a capacidade pratica nao esta chegando
  de forma suficiente nesses grupos
- o atraso em `recent_4_7d / needs_coverage` indica que o problema nao e apenas
  "backlog toleravel"; ha risco real para cobertura minima

Decisao para a Atividade 3:

- confirmar que a migration nova de `next_check` de fato melhorou os grupos
  `overchecked_*` e bandas altas
- separar o que e efeito saudavel da desaceleracao de `warm/old` do que ja
  virou falta de capacidade ou distribuicao inadequada
- usar esta leitura para decidir se o proximo ajuste deve atacar:
  - lote total do worker;
  - fatia guardrail;
  - refill/cotas por banda;
  - ou combinacao desses pontos antes de nova mudanca de `next_check`

#### Atividade 3 - Confirmar impacto da migration nova de `next_check`

Status: concluida em 2026-06-16.

Objetivo:

- validar se a regra por idade e cobertura reduziu pressao indevida de posts
  `warm` e `old` ja cobertos;
- confirmar que posts novos, recentes e com menos de `3` checagens continuam
  protegidos;
- decidir se a migration deve ser mantida em observacao ou se exige ajuste.

Contexto tecnico:

- migration de aplicacao:
  `sql/migrations/2026-06-15_004_queue_next_check_age_coverage_up.sql`;
- migration de conversao de timezone:
  `sql/migrations/2026-06-15_006_post_update_queue_next_check_timestamptz_up.sql`;
- regra esperada:
  - `total_checagens < 3`: preservar politica atual e guardrail;
  - `new_0_3d` e `recent_4_7d`: preservar politica atual;
  - `warm_8_30d` e `old_30d_plus` com `3+` checagens:
    - bandas `5` e `6`: minimo `12h`;
    - bandas `1` a `4`: minimo `24h`.

Etapas:

1. Confirmar que a fila atual mostra menos pressao em `warm` e `old` ja
   cobertos do que o baseline anterior da revisao de `next_check`.
2. Confirmar que `needs_coverage` continua aparecendo no batch quando vencido.
3. Confirmar que `new_0_3d` e `recent_4_7d` nao foram desacelerados
   indevidamente.
4. Verificar se posts antigos com muitas checagens ainda aparecem como
   gargalo relevante.
5. Registrar uma das tres conclusoes:
   - manter regra e observar;
   - ajustar regra de frequencia;
   - revisar capacidade/cotas antes de mexer em `next_check`.

Query sugerida:

```sql
select
  video_age_bucket,
  check_band,
  priority_band,
  sum(total_posts) as total_posts,
  sum(posts_vencidos) as posts_vencidos,
  sum(posts_no_batch_atual) as posts_no_batch_atual,
  max(p95_staleness_days) as p95_staleness_days,
  max(max_staleness_days) as max_staleness_days
from public.v_dashboard_queue_bottleneck_status
where
  video_age_bucket in ('warm_8_30d', 'old_30d_plus')
  and check_band <> 'needs_coverage'
group by
  video_age_bucket,
  check_band,
  priority_band
order by
  posts_vencidos desc,
  p95_staleness_days desc,
  total_posts desc;
```

Criterios de conclusao:

- impacto saudavel: queda da pressao em posts `warm`/`old` ja cobertos, sem
  aumento de risco em `needs_coverage`;
- impacto insuficiente: posts antigos ja cobertos continuam dominando atraso e
  batch;
- impacto inconclusivo: dados ainda sem janela suficiente para comparar,
  exigindo nova checagem antes da decisao.

Resultado esperado:

- decisao documentada sobre a migration de `next_check`;
- insumo para a Fase 2 da Sprint 2, focada em lote `50`, guardrail `6` e
  decisao final de manter ou ajustar a regra.

Resultado observado:

- `old_30d_plus | covered_3_49 | priority_band = 2`
  - `total_posts = 1021`
  - `posts_vencidos = 824`
  - `posts_no_batch_atual = 7`
  - `p95_staleness_days = 6.00`
- `old_30d_plus | covered_3_49 | priority_band = 1`
  - `total_posts = 1002`
  - `posts_vencidos = 778`
  - `posts_no_batch_atual = 5`
  - `p95_staleness_days = 5.91`
- `old_30d_plus | covered_3_49 | priority_band = 3`
  - `total_posts = 485`
  - `posts_vencidos = 338`
  - `posts_no_batch_atual = 6`
  - `p95_staleness_days = 3.00`
- `warm_8_30d | covered_3_49 | priority_band = 2`
  - `total_posts = 324`
  - `posts_vencidos = 313`
  - `posts_no_batch_atual = 0`
  - `p95_staleness_days = 4.02`
- `warm_8_30d | covered_3_49 | priority_band = 1`
  - `total_posts = 268`
  - `posts_vencidos = 232`
  - `posts_no_batch_atual = 1`
  - `p95_staleness_days = 5.83`

Leitura:

- os grupos `overchecked_*` e bandas `5` e `6` aparecem com `p95` muito baixo,
  em geral entre `0.20` e `0.70` dias, sem dominar o atraso total
- isso indica que a desaceleracao de posts muito checados e bandas altas
  parece estar funcionando como esperado
- o backlog pesado continua concentrado em `covered_3_49`, sobretudo em
  `old_30d_plus` e `warm_8_30d` das bandas `1` e `2`
- o grupo `warm_8_30d | covered_3_49 | priority_band = 2` continua como sinal
  forte de baixa aderencia do batch atual, com `313` vencidos e `0` itens no
  batch

Interpretacao:

- houve impacto saudavel da migration sobre os grupos que ela pretendia
  desacelerar
- nao ha evidência nesta leitura de que posts superchecados ou bandas altas
  estejam pressionando indevidamente a fila
- o problema remanescente parece ser operacional:
  - capacidade pratica insuficiente para o volume das bandas baixas e medias
  - distribuicao insuficiente do batch atual
  - possivel necessidade de revisar refill/cotas antes de nova mudanca de
    `next_check`

Conclusao:

- decisao recomendada: manter a regra atual de `next_check` em observacao
- nao ha sinal forte para ajustar novamente a frequencia neste momento
- o proximo ajuste deve priorizar capacidade e distribuicao da fila, nao uma
  nova mudanca na logica temporal

Saida da Fase 1:

- a migration nova de `next_check` pode ser considerada funcional do ponto de
  vista de desaceleracao de `warm/old` muito checados
- a principal frente aberta passa a ser a Fase 2 da Sprint 2:
  - verificar se lote `50` com guardrail `6` esta suficiente
  - revisar refill/cotas por banda
  - decidir se o ajuste deve ser de capacidade, distribuicao ou combinacao dos
    dois

#### Fase 2 - Capacidade do batch e distribuicao operacional

Objetivo:

- confirmar se o lote atual do worker consegue sustentar a cobertura minima e a
  fila normal ao mesmo tempo;
- medir se a fatia guardrail de `6` slots e suficiente para `needs_coverage`;
- decidir se o gargalo principal deve ser tratado com aumento de capacidade,
  ajuste de refill/cotas por banda ou combinacao dos dois.

Atividades da fase:

- [ ] Atividade 4: verificar se lote `50` com guardrail `6` esta suficiente.
- [x] Atividade 5: decidir se o ajuste deve atacar capacidade, distribuicao ou
  ambos.

Criterio de saida da fase:

- leitura objetiva sobre suficiência ou insuficiência do lote atual;
- leitura objetiva sobre suficiência ou insuficiência do guardrail atual;
- decisao documentada sobre o proximo ajuste operacional antes de qualquer
  mudanca em SQL.

#### Atividade 4 - Verificar se lote `50` com guardrail `6` esta suficiente

Status: concluida em 2026-06-16.

Objetivo:

- testar a hipótese central deixada pela Fase 1:
  a regra de `next_check` parece saudavel, mas a capacidade pratica do batch
  pode nao estar chegando bem aos grupos criticos;
- medir se `50` slots totais, com `6` reservados ao guardrail, sustentam:
  - `recent_4_7d / needs_coverage`;
  - backlog normal de `warm_8_30d` e `old_30d_plus / covered_3_49`;
  - distribuicao minima entre bandas `1` e `2`.

Perguntas de analise:

- os `6` slots de guardrail estao absorvendo os grupos `needs_coverage`
  vencidos sem deixar acumulacao relevante?
- o lote restante de `44` slots esta chegando de forma suficiente aos grupos
  `covered_3_49` de bandas `1` e `2`?
- a fila parece curta demais para a base atual ou apenas mal distribuida?
- o refill global esta compensando bem a sobra de cotas ou esta deixando grupos
  criticos de fora?

Etapas:

1. Somar os grupos `needs_coverage` e medir:
   - `total_posts`
   - `posts_vencidos`
   - `posts_no_batch_atual`
   - `p95_staleness_days`
2. Comparar a pressao de `needs_coverage` com a fatia protegida de `6` slots.
3. Somar os grupos `covered_3_49` de bandas `1` e `2` em `warm_8_30d` e
   `old_30d_plus` para medir a fila normal de maior pressao.
4. Comparar o volume vencido desses grupos com sua presenca no batch atual.
5. Classificar o comportamento em uma das leituras:
   - capacidade suficiente e distribuicao ruim;
   - capacidade insuficiente com distribuicao razoavel;
   - capacidade e distribuicao insuficientes ao mesmo tempo.
6. Registrar se o gargalo principal parece estar:
   - no tamanho total do lote;
   - na fatia guardrail;
   - nas cotas/refill;
   - ou em combinacao desses fatores.

Query sugerida - guardrail:

```sql
select
  video_age_bucket,
  priority_band,
  sum(total_posts) as total_posts,
  sum(posts_vencidos) as posts_vencidos,
  sum(posts_no_batch_atual) as posts_no_batch_atual,
  max(pior_p95_staleness_days) as pior_p95_staleness_days
from (
  select
    video_age_bucket,
    priority_band,
    total_posts,
    posts_vencidos,
    posts_no_batch_atual,
    p95_staleness_days as pior_p95_staleness_days
  from public.v_dashboard_queue_bottleneck_status
  where check_band = 'needs_coverage'
) q
group by
  video_age_bucket,
  priority_band
order by
  posts_vencidos desc,
  pior_p95_staleness_days desc,
  total_posts desc;
```

Query sugerida - fila normal mais pressionada:

```sql
select
  video_age_bucket,
  priority_band,
  sum(total_posts) as total_posts,
  sum(posts_vencidos) as posts_vencidos,
  sum(posts_no_batch_atual) as posts_no_batch_atual,
  max(p95_staleness_days) as pior_p95_staleness_days
from public.v_dashboard_queue_bottleneck_status
where
  check_band = 'covered_3_49'
  and video_age_bucket in ('warm_8_30d', 'old_30d_plus')
  and priority_band in (1, 2)
group by
  video_age_bucket,
  priority_band
order by
  posts_vencidos desc,
  pior_p95_staleness_days desc,
  total_posts desc;
```

Criterios de conclusao:

- se `needs_coverage` continuar acumulando vencidos com baixa presenca no
  batch, a fatia guardrail `6` pode estar insuficiente;
- se `covered_3_49` de bandas `1` e `2` continuar com centenas de vencidos e
  presenca residual no batch, a fila normal pode estar subdimensionada ou mal
  distribuida;
- se ambos ocorrerem ao mesmo tempo, o problema passa a ser de capacidade total
  mais distribuicao.

Resultado esperado:

- leitura objetiva sobre o lote `50`;
- leitura objetiva sobre o guardrail `6`;
- base numerica para a Atividade 5.

Resultado observado:

- leitura consolidada do guardrail `needs_coverage`:
  - total de grupos relevantes: `12`
  - `total_posts = 174`
  - `posts_vencidos = 146`
  - `posts_no_batch_atual = 6`
  - principal concentracao:
    - `recent_4_7d | priority_band = 1`: `68` posts, `61` vencidos, `1` no batch
    - `recent_4_7d | priority_band = 2`: `39` posts, `39` vencidos, `3` no batch
    - `recent_4_7d | priority_band = 3`: `17` posts, `17` vencidos, `1` no batch
- leitura consolidada da fila normal mais pressionada:
  - grupos avaliados:
    - `old_30d_plus | priority_band = 2`
    - `old_30d_plus | priority_band = 1`
    - `warm_8_30d | priority_band = 2`
    - `warm_8_30d | priority_band = 1`
  - `total_posts = 2615`
  - `posts_vencidos = 2147`
  - `posts_no_batch_atual = 13`
  - principais casos:
    - `old_30d_plus | priority_band = 2`: `1021` posts, `824` vencidos, `7` no batch
    - `old_30d_plus | priority_band = 1`: `1002` posts, `778` vencidos, `5` no batch
    - `warm_8_30d | priority_band = 2`: `324` posts, `313` vencidos, `0` no batch
    - `warm_8_30d | priority_band = 1`: `268` posts, `232` vencidos, `1` no batch

Leitura:

- a fatia guardrail de `6` slots esta sendo totalmente ocupada, mas nao esta
  conseguindo drenar a acumulacao de `needs_coverage`
- o foco mais sensivel do guardrail esta em `recent_4_7d`, justamente a janela
  que ainda deveria receber cobertura rapida
- a fila normal de maior pressao esta muito maior do que a capacidade pratica
  do batch atual consegue absorver
- o caso de `warm_8_30d | priority_band = 2` com `313` vencidos e `0` itens no
  batch reforca que nao e apenas um problema de volume; ha tambem problema de
  distribuicao/refill

Classificacao da suficiência atual:

- guardrail `6`: insuficiente para a pressao atual
- lote `50`: insuficiente para a fila normal mais pressionada
- distribuicao do batch: insuficiente nos grupos criticos de bandas `1` e `2`

Diagnostico:

- o problema atual parece ser de capacidade total e distribuicao ao mesmo tempo
- o guardrail esta no limite e mesmo assim deixa acumulacao relevante de
  `recent_4_7d / needs_coverage`
- a fila normal segue com backlog muito alto em `covered_3_49` de bandas
  baixas, com presenca pequena no batch
- o refill/cotas atuais nao parecem estar levando slots suficientes aos grupos
  mais pressionados

Conclusao:

- `lote 50 + guardrail 6` nao parece suficiente para a base atual
- aumentar apenas o guardrail provavelmente ajudaria a cobertura minima, mas
  deixaria a fila normal ainda mais pressionada se o lote total nao crescer
- revisar apenas o refill/cotas ajudaria a distribuicao, mas nao resolve
  sozinho o volume acumulado atual

Decisao para a Atividade 5:

- comparar caminhos que combinem:
  - aumento moderado de capacidade total
  - aumento moderado da fatia guardrail
  - revisao de refill/cotas para bandas `1` e `2`

#### Atividade 5 - Decidir se o ajuste deve atacar capacidade, distribuicao ou ambos

Status: proposta em elaboracao.

Objetivo:

- transformar os achados da Sprint 2 em uma decisao operacional clara;
- definir a proxima mudanca com o menor risco possivel para cobertura minima e
  backlog normal;
- evitar nova mudanca prematura em `next_check` quando o problema parece estar
  no lote ou no refill.

Opcoes a comparar:

- manter lote `50` e aumentar apenas a fatia guardrail;
- manter lote `50` e revisar cotas/refill por banda;
- aumentar lote total e manter a logica atual;
- combinar aumento moderado de lote com ajuste de guardrail e refill.

Etapas:

1. Revisar a conclusao da Atividade 4.
2. Classificar a causa dominante:
   - guardrail insuficiente;
   - fila normal insuficiente;
   - refill/cotas insuficientes;
   - causa mista.
3. Escolher a menor mudanca que responda ao gargalo dominante.
4. Registrar risco esperado de cada caminho:
   - impacto em cobertura minima;
   - impacto em backlog de bandas `1` e `2`;
   - impacto potencial em custo e volume de writes.
5. Definir recomendacao final da Sprint 2:
   - manter como esta por mais observacao;
   - ajustar capacidade;
   - ajustar distribuicao;
   - ajustar ambos.

Criterios de conclusao:

- a decisao final precisa apontar primeiro o alvo da mudanca, nao apenas o
  sintoma observado;
- se houver proposta de ajuste, ela deve vir antes de qualquer SQL com:
  - objetivo;
  - grupo que se pretende melhorar;
  - risco aceito;
  - criterio de validacao.

Resultado esperado:

- decisao operacional documentada;
- proposta curta do proximo ajuste;
- ponte clara entre Sprint 2 e eventual mudanca SQL ou teste operacional.

Proposta inicial:

- manter a revisao recente como base conceitual: `next_check` precisa continuar
  favorecendo posts novos/recentes e desacelerando posts antigos ja cobertos;
- ajustar a regra temporal para refletir melhor o ciclo horario real do worker
  e o baixo valor analitico de `old_30d_plus`;
- tratar a proxima iteracao como mudanca combinada de:
  - regra de `next_check`;
  - capacidade total do batch;
  - fatia guardrail;
  - distribuicao/refill por banda.

Regra proposta para simulacao:

- regra base por banda para grupos sensiveis:
  - banda `6`: `1h`
  - banda `5`: `2h`
  - banda `4`: `3h`
  - banda `3`: `4h`
  - banda `2`: `8h`
  - banda `1`: `12h`
- `total_checagens < 3`:
  - manter guardrail e politica de cobertura minima
- `new_0_3d` e `recent_4_7d`:
  - usar a regra base por banda
- `warm_8_30d` com `total_checagens >= 3`:
  - bandas `5` e `6`: `12h`
  - bandas `1` a `4`: `24h`
- `old_30d_plus` com `total_checagens >= 3`:
  - todas as bandas: `24h`

Leitura critica da proposta:

- ponto forte:
  - reduz a recorrencia desnecessaria de `old_30d_plus`, liberando capacidade
    para cobertura minima e backlog mais relevante
- ponto forte:
  - alinha a banda `6` ao ciclo real do worker horario, removendo a assimetria
    de uma banda `6` mais rapida que a propria frequencia operacional
- risco:
  - posts `warm_8_30d` ainda podem carregar alguma tracao residual; desacelerar
    demais esse grupo pode reduzir sensibilidade analitica
- risco:
  - se a mudanca ocorrer sem ajuste de lote, guardrail e refill, a melhora pode
    ser real mas insuficiente, como ocorreu na rodada anterior

Hipotese operacional:

- a nova regra deve reduzir demanda recorrente de `old_30d_plus` e bandas
  altas ja cobertas;
- essa reducao por si so ajuda, mas nao deve resolver completamente o backlog
  atual se `lote 50 + guardrail 6` permanecerem iguais;
- a melhora sustentavel exige validar a combinacao:
  - `next_check` mais aderente
  - capacidade total maior
  - fatia guardrail maior
  - distribuicao melhor nas bandas `1` e `2`

Algoritmo de simulacao proposto:

Objetivo:

- prever matematicamente se a mudanca melhora a fila antes de alterar o SQL de
  producao;
- permitir avaliacao offline do andamento da fila sobre o mesmo snapshot da
  base;
- estimar reducao de:
  - posts vencidos
  - `p95_staleness_days`
  - pressao no guardrail
  - pressao em `warm/old covered_3_49`

Entradas minimas:

- snapshot atual de `post_update_queue`
- `post_id`
- `priority_score`
- `priority_band`
- `last_checked`
- `next_check`
- `post_date`
- `needs_update`
- `total_checagens`
- `failure_status`
- pertencimento ao batch atual

Query de entrada recomendada:

- `sql/dml/export_queue_simulation_snapshot.sql`

Uso operacional da query:

1. rodar `sql/dml/export_queue_simulation_snapshot.sql` no banco;
2. exportar o resultado em CSV;
3. usar o CSV como entrada do script:
   - `scripts/queue_simulation/simulate_queue_offline.py`

Ideia do algoritmo:

1. Construir uma tabela base por post elegivel.
2. Recalcular `priority_band` e `video_age_bucket` conforme a regra atual do
   sistema.
3. Calcular `next_check_simulado` conforme uma configuracao de entrada da
   simulacao.
4. Fixar uma grade de tempo de simulacao:
   - por exemplo `72h`, em passos de `1h`, coerentes com o worker.
5. Para cada hora simulada:
   - marcar quais posts ficariam `due_now` segundo a configuracao escolhida;
   - montar o batch usando as mesmas regras de:
     - guardrail
     - cotas por banda
     - refill global
6. Ao "executar" um post no batch:
   - atualizar `last_checked` simulado para a hora corrente;
   - incrementar `total_checagens` simulado;
   - recalcular o proximo `next_check` pela mesma configuracao.
7. Repetir o processo ate o final da janela.
8. Ao final, consolidar as metricas da fila simulada.

Metricas de saida recomendadas:

- total de posts vencidos por hora
- composicao do batch por hora, com contagem por:
  - `video_age_bucket`
  - `check_band`
  - `priority_band`
- total de posts vencidos por:
  - `video_age_bucket`
  - `check_band`
  - `priority_band`
- media e `p95` de atraso simulado
- total de execucoes consumidas por:
  - guardrail
  - bandas `1` a `6`
- tempo medio para um post sair de `needs_coverage`
- backlog residual em:
  - `recent_4_7d / needs_coverage`
  - `warm_8_30d / covered_3_49`
  - `old_30d_plus / covered_3_49`

Criterio matematico de melhora:

- melhora minima esperada para aprovar a proposta:
  - queda material de vencidos em `recent_4_7d / needs_coverage`
  - queda material de backlog em bandas `1` e `2`
  - nenhuma piora relevante no `p95` dos grupos sensiveis
- melhora ideal:
- reduzir carga recorrente de `old_30d_plus`
- liberar execucoes para cobertura minima
- aumentar a participacao real de `warm/old covered_3_49` criticos no batch

Decisao recomendada neste momento:

- nao promover a nova regra apenas por intuicao;
- criar um script offline para simular o andamento da fila a partir do
  snapshot atual;
- fazer a configuracao da simulacao receber como parametros:
  - regra de `next_check`
  - lote total
  - fatia guardrail
  - cotas por banda
  - politica de refill
- exportar tambem a composicao do batch por iteracao em:
  - `hourly_batch_mix.csv`
- usar o script para avaliar qualquer proposta futura antes de alterar o SQL
  de producao.

### Fechamento da Sprint 2 - regra aprovada para producao

Regra aprovada apos simulacao offline:

- manter `batch_size = 50` e `guardrail_slots = 6`
- adotar o breakdown operacional:
  - `needs_coverage`: `< 3`
  - `covered_3_20`: `3..20`
  - `overchecked_21_100`: `21..100`
  - `overchecked_101_plus`: `101+`
- aplicar `next_check` minimo de `84h` para:
  - `warm_8_30d` com `total_checagens >= 21`
  - `old_30d_plus` com `total_checagens >= 21`
- manter:
  - `new_0_3d` e `recent_4_7d` na regra base por banda
  - `warm_8_30d` com `3..20` checagens em:
    - `12h` para bandas `5` e `6`
    - `24h` para bandas `1` a `4`
  - `old_30d_plus` com `3..20` checagens em `24h`

Evidencia que sustentou a decisao:

- simulacao de `260h` com `old_30d_plus >= 21 -> 84h` terminou com `2624`
  posts vencidos
- simulacao de `260h` com `warm_8_30d >= 21 -> 84h` e
  `old_30d_plus >= 21 -> 84h` terminou com `2558`
- ao desconsiderar as primeiras `36h`, o cenario final ainda permaneceu melhor:
  - fim `66` posts abaixo do cenario com `old` apenas
  - media da janela `36h..260h` `26,48` posts menor

Decisao operacional:

- promover a regra final para SQL
- recalcular `next_check` da fila existente na migration
- atualizar queries e dashboards para o novo breakdown de `check_band`
- manter o simulador offline como etapa obrigatoria antes de novas mudancas de
  fila ou rechecagem

Status da Atividade 5:

- concluida
- decisao final: atacar principalmente distribuicao temporal da fila via
  `next_check`, mantendo a capacidade atual (`batch 50` e `guardrail 6`)
- implementacao concluida na migration:
  - `sql/migrations/2026-06-16_008_queue_next_check_84h_rebucket_up.sql`
- validacao informada:
  - SQL atualizado
  - fila recalculada corretamente no ambiente

### Documentacao relacionada

- [25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md](../social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md)
- [08_QUEUE_CAPACITY_TEST.md](../social_media/08_QUEUE_CAPACITY_TEST.md)
- [09_QUEUE_SLICING_AND_RESCHEDULING.md](../social_media/09_QUEUE_SLICING_AND_RESCHEDULING.md)
- [05_DECISOES_TECNICAS.md](05_DECISOES_TECNICAS.md)

### Entregas

- Decisao documentada: manter regra atual ou ajustar.
- Caso haja ajuste, regra definida antes de qualquer mudanca SQL.
- Evidencia de impacto no backlog operacional e na cobertura minima.

### Estimativa

`1` a `2` dias.

---

## Sprint 3 - Dashboard MVP analitico

### Objetivo

Transformar o Streamlit em ferramenta interna util para leitura executiva e estudos de mercado automotivo.

### Escopo fechado do sprint

Este sprint deve fechar apenas o MVP analitico do dashboard com dados reais,
sem abrir uma nova frente de produto.

Inclui:

- validar contratos das views minimas do dashboard no Supabase
- fechar `Overview` como leitura macro da base monitorada
- substituir mock da `Visao geral` de `Creators` por dados reais
- implementar `YouTube > Melhores 7d` com `v_dashboard_post_growth_7d`
- garantir leitura de Data Quality antes de qualquer ranking
- ajustar estados vazios, mensagens de erro e textos executivos do MVP

Nao inclui:

- implementar `Hot now`
- abrir nova modelagem SQL fora das views necessarias ao MVP
- adicionar cadastro operacional novo como escopo principal do sprint
- evoluir enrichment, classificacao ou modulos de IA

### Estado atual observado

Status observado no repositorio em 2026-06-18:

- `Overview` ja consome views reais de creators, atividade semanal e Fenabrave
- `Data quality` ja possui leitura real e bloco operacional proprio
- `Criador individual` ja consome `v_dashboard_creator_summary`,
  `v_dashboard_creator_weekly_activity` e `v_dashboard_creator_weekly_audience`
- `Visao geral` de `Creators` ainda usa `get_creator_mock_rows()`
- `YouTube > Melhores 7d` ainda esta em placeholder
- `Hot now` continua explicitamente fora do MVP atual

Leitura:

- o bloqueio principal do Sprint 3 nao e mais infraestrutura
- o trabalho agora e consolidacao de produto sobre views reais
- a lacuna mais visivel do MVP esta em fechar ranking semanal e remover mocks

### Atividades detalhadas

#### Atividade 1 - Validar views minimas do MVP no Supabase

Status: em andamento.

Objetivo:

- confirmar que todas as views do Sprint 3 respondem com schema esperado,
  leitura segura e dados suficientes para o app online

Views minimas:

- `public.v_dashboard_guardrail_coverage_status`
- `public.v_dashboard_dead_post_validation_status`
- `public.v_dashboard_creator_summary`
- `public.v_dashboard_creator_weekly_activity`
- `public.v_dashboard_creator_weekly_audience`
- `public.v_dashboard_post_growth_7d`
- `public.v_dashboard_fenabrave_monthly_segments`

Etapas:

1. Confirmar se cada view existe no repositorio SQL e no ambiente alvo.
2. Validar leitura com a credencial segura usada pelo Streamlit.
3. Confirmar nomes de colunas, tipos esperados e presenca de linhas reais.
4. Registrar qualquer lacuna como:
   - falha de permissao
   - view nao aplicada
   - coluna divergente
   - base vazia
5. Corrigir primeiro o contrato de dados antes de ajustar UI.

Criterio de conclusao:

- todas as views minimas respondem com leitura valida no app
- qualquer divergencia de schema entre SQL e Streamlit esta resolvida
- o app nao depende de dado mock para telas do escopo do sprint

Dependencias:

- views aplicadas no ambiente alvo
- credencial de leitura do Streamlit funcionando
- contrato esperado das colunas revisado no app

Saida esperada:

- checklist unico de validacao das views do Sprint 3
- lista de gaps por view, quando houver
- decisao objetiva sobre o que ja pode seguir para UI e o que precisa ajuste

Evidencia de conclusao:

- consultas funcionando no app ou no ambiente alvo
- nomes de colunas confirmados contra o uso em `dashboard/streamlit_app.py`
- registro dos gaps resolvidos ou classificados

Execucao pratica:

1. Revisar as views uma a uma.
2. Comparar retorno real com os campos usados pelo Streamlit.
3. Corrigir primeiro qualquer mismatch de contrato.
4. Liberar somente depois a frente visual dependente da view.

Resultado observado em 2026-06-18:

- validacao executada no ambiente Supabase alvo com leitura real via REST
- `6` das `7` views minimas responderam com `200`
- `1` view minima retornou `404` no schema cache

Status por view:

- `public.v_dashboard_guardrail_coverage_status`: `ok_env`
- `public.v_dashboard_dead_post_validation_status`: `ok_env`
- `public.v_dashboard_creator_summary`: `ok_env`
- `public.v_dashboard_creator_weekly_activity`: `ok_env`
- `public.v_dashboard_creator_weekly_audience`: `ok_env`
- `public.v_dashboard_fenabrave_monthly_segments`: `ok_env`
- `public.v_dashboard_post_growth_7d`: `gap_env_missing`

Contrato observado nas views criticas:

- `v_dashboard_creator_summary` respondeu com colunas esperadas do app, incluindo:
  - `entity_name`
  - `platform`
  - `username`
  - `channel_id`
  - `followers`
  - `post_count`
  - `total_views`
  - `total_likes`
  - `total_comments`
  - `engagement_rate_pct`
  - `latest_post_date`
  - `latest_collected_at`
- `v_dashboard_creator_weekly_activity` respondeu com colunas esperadas do app, incluindo:
  - `week_start`
  - `week_end`
  - `week_label`
  - `video_type`
  - `videos_publicados`
  - `views_novas`
  - `views_growth_pct_vs_prev_week`
  - `likes_novos`
  - `comentarios_novos`
- `v_dashboard_creator_weekly_audience` respondeu no ambiente com contrato
  funcional para a UI atual:
  - retornou `latest_collected_at`
  - a aba `Criador individual` ja usa acompanhamento semanal de seguidores por
    `followers_delta_vs_prev_week` e `followers_weekly_status`
  - `followers_latest_collected_at` aparece apenas como expectativa antiga de
    contrato, nao como campo efetivamente usado na UI

Leitura:

- o item `1` da Atividade `1` foi fechado para existencia no repositorio e quase
  fechado para existencia no ambiente
- o bloqueador objetivo restante e `public.v_dashboard_post_growth_7d`, ausente
  no ambiente alvo
- no repositorio, a definicao de `sql/ddl/views/006_create_v_dashboard_post_growth_7d.sql`
  existe, mas nao segue o mesmo padrao explicito de `GRANT SELECT` visto nas
  demais views do dashboard
- o ponto de `latest_collected_at` versus `followers_latest_collected_at` nao e
  bloqueador funcional: a decisao e manter o comportamento atual da UI e
  atualizar apenas a documentacao do contrato esperado

Decisao para seguir:

- tratar `v_dashboard_post_growth_7d` como bloqueador da futura Atividade `4`
- manter `latest_collected_at` como campo valido no contexto atual
- remover da documentacao da atividade a expectativa de
  `followers_latest_collected_at` como requisito funcional da UI atual

### Passo a passo operacional da Atividade 1

#### Etapa 1.1 - Preparar a validacao

Objetivo:

- iniciar a atividade com uma lista fechada de views, telas consumidoras e
  campos esperados, evitando validacao solta ou parcial

Passo a passo:

1. Abrir `dashboard/streamlit_app.py` e listar onde cada view e consumida.
2. Consolidar a lista das views minimas do sprint:
   - `v_dashboard_guardrail_coverage_status`
   - `v_dashboard_dead_post_validation_status`
   - `v_dashboard_creator_summary`
   - `v_dashboard_creator_weekly_activity`
   - `v_dashboard_creator_weekly_audience`
   - `v_dashboard_post_growth_7d`
   - `v_dashboard_fenabrave_monthly_segments`
3. Mapear para cada view:
   - tela do app que depende dela
   - funcao que a consome
   - campos minimos esperados
4. Definir uma planilha ou checklist unico da atividade com uma linha por view.

Saida esperada:

- inventario fechado das views do Sprint 3
- mapa view -> tela -> funcao -> campos minimos

#### Etapa 1.2 - Confirmar existencia da view no repositorio SQL

Objetivo:

- garantir que a definicao versionada da view existe no repositorio antes de
  validar ambiente e UI

Passo a passo:

1. Localizar o arquivo SQL da view em `sql/ddl/views/`.
2. Confirmar se a definicao da view esta versionada no repositorio.
3. Verificar se o arquivo inclui `GRANT SELECT` para `anon` e
   `authenticated` quando isso fizer parte do contrato atual do dashboard.
4. Registrar o nome do arquivo SQL correspondente no checklist.

Classificacao:

- `ok_repo`: view encontrada e versionada
- `gap_repo_missing`: view nao encontrada no repositorio
- `gap_repo_grant`: view existe, mas falta grant esperado

Saida esperada:

- checklist preenchido com o arquivo SQL de cada view

#### Etapa 1.3 - Confirmar existencia da view no ambiente alvo

Objetivo:

- validar se a view que existe no Git tambem esta aplicada no Supabase usado
  pelo dashboard

Passo a passo:

1. Executar uma consulta simples na view no ambiente alvo.
2. Verificar se a leitura retorna:
   - linhas
   - zero linhas sem erro
   - erro de permissao
   - erro de objeto inexistente
3. Registrar o resultado bruto de cada consulta.
4. Se a view nao existir no ambiente, classificar antes de tentar corrigir UI.

Classificacao:

- `ok_env`: view existe e responde
- `gap_env_missing`: view nao aplicada no ambiente
- `gap_env_permission`: view existe, mas a credencial nao consegue ler

Saida esperada:

- checklist com status de ambiente por view

#### Etapa 1.4 - Validar leitura com a credencial real do Streamlit

Objetivo:

- confirmar que o problema nao esta apenas no banco, mas tambem nao aparece na
  camada real usada pelo app

Passo a passo:

1. Reproduzir a leitura pelo mesmo caminho usado no app, preferencialmente via
   `get_view_rows`, `get_single_row_view` ou `get_filtered_rows`.
2. Observar se a consulta funciona com a credencial configurada para o
   Streamlit.
3. Registrar se o retorno falha por:
   - RLS ou grant
   - timeout
   - coluna ausente
   - filtro incompatível
4. Confirmar se a falha acontece na view ou apenas no modo como o app chama a
   view.

Classificacao:

- `ok_app_read`
- `gap_app_permission`
- `gap_app_filter`
- `gap_app_timeout`

Saida esperada:

- validacao real do caminho de leitura do app

#### Etapa 1.5 - Validar contrato de colunas contra o app

Objetivo:

- garantir que cada coluna esperada pelo Streamlit existe com nome e semantica
  compativeis

Passo a passo:

1. Para cada view, listar as colunas retornadas.
2. Comparar com os campos usados no `dashboard/streamlit_app.py`.
3. Classificar cada coluna como:
   - presente e compativel
   - presente com nome divergente
   - ausente
   - presente, mas com semantica duvidosa
4. Registrar os campos bloqueadores da UI.
5. Priorizar correcoes de contrato antes de qualquer ajuste visual.

Exemplos criticos do sprint:

- `v_dashboard_creator_summary`:
  - `entity_name`
  - `platform`
  - `followers`
  - `post_count`
  - `total_views`
  - `engagement_rate_pct`
- `v_dashboard_creator_weekly_activity`:
  - `week_label`
  - `week_end`
  - `video_type`
  - `videos_publicados`
  - `views_novas`
  - `likes_novos`
  - `comentarios_novos`
- `v_dashboard_creator_weekly_audience`:
  - `followers_delta_vs_prev_week`
  - `followers_weekly_status`
  - `latest_collected_at`

Classificacao:

- `ok_schema`
- `gap_schema_missing_column`
- `gap_schema_renamed_column`
- `gap_schema_semantic_mismatch`

Saida esperada:

- contrato de colunas validado por view

#### Etapa 1.6 - Validar qualidade minima do retorno

Objetivo:

- separar view tecnicamente legivel de view realmente utilizavel no dashboard

Passo a passo:

1. Validar se a view retorna linhas reais quando deveria retornar base ativa.
2. Verificar excesso de nulos em campos que sustentam cards ou ranking.
3. Verificar se datas e periodos fazem sentido para a janela esperada da tela.
4. Verificar se agregacoes zeradas ou vazias representam:
   - falta real de dados
   - falha de pipeline
   - problema no SQL
5. Marcar casos em que a UI precisa fallback honesto em vez de correcao SQL.

Classificacao:

- `ok_data`
- `gap_data_empty`
- `gap_data_high_nulls`
- `gap_data_unexpected_period`
- `gap_data_incoherent_aggregation`

Saida esperada:

- leitura minima de utilidade por view

#### Etapa 1.7 - Registrar gaps e priorizar correcao

Objetivo:

- transformar a validacao em decisao executavel para o restante do sprint

Passo a passo:

1. Consolidar todos os gaps encontrados em uma lista unica.
2. Classificar cada gap por severidade:
   - bloqueador
   - importante
   - cosmetico
3. Relacionar cada gap com a tela afetada:
   - `Overview`
   - `Creators`
   - `YouTube > Melhores 7d`
   - `Data quality`
4. Corrigir primeiro gaps que impedem leitura real ou quebram o contrato.
5. Deixar ajustes cosmeticos para a Atividade 6.

Regra de prioridade:

- primeiro: view ausente, falta de permissao, coluna ausente
- depois: base vazia inesperada, semantica divergente, filtro quebrado
- por ultimo: copy, ordenacao fina, acabamento visual

Saida esperada:

- backlog curto de gaps da Atividade 1 ja priorizado para execucao

#### Etapa 1.8 - Emitir decisao de liberacao por tela

Objetivo:

- encerrar a Atividade 1 com uma resposta objetiva sobre o que ja pode avancar
  no sprint

Passo a passo:

1. Marcar cada view como:
   - liberada
   - liberada com ressalvas
   - bloqueada
2. Consolidar por tela:
   - `Overview`
   - `Creators > Visao geral`
   - `Criador individual`
   - `YouTube > Melhores 7d`
3. Registrar a proxima acao imediata por frente:
   - seguir para UI
   - corrigir SQL
   - corrigir grants/permissoes
   - revisar chamada do app
4. Encerrar a atividade somente quando a sequencia do sprint estiver clara.

Criterio de fechamento operacional:

- todas as views do sprint estao classificadas
- cada tela do MVP tem status de liberacao
- o proximo passo do sprint esta definido sem ambiguidade

#### Atividade 2 - Fechar a pagina `Overview`

Status: em andamento.

Objetivo:

- consolidar a `Overview` como leitura macro confiavel da base monitorada, com
  foco em contexto executivo e nao em profundidade de ranking

Escopo da tela:

- KPIs de base monitorada
- serie semanal de atividade recente
- bloco macro de Fenabrave
- ponte explicita para `Data quality`

Etapas:

1. Confirmar que os KPIs resumem a base monitorada e nao sugerem universo total
   do mercado.
2. Validar o comportamento do slider de semana fechada e seus estados vazios.
3. Revisar legendas, titulos e captions para leitura executiva curta.
4. Garantir que erros de view nao quebrem a tela inteira.
5. Confirmar coerencia visual entre overview, cards e grafico recente.

Criterio de conclusao:

- `Overview` abre com dados reais sem depender de placeholder estrutural
- estados sem dados ficam explicitos e honestos
- a tela comunica base monitorada, janela temporal e limite analitico da leitura

Dependencias:

- Atividade 1 concluida para `v_dashboard_creator_summary`
- Atividade 1 concluida para `v_dashboard_creator_weekly_activity`
- Atividade 1 concluida para `v_dashboard_fenabrave_monthly_segments`

Saida esperada:

- `Overview` funcional com texto executivo consolidado
- grafico semanal e cards coerentes com a leitura macro da base
- navegacao clara para `Data quality`

Evidencia de conclusao:

- tela abrindo com dados reais
- slider semanal funcionando com base preenchida e tambem em vazio controlado
- ausencia de placeholder estrutural no fluxo principal da overview

Execucao pratica:

1. Validar a leitura dos KPIs macro.
2. Ajustar a serie de atividade recente e o comportamento do slider.
3. Revisar textos, captions e limite de interpretacao da tela.
4. Confirmar fallback honesto quando alguma view vier vazia.

#### Atividade 3 - Trocar `Creators > Visao geral` para dados reais

Status: aberta.

Objetivo:

- substituir a carteira mockada por leitura real de `v_dashboard_creator_summary`
  para transformar a tela em comparativo util da base monitorada

Estado atual:

- a tela ainda usa `get_creator_mock_rows()`
- o criador individual ja esta ligado a views reais

Etapas:

1. Trocar a fonte principal da tela para `v_dashboard_creator_summary`.
2. Manter filtros coerentes com as colunas realmente disponiveis.
3. Recalcular KPIs agregados sobre a base filtrada real.
4. Ajustar ranking comparativo para nao depender de campos inexistentes.
5. Exibir mensagens claras quando a view vier vazia ou parcial.
6. Garantir consistencia entre `Visao geral` e `Criador individual`.

Criterio de conclusao:

- a visao geral de creators nao usa mais mock
- ranking, cards e filtros refletem dados reais da base
- a navegacao entre visao geral e criador individual permanece coerente

Dependencias:

- Atividade 1 concluida para `v_dashboard_creator_summary`
- alinhamento minimo com os campos do criador individual ja existente

Saida esperada:

- pagina comparativa de creators baseada apenas em leitura real
- KPIs agregados e ranking coerentes com a carteira monitorada
- remocao do uso de `get_creator_mock_rows()` na visao geral

Evidencia de conclusao:

- codigo da tela apontando para view real
- cards e ranking refletindo a base filtrada real
- tela funcionando mesmo com base parcial ou vazia

Execucao pratica:

1. Trocar a fonte dos dados.
2. Recalcular agregacoes com a base real filtrada.
3. Ajustar ranking e textos para os campos realmente disponiveis.
4. Validar consistencia com a tela de criador individual.

#### Atividade 4 - Implementar `YouTube > Melhores videos 7d`

Status: aberta.

Objetivo:

- transformar o placeholder em uma tela funcional de crescimento semanal usando
  `v_dashboard_post_growth_7d`

Escopo minimo:

- ranking semanal de videos em crescimento
- contexto temporal claro
- filtros minimos que nao compliquem o MVP
- mensagens de Data Quality antes da leitura do ranking

Definicoes aprovadas para a tela:

- o filtro `Todos` deve mostrar sempre os `10` melhores videos no ranking geral
- o filtro `Long` deve mostrar sempre os `10` melhores videos `long`
- o filtro `Short` deve mostrar sempre os `10` melhores videos `short`
- `Melhores videos 7d` deve usar `7` dias completos fechados, excluindo o dia atual
  parcial
- a `v_dashboard_post_growth_7d` deve materializar essa regra com janela iniciando em `date_trunc('day', now()) - interval '7 days'` e terminando antes de `date_trunc('day', now())`
- a janela precisa aparecer explicitamente na tela, para evitar leitura
  ambigua de periodo

Etapas:

1. Confirmar contrato da `v_dashboard_post_growth_7d`.
2. Definir campos minimos do ranking:
   - video
   - creator
   - views, likes e comentarios absolutos do ultimo snapshot
   - data do ultimo snapshot
   - quantidade de snapshots na janela
   - crescimento 7d como criterio de ordenacao
   - ordenacao oficial aplicada na consulta ao Supabase, sem reordenacao global no Streamlit
   - registrar como ponto em aberto a rechecagem futura da regra fina de desempate apos avaliacao visual da tela
3. Aplicar o comportamento fixo de `top 10` por filtro:
   - `Todos`
   - `Long`
   - `Short`
4. Explicitar na UI a semantica da janela:
   - `7` dias completos fechados
   - dia atual parcial fora da leitura
5. Desenhar a tela com foco em leitura rapida, nao em exploracao pesada.
6. Tratar base vazia, erro de permissao e dado parcial.
7. Garantir que a tela nao concorra semanticamente com `Hot now`.

Criterio de conclusao:

- a pagina `YouTube > Melhores videos 7d` deixa de ser placeholder
- o ranking semanal e alimentado por view real
- a leitura deixa claro que se trata de crescimento semanal, nao de tracao em
  tempo quase real

Dependencias:

- Atividade 1 concluida para `v_dashboard_post_growth_7d`
- decisao minima de layout para ranking semanal

Saida esperada:

- nova pagina real de ranking semanal
- leitura objetiva do que cresceu na janela de 7 dias
- top `10` consistente por filtro
- janela sem ambiguidade temporal na UI
- separacao semantica clara entre crescimento semanal e futuro `Hot now`

Evidencia de conclusao:

- rota do menu deixa de chamar `render_placeholder_page`
- tela exibe ranking real usando `v_dashboard_post_growth_7d`
- estados de erro e vazio ficam controlados

Execucao pratica:

1. Confirmar colunas e significado da view.
2. Montar cards e tabela ou ranking com foco em leitura rapida.
3. Incluir contexto temporal da janela analisada.
4. Validar fallback para view vazia ou indisponivel.

Expansao proposta fora do escopo minimo original, mas com alto ganho de usabilidade:

- exibir thumbnail real no ranking `Melhores videos 7d`
- abrir o video ao clicar na thumbnail
- abrir o video ao clicar no titulo

Detalhamento de execucao da expansao:

1. Compor a URL do video diretamente no Streamlit usando `post_id` como `video_id` do YouTube.
2. Compor a URL da thumbnail diretamente no Streamlit usando `https://i.ytimg.com/vi/VIDEO_ID/mqdefault.jpg`.
3. Nao alterar a `v_dashboard_post_growth_7d`, para evitar impacto operacional desnecessario.
4. Atualizar a UI para:
   - trocar placeholder por thumbnail real
   - transformar thumbnail em ancora clicavel
   - transformar titulo em ancora clicavel
5. Validar fallback para ausencia de thumbnail e ausencia de link.

Status desta expansao:

- ainda nao faz parte do criterio de conclusao minimo da Atividade 4
- deve ser tratada como melhoria priorizada da mesma tela apos estabilizacao do ranking atual
- decisao tomada: manter a feature na camada Streamlit, sem alterar SQL nem contrato operacional da view

#### Atividade 5 - Garantir `Data Quality` antes dos rankings

Status: aberta.

Objetivo:

- manter a regra do projeto de que nenhuma leitura analitica relevante deve
  aparecer sem contexto minimo de confiabilidade operacional

Etapas:

1. Definir onde a sinalizacao de qualidade aparece antes dos rankings.
2. Reusar views ja consolidadas:
   - `v_dashboard_guardrail_coverage_status`
   - `v_dashboard_dead_post_validation_status`
3. Decidir o formato minimo:
   - banner
   - cards
   - aviso contextual
4. Garantir que a sinalizacao seja visivel sem poluir a navegacao.
5. Evitar que uma falha de Data Quality derrube toda a tela analitica.

Criterio de conclusao:

- rankings e comparativos aparecem acompanhados de contexto de confiabilidade
- o dashboard nao incentiva leitura cega de ranking sem sinal operacional

Dependencias:

- Atividade 1 concluida para as views de Data Quality
- definicao das telas que exibem ranking ou comparativo

Saida esperada:

- padrao unico de sinalizacao de confiabilidade antes de leitura analitica
- reaproveitamento consistente dos dois KPIs principais de qualidade

Evidencia de conclusao:

- ranking semanal e comparativos acompanhados por contexto de qualidade
- comportamento resiliente quando a leitura de qualidade falhar

Execucao pratica:

1. Definir o componente de contexto de qualidade.
2. Aplicar esse componente nas telas comparativas do sprint.
3. Verificar se a leitura de qualidade informa sem bloquear a navegacao.
4. Ajustar o texto para orientar interpretacao e nao apenas mostrar alerta.

#### Atividade 6 - Fechamento de UX e robustez do MVP

Status: aberta.

Objetivo:

- fechar o MVP com acabamento suficiente para uso interno recorrente

Etapas:

1. Revisar textos de ajuda, captions e titulos das paginas do sprint.
2. Ajustar estados vazios para cada tela principal.
3. Revisar mensagens de erro para diferenciar:
   - indisponibilidade de view
   - falta de permissao
   - ausencia real de dados
4. Validar navegacao lateral do fluxo:
   - `Overview`
   - `Creators`
   - `YouTube > Melhores 7d`
   - `Data quality`
5. Fazer smoke test local do app apos as trocas do sprint.

Criterio de conclusao:

- o app pode ser usado internamente sem ambiguidade forte de leitura
- falhas comuns aparecem de forma clara e controlada
- a navegacao do MVP fica consistente entre paginas reais

Dependencias:

- Atividades 2 a 5 implementadas ou suficientemente estabilizadas

Saida esperada:

- acabamento final do sprint
- experiencia consistente entre telas reais do MVP
- smoke test local documentado como ultimo passo de fechamento

Evidencia de conclusao:

- navegacao lateral funcionando nas paginas do escopo
- mensagens de erro e vazio revisadas
- validacao final local sem quebra evidente de fluxo

Execucao pratica:

1. Fazer uma passada completa no fluxo do MVP.
2. Revisar textos, captions, erros e estados vazios.
3. Ajustar consistencia visual e de navegacao.
4. Rodar smoke test local antes de encerrar o sprint.

### Ordem recomendada de execucao

1. Validar views reais e contratos no Supabase.
2. Fechar `Overview` com leitura macro confiavel.
3. Remover mock da `Visao geral` de `Creators`.
4. Implementar `YouTube > Melhores videos 7d`.
5. Aplicar o gate de `Data Quality` antes dos rankings.
6. Fazer acabamento final de UX, estados vazios e smoke test.

### Plano de execucao por atividades

| Ordem | Atividade | Objetivo operacional | Dependencia principal | Saida esperada | Evidencia de pronto |
| --- | --- | --- | --- | --- | --- |
| 1 | Validar views minimas | garantir contrato de dados antes da UI | views aplicadas + leitura segura | checklist de validacao por view | consultas e colunas confirmadas |
| 2 | Fechar `Overview` | consolidar a leitura macro da base | creators + weekly activity + Fenabrave validados | overview real e sem placeholder estrutural | tela com dados reais e fallback honesto |
| 3 | Trocar `Creators > Visao geral` | remover mock e ligar carteira real | `v_dashboard_creator_summary` validada | comparativo de creators com base real | ausencia de `get_creator_mock_rows()` na visao geral |
| 4 | Implementar `YouTube > Melhores videos 7d` | entregar ranking semanal funcional | `v_dashboard_post_growth_7d` validada | nova pagina real de crescimento | tela deixa de ser placeholder |
| 5 | Garantir `Data Quality` antes dos rankings | reforcar a confiabilidade da leitura | views de Data Quality validadas | padrao unico de contexto de qualidade | ranking com sinal operacional visivel |
| 6 | Fechamento de UX e robustez | preparar o sprint para uso interno recorrente | atividades anteriores estabilizadas | acabamento final e smoke test | fluxo do MVP navegavel e consistente |

### Checklist de acompanhamento

- [ ] Atividade 1 concluida
- [ ] Atividade 2 concluida
- [ ] Atividade 3 concluida
- [ ] Atividade 4 concluida
- [ ] Atividade 5 concluida
- [ ] Atividade 6 concluida

### Documentacao relacionada

- [29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md](../dashboard/29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md)
- [16_ONLINE_DASHBOARD_SUPABASE_SPEC.md](../dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md)
- [33_CREATOR_VIEW_STREAMLIT_SPEC.md](../dashboard/33_CREATOR_VIEW_STREAMLIT_SPEC.md)
- [34_CREATOR_WEEKLY_TIMESERIES_CONTRACT.md](../dashboard/34_CREATOR_WEEKLY_TIMESERIES_CONTRACT.md)

### Entregas

- Dashboard interno navegavel com telas principais do MVP ligadas a dados reais.
- `Overview` fechada como leitura macro da base monitorada.
- `Creators > Visao geral` sem mock e coerente com `Criador individual`.
- `YouTube > Melhores videos 7d` implementada com ranking semanal real.
- Confirmacao de que rankings aparecem depois dos sinais de confiabilidade.
- Evidencia de que o MVP ficou pronto para uso interno recorrente.

### Pre-flight

Status: concluido em 2026-06-16.

Resultado observado:

- `dashboard/streamlit_app.py` ja concentra uma base funcional real do app
- `Overview` existe, mas ainda depende de placeholders para a area analitica principal
- `Creators` ja tem navegacao e estrutura visual, mas a visao geral ainda usa
  dados mockados
- `Criador individual` ja conversa com views reais de creator
- `YouTube > Melhores 7d` ainda esta em placeholder
- as views principais do MVP existem no repositorio SQL
- a pasta `dashboard/.streamlit/` ainda nao foi criada, entao faltam os
  arquivos auxiliares de configuracao e exemplo de secrets

Decisao para seguir no Sprint 3:

- nao e necessario reorganizar a estrutura do dashboard antes de continuar
- a frente correta agora e validar as views no Supabase e substituir mocks e
  placeholders por leituras reais nas paginas do MVP

### Ambiente online

Status: concluido em 2026-06-16.

Resultado observado:

- Streamlit e Supabase estao conectados e funcionando
- branch e arquivo principal do app estao operacionais para o MVP atual
- o Sprint 3 deixa de ter bloqueio de ambiente e passa a focar:
  - validacao das views reais
  - fechamento de `Overview`
  - substituicao dos mocks em `Creators`
  - implementacao de `YouTube > Melhores 7d`

### Estimativa

`2` a `4` dias.

---

## Sprint 4 - Ranking Hot Now

### Objetivo

Criar a primeira metrica temporal de oportunidade, separada da logica operacional da fila.

### Atividades

- Criar view SQL `v_dashboard_hot_now`.
- Calcular `velocity_6h`, `previous_velocity` e `acceleration`.
- Definir filtros minimos de historico para evitar falso positivo.
- Separar ranking analitico da fila operacional.
- Conectar a view no Streamlit.

### Documentacao relacionada

- [26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md](../social_media/26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md)
- [13_HYBRID_SCORE_EVALUATION_STRATEGY.md](../social_media/13_HYBRID_SCORE_EVALUATION_STRATEGY.md)
- [29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md](../dashboard/29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md)

### Entregas

- Ranking `Hot Now` baseado em aceleracao real.
- Base para detectar videos automotivos ganhando tracao.
- Limitacoes documentadas para historico insuficiente.

### Estimativa

`1` a `2` dias.

---

## Sprint 5 - Fontes externas

### Objetivo

Consolidar dados externos sem comprometer governanca, rastreabilidade ou qualidade.

### Atividades Fenabrave

- Validar rotina mensal.
- Decidir se modelagem por segmento e suficiente por enquanto.
- Avaliar necessidade de `ingestion_runs` e validacoes persistidas.

### Atividades Carros na Web

- Validar `anos_modelo_validos.csv`.
- Confirmar se captura e etica, repetivel e sem bypass.
- Decidir se a fonte segue em CSV/local, pausa ou evolui para schema.

### Documentacao relacionada

- [23_FENABRAVE_PHASE1_INGESTION_SPEC.md](../external_data/23_FENABRAVE_PHASE1_INGESTION_SPEC.md)
- [00_OFFLINE_OPERATIONS_CALENDAR.md](../external_data/00_OFFLINE_OPERATIONS_CALENDAR.md)
- [27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md](../external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md)
- [22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md](../external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md)

### Entregas

- Fenabrave com rotina mensal clara.
- Decisao objetiva sobre Carros na Web: continuar, pausar ou limitar escopo.
- Proximas necessidades de modelagem externa registradas.

### Estimativa

`2` a `4` dias.

---

## Sprint 6 - Enrichment e produto analitico

### Objetivo

Preparar a proxima camada de inteligencia, com classificacao e insights acionaveis para marketing automotivo.

### Atividades

- Definir classificacao minima de videos: nicho, subnicho e tipo.
- Priorizar campos de enrichment.
- Definir onde LLM entra no pipeline.
- Desenhar primeiras perguntas de produto:
  - creators emergentes
  - temas em alta
  - videos fora da curva
  - oportunidades por nicho automotivo
- Atualizar backlog e roadmap com proximos modulos.

### Documentacao relacionada

- [01_BACKLOG.md](01_BACKLOG.md)
- [02_ROADMAP.md](02_ROADMAP.md)
- [05_DECISOES_TECNICAS.md](05_DECISOES_TECNICAS.md)

### Entregas

- Plano de enrichment priorizado.
- Proximo roadmap orientado a produto.
- Separacao clara entre ideias, execucao e decisoes tecnicas.

### Estimativa

`2` a `3` dias.

---

## Procedimento para novas demandas

Quando surgir uma nova demanda durante um sprint:

1. Verificar se a demanda pertence ao sprint ativo.
2. Se pertencer, executar conforme roadmap e documentacao relacionada.
3. Se nao pertencer, perguntar ao usuario se deseja prosseguir.
4. Se o usuario nao quiser desviar o sprint, registrar a demanda no backlog.
5. Se o usuario aprovar o desvio, registrar a decisao em `05_DECISOES_TECNICAS.md` quando houver impacto tecnico relevante.

## Commit sugerido

```bash
git commit -m "docs(roadmap): define agenda de sprints do projeto"
```
