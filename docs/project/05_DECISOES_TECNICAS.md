# ðŸ§  DECISÃ•ES TÃ‰CNICAS

---

## ðŸ“Œ Estrutura de dados

### Uso de histÃ³rico (post_metrics_history)

Motivo:
- Permitir anÃ¡lise temporal
- Calcular crescimento real

---

## ðŸ“Œ EstratÃ©gia de pipeline

- Pipeline A â†’ novos posts
- Pipeline B â†’ atualizaÃ§Ã£o de mÃ©tricas

Motivo:
- ReduÃ§Ã£o de custo
- Escalabilidade

---

## ðŸ“Œ ClassificaÃ§Ã£o de vÃ­deo

- Regra: <= 270s â†’ short
- > 270s â†’ long

Motivo:
- PadronizaÃ§Ã£o

---

## ðŸ“Œ Prioridade de sistema

1. Pipeline funcionando
2. Qualidade dos dados
3. Analytics

Motivo:
- Evitar decisÃµes com dados ruins
---

## Fatiamento da fila de rechecagem

Decisao:

- a fila deixa de ser consumida diretamente por `priority_score desc`
- o sistema passa a usar bandas de prioridade com cotas por faixa
- a selecao do lote passa a ser feita por uma view SQL
- dentro de cada banda, a ordem passa a ser FIFO por `next_check`

Motivo:

- evitar starvation dos posts de faixas intermediarias
- manter prioridade para posts mais relevantes sem bloquear todo o restante
- centralizar a regra de negocio no banco para facilitar manutencao
- evitar concentracao excessiva dos maiores scores dentro da propria banda

Implementacao:

- `calculate_priority_band(...)`
- `calculate_next_check(...)`
- `v_post_update_queue_batch`

Impacto esperado:

- maior cobertura da fila
- rechecagem mais equilibrada
- menor dependencia do worker para regras de selecao
- maior rotacao entre posts da mesma faixa de prioridade

---

## Aumento do lote do worker de metricas para 40 posts

Decisao:

- aumentar o limite da view `v_post_update_queue_batch` de `20` para `40` posts por execucao
- dobrar as cotas por banda mantendo a proporcao original:
  - banda `6`: `8`
  - banda `5`: `8`
  - banda `4`: `8`
  - banda `3`: `6`
  - banda `2`: `6`
  - banda `1`: `4`

Motivo:

- aumentar a cobertura de posts elegiveis
- reduzir backlog operacional sem aumentar a frequencia do scheduler
- preservar a priorizacao por banda e a rotacao FIFO dentro da banda

Status:

- implementado no SQL do repositorio
- aplicado e validado em producao
- validado do ponto de vista de custo do Cloud Run apos alguns dias de execucao

Validacao obrigatoria:

- medir custo diario do Cloud Run
- medir duracao media por execucao
- medir uso de quota da YouTube Data API
- medir volume de inserts em `post_metrics_history`
- medir impacto no Supabase
- calcular custo por snapshot antes de manter a mudanca como definitiva

Resultado observado:

- apos alguns dias rodando com lote de `40` posts por execucao, nao houve aumento relevante de custos no Cloud Run
- a mudanca pode ser considerada aceita do ponto de vista de custo do worker

---

## Otimizacao Cloud Run e nova frequencia dos workers

Data:

- 2026-06-19

Decisao:

- configurar os workers Cloud Run com maximo `1 vCPU` e `256 MB` de RAM
- rodar o worker `postMetrics` a cada `30 minutos`
- rodar o `youtube_main_scraper` de descoberta de novos posts a cada `3 horas`

Motivo:

- reduzir custo unitario por execucao no Cloud Run
- aumentar a cadencia de atualizacao de metricas sem duplicar infraestrutura
- manter descoberta de novos posts mais frequente sem acoplar discovery e
  coleta de metricas
- preservar separacao entre:
  - discovery de novos posts
  - atualizacao de metricas de posts ja conhecidos

Impacto esperado:

- maior velocidade para drenar backlog da fila `postMetrics`
- menor tempo medio ate o primeiro historico de posts novos
- melhor frescor dos dados para o dashboard
- custo operacional controlado pela reducao de CPU/RAM por instancia

Validacao operacional:

- acompanhar duracao media das execucoes no Cloud Run
- acompanhar taxa de erro dos workers
- acompanhar uso de quota da YouTube Data API
- acompanhar volume de inserts em `post_metrics_history`
- acompanhar sinais do Streamlit em `Integridade da coleta`,
  `Evidencia de processamento` e `Sinais operacionais`

---

## Status do discovery com heartbeat operacional persistido

Data:

- 2026-07-16

Decisao:

- persistir heartbeat dedicado do `youtube_main_scraper` em
  `youtube_discovery_heartbeats`
- registrar por execucao `started_at`, `finished_at`, `status`,
  `processed_creators`, `attempted_creators`, `inserted_or_updated_posts`,
  `errors`, `cursor_start`, `cursor_end` e `error_summary`
- atualizar a view `v_dashboard_new_post_discovery_status` para priorizar o
  heartbeat como evidencia principal do discovery
- manter `posts.created_at` e `creator_metrics_history` apenas como fallbacks
  de compatibilidade e degradacao controlada
- expor no Streamlit a diferenca entre `rodou sem novidades`, `nao rodou` e
  `falhou antes de gerar resultado`

Motivo:

- o fallback por `posts.created_at` evitava falso `nok` quando havia posts
  novos, mas ainda nao comprovava uma execucao valida sem novidades
- a operacao precisava distinguir de forma persistida entre execucao sem novos
  posts, falha fatal e ausencia de execucao recente
- o novo contrato fecha essa lacuna sem generalizar prematuramente para um
  framework amplo de `ingestion_runs`

Contrato atual:

- `heartbeat` passa a ser a fonte principal para classificar a saude do worker
  dentro da janela operacional de `6h` e do limite de atencao de `12h`
- `posts.created_at` segue como evidencia de resultado recente quando ainda nao
  houver heartbeat valido
- `creator_metrics_history` permanece apenas como evidencia legada/auxiliar de
  snapshot de canal
- a view do dashboard deve aceitar `fonte_ultima_evidencia` em:
  - `heartbeat`
  - `post_insert`
  - `channel_snapshot_legacy`
- o KPI visual derivado de `creators_avaliados_24h` deixa de aparecer no
  Streamlit, porque o heartbeat passou a ser a leitura principal e o numero
  legado gerava interpretacao ambigua quando vinha `0`
- ponto aberto: manter `creators_avaliados_24h` na
  `v_dashboard_new_post_discovery_status` apenas como fallback tecnico por
  enquanto e revisar remocao futura do campo no SQL

---

## Descricao do YouTube como evidencia opcional do classificador V2

Data:

- 2026-07-29

Decisao:

- manter `public.posts` sem coluna de descricao nesta etapa
- nao transformar a descricao do YouTube em ingestao persistente ainda
- permitir rodadas manuais de calibracao com descricoes salvas em CSV externo
- adicionar `--descriptions-csv` ao classificador GPT V2 para inserir a
  descricao no JSON do harness quando ela estiver disponivel

Motivo:

- separar aquisicao de evidencia textual da classificacao propriamente dita
- testar se descricao melhora a classificacao antes de alterar modelo de dados
  ou pipeline
- evitar repetir o erro operacional de misturar fetch da YouTube Data API,
  montagem do harness e chamada GPT em um unico loop improvisado

Regra operacional:

- o CSV de descricao e artefato temporario/manual
- quando houver descricao preenchida, usar
  `input_evidence_level = title_description`
- quando nao houver descricao, manter `metadata_only`
- a descricao pode enriquecer a evidencia textual, mas nao autoriza inferencia
  sem suporte explicito no titulo, descricao ou metadado recebido

---

## Identificador Carros na Web nas entidades de veiculo classificadas

Data:

- 2026-07-29

Decisao:

- tratar o identificador do catalogo Carros na Web como parte essencial da
  saida operacional de `vehicle_entities[]`
- manter o GPT responsavel pela classificacao semantica e por entidades brutas
  explicitas quando ele as identificar
- executar tambem uma extracao deterministica por script sobre `title`,
  `description` e `transcript_90s`, sem enviar o catalogo ao GPT
- executar o matching contra `public.v_carrosnaweb_vehicle_catalog` no harness
  antes de gravar a classificacao
- preencher em `video_classification_vehicle_entities`:
  - `canonical_manufacturer_name`
  - `canonical_model_name`
  - `canonical_model_year`
  - `catalog_row_id`
  - `catalog_model_id`
  - `catalog_match_level`
  - `match_source`
  - `match_confidence`
  - `validation_issue`

Motivo:

- consultas de pesquisa de mercado dependem de entidade veicular canonica, nao
  apenas de texto bruto
- o GPT nao deve inventar identificador de catalogo nem escolher grafia
  canonica por plausibilidade
- o match contra Carros na Web precisa ser deterministico, auditavel e
  reprocessavel

Regra operacional:

- se marca/modelo/ano encontrarem match unico, gravar `matched` e
  `catalog_row_id`
- se marca/modelo forem encontrados mas o ano estiver ausente, gravar
  `catalog_model_id`, nomes canonicos e `matched`, sem escolher ano artificial
- se nao houver match, gravar `not_found`
- ambiguidades devem ficar em `needs_review`

Leitura esperada no dashboard:

- `ok`: heartbeat recente com posts tocados ou execucao confirmada sem
  novidades
- `atencao`: heartbeat parcial, heartbeat acima da janela ideal ou fallback sem
  heartbeat por `posts.created_at` / `creator_metrics_history`
- `nok`: ultimo heartbeat em `failed` dentro da janela de atencao ou ausencia
  total de evidencia recente

Validacao inicial em producao:

- data de validacao: `2026-07-16`
- execucao observada no Cloud Run:
  - `heartbeat_id = 2`
  - `cursor = 3`
  - `next_cursor = 6`
  - `processed = 3`
  - `errors = 0`
  - `inserted_or_updated_posts = 150`
- comportamento confirmado:
  - criacao do heartbeat com `201`
  - leitura de cursor e creators com `200`
  - status correto no Streamlit para o caso `success` com posts novos
- cenarios ainda nao observados em producao:
  - `partial_error`
  - `failed`
  - `success` sem posts novos

---

## Regra final de next_check da Sprint 2

Data:

- 2026-06-16

Decisao:

- manter o batch do worker em `50` posts por hora com guardrail de `6`
- adotar novo breakdown operacional de cobertura:
  - `needs_coverage`: `< 3`
  - `covered_3_20`: `3..20`
  - `overchecked_21_100`: `21..100`
  - `overchecked_101_plus`: `101+`
- aplicar desaceleracao forte de `next_check` para posts com historico amplo:
  - `warm_8_30d` com `total_checagens >= 21`: minimo `84h`
  - `old_30d_plus` com `total_checagens >= 21`: minimo `84h`
- manter para `warm_8_30d` abaixo desse limiar:
  - bandas `5` e `6`: minimo `12h`
  - bandas `1` a `4`: minimo `24h`
- manter para `old_30d_plus` com `3..20` checagens:
  - minimo `24h`
- manter `new_0_3d`, `recent_4_7d` e `needs_coverage` na regra base por banda

Motivo:

- o maior represamento da fila estava concentrado em `warm_8_30d` e `old_30d_plus`
  com cobertura ampla
- a simulacao offline mostrou que espacamento de `84h` nesses grupos libera
  capacidade real do batch sem pressionar o guardrail
- o recorte `3..20 / 21..100 / 101+` melhora a leitura operacional e alinha a
  classificacao com o ponto em que o valor marginal de nova checagem cai

Evidencia:

- simulacao `260h` com `old_30d_plus >= 21 -> 84h`: fim em `2624`
- simulacao `260h` com `warm_8_30d >= 21 -> 84h` e `old_30d_plus >= 21 -> 84h`:
  fim em `2558`
- ignorando as primeiras `36h`, o cenario com `warm + old` terminou `66` posts
  melhor e com media `26,48` posts menor do que o cenario com `old` apenas

Implementacao:

- migration `2026-06-16_008_queue_next_check_84h_rebucket_up.sql`
- atualizacao da funcao `calculate_next_check(...)`
- recalc da fila existente em `post_update_queue`
- atualizacao do breakdown em `v_dashboard_queue_bottleneck_status` e queries
  operacionais

Impacto esperado:

- menor reentrada prematura de posts warm/old superchecados
- mais espaco util do batch para backlog vencido e cobertura minima
- leitura mais aderente da fila em dashboards e auditorias

---

## Resumo de videos gerado por IA pelo YouTube

Data:

- 2026-05-08

Decisao:

- nao usar o resumo de video gerado por IA pelo YouTube como fonte oficial de dados do produto
- nao implementar scraping desse resumo como dependencia de pipeline
- gerar resumo proprio na camada de enriquecimento quando esse dado for necessario para analytics

Contexto:

- o YouTube informa que resumos gerados por IA existem apenas para videos selecionados em ingles
- os resumos podem aparecer abaixo do video, na Home ou nos resultados de busca
- o recurso e experimental, pode variar em disponibilidade e qualidade, e nao e controlado pelo creator
- a YouTube Data API v3 nao documenta campo publico para retornar esse resumo no recurso `videos`
- o endpoint oficial de captions exige autorizacao e permissao para editar o video quando usado para download de legenda

Motivo:

- evitar dependencia de campo nao documentado ou instavel
- reduzir risco operacional e juridico associado a scraping automatizado do YouTube
- manter a ingestao baseada em APIs oficiais e fontes controlaveis
- permitir padronizacao do resumo por criterios proprios do projeto automotivo

Diretriz de implementacao:

- coletar metadados oficiais via YouTube Data API, como `title`, `description`, `statistics` e `contentDetails`
- usar transcript apenas quando houver fonte permitida e rastreavel
- gerar `video_ai_summary` por LLM no enrichment layer
- registrar origem, idioma, modelo e data de geracao do resumo

Campos sugeridos:

- `video_ai_summary`
- `summary_source`
- `summary_language`
- `summary_generated_at`
- `summary_model`
- `summary_confidence`

Impacto esperado:

- maior controle sobre qualidade semantica dos resumos
- menor risco de quebra por mudancas na interface do YouTube
- melhor alinhamento com classificacao de nicho, subnicho e tipo de conteudo automotivo

---

## Dashboard online com Supabase sob demanda

Data:

- 2026-05-08

Decisao:

- o sistema de visualizacao sera online
- o MVP deve consultar dados do Supabase sob demanda
- a primeira camada de consumo sera baseada em views SQL analiticas
- o frontend nao deve carregar historico bruto para calcular crescimento

Views iniciais:

- `v_dashboard_creator_summary`
- `v_dashboard_post_growth_7d`
- `v_dashboard_data_quality_status` foi a primeira view generica de validacao, mas nao e mais o contrato principal de Data Quality do dashboard

Motivo:

- manter a logica analitica perto do banco
- reduzir duplicacao de regras no frontend
- evitar exposicao de segredos no navegador
- permitir que o dashboard evolua para produto sem reescrever a base de dados

Diretriz de implementacao:

- usar anon key somente com RLS e grants controlados
- nunca expor service role key no browser
- consultar indicadores de qualidade antes dos rankings
- adicionar indices para suportar leitura sob demanda em `post_metrics_history`

Impacto esperado:

- primeiro MVP online com overview, creators e crescimento semanal
- menor custo operacional do que precomputar tudo fora do Supabase no inicio
- base pronta para filtros por nicho, subnicho e tipo de conteudo

---

## Streamlit como solucao atual para dashboard analitico

Data:

- 2026-05-14

Decisao:

- usar Streamlit Community Cloud como solucao atual para o dashboard online
- tratar o dashboard como ferramenta interna de estudo de mercado, nao como produto SaaS publico
- manter Supabase como fonte de dados sob demanda
- manter views SQL como camada principal de consumo analitico

Motivo:

- o numero de acessos deve ser baixo
- a complexidade tende a crescer nas fontes de dados e nas perguntas analiticas, nao na escala de usuarios
- Streamlit permite iterar rapidamente com SQL, Python, Pandas e graficos
- a solucao reduz custo e complexidade em relacao a um app Next.js neste momento

Diretriz de implementacao:

- guardar credenciais no Streamlit secrets
- nunca usar service role key exposta em codigo ou navegador
- consultar os KPIs de Data Quality antes de rankings
- usar filtros de periodo antes de carregar historico
- usar cache com TTL curto para reduzir leituras repetidas no Supabase

Alternativa futura:

- reavaliar Next.js, TypeScript e Vercel/Cloudflare apenas se o dashboard evoluir para produto externo ou multiusuario

---

## Direcao visual do dashboard Streamlit

Data:

- 2026-05-19

Decisao:

- adotar uma linguagem visual inspirada em dashboards editoriais com sidebar escura, cards contrastados e pictos
- usar um fundo geral mais escuro que a referencia visual, baseado em escala de cinza
- manter acentos coral/salmao para destaques e interacoes
- usar pictos/icones lineares para navegacao, KPIs e secoes quando ajudarem a leitura

Motivo:

- o dashboard sera uma ferramenta de estudo de mercado e precisa ser escaneavel
- o visual deve ajudar a separar qualidade de dados, crescimento, creators, videos e operacao
- a escala de cinza reduz ruido visual e deixa os dados e alertas mais claros
- pictos ajudam a reconhecer rapidamente areas recorrentes sem transformar a interface em produto promocional

Diretriz de implementacao:

- criar tema Streamlit com background cinza escuro, sidebar grafite e cards claros/escuros
- evitar visual de landing page ou BI generico demais
- usar cards com raio baixo, cabecalhos escuros e informacao densa
- preservar legibilidade em tabelas e graficos
- reservar cores fortes para sinal analitico: crescimento, alerta, erro e selecao

---

## Data Quality do dashboard com dois KPIs operacionais

Data:

- 2026-05-19

Decisao:

- o bloco de Data Quality do dashboard deve ter exatamente dois KPIs principais
- KPI 1: legado guardrail, usando `v_dashboard_guardrail_coverage_status`
- KPI 2: posts mortos e validacao humana, usando `v_dashboard_dead_post_validation_status` para acompanhar o review humano dos indisponiveis e separar confirmados de candidatos, sem confundir esse fluxo com duplicidade de coleta
- a view generica `v_dashboard_data_quality_status` pode continuar existindo como auditoria auxiliar, mas nao deve guiar o bloco principal de Data Quality do app

Motivo:

- o objetivo do dashboard nao e corrigir todos os dados em tempo real
- o objetivo e garantir que os dados relevantes para analise estao linkados e monitorados
- o guardrail responde se existe legado/recovery abaixo da cobertura minima descrita em `25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md`
- posts mortos precisam ser acompanhados pelo status de validacao humana, nao misturados com checks genericos de frescor

Diretriz:

- nao usar `posts_stale_24h` como bloqueio geral do dashboard
- mostrar `recovery_low` como sinal principal de legado guardrail
- mostrar `pending_human_review` como sinal principal de posts mortos
- manter detalhes brutos das duas views visiveis na pagina Data Quality

---

## Logs persistentes como requisito para rotinas agendadas

Data:

- 2026-05-17

Decisao:

- toda rotina agendada relevante do projeto deve gerar log persistente por execucao
- scheduler sem log local ou centralizado deve ser tratado como configuracao incompleta
- troubleshooting operacional deve sempre combinar:
  - status do scheduler
  - log da execucao
  - evidencia no banco

Contexto:

- o backfill offline de `legacy_low` ficou alguns dias com a tarefa do Windows mal configurada
- a execucao manual funcionava, mas a execucao agendada nao produzia efeito
- a ausencia de log persistente atrasou o diagnostico e consumiu tempo operacional desnecessario

Motivo:

- evitar rotinas cegas
- reduzir tempo de diagnostico
- separar falha de scheduler, falha de script e ausencia de efeito no banco
- preservar evidencias operacionais para auditoria rapida

Diretriz de implementacao:

- gravar um arquivo por execucao com timestamp
- manter tambem um arquivo `latest` para consulta rapida
- documentar caminho do log e comando de leitura no runbook operacional
- validar logs antes de considerar uma automacao saudavel

Primeira aplicacao:

- `scripts/offline_backfill/run_legacy_low_backfill_phase1.ps1`
- logs em `scripts/offline_backfill/logs`

---

## Guarda de cobertura minima de historico

Data:

- 2026-05-17

Decisao:

- todo post com menos de `3` snapshots deve entrar no guardrail de cobertura
- o alvo operacional inicial e `3` snapshots por post
- a implementacao principal deve usar a regra simples `total_checagens < 3`
- os nomes `bootstrap_low`, `at_risk_bootstrap` e `recovery_low` ficam como
  diagnosticos, nao como regra principal de implementacao
- a configuracao inicial recomendada e reservar `4` slots por execucao para
  guardrail dentro do lote de `40`

Contexto:

- a fase 1 do backfill de `legacy_low` drenou o backlog historico para nivel
  residual
- o `low` remanescente passou a ser explicado principalmente por
  `bootstrap_low`
- sem uma rotina preventiva, novos posts podem envelhecer e recriar
  `legacy_low`

Motivo:

- impedir que posts fiquem perdidos por falta de snapshots
- transformar `legacy_low` futuro em alerta operacional, nao em backlog normal
- separar cold start legitimo de falha de cobertura
- proteger a avaliacao futura de velocity e acceleration

Diretriz:

- monitorar diariamente o total de posts com `total_checagens < 3`
- ordenar a fatia guardrail por `total_checagens asc`, `created_at asc` e
  `priority_score desc`
- tratar crescimento persistente do guardrail como sinal de falta de capacidade
- manter logs e evidencias de banco para qualquer rotina automatizada

Documento de referencia:

- `docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md`

---

## Monitoramento operacional do worker de metricas por fluxo e risco de cobertura

Data:

- 2026-05-21

Decisao:

- o bloco de sinais operacionais do worker de metricas nao deve usar
  `fila_itens_prontos` como KPI principal
- o bloco de sinais operacionais do worker de metricas nao deve usar
  `falhas_recentes_24h` como KPI principal
- os tres KPIs iniciais priorizados passam a ser:
  - `itens_atrasados`
  - `at_risk_bootstrap`
  - `recovery_low`

Contexto:

- a `v_post_update_queue_batch` continua sendo desenhada para devolver um lote
  completo por execucao
- por isso, `fila_itens_prontos` pode permanecer aparentemente saudavel mesmo
  quando o lote esta mascarando itens pouco uteis, atraso real ou baixa
  rotacao entre bandas
- `falhas_recentes_24h` sobrepoe o problema ja acompanhado na camada de posts
  mortos e validacao humana
- os problemas historicos observados no projeto foram mais proximos de
  capacidade, atraso e cobertura do que de volume bruto da fila:
  - starvation em bandas intermediarias
  - posts recentes presos com `1` coleta
  - crescimento de passivo com menos de `3` checagens
  - envelhecimento de posts para `recovery_low`

Motivo:

- medir o fluxo real do worker e nao apenas o volume aparente da view de lote
- detectar cedo quando a capacidade horaria deixa de sustentar a cobertura
  minima
- separar causa operacional de efeito acumulado na camada de Data Quality

Diretriz:

- `Monitoramento de posts sem checagem` continua sendo KPI de estoque e
  cobertura acumulada
- `Sinais operacionais` deve medir fluxo, atraso e risco de degradacao
- leitura recomendada:
  - `itens_atrasados` responde se o worker esta respeitando `next_check`
  - `at_risk_bootstrap` antecipa posts novos que podem falhar na cobertura
    minima
  - `recovery_low` mostra falha de cobertura ja consumada

Impacto esperado:

- leitura mais fiel da capacidade real do worker de metricas
- melhor capacidade de avaliar se o bucket atual esta dimensionado
- menor duplicacao de KPI entre fluxo operacional e posts mortos

---

## Revisao de `next_check` orientada por sinais operacionais

Data:

- 2026-05-21
- Atualizacao: 2026-06-15

Decisao:

- abrir revisao de prioridade alta sobre a regra de geracao de `next_check`
- nao alterar a funcao ainda sem analisar a distribuicao por banda, idade do
  post e cobertura minima
- adotar como direcao de regra revisada a desaceleracao de posts ja cobertos em
  `warm_8_30d` e `old_30d_plus`
- manter a politica atual/guardrail para posts com menos de `3` checagens

Contexto:

- os sinais operacionais do dashboard passaram a mostrar concentracao relevante
  em faixas de atraso maiores do que a janela desejada
- observacao atual dos sinais:
  - `Ate 1h = 48`
  - `Ate 6h = 199`
  - `Ate 24h = 430`
