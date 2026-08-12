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
Sprint ativo: Sprint 5 - Fontes externas
Ultimo sprint concluido: Sprint 4 - Ranking Hot Now
Datas: a definir conforme disponibilidade do usuario
```

Enquanto o Sprint 5 estiver ativo, apenas tarefas relacionadas a fontes
externas, rotina repetivel de Fenabrave e decisao de viabilidade do Carros na
Web devem ser executadas automaticamente. Alteracoes fora deste escopo devem
aguardar confirmacao.

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

Status: concluida.

Objetivo:

- substituir a carteira mockada por leitura real de `v_dashboard_creator_summary`
  para transformar a tela em comparativo util da base monitorada

Estado atual:

- a `Visao geral de criadores` passou a consumir `v_dashboard_creator_summary`
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

Resultado observado em 2026-06-19:

- `render_creator_overview_page()` deixou de usar `get_creator_mock_rows()`
- a tela passou a ler `v_dashboard_creator_summary` diretamente
- os KPIs de `Criadores ativos`, `Seguidores monitorados`, `Total de videos`,
  `Total de views`, `Total de likes` e `Total de comentarios` passaram a ser
  calculados sobre a base real filtrada
- o ranking comparativo passou a usar os campos reais da view
- a tela ganhou fallback honesto para erro de leitura, base vazia e filtro sem
  linhas
- por acabamento estético, o ranking comparativo passou a exibir avatar do
  criador com base em `creators.avatar_url`

Evidencia complementar da camada de avatar:

- foi adicionada a coluna `avatar_url` em `public.creators`
- `v_dashboard_creator_summary` passou a expor `avatar_url`
- foi criado um backfill offline em `scripts/offline_backfill/backfill_creator_avatars.py`
- o backfill foi executado em 2026-06-19 com os seguintes resultados:
  - lote 1: `35` creators elegiveis, `20` processados, `20` atualizados, `0` erros
  - lote 2: cursor em `20`, nenhum creator restante sem `avatar_url`, status `completed`

Leitura de fechamento da Atividade 3:

- a visao geral de creators deixou de depender de mock
- a tela agora reflete a carteira real monitorada e ficou coerente com o
  restante do dashboard
- o uso de avatar foi tratado como melhoria estética da mesma frente, sem criar
  view nova

Definicao de negocio consolidada para engajamento na `Visao geral de criadores`:

- `engajamento` deve ser lido como taxa de resposta da audiencia monitorada
- em linguagem de negocio, a metrica mostra qual parcela das views gerou
  reacao explicita do publico por meio de likes e comentarios
- a formula oficial atualmente em uso e:
  `((likes + comments) / views) * 100`
- leitura executiva:
  - `views` respondem quem concentrou mais alcance
  - `engajamento` responde quem ativou melhor a propria audiencia
  - um creator pode liderar em volume e nao liderar em engajamento, o que
    indica comportamento diferente de consumo da base
- essa definicao permanece como referencia principal para ordenacao por
  `Engajamento` na visao comparativa de creators

#### Atividade 4 - Implementar `YouTube > Melhores videos 7d`

Status: concluida.

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
- a `v_dashboard_post_growth_7d` deve materializar essa regra pela data local de `America/Sao_Paulo`, convertendo `collected_at` antes do filtro
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

Resolucao documentada da regra temporal:

- a primeira implementacao sem hoje, baseada apenas em `date_trunc('day', now())`, foi insuficiente porque o Supabase operava em `UTC`
- isso permitia que snapshots ainda considerados "hoje" no Brasil permanecessem na janela
- a correcao definitiva foi mover a regra para a data local de `America/Sao_Paulo`, aplicando a conversao sobre `collected_at`
- a UI tambem foi ajustada para exibir `latest_snapshot` em `America/Sao_Paulo`

Evidencia de resolucao:

- o video `_B7xWH5n8UI` (`Avaliação JETOUR T2 2026 - UM MONSTRO OFFROAD QUE NÃO É OFFROAD`) aparecia indevidamente com `latest_collected_at = 2026-06-18 10:00:11.782639`
- o ambiente do Supabase confirmou `db_timezone = UTC`
- depois da correcao final e da validacao no Streamlit, o caso deixou de aparecer

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

Resultado observado em 2026-06-18:

- a pagina `YouTube > Melhores videos 7d` deixou de ser placeholder e passou a
  consumir `public.v_dashboard_post_growth_7d`
- a navegacao lateral foi atualizada para `YouTube > Melhores videos 7d`
- o filtro fixo `Todos`, `Long` e `Short` passou a buscar sempre o `top 10`
  direto na consulta ao Supabase
- a tela passou a exibir:
  - thumbnail real do YouTube
  - titulo clicavel
  - canal
  - tipo de video
  - data de publicacao
  - crescimento `7d`
  - views, likes e comentarios absolutos
  - ultimo snapshot
  - quantidade de snapshots
- a regra temporal foi estabilizada em `7` dias completos fechados pela data
  local de `America/Sao_Paulo`
- o caso de snapshot de "hoje" que entrava indevidamente no ranking foi
  removido apos a correcao final da view
- a tela passou por refinamento de UX no cabecalho, identidade visual dos
  icones, links, thumbnails e scroll interno da lista

Leitura de fechamento da Atividade 4:

- o objetivo funcional da atividade foi atingido
- a tela agora entrega ranking semanal real, com criterio temporal explicito e
  separacao semantica clara em relacao a `Hot now`
- permanecem apenas ajustes finos futuros de UX e eventual revisao da regra de
  desempate, sem bloquear o encerramento desta atividade

#### Nota de escopo removido - `Data Quality` antes dos rankings

Em 2026-06-20 foi decidido remover do Sprint 3 a exigencia de embutir contexto
de `Data Quality` dentro de cada ranking ou comparativo.

Motivo:

- o dashboard tem uso pessoal
- a view dedicada `Data quality` ja entrega o diagnostico operacional
  necessario
- esse requisito nao estava ancorado previamente em roadmap ou decisao tecnica
  do projeto; ele havia nascido apenas dentro da propria agenda do sprint

Referencia da decisao:

- `docs/project/05_DECISOES_TECNICAS.md`

#### Atividade 5 - Fechamento de UX e robustez do MVP

Status: em andamento.

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

- Atividades 2 a 4 implementadas e estabilizadas

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
5. Fazer acabamento final de UX, estados vazios e smoke test.

### Plano de execucao por atividades

| Ordem | Atividade | Objetivo operacional | Dependencia principal | Saida esperada | Evidencia de pronto |
| --- | --- | --- | --- | --- | --- |
| 1 | Validar views minimas | garantir contrato de dados antes da UI | views aplicadas + leitura segura | checklist de validacao por view | consultas e colunas confirmadas |
| 2 | Fechar `Overview` | consolidar a leitura macro da base | creators + weekly activity + Fenabrave validados | overview real e sem placeholder estrutural | tela com dados reais e fallback honesto |
| 3 | Trocar `Creators > Visao geral` | remover mock e ligar carteira real | `v_dashboard_creator_summary` validada | comparativo de creators com base real | ausencia de `get_creator_mock_rows()` na visao geral |
| 4 | Implementar `YouTube > Melhores videos 7d` | entregar ranking semanal funcional | `v_dashboard_post_growth_7d` validada | nova pagina real de crescimento | tela deixa de ser placeholder |
| 5 | Fechamento de UX e robustez | preparar o sprint para uso interno recorrente | atividades anteriores estabilizadas | acabamento final e smoke test | fluxo do MVP navegavel e consistente |

### Checklist de acompanhamento

- [x] Atividade 1 concluida
- [x] Atividade 2 concluida
- [x] Atividade 3 concluida
- [x] Atividade 4 concluida
- [x] Atividade 5 concluida

### Status consolidado em 2026-06-20

Leitura atual do Sprint 3:

- o sprint saiu da fase de infraestrutura e contrato minimo de dados
- `Overview`, `Criador individual`, `Data quality` e `YouTube > Melhores videos 7d`
  ja estao ligados a dados reais
- `Creators > Visao geral` tambem passou a consumir dados reais e deixou de
  depender de mock
- a etapa de `YouTube > Melhores videos 7d` pode ser considerada concluida
- o fechamento final de UX, estados vazios, erros e smoke test foi aceito como
  concluido para o uso pessoal atual do dashboard
- o Sprint 3 pode ser tratado como encerrado do ponto de vista funcional e
  documental

Classificacao atual das atividades:

- Atividade 1: concluida
- Atividade 2: concluida
- Atividade 3: concluida
- Atividade 4: concluida
- Atividade 5: concluida

Percentual qualitativo estimado:

- Sprint 3 em `100%` de execucao real no escopo aprovado

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
- Evidencia de que o MVP ficou pronto para uso interno recorrente.
- Sprint 3 encerrado sem pendencias funcionais no escopo aprovado.

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

### Open point prioritario para fechamento do Sprint 3

#### Recalibrar `next_check` apos aumento de capacidade

Status: aberto e prioritario para o fim do Sprint 3.

Contexto operacional:

- o worker de metricas `postMetrics` passou a rodar a cada `30 minutos`
- a cadencia anterior era horaria, entao a capacidade potencial de snapshots foi
  duplicada
- o `youtube_main_scraper`, responsavel por discovery de novos posts, passou a
  rodar a cada `3 horas`
- a otimizacao de Cloud Run para maximo `1 vCPU` e `256 MB` de RAM reduziu o
  custo por execucao e permitiu aumentar a frequencia sem mudar a arquitetura

Decisao para o Sprint 3:

- nao alterar `next_check` no meio do fechamento do MVP sem validacao de impacto
- manter a regra atual em producao enquanto o dashboard estabiliza as leituras
  de fila, data quality e gargalo operacional
- tratar a revisao de `next_check` como item prioritario de saida do Sprint 3

Criterios para a revisao:

- comparar a capacidade diaria teorica antes e depois da mudanca de frequencia
- acompanhar `posts_acima_3_2d`, `p95_staleness_days`, `posts_vencidos` e
  `posts_no_batch_atual`
- validar quota da YouTube API, duracao das execucoes no Cloud Run e volume de
  writes no Supabase
- reduzir intervalos de `next_check` onde a nova capacidade justificar, sem
  sacrificar `needs_coverage`, posts novos/recentes ou estabilidade da fila
- evitar aumento de frequencia em posts ja saturados antes de confirmar que o
  gargalo de cobertura minima esta resolvido

### Estimativa

`2` a `4` dias.

---

## Sprint 4 - Ranking Hot Now

### Objetivo

Criar a primeira metrica temporal de oportunidade, separada da logica operacional da fila.

O Sprint 4 deve responder, de forma exploratoria e auditavel:

```text
Quais videos automotivos estao ganhando tracao agora, considerando velocidade
recente e aceleracao, sem confundir esse ranking com prioridade operacional da
fila de coleta?
```

### Escopo funcional

Inclui:

- modelar a view `public.v_dashboard_hot_now`;
- calcular `velocity_6h`, `previous_velocity` e `acceleration`;
- aplicar filtros minimos de historico para reduzir falso positivo;
- excluir videos indisponiveis da leitura analitica;
- conectar o ranking em `dashboard/streamlit_app.py`;
- documentar limitacoes e criterio de uso.

Nao inclui:

- alterar a fila operacional `v_post_update_queue_batch`;
- promover `priority_score_v2` para producao;
- mudar `calculate_next_check(...)`;
- criar enrichment por IA;
- transformar o ranking em decisao automatica de marketing.

### Atividades

- [x] Etapa 1: confirmar contrato analitico e criterios de elegibilidade.
- [x] Etapa 2: desenhar e criar a view SQL `v_dashboard_hot_now`.
- [x] Etapa 3: validar a view com dados reais e casos de borda.
- [x] Etapa 4: conectar `Hot now` no Streamlit.
- [x] Etapa 5: fazer fechamento de UX, documentacao e decisao de pronto.

### Planejamento por etapas

#### Etapa 1 - Contrato analitico e elegibilidade

Status: concluida em 2026-06-20.

Objetivo:

- definir exatamente o que significa "quente agora" no contexto automotivo;
- separar crescimento real de ruido causado por historico insuficiente;
- alinhar a view com a decisao tecnica de manter `priority_score_v2` fora da
  fila operacional.

Atividades:

1. Revisar o baseline do score hibrido `v2` e a estrategia de avaliacao.
2. Confirmar os campos disponiveis em `post_metrics_history` e `posts`.
3. Definir a metrica base para o score temporal inicial:
   - primeira opcao: score simples derivado de views, likes e comentarios;
   - alternativa conservadora: velocidade e aceleracao por views, com likes e
     comentarios como contexto.
4. Definir criterios minimos de elegibilidade:
   - quantidade minima de snapshots;
   - existencia de snapshot recente;
   - existencia de baseline anterior util;
   - exclusao de `unavailable` fora de auditoria;
   - tratamento de videos sem delta suficiente.
5. Registrar a decisao de metrica antes de criar a view.

Passo a passo operacional:

1. Confirmar a decisao de escopo do Sprint 4:
   - `Hot now` e ranking analitico de oportunidade;
   - `Hot now` nao altera fila, worker, `next_check` nem `priority_score_v2`;
   - a tela deve complementar `Melhores videos 7d`, nao duplicar a leitura
     semanal fechada.
2. Revisar a decisao tecnica vigente:
   - confirmar que `priority_score_v2` permanece em segundo plano;
   - confirmar que a metrica temporal deve priorizar velocidade recente e
     aceleracao;
   - registrar qualquer mudanca conceitual em `05_DECISOES_TECNICAS.md` antes
     de implementar SQL.
3. Revisar o baseline do score hibrido `v2`:
   - identificar por que `base_popularity` dominava o score;
   - confirmar que videos com pouco historico nao devem liderar por fallback;
   - extrair o cuidado principal para o `Hot now`: nao premiar apenas volume
     acumulado.
4. Confirmar o contrato minimo das tabelas de origem:
   - `post_metrics_history`: snapshots historicos de views, likes, comentarios
     e `collected_at`;
   - `posts`: metadados do video, status, creator, data de publicacao e tipo;
   - `creators`: nome do canal e avatar, se a view precisar enriquecer a UI.
5. Levantar a densidade real de historico para saber se a janela de `6h` e
   viavel:

```sql
select
  p.video_type,
  count(*) as total_posts,
  count(*) filter (where h.snapshot_count >= 3) as posts_com_3_snapshots,
  count(*) filter (where h.latest_collected_at >= now() - interval '12 hours') as posts_com_snapshot_recente
