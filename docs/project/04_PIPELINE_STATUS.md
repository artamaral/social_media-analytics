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
- Observacao: continua sendo a origem normal de novos posts e alimenta a fila

#### Worker creator analytics

- Status: migrado em execucao controlada
- Regiao atual: `us-central1`
- Motivo da migracao: avaliar reducao de preco/custo operacional em relacao a
  regiao anterior
- Escopo: worker de analytics/coleta de creators
- Validacao pendente:
  - confirmar que o worker inicia corretamente na nova regiao
  - confirmar que `YOUTUBE_API_KEY` esta disponivel no runtime
  - confirmar chamadas bem-sucedidas para YouTube Data API
  - confirmar inserts/atualizacoes esperados no Supabase
  - comparar custo, duracao media, erros e quota consumida contra a operacao
    anterior
- Leitura operacional:
  - a migracao para `us-central1` ainda nao deve ser considerada definitiva ate
    haver evidencia de execucao correta e reducao real de custo

### 1.2 Worker de metricas de posts

- Status: operacional
- Implementacao principal: `scripts/cloud_run/postMetrics/main.py`
- Fonte da fila: `public.v_post_update_queue_batch`
- Lote atual: `50` posts por execucao
- Guardrail atual: ate `6` posts com menos de `3` checagens
- Fila normal atual: ate `44` posts por bandas de prioridade
- Validacao de custo:
  - lote `40`: sem aumento relevante de custo no Cloud Run apos alguns dias em
    producao
  - lote `50`: em validacao controlada; risco esperado baixo porque a chamada
    `videos.list` continua em uma unica requisicao ate `50` IDs

#### Comportamento validado

- leitura da fila via view fatiada
- `next_check` controlado no SQL
- FIFO dentro da banda
- refill global entre bandas quando ha sobra de cota
- monitoramento indireto do worker deve usar evidencia no banco, nao apenas
  retorno do script; ver `docs/social_media/32_WORKER_HEALTH_MONITORING_SPEC.md`

#### Leitura operacional priorizada

- `fila_itens_prontos` nao deve ser usado como KPI principal do worker horario,
  porque a view de lote continua devolvendo `50` linhas elegiveis por desenho e
  esse numero mascara a composicao real do lote
- `falhas_recentes_24h` nao deve ser KPI principal deste worker, porque
  sobrepoe o sinal ja acompanhado em posts mortos e validacao humana
- os sinais operacionais priorizados para o worker horario passam a ser:
  - `itens_atrasados`
  - `at_risk_bootstrap`
  - `recovery_low`
- leitura recomendada:
  - `itens_atrasados` mede aderencia do worker ao agendamento definido em
    `next_check`
  - `at_risk_bootstrap` mostra posts novos em risco de nao atingir cobertura
    minima no tempo esperado
  - `recovery_low` mostra falha de cobertura ja consumada em posts mais antigos

#### Revisao de `next_check`

- Status: prioridade alta
- Sinais observados no dashboard:
  - `Ate 1h = 48`
  - `Ate 6h = 199`
  - `Ate 24h = 430`
- Leitura preliminar:
  - os numeros sugerem que a regra atual de `next_check` precisa de revisao
  - ainda falta entender qual faixa de atraso deve orientar a nova regra de
    agendamento
- Proximo passo:
  - analisar distribuicao por banda, idade do post e cobertura minima antes de
    alterar `calculate_next_check(...)`

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
- `4` dos `9` posts ja constam como possiveis dead posts, ainda com baixa
  cobertura
- posts confirmados manualmente como dead/unavailable continuam aparecendo em
  outras metricas, portanto a exclusao por status ainda nao esta padronizada
  em toda a camada analitica

Proxima avaliacao:

- auditar os `9` posts residuais antes de retomar o scheduler
- confirmar manualmente candidatos dead e marcar `status = 'unavailable'`
  quando aplicavel
