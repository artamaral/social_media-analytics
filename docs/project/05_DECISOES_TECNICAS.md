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
- consultar `v_dashboard_data_quality_status` antes de rankings
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