from public.posts p
left join (
  select
    post_id,
    count(*) as snapshot_count,
    max(collected_at) as latest_collected_at
  from public.post_metrics_history
  group by post_id
) h on h.post_id = p.post_id
where coalesce(p.failure_status, 'active') <> 'unavailable'
group by p.video_type
order by p.video_type;
```

6. Validar se existem snapshots suficientes para comparar janelas:
   - snapshot atual;
   - snapshot proximo de `6h` atras;
   - snapshot proximo de `24h` atras;
   - ou outro baseline aprovado se a densidade real nao suportar a janela
     ideal.
7. Escolher a metrica base inicial:
   - opcao preferencial conservadora: `views` como base de velocidade e
     aceleracao, com likes/comentarios como contexto;
   - opcao expandida: score ponderado por views, likes e comentarios;
   - a escolha deve favorecer interpretabilidade na primeira versao.
8. Definir formula conceitual do ranking:

```text
velocity_6h = (score_agora - score_6h_atras) / horas_entre_snapshots
previous_velocity = (score_6h_atras - score_24h_atras) / horas_entre_snapshots
acceleration = velocity_6h - previous_velocity
hot_now_rank_score = funcao simples de velocity_6h + acceleration
```

9. Definir tolerancia para busca de baseline:
   - exemplo: aceitar snapshot entre `4h` e `8h` atras como baseline de `6h`;
   - exemplo: aceitar snapshot entre `18h` e `30h` atras como baseline anterior;
   - se a tolerancia for ampla demais, marcar o ranking como exploratorio.
10. Definir filtros minimos de elegibilidade:
    - excluir `failure_status = 'unavailable'`;
    - exigir pelo menos `3` snapshots;
    - exigir snapshot atual recente;
    - exigir baseline de `6h` e baseline anterior;
    - exigir delta recente positivo para entrar no ranking principal;
    - manter `eligibility_status` para explicar exclusoes ou insuficiencia.
11. Definir campos obrigatorios do contrato da view:
    - identificacao: `post_id`, `creator_id`, `creator_name`, `title`;
    - contexto: `video_type`, `published_at`, `latest_collected_at`;
    - qualidade: `snapshot_count`, `eligibility_status`;
    - metricas: `velocity_6h`, `previous_velocity`, `acceleration`,
      `hot_now_rank_score`;
    - leitura complementar: deltas recentes de views, likes e comentarios.
12. Definir ordenacao inicial:
    - ranking principal por `hot_now_rank_score desc`;
    - desempate por `acceleration desc`;
    - segundo desempate por `velocity_6h desc`;
    - evitar ordenar por views totais como criterio principal.
13. Definir como a UI deve explicar a metrica:
    - "videos ganhando tracao agora";
    - "baseado em velocidade recente e aceleracao";
    - "ranking exploratorio, dependente de densidade de snapshots";
    - diferenciar claramente de crescimento acumulado em `7` dias.
14. Registrar a decisao final da Etapa 1 no sprint antes da Etapa 2:

```text
Metrica base escolhida:
Janela recente:
Janela anterior:
Tolerancia de baseline:
Filtros de elegibilidade:
Ordenacao oficial:
Limitacoes conhecidas:
Decisao:
```

15. So iniciar a criacao da `v_dashboard_hot_now` depois que os itens acima
    estiverem preenchidos.

Dependencias:

- `docs/social_media/26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md`
- `docs/social_media/13_HYBRID_SCORE_EVALUATION_STRATEGY.md`
- `docs/project/05_DECISOES_TECNICAS.md`

Saida esperada:

- contrato textual da view `v_dashboard_hot_now`;
- lista de campos obrigatorios;
- filtros minimos aprovados;
- confirmacao de que o ranking e analitico, nao operacional.

Criterio de pronto:

- e possivel escrever a SQL sem ambiguidades sobre janela, baseline, ordenacao
  e exclusao de dados invalidos.

Resultado observado em 2026-06-20:

- a consulta real ao Supabase confirmou `4022` posts ativos elegiveis apos
  excluir `20` posts com `post_collection_failures.status = unavailable`
- `v_post_priority_score_features_v2` retornou `4042` linhas, coerente com o
  total bruto de posts antes da exclusao de indisponiveis
- distribuicao de historico entre posts ativos:
  - `full`: `3947`
  - `partial`: `45`
  - `low`: `30`
- distribuicao por tipo:
  - `long`: `1658` ativos, `1633` com baseline `6h/24h`
  - `short`: `2364` ativos, `2314` com baseline `6h/24h`
- snapshots correntes:
  - `1132` posts com snapshot corrente nas ultimas `12h`
  - `2214` posts com snapshot corrente nas ultimas `24h`
- a tolerancia ampla de baseline mostrou risco de falso positivo, porque alguns
  posts tinham baseline nominal de `6h` com distancia real de `42h`, `77h` ou
  `84h`
- com criterio conservador para o `Hot now v1`:
  - snapshot corrente ate `12h`
  - baseline de `6h` entre `6h` e `8h`
  - baseline anterior entre `18h` e `30h`
  - velocidade recente positiva
  - exclusao de indisponiveis
- o ranking inicial teria `11` videos elegiveis:
  - `8` long
  - `3` short
  - `7` com aceleracao positiva

Decisao de contrato para a Etapa 2:

```text
Metrica base escolhida:
- views por hora como metrica principal de velocidade e aceleracao.
- likes e comentarios entram como contexto exibido, nao como peso do score v1.

