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

### 3. Atividade semanal

Fonte nova:

- `public.v_dashboard_creator_weekly_activity`

Papel:

- alimentar o grafico temporal da view `Criador individual`
- mostrar crescimento ou encolhimento por semana
- sustentar comparacoes sem depender de agregacao local no Streamlit

## Contrato proposto

Nome recomendado para os cards semanais:

- `public.v_dashboard_creator_weekly_activity`

Observacao:

- `public.v_dashboard_creator_weekly_timeseries` existe como primeira leitura de
  snapshots semanais, mas nao deve alimentar os cards semanais principais porque
  `active_posts_in_week` mede posts com snapshot util na semana, nao videos novos
  publicados na semana

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
| `video_type` | texto | `long`, `short` ou `todos` |
| `videos_publicados` | numerico | videos novos publicados na semana |
| `views_novas` | numerico | nome legado; views atuais dos videos publicados na semana |
| `views_growth_pct_vs_prev_week` | numerico | crescimento percentual de views contra a semana anterior |
| `likes_novos` | numerico | nome legado; likes atuais dos videos publicados na semana |
| `comentarios_novos` | numerico | nome legado; comentarios atuais dos videos publicados na semana |
| `posts_com_snapshot_na_semana` | numerico | quantidade de posts publicados na semana com `collected_at` preenchido |
| `posts_sem_baseline_para_delta` | numerico | campo legado mantido por compatibilidade; usar `0` nesta view |

Semantica dos cards semanais:

- o card semanal mede a performance atual dos videos publicados naquela semana
- o card semanal responde: `como meu portfolio publicado nesta semana performa hoje?`
- os cards semanais devem consumir a linha do `video_type` selecionado no app:
  `todos`, `long` ou `short`
- `videos_publicados` deve ser calculado por `public.posts.post_date`
- `views_novas`, `likes_novos` e `comentarios_novos` devem somar os valores
  atuais de `public.posts` para todos os videos publicados na semana
- apesar do sufixo `_novas` no contrato, esses campos nao representam delta de
  snapshot; eles representam o estado atual do portfolio publicado naquela semana
- por usar estado atual de `public.posts`, os contadores dos cards nao devem
  ficar negativos
- alem da linha `video_type = 'todos'`, a view deve expor linhas por tipo de
  video para que o mesmo bloco semanal possa alternar entre `todos`, `long` e
  `short`
- o Streamlit nao deve criar uma tabela adicional para esse detalhamento; o
  bloco de cards e o grafico semanal devem mudar conforme o tipo selecionado
- o grafico de distribuicao de engajamento tambem deve respeitar o tipo de
  video selecionado, usando os totais filtrados de `public.posts`
- a tabela editorial de videos e as futuras views de detalhe por post ficam
  responsaveis por leituras de posts isolados

Colunas desejaveis:

| Campo | Motivo |
|---|---|
| `top_post_id_in_week` | facilitar drill-down editorial |
| `top_post_title_in_week` | dar contexto narrativo ao pico semanal |
| `top_post_views_delta_in_week` | identificar o principal motor da semana |
| `week_status` | facilitar leitura visual de alta, queda ou estabilidade |

## Base de calculo

Fonte primaria dos cards semanais:

- `public.posts`

Justificativa:

- os cards semanais precisam bater com a lista editorial de videos publicados na
  mesma semana
- `public.posts` guarda o estado atual do video e a data de publicacao
- `public.post_metrics_history` continua relevante para analises historicas de
  movimento por snapshot, mas nao deve alimentar os cards semanais desta view

Regras de desenho:

- consolidar por `creator_id`
- derivar semana a partir de `public.posts.post_date`
- somar todos os posts publicados entre `week_start` e `week_end`
- gerar linhas por `video_type` e uma linha agregada `video_type = 'todos'`
- comparar cada semana com a semana imediatamente anterior do mesmo criador e
  tipo usando a soma atual dos videos publicados em cada semana
- data de corte inicial do dashboard: `2026-05-04`
- o app nao deve exibir semanas anteriores a essa data nos cards e graficos
  semanais de criador
- o seletor de semana pode listar as semanas fechadas disponiveis a partir da
  data de corte
- essa data foi escolhida por combinar cobertura historica suficiente e volume
  relevante de publicacoes com metricas atuais; semanas anteriores podem
  permanecer disponiveis para auditoria SQL, mas nao para leitura executiva no
  dashboard
- na primeira versao, a comparacao usa a ultima semana completa observada do
  criador
- semanas sem observacao util nao geram linha propria nesta versao inicial

## Como o Supabase gera os dados semanais

Modelo de geracao:

- a serie semanal nao depende de job separado no fim da semana
- a serie nasce de uma `view` SQL consultada sob demanda no Supabase
- essa `view` le `public.posts` no momento da consulta
- conforme os workers atualizam `public.posts`, as semanas fechadas passam a
  refletir automaticamente o estado atual dos videos publicados em cada semana

Fluxo real de incorporacao:

1. os workers continuam atualizando `public.posts` com metricas atuais
2. a view semanal agrupa os posts por semana de publicacao e por `creator_id`
3. a semana e calculada com `DATE_TRUNC('week', post_date)`
4. semanas abertas sao excluidas da view executiva
5. a view soma `views`, `likes` e `comments` atuais dos posts publicados naquela
   semana
