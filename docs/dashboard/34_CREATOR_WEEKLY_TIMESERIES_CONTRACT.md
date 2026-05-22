# Creator Weekly Timeseries Contract

Data: 2026-05-22

## Objetivo

Definir o contrato SQL da serie temporal semanal para a view de criador
individual no Streamlit.

Este documento existe para separar claramente:

- o que ja e entregue por `public.v_dashboard_creator_summary`
- o que continua sendo leitura editorial de `public.posts`
- o que precisa virar nova view semanal para sustentar crescimento e
  encolhimento no tempo

## Decisao

Para a view `Criador individual`, a serie temporal nao deve ser diaria nem
mensal.

Diretriz adotada:

- usar comparacao semanal
- trabalhar com semanas fechadas
- medir crescimento e encolhimento semana contra semana
- manter o calculo no banco, nao no Streamlit

Motivo:

- diario gera ruido demais para leitura executiva
- mensal alonga demais a resposta e esconde inflexoes recentes
- semanal conversa com a diretriz ja existente de crescimento `7d`

## Camadas de dados

### 1. Resumo do criador

Fonte:

- `public.v_dashboard_creator_summary`

Papel:

- alimentar KPIs totais do criador
- alimentar identificacao, status e painel lateral

### 2. Leitura editorial

Fonte:

- `public.posts`

Papel:

- alimentar a tabela de top videos
- manter titulo, data, tipo e metricas do video

### 3. Serie temporal semanal

Fonte nova:

- `public.v_dashboard_creator_weekly_timeseries`

Papel:

- alimentar o grafico temporal da view `Criador individual`
- mostrar crescimento ou encolhimento por semana
- sustentar comparacoes sem depender de agregacao local no Streamlit

## Contrato proposto

Nome recomendado:

- `public.v_dashboard_creator_weekly_timeseries`

Colunas minimas:

| Campo | Tipo logico | Descricao |
|---|---|---|
| `creator_id` | inteiro | id do criador |
| `entity_id` | inteiro | id da entidade |
| `entity_name` | texto | nome exibido do criador |
| `platform` | texto | plataforma do criador |
| `week_start` | data | inicio da semana consolidada |
| `week_end` | data | ultimo dia da semana consolidada |
| `week_label` | texto | rotulo pronto para exibicao no app |
| `views_week_end` | inteiro | estoque de views observado no fim da semana |
| `views_delta_vs_prev_week` | inteiro | delta de views contra a semana anterior |
| `views_growth_pct_vs_prev_week` | numerico | crescimento percentual de views contra a semana anterior |
| `likes_week_end` | inteiro | estoque de likes observado no fim da semana |
| `likes_delta_vs_prev_week` | inteiro | delta de likes contra a semana anterior |
| `comments_week_end` | inteiro | estoque de comentarios observado no fim da semana |
| `comments_delta_vs_prev_week` | inteiro | delta de comentarios contra a semana anterior |
| `active_posts_in_week` | inteiro | quantidade de posts com snapshot util na semana |

Colunas desejaveis:

| Campo | Motivo |
|---|---|
| `top_post_id_in_week` | facilitar drill-down editorial |
| `top_post_title_in_week` | dar contexto narrativo ao pico semanal |
| `top_post_views_delta_in_week` | identificar o principal motor da semana |
| `week_status` | facilitar leitura visual de alta, queda ou estabilidade |

## Base de calculo

Fonte primaria:

- `public.post_metrics_history`

Justificativa:

- crescimento e encolhimento real moram nos snapshots historicos
- `public.posts` guarda o estado mais recente e metadados do video
- `public.posts.post_date` ajuda no contexto editorial, mas nao substitui o
  historico de coleta

Regras de desenho:

- consolidar por `creator_id`
- derivar semana a partir de `collected_at`
- usar o snapshot mais recente de cada post dentro da semana para evitar dupla
  contagem interna
- comparar cada semana com a semana imediatamente anterior do mesmo criador

## Como o Supabase gera os dados semanais

Modelo de geracao:

- a serie semanal nao depende de job separado no fim da semana
- a serie nasce de uma `view` SQL consultada sob demanda no Supabase
- essa `view` le `public.post_metrics_history` no momento da consulta
- conforme novos snapshots entram no banco, as semanas fechadas passam a refletir
  automaticamente o estado mais recente consolidado