Janela recente:
- baseline nominal de 6h.
- aceitar somente baseline real entre 6h e 8h atras.

Janela anterior:
- baseline nominal de 24h.
- aceitar baseline real entre 18h e 30h atras.

Snapshot atual:
- exigir snapshot corrente com no maximo 12h de idade.

Formula:
- velocity_6h = (views_atual - views_6h) / horas_entre_snapshots.
- previous_velocity = (views_6h - views_24h) / horas_entre_baselines.
- acceleration = velocity_6h - previous_velocity.
- hot_now_rank_score = velocity_6h + greatest(acceleration, 0).

Filtros de elegibilidade:
- excluir posts com status unavailable em post_collection_failures.
- exigir baseline 6h e baseline 24h dentro das tolerancias acima.
- exigir delta recente positivo de views.
- manter eligibility_status para explicar exclusoes.

Ordenacao oficial:
- hot_now_rank_score desc.
- acceleration desc como primeiro desempate.
- velocity_6h desc como segundo desempate.

Limitacoes conhecidas:
- o ranking sera inicialmente pequeno por usar tolerancia conservadora.
- isso e aceitavel para evitar falso positivo e preservar a leitura de
  oportunidade real.
- se a tela ficar vazia em algum momento, a expansao de tolerancia deve ser
  decisao documentada, nao ajuste silencioso.

