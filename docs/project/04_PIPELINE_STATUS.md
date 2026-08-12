# PIPELINE STATUS

## Visao geral

Este arquivo registra o estado operacional atual do projeto organizado em 3
frentes:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

O objetivo e manter uma leitura simples de:

- o que esta rodando
- o que ja foi validado
- o que ainda esta em execucao controlada
- o que bloqueia a proxima etapa

---

## 1. Dados social media

### 1.1 Scraper principal

- Status: operacional
- Implementacao principal: `scripts/cloud_run/youtube_main_scraper/main.py`
- Objetivo: descoberta e ingestao principal de posts
- Frequencia atual: a cada `3 horas`
- Configuracao Cloud Run atual: maximo `1 vCPU` e `256 MB` de RAM
- Observacao: continua sendo a origem normal de novos posts e alimenta a fila

### 1.2 Worker de metricas de posts

- Status: operacional
- Implementacao principal: `scripts/cloud_run/postMetrics/main.py`
- Fonte da fila: `public.v_post_update_queue_batch`
- Frequencia atual: a cada `30 minutos`
- Lote atual: `50` posts por execucao
- Guardrail atual: ate `6` posts com menos de `3` checagens
- Fila normal atual: ate `44` posts por bandas de prioridade
- Configuracao Cloud Run atual: maximo `1 vCPU` e `256 MB` de RAM
- Validacao de custo:
  - lote `40`: sem aumento relevante de custo no Cloud Run apos alguns dias em
    producao
  - lote `50`: em validacao controlada; risco esperado baixo porque a chamada
    `videos.list` continua em uma unica requisicao ate `50` IDs
  - reducao de recursos para maximo `1 vCPU` e `256 MB` de RAM viabilizou
    aumentar a frequencia operacional sem aumentar complexidade do pipeline

#### Comportamento validado

- leitura da fila via view fatiada
- `next_check` controlado no SQL
- FIFO dentro da banda
- refill global entre bandas quando ha sobra de cota
- monitoramento executivo do worker ja implementado no Streamlit com 5 blocos:
  - `Monitoramento de posts sem checagem`
  - `Posts mortos e validacao humana`
  - `Integridade da coleta`
  - `Evidencia de processamento`
  - `Sinais operacionais`
- isolamento de videos `unavailable` validado na fila operacional em
  2026-06-16:
  - `v_post_update_queue_batch`: `0` posts `unavailable`, status `ok`
  - `v_dashboard_post_update_queue_batch`: `0` posts `unavailable`, status
    `ok`

#### Leitura atual do monitoramento

- `Integridade da coleta`: status `ok`
- `Evidencia de processamento`: status `ok`
- `Posts mortos e validacao humana`: `33/33` confirmados ou monitorados, `0` pendencias humanas e `0` candidatos em aberto
- `Monitoramento de posts sem checagem`: ainda existem posts abaixo da cobertura minima, mas sem risco imediato na faixa critica observada
- `Sinais operacionais`: continuam sendo o principal ponto de atencao por atraso agregado do worker de metricas

Leitura operacional:

- essa frente cobre o review humano dos videos indisponiveis e nao deve ser lida como sinal de duplicidade de coleta
- o papel dela e separar confirmados/monitorados de candidatos em aberto e manter visibilidade operacional do fluxo
- o worker de discovery agora persiste heartbeat em
  `youtube_discovery_heartbeats`, permitindo separar no dashboard:
  - `rodou sem novidades`
  - `falhou antes de gerar resultado`
  - ausencia de execucao recente
- a view `v_dashboard_new_post_discovery_status` passa a priorizar heartbeat e
  usa `posts.created_at` e `creator_metrics_history` apenas como fallback
- o KPI visual `Snapshots canal 24h` foi removido do Streamlit em
  `2026-07-16`, porque o numero estava confuso para leitura executiva e nao era
  mais evidencia principal do discovery
- ponto aberto: avaliar remocao futura desse campo tambem da
  `v_dashboard_new_post_discovery_status` quando o fallback legado deixar de
  ser util para diagnostico

