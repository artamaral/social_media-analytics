# Fenabrave packet RPC para analise GPT

Data: 2026-08-12

## Objetivo

Criar um contrato canonico de leitura mensal da Fenabrave para clientes GPT,
sem depender de Hermes, VPS, SQL bruto no cliente ou montagem manual de JSON.

O contrato deve devolver um `packet` em `jsonb` diretamente do Supabase,
pronto para uso editorial em `ChatGPT Work` ou outra interface online/mobile.

## Escopo desta entrega

- RPC canonica `public.get_fenabrave_monthly_packet(date, text)`
- leitura direta da camada validada da Fenabrave no Supabase
- suporte a:
  - `autos`
  - `comerciais_leves`
  - `autos_comerciais_leves`
- cobertura de eletrificados quando a camada validada suportar
- top `5` veiculos por categoria/canal relevante
- ajustes das skills editoriais para fluxo `packet-first`

Fora desta entrega:

- job agendado
- persistencia de packet em tabela dedicada
- plugin/chat connector real do `ChatGPT Work`
- deploy automatico da RPC no Supabase

## Contrato da RPC

Assinatura:

```sql
public.get_fenabrave_monthly_packet(
  p_reference_period date,
  p_scope text default 'autos_comerciais_leves'
) returns jsonb
```

Regras:

- o cliente GPT deve chamar apenas essa RPC
- o cliente GPT nao deve consultar tabelas Fenabrave brutas
- o packet deve ser deterministico para o mesmo `reference_period + scope`
- o `scope` aceito nesta versao e:
  - `autos`
  - `comerciais_leves`
  - `autos_comerciais_leves`

Status esperados:

- `ok`
- `not_available`
- `invalid_scope`
- `invalid_request`

## Blocos obrigatorios do packet

```json
{
  "status": "ok",
  "source_name": "Fenabrave",
  "reference_period": "2026-07",
  "scope": "autos_comerciais_leves",
  "source_page_url": "",
  "source_url": "",
  "retrieved_from_db_at": "",
  "totals": {},
  "channel_mix": {},
  "brand_share_total": [],
  "brand_share_retail": [],
  "brand_share_direct": [],
  "model_leaders": {},
  "electrified": {},
  "editorial_notes": {}
}
```

Leitura esperada de cada bloco:

- `totals`
  - total do mes
  - total do mes anterior
  - variacao mensal
- `channel_mix`
  - share de `varejo`
  - share de `venda_direta`
  - delta em pontos percentuais versus o mes anterior
- `brand_share_total`
  - share consolidado por marca para o escopo principal
- `brand_share_retail`
  - share por marca no varejo para o escopo principal
- `brand_share_direct`
  - share por marca na venda direta para o escopo principal
- `model_leaders`
  - top `5` em:
    - geral
    - varejo
    - venda direta
- `electrified`
  - resumo mensal por powertrain/categoria
  - ranking por marca quando houver
  - ranking por modelo somente quando houver dado validado
- `editorial_notes`
  - alertas de proxy, causalidade e escopo

## Comportamento por escopo

### `autos`

- totals e channel mix focados em `automoveis`
- top `5` de `autos` para:
  - geral
  - varejo
  - venda direta
- eletrificados apenas de `autos`

### `comerciais_leves`

- totals e channel mix focados em `comerciais_leves`
- top `5` de `comerciais_leves` para:
  - geral
  - varejo
  - venda direta
- eletrificados apenas de `comerciais_leves`

### `autos_comerciais_leves`

- totals e channel mix do consolidado `autos + comerciais leves`
- liderancas separadas por categoria em `model_leaders`
- eletrificados separados por categoria

## Fontes de dados esperadas

A RPC foi desenhada para ler apenas a camada validada ja existente:

- `v_market_registration_segment_summary`
- `v_market_fenabrave_sales_channel_mix`
- `v_market_fenabrave_brand_rankings`
- `v_market_fenabrave_model_rankings`
- `v_market_fenabrave_electrified_registrations`
- `market_source_files`
- `market_data_sources`

## Skills ajustadas

Skills afetadas nesta entrega:

- `codex/skills/fenabrave-monthly-source`
- `codex/skills/linkedin-automotive-posts`

Mudancas:

- remocao do fluxo centrado em Hermes
- adocao de handoff por packet RPC
- runbook novo `monthly-packet-runbook.md`
- alinhamento do tom editorial ao packet vindo do Supabase

## Estado atual da entrega

Preparado no repositorio:

- DDL da RPC em
  `sql/ddl/functions/009_create_fenabrave_monthly_packet_rpc.sql`
- teste estrutural em
  `sql/ddl/tests/012_test_fenabrave_monthly_packet_rpc.sql`
- skills atualizadas para consumo `packet-first`

Ainda pendente para considerar operacional:

- aplicar a DDL no Supabase
- rodar a bateria de validacao no banco real
- confirmar respostas vivas para `2026-07`
- conectar o cliente GPT online/mobile com permissao minima apenas nessa RPC
