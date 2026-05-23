# Creator View Streamlit Spec

Data: 2026-05-22

## Objetivo

Definir a primeira versao das views de criadores no Streamlit, usando a
referencia visual recebida como direcao de layout e a documentacao atual do
projeto como limite do contrato de dados.

Esta spec cobre:

- leitura critica da referencia visual
- proposta das duas views de criadores
- campos ja disponiveis na documentacao atual
- campos que ainda faltam no contrato SQL
- diretriz para o mockup inicial no app

## Leitura critica da imagem de referencia

Pelos elementos visiveis da referencia, os pontos mais fortes sao:

- hierarquia visual muito clara entre navegacao, filtros, KPIs, area principal
  e bloco editorial
- leitura rapida baseada em cards compactos e comparacao lateral
- densidade boa para ferramenta operacional, sem parecer landing page
- uso controlado de acento forte apenas para o item ativo e para destaques
- composicao em quatro camadas:
  - filtros no topo
  - faixa de KPIs
  - linha analitica com graficos
  - bloco largo de leitura editorial ou cadencia

Pontos que merecem cuidado ao adaptar para a nossa realidade:

- a referencia parece orientada a metricas unicas e pode esconder contexto de
  governanca e qualidade dos dados
- a referencia usa indicadores que nao existem no nosso contrato atual, como
  compartilhamentos, dislikes, average view percentage e URL publica por video
- um painel de detalhe muito rico exigiria campos que ainda nao existem na view
  atual ou nas tabelas auxiliares
- a view precisa continuar escaneavel mesmo sem dados historicos profundos de
  followers e sem subnicho real ja exposto no SQL

Conclusao:

- a view de criadores deve seguir a hierarquia estrutural da referencia
- precisamos separar a experiencia em duas views distintas
  - uma geral para leitura comparativa da carteira
  - uma individual para leitura aprofundada de um criador
- o ranking comparativo continua util, mas ele pertence principalmente a view
  geral
- a tabela de top videos deve existir na primeira versao da tela
- o bloco inferior de cadencia deve ser removido por enquanto
- a tela deve assumir explicitamente os gaps do contrato de dados atual

## Comparacao direta com o que foi feito antes

O mockup anterior capturava apenas uma parte da imagem:

- filtros compactos
- faixa de KPIs
- ranking de criadores
- painel lateral de detalhe

O que faltava em relacao a imagem:

- um miolo analitico com grafico de distribuicao
- uma serie temporal clara
- uma tabela editorial de top videos
- um bloco largo inferior inspirado no painel "when should you publish"

Correcao adotada:

- manter a linguagem visual dark do projeto
- reorganizar a Creator View na mesma logica da referencia
- adicionar blocos analiticos sustentados por dados documentados
- registrar de forma visivel os campos que ainda faltam

## Proposta de views

Estrutura de navegacao:

- `Criadores`
  - `Visao geral`
  - `Criador individual`

### 1. View geral de criadores

Objetivo:

- comparar a carteira monitorada
- priorizar onde vale aprofundar leitura
- responder quem concentra volume, tamanho de audiencia e engajamento

Blocos recomendados:

1. Cabecalho da pagina
   - titulo
   - subtitulo curto
   - banner executivo explicando o papel da tela

2. Filtros compactos
   - plataforma
   - no futuro, nicho e recorte temporal agregado

3. KPIs superiores
   - criadores ativos
   - seguidores monitorados
   - total de videos
   - total de views
   - total de likes
   - total de comentarios

4. Ranking comparativo principal
   - linhas densas por criador
   - seguidores
   - views totais
   - engajamento medio

### 2. View de criador individual

Objetivo:

- analisar profundamente apenas um criador
- manter leitura temporal
- abrir o bloco editorial dos top videos

1. Cabecalho da pagina
   - titulo
   - subtitulo curto
   - banner executivo comparando a adaptacao com a imagem

2. Filtros compactos
   - criador em foco
   - periodo
   - plataforma
   - modo de ordenacao

3. KPIs superiores
   - seguidores
   - rank de engajamento medio
   - total de videos
   - total de views
   - total de likes
   - total de comentarios
   - numeros devem usar notacao compacta para leitura executiva, por exemplo
     `99.9K`, `235.7K` e `18.3M`
   - a fonte dos valores deve ser a maior possivel dentro do card, sem quebra de
     linha e sem extrapolar o limite visual do bloco