Decisao:
- Atividade 1 concluida.
- Etapa 2 pode criar a view SQL `v_dashboard_hot_now` com esse contrato.
```

#### Etapa 2 - View SQL `v_dashboard_hot_now`

Status: concluida em 2026-06-20.

Objetivo:

- criar a camada SQL de consumo do ranking, mantendo calculo temporal no banco
  e evitando carregar historico bruto no Streamlit.

Atividades:

1. Criar arquivo novo em `sql/ddl/views/` para `v_dashboard_hot_now`.
2. Usar CTEs para separar:
   - snapshots recentes;
   - baseline de `6h` atras;
   - baseline anterior;
   - calculo de velocidade;
   - calculo de aceleracao;
   - ranking final.
3. Calcular campos minimos:
   - `post_id`;
   - `creator_id`;
   - `creator_name`;
   - `title`;
   - `video_type`;
   - `published_at`;
   - `latest_collected_at`;
   - `snapshot_count`;
   - `views_latest`;
   - `likes_latest`;
   - `comments_latest`;
   - `views_delta_recent`;
   - `likes_delta_recent`;
   - `comments_delta_recent`;
   - `velocity_6h`;
   - `previous_velocity`;
   - `acceleration`;
   - `hot_now_rank_score`;
   - `eligibility_status`.
4. Aplicar filtros:
   - remover `failure_status = 'unavailable'`;
   - exigir historico minimo;
   - evitar divisao por zero;
   - limitar ranking a videos com movimento recente real.
5. Conceder `GRANT SELECT` para `anon` e `authenticated`, seguindo o padrao das
   views do dashboard.

Dependencias:

- Etapa 1 concluida.

Saida esperada:

- arquivo SQL versionado para `public.v_dashboard_hot_now`;
- contrato de colunas estavel para o Streamlit;
- ranking ordenavel por `hot_now_rank_score` e explicavel por velocidade e
  aceleracao.

Criterio de pronto:

- a view compila localmente/por revisao SQL e esta pronta para aplicacao no
  Supabase;
- a SQL nao depende de funcao operacional da fila;
- a view nao altera tabelas nem workers.

Resultado observado em 2026-06-20:

- criado o arquivo SQL:
  - `sql/ddl/views/020_create_v_dashboard_hot_now.sql`
- a view criada foi:
  - `public.v_dashboard_hot_now`
- a SQL usa CTEs para separar:
  - posts indisponiveis;
  - ultimo snapshot por post;
  - contagem de snapshots;
  - metadados de post, creator e entity;
  - baseline mais proximo de `6h` dentro da tolerancia `6h-8h`;
  - baseline mais proximo de `24h` dentro da tolerancia `18h-30h`;
  - deltas, velocidade, velocidade anterior, aceleracao e elegibilidade
- a view nao usa:
  - `priority_score_v2`
  - `v_post_update_queue_batch`
  - `post_update_queue`
  - `calculate_next_check(...)`
  - `insert`, `update` ou `delete`
- a view exclui `post_collection_failures.status = 'unavailable'`
- a view expoe `eligibility_status` e `is_hot_now_eligible`
- `hot_now_rank_score` so e preenchido quando `eligibility_status = 'eligible'`
- foram incluidos `GRANT SELECT` para `anon` e `authenticated`

Contrato implementado:

```text
velocity_6h = (views_latest - views_6h) / horas_entre_latest_e_6h
previous_velocity = (views_6h - views_24h) / horas_entre_6h_e_24h
acceleration = velocity_6h - previous_velocity
hot_now_rank_score = velocity_6h + greatest(acceleration, 0)
```

Status de elegibilidade implementados:

- `no_snapshot`
- `insufficient_snapshots`
- `latest_snapshot_stale`
- `baseline_6h_missing`
- `baseline_24h_missing`
- `no_recent_views_delta`
- `eligible`

Validacao local executada:

- `git diff --check` sem erros
- revisao textual confirmou ausencia de dependencia operacional da fila
- `psql` e `supabase` CLI nao estao disponiveis localmente nesta maquina, entao
  a compilacao real no banco fica para a Etapa 3 ao aplicar/validar no Supabase

Decisao:

- Etapa 2 concluida do ponto de vista de repositorio e contrato SQL
- Etapa 3 deve aplicar ou validar `public.v_dashboard_hot_now` no Supabase e
  revisar o top do ranking com dados reais

#### Etapa 3 - Validacao com dados reais

Status: concluida em 2026-06-20.

Objetivo:

- confirmar que o ranking retorna oportunidades temporais plausiveis e nao
  apenas videos grandes, antigos ou com historico pobre.

Atividades:

1. Aplicar ou validar a view no Supabase.
2. Consultar o top do ranking:

```sql
select *
from public.v_dashboard_hot_now
order by hot_now_rank_score desc
limit 20;
```

3. Verificar casos de borda:
   - videos com poucos snapshots;
   - videos antigos com volume alto, mas sem aceleracao;
   - videos recentes com delta forte;
   - videos `short` versus `long`;
   - videos indisponiveis.
4. Comparar a leitura com `v_dashboard_post_growth_7d` para garantir separacao
   semantica:
   - `Melhores videos 7d`: crescimento semanal fechado;
   - `Hot now`: tracao recente e aceleracao.
5. Registrar limitacoes encontradas no proprio sprint.

Dependencias:

- Etapa 2 concluida;
- acesso de leitura ao Supabase com as views aplicadas.

Saida esperada:

- evidencias numericas do ranking;
- lista de ajustes necessarios antes da UI;
- decisao se a view esta pronta para consumo no app.

Criterio de pronto:

- top `20` revisado;
- pelo menos uma amostra de falso positivo analisada ou descartada;
- `Hot now` nao duplica semanticamente o ranking semanal de `7d`.

Resultado inicial em 2026-06-20:

- commit da Etapa 2 criado:
  - `054d45e feat(sql): cria view hot now`
- consulta REST ao Supabase para `public.v_dashboard_hot_now` retornou:

```text
status 404
code PGRST205
message Could not find the table 'public.v_dashboard_hot_now' in the schema cache
hint Perhaps you meant the table 'public.v_dashboard_post_growth_7d'
```

Leitura:

- a view `v_dashboard_hot_now` existe no repositorio em
  `sql/ddl/views/020_create_v_dashboard_hot_now.sql`
- a view ainda nao existe no Supabase no momento desta verificacao
- `psql` e `supabase` CLI nao estao disponiveis localmente nesta maquina
- nao ha `SUPABASE_DB_URL` configurado no `.env` operacional usado nesta frente

Proxima acao da Etapa 3:

1. Aplicar `sql/ddl/views/020_create_v_dashboard_hot_now.sql` no Supabase SQL
   Editor.
2. Reconsultar `public.v_dashboard_hot_now` via REST.
3. Revisar o top do ranking com dados reais.
4. Registrar o resultado observado antes de seguir para a integracao no
   Streamlit.

Resultado final em 2026-06-20:

- `SUPABASE_DB_URL` foi disponibilizada no `.env` local de
  `scripts/offline_backfill/`
- como `psql` e `supabase` CLI nao estavam disponiveis localmente, foi
  instalado o driver Python `pg8000` na `.venv` para conexao administrativa
  pontual
- `sql/ddl/views/020_create_v_dashboard_hot_now.sql` foi aplicado no Supabase
  via conexao Postgres
- a consulta REST a `public.v_dashboard_hot_now` passou a retornar `200`
- total retornado pela view: `4022` linhas
- distribuicao de elegibilidade:
  - `eligible`: `11`
  - `baseline_6h_missing`: `1081`
  - `insufficient_snapshots`: `50`
  - `latest_snapshot_stale`: `2880`
- top do ranking `Hot now` validado com dados reais:
  - `Lrro2uqNF58` | `long` | Meu Carro Life Style | score `736.6`
  - `0agSJfeXYqc` | `long` | CarroChefe | score `418.4331`
  - `4ePDRvnDyCI` | `long` | Meu Carro Life Style | score `413.4982`
  - `y71QviUz_O0` | `long` | stanleyravagnani | score `295.8159`
  - `KDp4IHEy0tU` | `short` | Carros com Tiago | score `263.3298`
- comparacao com o top `10` de `v_dashboard_post_growth_7d` mostrou `3`
  videos em comum:
  - `y71QviUz_O0`
  - `9D4SQbeDgaU`
  - `Bg7p2x8-r4Y`

Leitura:

- a view foi criada e esta exposta no Supabase
- o ranking e pequeno, como esperado pelo contrato conservador da Etapa 1
- a baixa sobreposicao com o top semanal confirma separacao semantica:
  - `Melhores videos 7d`: crescimento semanal fechado
  - `Hot now`: tracao recente com baselines proximos

Decisao:

- Etapa 3 concluida
- a view `v_dashboard_hot_now` esta pronta para consumo inicial no Streamlit
- a Etapa 4 pode conectar a pagina `YouTube > Hot now` sem alterar a SQL

#### Revisao pos-implantacao - overlap e Hot now 24h

Status: concluida em 2026-06-21.

Objetivo:

- revisar a elegibilidade do `Hot now` a luz da regra atual de `next_check`;
- medir a sobreposicao com `Melhores videos 7d`;
- substituir o contrato conservador `6h/24h` por um contrato mais aderente a
  base real monitorada.

Achados:

- a regra original de elegibilidade deixou a view pequena demais para o estado
  atual da coleta:
  - total na view: `4073`
  - `eligible`: `9`
  - `latest_snapshot_stale`: `2935`
  - `baseline_6h_missing`: `1075`
- o conflito principal apareceu na comparacao com `next_check`:
  - `1305` posts `latest_snapshot_stale` ainda estavam com `next_check` no
    futuro;
  - isso confirmou que boa parte das exclusoes vinha de uma regra de frescor
    mais exigente do que a cadencia operacional prometida pela fila.

Simulacao aprovada:

- manter bloqueios duros:
  - `no_snapshot`;
  - `insufficient_snapshots`.
- manter corte de frescor:
  - `latest_snapshot_stale` quando o ultimo snapshot tiver mais de `24h`.
- trocar o calculo temporal para snapshots reais consecutivos:
  - velocidade atual = ultimo snapshot vs snapshot anterior disponivel;
  - velocidade anterior = snapshot anterior vs penultimo disponivel;
  - aceleracao = velocidade atual - velocidade anterior.

Resultado da simulacao no universo do `Hot now`, excluindo `unavailable`:

- `sem_filtro_frescor`:
  - `4024` elegiveis
  - `1324` com aceleracao positiva
- `frescor_24h`:
  - `2125` elegiveis
  - `718` com aceleracao positiva
- `frescor_36h`:
  - `3125` elegiveis
  - `1075` com aceleracao positiva

Analise de overlap com `v_dashboard_post_growth_7d`:

- universo `Hot now 24h`: `2125` videos
- universo `Melhores videos 7d`: `3991` videos
- interseccao total: `2111` videos
- overlap do topo:
  - `top 10 x top 10`: `0`
  - `top 20 x top 20`: `3`
  - `top 50 x top 50`: `13`
- leitura:
  - a interseccao de universo e alta porque os dois rankings reaproveitam a
    base monitorada recente;
  - a sobreposicao baixa no topo confirma separacao semantica util:
    - `Melhores videos 7d`: crescimento semanal acumulado;
    - `Hot now 24h`: aceleracao recente com frescor operacionalmente
      plausivel.

Implementacao aplicada:

- `sql/ddl/views/020_create_v_dashboard_hot_now.sql` foi revisada para o
  modelo `Hot now 24h`;
- a view passou a:
  - excluir `unavailable`;
  - bloquear apenas `no_snapshot`, `insufficient_snapshots` e
    `latest_snapshot_stale > 24h`;
  - calcular velocidade e aceleracao com os tres snapshots mais recentes do
    proprio video;
  - manter o score como `velocidade_atual + greatest(aceleracao, 0)`.
- validacao real apos aplicar no Supabase:
  - `eligible`: `2125`
  - `latest_snapshot_stale`: `1899`
  - `insufficient_snapshots`: `49`

#### Etapa 4 - Integracao no Streamlit

Status: concluida em 2026-06-20.

Objetivo:

- transformar a pagina `Hot now` em uma tela real do dashboard, usando a view
  `v_dashboard_hot_now`.

Atividades:

1. Localizar a rota atual de `Hot now` em `dashboard/streamlit_app.py`.
2. Criar funcao de leitura da view com limite conservador, sem carregar
   historico bruto.
3. Implementar filtros minimos:
   - `Todos`;
   - `Long`;
   - `Short`.
4. Renderizar ranking com:
   - titulo do video;
   - creator;
   - tipo;
   - ultimo snapshot;
   - velocidade recente;
   - velocidade anterior;
   - aceleracao;
   - views/likes/comentarios recentes.
5. Reaproveitar o padrao visual de `YouTube > Melhores videos 7d` quando fizer
   sentido, sem criar identidade paralela.
6. Tratar estados:
   - view ausente;
   - base vazia;
   - historico insuficiente;
   - erro de permissao.

Dependencias:

- Etapa 3 concluida;
- contrato da view estavel.

Saida esperada:

- pagina `Hot now` funcional no dashboard;
- ranking carregado sob demanda via Supabase;
- mensagens claras quando o ranking nao puder ser calculado.

Criterio de pronto:

- a pagina deixa de ser placeholder;
- o ranking carrega sem erro com dados reais;
- a tela explica que a leitura e de tracao recente, nao de crescimento semanal
  fechado.

Resultado observado em 2026-06-20:

- a rota `YouTube > Hot now` deixou de chamar `render_placeholder_page`
- foi criada a funcao `render_youtube_hot_now_page()` em `dashboard/streamlit_app.py`
- a tela passou a consumir `public.v_dashboard_hot_now` via `get_filtered_rows`
- filtros implementados:
  - `Todos`
  - `Long`
  - `Short`
- a consulta usa:
  - `is_hot_now_eligible = true`
  - `order by hot_now_rank_score desc`
  - `limit 10`
- a pagina exibe:
  - thumbnail e titulo clicaveis para o YouTube
  - creator
  - tipo de video
  - ultimo snapshot
  - idade do snapshot
  - views totais
  - score
  - velocidade `6h`
  - velocidade anterior
  - aceleracao
  - delta recente de views
- estados tratados:
  - view indisponivel
  - base vazia
  - filtro sem videos elegiveis
- validacao local:
  - compilacao em memoria de `dashboard/streamlit_app.py`: `compile_ok`
  - consulta REST equivalente ao contrato da tela retornou `status 200`,
    `10` linhas e topo `Lrro2uqNF58` com score `736.6`

Leitura:

- a pagina esta pronta para uso inicial no Streamlit
- a integracao respeita o contrato conservador da view
- nao houve alteracao de SQL, fila operacional, worker ou `next_check`

Complemento em 2026-06-21:

- incluida a coluna `Views totais` logo apos o bloco do video na pagina
  `YouTube > Hot now`
- incluida no card a quantidade total de snapshots historicos do video
- removido o chip `Idade`, porque duplicava a informacao de data/hora do
  ultimo snapshot e podia ser confundido com idade do video
- incluido chip `Publicado DD/MM/AAAA` logo apos o chip de tipo de video
- observacao de uso: pela manha, os videos podem aparecer com `AC` negativo
  quando a velocidade recente fica abaixo da velocidade anterior
- nessa situacao, o `Score` fica igual a `V6`, porque o contrato atual usa
  `hot_now_rank_score = velocity_6h + greatest(acceleration, 0)`
- a avaliacao sobre `6h` ser uma janela curta demais deve ser tratada como
  ajuste de contrato em atividade posterior, nao como mudanca silenciosa da UI

#### Etapa 5 - Fechamento, documentacao e decisao de pronto

Status: concluida em 2026-06-21.

Objetivo:

- encerrar o sprint com evidencias, limitacoes e criterio claro de uso do
  ranking.

Atividades:

1. Fazer smoke test local do dashboard.
2. Validar a rota online se houver deploy automatico pela branch.
3. Documentar resultado observado nesta agenda:
   - view criada;
   - validacao da view;
   - comportamento no Streamlit;
   - limitacoes conhecidas.
4. Atualizar documentacao complementar se houver mudanca de contrato:
   - `docs/dashboard/29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md`;
   - `docs/project/05_DECISOES_TECNICAS.md`, se a metrica final mudar uma
     decisao tecnica relevante.
5. Definir se ajustes finos de UX viram backlog ou continuam dentro do Sprint
   4.
   - melhoria em aberto ja identificada:
     alinhar a lista de videos do criador individual ao mesmo padrao visual de
     `YouTube > Melhores videos 7d`;
   - classificacao:
     melhoria estetica;
   - destino:
     backlog, sem ampliar o escopo obrigatorio do Sprint 4.

Dependencias:

- Etapas 1 a 4 concluidas.

Saida esperada:

- Sprint 4 encerravel com evidencias;
- ranking pronto para uso exploratorio interno;
- proximos refinamentos separados de execucao obrigatoria.

Andamento inicial em 2026-06-21:

- smoke test local iniciado e validado:
  - parse de sintaxe de `dashboard/streamlit_app.py`: `syntax_ok`
  - dependencia local do dashboard instalada na `.venv` a partir de
    `dashboard/requirements.txt`
  - app Streamlit iniciada localmente em `http://127.0.0.1:8502`
  - checagem HTTP local retornou `status 200`
- backlog ja atualizado com melhoria estetica em aberto:
  - alinhar a lista de videos do criador individual ao mesmo padrao visual de
    `YouTube > Melhores videos 7d`

Validacao online:

- URL documentada para o dashboard:
  - `https://vehicle-market-media-analytics.streamlit.app/`
- teste realizado em 2026-06-21 com proxy limpo no ambiente local:
  - resposta HTTP `200`
  - retorno HTML de bootstrap do Streamlit com `content_length = 7902`
- leitura aplicada para fechamento:
  - smoke test local: validado;
  - validacao online: concluida no endpoint publico do app.

Decisao final de pronto:

- Sprint 4 fica encerrado para uso exploratorio interno;
- a view `Hot now 24h` esta aplicada no Supabase e conectada ao Streamlit;
- a tela local respondeu `200` no smoke test;
- a documentacao do sprint, da execucao do dashboard e das decisoes tecnicas
  foi atualizada para o contrato `Hot now 24h`;
