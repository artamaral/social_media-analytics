# ROADMAP

O projeto esta organizado em 3 frentes principais:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

Ha tambem um bloco transversal para documentacao, validacoes operacionais e decisoes que afetam mais de uma frente.

## Frente 1. Dados social media

### Prioridade alta - funcionamento e confiabilidade

- [ ] Avaliar e garantir que os posts estao sendo atualizados.
- [x] Confirmar que posts nao estavam sendo atualizados e que o novo codigo esta rodando.
- [ ] Auditar residual do cleanup temporario do guardrail antes de retomar o scheduler; restam `9` posts, sendo `4` ja listados como possiveis dead posts.
- [ ] Padronizar exclusao de posts confirmados como dead/unavailable nas views e metricas antes de considerar o guardrail limpo.
- [ ] Monitorar conclusao do cleanup temporario do guardrail: `warm_8_30d` e `old_30d_plus` ate `3` checagens; `new_0_3d` e `recent_4_7d` ate `2` checagens.
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
- [x] Implementar limpeza temporaria do backlog de guardrail. Rotina em execucao controlada via Windows Scheduler; proximo passo e monitorar conclusao.
- [x] Pausar promocao do score hibrido `v2` para a fila ativa. O `v2` fica em segundo plano e a prioridade analitica passa a ser `hot now` temporal.

## Frente 2. Dados de fontes externas

### Prioridade alta - novos blocos estruturados

- [ ] Planejar e iniciar a base Carros na Web para catalogo, modelos e ficha tecnica. Usar `27_CARROSNAWEB_VEHICLE_SPECS_INGESTION_PLAN.md` como referencia obrigatoria; manter discovery por links reais do catalogo, sem enumeracao sequencial de IDs, e com CSV/HTML bruto como MVP antes de criar schema definitivo no Supabase.

### Prioridade media - definicao de escopo

- [ ] Definir plano de dados externos automotivos com ingestao estruturada apenas de Fenabrave e SENATRAN/RENAVAM. Usar `22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md` como referencia antes de criar tabelas definitivas no Supabase; demais fontes ficam apenas como contexto para textos e interpretacao.

### Prioridade operacional - rotina de fonte

- [ ] Open point: avaliar como gerar lembrete futuro e/ou incluir em uma agenda a rotina mensal da Fenabrave descrita em `00_OFFLINE_OPERATIONS_CALENDAR.md`.

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