Validacao real mais recente do heartbeat:

- data de referencia: `2026-07-16`
- resultado observado no Cloud Run:
  - `heartbeat_id = 2`
  - `cursor = 3`
  - `next_cursor = 6`
  - `processed = 3`
  - `errors = 0`
  - `inserted_or_updated_posts = 150`
- confirmacoes operacionais:
  - `Heartbeat create: 201`
  - `Cursor status: 200`
  - `Creators status: 200`
  - retorno final com payload coerente para o batch executado
- confirmacao visual:
  - o Streamlit mostrou coleta recente e texto coerente para o caso validado
- cobertura de cenarios ainda pendente:
  - `partial_error`
  - `failed`
  - `success` sem posts novos (`rodou sem novidades`)

#### Open point principal - regra de `next_check`

- status: aberto e prioritario
- leitura atual:
  - o monitoramento implementado ja mostra atraso, cobertura e frescor, mas a
    regra de `next_check` continua em aberto porque a pressao operacional cresce
    junto com a base de posts
  - contagens brutas por faixa de atraso tendem a crescer com o tempo, portanto
    nao devem ser lidas isoladamente
  - a analise precisa considerar a prioridade esperada de cada post no
    agendamento, e nao apenas `tempo desde o atraso` e `volume acumulado`
  - para formar historico rapido e confiavel, cada post deve sair do bootstrap
    com mais de `3` snapshots, apoiado pela prioridade da fila
- checagens que ainda faltam:
  - verificar se a prioridade embutida em `next_check` esta coerente com banda
  - verificar se esta coerente com idade do post
  - verificar se esta coerente com cobertura minima esperada
  - verificar se esta coerente com urgencia operacional e risco real de atraso
- criterio operacional ja valido:
  - manter os posts monitorados ate ultrapassarem `3` snapshots
  - tratar a fila como mecanismo de aceleracao do historico, nao como
    contagem estavel em tempo fixo
- criterio de saida deste open point:
  - concluir se a regra atual e suficiente ou nao
  - se nao for suficiente, definir ajuste de prioridade antes de mudar apenas
    thresholds ou tempos absolutos

### 1.3 Backfill offline de `legacy_low` - fase 1

- Status: concluida
- Implementacao: `scripts/offline_backfill/legacy_low_backfill_phase1.py`
- Launcher agendado: `scripts/offline_backfill/run_legacy_low_backfill_phase1.ps1`
- Objetivo: inserir 1 snapshot inicial para posts antigos com historico
  insuficiente
- Escopo: apenas `legacy_low`
- Prioridade de selecao:
  - `total_checagens asc`
  - `priority_score_v2 desc`
- Tamanho do lote: `50`
- Frequencia atual do scheduler: `10` minutos
- Observacao de custo: consumo observado da API do YouTube segue baixo nesta
  frequencia
- Observacao operacional: logs por execucao agora sao obrigatorios em
  `scripts/offline_backfill/logs`

#### Resultado da primeira execucao validada

- Ultimo snapshot inserido: `2026-05-14 21:27:43.970034`
- `legacy_low` antes: `511`
- `legacy_low` depois: `474`
- Reducao observada: `37`

#### Interpretacao

- a fase 1 esta funcionando como esperado
- os snapshots foram inseridos em `post_metrics_history`
- os posts atendidos continuam `history_level = low`, o que e esperado nesta
  fase
- o objetivo imediato continua sendo reduzir o passivo legado, nao promover
  estado

#### Encerramento da fase 1

- `legacy_low` residual observado: `3`
- composicao residual:
  - `legacy_low` com `0` checagens: `2`
  - `legacy_low` com `1` checagem: `1`
- os logs da execucao passaram a mostrar apenas `3` candidatos
- a fase 1 cumpriu o objetivo de drenar o passivo legado relevante
- o `low` remanescente da base passa a ser explicado principalmente por
  `bootstrap_low`, nao por backlog legado

#### Trabalho restante antes da fase 2

