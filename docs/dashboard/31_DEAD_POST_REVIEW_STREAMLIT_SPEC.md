# Sanitizacao operacional no Streamlit

## Objetivo

Criar uma tela operacional no dashboard Streamlit para executar a
sanitizacao manual de casos que exigem decisao humana, com foco inicial em
videos que a YouTube API deixou de retornar.

O objetivo nao e repetir os KPIs de `Data quality`, mas transformar os sinais
de `Data quality` em acao auditavel dentro do dashboard.

Esta tela deve apoiar o processo ja documentado em
`docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`.

## Papel da pagina

Separacao de responsabilidade:

- `Data quality`: monitora e resume o problema por KPI
- `Sanitizacao operacional`: lista casos concretos e permite acao humana

O bloco de `Data quality` deve continuar mostrando apenas:

- legado guardrail
- posts mortos / pendentes de validacao

A decisao sobre itens especificos deve acontecer na tela de sanitizacao.

## Resumo da atividade inicial

Durante a operacao da fila, alguns `post_id` deixam de ser retornados pela
chamada `videos.list` da YouTube API. O pipeline ja registra esses casos em
`post_collection_failures`, incrementa `failure_count` e promove o status para
`unavailable` depois de falhas repetidas.

O problema operacional atual e que a confirmacao humana ainda depende de abrir
URLs manualmente e rodar SQL no banco. Isso funciona, mas nao escala bem para
listas maiores e aumenta risco de erro humano.

A melhoria proposta e criar um fluxo no dashboard:

1. listar candidatos indisponiveis
2. exibir `youtube_url` como link clicavel
3. permitir selecao por checkbox
4. confirmar selecionados como `confirmed_unavailable`
5. registrar auditoria humana no banco

## Nome recomendado da pagina

Nome sugerido no app:

```text
Sanitizacao Operacional
```

Motivo:

- nao limita a pagina apenas a dead posts
- deixa claro que esta e a area de acao manual
- permite incluir futuramente outras rotinas de sanitizacao controlada

Subtitulo sugerido:

```text
Revisao manual e confirmacao de casos operacionais
```

## Escopo inicial

Incluido:

- tela Streamlit de sanitizacao
- tabela baseada em `v_dashboard_unavailable_video_review`
- links clicaveis para cada `youtube_url`
- selecao por checkbox dos itens revisados
- botao para confirmar selecionados como `confirmed_unavailable`
- campo opcional de nota humana
- feedback visual apos atualizacao

Fora do escopo inicial:

- abrir automaticamente todos os videos no Microsoft Edge
- controlar navegador local a partir do Streamlit Cloud
- apagar posts, historico ou snapshots
- corrigir todas as views analiticas que ainda exibem dead posts confirmados
- outras rotinas de sanitizacao ainda nao formalizadas

## Fonte de dados inicial

View principal:

```text
public.v_dashboard_unavailable_video_review
```

Campos esperados:

- `post_id`
- `youtube_url`
- `failure_count`
- `status`
- `last_failure_reason`
- `first_failed_at`
- `last_failed_at`
- `human_review_status`
- `human_reviewed_at`
- `human_reviewed_by`

Filtros iniciais recomendados:

- `human_review_status is null`
- `status in ('unavailable_candidate', 'unavailable')`
- ordenacao por `failure_count desc`, `last_failed_at desc`

## Experiencia da tela

Blocos:

1. KPIs de revisao
2. filtros
3. tabela de candidatos
4. painel de acao
5. resultado da ultima acao

KPIs:

- candidatos pendentes
- candidatos com `failure_count >= 3`
- confirmados hoje
- itens selecionados

Filtros:

- status
- failure_count minimo
- apenas pendentes de revisao humana
- busca por `post_id`

Tabela:

- checkbox de selecao
- `post_id`
- `youtube_url` como link clicavel
- `failure_count`
- `status`
- `last_failed_at`
- `human_review_status`

Acao:

- campo `reviewed_by`
- campo `human_review_notes`
- botao `Confirmar selecionados como unavailable`

## Comportamento esperado

Quando o usuario clicar no link:

- abrir o video no navegador
- permitir confirmacao visual no YouTube

Quando o usuario selecionar linhas e clicar no botao:

- validar que existe pelo menos um item selecionado
- exibir uma confirmacao visual antes do update, se possivel
- chamar uma RPC ou query controlada
- atualizar a tabela apos sucesso
- exibir quantos registros foram confirmados

## Regra de banco recomendada

Preferir RPC no Supabase em vez de SQL solto no Streamlit.

Nome sugerido:

```text
public.confirm_unavailable_posts(
  p_post_ids text[],
  p_reviewed_by text,
  p_notes text
)
```

Comportamento:

```sql
update public.post_collection_failures
set
  status = 'unavailable',
  human_review_status = 'confirmed_unavailable',
  human_reviewed_at = now(),
  human_reviewed_by = p_reviewed_by,
  human_review_notes = coalesce(
    p_notes,
    'Confirmado manualmente no YouTube: video indisponivel.'
  )
where post_id = any(p_post_ids)
  and status in ('unavailable_candidate', 'unavailable');
```

Resultado esperado:

- retorna quantidade de linhas atualizadas
- nao altera posts fora de `post_collection_failures`
- nao apaga historico
- nao altera snapshots existentes

## Pseudofluxo Streamlit

```python
rows = load_unavailable_review()
edited = st.data_editor(
    rows,
    column_config={
        "selected": st.column_config.CheckboxColumn("Selecionar"),
        "youtube_url": st.column_config.LinkColumn("YouTube"),
    },
)

selected_ids = edited.loc[edited["selected"], "post_id"].tolist()

if st.button("Confirmar selecionados como unavailable"):
    if not selected_ids:
        st.warning("Selecione ao menos um video.")
    else:
        result = supabase.rpc(
            "confirm_unavailable_posts",
            {
                "p_post_ids": selected_ids,
                "p_reviewed_by": reviewed_by,
                "p_notes": notes,
            },
        ).execute()
        st.success(f"{len(selected_ids)} videos confirmados.")
```

## Validacoes obrigatorias

Antes de considerar a tela pronta:

- confirmar que os links abrem corretamente
- confirmar que apenas linhas selecionadas sao atualizadas
- confirmar que registros ja `confirmed_unavailable` nao precisam aparecer por padrao
- confirmar que videos confirmados saem de `v_post_update_queue_batch`
- confirmar que a view de auditoria continua mostrando historico de revisao
- confirmar que a tela nao usa `SUPABASE_SERVICE_ROLE_KEY`

## Evolucao futura

Esta pagina pode receber outras acoes de sanitizacao no futuro, desde que
sigam o mesmo principio:

- lista concreta de itens
- selecao explicita
- update controlado
- auditoria humana registrada

Exemplos possiveis, se forem formalizados depois:

- reclassificacao de casos ambíguos
- marcacao de itens revisados como disponiveis novamente
- saneamento manual de residuos operacionais

## Decisao recomendada

Implementar a primeira versao com:

- links clicaveis, nao abertura automatica no Edge
- selecao explicita por checkbox
- confirmacao via RPC
- logs visuais no proprio dashboard
- filtro padrao para pendentes de revisao humana

Essa versao resolve a dor operacional sem criar dependencia do ambiente local
do usuario e mantem o processo auditavel.
