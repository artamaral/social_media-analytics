# Historico de metricas de creators

## Objetivo

Criar uma camada historica para metricas dinamicas de creators, iniciando por
followers do YouTube.

No YouTube, o campo usado como follower e `statistics.subscriberCount`,
retornado pela YouTube Data API no metodo `channels.list` com
`part=statistics`.

## Principio

`creators.followers` representa apenas o valor corrente mais recente.

Analises de crescimento, tendencia e aceleracao devem usar snapshots em
`creator_metrics_history`, nunca apenas o valor atual em `creators`.

Esse desenho segue o mesmo principio de `post_metrics_history`: metricas
dinamicas precisam de historico para serem confiaveis em analytics.

## Tabela `creators`

A tabela `creators` passa a armazenar o estado corrente das metricas de canal.
Esses campos existem para leitura rapida no dashboard e para joins simples.

Campos:

- `followers`: ultimo valor conhecido de inscritos/followers do canal.
- `followers_collected_at`: data e hora do snapshot que atualizou o valor atual.
- `followers_source`: origem da coleta, inicialmente `youtube_channels_api`.
- `hidden_subscriber_count`: indica se o canal esconde a contagem de inscritos.
- `channel_view_count`: total de views do canal retornado pela API.
- `channel_video_count`: total de videos do canal retornado pela API.

## Tabela `creator_metrics_history`

Cada linha representa um snapshot de metricas de um creator em um momento
especifico.

Campos:

- `id`: identificador tecnico do snapshot.
- `creator_id`: referencia para `creators.id`.
- `followers`: inscritos/followers retornados pela API.
- `channel_view_count`: views totais do canal no momento da coleta.
- `channel_video_count`: quantidade total de videos do canal no momento da
  coleta.
- `hidden_subscriber_count`: indica se a contagem de inscritos esta oculta.
- `collected_at`: data e hora da coleta.
- `source`: origem do dado, inicialmente `youtube_channels_api`.

Indices:

- `idx_creator_metrics_history_creator_collected_at`: suporta consultas por
  creator ordenadas do snapshot mais recente para o mais antigo.
- `idx_creator_metrics_history_collected_at`: suporta auditorias e recortes por
  periodo.

## Trigger de sincronizacao

A funcao `sync_creator_latest_metrics()` roda apos cada insert em
`creator_metrics_history`.

Ela atualiza os campos correntes em `creators` apenas quando o novo snapshot e
mais recente ou igual ao `followers_collected_at` atual.

Isso evita que uma carga atrasada sobrescreva o estado corrente com um snapshot
mais antigo.

Fluxo:

1. Worker coleta metricas de canal via YouTube Data API.
2. Worker insere snapshot em `creator_metrics_history`.
3. Trigger atualiza `creators.followers` e campos auxiliares.
4. Dashboard usa `creators` para estado atual e `creator_metrics_history` para
   crescimento temporal.

## Implementacao no worker

A primeira implementacao fica no worker
`scripts/cloud_run/youtube_main_scraper/main.py`.

Esse worker busca todos os creators do YouTube no Supabase, mas processa apenas
um lote por execucao, controlado por `BATCH_SIZE` e pelo cursor salvo em
`pipeline_state`.

Portanto, a coleta de followers segue a mesma cobertura do discovery:

- em uma execucao, coleta apenas os creators do lote atual;
- ao longo das execucoes, percorre todos os creators;
- quando chega ao fim da lista, o cursor volta para `0`.

Na chamada `channels.list`, o worker usa `part=contentDetails,statistics`.
Assim, a mesma chamada que retorna a playlist de uploads tambem retorna as
metricas do canal.

Campos usados da resposta:

- `contentDetails.relatedPlaylists.uploads`
- `statistics.subscriberCount`
- `statistics.hiddenSubscriberCount`
- `statistics.viewCount`
- `statistics.videoCount`

O worker nao atualiza `creators` diretamente. Ele insere o snapshot em
`creator_metrics_history` e deixa o trigger sincronizar o valor corrente.

## Permissoes e RLS

Como o worker escreve via Supabase REST/PostgREST, a tabela
`creator_metrics_history` precisa ter permissao e policy de insert compativeis
com a role usada pela chave configurada em `SUPABASE_KEY`.

A migration cria:

- `GRANT SELECT, INSERT` na tabela para `anon`, `authenticated` e
  `service_role`;
- `GRANT USAGE, SELECT` na sequence `creator_metrics_history_id_seq`;
- policy `creator_metrics_history_insert_worker` permitindo insert quando
  `source = 'youtube_channels_api'`.

Se o worker retornar erro `new row violates row-level security policy`, aplicar
novamente a migration `_up.sql` ou executar o bloco de grants/policy da
documentacao de migration.

## Status de implementacao

Status:

- implementado
- testado ponta a ponta
- validado em 2026-05-22

Evidencias de validacao:

- worker executado com `errors = 0`, `processed = 3` e `error_details = []`;
- snapshots reais gravados em `creator_metrics_history` com
  `source = 'youtube_channels_api'`;
- trigger sincronizou `creators.followers`, `followers_collected_at`,
  `followers_source`, `channel_view_count`, `channel_video_count` e
  `hidden_subscriber_count`;
- validacao confirmou creators atualizados como `garagem do bellote`,
  `canal da mecanica`, `flatout`, `jacare racing`, `corte de giro` e
  `fator premium`.

Conclusao:

- nao existe pendencia aberta no backlog para essa atividade;
- proximas melhorias devem ser tratadas como novas tarefas, por exemplo views
  analiticas de crescimento de followers por periodo.

## Analises suportadas

Com os snapshots sera possivel medir:

- crescimento absoluto de followers por periodo;
- crescimento percentual de followers;
- velocidade de crescimento de audiencia;
- aceleracao de crescimento;
- ranking de creators emergentes;
- relacao entre crescimento do canal e performance recente de videos.

## Observacoes da API

`subscriberCount` pode ser arredondado pela propria API do YouTube. Por isso,
ele deve ser tratado como indicador operacional de escala e crescimento, nao
como contador exato em todos os cenarios.

Canais com `hiddenSubscriberCount = true` podem nao retornar uma contagem util
de inscritos. Nesses casos, o snapshot ainda deve registrar a flag para evitar
interpretacoes erradas no dashboard.

## Validacao inicial

Depois de aplicar a migration:

```sql
select column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name = 'creators'
  and column_name in (
    'followers',
    'followers_collected_at',
    'followers_source',
    'hidden_subscriber_count',
    'channel_view_count',
    'channel_video_count'
  )
order by column_name;
```

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name = 'creator_metrics_history';
```

```sql
select trigger_name
from information_schema.triggers
where event_object_schema = 'public'
  and event_object_table = 'creator_metrics_history';
```

Teste manual controlado:

```sql
insert into public.creator_metrics_history (
  creator_id,
  followers,
  channel_view_count,
  channel_video_count,
  hidden_subscriber_count,
  collected_at,
  source
)
select
  id,
  1000,
  50000,
  120,
  false,
  now(),
  'manual_test'
from public.creators
where platform = 'youtube'
limit 1;
```

Depois:

```sql
select
  id,
  followers,
  followers_collected_at,
  followers_source,
  hidden_subscriber_count,
  channel_view_count,
  channel_video_count
from public.creators
where followers_source = 'manual_test'
order by followers_collected_at desc
limit 1;
```

Remover o teste manual antes de usar dados reais, se ele for feito em producao.