- manter a fase 1 pausada, salvo necessidade de rodada corretiva pontual
- detalhar a fase 2 de promocao de estado para os legados agora com contexto
- desenhar o bootstrap de posts novos, que passa a ser a principal fonte de
  `low`
- acompanhar logs do scheduler junto com inserts no banco em qualquer futura
  retomada

#### Atualizacao observada apos aproximadamente 12h

- `legacy_low` atual: `447`
- distribuicao atual de `history_level`:
  - `full`: `1785`
  - `low`: `636`
  - `partial`: `7`
- distribuicao de checagens:
  - principal concentracao atual em `2` checagens: `1033` posts
  - ainda existem `165` posts com `1` checagem

#### Interpretacao da atualizacao

- a fase 1 segue drenando o passivo legado
- o seed historico em massa parece estar funcionando
- a promocao para `partial` ainda e residual, o que continua coerente com o
  desenho atual
- a estrategia passa a priorizar explicitamente posts com `0`, `1` e `2`
  checagens, nessa ordem, usando `priority_score_v2` como criterio secundario
  para acelerar a reducao do `legacy_low`

#### Estimativa operacional atual

- base inicial de `legacy_low`: `511`
- lote configurado: `50`
- execucoes necessarias estimadas: aproximadamente `11`
- execucoes validadas ate agora: `1`
- execucoes ainda pendentes estimadas: aproximadamente `10`

### 1.4 Proximos checkpoints desta frente

#### Cleanup temporario do guardrail

- Status: pausado pelo usuario apos reducao forte do backlog operacional
- Tarefa: `guardrail-cleanup-backfill`
- Frequencia: a cada `10` minutos
- Script: `scripts/offline_backfill/legacy_low_backfill_phase1.py`
- Launcher: `scripts/offline_backfill/run_legacy_low_backfill_phase1.ps1`
- Resultado do scheduler validado: `0` na execucao de `2026-05-19 17:10`
- Objetivo:
  - limpar `warm_8_30d` e `old_30d_plus` ate `3` checagens
  - limpar `new_0_3d` e `recent_4_7d` ate `2` checagens
  - devolver o controle restante ao guardrail permanente

Baseline inicial registrado em `2026-05-19 17h`:

| video_age_bucket | total_checagens | total_posts |
| --- | ---: | ---: |
| new_0_3d | 0 | 41 |
| recent_4_7d | 0 | 75 |
| recent_4_7d | 1 | 43 |
| warm_8_30d | 2 | 548 |
| old_30d_plus | 1 | 1 |
| old_30d_plus | 2 | 806 |

Resultado parcial apos pausa:

| video_age_bucket | total_checagens | total_posts |
| --- | ---: | ---: |
| warm_8_30d | 2 | 6 |
| old_30d_plus | 1 | 1 |
| old_30d_plus | 2 | 2 |

Leitura atual:

- restam `9` posts no alvo do cleanup temporario
- a frente de `Posts mortos e validacao humana` no Streamlit ja tratou os `13`
  posts detectados, sem pendencias humanas em aberto
- o ponto remanescente agora e confirmar que toda a camada analitica exclui
  corretamente `unavailable` fora dos contextos de auditoria

Proxima avaliacao:

- auditar os `9` posts residuais antes de retomar o scheduler
- revisar views analiticas de rankings, crescimento e cobertura geral para
  excluir confirmados como `unavailable` quando a analise nao for uma
  auditoria de indisponibilidade

#### Guarda de cobertura minima

- especificacao registrada em:
  - `docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md`
- objetivo:
  - impedir que posts com menos de `3` checagens fiquem para tras
- proximo passo:
  - aplicar e validar no banco a nova versao de `v_post_update_queue_batch`
  - manter `bootstrap_low`, `at_risk_bootstrap` e `recovery_low` apenas como
    diagnosticos de monitoramento
  - acompanhar se a fatia de `4` slots e suficiente para manter o guardrail
    sob controle
  - cruzar os sinais do Streamlit com a regra de `next_check` para entender se
    o agendamento esta priorizando corretamente a base conforme o crescimento
    do numero de posts