- ajustes finos adicionais de UX ficam fora do escopo obrigatorio do sprint e
  devem seguir pelo backlog.

Criterio de pronto:

- SQL, Streamlit e documentacao estao coerentes;
- ranking e interpretavel para estudo de mercado automotivo;
- limitacoes de historico insuficiente estao visiveis;
- nenhuma alteracao operacional de fila foi feita sem decisao separada.

### Ordem recomendada de execucao

1. Fechar contrato analitico.
2. Criar `v_dashboard_hot_now`.
3. Validar top do ranking no Supabase.
4. Ligar a tela `Hot now` no Streamlit.
5. Fazer smoke test e documentar resultado.

### Plano de execucao por atividades

| Ordem | Atividade | Objetivo operacional | Dependencia principal | Saida esperada | Evidencia de pronto |
| --- | --- | --- | --- | --- | --- |
| 1 | Contrato analitico | definir janelas, elegibilidade e metrica | decisoes tecnicas + baseline `v2` | contrato da view | campos e filtros aprovados |
| 2 | View SQL | materializar ranking temporal no banco | contrato fechado | `v_dashboard_hot_now` | SQL versionado e aplicavel |
| 3 | Validacao real | reduzir falso positivo e confirmar semantica | view aplicada | leitura do top `20` | amostras revisadas |
| 4 | Streamlit | entregar pagina real `Hot now` | contrato estavel | ranking no app | placeholder removido |
| 5 | Fechamento | registrar evidencias e limites | tela funcional | sprint encerravel | smoke test e docs atualizados |

### Checklist de acompanhamento

- [x] Etapa 1 concluida
- [x] Etapa 2 concluida
- [x] Etapa 3 concluida
- [x] Etapa 4 concluida
- [x] Etapa 5 concluida

### Riscos e cuidados

- evitar que videos grandes e antigos liderem apenas por volume acumulado;
- evitar falso positivo em videos com poucos snapshots;
- nao reintroduzir o `priority_score_v2` como criterio operacional;
- nao misturar `Hot now` com `Melhores videos 7d`;
- nao carregar historico bruto no Streamlit;
- manter a interpretacao como exploratoria ate a metrica ser observada em uso
  real.

### Status inicial em 2026-06-20

Leitura atual:

- Sprint 3 esta concluido no escopo aprovado;
- roadmap ja prioriza `Hot now` como proxima frente do dashboard;
- plano do dashboard ja aponta `v_dashboard_hot_now` como primeira view nova;
- decisao tecnica existente separa analise temporal da fila operacional;
- Sprint 4 fica preparado para iniciar pela definicao do contrato analitico.

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

- [x] Validar rotina mensal.
- [x] Implementar upload do PDF pela view `Cadastro Fenabrave` com pasta
  obrigatoria por `ano/mes` para suportar historico.
- [x] Expandir a fase 2 por item do PDF com parser, preview, persistencia e
  backfill historico controlado.
- [x] Fechar a revisao formal de cobertura do historico `12/2025` a `06/2026`.
- [x] Saneamento da duplicidade cadastral de `12/2025`.
- [x] Fechar a governanca final:
  - `ingestion_runs`
  - persistencia adicional de validacoes
  - lembrete operacional mensal
- [x] Expor uma RPC canonica `get_fenabrave_monthly_packet(...)` para consumo
  direto por GPT, com packet `jsonb`, top `5` por categoria/canal e bloco de
  eletrificados, sem Hermes no fluxo de analise. Aplicada e validada em leitura
  real no Supabase em `2026-08-12`.
- [ ] Consolidar o fluxo repo-specific Fenabrave GPT em `.agents/skills/`, com
  skill coordenadora mensal, handoff editorial e uso somente leitura da RPC.

Status em 2026-07-15:

- governanca final da Fenabrave fechada como contrato operacional documentado,
  sem nova tabela fisica obrigatoria nesta etapa
- cada mes carregado passa a ser tratado como um `ingestion_run` logico,
  identificado pelo registro canonico em `market_source_files` e detalhado por
  item em `market_fenabrave_extraction_items`
- a rotina mensal deve ser acompanhada pelo calendario offline apos o 5o dia
  util, processando sempre o mes anterior
- uma tabela formal de `ingestion_runs` fica fora do escopo imediato e so deve
  ser retomada se a automacao futura exigir historico independente de execucao,
  retries ou multiplas fontes no mesmo contrato de monitoramento

Atualizacao de 2026-08-12:

- por solicitacao explicita do usuario, a frente Fenabrave ganhou um
  desdobramento direto de consumo analitico para GPT online/mobile
- a RPC ja foi aplicada no projeto `Proj_mktDigital`
- a leitura real de `2026-07-01` confirmou `status = ok` para:
  - `autos`
  - `comerciais_leves`
  - `autos_comerciais_leves`
- a entrega local desta rodada passa a focar:
  - organizacao do fluxo em branch propria
  - reposicionamento das skills para `.agents/skills/`
  - criacao da skill coordenadora `fenabrave-monthly-linkedin`
  - validacao do uso repo-specific sem SQL bruto nem Hermes

Observacao fora do Sprint 5:

- em `2026-07-16`, por solicitacao explicita do usuario, foi executada fora do
  escopo automatico do Sprint 5 a implantacao e validacao inicial do heartbeat
  do `youtube_main_scraper`
- a frente social media confirmou em producao o caso `success` com posts novos
  (`processed = 3`, `errors = 0`, `inserted_or_updated_posts = 150`,
  `cursor 3 -> 6`, `heartbeat_id = 2`) e validou a leitura correspondente no
  Streamlit
- o Sprint ativo permanece `Sprint 5 - Fontes externas`; a evidência acima nao
  reabre Sprint 3 nem muda a prioridade automatica do roadmap

### Atividades Carros na Web

- [ ] Definir rotina de download recorrente dos CSVs existentes do Carros na Web.
- [ ] Persistir os dados de catalogo no Supabase com rastreabilidade de arquivo,
  data de download, hash/versao e status de validacao.
- [ ] Criar view inicial para consumo no Streamlit.
- [x] Colocar scraping de fichas tecnicas em `on_hold`.

Status em 2026-07-15:

- confirmado pelo usuario que os CSVs de catalogo ja existem, mas nao nesta
  maquina
- esses CSVs passam a ser a fonte operacional da frente, devendo ser baixados
  regularmente para detectar novas entradas
- a visao contratual correta passa a ser: CSV recorrente -> persistencia no
  banco -> view analitica -> consumo no Streamlit
- fichas tecnicas por scraping nao sao viaveis nesta etapa e ficam em
  `on_hold`, sem bloquear a ingestao dos CSVs de catalogo
- a decisao pendente deixa de ser "scraping ou schema" e passa a ser o desenho
  da modelagem inicial, rotina de download e contrato da view do Streamlit

### Documentacao relacionada

- [23_FENABRAVE_PHASE1_INGESTION_SPEC.md](../external_data/23_FENABRAVE_PHASE1_INGESTION_SPEC.md)
- [00_OFFLINE_OPERATIONS_CALENDAR.md](../external_data/00_OFFLINE_OPERATIONS_CALENDAR.md)
- [27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md](../external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md)
- [22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md](../external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md)
- [60_FENABRAVE_PACKET_RPC_GPT_ANALYSIS.md](../external_data/60_FENABRAVE_PACKET_RPC_GPT_ANALYSIS.md)

### Entregas

- Fenabrave com rotina mensal clara, historico canonico validado e fase 2 ativa
  consolidada para os itens `1..8` e `11..22`, com governanca mensal fechada.
- Fluxo mensal Fenabrave GPT organizado em skills repo-specific, com GitHub
  como fonte de verdade das skills e Supabase como unica fonte de dados.
- Decisao objetiva sobre Carros na Web: CSVs de catalogo continuam como fonte
  estruturada; scraping de fichas tecnicas fica em `on_hold`.
- Proximas necessidades de modelagem externa registradas.

### Estimativa

`2` a `4` dias.

---

## Sprint 6 - Enrichment e produto analitico

### Objetivo

Iniciar o planejamento operacional da camada de enrichment, validando metodo,
taxonomia e uso controlado de IA antes de qualquer escala para a base completa.

### Status inicial em 2026-07-16

Leitura atual:

- o Sprint 5 continua como sprint ativo formal, mas a frente Carros na Web esta
  bloqueada operacionalmente nesta maquina pela ausencia dos CSVs de catalogo
  no ambiente atual
- por solicitacao explicita do usuario, o Sprint 6 entra em inicio de
  planejamento sem ser tratado ainda como execucao em escala
- os documentos
  `docs/external_data/29_SPEC-INGESTAO-VALIDACAO-NICHOS-SUBNICHOS.md` e
  `docs/external_data/30_SPEC_PREMISSAS_OPENAI_CLASSIFICACAO_TRANSCRICAO.md`
  passam a ser a base obrigatoria deste planejamento

Premissas ja fechadas para o inicio do sprint:

- a classificacao deve comecar por amostra manual de `10` videos, com
  comparacao humano vs IA, antes de qualquer escala
- a primeira classificacao deve usar apenas dados ja existentes do video, sem
  transcricao na chamada inicial
- a camada de IA desta fase usara somente OpenAI
- o maior risco operacional desta frente nao e custo, e sim TPM/RPM em Tier 1
  e competicao com o Hermes
- transcricao deve ser parcial, sob demanda e acionada apenas quando a
  confianca inicial nao for suficiente ou quando o video tiver relevancia
  analitica alta

### Atividades

- [x] Consolidar a taxonomia inicial da fase metodologica, cobrindo no minimo:
  - `niche`
  - `sub_niche`
  - `sub_sub_niche`
  - `content_type`
  - `audience_intent`
- [x] Confirmar as dimensoes automotivas complementares que entram ja na
  validacao inicial:
  - `vehicle_brand`
  - `vehicle_model`
  - `vehicle_year_or_generation`
  - `automotive_system`
  - `component`
  - `problem`
