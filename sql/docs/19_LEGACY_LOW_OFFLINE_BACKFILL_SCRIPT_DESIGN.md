# LEGACY LOW OFFLINE BACKFILL SCRIPT DESIGN

## Objetivo

Detalhar o desenho do script offline da fase 1 do backfill para `legacy_low`,
mantendo o maximo possivel de proximidade com
`scripts/cloud_run/postMetrics/main.py`.

Este documento nao representa codigo implementado.

Ele existe para orientar a implementacao com:

- mesma estrutura mental do pipeline atual
- baixo risco de divergencia
- funcoes pequenas e reutilizaveis
- comportamento previsivel

---

## Principio de implementacao

O script offline deve ser tratado como uma variante controlada do
`postMetrics/main.py`.

Em vez de criar um pipeline totalmente novo, a ideia e:

- manter as funcoes de integracao com Supabase
- manter a chamada da YouTube API
- manter a normalizacao
- manter o insert em `post_metrics_history`
- trocar apenas a origem dos `post_id`

No pipeline online:

- a origem e `v_post_update_queue_batch`

No backfill offline:

- a origem e a query de selecao de `legacy_low`

---

## Fluxo esperado

```text
1. Carregar configuracao e headers
2. Buscar lote de legacy_low
3. Extrair post_ids
4. Buscar estatisticas na YouTube API
5. Normalizar resposta
6. Inserir snapshots em post_metrics_history
7. Registrar logs finais
```

---

## Estrutura sugerida do script

```python
import os
import requests
from datetime import datetime, UTC
```

---

## Configuracao global

```python
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
```

### Comentario

Esta parte deve permanecer praticamente identica ao `postMetrics/main.py`.

Motivo:

- reduz variacao desnecessaria
- evita erro de autenticacao diferente entre scripts
- padroniza a integracao com Supabase

---

## Funcao 1. `fetch_legacy_low_batch()`

### Papel

Substituir a funcao `fetch_queue()` do pipeline online.

Em vez de buscar `v_post_update_queue_batch`, esta funcao deve buscar o lote de
`legacy_low` ordenado por `priority_score_v2`.

### Assinatura sugerida

```python
def fetch_legacy_low_batch(batch_size=50):
```

### Responsabilidade

- consultar o Supabase
- executar a selecao dos `legacy_low`
- devolver as linhas do lote

### Comentario detalhado

Esta funcao e o coracao da diferenca entre o pipeline online e o offline.

Tudo o que vem depois dela pode continuar quase igual ao `postMetrics`.

Ela deve:

- aplicar o criterio de elegibilidade legado
- ordenar por `priority_score_v2 desc`
- respeitar o `batch_size`
- retornar estrutura simples, com pelo menos `post_id`

### Query conceitual

```sql
select
  p.post_id,
  p.created_at,
  p.collected_at,
  coalesce(h.total_checagens, 0) as total_checagens,
  f.priority_score_v2,
  f.history_level
from posts p
left join (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h on h.post_id = p.post_id
join public.v_post_priority_score_features_v2 f
  on f.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(h.total_checagens, 0) <= 1
order by
  f.priority_score_v2 desc,
  coalesce(h.total_checagens, 0) asc,
  p.collected_at asc nulls first,
  p.post_id
limit 50;
```

### Observacoes de implementacao

- Pode ser implementada via endpoint REST do Supabase sobre uma view dedicada.
- Se a query ficar muito complexa para REST puro, vale criar uma view SQL de
  apoio apenas para leitura analitica do backfill.
- O retorno ideal deve ser uma lista de objetos contendo ao menos `post_id`.

---

## Funcao 2. `extract_ids()`

### Papel

Reaproveitar diretamente a mesma funcao do `postMetrics/main.py`.

### Assinatura

```python
def extract_ids(rows):
```

### Comentario detalhado

Esta funcao deve continuar extremamente simples:

- recebe as linhas retornadas pela selecao do lote
- devolve apenas a lista de `post_id`

Ela e importante porque isola um contrato:

- etapa de selecao pode devolver objetos ricos
- etapa de chamada da API do YouTube precisa so dos IDs

### Implementacao esperada

```python
def extract_ids(rows):
    return [r["post_id"] for r in rows]
```

### Motivo para manter igual

- facilita copiar a estrutura atual
- reduz superficie de mudanca
- mantem previsibilidade

---

## Funcao 3. `fetch_youtube_stats()`

### Papel

Reaproveitar a mesma logica do `postMetrics/main.py` para consultar
`videos.list`.

### Assinatura

```python
def fetch_youtube_stats(video_ids):
```

### Comentario detalhado

Esta funcao deve continuar igual ou quase igual ao pipeline online.

Ela deve:

- montar a chamada para `https://www.googleapis.com/youtube/v3/videos`
- enviar multiplos IDs em uma unica request
- pedir `part=statistics`
- validar `status_code`
- devolver a lista `items`

### Motivo para reuso

- a integracao com a API do YouTube ja esta validada
- o comportamento esperado ja e conhecido em producao
- reduz o risco de introduzir bugs em uma parte que ja funciona

### Observacao operacional

Se houver IDs invalidos ou posts removidos:

- a funcao pode receber menos itens do que IDs enviados
- isso nao deve quebrar o pipeline
- o script deve apenas registrar a diferenca em log

---

## Funcao 4. `normalize()`

### Papel

Transformar a resposta da YouTube API no payload esperado por
`post_metrics_history`.

### Assinatura

```python
def normalize(items):
```

### Comentario detalhado