Fluxo real de incorporacao:

1. os workers continuam inserindo snapshots em `public.post_metrics_history`
2. a view semanal agrupa esses snapshots por semana e por `creator_id`
3. para cada post em cada semana, a view usa o ultimo snapshot util daquela
   semana
4. depois agrega os posts por criador
5. por fim calcula delta e percentual contra a semana anterior do mesmo criador

Implicacao importante:

- nao existe rotina manual de "fechar a semana" no Streamlit
- o fechamento da semana e logico, definido pela propria query
- assim que a semana acaba, ela passa a ser elegivel para aparecer na view

## Regra obrigatoria de semana completa

Diretriz:

- o dashboard deve mostrar e calcular apenas semanas completas

Definicao adotada:

- semana de segunda a domingo
- `week_start` = segunda-feira `00:00:00`
- `week_end` = domingo da mesma semana

Regra SQL:

- a view deve excluir a semana corrente ainda aberta
- apenas semanas com `week_end < data_atual` podem aparecer

Leitura pratica:

- se hoje ainda estamos na semana de `19/05/2026` a `25/05/2026`, essa semana
  nao entra no grafico
- a ultima semana visivel sera a semana fechada imediatamente anterior

Motivo:

- evitar comparacao injusta entre semana parcial e semana completa
- impedir falsos sinais de queda no meio da semana
- manter consistencia visual e analitica

## Como mostrar o intervalo semanal

Recomendacao principal:

- mostrar intervalo completo no eixo ou tooltip
- formato recomendado: `18/05/2026-24/05/2026`

Alternativa curta:

- mostrar apenas `24/05/2026` como fim da semana

Decisao recomendada para o app:

- usar `week_label` como rotulo principal
- usar `week_end` como campo de apoio para ordenacao e tooltip

Motivo:

- o intervalo completo evita ambiguidade
- o usuario enxerga imediatamente o periodo consolidado
- o numero da semana isolado, como `semana 21`, nao e suficiente para leitura
  rapida

## Leitura no Streamlit

### Blocos da view `Criador individual`

1. KPIs totais

Fonte:

- `public.v_dashboard_creator_summary`

Campos atuais:

- `followers`
- `post_count`
- `total_views`
- `total_likes`
- `total_comments`
- `engagement_rate_pct`

Ja atendem:

- `Seguidores`
- `Rank de engajamento medio`
- `Total de videos`
- `Total de views`
- `Total de likes`
- `Total de comentarios`

2. Distribuicao de engajamento

Fonte:

- `public.v_dashboard_creator_summary`

Campos atuais:

- `total_likes`
- `total_comments`

Gap atual:

- sem `total_shares`
- sem `total_dislikes`

3. Serie temporal semanal

Fonte desejada:

- `public.v_dashboard_creator_weekly_timeseries`

Campos necessarios no Streamlit:

- `week_start`
- `week_end`
- `week_label`
- `views_delta_vs_prev_week`
- `views_growth_pct_vs_prev_week`
- `likes_delta_vs_prev_week`
- `comments_delta_vs_prev_week`
- `active_posts_in_week`

Situacao atual no Streamlit:

- o mockup ainda usa uma serie mensal local simulada
- a tela ainda nao consome uma view semanal real
- a tela ainda nao diferencia explicitamente semana completa de semana aberta

4. Top videos por views

Fonte:

- `public.posts`

Campos atuais:

- `title`
- `post_date`
- `views`
- `likes`
- `comments`
- `video_type`
- `post_id`

Gap atual:

- falta `post_url`

## Campos atuais vs campos faltantes no Streamlit

### Ja cobertos por contrato atual

| Bloco | Fonte atual | Campos atuais |
|---|---|---|
| KPIs totais do criador | `v_dashboard_creator_summary` | `followers`, `post_count`, `total_views`, `total_likes`, `total_comments`, `engagement_rate_pct` |
| Identificacao do criador | `v_dashboard_creator_summary` | `entity_name`, `platform`, `username`, `channel_id`, `is_active`, `latest_post_date`, `latest_collected_at` |
| Distribuicao de engajamento | `v_dashboard_creator_summary` | `total_likes`, `total_comments` |
| Top videos | `posts` | `title`, `post_date`, `views`, `likes`, `comments`, `video_type`, `post_id` |