6. depois agrega os posts por criador e `video_type`
7. a linha `video_type = 'todos'` soma `long`, `short` e demais tipos existentes
8. por fim calcula percentual contra a semana anterior do mesmo criador e tipo

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
- a comparacao semanal e calculada apenas entre semanas completas que entraram
  na view

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

3. Atividade semanal do criador

Fonte desejada:

- `public.v_dashboard_creator_weekly_activity`

Campos necessarios no Streamlit:

- `week_start`
- `week_end`
- `week_label`
- `video_type`
- `videos_publicados`
- `views_novas`
- `views_growth_pct_vs_prev_week`
- `likes_novos`
- `comentarios_novos`
- `posts_com_snapshot_na_semana`
- `posts_sem_baseline_para_delta`

Situacao atual no Streamlit:

- a tela consome a view semanal real
- a tela diferencia semana fechada de semana aberta pela propria view SQL
- a tela nao calcula cards semanais localmente; ela consome a agregacao pronta
  de `public.v_dashboard_creator_weekly_activity`

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
| Distribuicao de engajamento | `v_dashboard_creator_summary` | `total_views * 1`, `total_likes * 10`, `total_comments * 20` |
| Top videos | `posts` | `title`, `post_date`, `views`, `likes`, `comments`, `video_type`, `post_id` |

### Faltantes para a nova documentacao

| Bloco | Campo faltante | Fonte desejada |
|---|---|---|
| Atividade semanal | `week_start` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `week_end` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `week_label` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `video_type` | `v_dashboard_creator_weekly_activity`, conforme filtro `todos`, `long` ou `short` |
| Atividade semanal | `videos_publicados` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `views_novas` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `views_growth_pct_vs_prev_week` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `likes_novos` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `comentarios_novos` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `posts_com_snapshot_na_semana` | `v_dashboard_creator_weekly_activity` |
| Atividade semanal | `posts_sem_baseline_para_delta` | `v_dashboard_creator_weekly_activity` |
| Audiencia temporal | `followers_delta_7d` | evolucao futura da camada de creator |
| Audiencia temporal | `followers_latest_collected_at` | evolucao futura da camada de creator |
| Editorial | `post_url` | enrich ou contrato futuro sobre `posts` |
| Classificacao | `sub_niches_display` real | evolucao de `v_dashboard_creator_summary` |

## Passo a passo de implantacao

### Etapa 1. Validar o insumo de publicacao

Objetivo:

- confirmar que `public.posts` tem `post_date`, `views`, `likes`, `comments` e
  `video_type` suficientes para leitura semanal por criador

Checar:

- posts com `post_date` nulo
- posts sem `creator_id`
- posts com contadores nulos
- distribuicao de `video_type`

### Etapa 2. Definir a logica semanal

Objetivo:

- fechar a regra sem ambiguidades antes da view

Decisoes:

- semana inicia em qual dia
- como tratar posts sem `video_type`
- como separar performance dos videos publicados na semana de movimento
  historico observado por snapshots
- como excluir a semana corrente ainda aberta
- qual rotulo semanal o app deve exibir

Recomendacao:

- usar segunda a domingo como calendario semanal
- somar os valores atuais de todos os posts publicados na semana
- depois agregar por criador e `video_type`
- manter a linha `video_type = 'todos'` como leitura agregada dos cards
  executivos quando o filtro estiver em `todos`
- excluir da view qualquer semana ainda aberta
- gerar `week_label` pronto no SQL
- na primeira versao, nao criar semanas artificiais sem publicacao

### Etapa 3. Criar a view SQL

Objetivo:

- materializar o contrato `v_dashboard_creator_weekly_activity`

Entrega esperada:

- arquivo proprio em `sql/ddl/views/`
- `GRANT SELECT` para leitura do dashboard
- nomes de colunas estaveis para o app

### Etapa 4. Validar no Supabase

Objetivo:

- garantir que a view responde rapido e com semantica correta

Checks:

- um criador com varias semanas retorna sequencia coerente
- semanas com menor performance publicada podem mostrar percentual negativo
  contra a semana anterior, mas os contadores absolutos nunca ficam negativos
- percentuais nao explodem com denominador zero
- criadores sem publicacao suficiente nao quebram a consulta
- a semana corrente nao aparece enquanto estiver incompleta
- o intervalo exibido bate com `week_start` e `week_end`
- a soma da linha `video_type = 'todos'` bate com a soma das linhas `long`,
  `short` e demais tipos para a mesma semana
- os valores batem com uma query direta em `public.posts` usando o mesmo
  `creator_id` e intervalo de `post_date`

### Etapa 5. Ligar no Streamlit

Objetivo:

- manter a leitura real da view semanal no app

Mudancas no app:

- carregar a nova view filtrada por `creator_id`
- filtrar cards e graficos semanais pelo `video_type` selecionado no app
- usar `week_label` no eixo x
- usar `week_end` para ordenacao cronologica e tooltip
- usar `views_novas` como barras principais
- usar `likes_novos` e `comentarios_novos` como linhas de apoio
- priorizar a escala coral do highlight do menu lateral para cores de graficos
- no grafico, rotulos visuais devem aparecer como `Views`, `Likes` e
  `Comentarios`, sem expor o sufixo tecnico `novas`
- o eixo x deve usar `week_label` como valor, mas nao deve exibir esse nome como
  titulo visual
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
- os cards semanais baterem com uma query direta sobre `public.posts` por
  `post_date` da semana selecionada
