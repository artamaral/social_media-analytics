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
- `public.v_dashboard_creator_weekly_audience`

Papel:

- alimentar o grafico temporal da view `Criador individual`
- mostrar crescimento ou encolhimento por semana
- sustentar comparacoes sem depender de agregacao local no Streamlit
- `v_dashboard_creator_weekly_audience` sustenta a leitura semanal de
  seguidores por fechamento de semana

## Contrato proposto

Nome recomendado para os cards semanais:

- `public.v_dashboard_creator_weekly_activity`
- `public.v_dashboard_creator_weekly_audience`

Observacao:

- `public.v_dashboard_creator_weekly_timeseries` existe como primeira leitura de
  snapshots semanais, mas nao deve alimentar diretamente os cards semanais
  principais porque nao separa o fato editorial `Videos` das metricas de
  performance `Views`, `Likes` e `Comentarios`

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
| `views_novas` | numerico | nome legado; views ganhas na semana por todos os videos observados do criador |
| `views_growth_pct_vs_prev_week` | numerico | crescimento percentual de views contra a semana anterior |
| `likes_novos` | numerico | nome legado; likes ganhos na semana por todos os videos observados do criador |
| `comentarios_novos` | numerico | nome legado; comentarios ganhos na semana por todos os videos observados do criador |
| `posts_com_snapshot_na_semana` | numerico | quantidade de posts com pelo menos 1 snapshot na semana |
| `posts_sem_baseline_para_delta` | numerico | posts com snapshot na semana, mas sem base suficiente para delta |
| `posts_com_base_para_delta` | numerico | posts com pelo menos 2 snapshots na semana |
| `snapshots_na_semana` | numerico | total de snapshots usados para evidenciar movimento semanal |
| `semana_tem_base` | booleano | indica se a semana tem base minima para mostrar views, likes e comentarios |
| `followers_first` | numerico | primeiro snapshot de seguidores da semana |
| `followers_last` | numerico | ultimo snapshot de seguidores da semana |
| `snapshots_com_followers` | numerico | total de snapshots de audiencia com followers util para auditoria |
| `latest_collected_at` | timestamp | ultima coleta da semana para auditoria de frescor |
| `followers_delta_vs_prev_week` | numerico | delta de seguidores contra a semana anterior, usando o fechamento da semana |
| `followers_weekly_status` | texto | leitura executiva de alta, queda, estabilidade ou sem base |

Semantica dos cards semanais:

- o card semanal responde: `como meu portfolio performou nesta semana?`
- existe uma distincao obrigatoria entre fatos editoriais e metricas de
  performance:
  - `Videos` mede videos novos publicados naquela semana e vem de
    `public.posts.post_date`
  - `Views`, `Likes` e `Comentarios` medem movimento observado naquela semana e
    vem de `public.post_metrics_history`
- os cards semanais devem consumir a linha do `video_type` selecionado no app:
  `todos`, `long` ou `short`
- `videos_publicados` deve ser calculado por `public.posts.post_date`
- `views_novas`, `likes_novos` e `comentarios_novos` devem somar os deltas
  snapshot-a-snapshot observados dentro da semana, alocando o delta na janela
  do snapshot atual
- apesar do sufixo `_novas` no contrato, esses campos representam ganhos
  observados na semana, nao valores atuais do post
- como sao deltas de contador acumulado, valores negativos devem ser truncados
  para `0`
- quando uma semana nao tiver nenhum snapshot util para delta, `Views`,
  `Likes` e `Comentarios` podem ficar sem valor executivo (`--` no Streamlit),
  mesmo que `Videos` tenha valor por `post_date`
- para seguidores, a leitura semanal deve usar o ultimo snapshot da semana
  comparado ao ultimo snapshot da semana anterior; nao usar o delta entre o
  primeiro e o ultimo snapshot da mesma semana como leitura executiva
- isso significa que `followers_first` e `followers_last` continuam sendo
  metadados de auditoria, mas o valor principal exibido no card deve vir de
  `followers_delta_vs_prev_week`
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
| `followers_first` | auditoria da base semanal de audiencia |
| `followers_last` | auditoria da base semanal de audiencia |
| `followers_delta_vs_prev_week` | leitura executiva de crescimento de audiencia |
| `followers_weekly_status` | leitura executiva de crescimento, queda ou estabilidade |