### Faltantes para a nova documentacao

| Bloco | Campo faltante | Fonte desejada |
|---|---|---|
| Serie temporal semanal | `week_start` | `v_dashboard_creator_weekly_timeseries` |
| Serie temporal semanal | `week_end` | `v_dashboard_creator_weekly_timeseries` |
| Serie temporal semanal | `week_label` | `v_dashboard_creator_weekly_timeseries` |
| Serie temporal semanal | `views_delta_vs_prev_week` | `v_dashboard_creator_weekly_timeseries` |
| Serie temporal semanal | `views_growth_pct_vs_prev_week` | `v_dashboard_creator_weekly_timeseries` |
| Serie temporal semanal | `likes_delta_vs_prev_week` | `v_dashboard_creator_weekly_timeseries` |
| Serie temporal semanal | `comments_delta_vs_prev_week` | `v_dashboard_creator_weekly_timeseries` |
| Serie temporal semanal | `active_posts_in_week` | `v_dashboard_creator_weekly_timeseries` |
| Audiencia temporal | `followers_delta_7d` | evolucao futura da camada de creator |
| Audiencia temporal | `followers_latest_collected_at` | evolucao futura da camada de creator |
| Editorial | `post_url` | enrich ou contrato futuro sobre `posts` |
| Classificacao | `sub_niches_display` real | evolucao de `v_dashboard_creator_summary` |

## Passo a passo de implantacao

### Etapa 1. Validar o insumo historico

Objetivo:

- confirmar que `post_metrics_history` tem cobertura suficiente para leitura
  semanal

Checar:

- frequencia de `collected_at`
- quantidade de snapshots por post
- distribuicao de criadores com historico minimo utilizavel

### Etapa 2. Definir a logica semanal

Objetivo:

- fechar a regra sem ambiguidades antes da view

Decisoes:

- semana inicia em qual dia
- como consolidar um post com varios snapshots na mesma semana
- como tratar semanas sem observacao
- se `views_week_end` representa ultimo snapshot da semana ou soma agregada
- como excluir a semana corrente ainda aberta
- qual rotulo semanal o app deve exibir

Recomendacao:

- usar segunda a domingo como calendario semanal
- usar ultimo snapshot util de cada post na semana
- depois agregar por criador
- excluir da view qualquer semana ainda aberta
- gerar `week_label` pronto no SQL

### Etapa 3. Criar a view SQL

Objetivo:

- materializar o contrato `v_dashboard_creator_weekly_timeseries`

Entrega esperada:

- arquivo proprio em `sql/ddl/views/`
- `GRANT SELECT` para leitura do dashboard
- nomes de colunas estaveis para o app

### Etapa 4. Validar no Supabase

Objetivo:

- garantir que a view responde rapido e com semantica correta

Checks:

- um criador com varias semanas retorna sequencia coerente
- semanas com queda mostram delta negativo
- percentuais nao explodem com denominador zero
- criadores sem historico suficiente nao quebram a consulta
- a semana corrente nao aparece enquanto estiver incompleta
- o intervalo exibido bate com `week_start` e `week_end`

### Etapa 5. Ligar no Streamlit

Objetivo:

- substituir a serie temporal local simulada por leitura real

Mudancas no app:

- trocar a funcao mockada da serie mensal
- carregar a nova view filtrada por `creator_id`
- usar `week_label` no eixo x
- usar `week_end` para ordenacao cronologica e tooltip
- usar `views_delta_vs_prev_week` como serie principal
- usar `views_growth_pct_vs_prev_week` ou `likes_delta_vs_prev_week` como
  segunda leitura
- nunca montar semana localmente no app

### Etapa 6. Revisar texto e semantica visual

Objetivo:

- garantir que o grafico responde a pergunta certa

Texto recomendado:

- `Crescimento semanal`
- `Variacao de views por semana`
- `Semana contra semana`

Evitar:

- `Views mensais`
- `Evolucao mensal`
- `Historico diario`

## Criterio de pronto

Esta fase estara pronta quando:

- a spec da Creator View apontar para serie semanal real
- o contrato da nova view estiver documentado
- a view SQL existir
- o Streamlit estiver ligado na nova view
- o mock mensal local tiver sido removido
