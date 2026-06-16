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
Sprint ativo: Sprint 1 - Confiabilidade da coleta social media
Datas: a definir conforme disponibilidade do usuario
```

Enquanto o Sprint 1 estiver ativo, apenas tarefas relacionadas a confiabilidade
da coleta social media devem ser executadas automaticamente. Implementacoes,
alteracoes de pipeline, SQL ou dashboard fora deste escopo devem aguardar
confirmacao.

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
- Detectar gaps de coleta por post.
- Confirmar creators sem posts ou posts sem creator.
- Checar se videos `unavailable` estao isolados corretamente.

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

- Analisar `v_dashboard_queue_bottleneck_status`.
- Validar atraso por banda, idade do video e numero de checagens.
- Confirmar impacto da migration nova de `next_check`.
- Verificar se lote `50` com guardrail `6` esta suficiente.
- Decidir se a regra de frequencia deve ser mantida ou ajustada.

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

### Atividades

- Fechar pagina `Overview`.
- Fechar pagina `Creators`.
- Fechar leitura de crescimento semanal.
- Garantir Data Quality antes dos rankings.
- Validar views principais com Supabase.
- Ajustar textos executivos, estados vazios e mensagens de erro.

### Documentacao relacionada

- [29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md](../dashboard/29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md)
- [16_ONLINE_DASHBOARD_SUPABASE_SPEC.md](../dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md)
- [33_CREATOR_VIEW_STREAMLIT_SPEC.md](../dashboard/33_CREATOR_VIEW_STREAMLIT_SPEC.md)
- [34_CREATOR_WEEKLY_TIMESERIES_CONTRACT.md](../dashboard/34_CREATOR_WEEKLY_TIMESERIES_CONTRACT.md)

### Entregas

- Dashboard interno navegavel com dados reais.
- Leitura basica de qualidade, creators e crescimento.
- Confirmacao de que rankings aparecem depois dos sinais de confiabilidade.

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
