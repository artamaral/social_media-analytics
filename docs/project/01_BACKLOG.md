# BACKLOG GERAL

Itens abertos usam a tag curta no inicio do item, no formato `- [ ] [tag] texto`.
Itens ja concluidos ficam consolidados no historico ao fim do arquivo.

## Pipeline

- Os itens de `Pipeline` abaixo tratam do fluxo de descoberta, coleta e
  atualizacao de metricas da base social media.
- [ ] [bug] Melhorar controle de fim de lista no scraper. Garantir que a rotina de
  discovery pare no momento certo quando a API ou a pagina final indicar
  encerramento de lista, evitando truncar creators, repetir paginas ou perder
  novos posts na ultima iteracao.
- [ ] [bug] Validar duplicidade de coleta. Detectar e bloquear a gravacao repetida do
  mesmo post quando o scraper ou o worker reencontra o item em janelas
  sobrepostas, retries ou reprocessamentos manuais.
- [ ] [melhoria] Retry automatico para falhas API. Reexecutar falhas temporarias com
  backoff e limite de tentativas, sem esconder erro persistente, para reduzir
  lacunas de coleta e dependencia de operacao manual.

## Dados / Qualidade

- [ ] [ops] Identificar creators sem coleta recente
- [ ] [ops] Monitorar backlog de guardrail separando posts novos, recentes, warm e antigos para garantir que posts novos nao fiquem bloqueados por divida historica.
- [ ] [bug] Padronizar exclusao de posts confirmados como dead/unavailable das metricas e views analiticas, pois posts ja confirmados pelo usuario ainda aparecem fora da fila ativa.

## Analytics

- [ ] [feat] Query de crescimento por intervalo
- [ ] [feat] Ranking de creators emergentes
- [ ] [analise] Identificacao de outliers

## Operacional / Monitoramento

- [ ] [ops] Monitorar semanalmente videos indisponiveis em `v_dashboard_unavailable_video_review` e confirmar manualmente candidatos quando necessario.
- [ ] [feat] Implementar heartbeat operacional do `youtube_main_scraper` para comprovar execucoes sem posts novos e separar "rodou sem novidades" de "nao rodou".
- [ ] [ops] Auditar os `9` posts residuais do cleanup temporario do guardrail antes de retomar o scheduler; `4` deles ja constam como possiveis dead posts.
- [ ] [ops] Monitorar o cleanup temporario do guardrail ate `warm_8_30d` e `old_30d_plus` chegarem a `3` checagens, e `new_0_3d` e `recent_4_7d` chegarem a `2`.
- [ ] [ops] Revisar periodicamente a regra de `next_check` e a capacidade diaria da fila, porque o volume total de checagens tende a crescer junto com a base de posts; a melhora atual reduz represamento, mas nao elimina a necessidade de reavaliar frequencias, batch e distribuicao conforme a base aumenta.

## Visualizacao / Estudos de mercado

- [ ] [analise] ATIVIDADE ATUAL E PRIORITARIA: definir o proximo bloco da fase 2 Fenabrave apos a conclusao dos itens 6, 7 e 8, priorizando a decisao entre avancar para os itens 9 e 10 de modelos eletrificados ou reorganizar o escopo ativo da fase 2 antes da proxima implementacao.
- [ ] [feat] Ranking de creators por views, engajamento e frequencia
- [ ] [melhoria] Melhoria estetica: alinhar a lista de videos do criador individual ao mesmo padrao visual de `YouTube > Melhores videos 7d`, com hierarquia, colunas e leitura comparavel entre as duas telas.
- [ ] [analise] Rechecar a regra fina de desempate do ranking `YouTube > Melhores videos 7d` apos avaliacao visual da tela em uso real, antes de consolidar a ordenacao como contrato definitivo.
- [ ] [feat] Incluir thumbnail real e link clicavel no titulo e na thumbnail de `YouTube > Melhores videos 7d`, com fallback seguro para ausencia de imagem ou URL.
- [ ] [feat] Filtros por plataforma, creator, nicho e subnicho
- [ ] [feat] Exportacao CSV dos rankings principais

## IA / Classificacao

- [ ] Classificar videos por tipo
- [ ] Melhorar subnicho automatico
- [ ] Proxima etapa de IA: montar a validacao metodologica de nicho/subnicho com amostra inicial de `10` videos, classificacao humana, classificacao por IA sem transcricao, calculo de `agreement_score` e revisao da taxonomia antes de escalar para lotes maiores, conforme `docs/external_data/29_SPEC-INGESTAO-VALIDACAO-NICHOS-SUBNICHOS.md`.
- [ ] Proxima etapa operacional de IA: desenhar a implementacao com OpenAI para classificacao inicial, transcricao parcial e reclassificacao, incluindo thresholds, controle de `TPM/RPM`, batch pequeno, concorrencia baixa, backoff, historico de tentativas e separacao operacional do Hermes, conforme `docs/external_data/30_SPEC_PREMISSAS_OPENAI_CLASSIFICACAO_TRANSCRICAO.md`.