## Base de calculo

Fonte primaria dos cards semanais:

- `public.posts` para `Videos`
- `public.post_metrics_history` para `Views`, `Likes` e `Comentarios`

Justificativa:

- `Videos` precisa bater com a lista editorial de videos publicados na mesma
  semana
- `Views`, `Likes` e `Comentarios` precisam responder a performance semanal do
  portfolio inteiro do criador, portanto dependem de snapshots
- usar valores atuais de `public.posts` para semanas passadas constroi uma
  historia que o banco pode nao ter observado e cria falso sinal para creators
  recem cadastrados

Regras de desenho:

- consolidar por `creator_id`
- derivar a semana editorial de `public.posts.post_date` para contar videos
- derivar a semana de performance de `post_metrics_history.collected_at` para
  contar ganhos de views, likes e comentarios
- gerar linhas por `video_type` e uma linha agregada `video_type = 'todos'`
- comparar cada semana somando os deltas de snapshot do proprio periodo do
  mesmo criador e tipo
- para seguidores, comparar o ultimo snapshot da semana com o ultimo snapshot
  da semana anterior, ambos no mesmo fuso de exibicao do dashboard
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
- semanas com publicacao podem gerar linha mesmo sem base de snapshot; nesse
  caso apenas `Videos` tem valor executivo

## Como o Supabase gera os dados semanais

Modelo de geracao:

- a serie semanal nao depende de job separado no fim da semana
- a serie nasce de uma `view` SQL consultada sob demanda no Supabase
- essa `view` le `public.posts` no momento da consulta
- conforme os workers inserem snapshots em `post_metrics_history`, as semanas
  fechadas passam a refletir automaticamente o movimento observado do portfolio
  do criador

Fluxo real de incorporacao:

1. os workers continuam atualizando `public.posts` com metricas atuais e
   inserindo historico em `post_metrics_history`
2. a view semanal agrupa videos publicados por semana de `post_date`
3. a mesma view agrupa snapshots por semana de `collected_at`
4. semanas abertas sao excluidas da view executiva
5. `Videos` vem da quantidade publicada naquela semana
6. `Views`, `Likes` e `Comentarios` vem da soma dos deltas snapshot-a-snapshot
   cujos snapshots caem dentro da semana do proprio snapshot atual
7. depois agrega os posts por criador e `video_type`
8. a linha `video_type = 'todos'` soma `long`, `short` e demais tipos existentes
9. para seguidores, usa o fechamento semanal e compara contra o fechamento da
   semana anterior do mesmo criador
10. por fim calcula percentual contra a semana anterior do mesmo criador e tipo

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
- a conta semanal deve ser snapshot atual menos snapshot anterior, alocando o
  delta na semana do snapshot atual

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
- para seguidores, o valor exibido no card semanal deve vir do fechamento
  semanal contra a semana anterior, e nao da diferenca interna entre
  `followers_first` e `followers_last`
- para `Views`, `Likes` e `Comentarios`, a comparacao semanal deve refletir o
  portfolio inteiro do criador na semana pela soma dos deltas dos snapshots
  dentro da janela
- ao filtrar a tabela editorial pela semana selecionada, incluir o dia final
  inteiro com limite superior exclusivo: `post_date < week_end + 1 dia`

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
| Audiencia temporal | `followers_delta_vs_prev_week` | `v_dashboard_creator_weekly_audience` |
| Audiencia temporal | `followers_latest_collected_at` | `v_dashboard_creator_weekly_audience` |
| Editorial | `post_url` | enrich ou contrato futuro sobre `posts` |
| Classificacao | `sub_niches_display` real | evolucao de `v_dashboard_creator_summary` |

## Passo a passo de implantacao

### Etapa 1. Validar o insumo de publicacao

Objetivo:

- confirmar que `public.posts` tem `post_date` e `video_type` suficientes para
  leitura editorial semanal por criador