- [x] Selecionar a amostra inicial de `10` videos com mistura de casos claros e
  ambiguos, seguindo a composicao metodologica definida na spec de nichos e
  subnichos.
- [x] Publicar workbook unico em Excel para a rodada humana:
  - aba `taxonomias`
  - aba `execucao_humana`
  - links clicaveis
  - dropdowns editaveis
  - `sub_niche` com preenchimento multiplo no mesmo campo
- [x] Registrar a classificacao humana dos `10` videos em duas entregas
  separadas:
  - `entrega_1_descricao`
  - `entrega_2_90s_iniciais`
- [ ] Adquirir e incluir a descricao dos `10` videos no material de execucao
  antes da primeira entrega.
- [x] Registrar os achados pos-teste sobre hierarquia, coerencia entre campos,
  validacao futura no banco e sobreposicao entre `diagnostico` e `manutencao`.
- [x] Desenhar a taxonomia v2 com arvore legivel e codigos canonicos separados
  da navegacao apresentada ao usuario.
- [x] Definir matrizes de compatibilidade entre rota taxonomica,
  `automotive_system`, `component` e `problem`.
- [x] Definir a validacao referencial de `vehicle_brand`, `vehicle_model` e
  `vehicle_year_or_generation` contra cadastros canonicos futuros.
- [ ] Decidir, usando os resultados do piloto, entre:
  - separar `automotive_domain` e `activity_type`
  - adotar `niche_primary` e `niche_secondary` controlados
- [x] Definir o contrato da classificacao inicial por IA usando somente
  metadados existentes do video.
- [x] Consolidar o resultado humano e o contrato de avaliacao cega pelo agente
  GPT no doc `36`.
- [ ] Corrigir os metadados truncados da amostra e capturar snapshots das
  descricoes antes da avaliacao GPT.
- [x] Capturar ou gerar as transcricoes dos `90s` iniciais dos `10` videos.
- [x] Executar round exploratorio com GPT 5.5 para evolucao taxonomica, usando
  apenas titulo/metadados quando descricao e transcricao nao estiverem
  versionadas.
- [x] Executar classificacao GPT 5.5 exploratoria com os transcripts Whisper
  dos `90s` e comparar com o baseline humano equivalente.
- [ ] Executar as duas etapas GPT sem expor o baseline humano ao classificador.
- [ ] Fechar a formula e os campos obrigatorios do `confidence_score`.
- [x] Documentar a avaliacao de qualidade textual do `transcript_90s` como
  evidencia auxiliar da classificacao.
- [ ] Fechar o calculo e os pesos do `agreement_score` para comparacao humano
  vs IA.
- [ ] Unificar os thresholds operacionais da fase:
  - aprovacao sem transcricao
  - aprovacao provisoria por amostragem
  - envio para transcricao parcial
  - revisao humana
- [x] Definir o contrato operacional OpenAI desta fase:
  - classificacao diagnostica inicial com `gpt-5-nano`
  - transcricao operacional sob demanda com GPT Transcribe
    (`gpt-4o-mini-transcribe`)
  - classificacao operacional combinada com titulo, metadados e transcricao
    dos `90s` usando `gpt-5-nano`
  - sem fallback automatico para `gpt-5.4-mini` nesta etapa
- [ ] Definir as guardas operacionais contra TPM/RPM:
  - `batch_size` pequeno
  - `concurrency = 1` no inicio
  - backoff exponencial em `429`
  - janelas separadas do Hermes
  - limite diario de videos
- [ ] Definir a separacao de papeis entre orquestracao e logica pesada:
  - `n8n` controla lotes, status e roteamento
  - servico Python/API monta prompt, chama OpenAI, valida JSON e calcula
    scores
  - banco persiste status e historico de tentativas
- [ ] Definir o historico minimo obrigatorio por tentativa:
  - `post_id`
  - `attempt_type`
  - `model_name`
  - `prompt_version`
  - `input_token_estimate`
  - `output_token_estimate`
  - `confidence_score`
  - `classification_result`
  - `error_message`
  - `created_at`
- [ ] Traduzir o enrichment em perguntas de produto que orientem o proximo
  modulo analitico:
  - creators emergentes por nicho
  - temas em alta por subnicho
  - videos fora da curva no contexto do proprio creator
  - oportunidades por nicho, marca, modelo ou sistema automotivo
- [ ] Atualizar roadmap, backlog e decisoes tecnicas com o recorte real da fase
  seguinte, separando claramente:
  - validacao metodologica
  - implementacao de pipeline
  - consumo analitico no dashboard

#### Atividade 4 - Workbook unico para execucao humana

Status: concluida em 2026-07-16.

Objetivo:

- consolidar taxonomia, dimensoes complementares e amostra piloto em um unico
  arquivo Excel para facilitar a rodada humana
- reduzir friccao operacional da classificacao manual, mantendo rastreabilidade
  com os artefatos canonicos anteriores

Resultado publicado:

- `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsx`
- `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsm`
- `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.md`
- `scripts/external_data/build_pilot_human_workbook.ps1`

Contrato operacional da v1:

- a aba `taxonomias` consolida os CSVs canonicos dos docs `31` e `32`
- a aba `execucao_humana` traz os `10` videos primarios da amostra do doc `33`
- `video_url` e publicado com link clicavel para o video
- os campos de classificacao usam dropdowns sugeridos sem bloquear valor novo
- `sub_niche` pode receber mais de um valor no mesmo campo usando separacao por
  `, `
- o arquivo `.xlsx` e a versao recomendada para execucao humana nesta v1

Contrato das entregas humanas:

- Entrega 1: classificar pela descricao, sem assistir ao video
- Entrega 2: classificar novamente pelos `90s` iniciais do video
- para videos menores que `90s`, usar o conteudo completo na Entrega 2
- preservar os dois arquivos sem sobrescrita para comparacao posterior
- a descricao dos videos deve ser incluida no material antes da Entrega 1

Validacao corretiva em 2026-07-16:

- corrigida a serializacao que distribuia cada registro de taxonomia letra por
  letra
- confirmadas `102` linhas de taxonomia, `10` videos, `10` hyperlinks e `12`
  dropdowns no Excel desktop
- o gerador passou a interromper a publicacao se essas contagens nao forem
  atendidas

#### Achados pos-teste da taxonomia v1

Status: registrados em 2026-07-20.

Documento:

- `docs/external_data/35_ACHADOS_POS_TESTE_TAXONOMIA_CLASSIFICACAO_V1.md`

Leitura:

- a taxonomia precisa de uma arvore de apresentacao mais clara, como
  `diagnostico > scanner_obd2` e `diagnostico > luz_injecao`
- a arvore visual nao deve misturar tecnicamente subnicho, problema, sistema e
  componente na mesma dimensao canonica
- combinacoes entre tema, sistema, componente e problema precisam ser
  validadas por matrizes de compatibilidade
- marca, modelo e geracao precisam ser reconciliados com cadastros canonicos
  do banco antes da persistencia futura
- a possibilidade de mais de um niche permanece em decisao; a alternativa
  preferida para teste e separar dominio automotivo de tipo de atividade
- a taxonomia v1 nao sera reescrita retroativamente e permanece como evidencia
  da primeira rodada

#### Resultado do baseline humano em duas etapas

Status: consolidado em 2026-07-20.

Artefatos:

- `docs/external_data/36_RESULTADO_BASELINE_HUMANO_E_CONTRATO_AVALIACAO_GPT_V1.md`
- `docs/external_data/36_BASELINE_HUMANO_DUAS_ETAPAS_V1.csv`

Resultado:

- `2/10` videos ficaram finalizados apenas pela descricao
- `9/10` ficaram finalizados depois dos `90s` iniciais
- `7/10` mudaram em pelo menos um campo de classificacao
- foram observadas `29` mudancas de campo
- `8/10` resultados apos `90s` apresentam termo fora da v1 ou incompatibilidade
  de parent, confirmando a necessidade das travas registradas no doc `35`
- a proxima rodada sera executada pelo GPT em duas etapas cegas equivalentes,
  sem acesso previo ao baseline humano

#### Round exploratorio GPT 5.5 para taxonomia

Status: registrado em 2026-07-20.

Artefatos:

- `docs/external_data/37_ANALISE_GPT55_EXPLORATORIA_TAXONOMIA_R1.md`
- `docs/external_data/37_RESULTADO_GPT55_EXPLORATORIO_TAXONOMIA_R1.csv`

Resultado:

- `10/10` videos da amostra canonica foram avaliados na etapa
  `gpt55_entrega_1_descricao`
- a evidencia disponivel ficou limitada a titulo e metadados, porque as
  descricoes reais ainda nao estao versionadas no doc `33`
- `10/10` registros da etapa `gpt55_entrega_2_90s_iniciais` foram preservados,
  mas marcados como `sem_evidencia_90s`, pois nao ha transcricao textual
  versionada dos primeiros `90s`
- a rodada nao e benchmark final da API `gpt-5.4-mini`; ela serve para evoluir
  a taxonomia e orientar os proximos rounds de fine tuning conceitual

#### Transcricao local dos 90s com Whisper

Status: concluida em 2026-07-20.

Artefatos:

- `scripts/external_data/transcribe_pilot_90s_whisper.py`
- `docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.md`
- `docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.csv`

Contrato:

- executar localmente, sem `OPENAI_API_KEY`
- usar `yt-dlp` para audio do YouTube e `faster-whisper` local para speech-to-text
- transcrever ate `90s` por video, ou a duracao completa quando o video for
  menor que `90s`
- nao versionar audio, video, cache de modelo ou arquivos temporarios
- preservar uma linha por `post_id`, inclusive quando houver falha

Resultado:

- `10/10` videos transcritos com `success`
- `0` falhas
- `pINW53ErjQI` foi transcrito por `86s`, por ser menor que `90s`
- `_j1gOOnjgcU` foi transcrito por `73s`, por ser menor que `90s`
- os demais `8` videos foram limitados a `90s`