- esses numeros sugerem que o agendamento atual merece reavaliacao, mas ainda
  nao fecham sozinhos a regra ideal
- analise de 2026-06-15 mostrou que posts `old_30d_plus` com centenas de
  checagens continuavam voltando muito rapido por causa de `priority_score`
  alto
- exemplos observados:
  - posts `old_30d_plus`, `priority_band = 6`, com `777` a `940` checagens
    eram reagendados em `30 minutes`
  - simulacao com `old_30d_plus`, bandas `5` e `6` a cada `12h`, e demais
    bandas a cada `24h`, removeu `289` posts do `due_now`
  - simulacao em `warm_8_30d` apenas para posts ja cobertos (`3+`
    checagens), com bandas `5` e `6` a cada `12h`, e demais bandas a cada
    `24h`, removeu `130` posts do `due_now`

Motivo:

- o problema nao e apenas atraso pontual; e preciso entender se a funcao de
  `next_check` esta calibrada para a rotacao real da fila
- uma mudanca precipitada pode piorar cobertura ou deslocar o backlog para uma
  faixa errada
- a leitura precisa continuar conectada ao guardrail, ao tamanho do bucket e a
  idade dos posts
- a frequencia alta deve capturar mudanca recente e janela de crescimento, nao
  apenas volume acumulado de views/likes/comments
- posts antigos ja cobertos continuam relevantes para rankings historicos, mas
  nao devem consumir a mesma cadencia de posts novos ou em bootstrap

Diretriz:

- tratar essa revisao como prioridade alta na `main`
- manter os sinais operacionais como base de analise antes de mexer em
  `calculate_next_check(...)`
- documentar qualquer nova regra de agendamento com os criterios usados para
  separar `Ate 1h`, `Ate 6h` e `Ate 24h`
- regra aprovada e implementada em SQL:
  - `total_checagens < 3`: preservar politica atual e guardrail
  - `new_0_3d` e `recent_4_7d`: preservar politica atual
  - `warm_8_30d` com `total_checagens >= 3`:
    - bandas `5` e `6`: minimo `12h`
    - bandas `1` a `4`: minimo `24h`
  - `old_30d_plus` com `total_checagens >= 3`:
    - bandas `5` e `6`: minimo `12h`
    - bandas `1` a `4`: minimo `24h`
- a implementacao nao deve ser feita apenas editando a funcao atual, pois
  `calculate_next_check(priority_score, checked_at)` nao recebe `post_date` nem
  `total_checagens`
- a implementacao foi feita com uma sobrecarga de `calculate_next_check(...)`
  que recebe `post_date` e `total_checagens`
- o trigger `refresh_post_queue_on_metrics()` passa a buscar `post_date` e
  `total_checagens` antes de calcular o novo `next_check`
- migration de aplicacao:
  `sql/migrations/2026-06-15_004_queue_next_check_age_coverage_up.sql`
- migration de rollback:
  `sql/migrations/2026-06-15_004_queue_next_check_age_coverage_down.sql`
- o Streamlit deve acompanhar a fila por banda com:
  - posts vencidos por banda
  - media de checagens por banda
  - backlog atrasado por idade/check band
  - concentracao do batch atual por idade e saturacao

---

## Views de cadastro no Streamlit como camada operacional guiada

Data:

- 2026-05-21

Decisao:

- implementar no Streamlit views de cadastro para processos operacionais do
  projeto
- iniciar com duas views:
  - `Cadastro de Criadores`
  - `Cadastro Fenabrave`
- tratar essas views como camadas guiadas de operacao, e nao como substitutas
  dos processos manuais e das regras de governanca ja documentadas

Contexto:

- o dashboard passou a ter mockups operacionais para validar metodo, texto,
  ordem das etapas e pontos de controle antes de ligar o app ao SQL
- no caso de criadores, o fluxo depende de `entity_intake`, revisao, publish e
  validacao antes do cadastro final em `creators`
- no caso de Fenabrave, a rotina depende de confirmacao da fonte, preservacao
  do PDF, registro de `market_source_files`, preview, validacao e aprovacao do
  periodo

Motivo:

- reduzir erro operacional
- tornar a governanca visivel dentro do app
- validar o processo com baixo custo antes de implementar RPCs, grants e
  ligacoes SQL reais
- evitar que o Streamlit vire uma porta de escrita direta em tabelas finais

Diretriz:

- a UI deve espelhar o processo manual existente, nao reinventar a rotina
- qualquer escrita futura no banco deve ser controlada e rastreavel
- a ligacao SQL dessas views deve ser implementada em etapas, com foco primeiro
  na leitura e no bloqueio de erros operacionais

Impacto esperado:

- melhor validacao de UX e governanca antes da integracao real
- backlog mais claro para ligacao SQL das views de cadastro
- menor risco de misturar app operacional com bypass de processo

---

## PDF Fenabrave via Streamlit com persistencia oficial no Storage

Data:

- 2026-05-21

Decisao:

- permitir o carregamento do PDF mensal e historico da Fenabrave pela view
  `Cadastro Fenabrave` no Streamlit
- usar a propria UI para enviar o arquivo ao bucket privado com caminho
  padronizado por periodo em `fenabrave/{ano}/{mes}/arquivo.pdf`
- manter o bucket privado `market-source-files` como armazenamento oficial

Contexto:

- a rotina mensal da Fenabrave continua controlada nesta fase
- a carga historica precisa de um fluxo repetivel por ano e mes dentro da
  propria UI
- ao mesmo tempo, o processo documentado exige preservacao do PDF, rastreio por
  `storage_path` e protecao contra exposicao de credenciais privilegiadas

Motivo:

- melhorar a ergonomia operacional sem quebrar a seguranca
- suportar carga historica no Streamlit sem depender de upload manual fora do
  app
- preservar o papel do Storage privado e dos metadados em
  `market_source_files`

Diretriz:

- o upload pelo app deve usar fluxo seguro
- o `storage_path` deve ser derivado do periodo selecionado para manter a pasta
  `fenabrave/{ano}/{mes}/`
- o app nao deve expor `SUPABASE_SERVICE_ROLE_KEY` ao navegador; se o upload
  ocorrer pelo Streamlit, a chave pode existir apenas em `secrets` do servidor
- a versao oficial do PDF precisa continuar no bucket privado
- a liberacao do periodo segue dependente de preview, validacao e aprovacao
  humana

Impacto esperado:

- caminho claro para evoluir a rotina mensal sem perder governanca
- separacao objetiva entre apoio operacional na UI e persistencia oficial no
  backend

---

## Historico de followers de creators por snapshot

Data:

- 2026-05-21

Decisao:

- tratar `creators.followers` como valor corrente, nao como historico analitico
- criar uma camada de snapshots para metricas dinamicas de creator, iniciando por followers do YouTube
- usar a YouTube Data API `channels.list` com `part=statistics` para coletar `statistics.subscriberCount`
- gravar cada coleta na tabela `creator_metrics_history`
- manter `creators.followers` sincronizado com o snapshot mais recente para consumo rapido no dashboard
- a leitura semanal de audiencia deve usar o fechamento da semana contra o
  fechamento da semana anterior, nunca o delta entre primeiro e ultimo snapshot
  da mesma semana como numero executivo

Contexto:

- followers de creator sao metricas dinamicas, assim como views, likes e comments dos posts
- a tabela `creators` ja possui o campo `followers`, mas ele representa apenas o estado atual
- a tabela `creator_metrics_history` passa a ser a fonte de verdade para serie
  semanal de audiencia no Streamlit
- a tela semanal de criadores deve consumir `v_dashboard_creator_weekly_audience`
  para seguidores e manter `v_dashboard_creator_weekly_activity` apenas para
  videos, views, likes e comentarios
- sem snapshots, nao sera possivel medir crescimento de canal, aceleracao ou tendencia de audiencia
- a API oficial do YouTube expoe `statistics.subscriberCount`, `statistics.hiddenSubscriberCount`, `statistics.viewCount` e `statistics.videoCount` no recurso de canal
- o `subscriberCount` retornado pela API pode ser arredondado para tres algarismos significativos

Motivo:

- preservar historico de crescimento de canais
- evitar analises baseadas apenas no volume atual de seguidores
- permitir ranking de creators emergentes por crescimento relativo
- alinhar metricas de creators ao mesmo principio ja usado em `post_metrics_history`
- manter o dashboard rapido sem perder rastreabilidade historica

Diretriz de implementacao:

- avaliar implementacao inicial no `youtube_main_scraper`, pois ele ja percorre creators e chama `channels.list` para buscar a playlist de uploads
- aproveitar a chamada de canal adicionando `statistics` ao `part` quando fizer sentido operacional
- inserir snapshot em `creator_metrics_history` a cada coleta bem-sucedida
- atualizar `creators.followers` com o `subscriberCount` mais recente
- salvar tambem sinais auxiliares como `hidden_subscriber_count`, `channel_views` e `video_count`
- nao acoplar essa coleta ao `postMetrics` neste momento, pois esse worker opera por video e deve continuar focado em metricas de posts

Campos sugeridos para snapshot:

- `creator_id`
- `followers`
- `channel_views`
- `video_count`
- `hidden_subscriber_count`
- `collected_at`

Impacto esperado:

- base para crescimento temporal de canais
- melhor leitura de creators emergentes no setor automotivo
- possibilidade futura de comparar crescimento de audiencia com performance de videos
- menor risco de misturar metricas correntes com metricas historicas

## Regra de delta snapshot-a-snapshot para semana fechada em `v_dashboard_creator_weekly_activity`

Data:

- 2026-06-18

Decisao:

- a semana fechada de `Views`, `Likes` e `Comentarios` deve somar os deltas
  snapshot-a-snapshot observados dentro da janela
- cada delta deve ser alocado na semana do snapshot atual
- nao criar novo status de validacao para esse caso; a correcao deve ser apenas
  matematica no SQL e documentacao do contrato

Motivo:

- a leitura semanal deve refletir o portfolio completo do criador
- a forma mais auditavel de fazer isso e somar os deltas de cada snapshot na
  semana do proprio snapshot
- isso evita depender de uma base intermediaria de carry e deixa a regra mais
  simples de validar

Diretriz de implementacao:

- calcular `snapshot_atual - snapshot_anterior` para views, likes e comentarios
- alocar o delta na semana do snapshot atual
- manter `posts_sem_baseline_para_delta` apenas para os posts que realmente nao
  possuem snapshot anterior util
- manter `videos_publicados` separado do delta de snapshots

---

## Score hibrido v2 em espera e foco em analise temporal

Data:

- 2026-05-19

Decisao:

- manter `priority_score_v2` em modo analitico e em segundo plano
- nao promover o `v2` para a fila ativa neste momento
- separar a fila operacional da analise temporal do dashboard
- priorizar uma view simples de "hot now" baseada em velocidade recente e
  aceleracao do score

Contexto:

- o baseline do `v2` mostrou baixo overlap com a fila ativa
- o `v2` ainda favorece posts `low` em bandas altas por causa de popularidade
  base
- a aceleracao aparece fraca no score agregado atual
- a fila ativa ja possui guardrail para cobertura minima e bandas operacionais
- a avaliacao atual do backlog mostrou que o maior problema de curto prazo e
  limpar divida de guardrail, nao trocar o score da fila

Motivo:

- o produto deve responder primeiro o que esta quente no momento
- analises do dashboard serao majoritariamente temporais, nao baseadas na vida
  inteira do video
- detectar tracao recente e mais importante agora do que antecipar videos que
  ainda nao possuem historico suficiente
- a promocao do `v2` adicionaria complexidade operacional sem beneficio claro
  para o MVP analitico

Diretriz:

- fila operacional continua com guardrail + `priority_band` atual
- dashboard deve usar views temporais para medir:
  - velocidade recente
  - velocidade anterior
  - aceleracao
- `v2` so deve voltar a ser prioridade se houver necessidade explicita de uma
  fila operacional mais inteligente
- nao usar `v2` como criterio de produto para o ranking "quente agora"

Formula conceitual recomendada para analytics:

```text
velocity_6h = (score_agora - score_6h_atras) / horas

previous_velocity = (score_6h_atras - score_24h_atras) / horas

acceleration = velocity_6h - previous_velocity
```

Impacto esperado:

- simplificacao do modelo analitico
- menor risco de promover posts com baixo historico por fallback de score
- melhor alinhamento entre dashboard e pergunta de negocio
- manutencao da estabilidade operacional da fila atual

Documentos relacionados:

- `docs/social_media/26_HYBRID_SCORE_V2_BASELINE_2026-05-17.md`
- `docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md`

---

## Contrato inicial do ranking `Hot now`

Data:

- 2026-06-20

Decisao:

- implementar o `Hot now v1` como ranking analitico de oportunidade baseado em
  views por hora, velocidade recente e aceleracao
- manter likes e comentarios como contexto exibido no dashboard, sem peso no
  score inicial
- manter o ranking separado da fila operacional, de `calculate_next_check(...)`
  e de `priority_score_v2`
- exigir tolerancia conservadora de baseline para evitar falso positivo:
  - snapshot corrente com no maximo `12h`
  - baseline nominal de `6h` aceito entre `6h` e `8h`
  - baseline nominal de `24h` aceito entre `18h` e `30h`
  - delta recente positivo de views
  - exclusao de posts `unavailable`

Motivo:

- a validacao do Sprint 4 mostrou que a base possui historico amplo, mas nem
  sempre com densidade suficiente para tratar qualquer baseline antigo como
  comparavel a `6h`
- `4022` posts estavam ativos apos excluir `20` indisponiveis
- `3947` posts ativos tinham historico `full` na view analitica existente
- apenas `11` posts atendiam ao criterio conservador final do `Hot now v1`,
  dos quais `7` apresentavam aceleracao positiva
- manter o ranking pequeno no inicio e preferivel a premiar videos com
  baselines distantes demais e leitura temporal enganosa

Formula v1:

```text
velocity_6h = (views_atual - views_6h) / horas_entre_snapshots
previous_velocity = (views_6h - views_24h) / horas_entre_baselines
acceleration = velocity_6h - previous_velocity
hot_now_rank_score = velocity_6h + greatest(acceleration, 0)
```

Diretriz de implementacao:

- a view `v_dashboard_hot_now` deve expor `eligibility_status` para explicar
  exclusoes por historico insuficiente, baseline fora da tolerancia ou ausencia
  de movimento recente
- a ordenacao oficial deve ser:
  - `hot_now_rank_score desc`
  - `acceleration desc`
  - `velocity_6h desc`
- qualquer relaxamento futuro de tolerancia deve ser registrado como decisao,
  nao aplicado silenciosamente na SQL ou no Streamlit

Impacto esperado:

- ranking mais fiel a tracao recente
- menor dependencia de popularidade acumulada
- separacao clara entre oportunidade analitica e prioridade operacional de
  coleta

---

## Revisao do ranking `Hot now` para o modelo 24h

Data:

- 2026-06-21

Decisao:

- substituir o contrato inicial `6h/24h` do `Hot now v1` por um contrato
  `Hot now 24h`
- manter separados:
  - ranking analitico do dashboard
  - fila operacional
  - `calculate_next_check(...)`
- aplicar os seguintes bloqueios:
  - `no_snapshot`
  - `insufficient_snapshots`
  - `latest_snapshot_stale` quando o ultimo snapshot tiver mais de `24h`
- calcular o sinal temporal com os tres snapshots mais recentes disponiveis:
  - velocidade atual = ultimo vs anterior
  - velocidade anterior = anterior vs penultimo
  - aceleracao = velocidade atual - velocidade anterior
- manter o score:
  - `hot_now_rank_score = velocidade_atual + greatest(aceleracao, 0)`

Motivo:

- a comparacao entre elegibilidade do `Hot now` e a regra vigente de
  `next_check` mostrou desalinhamento estrutural:
  - `2935` posts eram excluidos por `latest_snapshot_stale`
  - `1305` desses ainda estavam com `next_check` no futuro
- a simulacao de relaxar apenas o stale threshold quase nao resolvia a lista;
  o verdadeiro gargalo do contrato antigo passava a ser `baseline_6h_missing`
- a simulacao com snapshots consecutivos preservou rastreabilidade temporal e
  ficou mais aderente ao ritmo real de medicao da base

Evidencia:

- no universo `Hot now`, excluindo `unavailable`:
  - `frescor_24h`: `2125` elegiveis
  - `718` elegiveis com aceleracao positiva
- overlap com `v_dashboard_post_growth_7d`:
  - interseccao total alta por compartilhar a base recente monitorada
  - overlap baixo no topo:
    - `top 10 x top 10`: `0`
    - `top 20 x top 20`: `3`
    - `top 50 x top 50`: `13`
- leitura final:
  - `Melhores videos 7d` continua respondendo crescimento semanal
  - `Hot now 24h` passa a responder aceleracao recente sob frescor operacional
    plausivel

Formula v2:

```text
velocidade_atual = (views_ultimo - views_anterior) / horas_entre_eles
velocidade_anterior = (views_anterior - views_penultimo) / horas_entre_eles
aceleracao = velocidade_atual - velocidade_anterior
hot_now_rank_score = velocidade_atual + greatest(aceleracao, 0)
```

Diretriz de implementacao:

- preservar o contrato de colunas da `v_dashboard_hot_now` para evitar quebra
  no Streamlit
- aceitar que os aliases historicos `velocity_6h` e `collected_at_6h` passem a
  representar o snapshot anterior disponivel, nao uma ancora fixa de `6h`
- refletir essa mudanca de semantica nos rotulos e textos explicativos da tela

---

## Execucao controlada por sprint ativo

Data:

- 2026-06-16

Decisao:

- criar uma agenda formal de sprints em `docs/project/07_SPRINT_AGENDA.md`
- tratar o sprint ativo como filtro obrigatorio de execucao do projeto
- executar automaticamente apenas atividades relacionadas ao sprint ativo
- quando uma demanda nao tiver relacao clara com o sprint ativo, o GPT deve
  perguntar ao usuario antes de prosseguir
- sem confirmacao explicita do usuario, demandas fora do sprint ativo devem ser
  tratadas como ideias para backlog/roadmap, nao como execucao

Motivo:

- evitar execucao desorganizada
- impedir que novas ideias interrompam estabilidade de pipeline, data quality e
  dashboard
- preservar foco operacional enquanto o projeto evolui para uma plataforma de
  analytics automotivo
- manter rastreabilidade entre prioridade, execucao e decisao tecnica

Pergunta padrao:

```text
Esta atividade nao esta relacionada ao sprint ativo. Deseja prosseguir mesmo assim ou prefere registrar no backlog/roadmap?
```

Impacto esperado:

- maior controle sobre escopo de cada ciclo de trabalho
- menor risco de misturar backlog com execucao
- maior clareza para decidir datas conforme disponibilidade do usuario
- melhor alinhamento entre roadmap, data quality, pipeline e dashboard

---

## Data Quality como view dedicada, nao como gate embutido em cada ranking

Data:

- 2026-06-20

Decisao:

- remover do Sprint 3 a exigencia de exibir contexto de `Data Quality` dentro
  de cada tela de ranking ou comparativo
- manter `Data quality` como view dedicada e navegavel do dashboard
- nao tratar essa integracao embutida como requisito obrigatorio do MVP atual
- reforcar que novos requisitos de sprint devem nascer de documentacao de
  projeto, roadmap ou decisao tecnica registrada, e nao apenas de uma agenda de
  sprint isolada

Motivo:

- o dashboard tem uso pessoal e a existencia da pagina dedicada de `Data quality`
  ja entrega o diagnostico operacional necessario para esse contexto
- embutir esse resumo em todas as telas comparativas aumentaria complexidade de
  UX sem ganho proporcional de valor para o uso atual
- a exigencia de "Data Quality antes dos rankings" ficou registrada apenas na
  agenda do sprint, sem origem clara em documento de prioridade ou decisao
  tecnica anterior
- o sprint deve refletir o projeto, nao criar sozinho novos requisitos

Impacto esperado:

- fechamento mais coerente do Sprint 3 com o escopo real do MVP entregue
- menor acoplamento entre telas analiticas e sinalizacao operacional
- preservacao da view `Data quality` como superficie oficial de diagnostico
- governanca mais clara entre roadmap, decisoes tecnicas e agenda de execucao

---

## Fenabrave fase 2 por itens, nao por parser unico do PDF

Data:

- 2026-07-07

Decisao:

- implementar a expansao Fenabrave em blocos por item do PDF, com parser,
  preview, validacao e backfill especificos para cada item
- nao criar um parser generico para todo o PDF Fenabrave nesta etapa
- iniciar a execucao pelo item 1 da fase 2:
  `Ranking dos emplacamentos mes`, pagina 6, automoveis e comerciais leves
- manter os itens 2 e 3 no backlog como pendencias explicitas:
  - item 2: localizar e validar corretamente o ranking acumulado antes de
    implementar, pois ele nao foi encontrado na pagina 6 pelo teste de texto e
    tabelas
  - item 3: implementar apos o item 1, aproveitando que o teste da pagina 8
    indicou boa extraibilidade, mas sem misturar a primeira entrega
- deixar paginas com graficos ou associacao visual ambigua fora da primeira
  carga automatizada

Evidencia:

- teste exploratorio com o PDF oficial `2026_06_02.pdf`, baixado da URL publica
  da Fenabrave em 2026-07-06
- resultado geral dos 20 itens avaliados:
  - `10` itens com extracao inicial OK
  - `3` itens com warning
  - `7` itens com falha ou baixa confiabilidade
- paginas com boa extracao textual inicial:
  - `6`, `8`, `9`, `20`, `30`, `31`, `32`, `33`
- paginas com problemas relevantes:
  - `24` e `25`: percentuais aparecem, mas a associacao visual entre categoria
    e canal precisa revisao manual
  - `26` a `29`: conteudo aparece como grafico; texto sai invertido ou fora de
    ordem
  - item 2, item 9 e item 10: nao foram localizados nas paginas informadas pelo
    metodo de texto/tabelas usado no teste

Motivo:

- o PDF combina tabelas reais, texto bem estruturado, blocos graficos e paginas
  cujo significado depende de leitura visual
- uma extracao unica aumentaria o risco de persistir dados aparentemente
  estruturados, mas semanticamente errados
- uma implantacao por item permite validar cada pagina com criterio proprio,
  fazer backfill historico com menor risco e registrar excecoes sem bloquear os
  itens confiaveis

Diretriz de implementacao:

- criar ou usar uma camada de controle por `source_file_id` e `item_code` para
  registrar status, quantidade de linhas, validacoes e pendencias
- implementar primeiro o item 1 com parser dedicado para a pagina 6
- carregar o historico por item para todos os PDFs ja preservados, antes de
  avanca-lo como fonte confiavel para dashboard ou API
- tratar os itens posteriores como extensoes independentes, cada um com plano,
  validacao e criterio de aceite proprios

---

## Status de hold para creators sem coleta recente

Data:

- 2026-07-10

Decisao:

- adotar um status operacional `on_hold_discovery` para creators sem novos posts
  por mais de `30` dias, quando a ausencia de publicacao indicar baixa
  probabilidade de discovery util em vez de falha transitória
- manter a identificacao como monitoramento continuo, nao como exclusao
  definitiva
- usar esse status para sinalizar pausa do discovery daquele creator e evitar
  gasto recorrente com busca de novos posts de um canal potencialmente inativo

Motivo:

- creators sem coleta recente podem representar canal realmente inativo,
  periodo sem publicacao ou falha de discovery
- a ausencia de criterio unico pode fazer o scraper continuar investindo em
  creators com baixa chance de retorno
- um status intermediario separa o "ainda ativo" do "parar por ora e revisar"

Leitura operacional:

- o gatilho inicial de analise deve considerar `> 30d` sem novos posts
- a revisao deve usar contexto de posts existentes, idade da base e recorrencia
  historica do creator
- o status `on_hold_discovery` deve ser reversivel quando houver evidencia nova
  de publicacao
- a auditoria de suporte continua sendo a query de integridade entre creators e
  posts, com `creator_without_recent_discovery` como sinal de alerta e nao como
  bloqueio automatico

---

## Fenabrave: rankings por marca com suporte a share sem unidades

Data:

- 2026-07-12

Decisao:

- manter `market_vehicle_brand_rankings` como tabela unica para rankings por
  marca da Fenabrave
- permitir que `units` seja nulo quando o PDF publicar apenas percentual de
  participacao, como nos itens `13` a `16`
- exigir que pelo menos um entre `units` e `market_share_pct` esteja
  preenchido

Motivo:

- os itens `3` e `4` publicam volume absoluto e share
- os itens `13` e `14` publicam apenas share por marca no breakdown de varejo
- criar uma tabela paralela para o mesmo conceito aumentaria custo de consumo,
  duplicacao de views e complexidade de backfill