## Historico

- [x] Validar se todos posts possuem historico. Fechado com a auditoria da Sprint 1: posts ativos sem snapshot = `0`; os casos restantes eram `unavailable` confirmados.
- [x] Checar consistencia de collected_at. Fechado com a auditoria da Sprint 1: nao houve evidencia de `collected_at` nulo ou defasado em posts ativos.
- [x] Criar view temporal `v_dashboard_hot_posts_now` baseada em velocidade recente e aceleracao do score, sem depender do score hibrido `v2` como regra operacional. Entregue como `v_dashboard_hot_now` e refinada para o contrato `Hot now 24h`.
- [x] App Streamlit online consumindo Supabase sob demanda. Entregue com Streamlit Community Cloud consumindo Supabase sob demanda.
- [x] Tela inicial com status de qualidade dos dados. Entregue na superficie `Data quality` do dashboard.
- [x] Evoluir a view Fenabrave consumida pelo Streamlit para exibir o historico anual completo por periodo, garantindo leitura de 2025 e 2026, com cards mostrando o acumulado do ano por categoria e nao a soma de todos os arquivos carregados. O contrato da dashboard ja define acumulado reiniciado por ano calendario e os cards nao devem somar todos os arquivos.
- [x] Ranking semanal de crescimento de videos. Entregue como `v_dashboard_post_growth_7d` e consumido no dashboard.
- [x] Finalizar o item 5 da fase 2 Fenabrave, `Emplacamentos por sub segmento` da pagina 17, com parser, preview, validacoes, persistencia mensal automatica e backfill historico validado no Supabase para `12/2025` a `06/2026`, considerando automoveis, os percentuais publicados de mes corrente, acumulado do ano corrente (`n`) e acumulado do ano anterior (`n-1`), sem carregar a coluna de mes anterior.
- [x] Tratar videos indisponiveis na YouTube API para evitar posts presos na fila. Implementado com `post_collection_failures`, RPC `register_post_collection_result(...)`, view `v_dashboard_unavailable_video_review`, exclusao de `status = unavailable` da fila ativa e processo de confirmacao manual documentado em `docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`.
- [x] Criar limpeza temporaria do backlog de guardrail. Implementado no script `scripts/offline_backfill/legacy_low_backfill_phase1.py`, documentado em `docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md` e em execucao controlada via scheduler `guardrail-cleanup-backfill`.
- [x] Manter `priority_score_v2` em modo analitico/segundo plano. Decisao registrada em `docs/project/05_DECISOES_TECNICAS.md`; o `v2` nao deve ser promovido para a fila ativa enquanto o foco for analise temporal de videos quentes no momento.
- [x] Finalizar o item 1 da fase 2 Fenabrave, `Ranking dos emplacamentos mes` da pagina 6, para automoveis e comerciais leves, com parser integrado a rotina mensal, preview no Streamlit, persistencia no banco e backfill historico validado para `12/2025` a `06/2026`, conforme `docs/external_data/25_FENABRAVE_PHASE2_ITEM1_RANKING_EMPLACAMENTOS_MES_PLAN.md` e `docs/external_data/24_FENABRAVE_PHASE2_EXTENDED_DATA_PLAN.md`.
- [x] Finalizar o item 2 da fase 2 Fenabrave, `Ranking dos emplacamentos acumulado` da pagina 7, para automoveis e comerciais leves, com parser integrado a rotina mensal, persistencia em `market_vehicle_model_rankings` e backfill historico validado.
- [x] Finalizar o item 3 da fase 2 Fenabrave, `Ranking por marca mes` da pagina 8, para automoveis e comerciais leves, com parser integrado a rotina mensal, persistencia em `market_vehicle_brand_rankings` e backfill historico validado.
- [x] Finalizar o item 4 da fase 2 Fenabrave, `Ranking por marca acumulado` da pagina 9, para automoveis e comerciais leves, com parser integrado a rotina mensal, preview no Streamlit, persistencia em `market_vehicle_brand_rankings` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`, mantendo `source_file_id = 8` apenas como duplicidade historica rastreavel.
- [x] Finalizar o item 5 da fase 2 Fenabrave, `Emplacamentos por sub segmento` da pagina 17, com parser, preview, validacoes, persistencia mensal automatica e backfill historico validado, considerando apenas a tabela principal da pagina 17, removendo o prefixo `AU -` dos subsegmentos e preservando separadamente o acumulado do ano corrente (`n`) e do ano anterior (`n-1`).
- [x] Finalizar os itens 6, 7 e 8 da fase 2 Fenabrave, cobrindo `Mercado de eletrificados`, `Total por marca hibrido mes` e `Total por marca eletrico mes` das paginas 20 e 21, com parser estabilizado para `automoveis` e `comerciais_leves`, preview no Streamlit, persistencia em `market_vehicle_electrified_registrations` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`.