- confirmar que `public.post_metrics_history` tem snapshots suficientes para
  leitura semanal de views, likes e comentarios

Checar:

- posts com `post_date` nulo
- posts sem `creator_id`
- distribuicao de `video_type`
- posts sem snapshots na semana
- posts com apenas 1 snapshot na semana, sem base para delta

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
- contar videos publicados na semana via `public.posts.post_date`
- somar views, likes e comentarios por delta entre snapshots da semana
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
- o delta semanal bate com a soma dos deltas snapshot-a-snapshot da semana
  fechada
## Query de auditoria

Use esta consulta para validar o delta snapshot-a-snapshot semanal de um post
especifico:

```sql
WITH params AS (
  SELECT
    15::bigint AS creator_id,
    'wzmuGKngTzc'::text AS post_id,
    DATE '2026-06-08' AS week_start
),
snapshots AS (
  SELECT
    pmh.post_id,
    pmh.collected_at,
    pmh.views,
    pmh.likes,
    pmh.comments,
    DATE_TRUNC('week', (pmh.collected_at - INTERVAL '3 hours'))::date AS snapshot_week_start,
    LAG(pmh.collected_at) OVER (
      PARTITION BY pmh.post_id
      ORDER BY pmh.collected_at ASC, pmh.id ASC
    ) AS prev_collected_at,
    LAG(COALESCE(pmh.views, 0)) OVER (
      PARTITION BY pmh.post_id
      ORDER BY pmh.collected_at ASC, pmh.id ASC
    ) AS prev_views,
    LAG(COALESCE(pmh.likes, 0)) OVER (
      PARTITION BY pmh.post_id
      ORDER BY pmh.collected_at ASC, pmh.id ASC
    ) AS prev_likes,
    LAG(COALESCE(pmh.comments, 0)) OVER (
      PARTITION BY pmh.post_id
      ORDER BY pmh.collected_at ASC, pmh.id ASC
    ) AS prev_comments,
    GREATEST(
      COALESCE(pmh.views, 0) - COALESCE(
        LAG(COALESCE(pmh.views, 0)) OVER (
          PARTITION BY pmh.post_id
          ORDER BY pmh.collected_at ASC, pmh.id ASC
        ),
        COALESCE(pmh.views, 0)
      ),
      0
    ) AS delta_views_snapshot,
    GREATEST(
      COALESCE(pmh.likes, 0) - COALESCE(
        LAG(COALESCE(pmh.likes, 0)) OVER (
          PARTITION BY pmh.post_id
          ORDER BY pmh.collected_at ASC, pmh.id ASC
        ),
        COALESCE(pmh.likes, 0)
      ),
      0
    ) AS delta_likes_snapshot,
    GREATEST(
      COALESCE(pmh.comments, 0) - COALESCE(
        LAG(COALESCE(pmh.comments, 0)) OVER (
          PARTITION BY pmh.post_id
          ORDER BY pmh.collected_at ASC, pmh.id ASC
        ),
        COALESCE(pmh.comments, 0)
      ),
      0
    ) AS delta_comments_snapshot
  FROM public.post_metrics_history pmh
  JOIN public.posts p ON p.post_id = pmh.post_id
  JOIN params pr ON pr.post_id = pmh.post_id
  WHERE p.creator_id = pr.creator_id
)
SELECT
  s.post_id,
  s.snapshot_week_start AS week_start,
  MIN(s.collected_at) AS first_snapshot_in_week,
  MAX(s.collected_at) AS last_snapshot_in_week,
  COUNT(*) AS snapshots_na_semana,
  SUM(s.delta_views_snapshot) AS views_novas_semana,
  SUM(s.delta_likes_snapshot) AS likes_novas_semana,
  SUM(s.delta_comments_snapshot) AS comentarios_novos_semana
FROM snapshots s
JOIN params pr ON TRUE
WHERE s.snapshot_week_start = pr.week_start
GROUP BY s.post_id, s.snapshot_week_start;
```

Leitura esperada:

- cada linha de snapshot gera um delta contra o snapshot anterior
- o delta entra na semana do snapshot atual
- a soma da semana precisa bater com a view semanal do dashboard

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
