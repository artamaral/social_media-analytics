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

## Status do discovery com dados existentes e open point de heartbeat

Data:

- 2026-06-20

Decisao:

- nao alterar o worker `youtube_main_scraper` neste momento
- ajustar a leitura do dashboard para usar `posts.created_at` como evidencia de
  resultado do discovery
- manter `creator_metrics_history` apenas como evidencia legada/auxiliar de
  snapshot de canal
- nao marcar o discovery como `nok` quando houver posts inseridos nas ultimas
  24 horas

Motivo:

- logs do Cloud Run confirmaram execucao bem-sucedida do worker, com `POST 200`,
  creators processados, `Upsert 200`, `Erros: 0` e cursor salvo
- a view antiga marcava `nok` porque dependia de `creator_metrics_history`,
  que nao representa a evidencia principal do fluxo atual de discovery
- `posts.created_at` comprova resultado de discovery quando posts novos entram
  no banco

Limite conhecido:

- sem heartbeat persistido pelo worker, o banco nao comprova uma execucao que
  rodou sem encontrar posts novos
- quando nao ha posts novos, a evidencia de execucao fica apenas nos logs do
  Cloud Run/Scheduler
- por isso, a leitura atual separa:
  - resultado observado no banco por `posts.created_at`
  - snapshot legado de canal por `creator_metrics_history`
  - execucao comprovada apenas fora do banco pelos logs

Open point futuro:

- implementar heartbeat operacional do `youtube_main_scraper`
- registrar `started_at`, `finished_at`, `processed_creators`,
  `inserted_or_updated_posts`, `errors` e `status`
- usar o heartbeat para diferenciar de forma confiavel:
  - worker rodou e nao encontrou posts novos
  - worker nao rodou
  - worker falhou antes de gerar resultado

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

## Runtime do Streamlit fixado em Python 3.12

Data:

- 2026-07-12

Decisao:

- fixar o runtime do deploy do Streamlit em `python-3.12.12` via
  `runtime.txt`
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

- arquivo adicionado: `runtime.txt`
- versao travada: `python-3.12.12`