- revisar views e metricas operacionais para excluir confirmados como
  `unavailable` quando a analise nao for uma auditoria de indisponibilidade

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
  - usar `itens_atrasados`, `at_risk_bootstrap` e `recovery_low` como trio
    principal de sinais operacionais do worker horario

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

- Status: implementacao inicial pronta para uso local controlado
- Implementacao principal: `scripts/fenabrave_ingestion/ingest_fenabrave_phase1.py`
- Documento operacional principal: `scripts/fenabrave_ingestion/README.md`
- Papel na arquitetura: ingestao estruturada de emplacamentos e leitura mensal
  de mercado

#### Escopo operacional atual

- o PDF fonte ja deve estar salvo no Supabase Storage
- o registro inicial em `market_source_files` continua manual nesta fase
- o script executa leitura do PDF, extracao da primeira tabela, normalizacao e
  validacao dos totais
- o fluxo suporta `dry-run`, `write`, `replace` e revisao interativa

#### Estado atual

- a frente ja possui script, setup local e runbook de execucao mensal
- o processo ainda e local e controlado, nao um pipeline automatico completo
- a estrutura minima de ingestao e validacao ja esta desenhada

### 2.2 Carros na Web

- Status: em fase de planejamento de ingestao
- Documento principal: `docs/external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md`
- Papel na arquitetura: base estruturada de catalogo automotivo, versoes e
  ficha tecnica

#### Estado atual

- existe plano detalhado para discovery por links reais do catalogo
- a fase 1 prevista usa CSV e HTML bruto locais antes de schema definitivo no
  Supabase
- ainda nao ha implementacao principal versionada em `scripts/carrosnaweb_ingestion/`

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

### 2.4 Proximos checkpoints desta frente

- consolidar Fenabrave como rotina mensal repetivel
- iniciar a base Carros na Web em formato local controlado
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
- `Cadastro > Criadores` ja foi validado em producao operacional via
  Streamlit:
  - caso validado: `Autoesporte`
  - `creator_id`: `55`
  - `entity_id`: `52`
  - `channel_id`: `UCc6jv88ebCrDVxJQUjZfGT`
  - subnichos: `compra`, `noticia`, `review`, `teste`
  - resultado: criador cadastrado com subnicho e visivel na view de criadores
  - pendente: confirmar nos proximos dias se o worker incorporou o criador ao
    ciclo normal de discovery/coleta

### 3.4 Proximos checkpoints desta frente

- acompanhar se o novo criador validado entra no ciclo normal dos workers
- consolidar overview, creators e crescimento semanal
- expor indicadores de qualidade dos dados antes dos rankings
- manter consumo sob demanda do Supabase sem expor `service role key`

---

## 4. Leitura transversal

### 4.1 O que esta operacional hoje

- social media no YouTube esta operacional
- worker de metricas esta operacional
- backfill legado fase 1 foi concluido
- Fenabrave ja tem implementacao local inicial e runbook
- dashboard ja tem base SQL e direcao tecnica definidas

### 4.2 O que ainda esta em execucao controlada

- score hibrido `v2`
- guarda de cobertura minima
- consolidacao da rotina Fenabrave
- inicio da ingestao Carros na Web
- estudo de granularidade para SENATRAN / RENAVAM
- implementacao do app Streamlit

### 4.3 O que bloqueia a proxima etapa

- evolucao do social media depende de consolidar cobertura minima e validacoes
  de historico
- evolucao das fontes externas depende de transformar planos em ingestao
  repetivel
- evolucao do dashboard depende de app inicial e integracao segura com as views

### 4.4 Ultima verificacao manual consolidada

- Data de referencia deste status: `2026-05-26`
- Resultado:
  - frente social media segue como base operacional principal
  - frente Fenabrave ja saiu de estudo e entrou em implementacao local
  - frente Carros na Web segue em planejamento
  - frente SENATRAN / RENAVAM segue em estudo
  - frente dashboard ja validou cadastro de criadores via Streamlit com
    visibilidade na view de criadores
  - ainda falta acompanhar a incorporacao do criador validado pelos workers

