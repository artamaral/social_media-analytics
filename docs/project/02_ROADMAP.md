# ROADMAP

## Regra de execucao por sprint

O roadmap define as prioridades gerais, mas a execucao deve seguir o sprint ativo
registrado em `07_SPRINT_AGENDA.md`.

Regra obrigatoria:

- apenas atividades relacionadas ao sprint ativo devem ser executadas;
- se uma demanda nao tiver relacao clara com o sprint ativo, o GPT deve
  perguntar antes de prosseguir;
- sem confirmacao explicita do usuario, demandas fora do sprint ativo devem ser
  registradas como ideias ou sugestoes, nao executadas.

O projeto esta organizado em 3 frentes principais:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

Ha tambem um bloco transversal para documentacao, validacoes operacionais e decisoes que afetam mais de uma frente.

## Frente 1. Dados social media

### Prioridade alta - funcionamento e confiabilidade

- [x] Implementar monitoramento executivo no Streamlit para acompanhar integridade da coleta, evidencia de processamento e sinais operacionais dos 2 workers.
- [ ] Consolidar a analise de confiabilidade operacional dos posts atualizados com base no monitoramento do Streamlit e nas evidencias do banco.
- [x] Confirmar que posts nao estavam sendo atualizados e que o novo codigo esta rodando.
- [x] Implementar e operar a view `Posts mortos e validacao humana` no Streamlit, tratando os `13` posts detectados e zerando as pendencias humanas.
- [ ] Confirmar se toda a camada analitica ja exclui corretamente posts `unavailable` fora dos contextos de auditoria.
- [ ] Monitorar conclusao do cleanup temporario do guardrail: `warm_8_30d` e `old_30d_plus` ate `3` checagens; `new_0_3d` e `recent_4_7d` ate `2` checagens.
- [ ] Analisar a regra de `next_check` como principal open point operacional. O monitoramento atual mostra atraso e risco, mas ainda nao diz se a regra e suficiente ou nao para a base em crescimento.
- [ ] Verificar se a prioridade embutida em `next_check` esta coerente com banda, idade do post, cobertura minima esperada e urgencia operacional. A avaliacao nao deve olhar apenas tempo e contagem bruta, porque esses numeros tendem a crescer junto com a base.
- [ ] Executar teste pendente descrito em `08_QUEUE_CAPACITY_TEST.md` e `09_QUEUE_SLICING_AND_RESCHEDULING.md`.
- [ ] Garantir que scraper percorre todos creators.
- [ ] Validar integridade de `post_metrics_history`.
- [ ] Criar query de auditoria de coleta.
- [ ] Detectar gaps de coleta por post.
- [ ] Validar atualizacao de `collected_at`.

### Prioridade estrategica - modelo de priorizacao

- [ ] Criar abordagem analitica simples para `hot now`, baseada em `velocity_6h`, `previous_velocity` e `acceleration`, usando views SQL para dashboard.

### Itens concluidos nesta frente

- [x] Validacao da mudanca para FIFO dentro da banda ao inves de score. Usar arquivo `11_QUEUE_FIFO_VALIDATION_2026-05-08.md` como referencia e deixar rodar por dois dias. Validacao em 2026-05-10.
- [x] Validar impacto FinOps e custos apos aumento do lote do worker para 40 posts por execucao. Resultado observado apos alguns dias em producao: nao houve aumento relevante de custos no Cloud Run.
- [x] Open point: reavaliar se o refill global da `v_post_update_queue_batch` deve continuar assim ou migrar para cascata por banda. Hoje, cotas nao usadas por uma banda vao para um pool global ordenado por antiguidade, e nao automaticamente para a proxima banda mais alta.
- [x] Tratar videos indisponiveis na YouTube API para evitar posts presos na fila. Implementado com tabela de falhas, RPC, view de dashboard e exclusao de `unavailable` da fila ativa.
- [x] Implementar no Streamlit os blocos executivos de `Integridade da coleta`, `Evidencia de processamento`, `Sinais operacionais`, `Monitoramento de posts sem checagem` e `Posts mortos e validacao humana`.
- [x] Implementar limpeza temporaria do backlog de guardrail. Rotina em execucao controlada via Windows Scheduler; proximo passo e monitorar conclusao.
- [x] Pausar promocao do score hibrido `v2` para a fila ativa. O `v2` fica em segundo plano e a prioridade analitica passa a ser `hot now` temporal.

