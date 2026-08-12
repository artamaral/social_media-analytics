# Fenabrave packet RPC e fluxo mensal GPT

Data: 2026-08-12

## Objetivo

Consolidar um contrato canonico de leitura mensal da Fenabrave para clientes
GPT, usando o GitHub como fonte oficial das skills repo-specific e o Supabase
como fonte oficial dos dados, sem depender de Hermes, VPS ou SQL bruto no
cliente.

O contrato deve devolver um `packet` em `jsonb` diretamente do Supabase,
pronto para uso editorial em `ChatGPT Work`, Codex ou outra interface
online/mobile.

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
- skills repo-specific em `.agents/skills/`
- skill coordenadora mensal para analise + post LinkedIn

Fora desta entrega:

- job agendado
- persistencia de packet em tabela dedicada
- automacao mensal sem validacao previa do uso manual/assistido

## Arquitetura operacional

Fonte de verdade das skills:

- repositorio GitHub `artamaral/social_media-analytics`
- diretorio repo-specific `.agents/skills/`

Fonte de verdade dos dados:

- projeto Supabase `Proj_mktDigital`
- RPC canonica `public.get_fenabrave_monthly_packet(...)`

Regras:

- o cliente GPT deve chamar apenas a RPC
- o cliente GPT nao deve consultar tabelas Fenabrave brutas
- skills nao devem conter credenciais, tokens nem qualquer segredo
- o plugin/conector Supabase autenticado deve ser tratado como mecanismo de
  leitura; se o ambiente nao expuser um identificador confiavel para declarar
  dependencia em `agents/openai.yaml`, a skill deve documentar essa limitacao e
  nao inventar configuracao

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

## Skills do fluxo

Skills repo-specific do fluxo:

- `.agents/skills/fenabrave-monthly-source`
- `.agents/skills/linkedin-automotive-posts`
- `.agents/skills/fenabrave-monthly-linkedin`

Papeis:

- `fenabrave-monthly-source`
  - confirma periodo, escopo, fonte e contrato do packet
- `linkedin-automotive-posts`
  - aplica a persona e as regras editoriais automotivas
- `fenabrave-monthly-linkedin`
  - coordena a chamada da RPC, valida o packet, produz leitura executiva e
    redige o post final

Mudancas estruturais:

- remocao do fluxo centrado em Hermes
- adocao de handoff por packet RPC
- runbook `monthly-packet-runbook.md`
- novo contrato de saida em `output-contract.md`
- alinhamento do tom editorial ao packet vindo do Supabase

## Estado atual da entrega

Preparado no repositorio:

- DDL da RPC em
  `sql/ddl/functions/009_create_fenabrave_monthly_packet_rpc.sql`
- teste estrutural em
  `sql/ddl/tests/012_test_fenabrave_monthly_packet_rpc.sql`
- skills atualizadas para consumo `packet-first`
- skill coordenadora mensal em `.agents/skills/fenabrave-monthly-linkedin`

Aplicado e validado:

- a RPC foi aplicada no projeto `Proj_mktDigital`
- a leitura real confirmou `status = ok` para `2026-07-01` nos escopos:
  - `autos`
  - `comerciais_leves`
  - `autos_comerciais_leves`

Ainda pendente para considerar fechado como fluxo operacional completo:

- validar descoberta repo-specific das tres skills no caminho `.agents/skills/`
- confirmar em cliente GPT com plugin/conector Supabase autenticado
- manter a automacao mensal como etapa posterior, depois da validacao manual
  assistida