#### Backfill legado fase 1

- confirmar reducao continua do `legacy_low`
- confirmar reducao dos blocos de `0`, `1` e `2` checagens
- confirmar inserts recorrentes em `post_metrics_history`
- confirmar que a selecao continua aderente a `total_checagens asc` e
  `priority_score_v2 desc`

#### Fase 2 do legado

- desbloqueada do ponto de vista operacional
- depende agora de definicao da estrategia de promocao temporal entre snapshots
- baseline inicial registrado em:
  - `docs/social_media/24_PHASE2_INITIAL_DATA_BASELINE_2026-05-17.md`

#### Score hibrido `v2`

- status: analitico, nao ativo
- baseline atual registrado em:
  - `docs/social_media/26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md`
- leitura atual:
  - overlap baixo entre fila ativa e `v2`
  - `v2` ainda favorece muitos `low` em bandas altas
  - acceleration aparece praticamente nula no baseline
  - formula ainda precisa de recalibracao antes de promocao

### 1.5 Problemas conhecidos desta frente

- posts seedados pela fase 1 nao saem imediatamente de `low`
- o `bootstrap_low` continua sendo a principal fonte de `low`
- sem guarda de cobertura minima, posts com menos de `3` checagens podem ficar
  para tras e recriar `legacy_low`
- a fase 2 ainda nao foi iniciada
- houve um incidente operacional no scheduler do Windows:
  - a tarefa ficou com a acao malformada
  - o script manual rodava, mas a execucao agendada falhava
  - a ausencia de log persistente atrasou o diagnostico

#### Mitigacao aplicada

- a tarefa foi recriada com comando corrigido
- o launcher passou a gravar log por execucao e um arquivo `latest`
- troubleshooting de scheduler agora exige:
  - checar `Last Result`
  - checar log mais recente
  - checar novos inserts em `post_metrics_history`

---

## 2. Dados de fontes externas

### 2.1 Fenabrave

- Status: rotina mensal estruturada, historico validado no banco e governanca
  final fechada para a fase 2 ativa
- Implementacao principal: `scripts/fenabrave_ingestion/ingest_fenabrave_phase1.py`
- Documento operacional principal: `scripts/fenabrave_ingestion/README.md`
- Papel na arquitetura: ingestao estruturada de emplacamentos e leitura mensal
  de mercado

#### Escopo operacional atual

- o PDF fonte pode ser carregado pela view `Cadastro Fenabrave` direto no
  bucket privado `market-source-files`
- o caminho do arquivo deve respeitar o padrao `fenabrave/{ano}/{mes}/`
- o registro em `market_source_files` continua guiado pela rotina operacional
  do app
- o script executa leitura do PDF, extracao por item, normalizacao, validacoes
  por bloco e persistencia nas tabelas analiticas da frente
- o fluxo suporta `dry-run`, `write`, `replace` e revisao interativa

#### Estado atual

- a frente ja possui rotina mensal guiada por UI, script versionado, setup
  local, runbook e backfill historico validado no Supabase
- a fase 2 ativa foi consolidada para o historico `12/2025` a `06/2026`,
  cobrindo os itens `1..8` e `11..22`
- a revisao formal de 2026-07-12 confirmou cobertura canonica completa nos
  `source_file_id` `17`, `5`, `4`, `3`, `2`, `6` e `13`
- a duplicidade residual de `12/2025` foi saneada, mantendo apenas o
  `source_file_id = 17` como cadastro canonico em `market_source_files`
- a modelagem operacional ja existe no repositorio com:
  - `market_data_sources`
  - `market_source_files`
  - `market_vehicle_registrations_segment`
  - `market_fenabrave_extraction_items`
  - `market_vehicle_model_rankings`
  - `market_vehicle_brand_rankings`
  - `market_vehicle_subsegment_shares`
  - `market_vehicle_electrified_registrations`
  - `market_vehicle_sales_channel_mix`
  - `v_dashboard_fenabrave_monthly_segments`

#### Governanca operacional fechada

