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
- [ ] [melhoria] Retry automatico para falhas API. Reexecutar falhas temporarias com
  backoff e limite de tentativas, sem esconder erro persistente, para reduzir
  lacunas de coleta e dependencia de operacao manual.

## Dados / Qualidade

- [ ] [ops] Identificar creators sem coleta recente (>30d). Monitorar creators sem novos posts por janela definida para decidir pausa do discovery, introduzir status `on_hold_discovery` e evitar seguir descobrindo posts de creators que ficaram inativos por tempo relevante.
- [ ] [ops] Revisar periodicamente a regra de `next_check` e a capacidade diaria da fila, porque o volume total de checagens tende a crescer junto com a base de posts; a monitoracao existe, mas o problema escala com o tempo e exige manter cada post com mais de `3` snapshots para formar historico rapido dentro da prioridade da fila.
- [ ] [bug] Padronizar exclusao de `dead posts` das metricas e views analiticas, mantendo esses posts apenas em auditoria e revisao humana para nao contaminar a leitura da base ativa.

## Analytics

- [ ] [feat] Query de crescimento por intervalo. Comparar intervalos customizaveis para medir delta, taxa de crescimento e aceleracao, reaproveitando a base temporal ja existente.
- [ ] [feat] Ranking de creators emergentes. Ordenar creators por crescimento relativo recente, combinando volume, engajamento e frescor para destacar canais em ascensao.
- [ ] [analise] Identificacao de outliers. Detectar picos e desvios fora do padrao em creators e posts, separando crescimento real de ruido operacional.

## Operacional / Monitoramento

- [ ] [feat] Implementar heartbeat operacional do `youtube_main_scraper` para comprovar execucoes sem posts novos e separar "rodou sem novidades" de "nao rodou".
- [ ] [ops] Monitorar o cleanup temporario do guardrail ate `warm_8_30d` e `old_30d_plus` chegarem a `3` checagens, e `new_0_3d` e `recent_4_7d` chegarem a `2`.

## Visualizacao / Estudos de mercado

