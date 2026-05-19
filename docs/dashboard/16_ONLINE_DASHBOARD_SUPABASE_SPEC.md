# Dashboard analitico interno com Supabase e Streamlit

## Objetivo

Criar um sistema de visualizacao online para estudos de mercado automotivo, consumindo dados do Supabase sob demanda e sem copiar metricas para uma base paralela no MVP.

O dashboard, neste momento, nao tem objetivo de virar produto SaaS publico. Ele deve funcionar como uma bancada analitica interna para investigar creators, videos, crescimento, engajamento, nichos e qualidade da coleta.

## Principios

- O dashboard le dados agregados do Supabase em tempo de consulta.
- O app nunca expoe `SUPABASE_SERVICE_ROLE_KEY`.
- Toda consulta passa por views SQL, RPCs ou queries controladas.
- Toda analise visual deve exibir estado de qualidade dos dados antes dos rankings.
- O MVP prioriza estudo de mercado, exploracao analitica e confiabilidade dos dados antes de acabamento visual de produto.
- A evolucao esperada e aumentar fontes de dados e profundidade analitica, nao numero de acessos.

## Arquitetura recomendada

```text
Usuario
  -> Streamlit Community Cloud
  -> queries Python controladas
  -> Supabase views/RPCs
  -> tabelas analiticas e historico
```

## App online

Recomendacao para MVP:

- Streamlit Community Cloud
- Python
- Pandas para analises exploratorias
- Supabase Python client ou conexao Postgres read-only
- secrets gerenciados no proprio Streamlit Cloud
- cache de consultas com TTL curto para reduzir leituras repetidas

## Banco

Consumir preferencialmente:

- `v_dashboard_creator_summary`
- `v_dashboard_post_growth_7d`
- `v_dashboard_data_quality_status`
- `v_dashboard_unavailable_video_review`

Essas views deixam o dashboard simples e evitam repetir logica analitica no app.

Para estudos mais exploratorios, o Streamlit pode complementar as views com Pandas, desde que nao carregue historico bruto sem filtros de periodo.

## MVP de telas

### 1. Overview

Objetivo:

- mostrar se o sistema esta confiavel para analise
- resumir volume total de creators, posts, views e engajamento

Componentes:

- status de qualidade dos dados
- total de creators ativos
- total de posts monitorados
- total de views atuais
- media de engagement rate

### 2. Creators

Objetivo:

- comparar creators automotivos monitorados
- identificar quem merece acompanhamento comercial ou editorial

Componentes:

- ranking por views totais
- ranking por engagement rate
- posts monitorados por creator
- ultima coleta conhecida
- filtro por plataforma

### 3. Crescimento semanal

Objetivo:

- identificar videos com tracao recente
- separar volume absoluto de crescimento real

Componentes:

- ranking de delta de views em 7 dias
- crescimento percentual em 7 dias
- likes e comentarios incrementais
- link ou identificador do video
- creator associado

### 4. Qualidade operacional da fila

Objetivo:

- identificar videos que nao voltaram da YouTube API
- facilitar revisao humana sem depender de logs do Cloud Run
- evitar que posts indisponiveis fiquem presos no guardrail ou na fila normal

Componentes:

- tabela de `unavailable_candidate` e `unavailable`
- `post_id`
- `youtube_url` completa e clicavel
- `failure_count`
- `last_failure_reason`
- `first_failed_at` e `last_failed_at`
- `human_review_status`
- `human_review_notes`

View recomendada:

- `public.v_dashboard_unavailable_video_review`

Referencia tecnica:

- `docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`

## Consultas sob demanda

O MVP deve consultar o Supabase apenas quando:

- o usuario abre uma pagina
- altera filtros
- muda ordenacao ou periodo
- solicita refresh manual

Evitar:

- polling frequente sem necessidade
- carregar historico bruto sem filtros
- calcular crescimento linha a linha no app quando uma view SQL puder resolver
- consultas abertas sem limite de periodo

## Seguranca

Regras obrigatorias:

- nunca expor `SUPABASE_SERVICE_ROLE_KEY`
- usar uma chave/usuario de leitura quando possivel
- guardar credenciais apenas em Streamlit secrets
- criar grants especificos para views consumidas pelo dashboard
- aplicar filtros de periodo e limites nas consultas de historico

## Data quality antes de analytics

Antes de liberar rankings como sinal de negocio, validar:

- posts sem historico
- posts com `collected_at` nulo
- posts sem atualizacao nas ultimas 24h
- creators sem posts
- videos indisponiveis presos na fila de atualizacao

O dashboard deve exibir esses indicadores na tela inicial.

## Roadmap tecnico

### Fase 1 - Base analitica

- criar views SQL de consumo
- criar view de revisao de videos indisponiveis com URL completa
- criar indices para `post_metrics_history`
- validar data quality
- documentar contrato dos dados

### Fase 2 - App Streamlit MVP

- criar app Streamlit
- configurar secrets do Supabase
- implementar overview, creators e crescimento semanal
- publicar no Streamlit Community Cloud

### Fase 3 - Estudos avancados

- filtros por nicho e subnicho
- curvas temporais por creator
- deteccao de outliers
- comparativo entre creators
- exportacao CSV
- analises por fonte de dados adicional

## Stack recomendada

Escolha padrao:

- Streamlit Community Cloud
- Python
- Pandas
- Supabase Python client ou psycopg
- Plotly ou Altair para graficos

Motivo:

- deploy online simples e gratuito
- baixa complexidade de manutencao
- adequado para poucos acessos e muita exploracao analitica
- permite iterar rapidamente novas perguntas de mercado
- combina bem com SQL, Pandas e estudos automotivos por creator/video

## Alternativa futura

Se o dashboard deixar de ser ferramenta interna e passar a ser produto para terceiros, reavaliar:

- Next.js
- TypeScript
- Supabase JS
- Tailwind CSS
- Recharts ou Tremor

Essa alternativa deve ser tratada como evolucao de produto, nao como prioridade atual.

## Criterio de pronto do MVP

- app online acessivel por URL
- nenhum segredo exposto no codigo ou no navegador
- overview mostra qualidade dos dados
- ranking de creators funcionando
- ranking de crescimento semanal funcionando
- revisao de videos indisponiveis disponivel por view com URL clicavel
- queries respondem sem leitura excessiva do historico
- limitacao conhecida de frescor dos dados documentada