- cada execucao mensal da Fenabrave passa a ser tratada como um
  `ingestion_run` logico, sem exigir nova tabela fisica nesta etapa
- o identificador operacional do run e o registro canonico em
  `market_source_files`, com `reference_period` no primeiro dia do mes e PDF
  preservado em `market-source-files/fenabrave/{ano}/{mes}/`
- a granularidade de status por bloco fica em
  `market_fenabrave_extraction_items`, com `item_code`, `status`, `row_count` e
  `validation_status`
- a carga mensal so deve ser considerada fechada quando:
  - o arquivo mensal estiver cadastrado e rastreavel no Storage
  - a fase 1 estiver persistida e validada
  - todos os itens ativos da fase 2 (`1..8` e `11..22`) estiverem com status
    concluido ou warning aceito
  - as validacoes de cobertura, linhas esperadas e coerencia mensal/acumulado
    tiverem sido revisadas
- a criacao de uma tabela fisica dedicada de `ingestion_runs` deixa de ser
  obrigatoria no Sprint 5 e deve ser retomada apenas se houver necessidade de
  orquestracao automatica, retries, SLA operacional ou monitoramento
  multi-fonte

#### O que ainda falta nesta frente

- manter a execucao mensal conforme calendario offline, apos o 5o dia util
- avaliar futuramente se a rotina precisa evoluir para automacao de agenda,
  alerta ou tabela fisica de runs quando houver operacao recorrente suficiente
- aplicar e validar no Supabase a RPC canonica
  `public.get_fenabrave_monthly_packet(reference_period, scope)` preparada no
  repositorio em 2026-08-12 para consumo direto por GPT online/mobile

#### Packet RPC para GPT

- Status: implementacao local preparada no repositorio; ainda nao aplicada nem
  validada no banco real
- DDL principal: `sql/ddl/functions/009_create_fenabrave_monthly_packet_rpc.sql`
- Teste estrutural: `sql/ddl/tests/012_test_fenabrave_monthly_packet_rpc.sql`
- Papel na arquitetura:
  - devolver um `jsonb` canonico para analise editorial
  - evitar SQL bruto no cliente GPT
  - manter Hermes fora do fluxo de analise

### 2.2 Carros na Web

- Status: CSVs de catalogo seguem como frente estruturada a modelar; scraping
  de fichas tecnicas em `on_hold`
- Documento principal: `docs/external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md`
- Papel na arquitetura: base estruturada de catalogo automotivo, fabricantes,
  modelos e anos do modelo, com consumo futuro no Streamlit

#### Estado atual

- o usuario confirmou em 2026-07-15 que os CSVs de catalogo ja existem fora
  desta maquina e devem ser baixados regularmente
- a frente deixa de depender de scraping de fichas para avancar
- o contrato operacional passa a ser baixar os CSVs, detectar novas entradas,
  persistir no Supabase e consumir por uma view no Streamlit
- fichas tecnicas por scraping nao sao viaveis nesta etapa e ficam em
  `on_hold`
- diagnosticos antigos de ficha e parser exploratorio permanecem como evidencia
  historica, mas nao guiam a execucao atual

#### O que ainda falta nesta frente

- definir origem/caminho de download dos CSVs recorrentes
- criar modelagem inicial no Supabase para catalogo, com rastreabilidade de
  arquivo, hash/versao, data de download e status de validacao
- criar view inicial para Streamlit, priorizando cobertura, novas entradas e
  consulta por fabricante/modelo/ano
- manter fichas tecnicas em `on_hold` ate surgir fonte viavel sem scraping

### 2.3 SENATRAN / RENAVAM

- Status: em fase de estudo
- Documento principal: `docs/external_data/22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md`
- Papel na arquitetura: camada governamental de frota registrada e validacao
  estrutural

#### Estado atual

- a fonte ja foi enquadrada como estruturada no escopo do projeto
- a granularidade e a modelagem final ainda nao foram fechadas
- a preocupacao principal segue sendo distinguir corretamente frota registrada
  de venda e emplacamento

#### O que ainda falta nesta frente

