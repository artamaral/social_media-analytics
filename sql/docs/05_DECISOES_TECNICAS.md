# 🧠 DECISÕES TÉCNICAS

---

## 📌 Estrutura de dados

### Uso de histórico (post_metrics_history)

Motivo:
- Permitir análise temporal
- Calcular crescimento real

---

## 📌 Estratégia de pipeline

- Pipeline A → novos posts
- Pipeline B → atualização de métricas

Motivo:
- Redução de custo
- Escalabilidade

---

## 📌 Classificação de vídeo

- Regra: <= 270s → short
- > 270s → long

Motivo:
- Padronização

---

## 📌 Prioridade de sistema

1. Pipeline funcionando
2. Qualidade dos dados
3. Analytics

Motivo:
- Evitar decisões com dados ruins
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
- pendente de aplicacao/validacao em producao
- pendente de validacao FinOps e custos

Validacao obrigatoria:

- medir custo diario do Cloud Run
- medir duracao media por execucao
- medir uso de quota da YouTube Data API
- medir volume de inserts em `post_metrics_history`
- medir impacto no Supabase
- calcular custo por snapshot antes de manter a mudanca como definitiva

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
- `v_dashboard_data_quality_status`

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