4. Linha analitica principal
   - distribuicao de engajamento
   - serie temporal semanal do criador
   - top videos por views

5. Painel de detalhe do criador
   - leitura operacional
   - detalhe analitico
   - bloco explicito de campos faltantes

6. Expander tecnico
   - lista dos campos usados no mockup
   - origem de cada campo

## Dados exatos para os blocos analiticos

### Grafico 1: distribuicao de engajamento

Objetivo:

- reproduzir o papel visual do grafico circular da imagem
- mostrar como o engajamento do criador esta distribuido dentro do que o nosso
  contrato atual permite

Dados usados:

- `public.v_dashboard_creator_summary.total_likes`
- `public.v_dashboard_creator_summary.total_comments`

Formula:

- fatia 1 = participacao ponderada de `total_views * 1`
- fatia 2 = participacao ponderada de `total_likes * 10`
- fatia 3 = participacao ponderada de `total_comments * 20`

Regra visual:

- o grafico deve ser estatico, sem interacao de zoom/pan
- a leitura e normalizada para mostrar a proporcao de cada componente no score
  ponderado ja usado pelo projeto
- a formula de referencia e `views * 1 + likes * 10 + comments * 20`
- a diferenca entre views e interacoes deve respeitar os pesos do algoritmo de
  prioridade/engajamento, sem usar valores brutos isolados
- os nomes das fatias devem ficar apenas na legenda
- dentro do donut deve aparecer apenas o percentual
- labels devem ficar dentro do grafico; se nao couberem, devem ser ocultados em
  vez de sair cortados para fora da caixa

Limite atual:

- nao temos `total_shares`
- nao temos `total_dislikes`

### Grafico 2: serie temporal semanal clara

Objetivo:

- responder como o volume do criador cresce ou encolhe semana a semana
- manter uma leitura simples e confiavel
- evitar excesso de ruido diario e ao mesmo tempo nao alongar demais a leitura

Definicao obrigatoria dos cards semanais:

- o bloco semanal representa o movimento geral do criador na semana fechada
- `Videos` mede videos novos publicados na semana, a partir de `public.posts.post_date`
- `Views` mede views novas na semana, considerando todos os posts monitorados do criador
- `Likes` mede likes novos na semana, considerando todos os posts monitorados do criador
- `Comentarios` mede comentarios novos na semana, considerando todos os posts monitorados do criador
- `Views`, `Likes` e `Comentarios` devem vir do mesmo historico temporal de snapshots, nao dos valores atuais dos videos publicados naquela semana
- analise de posts isolados permanece na tabela editorial de videos e em views especificas de detalhe por post

Contrato recomendado:

- `public.v_dashboard_creator_weekly_activity`

Dados esperados da view:

- `creator_id`
- `entity_id`
- `entity_name`
- `platform`
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

Observacao:

- este grafico deve sempre ser de um unico criador por vez
- o Streamlit nao deve calcular a serie bruta a partir de `public.posts`
- o Streamlit nao deve usar valores atuais de posts publicados na semana para preencher os cards semanais de `Views`, `Likes` e `Comentarios`
- quando a ligacao SQL acontecer, o ideal e filtrar por `creator_id`
- o filtro `long/short/todos` deve usar a coluna `video_type` ja consolidada na view
- a unidade recomendada para comparacao e a semana fechada, nao o dia isolado
- semanas abertas nao devem aparecer no grafico
- o rotulo recomendado para exibicao e o intervalo completo da semana
- o grafico deve ser estatico, sem interacao de zoom/pan
- a serie deve mostrar `views_novas`, `likes_novos` e `comentarios_novos`
- o seletor nao deve abrir todas as semanas indiscriminadamente
- data de corte inicial: `2026-05-04`, definida apos conferencia de cobertura
  historica e volume de snapshots
- o app deve permitir selecionar apenas semanas fechadas dentro da janela de
  corte
- a implementacao detalhada do contrato fica em documento proprio

### Tabela editorial: top videos por views

Objetivo:

- reproduzir o painel editorial mais forte da imagem
- mostrar rapidamente quais videos puxam o desempenho do criador

Dados usados:

- `public.posts.title`
- `public.posts.post_date`
- `public.posts.views`
- `public.posts.likes`
- `public.posts.comments`
- `public.posts.video_type`

Ordenacao proposta:

- ordenar por `views desc`

Gap atual:

- `post_url` ainda nao existe no contrato

## Campos documentados que ja podem ser usados

Fontes principais atuais:

- `public.v_dashboard_creator_summary`
- `public.posts`

Campos da view resumida:

| Campo | Origem | Uso na view |
|---|---|---|
| `entity_id` | `v_dashboard_creator_summary` | identificacao tecnica |
| `entity_name` | `v_dashboard_creator_summary` | titulo do criador |
| `niche` | `v_dashboard_creator_summary` | filtro e contexto |
| `creator_type` | `v_dashboard_creator_summary` | contexto do perfil |
| `creator_id` | `v_dashboard_creator_summary` | identificacao tecnica |
| `platform` | `v_dashboard_creator_summary` | filtro e etiqueta |
| `username` | `v_dashboard_creator_summary` | identificacao publica |
| `channel_id` | `v_dashboard_creator_summary` | identificacao tecnica |
| `followers` | `v_dashboard_creator_summary` | KPI e ranking |
| `post_count` | `v_dashboard_creator_summary` | KPI e ranking |
| `total_views` | `v_dashboard_creator_summary` | KPI e ranking |
| `total_likes` | `v_dashboard_creator_summary` | detalhe lateral |
| `total_comments` | `v_dashboard_creator_summary` | detalhe lateral |
| `engagement_rate_pct` | `v_dashboard_creator_summary` | KPI e ranking |
| `latest_post_date` | `v_dashboard_creator_summary` | detalhe editorial |
| `latest_collected_at` | `v_dashboard_creator_summary` | detalhe operacional |
| `is_active` | `v_dashboard_creator_summary` | status |

Campos da tabela de posts que ajudam a aproximar a imagem:

| Campo | Origem | Uso na view |
|---|---|---|
| `title` | `public.posts` | tabela de top videos |
| `post_date` | `public.posts` | tabela de top videos e serie temporal semanal |
| `views` | `public.posts` | top videos e serie temporal semanal |
| `likes` | `public.posts` | distribuicao e serie temporal semanal |
| `comments` | `public.posts` | distribuicao e tabela |
| `video_type` | `public.posts` | etiqueta editorial |
| `post_id` | `public.posts` | base potencial para URL futura |

Nova camada recomendada para serie temporal:

| Campo | Origem | Uso na view |
|---|---|---|
| `week_start` | `v_dashboard_creator_weekly_activity` | eixo temporal semanal |
| `week_end` | `v_dashboard_creator_weekly_activity` | fechamento da semana consolidada |
| `week_label` | `v_dashboard_creator_weekly_activity` | rotulo amigavel no grafico |
| `video_type` | `v_dashboard_creator_weekly_activity` | filtro `long`, `short` ou `todos` |
| `videos_publicados` | `v_dashboard_creator_weekly_activity` | videos novos publicados na semana |
| `views_novas` | `v_dashboard_creator_weekly_activity` | movimento de views na semana |
| `views_growth_pct_vs_prev_week` | `v_dashboard_creator_weekly_activity` | intensidade relativa da variacao |
| `likes_novos` | `v_dashboard_creator_weekly_activity` | movimento de likes na semana |
| `comentarios_novos` | `v_dashboard_creator_weekly_activity` | movimento de comentarios na semana |

Campos complementares documentados fora da view atual:

| Campo | Origem documentada | Situacao |
|---|---|---|
| `created_at` | `public.creators` | existe na tabela, nao sobe na view |
| `normalized_name` | `public.entities` | existe na tabela, nao sobe na view |
| `followers` historico | `creator_metrics_history` na documentacao de projeto | documentado como direcao, nao disponivel nesta branch via view |

## Campos que faltam para uma boa Creator View

Campos faltantes mais importantes:

| Campo desejado | Motivo | Situacao atual |
|---|---|---|
| `sub_niches` do criador | a referencia de tela pede comparacao mais fina do que apenas `niche` | nao sobe na view atual |
| `monitoring_started_at` | permite mostrar desde quando o criador esta monitorado | nao existe na view atual |
| `followers_delta_7d` / `followers_delta_30d` | ajuda a ver crescimento de audiencia | nao existe na view atual |
| `followers_latest_collected_at` | separa frescor de audiencia do frescor de posts | nao existe na view atual |
| `avg_views_per_post` como coluna da view | pode ser calculado no app, mas idealmente deveria vir pronto do SQL | hoje depende de derivacao local |
| `latest_post_url` | facilitaria drill-down rapido para o ultimo conteudo | nao existe na view atual |
| `content_mix` ou distribuicao de tipo de conteudo | importante para leitura editorial | nao existe no contrato atual |
| `top_posts_summary` | detalhe lateral mais forte | nao existe no contrato atual |
| `total_shares` | a imagem de referencia usa essa metrica em destaque | nao existe no contrato atual |
| `total_dislikes` | a imagem de referencia explicita dislikes no donut | nao existe no contrato atual |
| `average_view_pct` | a imagem usa essa leitura no topo | nao existe no contrato atual |
| `post_url` | a tabela da imagem tem coluna de URL | nao existe no contrato atual |

## Campos que o mockup usa com fallback visual

No mockup inicial do Streamlit:

- `subnicho` aparece como placeholder visual
- `curva de followers` aparece como gap explicito
- `top videos` usa apenas os campos ja documentados em `public.posts`
- `rank de engajamento medio` e derivado localmente para leitura visual
- a serie temporal precisa priorizar janela semanal
- a serie temporal atual do mockup ainda nao reflete o contrato ideal
- a cadencia de publicacao foi removida ate existir uma base confiavel

Regra importante:

- o mockup nao deve fingir que esses campos existem no SQL
- os gaps precisam ficar visiveis para orientar a proxima iteracao da view

## Contrato SQL minimo sugerido para a proxima etapa

Evolucao recomendada de `v_dashboard_creator_summary`:

```text
entity_id
entity_name
niche
creator_type
creator_id
platform
username
channel_id
followers
post_count
total_views
total_likes
total_comments
engagement_rate_pct
latest_post_date
latest_collected_at
is_active
sub_niches_display
monitoring_started_at
followers_delta_30d
followers_latest_collected_at
avg_views_per_post
```

Nova view recomendada para o criador individual:

```text
v_dashboard_creator_weekly_activity
```

Papel dessa view:

- sustentar a serie temporal semanal do criador individual
- separar leitura de crescimento por criador da leitura de crescimento por post
- evitar que o Streamlit agregue historico bruto localmente

Prioridade dos campos novos:

1. `sub_niches_display`
2. `monitoring_started_at`
3. `followers_delta_30d`
4. `followers_latest_collected_at`
5. `avg_views_per_post`

## Diretriz para o mockup no app

O mockup da pagina deve:

- usar a paleta cinza escuro + coral ja definida no dashboard
- separar claramente a view geral da view individual
- manter filtros compactos no topo
- usar cards superiores para KPIs
- reproduzir a composicao da referencia com foco em
  - distribuicao
  - serie temporal
  - tabela editorial
- mostrar tabela de top videos por views
- mostrar um painel lateral com o criador selecionado na view individual
- deixar claros os gaps do contrato de dados

O mockup nao deve:

- consultar SQL novo ainda
- inventar campos como se ja existissem
- transformar a tela em tabela tecnica pura
- esconder a diferenca entre dado real e placeholder

## Criterio de pronto desta fase

Esta fase estara pronta quando:

- a analise critica da referencia estiver registrada
- os campos atuais e faltantes estiverem mapeados por bloco das duas telas
- a documentacao da view estiver criada
- o app Streamlit tiver um mockup navegavel das duas telas de `Criadores`
- a comparacao entre mockup e imagem estiver explicitada

## Proximo passo recomendado

Depois desta fase:

1. revisar a UX do mockup no app
2. decidir a nova versao de `v_dashboard_creator_summary`
3. definir o contrato de `v_dashboard_creator_weekly_activity`
4. implementar a evolucao SQL em arquivo proprio
5. ligar a pagina a dados reais somente depois da validacao do contrato