- definir qual dataset aberto sera usado de fato
- definir a granularidade util para o produto
- definir a tabela normalizada final
- validar a rotulagem de frota para nao confundir o uso analitico com venda

### 2.4 Proximos checkpoints desta frente

- consolidar Fenabrave como rotina mensal repetivel
- modelar Carros na Web por CSV recorrente, com banco e view para Streamlit
- fechar a avaliacao de granularidade util para SENATRAN / RENAVAM
- harmonizar futuramente marcas e modelos entre social media, Fenabrave,
  catalogo tecnico e frota registrada

---

## 3. Dashboard

### 3.1 Direcao atual

- Status: estrategia definida, app inicial criado na branch `codex/dashboard-streamlit-mvp`
- Solucao atual: Streamlit Community Cloud
- Fonte de dados: Supabase sob demanda
- Documento principal: `docs/dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md`

### 3.2 Base analitica

- views principais ja definidas:
  - `v_dashboard_creator_summary`
  - `v_dashboard_post_growth_7d`
  - `v_dashboard_guardrail_coverage_status`
  - `v_dashboard_dead_post_validation_status`
  - `v_dashboard_unavailable_video_review`
- principio mantido:
  - Data Quality deve aparecer antes dos rankings com 2 KPIs: legado guardrail e posts mortos/validacao

### 3.3 Estado atual

- a camada SQL de consumo inicial ja foi preparada
- a stack do dashboard ja foi decidida
- o posicionamento como ferramenta interna de estudo de mercado ja foi
  confirmado
- o app Streamlit inicial ja existe na branch `codex/dashboard-streamlit-mvp`
- a conexao com Supabase via secrets ja foi validada no app
- Data Quality ja exibe:
  - `Monitoramento de posts sem checagem`
  - `Posts mortos e validacao humana`
  - `Integridade da coleta`
  - `Evidencia de processamento`
  - `Sinais operacionais`
- o principal uso atual do Data Quality e orientar a analise da regra de
  `next_check` e da cobertura operacional do worker
- incidente de estabilidade do Streamlit Cloud em 2026-07-12:
  - sintomas: app encerrava com `Segmentation fault` sem traceback Python
  - runtime fixado em Python 3.12 via `runtime.txt` e `.python-version`
  - traces indicaram que a queda ocorria apos as queries e durante a
    renderizacao de componentes
  - pagina confirmada no log: `Criadores > Criador individual`
  - mitigacao inicial aplicada: remover cache do cliente Supabase e aliviar o
    caminho padrao de renderizacao
  - fechamento operacional em 2026-07-15: graficos e dataframes foram
    reintroduzidos por lotes controlados em `Criador individual`,
    `Data Quality`, `Cadastro de Criadores` e Fenabrave sem nova queda
    reportada pelo usuario
  - padrao adotado: `st.dataframe` e `st.plotly_chart` usam `width="stretch"`
    nos pontos estabilizados, evitando o padrao antigo com
    `use_container_width=True`
  - leitura atual: incidente estabilizado; manter monitoramento em novos
    deploys e evitar reintroduzir componentes pesados sem teste controlado

### 3.4 Proximos checkpoints desta frente

- manter observacao da estabilidade do dashboard no Streamlit Cloud apos a
  reintroducao controlada dos componentes interativos
- implementar overview, creators e crescimento semanal quando a frente de
  estabilidade estiver encerrada
- expor indicadores de qualidade dos dados antes dos rankings
- manter consumo sob demanda do Supabase sem expor `service role key`

---

## 4. Leitura transversal

### 4.1 O que esta operacional hoje

- social media no YouTube esta operacional
- worker de metricas esta operacional
- backfill legado fase 1 foi concluido
- Fenabrave opera com rotina mensal estruturada, preview no Streamlit e
  historico validado da fase 2 ativa
- dashboard ja tem base SQL e direcao tecnica definidas

### 4.2 O que ainda esta em execucao controlada