- [ ] [analise] ATIVIDADE ATUAL E PRIORITARIA: revisar e priorizar a proxima frente da fase 2 Fenabrave apos concluir o bloco `19 a 22`, consolidando backlog, roadmap operacional e criterio de cobertura restante para os itens ja entregues no historico `12/2025` a `06/2026`.
- [ ] [melhoria] Evoluir o ranking de creators para tratar frequencia como criterio explicito, porque a base atual e a tela ja cobrem views e engajamento pela `v_dashboard_creator_summary`, mas a cadencia ainda nao entra como ordenacao ou leitura principal do comparativo.
- [ ] [melhoria] Alinhar a lista de videos do criador individual ao mesmo padrao visual de `YouTube > Melhores videos 7d`, porque a tela atual do criador ainda usa tabela simples para os videos e nao a mesma hierarquia visual, colunas e leitura comparavel do ranking semanal.
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
- [x] Validar duplicidade de coleta. Fechado porque existe regra hard coded no fluxo que impede duplicidade de gravacao no snapshot operacional; o historico com mais de uma linha por post continua sendo comportamento esperado e nao foi tratado como issue.
- [x] Monitorar backlog de guardrail separando posts novos, recentes, warm e antigos. Fechado porque essa leitura ja fica absorvida pelo monitoramento total da fila e pelo item de `next_check`; o ponto virou subleitura operacional e nao precisa seguir como item separado.
- [x] Revisar periodicamente a regra de `next_check` em `Operacional / Monitoramento`. Fechado por fallback para `Dados / Qualidade`, onde o mesmo tema ficou concentrado com a formulacao mais completa e sem duplicidade.
- [x] Auditar os `9` posts residuais do cleanup temporario do guardrail antes de retomar o scheduler. Fechado porque a frente de `Posts mortos e validacao humana` hoje esta em `33/33`, com `0` pendencias humanas e `0` candidatos em aberto, superando o contexto antigo dos residuais e dos `4` possiveis dead posts.
- [x] Criar view temporal `v_dashboard_hot_posts_now` baseada em velocidade recente e aceleracao do score, sem depender do score hibrido `v2` como regra operacional. Entregue como `v_dashboard_hot_now` e refinada para o contrato `Hot now 24h`.
- [x] App Streamlit online consumindo Supabase sob demanda. Entregue com Streamlit Community Cloud consumindo Supabase sob demanda.
- [x] Tela inicial com status de qualidade dos dados. Entregue na superficie `Data quality` do dashboard.
- [x] Evoluir a view Fenabrave consumida pelo Streamlit para exibir o historico anual completo por periodo, garantindo leitura de 2025 e 2026, com cards mostrando o acumulado do ano por categoria e nao a soma de todos os arquivos carregados. O contrato da dashboard ja define acumulado reiniciado por ano calendario e os cards nao devem somar todos os arquivos.
- [x] Ranking semanal de crescimento de videos. Entregue como `v_dashboard_post_growth_7d` e consumido no dashboard.
- [x] Finalizar o item 5 da fase 2 Fenabrave, `Emplacamentos por sub segmento` da pagina 17, com parser, preview, validacoes, persistencia mensal automatica e backfill historico validado no Supabase para `12/2025` a `06/2026`, considerando automoveis, os percentuais publicados de mes corrente, acumulado do ano corrente (`n`) e acumulado do ano anterior (`n-1`), sem carregar a coluna de mes anterior.
- [x] Tratar videos indisponiveis na YouTube API para evitar posts presos na fila. Implementado com `post_collection_failures`, RPC `register_post_collection_result(...)`, view `v_dashboard_unavailable_video_review`, exclusao de `status = unavailable` da fila ativa e processo de confirmacao manual documentado em `docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`.
- [x] Monitorar semanalmente videos indisponiveis em `v_dashboard_unavailable_video_review` e confirmar manualmente candidatos quando necessario. Fechado pela mesma frente de `Posts mortos e validacao humana`, que hoje mostra `33/33` confirmados/monitorados, `0` pendencias humanas e `0` candidatos em aberto; a tela cobre o review humano como operacao corrente, nao como gap de coleta.
- [x] Criar limpeza temporaria do backlog de guardrail. Implementado no script `scripts/offline_backfill/legacy_low_backfill_phase1.py`, documentado em `docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md` e em execucao controlada via scheduler `guardrail-cleanup-backfill`.
- [x] Manter `priority_score_v2` em modo analitico/segundo plano. Decisao registrada em `docs/project/05_DECISOES_TECNICAS.md`; o `v2` nao deve ser promovido para a fila ativa enquanto o foco for analise temporal de videos quentes no momento.
- [x] Finalizar o item 1 da fase 2 Fenabrave, `Ranking dos emplacamentos mes` da pagina 6, para automoveis e comerciais leves, com parser integrado a rotina mensal, preview no Streamlit, persistencia no banco e backfill historico validado para `12/2025` a `06/2026`, conforme `docs/external_data/25_FENABRAVE_PHASE2_ITEM1_RANKING_EMPLACAMENTOS_MES_PLAN.md` e `docs/external_data/24_FENABRAVE_PHASE2_EXTENDED_DATA_PLAN.md`.
- [x] Finalizar o item 2 da fase 2 Fenabrave, `Ranking dos emplacamentos acumulado` da pagina 7, para automoveis e comerciais leves, com parser integrado a rotina mensal, persistencia em `market_vehicle_model_rankings` e backfill historico validado.
- [x] Finalizar o item 3 da fase 2 Fenabrave, `Ranking por marca mes` da pagina 8, para automoveis e comerciais leves, com parser integrado a rotina mensal, persistencia em `market_vehicle_brand_rankings` e backfill historico validado.
- [x] Finalizar o item 4 da fase 2 Fenabrave, `Ranking por marca acumulado` da pagina 9, para automoveis e comerciais leves, com parser integrado a rotina mensal, preview no Streamlit, persistencia em `market_vehicle_brand_rankings` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`, mantendo `source_file_id = 8` apenas como duplicidade historica rastreavel.
- [x] Finalizar o item 5 da fase 2 Fenabrave, `Emplacamentos por sub segmento` da pagina 17, com parser, preview, validacoes, persistencia mensal automatica e backfill historico validado, considerando apenas a tabela principal da pagina 17, removendo o prefixo `AU -` dos subsegmentos e preservando separadamente o acumulado do ano corrente (`n`) e do ano anterior (`n-1`).
- [x] Finalizar os itens 6, 7 e 8 da fase 2 Fenabrave, cobrindo `Mercado de eletrificados`, `Total por marca hibrido mes` e `Total por marca eletrico mes` das paginas 20 e 21, com parser estabilizado para `automoveis` e `comerciais_leves`, preview no Streamlit, persistencia em `market_vehicle_electrified_registrations` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`.
- [x] Finalizar os itens 11 e 12 da fase 2 Fenabrave, cobrindo `Participacao de venda direta e varejo` das paginas 24 e 25, com parser posicional sem OCR, preview no Streamlit, persistencia em `market_vehicle_sales_channel_mix` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`.
- [x] Finalizar os itens 13 e 14 da fase 2 Fenabrave, cobrindo `Ranking por marca de emplacamento varejo` das paginas 26 e 27, com parser posicional, diagnostico de texto invertido, preview no Streamlit, persistencia em `market_vehicle_brand_rankings` com suporte a share sem unidades e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`.
- [x] Finalizar o item 15 da fase 2 Fenabrave, cobrindo `Ranking por marca de emplacamento direta mes` da pagina 28, com parser posicional, correcao canonica de marcas apos texto invertido, preview no Streamlit, persistencia em `market_vehicle_brand_rankings` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`.
- [x] Finalizar o item 16 da fase 2 Fenabrave, cobrindo `Ranking por marca de emplacamento direta acumulado` da pagina 29, com parser posicional, preview no Streamlit, persistencia em `market_vehicle_brand_rankings` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`.
- [x] Finalizar os itens 17 e 18 da fase 2 Fenabrave, cobrindo o consolidado de `Participacao de mercado por marca` das paginas 3 e 4, com parser posicional, tratamento de texto invertido, preview no Streamlit, persistencia em `market_vehicle_brand_rankings` com `sales_channel = all` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`, mantendo `11` linhas por categoria como contrato publicado desse bloco consolidado.
- [x] Finalizar os itens 19 e 20 da fase 2 Fenabrave, cobrindo `Modelos mais emplacados venda direta mes` das paginas 30 e `Modelos mais emplacados venda varejo mes` da pagina 31, com parser no mesmo contrato do ranking geral por modelo, preview no Streamlit, persistencia em `market_vehicle_model_rankings` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`, aceitando `top N` variavel no item 19 conforme o PDF publicado.
- [x] Finalizar o item 21 da fase 2 Fenabrave, cobrindo `Modelos mais emplacados venda direta acumulado` da pagina 32, com parser no mesmo contrato do item 19, preview no Streamlit, persistencia em `market_vehicle_model_rankings` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`, aceitando `top N` variavel em `comerciais_leves` conforme o PDF publicado.
- [x] Finalizar o item 22 da fase 2 Fenabrave, cobrindo `Modelos mais emplacados venda varejo acumulado` da pagina 33, com parser no mesmo contrato do item 20, preview no Streamlit, persistencia em `market_vehicle_model_rankings` e backfill historico validado para `12/2025` a `06/2026` nos `source_file_id` oficiais `17, 5, 4, 3, 2, 6 e 13`, mantendo `50 + 50` linhas por categoria no historico carregado.
- [x] Confirmar retirada dos itens 9 e 10 da fase 2 Fenabrave do escopo ativo. A revisao operacional da pagina 20 mostrou que o bloco de eletrificados publicado pela Fenabrave traz mercado consolidado e rankings por marca, mas nao traz ranking por modelo; por isso os itens 9 e 10 passam a ser tratados como desejo analitico e nao como dado disponivel para extracao.