Impacto esperado:

- reuso da mesma tabela para rankings por marca totais e por canal
- persistencia mensal dos itens `13` e `14` sem gambiarra no parser
- base pronta para estender o mesmo contrato aos itens `15` e `16`
- suporte explicito a `autos_comerciais_leves` quando o PDF publicar o bloco
  combinado de participacao por canal

Aplicacao operacional ja confirmada:

- os itens `13` e `14` ja foram gravados e retrocarregados de `12/2025` a
  `06/2026` nesse contrato
- o item `15` passa a nascer sobre a mesma base tecnica, sem criar nova tabela
  nem novo formato de persistencia

---

## Fenabrave: fechamento canonico de 12/2025 e revisao formal da fase 2 ativa

Data:

- 2026-07-12

Decisao:

- tratar `source_file_id = 17` como unica referencia canonica de `12/2025`
- remover o cadastro legado `source_file_id = 8` de `market_source_files`
  depois de confirmar ausencia de dependencias analiticas e de auditoria
- considerar a fase 2 ativa formalmente consolidada no historico `12/2025` a
  `06/2026` para os itens `1..8` e `11..22`
- mover a discussao remanescente da frente Fenabrave do eixo "parser/backfill"
  para o eixo de governanca final:
  - `ingestion_runs`
  - persistencia adicional de validacoes
  - lembrete operacional mensal

Motivo:

- a revisao formal de cobertura confirmou presenca e validacao completa dos
  itens ativos em todos os meses canonicos
- o unico ruido operacional remanescente estava na duplicidade cadastral de
  `12/2025`, que podia distorcer selecao de periodo, auditoria e leituras da UI
- manter o cadastro legado sem dependencias reais deixaria a documentacao e a
  operacao mais confusas do que auditaveis

Impacto esperado:

- dezembro/2025 passa a existir com um unico cadastro oficial no fluxo
  Fenabrave
- auditorias, views e telas deixam de competir entre `2025-12-01` e
  `2025-12-02` para o mesmo PDF
- a frente externa fica pronta para discutir governanca final em vez de seguir
  tratando pendencias historicas ja saneadas

Aplicacao operacional ja confirmada:

- o `source_file_id = 8` foi removido de `market_source_files`
- o Streamlit passou a priorizar `match` exato de `reference_period` antes do
  fallback por normalizacao mensal
- a RPC `list_fenabrave_source_files` voltou a expor `12/2025` apenas uma vez,
  ligada ao `source_file_id = 17`

---

## Fenabrave: contrato final de governanca mensal

Data:

- 2026-07-15

Decisao:

- fechar a governanca final da Fenabrave como contrato operacional mensal, sem
  criar uma tabela fisica obrigatoria de `ingestion_runs` nesta etapa
- tratar cada registro canonico de `market_source_files` como o `ingestion_run`
  logico do periodo
- usar `market_fenabrave_extraction_items` como persistencia oficial do status
  por item da fase 2, incluindo `item_code`, `status`, `row_count` e
  `validation_status`
- manter como validacoes persistidas minimas:
  - existencia de um unico arquivo canonico por `reference_period`
  - PDF preservado no Storage em `fenabrave/{ano}/{mes}/`
  - status validado da fase 1
  - status por item ativo da fase 2
  - contagem de linhas por item
  - revisao de cobertura dos itens `1..8` e `11..22`
  - comparacao de coerencia entre mensal, acumulado do ano e acumulado do ano
    anterior quando o item publicar essas dimensoes
- manter o lembrete operacional mensal no calendario offline, com execucao apos
  o 5o dia util e processamento do mes anterior
- retomar uma tabela fisica dedicada de `ingestion_runs` apenas se a rotina
  passar a exigir automacao de agenda, retries, SLA, alertas ou monitoramento
  multi-fonte

Motivo:

- o volume da Fenabrave e mensal e pequeno, com confirmacao humana da fonte e
  upload guiado pela UI
- a rastreabilidade principal ja esta coberta por `market_source_files`,
  Storage e itens de extracao
- criar nova tabela agora aumentaria superficie operacional sem resolver uma
  lacuna real da fase 2 ativa
- a decisao mantem a rotina repetivel e auditavel sem transformar a frente em
  automacao prematura

Impacto esperado:

- a frente Fenabrave deixa de ter pendencia estrutural de governanca no Sprint
  5
- novos meses seguem um criterio claro de fechamento operacional
- parser e backfill permanecem encerrados para o historico `12/2025` a
  `06/2026`, salvo mudanca real no PDF publicado
- a proxima discussao de fontes externas pode focar Carros na Web e
  SENATRAN/RENAVAM

---

## Carros na Web: CSV recorrente no banco e fichas tecnicas em on hold

Data:

- 2026-07-15

Decisao:

- tratar os CSVs existentes do Carros na Web como a fonte operacional da frente
  nesta etapa
- baixar os CSVs regularmente para identificar novas entradas de catalogo
- persistir os dados no Supabase com rastreabilidade de arquivo, data de
  download, hash/versao e status de validacao
- criar uma view analitica inicial para consumo no Streamlit
- colocar fichas tecnicas por scraping em `on_hold`

Motivo:

- o usuario confirmou que os CSVs ja existem, mas nao estao nesta maquina
- o caminho por CSV e mais repetivel e auditavel do que tentar scraping de
  fichas tecnicas
- as fichas tecnicas nao sao viaveis de scrape nesta etapa
- manter a frente parada por causa das fichas impediria usar um catalogo que ja
  pode gerar valor analitico no dashboard

Impacto esperado:

- Carros na Web passa a ter escopo estruturado limitado a catalogo por CSV
- a proxima implementacao deve focar download, staging, tabela normalizada e
  view para Streamlit
- scripts de scraping de ficha, parser de HTML e discovery por ficha deixam de
  guiar o sprint ativo
- futuras discussoes de ficha tecnica so devem voltar se surgir fonte viavel
  sem scraping fragil

---

## Runtime do Streamlit fixado em Python 3.12

Data:

- 2026-07-12

Decisao:

- fixar o runtime do deploy do Streamlit em `python-3.12.12` via
  `runtime.txt` e `.python-version`
- evitar a execucao padrao em Python 3.14 no Streamlit Cloud enquanto houver
  sinais de instabilidade nativa no startup

Motivo:

- o log de startup do app mostrou o ambiente do Streamlit Cloud usando
  Python 3.14.6
- o processo chegou a subir dependencias e depois encerrou com
  `Segmentation fault` no wrapper de execucao
- o repositorio nao possuía pin de runtime, entao o deploy estava herdando a
  versao padrao mais nova do ambiente

Impacto esperado:

- reduzir risco de crash nativo no startup
- manter previsibilidade da combinacao `streamlit` + `pandas` + `numpy`
- deixar o deploy alinhado com o interpretador local moderno ja validado na
  maquina de trabalho

Aplicacao operacional:

- arquivos adicionados: `runtime.txt` e `.python-version`
- versao travada: `3.12.12`

---

## Incidente de `Segmentation fault` no Streamlit Cloud

Data:

- 2026-07-12

Achado:

- o erro observado no Streamlit Cloud nao apresentou traceback Python; o
  processo encerrou com `Segmentation fault` no wrapper de execucao do
  Streamlit
- a troca para Python 3.12 reduziu o risco de incompatibilidade com o runtime
  mais novo, mas nao eliminou o crash durante interacoes na UI
- os traces de startup mostraram que as consultas ao Supabase concluiam antes
  da queda
- no caso confirmado de `Criadores > Criador individual`, a tela carregou:
  - `v_dashboard_creator_weekly_activity`
  - `v_dashboard_creator_weekly_audience`
  - `posts`
- a queda ocorreu depois das queries e junto da fase de renderizacao, com
  avisos de `use_container_width`

Leitura tecnica:

- a falha mais provavel esta na renderizacao/serializacao nativa de
  componentes do Streamlit Cloud, especialmente `st.plotly_chart`,
  `st.dataframe` ou a combinacao deles com `streamlit`, `pyarrow`, `numpy`,
  `pandas`, `plotly` e Python 3.12
- nao ha evidencia de erro funcional nas views do Supabase ou na regra de
  negocio da pagina afetada
- enquanto a causa exata nao for isolada, componentes pesados devem ser
  evitados no caminho padrao das telas criticas

Mitigacao aplicada:

- remover cache do cliente Supabase para evitar reutilizacao de recurso de
  conexao entre reruns
- manter cache apenas nos dados retornados pelas queries
- desativar por padrao os graficos interativos do criador individual
- substituir a tabela de videos do criador por renderizacao HTML simples
- substituir o dataframe tecnico do expander por texto markdown

Resultado observado:

- apos a mitigacao da pagina de criador individual, o app deixou de cair no
  teste manual informado pelo usuario

Fechamento operacional:

- em 2026-07-15, os componentes foram reintroduzidos por lotes controlados no
  Streamlit Cloud
- a sequencia validada pelo usuario incluiu:
  - `Criadores > Criador individual`: graficos Plotly, tabela de videos e
    tabela tecnica
  - `Data Quality`: tabelas tecnicas do detalhamento
  - `Cadastro Fenabrave`: preview inicial, itens `1..8`, itens `11..22` e
    tabela persistida
  - `Cadastro de Criadores`: tabelas de correspondencia, criador cadastrado e
    detalhe tecnico da revisao
  - graficos Plotly remanescentes do dashboard
- os dataframes e graficos passaram a usar `width="stretch"` nos pontos
  estabilizados, substituindo o uso anterior de `use_container_width=True`
- nao houve nova queda reportada durante os testes manuais apos a reintroducao
  completa desses componentes

Decisao atual:

- considerar o incidente estabilizado do ponto de vista operacional
- manter a remocao de cache do cliente Supabase
- manter `width="stretch"` para novos `st.dataframe` e `st.plotly_chart`
- reintroduzir qualquer componente pesado futuro em lote pequeno, com traces
  temporarios quando houver risco de regressao

Pendencias:

- seguir monitorando novos deploys do Streamlit Cloud, especialmente quando
  houver mudanca indireta de `streamlit`, `pyarrow`, `numpy`, `pandas` ou
  `plotly`
- avaliar pinagem conservadora de dependencias apenas se houver nova regressao
  nativa ou diferenca relevante entre ambiente local e Cloud

---

## Taxonomia piloto v1 para classificacao de videos do Sprint 6

Data:

- 2026-07-16

Decisao:

- definir uma taxonomia piloto v1 compacta para a fase metodologica de
  classificacao de videos do Sprint 6
- tratar esta taxonomia como fonte de verdade temporaria em documento + CSV,
  separada da taxonomia operacional atual de `public.sub_niches`
- usar `powertrain` como niche para temas de motorizacao:
  - `eletrico`
  - `hibrido`
  - `combustao`
  - `flex`
  - `diesel`
- manter `eletrica_eletronica` restrita a bateria `12v`, sensores, modulos,
  chicote e falhas eletricas/eletronicas em geral
- proibir `motor` e `cambio` como `sub_niche` solto
- exigir termos contextualizados quando o assunto mudar de natureza:
  - `manutencao_motor`
  - `diagnostico_motor`
  - `manutencao_cambio`
  - `diagnostico_cambio`
- manter `scanner_obd2` dentro de `diagnostico`, mesmo quando o problema final
  estiver ligado a motor ou cambio

Motivo:

- a classificacao metodologica do piloto precisa evitar termos ambiguos que
  mudam de significado entre manutencao e diagnostico
- `eletrico` e `hibrido` descrevem melhor tipo de motorizacao do que um tema
  generico de eletrica/eletronica
- misturar motorizacao com eletrica ou diagnostico com manutencao reduziria a
  concordancia humano vs IA e enfraqueceria o `agreement_score`
- separar a taxonomia piloto do banco atual permite calibrar a metodologia
  antes de assumir compromisso estrutural de schema ou seed

Impacto esperado:

- classificacao inicial mais consistente na rodada de `10` videos
- menor risco de colisao semantica entre niches e subnichos
- melhor base para `confidence_score`, `agreement_score` e revisao de
  taxonomia apos a rodada piloto
- base pronta para discussao futura de persistencia operacional sem acoplar o
  piloto ao banco cedo demais

Aplicacao operacional:

- documento canonico: `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.md`
- CSV canonico: `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.csv`
- escopo atual: fase metodologica do piloto de `10` videos
- fora do escopo atual:
  - seed de banco
  - migration SQL
  - integracao automatica com `public.sub_niches`

