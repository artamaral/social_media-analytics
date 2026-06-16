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
- `Posts mortos e validacao humana`: `13/13` confirmados ou monitorados, `0` pendencias humanas e `0` candidatos em aberto
- `Monitoramento de posts sem checagem`: ainda existem posts abaixo da cobertura minima, mas sem risco imediato na faixa critica observada
- `Sinais operacionais`: continuam sendo o principal ponto de atencao por atraso agregado do worker horario

#### Open point principal - regra de `next_check`

- status: aberto e prioritario
- leitura atual:
  - o monitoramento implementado ja mostra atraso e cobertura, mas ainda nao
    responde se a regra de `next_check` e suficiente ou nao
  - contagens brutas por faixa de atraso tendem a crescer conforme a base de
    posts cresce, portanto nao devem ser lidas isoladamente
  - a analise precisa considerar a prioridade esperada de cada post no
    agendamento, e nao apenas `tempo desde o atraso` e `volume acumulado`
- checagens que ainda faltam:
  - verificar se a prioridade embutida em `next_check` esta coerente com banda
  - verificar se esta coerente com idade do post
  - verificar se esta coerente com cobertura minima esperada
  - verificar se esta coerente com urgencia operacional e risco real de atraso
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
- a modelagem inicial ja existe no repositorio com:
  - `market_data_sources`
  - `market_source_files`
  - `market_vehicle_registrations_segment`
  - `v_dashboard_fenabrave_monthly_segments`

#### O que ainda falta nesta frente

- decidir se a modelagem atual por segmento permanece como fase suficiente por
  mais tempo ou se deve expandir para `marca` e `modelo`
- decidir se a camada `raw` sera persistida formalmente no banco ou se
  continuara apenas como etapa transitiva de extracao
- decidir se a frente passa a ter tabela formal de `ingestion_runs` e de
  validacoes persistidas
- consolidar a rotina mensal como processo repetivel, e nao apenas execucao
  local controlada

### 2.2 Carros na Web

- Status: bloqueado por captcha; ainda em avaliacao de viabilidade de ingestao
- Documento principal: `docs/external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md`
- Papel na arquitetura: base estruturada de catalogo automotivo, versoes e
  ficha tecnica

#### Estado atual

- existe plano detalhado para discovery por links reais do catalogo
- ja existe codigo versionado para diagnostico de acesso, parser exploratorio
  de tabela e discovery de modelos em `scripts/carrosnaweb_ingestion/`
- o diagnostico recente conseguiu retornar `success` para fichas reais como
  `44763`, `22547` e `4801`
- a captura real ainda encontra captcha em alguns padroes e por isso os dados
  ainda nao estao sendo obtidos com confiabilidade suficiente
- por isso, a frente ainda nao deve ser tratada como schema definitivo nem como
  pipeline estruturado
- ja existe parser de `table/tr/td` funcionando sobre HTML bruto, mas o fluxo
  completo ainda nao foi consolidado como rotina repetivel

#### O que ainda falta nesta frente

- validar se existe caminho etico e repetivel para captura sem bypass de
  protecao
- confirmar se a cobertura obtida justificaria manter a frente como fonte
  estruturada
- somente depois disso decidir se faz sentido criar schema proprio no Supabase

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
- tratar Carros na Web primeiro como problema de viabilidade de captura antes de
  retomar schema e pipeline
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

### 3.4 Proximos checkpoints desta frente

- implementar overview, creators e crescimento semanal
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
- avaliacao de viabilidade do Carros na Web sob captcha
- estudo de granularidade para SENATRAN / RENAVAM
- implementacao do app Streamlit

### 4.3 O que bloqueia a proxima etapa

- evolucao do social media depende principalmente de analisar se a regra de
  `next_check` esta priorizando corretamente a base conforme ela cresce, alem
  de consolidar cobertura minima e validacoes de historico
- evolucao das fontes externas depende de transformar planos em ingestao
  repetivel
- evolucao do dashboard depende de app inicial e integracao segura com as views

### 4.4 Ultima verificacao manual consolidada

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
  - frente Carros na Web esta bloqueada por captcha e ainda nao deve ser
    tratada como pipeline estruturado
  - frente SENATRAN / RENAVAM segue em estudo
  - frente dashboard esta com estrategia pronta e aguarda implementacao do app