Esta funcao deve continuar muito proxima da atual.

Ela deve:

- iterar sobre os `items` da API
- ler `statistics`
- montar um dicionario padronizado por post
- atribuir `collected_at = datetime.now(UTC).isoformat()`

### Contrato de saida

Cada item normalizado deve conter:

- `post_id`
- `views`
- `likes`
- `comments`
- `collected_at`

### Motivo para manter igual

- o banco e os triggers ja esperam esse formato
- evita bifurcar o contrato de historico
- deixa o offline compativel com o online

### Observacao

Esta funcao nao deve:

- calcular score
- decidir banda
- atualizar fila

Essas regras continuam no banco.

---

## Funcao 5. `insert_history()`

### Papel

Inserir os registros normalizados em `post_metrics_history`.

### Assinatura

```python
def insert_history(records):
```

### Comentario detalhado

Esta funcao tambem deve ser reaproveitada diretamente do `postMetrics`.

Ela deve:

- fazer `POST` em `/rest/v1/post_metrics_history`
- enviar o lote de registros normalizados
- registrar status HTTP
- logar resposta em caso de erro

### Motivo para manter igual

- o efeito colateral desejado ja esta estabelecido
- ao inserir no historico, os triggers cuidam de:
  - atualizar `posts`
  - atualizar `post_update_queue`

### Regra importante

O script offline nao deve duplicar o que o banco ja faz.

Ou seja:

- nada de update manual em `posts`
- nada de update manual em `post_update_queue`

---

## Funcao 6. `run_backfill_batch()`

### Papel

Orquestrar uma execucao unica do lote offline.

### Assinatura sugerida

```python
def run_backfill_batch(batch_size=50):
```

### Comentario detalhado

Esta funcao e o equivalente offline do `run_pipeline()`.

Fluxo esperado:

1. buscar lote `legacy_low`
2. abortar se nao houver itens
3. extrair IDs
4. chamar YouTube API
5. abortar se nao houver resposta util
6. normalizar
7. inserir historico
8. logar total processado

### Responsabilidade

Ela deve coordenar o fluxo, nao concentrar regras de negocio.

As regras de negocio devem continuar distribuidas assim:

- elegibilidade do lote: query de selecao
- coleta: `fetch_youtube_stats()`
- formato de historico: `normalize()`
- atualizacao estrutural: triggers do banco

---

## Funcao 7. `run()`

### Papel

Oferecer um entrypoint simples para execucao local ou controlada.

### Assinatura sugerida

```python
def run():
```

### Comentario detalhado

Como o script e offline, ele nao precisa seguir exatamente o mesmo contrato HTTP
do Cloud Run.

Mas vale manter um entrypoint pequeno e padronizado:

- log de inicio
- `try/except`
- chamada de `run_backfill_batch()`
- log final de sucesso ou erro

Se no futuro o script for adaptado para job controlado:

- esse entrypoint pode ser facilmente ajustado

---

## Esqueleto sugerido

```python
import os
import requests
from datetime import datetime, UTC

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


def fetch_legacy_low_batch(batch_size=50):
    # Busca apenas posts legacy_low, ordenados por priority_score_v2.
    # Esta e a unica troca estrutural relevante em relacao ao postMetrics.
    pass


def extract_ids(rows):
    # Mantem a mesma responsabilidade do pipeline online:
    # isolar somente os post_ids que serao enviados para a YouTube API.
    return [r["post_id"] for r in rows]


def fetch_youtube_stats(video_ids):
    # Reaproveita a mesma logica do postMetrics:
    # uma unica chamada ao endpoint videos.list com multiplos IDs.
    pass


def normalize(items):
    # Traduz a resposta da API para o contrato aceito por post_metrics_history.
    pass


def insert_history(records):
    # Insere snapshots no historico e deixa os triggers atualizarem
    # posts e post_update_queue.
    pass


def run_backfill_batch(batch_size=50):
    # Orquestra uma rodada completa do backfill offline.
    pass


def run():
    # Entry point simples para execucao manual/controlada.
    pass
```

---

## Logs recomendados

Cada rodada deve registrar:

- `batch_size` solicitado
- quantidade retornada por `fetch_legacy_low_batch()`
- quantidade de IDs enviados para YouTube
- quantidade de itens retornados pela API
- quantidade de registros inseridos
- duracao total
- lista de IDs faltantes, se houver discrepancia

---

## Pontos de cuidado

### 1. IDs enviados versus itens retornados

A YouTube API pode nao devolver todos os IDs enviados.

O script deve:

- aceitar isso sem falhar por completo
- registrar quais IDs nao voltaram

### 2. Reexecucao segura

Como a fase 1 so tenta semear historico, pode haver reexecucao de lote por erro
operacional.

Por isso, vale considerar:

- reconsultar `legacy_low` a cada rodada
- nao depender de lista fixa salva fora do banco

### 3. Nao competir com o pipeline principal

Mesmo sendo offline, o script deve ser usado em janelas controladas.

Ele nao deve:

- rodar continuamente
- disputar volume com a coleta normal

---

## Decisao de arquitetura

Para esta fase, a implementacao recomendada e:

- criar um script proprio para backfill offline
- mas com o maximo de reuso estrutural do `postMetrics/main.py`

Em termos praticos:

- mesma integracao
- mesma coleta
- mesma persistencia
- nova selecao de lote

---

## Status

Este documento detalha o desenho recomendado do script offline de fase 1 para
`legacy_low`.

O proximo passo natural e transformar este desenho em implementacao Python no
repositorio.