---

## Dimensoes complementares piloto v1 para classificacao de videos

Data:

- 2026-07-16

Decisao:

- fechar um contrato piloto para as dimensoes complementares:
  - `vehicle_brand`
  - `vehicle_model`
  - `vehicle_year_or_generation`
  - `automotive_system`
  - `component`
  - `problem`
- tratar essas dimensoes como camada complementar da taxonomia principal, sem
  permitir que redefinam `niche` ou `sub_niche`
- manter `vehicle_brand` e `vehicle_model` como campos semifechados,
  preenchidos apenas quando houver evidencia explicita ou muito forte
- tratar `vehicle_year_or_generation` como campo hibrido:
  - ano exato quando existir
  - descritores controlados quando nao houver ano
- fechar `automotive_system`, `component` e `problem` com vocabulario piloto
  controlado
- manter a regra de que `scanner_obd2` continua em diagnostico, usando sistema,
  componente e problema apenas como refinamento tecnico
- usar `automotive_system = powertrain` quando o video for claramente sobre
  motorizacao eletrica, hibrida, flex, diesel ou combustao

Motivo:

- sem esse contrato, a rodada humano vs IA dos `10` videos ficaria sujeita a
  interpretacoes diferentes mesmo com a taxonomia principal fechada
- as dimensoes complementares precisam enriquecer a leitura tecnica sem
  competir com o tema principal do video
- preencher marca, modelo ou componente por inferencia fraca aumentaria ruido,
  derrubaria o `agreement_score` e tornaria a revisao metodologica menos
  confiavel

Impacto esperado:

- classificacao manual e automatica mais consistente no piloto
- menor risco de contradicao entre `sub_niche`, sistema, componente e problema
- melhor base para revisar divergencias humano vs IA sem misturar tema e
  detalhe tecnico

Aplicacao operacional:

- documento canonico:
  `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.md`
- CSV canonico:
  `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.csv`
- escopo atual:
  - fase metodologica do piloto de `10` videos
  - uso conjunto com a taxonomia piloto v1
- fora do escopo atual:
  - tabela definitiva de marcas
  - tabela definitiva de modelos
  - cruzamento automatico com Fenabrave, Carros na Web ou `public.sub_niches`

---

## Amostra piloto v1 de 10 videos para a rodada humano vs IA

Data:

- 2026-07-16

Decisao:

- fechar uma amostra metodologica inicial de `10` videos para a rodada humano
  vs IA do Sprint 6
- dividir a amostra em:
  - `5` videos `short`
  - `5` videos `long`
- excluir creators cujo `entity_name` ou `username` combine com:
  - `Acelerados`
  - `ACF`
  - `Tcar`
- evitar creators muito pequenos e videos com baixo engajamento usando os
  filtros:
  - `followers >= 150000`
  - `engagement_pct >= 2.0`
- manter uma mistura intencional de:
  - casos claros
  - titulos ambiguos
  - temas de `powertrain`
  - temas de `manutencao`
  - temas de `mercado` ou `compra_venda`

Motivo:

- a rodada inicial precisa calibrar o metodo, nao medir distribuicao
  estatistica da base
- excluir `Acelerados`, `ACF` e `Tcar` reduz vies editorial e respeita a
  restricao definida para o piloto
- exigir porte e engajamento minimos reduz o risco de montar o piloto com
  videos fracos demais para classificacao util

Impacto esperado:

- base inicial mais estavel para classificacao humana e automatica
- menor risco de ruído metodologico por creators muito pequenos ou pouco
  engajados
- melhor variedade de sinais para testar a taxonomia piloto

Aplicacao operacional:

- documento canonico:
  `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.md`
- CSV canonico:
  `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv`
- fonte usada para shortlist:
  - `posts`
  - `creators`
- fora do escopo atual:
  - classificacao humana
  - prompt final da IA
  - execucao da rodada automatica

---

## Workbook unico em Excel para execucao humana do piloto do Sprint 6

Data:

- 2026-07-16

Decisao:

- publicar o workbook operacional recomendado em
  `docs/external_data/34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsx`
- manter uma copia `.xlsm` para compatibilidade com evolucao futura
- consolidar no arquivo:
  - taxonomias do piloto
  - lista canonica dos `10` videos primarios
  - campos de classificacao humana
- manter uma aba visivel de taxonomias e uma aba visivel de execucao humana
- usar dropdowns com valores canonicos sugeridos, mas sem bloquear digitacao
  livre
- manter `sub_niche` apto a receber mais de um valor no mesmo campo usando
  separacao canonica por `, `

Motivo:

- a rodada humana fica mais simples e auditavel em um unico arquivo de Excel
- manter taxonomia e amostra no mesmo artefato reduz ambiguidade operacional
- dropdowns aceleram o preenchimento sem impedir excecoes justificadas durante
  a calibracao
- permitir mais de um `sub_niche` no mesmo campo preserva casos hibridos do
  piloto sem multiplicar colunas ou forcar categoria ad hoc

Contrato atual:

- o workbook operacional complementa, mas nao substitui, os artefatos canonicos
  `31`, `32` e `33`
- `video_url` deve ser publicado com link clicavel para YouTube a partir de
  `post_id`
- a aba oculta `listas` e a fonte dos dropdowns
- o arquivo e gerado por
  `scripts/external_data/build_pilot_human_workbook.ps1`

Observacao de implementacao:

- o gerador atual publica `.xlsx` e `.xlsm` com dropdowns editaveis e
  preenchimento manual livre
- o `.xlsx` e a versao recomendada para uso nesta v1
- nesta v1, a multisselecao de `sub_niche` fica operacional por preenchimento
  manual no mesmo campo, usando separacao por `, `
- o gerador valida antes da entrega as contagens de taxonomias, videos,
  hyperlinks e dropdowns

---

## Baseline humano do piloto em duas entregas

Data:

- 2026-07-16

Decisao:

- produzir duas classificacoes humanas para os mesmos `10` videos
- Entrega 1:
  - identificador `entrega_1_descricao`
  - usar a descricao como evidencia semantica principal
  - nao assistir ao video nem usar audio ou transcricao
- Entrega 2:
  - identificador `entrega_2_90s_iniciais`
  - classificar novamente usando os `90s` iniciais do video
  - usar o video completo quando a duracao for menor que `90s`
- preservar as duas entregas separadamente, sem sobrescrever resultados

Motivo:

- o desenho segue o padrao ja previsto nos docs `29` e `30`: classificacao
  inicial com texto e reclassificacao com evidencia parcial do conteudo
- comparar as duas entregas permite medir em quais dimensoes a descricao e
  suficiente e onde os primeiros `90s` mudam a leitura
- a separacao reduz perda de rastreabilidade e permite calibrar a futura
  decisao de transcrever ou nao um video

Pre-requisito operacional:

- adquirir e incluir a descricao dos `10` videos antes da Entrega 1
- o CSV canonico do doc `33` ainda nao contem `description`

Impacto esperado:

- baseline humano com duas camadas de evidencia
- comparacao por campo entre descricao e conteudo inicial
- melhor criterio para avaliar a classificacao inicial da IA e a
  reclassificacao apos transcricao parcial

---

## Evolucao da taxonomia apos o primeiro teste humano

Data:

- 2026-07-20

Decisao:

- preservar a taxonomia v1 e os workbooks preenchidos como evidencia da rodada
- nao alterar retroativamente os CSVs `31` e `32`
- preparar uma taxonomia v2 com arvore de apresentacao legivel e dimensoes
  canonicas separadas
- exigir no desenho futuro compatibilidade entre:
  - niche, sub_niche e sub_sub_niche
  - rota taxonomica, sistema, componente e problema
  - marca, modelo e geracao
- validar resultados da IA antes da persistencia e enviar combinacoes invalidas
  para revisao humana

Decisao ainda aberta:

- nao liberar multi-niche irrestrito nesta fase
- avaliar primeiro a separacao entre `automotive_domain` e `activity_type`
- testar `niche_primary` e `niche_secondary` controlados apenas se a separacao
  de eixos nao resolver os casos hibridos

Motivo:

- o teste mostrou sobreposicao semantica entre `diagnostico` e `manutencao`
- dropdowns independentes permitem combinacoes tecnicamente impossiveis
- uma arvore amigavel ao humano nao precisa reproduzir diretamente as colunas
  do modelo de dados
- travas apenas na interface nao protegem persistencia por API ou IA

Referencia:

- `docs/external_data/35_ACHADOS_POS_TESTE_TAXONOMIA_CLASSIFICACAO_V1.md`

---

## Avaliacao GPT equivalente ao baseline humano em duas etapas

Data:

- 2026-07-20

Decisao:

- executar o agente GPT sobre os mesmos `10` videos em duas etapas
- Etapa 1: descricao sem audio, video ou transcricao
- Etapa 2: mesma descricao acrescida da transcricao dos `90s` iniciais
- nao fornecer classificacoes ou observacoes humanas ao agente classificador
- persistir as duas saidas GPT antes de iniciar comparacoes
- manter termos novos em `taxonomy_gaps` e inconsistencias em
  `validation_issues`, sem alterar silenciosamente a taxonomia v1

Motivo:

- o isolamento evita vazamento do baseline humano para o agente
- a equivalencia de evidencias permite medir o valor marginal dos `90s`
- preservar lacunas separadamente evita confundir capacidade do modelo com
  insuficiencia da taxonomia

Pre-requisitos:

- corrigir os metadados truncados por virgulas no CSV da amostra
- capturar e versionar descricoes
- obter transcricoes limitadas ao intervalo contratado
- fechar o JSON Schema da resposta

Referencia:

- `docs/external_data/36_RESULTADO_BASELINE_HUMANO_E_CONTRATO_AVALIACAO_GPT_V1.md`
- `docs/external_data/36_BASELINE_HUMANO_DUAS_ETAPAS_V1.csv`

---

## Round exploratorio GPT 5.5 para evolucao da taxonomia

Data:

- 2026-07-20

Decisao:

- executar uma rodada exploratoria com `gpt-5.5` disponivel no ambiente de
  trabalho para evoluir a taxonomia antes de automatizar o processo
- tratar o resultado como insumo de desenho taxonomico e fine tuning
  conceitual, nao como benchmark final do modelo de API
- nao chamar `gpt-5.4-mini` por API nesta etapa
- nao chamar modelo de transcricao nesta etapa
- nao criar tabelas, migrations, workers ou scripts robustos para esta rodada
- persistir apenas CSV e documento analitico simples

Motivo:

- a prioridade imediata e entender lacunas de taxonomia, sobreposicoes entre
  campos e travas futuras
- automatizar cedo demais aumentaria custo de manutencao antes de estabilizar
  a estrutura conceitual
- a etapa de `90s` ainda nao tem transcricao textual versionada, entao deve ser
  registrada como ausencia de evidencia em vez de ser simulada

Contrato:

- `gpt-5.5` nesta rodada significa avaliacao exploratoria no ambiente atual
- as saidas devem registrar `taxonomy_gaps` e `validation_issues`
- o baseline humano nao deve ser usado como entrada do classificador
- a comparacao futura com `gpt-5.4-mini` continua separada e devera usar
  entradas versionadas, schema fechado e transcricoes dos `90s`

Referencia:

- `docs/external_data/37_ANALISE_GPT55_EXPLORATORIA_TAXONOMIA_R1.md`
- `docs/external_data/37_RESULTADO_GPT55_EXPLORATORIO_TAXONOMIA_R1.csv`

---

## Transcricao local com Whisper para o round taxonomico

Data:

- 2026-07-20

Decisao:

- gerar as transcricoes dos primeiros `90s` dos `10` videos do piloto com
  Whisper local, sem configurar `OPENAI_API_KEY`
- usar `yt-dlp` para obter audio dos links do YouTube derivados de `post_id`
- usar `faster-whisper` com modelo `small`, idioma `pt` e `compute_type=int8`
- manter audio, video e cache de modelo fora do Git
- tratar o resultado como insumo de calibracao taxonomica, nao como benchmark
  final do fluxo automatizado futuro

Motivo:

- o objetivo imediato e evoluir a taxonomia e a estrutura dos campos
- configurar chave OpenAI neste laptop nao e necessario para esta rodada
- o lote de `10` videos e pequeno o suficiente para transcricao local

Resultado:

- `10/10` videos transcritos com sucesso
- videos menores que `90s` foram transcritos na duracao completa
- a qualidade deve ser revisada em nomes proprios e termos automotivos antes de
  usar o transcript como evidencia definitiva

