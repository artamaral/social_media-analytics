# ROADMAP

## NON Negotiable - Parar tudo para fazer

- [x] Validacao da mudanca para FIFO dentro da banda ao inves de score. Usar arquivo `11_QUEUE_FIFO_VALIDATION_2026-05-08.md` como referencia e deixar rodar por dois dias. Validacao em 2026-05-10.
- [x] Validar impacto FinOps e custos apos aumento do lote do worker para 40 posts por execucao. Resultado observado apos alguns dias em producao: nao houve aumento relevante de custos no Cloud Run.
- [x] Open point: reavaliar se o refill global da `v_post_update_queue_batch` deve continuar assim ou migrar para cascata por banda. Hoje, cotas nao usadas por uma banda vao para um pool global ordenado por antiguidade, e nao automaticamente para a proxima banda mais alta.
- [ ] Avaliar score hibrido em modo analitico sem segundo Cloud Run. Usar simulacao `v2` apenas no banco e validar com SQL + Excel/Pandas antes de qualquer troca no modelo ativo.

## Finalizar documentacao no GitHub

- [x] Documentacao do SQL: incluir tabelas com extensao correta e deletar versao antiga.
- [x] Documentacao do SQL: entender e documentar triggers do banco.
- [x] Incluir scripts de trigger no GitHub e verificar local correto.
- [x] Checar documentacao existente para inclusao de novos dados e gerar arquivo `.md`.
- [x] Criar README principal.

## Prioridade alta - infra / funcionamento

- [ ] Avaliar e garantir que os posts estao sendo atualizados.
- [x] Confirmar que posts nao estavam sendo atualizados e que o novo codigo esta rodando.
- [ ] Executar teste pendente descrito em `08_QUEUE_CAPACITY_TEST.md` e `09_QUEUE_SLICING_AND_RESCHEDULING.md`.
- [ ] Garantir que scraper percorre todos creators.
- [ ] Validar integridade de `post_metrics_history`.
- [ ] Criar query de auditoria de coleta.

## Media - confiabilidade

- [ ] Detectar gaps de coleta por post.
- [ ] Validar atualizacao de `collected_at`.
- [x] Preparar camada SQL para dashboard online sob demanda no Supabase.
- [x] Definir stack e deploy do dashboard online: Streamlit Community Cloud + Supabase.

## Baixa - produto / insights

- [ ] Dashboard inicial.
- [ ] Ranking de crescimento semanal.
- [ ] Definir plano de dados externos automotivos com ingestao estruturada apenas de Fenabrave e SENATRAN/RENAVAM. Usar `22_EXTERNAL_MARKET_DATA_STUDY_PLAN.md` como referencia antes de criar tabelas definitivas no Supabase; demais fontes ficam apenas como contexto para textos e interpretacao.

## Atualizacao 2026-05-08 - Visualizacao online

- [ ] Implementar MVP online com overview, creators e crescimento semanal.
- [ ] Exibir status de qualidade dos dados antes dos rankings.
- [ ] Garantir que o app use Supabase sob demanda sem expor service role key.

## Atualizacao 2026-05-14 - Direcao do dashboard

- [x] Confirmar que o dashboard e uma ferramenta interna de estudo de mercado, nao um produto SaaS publico.
- [x] Definir Streamlit como solucao atual por simplicidade, custo zero e velocidade analitica.
- [ ] Criar app Streamlit inicial consumindo as views do Supabase.
