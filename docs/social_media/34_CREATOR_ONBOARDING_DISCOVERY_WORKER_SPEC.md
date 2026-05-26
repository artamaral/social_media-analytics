# Worker de discovery inicial para novos creators

## Objetivo

Definir as regras para um worker separado de onboarding de creators do YouTube.

Esse worker existe para resolver o intervalo entre:

1. o cadastro de um novo creator pela operacao;
2. a chegada desse creator ao ciclo normal do `youtube_main_scraper`.

O worker deve fazer apenas discovery inicial de posts. Ele nao substitui o
scraper principal e nao deve coletar snapshots historicos de metricas.

## Decisao

Criar um worker separado para discovery inicial de novos creators.

Regra de fluxo:

```text
Novo creator cadastrado?
  sim
    -> concluir a acao "Cadastrar criador no Supabase"
    -> confirmar sucesso da criacao do creator no banco
    -> chamar URL do worker de onboarding
    -> worker recebe creator_id
    -> worker busca channel_id no banco
    -> worker verifica se ja existem posts para o creator
    -> se nao existem posts, coleta uploads recentes do canal
    -> worker faz upsert em public.posts
    -> trigger add_to_queue() coloca os posts em public.post_update_queue
    -> worker termina
  nao
    -> nao chamar worker
```

## Escopo do worker

Implementacao:

- `scripts/cloud_run/youtube_creator_onboarding/main.py`
- `scripts/cloud_run/youtube_creator_onboarding/requirements.txt`
- `scripts/cloud_run/youtube_creator_onboarding/Procfile`

Comando de start esperado no Cloud Run:

```text
functions-framework --target=run --host=0.0.0.0 --port=${PORT}
```

Esse comando e necessario para que o container escute a porta definida pela
variavel `PORT` do Cloud Run, normalmente `8080`.

Variaveis de ambiente esperadas:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `YOUTUBE_API_KEY`
- `ONBOARDING_WORKER_TOKEN`
- `MAX_UPLOADS` opcional, com limite efetivo de `1` a `50`

O worker deve:

- receber apenas `creator_id` como parametro operacional;
- buscar `channel_id` em `public.creators`;
- validar que o creator existe;
- validar que `platform = 'youtube'`;
- validar que `channel_id` esta preenchido;
- checar se ja existem posts em `public.posts` para o `creator_id`;
- se ja existirem posts, retornar `skipped`;
- se nao existirem posts, buscar uploads recentes do canal no YouTube;
- buscar detalhes basicos dos videos necessarios para popular `public.posts`;
- fazer upsert dos posts usando a mesma modelagem do scraper principal;
- retornar resumo com `creator_id`, `processed_posts`, `skipped` e
  `error_details`.

O worker nao deve:

- alterar `pipeline_state`;
- ler ou salvar o cursor `youtube_cursor`;
- gravar em `creator_metrics_history`;
- atualizar `creators.followers`;
- calcular prioridade de fila no codigo;
- alterar `post_update_queue` diretamente;
- substituir o `youtube_main_scraper` recorrente;
- substituir o worker `postMetrics`.

## Relação com snapshots e guardrail

Esse worker nao coleta snapshots.

Depois do upsert em `public.posts`, a entrada na fila deve acontecer pelo
trigger ja existente:

- `public.add_to_queue()`
- trigger `trigger_add_to_queue` em `public.posts`

Posts novos entram sem historico em `post_metrics_history`. Na pratica, eles
terao:

```text
total_checagens = 0
```

Por isso, a view `public.v_post_update_queue_batch` deve tratar esses posts
pelo guardrail operacional de cobertura minima, sem criar uma regra especial
para creator recem-cadastrado.

## Regra simples de idempotencia

A trava inicial deve ser existencia de posts, nao metricas diferentes de zero.

Consulta conceitual:

```sql
select exists (
  select 1
  from public.posts
  where creator_id = :creator_id
);
```

Se retornar `true`, o worker deve encerrar sem chamar a YouTube API.

Motivo:

- views, likes e comentarios podem ser legitimamente `0`;
- followers pode estar oculto ou nulo;
- existencia de linha em `posts` e um sinal mais estavel de discovery ja
  realizado;
- a regra reduz chamadas repetidas por clique duplo, retry ou timeout da UI.

Limite conhecido:

- duas chamadas simultaneas podem consultar o banco antes do primeiro insert e
  ambas seguirem para a YouTube API.

Esse risco e aceitavel para o MVP operacional. Se houver repeticao real em
producao, a proxima evolucao deve ser uma trava por `creator_id`, como status
de onboarding ou lock transacional.

## Autenticacao da URL

A URL do worker nao deve ser tratada como endpoint publico livre.

Mesmo sendo um worker separado, uma URL sem autenticacao permite que qualquer
pessoa com o link acione:

- consumo de quota da YouTube Data API;
- custo de Cloud Run;
- escritas no Supabase;
- ruido operacional nos logs.

Padrao minimo recomendado:

```text
POST /run
Header: x-worker-token: <segredo>
Body: { "creator_id": 55 }
```

O token deve ficar:

- nos secrets do Streamlit, quando a chamada partir do app;
- nas variaveis de ambiente do Cloud Run, quando validado pelo worker.

O worker deve retornar `401` ou equivalente quando o token estiver ausente ou
incorreto.

## Separacao sem duplicar regra de negocio

Worker separado cria clareza operacional, mas a regra de coleta nao deve
divergir do scraper principal.