Referencia:

- `docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.md`
- `docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.csv`

---

## Comparacao exploratoria humano vs GPT 5.5 com transcripts de 90s

Data:

- 2026-07-21

Decisao:

- usar os transcripts locais dos `90s` para executar uma nova classificacao GPT
  5.5 exploratoria
- comparar essa saida contra a `entrega_2_90s_iniciais` humana
- publicar apenas concordancia exata por campo e divergencias brutas
- manter `agreement_score` fora desta rodada ate os pesos serem definidos

Motivo:

- a comparacao por `90s` mede melhor o ganho de evidencia em relacao ao titulo
  isolado
- divergencias em `niche`, `sub_niche` e `component` ajudam a direcionar a
  Taxonomia v2
- entidades explicitas podem ser avaliadas separadamente dos problemas de
  modelagem taxonomica

Resultado:

- maior concordancia em `vehicle_brand`, `vehicle_model` e `audience_intent`
- maiores divergencias em `sub_niche`, `automotive_system` e
  `vehicle_year_or_generation`
- conclusao: a v2 deve separar dominio, atividade, arvore de topicos,
  entidades e compatibilidade tecnica

Referencia:

- `docs/external_data/39_RESULTADO_GPT55_90S_WHISPER_R1.csv`
- `docs/external_data/39_COMPARACAO_HUMANO_GPT55_90S_R1.md`

---

## Taxonomia V2 por eixos separados para videos automotivos

Data:

- 2026-07-21

Decisao:

- documentar a Taxonomia V2 como proposta metodologica antes de alterar CSVs,
  workbook, banco ou pipeline
- testar a classificacao por eixos separados:
  - `automotive_domain`
  - `activity_type`
  - `topic_path`
  - `vehicle_entity`
  - `technical_context`
- usar `topic_path` como arvore de navegacao humana
- manter `content_type` e `audience_intent` separados do tema automotivo
- registrar lacunas em `taxonomy_gaps`, sem promover termos livres a canonicos
  automaticamente

Motivo:

- o piloto mostrou que `niche` unico nao representa bem videos que misturam
  `review`, `mercado`, `powertrain`, manutencao, diagnostico e custo
- entidades explicitas tiveram boa concordancia, mas `sub_niche`,
  `automotive_system` e ano/geracao ainda precisam de estrutura melhor
- a separacao de eixos reduz a necessidade de multi-niche livre e prepara
  matrizes de compatibilidade tecnica

Contrato:

- `fora_escopo` e rota valida para videos nao automotivos ou apenas
  incidentalmente ligados a carros
- `eletrico`, `hibrido`, `flex` e `diesel` pertencem a `powertrain`
- `motor` e `cambio` nao devem ser usados como rotulos soltos
- marca, modelo e ano devem ser tratados como entidades, nao como subnichos
- a v1 permanece preservada como evidencia historica

Referencia:

- `docs/external_data/40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md`

---

## Enriquecimento da Taxonomia V2 por fontes editoriais externas

Data:

- 2026-07-23

Decisao:

- usar fontes editoriais automotivas externas como insumo controlado para
  enriquecer a Taxonomia V2, desde que a promocao de termos preserve os eixos
  separados da taxonomia
- promover `revisao_10k` como rota de `topic_path` para checklist periodico
  amplo de manutencao preventiva
- manter itens como oleo, filtros, freios, suspensao, arrefecimento e bateria
  como rotas especificas ou contexto tecnico compativel, nao como nichos
  soltos
- adicionar sintomas gerais de diagnostico, como `luzes_painel`,
  `perda_potencia`, `vibracao` e `direcao_puxando`
- manter `barulho` apenas como sinonimo/sinal textual; `ruido` permanece o
  codigo canonico para sintoma sonoro
- manter banco, workbook e pipeline inalterados nesta etapa

Motivo:

- a fonte Moura evidencia que conteudos de manutencao preventiva podem ser
  checklists amplos por quilometragem, e nao apenas videos sobre um unico
  componente
- sem uma rota de checklist periodico, classificadores humanos ou IA tenderiam
  a escolher um componente arbitrario como tema principal
- a matriz tecnica precisa validar relacoes entre rota, sistema, componente e
  problema para evitar combinacoes incoerentes

Referencia:

- `docs/external_data/47_ANALISE_FONTE_MOURA_MANUTENCAO_PREVENTIVA_TAXONOMIA_V2.md`
- `docs/external_data/42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv`
- `docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`

---

## Technical context repetivel na Taxonomia V2

Data:

- 2026-07-23

Decisao:

- adotar `technical_context[]` como estrutura repetivel para contexto tecnico
  na Taxonomia V2
- materializar a estrutura nesta fase como CSV filho em formato longo, com uma
  linha por combinacao coerente de `automotive_system`, `component` e
  `problem`
- manter os campos agregados `automotive_system`, `component` e `problem` como
  resumo legado/compatibilidade em artefatos consolidados
- nao usar `;` para juntar multiplos sistemas, componentes ou problemas em uma
  unica celula do contexto tecnico detalhado
- validar cada linha contra a matriz tecnica `43`, marcando
  `needs_review` quando a combinacao ainda nao estiver coberta
- manter banco, workbook e pipeline inalterados nesta etapa

Motivo:

- videos reais de manutencao pesada, dicas multiplas e procedimentos de oficina
  frequentemente citam varios sistemas e componentes no mesmo trecho
- campos unicos forcam perda de informacao ou combinacoes ambiguas
- uma estrutura repetivel permite validar linha a linha sem reabrir multi-nicho
  livre ou categorias soltas

Referencia:

- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.md`
- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.csv`

---

## Limite de profundidade da arvore taxonomica V2

Data:

- 2026-07-23

Decisao:

- manter `topic_path` como arvore curta, estavel e navegavel
- nao promover automaticamente todo termo tecnico novo para subnicho ou novo
  nivel de `topic_path`
- usar `technical_context[]` para registrar profundidade tecnica, como pecas,
  sintomas, procedimentos, insumos e problemas citados no video
- tratar termos tecnicos novos primeiro como vocabulario controlado,
  sinonimos, evidencias ou `taxonomy_gaps`
- promover um termo para `topic_path` apenas quando ele representar um tipo
  recorrente de conteudo e melhorar a navegacao/classificacao humana

Motivo:

- o aprendizado incremental pode gerar profundidade praticamente ilimitada se
  cada novo termo virar subnicho
- uma arvore infinita prejudicaria consistencia, validacao e comparacao humano
  vs IA
- separar arvore navegavel de contexto tecnico preserva riqueza semantica sem
  transformar a taxonomia em lista de pecas e sintomas

Exemplo:

- `topic_path = manutencao_reparo > reparo_corretivo > troca_motor`
- `technical_context[]` registra `motor_conjunto`, `oleo_motor`,
  `oleo_vencido`, `borra`, `carbonizacao`, `desgaste`, `folga_axial` e
  `retifica_motor` quando houver evidencia

Referencia:

- `docs/external_data/40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md`
- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.md`

---

## Catalogo Carros na Web para homogeneizacao de veiculos

Data:

- 2026-07-23

Decisao:

- persistir no Supabase os CSVs de catalogo do Carros na Web para fabricantes,
  modelos e anos/modelo
- usar o catalogo como base de homogeneizacao de `vehicle_brand`,
  `vehicle_model` e `vehicle_year_or_generation` extraidos de descricao e
  transcricao
- excluir `aplicacoes_modelo_ano_test.csv` da carga, pois o arquivo pertence a
  exploracao de ficha tecnica
- preservar `params` bruto como JSON e extrair campos canonicos para fabricante,
  modelo e ano/modelo
- expor uma view inicial `v_carrosnaweb_vehicle_catalog` para matching de
  entidades de veiculo

Motivo:

- a rodada de classificacao mostrou que identificar veiculo, marca e modelo e
  fundamental quando a informacao esta disponivel
- entidades extraidas por humanos ou GPT precisam ser comparadas a uma base
  controlada para evitar grafias divergentes e combinacoes impossiveis
- ficha tecnica continua fora de escopo; o valor imediato esta no catalogo de
  nomes e anos

Referencia:

- `docs/external_data/51_CARROSNAWEB_CATALOGO_SUPABASE_HOMOGENEIZACAO_VEICULOS.md`
- `sql/ddl/tables/021_create_market_carrosnaweb_catalog.sql`
- `sql/ddl/views/022_create_v_carrosnaweb_vehicle_catalog.sql`
- `sql/ddl/tests/010_test_carrosnaweb_catalog.sql`

Status operacional:

- DDL e script de ingestao foram preparados
- `dry-run` validou `127` fabricantes, `1458` modelos e `8914` anos/modelo
- carga REST foi concluida no Supabase com `127` fabricantes, `1458` modelos e
  `8914` anos/modelo
- `v_carrosnaweb_vehicle_catalog` foi validada com buscas por `BYD Dolphin`,
  `Renault Kwid`, `Changan Uni-T` e `Hyundai HB20`

---

## Taxonomia V2: consolidacao apos amostra aleatoria

Data:

- 2026-07-23

Decisao:

- manter a arvore `topic_path` estavel apos a rodada aleatoria de `10` videos
- nao criar `audience_context`, `estagio_produto` ou `engineering_context`
  nesta fase
- manter motos e duas rodas como fora de escopo
- usar ano/modelo apenas quando a informacao estiver disponivel e confiavel,
  seguindo o contrato ja estabelecido nas bases externas
- tratar prototipo, flagra, camuflado, pista de teste, calibracao e
  tropicalizacao como evidencia textual, observacao ou `taxonomy_gaps`, sem
  nova categoria canonica agora
- classificar pista/calibracao/tropicalizacao como
  `review_teste > avaliacao_tecnica` quando o conteudo for automotivo e houver
  evidencia clara
- permitir no contexto tecnico de review apenas os novos termos aprovados:
  `cambio_automatico`, `cambio_cvt`, `tracao_traseira`, `tracao_dianteira` e
  `tracao_integral`

Motivo:

- a rodada mostrou que a Taxonomia V2 ja cobre bem os temas principais
- as lacunas observadas nao justificam abrir novos eixos estruturais agora
- a prioridade e preservar uma arvore curta e estavel, usando contexto tecnico
  e `taxonomy_gaps` para aprendizado incremental

Referencia:

- `docs/external_data/57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.md`
- `docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`

---

## Harness GPT e persistencia Supabase da Taxonomia Video V2

Data:

- 2026-07-23

Decisao:

- criar uma camada operacional no Supabase para armazenar a Taxonomia Video V2
  e os resultados de classificacao por GPT
- tratar o harness como contrato de entrada/saida, nao como metodo de ingestao
  nem script de coleta
- versionar a skill do classificador como prompt/contrato usado na chamada da
  API GPT, referenciado por `prompt_contract_version`
- exigir saida JSON estruturada e imputavel diretamente nas tabelas de
  classificacao
- persistir `technical_context[]` como tabela filha repetivel, com uma linha
  por combinacao coerente de sistema, componente e problema
- persistir entidades de veiculo em tabela filha separada, preservando valor
  bruto e preparando match futuro contra Carros na Web/Fenabrave
- usar `gpt-5-nano` para classificacao por titulo/metadados e tambem para
  classificacao por transcricao dos `90s`
- usar `gpt-4o-mini-transcribe` apenas para gerar a transcricao textual
- nao aplicar fallback automatico para `gpt-5.4-mini` nesta fase
- manter fora desta entrega ingestao, execucao Google Cloud, worker, dashboard
  e alteracao do workbook

Motivo:

- a Taxonomia V2 ja e a estrutura mais completa disponivel no projeto
- as proximas rodadas precisam de um contrato forte para impedir classificacao
  por achismo e permitir gravacao direta no banco
- separar resultado principal, contexto tecnico e entidades de veiculo evita
  campos concatenados e facilita validacao referencial
- a tarefa de classificacao deve ser validada primeiro com o modelo de menor
  custo operacional antes de considerar modelos maiores
- a decisao de fallback deve depender de resultado empirico depois da
  implementacao, nao de premissa antecipada

Referencia:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_OUTPUT_SCHEMA_V2.json`
- `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
- `sql/ddl/views/023_create_v_video_classification_latest.sql`
- `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

---

## Execucao do classificador GPT em VPS via cron

Data:

- 2026-07-23

Decisao:

- usar uma VPS Hostinger como ambiente inicial de execucao agendada do
  classificador GPT da Taxonomia V2
- acessar a VPS pelo VS Code com Remote SSH durante o desenvolvimento
- usar Ubuntu 24.04 LTS como ambiente operacional observado
- usar `/opt/social-media-analytics` como diretorio base no servidor
- subir apenas o script e arquivos auxiliares necessarios, sem clonar o
  repositorio completo nesta fase
- agendar a rotina futura com `cron`
- manter credenciais, chaves SSH, `.env`, IP publico e usuario real fora do Git

Motivo:

- a etapa atual precisa validar a execucao operacional do classificador antes
  de criar automacao mais pesada
- deploy minimo reduz superficie de erro e evita levar o repositorio completo
  para a VPS antes de necessidade real
- cron e suficiente para o primeiro ciclo de classificacao controlada
- a decisao pode ser reaberta depois para GitHub Actions, Docker ou Google
  Cloud se a rotina amadurecer

Referencia:

- `docs/external_data/59_VPS_CRON_CLASSIFICADOR_GPT_V2_RUNBOOK.md`

---

## Classificacao operacional combinada com titulo e transcricao

Data:

- 2026-07-24

Decisao:

- usar uma unica chamada operacional por video no estagio `transcript_90s`
  quando a transcricao dos primeiros `90s` estiver disponivel
- gerar a transcricao operacional por GPT Transcribe, inicialmente com
  `gpt-4o-mini-transcribe`
- enviar na mesma chamada titulo, metadados confiaveis, descricao quando existir
  e transcricao textual dos `90s`
- manter `title_metadata` apenas para diagnostico, calibracao, comparacao
  metodologica de sinal fraco ou triagem preliminar
- nao criar um novo estagio ou schema nesta fase; o contrato atual de
  `transcript_90s` ja comporta a chamada combinada

Motivo:

- a classificacao apenas por titulo mostrou utilidade para testar guardrails,
  mas tambem evidencia limitada em titulos vagos ou sensacionalistas
- a chamada combinada tende a reduzir inferencia ruim sem duplicar toda a
  entrada fixa de taxonomia, matriz de compatibilidade e prompt
- o custo por chamada aumenta em relacao ao titulo puro por incluir transcript,
  mas deve ser menor que executar duas classificacoes completas e persistir dois
  resultados operacionais equivalentes

Aplicacao operacional:

- `gpt-5-nano` permanece como modelo classificador definido para esta fase
- `gpt-4o-mini-transcribe` permanece apenas como modelo de geracao do texto da
  transcricao
- Whisper/local fica preservado apenas como evidencia historica das rodadas
  exploratorias, nao como padrao operacional
- rodadas de comparacao em duas etapas continuam permitidas, desde que marcadas
  com `round_id` experimental e nao confundidas com resultado operacional final

Referencia:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`

---

## Faster Whisper operacional e qualidade textual persistida

Data:

- 2026-07-24

Decisao:

- substituir a decisao anterior de GPT Transcribe por `faster-whisper` local
  como fonte operacional atual dos primeiros `90s`
- usar modelo `small`, CPU e `compute_type=int8` na VPS
- executar uma unica chamada `gpt-5-nano` por video para avaliar a qualidade
  textual e classificar com titulo, metadados e transcript
- manter `description = null`, pois `public.posts` nao possui descricao
- persistir score, status, issues, impacto e necessidade de retranscricao em
  `video_classification_results`
- nao persistir o transcript completo no Supabase; manter somente evidencias
  curtas e metadados sanitizados com hash e tamanho
- manter o cron desativado ate a validacao manual do Batch 1

Motivo:

- a VPS nao tem restricao de tempo equivalente a um job curto em cloud
- a transcricao local elimina custo e dependencia de API para speech-to-text
- o doc `39` mostrou ganho relevante em entidades e contexto tecnico com os
  primeiros `90s`
- qualidade textual precisa ser consultavel para revisao e retranscricao sem
  armazenar todo o transcript

Referencia:

- `docs/external_data/39_COMPARACAO_HUMANO_GPT55_90S_R1.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/59_VPS_CRON_CLASSIFICADOR_GPT_V2_RUNBOOK.md`

---

## Avaliacao da qualidade textual da transcricao pelo classificador

Data:

- 2026-07-24

Decisao:

- o classificador GPT deve avaliar se o `transcript_90s` recebido e textual e
  semanticamente utilizavel para sustentar a classificacao
- essa avaliacao mede qualidade da evidencia textual, nao qualidade do audio
  original
- a nota de qualidade do transcript deve influenciar `confidence_score`,
  `needs_human_review` e `validation_issues`
- nao salvar transcript completo no Supabase apenas para auditoria; preservar
  evidencias curtas nos campos ja contratados:
  - `evidence_summary`
  - `technical_contexts[].evidence_text`
  - `vehicle_entities[].evidence_text`
- implementar o bloco obrigatorio `transcript_quality` no schema `r2` e
  persistir seus campos consultaveis no banco, conforme a decisao Faster
  Whisper imediatamente anterior

Motivo:

- a transcricao pode conter erros em nomes de marcas, modelos, versoes e termos
  automotivos
- mesmo sem ouvir o audio, o GPT consegue identificar sinais textuais de baixa
  qualidade, como frases truncadas, incoerencia, transcript vazio ou termos
  degradados
- guardar uma nota de qualidade da evidencia ajuda a decidir quando revisar,
  retranscrever ou reduzir confianca sem armazenar todo o transcript no banco

Referencia:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`

---

## PO Token para aquisicao de audio na VPS

Data:

- 2026-07-29

Decisao:

- testar PO Token Provider plugin do `yt-dlp` apenas em execucao manual na VPS
- expor no classificador flags genericas para repassar ao `yt-dlp`:
  - `--yt-dlp-plugin-dir`
  - `--yt-dlp-extractor-args`
- manter cookies, tokens, user-agent e plugins instalados localmente fora do Git
- manter `--transcripts-csv` como fallback validado para classificacao quando a
  aquisicao de audio falhar
- nao ativar cron enquanto a aquisicao de audio por PO Token nao for validada
  em lote pequeno
- nao adotar Tor, proxy residencial ou conta Google descartavel como padrao
  operacional nesta fase

Motivo:

- a VPS foi recusada pelo YouTube com `Sign in to confirm you're not a bot`
  mesmo usando cookies e user-agent aceitos localmente
- a documentacao atual do `yt-dlp` indica exigencia crescente de PO Tokens em
  alguns clients, formatos e subtitles
- a falha esta na aquisicao de audio, nao no contrato do classificador GPT, que
  ja foi validado com CSV de transcript

Referencia:

- `docs/external_data/60_PO_TOKEN_YTDLP_TRANSCRICAO_VPS_R1.md`
- `docs/external_data/59_VPS_CRON_CLASSIFICADOR_GPT_V2_RUNBOOK.md`

---

## Matching deterministico de veiculo por script

Data:

- 2026-07-29

Decisao:

- nao enviar a lista Carros na Web ao GPT para classificacao de veiculos
- nao fazer uma segunda chamada GPT para normalizar marca/modelo/ano
- executar no harness um matcher deterministico por script usando `title`,
  `description` e `transcript_90s`
- usar `catalog_row_id` apenas quando marca/modelo/ano estiverem sustentados
  pela evidencia textual
- adicionar `catalog_model_id` para casos em que o modelo e identificado, mas o
  ano nao aparece
- permitir preencher a montadora canonica pelo catalogo quando o modelo citado
  for unico; exemplo: `Kwid` resolve para `Renault/Kwid`

Motivo:

- o identificador de veiculo e essencial para pesquisa de mercado, como buscas
  por todos os videos que falam de um lancamento ou modelo
- passar o catalogo inteiro ao GPT aumenta tokens e ainda assim nao garante
  homogeneizacao consistente
- escolher um ano artificial quando o texto nao cita ano criaria falsa precisao
- o script consegue resolver marca/modelo de forma auditavel, barata e
  reproduzivel, preservando a chamada GPT unica para a classificacao semantica

Referencia:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `scripts/video_classification/README.md`

---

## Reforco do harness V2: tema principal vs contexto tecnico

Data:

- 2026-07-30

Decisao:

- manter `topic_path` como representacao da proposta principal do video
- guardar sistemas, componentes, atributos e problemas citados em
  `technical_contexts[]`, sem deixar que um detalhe tecnico substitua o tema
  editorial principal
- em videos de `review_teste` ou `mercado_produto`, usar `powertrain` como
  principal apenas quando o video for explicitamente sobre motorizacao,
  autonomia, recarga, consumo, cambio ou tecnologia de propulsao
- reforcar exemplos do Batch 1 na skill:
  `aXbFPJMVGKw`, `CjFrJg6VCjc`, `z55GnDEg7_U`, `RTZHxSE2t5M` e
  `6qSnrkGd70I`
- restringir o matcher deterministico para modelos que tambem sao palavras
  comuns; `100`, `tipo`, `bora` e `link` exigem marca explicita e proxima no
  texto antes de virar `vehicle_entity`

Motivo:

- a rodada Batch 1 com `transcript_90s` mostrou melhora clara em titulos
  ambiguos, mas tambem mostrou que detalhes como `motor 1.5 turbo` podem roubar
  o `topic_path` de um review
- a mesma rodada revelou falsos positivos do catalogo Carros na Web em termos
  comuns da fala, como `100%`, `bora para o canal`, `tipo SKD` e `link na
  descricao`
- a solucao preserva uma unica chamada GPT por video e usa regras
  deterministicas para evitar inferencia ruim

Referencia:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`
- `scripts/video_classification/README.md`

---

## WARP isolado em container para aquisicao de audio

Data:

- 2026-07-29

Decisao:

- nao usar `warp-cli connect` global no host da VPS como caminho operacional
- usar Cloudflare WARP apenas isolado em container/proxy quando o IP da VPS for
  recusado pelo YouTube
- expor o proxy local somente em `127.0.0.1`, inicialmente
  `socks5://127.0.0.1:11080`
- repassar esse proxy ao `yt-dlp` via flag do classificador
  `--yt-dlp-proxy`
- manter o PO Token Provider `bgutil` em `127.0.0.1:4416` como complemento ao
  proxy WARP

Motivo:

- `warp-cli connect` global alterou DNS/rota da VPS e colocou o acesso SSH em
  risco
- o modo proxy do client WARP Linux aceitou comandos, mas nao abriu listener
  local
- o container `warproxy` expôs SOCKS5 local e o trace via proxy retornou
  `warp=on`
- `yt-dlp` com `--proxy socks5://127.0.0.1:11080` passou da barreira
  `Sign in to confirm you're not a bot` no teste manual
- a rodada Batch 1 mostrou falhas `ffmpeg exited with code -11`; o classificador
  passou a ter fallback estavel que baixa a fonte sem conversao pelo `yt-dlp`,
  preferindo audio leve `139/140` antes do progressivo `18`, e corta/converte
  com `ffmpeg` em etapa separada

Referencia:

- `docs/external_data/59_VPS_CRON_CLASSIFICADOR_GPT_V2_RUNBOOK.md`
- `docs/external_data/60_PO_TOKEN_YTDLP_TRANSCRICAO_VPS_R1.md`

---

## Default VPS para audio YouTube: android_vr sem bgutil

Data:

- 2026-07-31

Decisao:

- usar `youtube:player-client=android_vr` como default operacional do
  `yt-dlp` na VPS
- manter WARP apenas via proxy local `socks5://127.0.0.1:11080`
- manter cookies e user-agent/referer, mas sem `mweb` e sem
  `youtubepot-bgutilhttp` como caminho padrao
- deixar `mweb + bgutil` como fallback experimental, porque o provider retornou
  `HTTP 500` em `POST /get_pot`

Motivo:

- `mweb + bgutil` ficou preso em tentativas de PO Token, chegando a `300s` no
  download direto e mais `300s` no fallback
- `android_vr` eliminou o gargalo: nos quatro pendentes do Batch 2, fallback de
  audio levou `1.45s..4.27s`, Whisper `9.64s..22.40s` e OpenAI `46.60s..70.16s`
- o Batch 2 fechou `10/10` no Supabase com `transcript_quality_status = usable`
  para todos os videos

Referencia:

- `docs/external_data/59_VPS_CRON_CLASSIFICADOR_GPT_V2_RUNBOOK.md`
- `docs/external_data/60_PO_TOKEN_YTDLP_TRANSCRICAO_VPS_R1.md`
