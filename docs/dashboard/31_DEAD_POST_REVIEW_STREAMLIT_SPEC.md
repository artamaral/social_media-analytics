# Dead post review no Streamlit

## Objetivo

Criar uma tela operacional no dashboard Streamlit para revisar videos que a
YouTube API deixou de retornar, confirmar manualmente dead posts e registrar a
decisao no Supabase sem depender de SQL manual recorrente.

Esta tela deve apoiar o processo ja documentado em
`docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`.

## Resumo da atividade

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
4. confirmar selecionados como dead/unavailable via botao
5. registrar auditoria humana no banco

## Escopo

Incluido:

- tela Streamlit para revisar dead posts
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

## Observacoes importantes

### Abrir todos no MS Edge

Em ambiente local seria possivel tentar abrir URLs no navegador padrao via
codigo Python local. No Streamlit Cloud isso nao funciona como esperado,
porque o app roda no servidor e nao no Windows do usuario.

Por isso, a decisao recomendada e:

- usar links clicaveis na tabela
- permitir que o usuario abra cada video em nova aba
- opcionalmente gerar uma lista de links selecionados para abertura manual
- evitar automacao que dependa de MS Edge local

Essa abordagem e mais simples, portavel e compativel com Streamlit Cloud.

### Selecao por checkbox

A confirmacao nao deve ser feita automaticamente para todos os itens da view.
O usuario deve selecionar explicitamente os videos revisados.

Motivo:

- evita confirmar como dead um video que voltou a ficar disponivel
- cria uma etapa humana clara
- reduz risco de update em massa acidental
- mantém auditabilidade por `human_reviewed_by`, `human_reviewed_at` e notas

## Fonte de dados

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

### Layout

Nome sugerido da pagina:

```text
Sanitizacao Operacional
```

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
- confirmar que registros ja `confirmed_unavailable` nao precisam aparecer por
  padrao
- confirmar que videos confirmados saem de `v_post_update_queue_batch`
- confirmar que a view de auditoria continua mostrando historico de revisao
- confirmar que a tela nao usa `SUPABASE_SERVICE_ROLE_KEY`

## Riscos

- abrir muitas abas de uma vez pode ser bloqueado pelo navegador
- update em massa sem checkbox pode confirmar videos errados
- usar service role no Streamlit pode expor permissao sensivel
- chamar SQL direto no app dificulta auditoria e reuso

## Decisao recomendada

Implementar a primeira versao com:

- links clicaveis, nao abertura automatica no Edge
- selecao explicita por checkbox
- confirmacao via RPC
- logs visuais no proprio dashboard
- filtro padrao para pendentes de revisao humana

Essa versao resolve a dor operacional sem criar dependencia do ambiente local
do usuario e mantem o processo auditavel.