Risco de duplicacao:

- regra de short vs long diferente;
- payload de `posts` diferente;
- tratamento de erro diferente;
- coleta de campos diferente;
- upsert diferente;
- correcao futura aplicada em um worker e esquecida no outro.

Diretriz:

```text
worker principal
  -> seleciona creators por cursor
  -> chama funcao compartilhada de discovery

worker onboarding
  -> recebe creator_id
  -> busca creator no banco
  -> chama funcao compartilhada de discovery
```

Se a primeira implementacao duplicar codigo por simplicidade, ela deve ser
tratada como etapa temporaria e documentada para refatoracao posterior.

## Integracao com Streamlit

Nao e necessario criar um documento separado apenas para a integracao com
Streamlit neste momento.

Motivo:

- o fluxo de cadastro ja esta documentado em
  `docs/data_model/entity_intake_process.md`;
- a integracao do app deve ser apenas uma etapa adicional apos
  `public.create_creator_from_resolved_entity(...)`;
- o contrato do worker fica centralizado neste spec;
- evita duplicar regras entre documento de dashboard e documento de pipeline.

Regra para o Streamlit:

1. cadastrar o creator pelo fluxo controlado existente;
2. executar a acao/botao `Cadastrar criador no Supabase`;
3. aguardar sucesso da RPC que cria o registro em `public.creators`;
4. receber ou resolver o `creator_id` criado;
5. chamar o worker de onboarding com `creator_id`;
6. nao enviar `channel_id` no payload;
7. nao expor token no navegador;
8. mostrar retorno operacional simples: `processed`, `skipped` ou `error`.

O worker deve rodar somente depois do sucesso do cadastro do creator no
Supabase. Essa ordem garante que o `channel_id` novo ja esta persistido em
`public.creators` antes da chamada do worker.

Se futuramente o Streamlit ganhar UI dedicada de monitoramento, retry ou fila
de jobs de onboarding, ai sim deve ser criado um spec proprio em
`docs/dashboard`.

## Fallback manual para primeira carga

O fluxo preferencial e automatico via Streamlit, logo apos o cadastro do
creator no Supabase.

Se o cadastro do creator funcionar, mas o dashboard ou a validacao SQL mostrar
`post_count = 0`, o operador pode executar manualmente a primeira carga de
discovery chamando a URL do worker.

Esse fallback deve ser usado apenas quando:

- o creator ja existe em `public.creators`;
- o `creator_id` ja foi retornado pela UI ou confirmado no Supabase;
- a UI nao chamou o worker automaticamente, ou o retorno do worker nao ficou
  visivel;
- `public.posts` ainda nao possui posts para o creator.

Exemplo em PowerShell:

```powershell
Invoke-WebRequest `
  -UseBasicParsing `
  -Uri "https://youtube-creator-onboarding-750306104774.us-central1.run.app" `
  -Method POST `
  -Headers @{ "x-worker-token" = "SEU_TOKEN" } `
  -ContentType "application/json" `
  -Body '{"creator_id":56}'
```

Depois da chamada manual, executar
`sql/dml/validate_creator_onboarding_discovery.sql` trocando o `creator_id` na
CTE `params`.

Resultado esperado:

- `posts_total > 0`;
- `queue_total = posts_total`;
- `validation_status = 'ok'`;
- a segunda chamada para o mesmo `creator_id` deve retornar `skipped`.

## Validacao em producao

Validacoes registradas em 2026-05-26:

1. Chamada manual do worker:
   - creator: `Autoesporte`
   - `creator_id`: `55`
   - resultado do worker: `processed_posts = 50`
   - resultado no Supabase: `posts_total = 50` e `queue_total = 50`
2. Fluxo automatico pelo Streamlit:
   - creator: `Carros com Tiago`
   - `creator_id`: `57`
   - `channel_id`: `UC_dEiS87i1OEiUc5iPfXRKA`
   - mensagem na UI: `Discovery inicial concluido: 50 posts processados.`
   - view `v_dashboard_creator_summary`: `post_count = 50`,
     `total_views = 9941797`, `latest_post_date = 2026-05-25 22:59:39`,
     `latest_collected_at = null`

Observacao:

- `latest_collected_at = null` e esperado imediatamente apos o onboarding,
  porque o worker faz discovery de posts e nao snapshots em
  `post_metrics_history`.
- Depois da entrada de novos posts, o KPI `Monitoramento de posts sem checagem`
  pode subir temporariamente. Baseline observado apos as cargas recentes:
  `239` posts com menos de `3` checagens.

## Validacoes obrigatorias

Antes de considerar o worker saudavel:

- cadastrar um creator novo em ambiente controlado;
- confirmar que o worker buscou o `channel_id` no banco;
- confirmar que novos posts entraram em `public.posts`;
- confirmar que novos posts entraram em `public.post_update_queue`;
- confirmar que `public.v_post_update_queue_batch` retorna os posts quando
  elegiveis pelo guardrail;
- confirmar que `creator_metrics_history` nao recebeu insert desse worker;
- repetir a chamada para o mesmo `creator_id` e confirmar retorno `skipped`;
- confirmar logs com `creator_id`, status e detalhes de erro.

## Fora de escopo

- ranking de creators emergentes;
- atualizacao imediata de followers;
- historico de metricas de canal;
- mudanca na regra de `next_check`;
- mudanca em `v_post_update_queue_batch`;
- nova prioridade especial para creator recem-cadastrado;
- mudanca no scheduler do scraper principal.