## Frente 2. Dados de fontes externas

### Prioridade alta - novos blocos estruturados

- [ ] Consolidar o fluxo operacional do Carros na Web em camadas persistidas: `fabricantes -> modelos -> fichas -> parser -> atualizacao incremental`, usando a etapa por ano como subetapa tecnica quando o catalogo exigir.
- [ ] Validar a etapa intermediaria do Carros na Web: gerar e revisar `anos_modelo_validos.csv` a partir de `anos_modelo.csv`, classificando cada URL de ano como `valid_year_page`, `no_ficha_links`, `site_error`, `http_error` ou `unexpected_page`.
- [ ] Se houver paginas de ano validas, retomar a descoberta de fichas tecnicas a partir de `anos_modelo_validos.csv`, mantendo discovery por links reais do catalogo, sem enumeracao sequencial de IDs e sem bypass de captcha.
- [ ] Manter Carros na Web fora de schema definitivo no Supabase ate provar captura etica, repetivel e com cobertura suficiente. Usar `docs/external_data/27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md` como referencia obrigatoria.

### Prioridade media - definicao de escopo

- [x] Delimitar Fenabrave e SENATRAN/RENAVAM como fontes estruturadas prioritarias no Supabase, deixando as demais fontes apenas como contexto textual.
- [ ] Consolidar a modelagem final de Fenabrave, decidindo se a fase inicial por segmento permanece temporariamente suficiente ou se a frente deve expandir para marca, modelo, runs de ingestao e validacoes persistidas.
- [ ] Definir a modelagem final de SENATRAN/RENAVAM, incluindo dataset real, granularidade util, rotulagem correta de frota e tabela normalizada final.

### Prioridade operacional - rotina de fonte

- [ ] Open point: avaliar como gerar lembrete futuro e/ou incluir em uma agenda a rotina mensal da Fenabrave descrita em `00_OFFLINE_OPERATIONS_CALENDAR.md`.

### Itens concluidos nesta frente

- [x] Implementar a modelagem inicial de Fenabrave com cadastro de fontes, arquivos rastreaveis, tabela normalizada por segmento e view analitica inicial para dashboard.

## Frente 3. Dashboard

### Base tecnica

- [x] Preparar camada SQL para dashboard online sob demanda no Supabase.
- [x] Definir stack e deploy do dashboard online: Streamlit Community Cloud + Supabase.
- [x] Confirmar conta Streamlit Community Cloud linkada ao GitHub.
- [x] Validar conexao online do Streamlit com Supabase via secrets.

### MVP do app

- [ ] Dashboard inicial.
- [ ] Ranking de crescimento semanal.
- [ ] Criar ranking "quente agora" com velocidade e aceleracao temporal do score, separado da logica operacional da fila.
- [ ] Seguir plano de execucao do dashboard em `docs/dashboard/29_STREAMLIT_DASHBOARD_EXECUTION_PLAN.md`.
- [ ] Implementar MVP online com overview, creators e crescimento semanal.
- [ ] Exibir status de qualidade dos dados antes dos rankings.
- [x] Garantir que o app use Supabase sob demanda sem expor service role key.
- [ ] Criar app Streamlit inicial consumindo as views do Supabase.
- [ ] Aplicar tema visual do dashboard com fundo em escala de cinza, sidebar escura, cards contrastados e pictos.
- [ ] Aplicar views de Data Quality do dashboard: guardrail legado e posts mortos/validados.

### Direcao desta frente

- [x] Confirmar que o dashboard e uma ferramenta interna de estudo de mercado, nao um produto SaaS publico.
- [x] Definir Streamlit como solucao atual por simplicidade, custo zero e velocidade analitica.
- [x] Definir direcao visual inicial: dashboard escuro em escala de cinza com acento coral e pictos.

## Bloco transversal

### Documentacao no GitHub

- [x] Documentacao do SQL: incluir tabelas com extensao correta e deletar versao antiga.
- [x] Documentacao do SQL: entender e documentar triggers do banco.
- [x] Incluir scripts de trigger no GitHub e verificar local correto.
- [x] Checar documentacao existente para inclusao de novos dados e gerar arquivo `.md`.
- [x] Criar README principal.

### Leitura de prioridade geral

- a frente `Dados social media` continua sendo a base operacional principal
- a frente `Dados de fontes externas` expande a profundidade analitica do projeto automotivo
- a frente `Dashboard` organiza a camada de consumo e visualizacao