- score hibrido `v2`
- guarda de cobertura minima
- modelagem inicial do Carros na Web por CSV recorrente
- classificador GPT da Taxonomia V2 em preparacao para execucao agendada em
  VPS Hostinger via `cron`
- estudo de granularidade para SENATRAN / RENAVAM
- expansao funcional do app Streamlit

### 4.3 O que bloqueia a proxima etapa

- evolucao do social media depende principalmente de analisar se a regra de
  `next_check` esta priorizando corretamente a base conforme ela cresce, alem
  de consolidar cobertura minima e validacoes de historico
- evolucao das fontes externas depende principalmente de modelar Carros na Web
  por CSV recorrente e definir SENATRAN/RENAVAM; Fenabrave ja tem governanca
  mensal fechada para a fase 2 ativa
- evolucao do dashboard depende de expandir a cobertura funcional do app sobre
  as views ja operacionais
- evolucao da classificacao GPT depende de implementar o script minimo,
  copiar para a VPS, validar execucao manual e so depois ativar cron

Status do classificador GPT em 2026-07-24:

- script inicial versionado em
  `scripts/video_classification/classify_videos_gpt_v2.py`
- seed estatico versionado em `sql/dml/seed_video_taxonomy_v2.sql`
- execucao suportada por enquanto:
  - `title_metadata` direto de `posts`/`creators`
  - `transcript_90s` apenas com CSV de transcricoes ja existente
- cron ainda nao esta ativo
- proximo checkpoint: copiar o script para `/opt/social-media-analytics/bin/`
  na VPS e rodar `--dry-run` manual

### 4.4 Ultima verificacao manual consolidada

- Data de referencia deste status: `2026-07-12`
- Resultado:
  - a revisao formal da frente Fenabrave confirmou cobertura canonica completa
    da fase 2 ativa para `12/2025` a `06/2026`
  - os itens `1..8` e `11..22` ficaram presentes e validados em todos os meses
    canonicos
  - a duplicidade cadastral de `12/2025` foi saneada em
    `market_source_files`, mantendo apenas `source_file_id = 17`
- Data de referencia deste status: `2026-07-15`
- Resultado:
  - a governanca final da Fenabrave foi fechada como contrato operacional:
    `market_source_files` representa o run mensal canonico e
    `market_fenabrave_extraction_items` persiste o status por item
  - a rotina mensal deve seguir o calendario offline apos o 5o dia util,
    processando sempre o mes anterior
  - uma tabela fisica dedicada de `ingestion_runs` nao e obrigatoria nesta
    etapa e fica condicionada a automacao futura, retries, SLA ou monitoramento
    multi-fonte

- Data de referencia deste status: `2026-07-15`
- Resultado:
  - a frente Carros na Web foi redefinida para CSVs recorrentes de catalogo,
    persistencia no Supabase e view de consumo no Streamlit
  - fichas tecnicas por scraping ficaram em `on_hold`
  - a proxima execucao deve definir origem dos CSVs, modelagem inicial,
    validacoes de download e contrato da view

- Data de referencia deste status: `2026-06-16`
- Resultado:
  - Sprint 1 validou que videos `unavailable` nao aparecem na fila operacional
    do worker nem na view de dashboard da fila
  - auditoria usada:
    `sql/dml/audit_unavailable_posts_in_queue.sql`
  - resultado consolidado:
    - `v_dashboard_post_update_queue_batch`: `0` posts `unavailable`, status
      `ok`
    - `v_post_update_queue_batch`: `0` posts `unavailable`, status `ok`
  - permanece como proximo cuidado separar a auditoria de views analiticas de
    ranking, crescimento e cobertura geral

- Data de referencia deste status: `2026-05-19`
- Resultado:
  - frente social media segue como base operacional principal
  - frente Fenabrave ja saiu de estudo e entrou em implementacao local
  - leitura antiga sobre Carros na Web foi substituida em 2026-07-15 pelo
    contrato de CSV recorrente com fichas tecnicas em `on_hold`
  - frente SENATRAN / RENAVAM segue em estudo
  - frente dashboard esta com estrategia pronta e aguarda implementacao do app