#### Comparacao humano vs GPT 5.5 com transcripts de 90s

Status: concluida em 2026-07-21.

Artefatos:

- `docs/external_data/39_RESULTADO_GPT55_90S_WHISPER_R1.csv`
- `docs/external_data/39_COMPARACAO_HUMANO_GPT55_90S_R1.md`

Resultado:

- `10/10` videos classificados pelo GPT 5.5 exploratorio usando transcripts
  Whisper dos `90s`
- comparacao feita contra `entrega_2_90s_iniciais` do baseline humano
- maior concordancia em entidades explicitas:
  - `vehicle_brand`: `10/10`
  - `vehicle_model`: `9/10`
  - `audience_intent`: `8/10`
- maiores divergencias em:
  - `sub_niche`: `4/10`
  - `automotive_system`: `4/10`
  - `vehicle_year_or_generation`: `5/10`
- leitura principal: as divergencias restantes indicam limitacao estrutural da
  taxonomia v1, especialmente em videos que cruzam `review`, `mercado`,
  `powertrain`, diagnostico, manutencao e custo

#### Taxonomia V2 e guia de classificacao

Status: documentada em 2026-07-21.

Artefato:

- `docs/external_data/40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md`

Decisao metodologica:

- a V2 deixa de depender de um unico `niche`
- a classificacao passa a separar:
  - `automotive_domain`
  - `activity_type`
  - `topic_path`
  - `content_type`
  - `audience_intent`
  - entidades do veiculo
  - contexto tecnico
- `topic_path` e a arvore legivel para navegacao humana
- banco, workbook, CSVs v1 e pipeline ainda nao sao alterados por esta entrega

Resultado:

- a arvore V2 cobre os `10` videos do piloto
- `fora_escopo` passa a existir como rota controlada
- `eletrico`, `hibrido`, `flex` e `diesel` ficam sob `powertrain`
- `motor` e `cambio` ficam preservados como contexto tecnico ou rotas
  contextualizadas, nao como rotulos soltos

#### Round GPT 5.5 usando Taxonomia V2

Status: concluido em 2026-07-21.

Artefatos:

- `docs/external_data/41_RESULTADO_GPT55_TAXONOMIA_V2_R1.csv`
- `docs/external_data/41_COMPARACAO_GPT55_V1_V2_R1.md`

Resultado:

- `10/10` videos foram classificados na etapa
  `gpt55_v2_entrega_1_descricao`, usando titulo e metadados porque a descricao
  real ainda nao esta versionada
- `10/10` videos foram classificados na etapa
  `gpt55_v2_entrega_2_90s_iniciais`, usando os transcripts Whisper locais
  dos primeiros `90s`
- a V2 reduziu a disputa estrutural entre `review`, `mercado` e `powertrain`
  ao separar `automotive_domain`, `activity_type`, `topic_path`,
  `content_type` e contexto tecnico
- a V2 tambem tornou `fora_escopo` uma rota operacional explicita para casos
  como `pINW53ErjQI`
- a proxima necessidade metodologica passa a ser criar CSV canonico da arvore
  V2 e matriz de compatibilidade entre `topic_path`, `automotive_system`,
  `component` e `problem`

#### CSVs operacionais da Taxonomia V2

Status: concluido em 2026-07-21.

Artefatos:

- `docs/external_data/42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv`
- `docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`

Resultado:

- a arvore `topic_path` da V2 foi transformada em CSV operacional com dominio,
  atividade default, hierarquia, sinal de uso no piloto e suporte opcional a
  `topic_path_secondary`
- a matriz inicial de compatibilidade tecnica cobre `motor`, `transmissao`,
  `arrefecimento`, `eletrica_eletronica` e `powertrain`
- `fora_escopo` passou a ter regra operacional para impedir preenchimento de
  sistema, componente ou problema quando os termos tecnicos forem incidentais
- `motor` e `cambio` permanecem proibidos como tema solto, aparecendo apenas
  como contexto tecnico ou rotas contextualizadas
- banco, workbook e pipeline permanecem inalterados nesta entrega

#### Enriquecimento da Taxonomia V2 por titulos

Status: documentado em 2026-07-22.

Artefato:

- `docs/external_data/44_ENRIQUECIMENTO_TAXONOMIA_V2_TITULOS_E_PROXIMA_TRANSCRICAO.md`

Resultado:

- busca exploratoria no Supabase usou `title`, porque `public.posts` ainda nao
  possui coluna `description`
- foram lidos `5179` posts e identificados `1462` candidatos apos filtros de
  qualidade e termos de taxonomia
- foram selecionados `10` videos para enriquecer a V2 por titulo, cobrindo
  sinais de `diagnostico`, `manutencao`, `review`, `mercado`, `powertrain`,
  `pos_venda` e `off_road`
- a curadoria removeu `motorhome`, `4x4` e `carros_descartaveis` da lista de
  candidatos canonicos nesta rodada
- a proxima etapa deve repetir a extracao usando transcricao dos `90s`, com
  separacao entre termos brutos, candidatos canonicos e termos rejeitados

#### Transcricao 90s para enriquecimento da Taxonomia V2

Status: concluida em 2026-07-23.

Artefatos:

- `docs/external_data/45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.csv`
- `docs/external_data/45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md`

Resultado:

- os `10` videos selecionados no doc `44` foram transcritos localmente com
  `yt-dlp+faster-whisper-local`
- `10/10` videos terminaram com `transcription_status = success`
- videos menores que `90s` foram transcritos na duracao completa
- o video `6qSnrkGd70I` exigiu retry pontual apos falha inicial de `ffmpeg`
- a proxima etapa e extrair termos dos transcripts e comparar contra a
  extracao feita apenas por titulo

#### Analise dos transcripts e enriquecimento da Taxonomia V2

Status: concluida em 2026-07-23.

Artefato:

- `docs/external_data/46_ANALISE_TRANSCRICOES_ENRIQUECIMENTO_TAXONOMIA_V2_R1.md`

Resultado:

- os CSVs `42` e `43` foram atualizados com aprendizados dos transcripts do
  doc `45`
- `ruido` passou a ser o codigo canonico para sintoma sonoro
- `barulho` ficou como sinonimo e sinal textual em `example_signals`
- `off_road__4x4` foi removido como `topic_path_code`; `4x4` permanece apenas
  como sinal textual
- `motorhome`, `carros_descartaveis` e `efeito_dolphin` permanecem fora da
  taxonomia canonica
- foram adicionadas compatibilidades iniciais para suspensao, freios,
  transmissao/CVT, motor, arrefecimento, pneus e powertrain hibrido plug-in
- banco, workbook e pipeline permanecem inalterados

#### Enriquecimento da Taxonomia V2 por fonte Moura

Status: concluido em 2026-07-23.

Artefato:

- `docs/external_data/47_ANALISE_FONTE_MOURA_MANUTENCAO_PREVENTIVA_TAXONOMIA_V2.md`

Fonte avaliada:

- `https://www.moura.com.br/blog/checklist-de-manutencao-preventiva-carro`

Resultado:

- a Taxonomia V2 foi enriquecida com a rota de checklist periodico
  `manutencao_reparo__manutencao_preventiva__revisao_10k`
- foram adicionadas rotas preventivas para `oleo_filtros`, `filtro_ar`,
  `filtro_combustivel`, `alinhamento_balanceamento`, `correias_tensores` e
  `controle_revisao`
- foram adicionadas rotas de diagnostico por sintomas gerais:
  `luzes_painel`, `perda_potencia`, `vibracao` e `direcao_puxando`
- a matriz tecnica passou a cobrir `combustivel_injecao` e
  `rodagem_direcao`, alem de reforcar componentes de motor, freios,
  suspensao, arrefecimento e eletrica/eletronica
- `barulho` permanece apenas como sinonimo/sinal textual; `ruido` continua
  sendo o codigo canonico para sintoma sonoro
- banco, workbook e pipeline permanecem inalterados

#### Reclassificacao dos 20 videos com Taxonomia V2 enriquecida

Status: concluida em 2026-07-23.

Artefatos:

- `docs/external_data/48_RESULTADO_GPT55_TAXONOMIA_V2_ENRIQUECIDA_20VIDEOS_R1.csv`
- `docs/external_data/49_COMPARACAO_TAXONOMIA_V2_ENRIQUECIDA_20VIDEOS_R1.md`

Resultado:

- as transcricoes salvas dos docs `38` e `45` foram reutilizadas como
  evidencia dos `90s`
- foram classificadas `20` linhas:
  - `10` do piloto original
  - `10` da rodada de enriquecimento
- ha `16` videos unicos, porque `4` videos aparecem nos dois lotes
- contra a rodada anterior do piloto, `automotive_domain`, `activity_type` e
  `topic_path` ficaram estaveis em `10/10`
- as principais mudancas ocorreram em `component`, `problem`,
  `content_type`, `topic_path_secondary` e `needs_human_review`
- a rodada confirmou o gargalo de modelar `technical_context` como estrutura
  repetivel para videos com multiplos sistemas e componentes
- banco, workbook e pipeline permanecem inalterados

#### Technical context repetivel para Taxonomia V2

Status: concluido em 2026-07-23.

Artefatos:

- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.md`
- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.csv`

Resultado:

- `technical_context[]` foi definido como estrutura repetivel canonica para
  representar multiplos sistemas, componentes, problemas e evidencias
- o formato operacional desta fase e um CSV filho em formato longo, com uma
  linha por contexto tecnico coerente
- os campos agregados `automotive_system`, `component` e `problem` continuam
  como resumo legado/compatibilidade em resultados consolidados
- videos como `_j1gOOnjgcU`, `ITBdyKnV5Pg` e `6qSnrkGd70I` passaram a ter
  multiplas linhas de contexto tecnico em vez de valores concatenados por `;`
- casos `fora_escopo` e analises setoriais permanecem sem contexto tecnico
  principal
- banco, workbook e pipeline permanecem inalterados

Complemento metodologico registrado em 2026-07-23:

- `topic_path` deve permanecer como arvore curta, estavel e navegavel
- termos tecnicos novos nao devem virar subnichos automaticamente
- a profundidade incremental de pecas, sintomas, procedimentos e insumos deve
  ficar em `technical_context[]`, vocabulario tecnico controlado,
  `taxonomy_gaps` ou sinonimos
- a promocao de um termo para `topic_path` exige evidencia de que ele
  representa um tipo recorrente de conteudo e melhora a navegacao humana
- `context_order` nao representa peso de importancia; serve apenas para ordem
  de aparicao ou organizacao operacional

#### Catalogo Carros na Web para entidades de veiculo

Status: concluido e validado no Supabase em 2026-07-23.

Artefatos:

- `docs/external_data/51_CARROSNAWEB_CATALOGO_SUPABASE_HOMOGENEIZACAO_VEICULOS.md`
- `sql/ddl/tables/021_create_market_carrosnaweb_catalog.sql`
- `sql/ddl/views/022_create_v_carrosnaweb_vehicle_catalog.sql`
- `sql/ddl/tests/010_test_carrosnaweb_catalog.sql`
- `scripts/carrosnaweb_ingestion/ingest_carrosnaweb_catalog.py`

Resultado:

- os CSVs historicos de `fabricantes`, `modelos` e `anos_modelo` do Carros na
  Web foram adotados como base inicial de catalogo para Supabase
- `aplicacoes_modelo_ano_test.csv` ficou fora da carga por pertencer a ficha
  tecnica
- a modelagem passa a suportar homogeneizacao futura de marca, modelo e ano
  extraidos da descricao e da transcricao
- o catalogo nao altera `topic_path`, `technical_context[]`, banco do pipeline
  de classificacao ou workbook humano
- o `dry-run` validou `127` fabricantes, `1458` modelos e `8914` anos/modelo
- a carga `--write` gravou `127` fabricantes, `1458` modelos e `8914`
  anos/modelo no Supabase
- a view `v_carrosnaweb_vehicle_catalog` foi validada com buscas por `BYD
  Dolphin`, `Renault Kwid`, `Changan Uni-T` e `Hyundai HB20`

#### Amostra aleatoria de validacao da Taxonomia V2

Status: concluido em 2026-07-23.

Artefatos:

- `docs/external_data/55_AMOSTRA_ALEATORIA_TAXONOMIA_V2_10_VIDEOS_R1.csv`
- `docs/external_data/56_TRANSCRICOES_90S_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv`
- `docs/external_data/57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.md`
- `docs/external_data/57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv`

Resultado:

- foram sorteados `10` videos elegiveis, sem intersecao com rodadas anteriores
- todas as transcricoes dos primeiros `90s` foram concluidas com sucesso
- a confianca media subiu de `0.843` por titulo/metadados para `0.921` com
  transcricao
- a revisao humana decidiu nao expandir `topic_path` nesta rodada
- motos e duas rodas permanecem fora de escopo
- nao serao criados `audience_context`, `estagio_produto` ou
  `engineering_context` nesta fase
- foram aceitos apenas novos termos tecnicos controlados para review:
  `cambio_automatico`, `cambio_cvt`, `tracao_traseira`, `tracao_dianteira` e
  `tracao_integral`

#### Harness GPT e contrato Supabase para Taxonomia V2

Status: documentado e modelado em 2026-07-23.

Artefatos:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_OUTPUT_SCHEMA_V2.json`
- `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
- `sql/ddl/views/023_create_v_video_classification_latest.sql`
- `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

Resultado:

- foi criado o contrato de banco para armazenar a Taxonomia V2 no Supabase
  como referencia operacional
- foram modeladas tabelas para rodadas de classificacao, resultado principal,
  `technical_context[]` repetivel e entidades de veiculo
- o harness foi definido como contrato de entrada/saida, nao como metodo de
  ingestao ou script local
- a skill do classificador passa a ser o prompt/contrato enviado na chamada
  da API GPT e versionado pelo campo `prompt_contract_version`
- a saida aceitavel do GPT deve validar contra schema JSON e ser imputavel
  diretamente nas tabelas de classificacao
- a definicao operacional de modelo fica:
  - `gpt-5-nano` para classificacao diagnostica por titulo/metadados
  - `gpt-4o-mini-transcribe` para transcricao operacional dos `90s`
  - `gpt-5-nano` para classificacao operacional combinada por titulo,
    metadados e transcricao
  - sem fallback automatico para `gpt-5.4-mini`
- a qualidade do `gpt-5-nano` sera avaliada depois da implementacao em rodada
  propria
- a execucao futura fica reservada para rotina Google Cloud separada
- dashboard, workbook, coleta e pipeline permanecem fora desta entrega

#### Ambiente de execucao VPS para classificador GPT

Status: documentado em 2026-07-23.

Artefato:

- `docs/external_data/59_VPS_CRON_CLASSIFICADOR_GPT_V2_RUNBOOK.md`
- `scripts/video_classification/classify_videos_gpt_v2.py`
- `scripts/video_classification/README.md`
- `sql/dml/seed_video_taxonomy_v2.sql`

Resultado:

- foi definido que a primeira execucao agendada do classificador sera em VPS
  Hostinger via `cron`
- o acesso de desenvolvimento sera feito por VS Code Remote SSH
- o servidor observado usa Ubuntu 24.04 LTS
- o diretorio base definido no servidor e `/opt/social-media-analytics`
- nesta fase, nao sera clonado o repositorio completo na VPS
- o deploy sera minimo: subir apenas script e arquivos auxiliares necessarios
- credenciais, `.env`, chaves SSH, IP publico e usuario real ficam fora do Git
- a decisao sobre Google Cloud, Docker ou CI/CD fica adiada ate a rotina ser
  validada em lote pequeno
- o script inicial foi implementado para execucao manual:
  - `--stage title_metadata`
  - `--stage transcript_90s` com CSV de transcricoes ja existente
  - `--dry-run` e `--write`
  - validacao local de JSON/schema e regras semanticas antes da gravacao
- foi criado seed estatico para carregar a Taxonomia V2 no Supabase:
  - `104` topic paths
  - `91` regras de compatibilidade tecnica
  - `59` termos controlados
- cron continua desativado ate validacao manual na VPS

#### Decisao de chamada operacional combinada

Status: documentada em 2026-07-24.

Resultado:

- o estagio `transcript_90s` passa a ser a classificacao operacional principal
  quando houver transcricao salva
- a transcricao operacional deve ser gerada por GPT Transcribe, nao por
  Whisper/local
- cada chamada operacional deve combinar titulo, metadados confiaveis, descricao
  quando existir e transcricao dos primeiros `90s`
- `title_metadata` permanece disponivel para diagnostico, calibracao, triagem
  ou comparacao metodologica, mas nao como resultado final quando a transcricao
  ja existir
- a decisao evita duplicar prompt, taxonomia, matriz tecnica e JSON de saida em
  duas chamadas completas
- banco, schema, workbook e pipeline permanecem inalterados

#### Qualidade textual da transcricao

Status: documentada em 2026-07-24.

Resultado:

- o classificador deve avaliar se o transcript recebido e suficiente para
  sustentar a classificacao automotiva
- a avaliacao mede a qualidade textual da evidencia, nao a qualidade do audio
  original
- transcripts vazios, truncados, incoerentes ou com nomes proprios degradados
  devem reduzir confianca e podem acionar revisao humana ou retranscricao
- evidencias curtas permanecem nos campos `evidence_summary`,
  `technical_contexts[].evidence_text` e `vehicle_entities[].evidence_text`
- o transcript completo nao sera salvo no Supabase por padrao nesta etapa
- uma futura revisao do schema podera incluir `transcript_quality`, mas banco e
  script permanecem inalterados nesta decisao

### Criterio de saida do planejamento

O inicio do planejamento do Sprint 6 so deve ser considerado concluido quando
existirem, no minimo:

- taxonomia inicial validada para a fase de teste
- amostra de `10` videos definida
- contrato de classificacao humana vs IA documentado
- thresholds de `confidence_score` e `agreement_score` consolidados
- contrato OpenAI e guardas de TPM/RPM documentados
- desenho claro do que fica para validacao metodologica, implementacao e
  consumo no dashboard

### Proxima execucao esperada

Depois deste planejamento inicial, a primeira execucao do Sprint 6 deve seguir
esta ordem:

1. selecionar os `10` videos
2. adquirir e incluir a descricao dos `10` videos
3. produzir a classificacao humana `entrega_1_descricao`
4. produzir a classificacao humana `entrega_2_90s_iniciais`
5. classificar os mesmos `10` videos por IA sem transcricao
6. calcular `confidence_score` e `agreement_score`
7. comparar humano por descricao, humano por `90s` e IA
8. revisar divergencias
9. decidir se a fase avanca para nova rodada, para transcricao parcial ou para
   ajuste de taxonomia/prompt

### Documentacao relacionada

- [01_BACKLOG.md](01_BACKLOG.md)
- [02_ROADMAP.md](02_ROADMAP.md)
- [05_DECISOES_TECNICAS.md](05_DECISOES_TECNICAS.md)
- [29_SPEC-INGESTAO-VALIDACAO-NICHOS-SUBNICHOS.md](../external_data/29_SPEC-INGESTAO-VALIDACAO-NICHOS-SUBNICHOS.md)
- [30_SPEC_PREMISSAS_OPENAI_CLASSIFICACAO_TRANSCRICAO.md](../external_data/30_SPEC_PREMISSAS_OPENAI_CLASSIFICACAO_TRANSCRICAO.md)

### Entregas

- Sprint 6 com inicio de planejamento formalizado e alinhado aos docs `29` e
  `30`.
- Plano metodologico inicial de enrichment orientado por amostra de `10`
  videos.
- Contrato operacional preliminar de OpenAI, transcricao parcial e protecao de
  TPM/RPM.
- Separacao clara entre validacao metodologica, execucao futura de pipeline e
  consumo analitico.

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
