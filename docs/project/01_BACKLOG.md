# BACKLOG GERAL

## Pipeline

- [ ] Melhorar controle de fim de lista no scraper
- [ ] Validar duplicidade de coleta
- [ ] Retry automatico para falhas API
- [ ] Adicionar coleta historica de followers de creators do YouTube via `channels.list(part=statistics)`, gravando snapshots em `creator_metrics_history` e atualizando `creators.followers` como valor corrente. Avaliar implementacao no `youtube_main_scraper`, que ja percorre creators e chama `channels.list` para buscar a playlist de uploads.

## Dados / Qualidade

- [ ] Validar se todos posts possuem historico
- [ ] Checar consistencia de collected_at
- [ ] Identificar creators sem coleta recente
- [ ] Monitorar backlog de guardrail separando posts novos, recentes, warm e antigos para garantir que posts novos nao fiquem bloqueados por divida historica.
- [ ] Padronizar exclusao de posts confirmados como dead/unavailable das metricas e views analiticas, pois posts ja confirmados pelo usuario ainda aparecem fora da fila ativa.

## Analytics

- [ ] Criar view temporal `v_dashboard_hot_posts_now` baseada em velocidade recente e aceleracao do score, sem depender do score hibrido `v2` como regra operacional.
- [ ] Query de crescimento por intervalo
- [ ] Ranking de creators emergentes
- [ ] Identificacao de outliers

## Operacional / Monitoramento

- [ ] Monitorar semanalmente videos indisponiveis em `v_dashboard_unavailable_video_review` e confirmar manualmente candidatos quando necessario.
- [ ] Auditar os `9` posts residuais do cleanup temporario do guardrail antes de retomar o scheduler; `4` deles ja constam como possiveis dead posts.
- [ ] Monitorar o cleanup temporario do guardrail ate `warm_8_30d` e `old_30d_plus` chegarem a `3` checagens, e `new_0_3d` e `recent_4_7d` chegarem a `2`.
- [ ] Prioridade alta: revisar a regra de geracao de `next_check` com base nos sinais operacionais do worker horario. Sinais observados: `Ate 1h = 48`, `Ate 6h = 199`, `Ate 24h = 430`.

## Visualizacao / Estudos de mercado

- [ ] App Streamlit online consumindo Supabase sob demanda
- [ ] Tela inicial com status de qualidade dos dados
- [ ] Ranking de creators por views, engajamento e frequencia
- [ ] Ranking semanal de crescimento de videos
- [ ] Filtros por plataforma, creator, nicho e subnicho
- [ ] Exportacao CSV dos rankings principais

## IA / Classificacao

- [ ] Classificar videos por tipo
- [ ] Melhorar subnicho automatico

## Itens tratados / arquivados

- [x] Tratar videos indisponiveis na YouTube API para evitar posts presos na fila. Implementado com `post_collection_failures`, RPC `register_post_collection_result(...)`, view `v_dashboard_unavailable_video_review`, exclusao de `status = unavailable` da fila ativa e processo de confirmacao manual documentado em `docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`.
- [x] Criar limpeza temporaria do backlog de guardrail. Implementado no script `scripts/offline_backfill/legacy_low_backfill_phase1.py`, documentado em `docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md` e em execucao controlada via scheduler `guardrail-cleanup-backfill`.
- [x] Manter `priority_score_v2` em modo analitico/segundo plano. Decisao registrada em `docs/project/05_DECISOES_TECNICAS.md`; o `v2` nao deve ser promovido para a fila ativa enquanto o foco for analise temporal de videos quentes no momento.
