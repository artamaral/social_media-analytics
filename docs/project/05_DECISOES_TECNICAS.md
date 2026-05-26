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

## Cadastro de criadores via Streamlit com RPC controlada

Data:

- 2026-05-26

Decisao:

- usar a tela `Cadastro > Criadores` como caminho preferencial para cadastrar
  nova entity e novo creator
- manter o fluxo de governanca baseado em `public.entity_intake`
- publicar uma linha de intake por vez por RPC controlada, usando
  `public.publish_entity_intake_entry(p_intake_id)`
- cadastrar o creator por RPC separada, usando
  `public.create_creator_from_resolved_entity(...)`
- nao usar SQL livre, `service role key` ou escrita direta em
  `public.entities` / `public.entity_sub_niches` na UI

Validacao:

- caso validado: `Autoesporte`
- `creator_id`: `55`
- `entity_id`: `52`
- `channel_id`: `UCc6jv88ebCrDVxJQUjZfGT`
- subnichos vinculados: `compra`, `noticia`, `review`, `teste`
- resultado: cadastro validado com subnicho e visivel na view de criadores do
  Streamlit

Pendente:

- verificar nos proximos dias se o worker passou a incorporar o novo criador no
  ciclo normal de discovery/coleta.

Motivo:

- reduzir erro manual de cadastro
- manter auditabilidade do intake
- evitar que a operacao dependa do Supabase SQL Editor para o fluxo comum
- preservar a separacao entre entity, subnicho e creator

---

## Worker separado de discovery inicial para novos creators

Data:

- 2026-05-26

Decisao:

- criar um worker separado para discovery inicial de posts quando um novo
  creator do YouTube for cadastrado
- manter o `youtube_main_scraper` recorrente como fluxo principal por
  lote/cursor
- nao alterar `pipeline_state` nem o cursor `youtube_cursor` no worker de
  onboarding
- nao gravar snapshots em `creator_metrics_history` nesse worker
- nao atualizar followers ou metricas correntes de canal nesse worker
- inserir apenas posts descobertos, deixando o trigger `add_to_queue()` enviar
  os posts para `post_update_queue`
- deixar a `v_post_update_queue_batch` priorizar os posts novos pelo guardrail
  normal, pois eles entram com `total_checagens = 0`

Motivo:

- reduzir a espera entre cadastro de creator e descoberta inicial de videos
- evitar mexer no scraper principal que ja esta operacional
- evitar complexidade em views e regras de fila
- preservar separacao clara entre discovery inicial, snapshots de creator e
  snapshots historicos de posts

Diretriz:

- a chamada externa deve enviar apenas `creator_id`
- o worker deve buscar `channel_id` no banco
- a trava simples de idempotencia deve ser existencia de posts em
  `public.posts` para o `creator_id`
- a URL deve exigir autenticacao por token ou mecanismo equivalente
- a integracao com Streamlit nao precisa de documento separado agora; o fluxo
  fica no processo de intake e o contrato do worker no spec social media

Documento de referencia:

- `docs/social_media/34_CREATOR_ONBOARDING_DISCOVERY_WORKER_SPEC.md`

---

## Data Quality do dashboard com dois KPIs operacionais

Data:

- 2026-05-19

Decisao:

- o bloco de Data Quality do dashboard deve ter exatamente dois KPIs principais
- KPI 1: legado guardrail, usando `v_dashboard_guardrail_coverage_status`
- KPI 2: posts mortos e validacao humana, usando `v_dashboard_dead_post_validation_status`
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

Complemento:

- `Data Quality` deve ficar restrito a KPI e monitoramento
- a acao humana sobre casos concretos nao deve acontecer dentro da pagina de
  `Data Quality`
- a pagina operacional recomendada para esse fluxo passa a ser
  `Sanitizacao Operacional`
- o primeiro caso de uso dessa pagina e a revisao manual de itens de
  `v_dashboard_unavailable_video_review`

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

## Monitoramento operacional do worker horario por fluxo e risco de cobertura

Data:

- 2026-05-21

Decisao:

- o bloco de sinais operacionais do worker horario nao deve usar
  `fila_itens_prontos` como KPI principal
- o bloco de sinais operacionais do worker horario nao deve usar
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

- leitura mais fiel da capacidade real do worker horario
- melhor capacidade de avaliar se o bucket atual esta dimensionado
- menor duplicacao de KPI entre fluxo operacional e posts mortos

---

## Revisao de `next_check` orientada por sinais operacionais

Data:

- 2026-05-21

Decisao:

- abrir revisao de prioridade alta sobre a regra de geracao de `next_check`
- nao alterar a funcao ainda sem analisar a distribuicao por banda, idade do
  post e cobertura minima

Contexto:

- os sinais operacionais do dashboard passaram a mostrar concentracao relevante
  em faixas de atraso maiores do que a janela desejada
- observacao atual dos sinais:
  - `Ate 1h = 48`
  - `Ate 6h = 199`
  - `Ate 24h = 430`
- esses numeros sugerem que o agendamento atual merece reavaliacao, mas ainda
  nao fecham sozinhos a regra ideal

Motivo:

- o problema nao e apenas atraso pontual; e preciso entender se a funcao de
  `next_check` esta calibrada para a rotacao real da fila
- uma mudanca precipitada pode piorar cobertura ou deslocar o backlog para uma
  faixa errada
- a leitura precisa continuar conectada ao guardrail, ao tamanho do bucket e a
  idade dos posts

Diretriz:

- tratar essa revisao como prioridade alta na `main`
- manter os sinais operacionais como base de analise antes de mexer em
  `calculate_next_check(...)`
- documentar qualquer nova regra de agendamento com os criterios usados para
  separar `Ate 1h`, `Ate 6h` e `Ate 24h`

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

## PDF Fenabrave via Streamlit apenas como apoio operacional

Data:

- 2026-05-21

Decisao:

- considerar viavel o carregamento do PDF mensal da Fenabrave via Streamlit
  apenas como apoio operacional
- nao tratar o Streamlit como destino final de armazenamento do arquivo
- manter o bucket privado `market-source-files` como armazenamento oficial

Contexto:

- a rotina mensal da Fenabrave continua manual nesta fase
- o mockup da view `Cadastro Fenabrave` mostrou que o upload na UI pode ajudar
  a conferencia do arquivo e o preenchimento inicial dos metadados
- ao mesmo tempo, o processo documentado exige preservacao do PDF, rastreio por
  `storage_path` e protecao contra exposicao de credenciais privilegiadas

Motivo:

- melhorar a ergonomia operacional sem quebrar a seguranca
- permitir avaliacao futura de upload guiado no app
- preservar o papel do Storage privado e dos metadados em
  `market_source_files`

Diretriz:

- o upload pelo app, se implementado, deve usar fluxo seguro
- o app nao deve expor `SUPABASE_SERVICE_ROLE_KEY`
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

Contexto:

- followers de creator sao metricas dinamicas, assim como views, likes e comments dos posts
- a tabela `creators` ja possui o campo `followers`, mas ele representa apenas o estado atual
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

## Filtros temporais com limite superior exclusivo

Data:

- 2026-05-25

Decisao:

- todo filtro sobre campo `timestamp` deve usar limite superior exclusivo
- nao usar `timestamp_col <= data_final` quando `data_final` representa apenas
  uma data sem horario
- para janelas fechadas de calendario, usar `timestamp_col >= inicio` e
  `timestamp_col < fim + intervalo`
- para comparacoes por dia/semana em SQL, quando a regra for de calendario, usar
  `timestamp_col::date` ou calcular `period_end_exclusive`

Contexto:

- a tabela de videos da semana no Streamlit deixou de listar posts publicados no
  domingo depois de `00:00:00`
- o bloco semanal estava correto porque a view usava `post_date::date`
- a tabela estava incorreta porque filtrava `post_date <= week_end`, e
  `week_end` era interpretado como `domingo 00:00:00`

Motivo:

- evitar perda silenciosa de registros no ultimo dia do periodo
- manter consistencia entre cards, tabelas, graficos e queries SQL
- reduzir risco de bugs quando GPT/Codex gerar filtros de periodo

Padrao obrigatorio:

```sql
-- Para timestamp:
where event_at >= period_start
  and event_at < period_end + interval '1 day'

-- Para campo convertido para calendario:
where event_at::date between period_start::date and period_end::date
```

Padrao em Pandas/Streamlit:

```python
mask = (df["event_at"] >= period_start) & (
    df["event_at"] < (period_end + pd.Timedelta(days=1))
)
```

Diretriz:

- sempre explicitar se o campo e `date` ou `timestamp`
- qualquer nova view, tabela do dashboard, filtro de semana, filtro mensal ou
  query gerada por GPT deve seguir esta regra
- se houver comparacao entre bloco agregado e tabela detalhada, ambos devem usar
  exatamente a mesma janela temporal

Documentos relacionados:

- `docs/dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md`
- `docs/dashboard/33_CREATOR_VIEW_STREAMLIT_SPEC.md`
- `docs/dashboard/34_CREATOR_WEEKLY_TIMESERIES_CONTRACT.md`
