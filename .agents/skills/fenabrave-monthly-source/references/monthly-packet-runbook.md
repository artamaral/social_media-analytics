# Runbook mensal packet-first - Fenabrave para analise GPT

## Objetivo

Permitir que um cliente GPT online/mobile consuma o packet mensal Fenabrave diretamente da RPC canonica do Supabase e gere analise ou redacao sem depender de Hermes, VPS ou SQL bruto no cliente.

## Frequencia recomendada

Executar sob demanda apos o 5o dia util, sempre olhando para o mes anterior salvo quando o usuario pedir outro periodo.

## Entrada minima

- `reference_period`
- `scope`
  - `autos`
  - `comerciais_leves`
  - `autos_comerciais_leves`

## Contrato minimo da chamada

Chamar apenas:

```text
public.get_fenabrave_monthly_packet(reference_period, scope)
```

Nao consultar tabelas Fenabrave brutas nem reconstruir joins no cliente.

## Saida esperada para a analise

O packet deve entregar no minimo:

| Campo | Obrigatorio | Observacao |
| --- | --- | --- |
| `status` | Sim | `ok`, `not_available`, `invalid_scope` ou `invalid_request`. |
| `source_name` | Sim | Usar `Fenabrave`. |
| `reference_period` | Sim | Mes e ano normalizados. |
| `scope` | Sim | Escopo efetivo da leitura. |
| `source_page_url` | Sim | Pagina oficial de emplacamentos Fenabrave. |
| `source_url` | Sim | Link oficial do PDF/download quando disponivel. |
| `totals` | Sim | Total do mes, mes anterior e variacao. |
| `channel_mix` | Sim | Venda direta, varejo e delta versus mes anterior. |
| `brand_share_total` | Sim | Share consolidado por marca no escopo. |
| `brand_share_retail` | Sim | Share por marca no varejo. |
| `brand_share_direct` | Sim | Share por marca na venda direta. |
| `model_leaders` | Sim | Top 5 por categoria/canal conforme o escopo. |
| `electrified` | Sim | Resumo e rankings quando a camada validada suportar. |
| `editorial_notes` | Sim | Alertas de proxy de mercado, causalidade e escopo. |

## Sequencia operacional

1. Confirmar periodo alvo.
2. Confirmar escopo editorial.
3. Chamar a RPC canonica.
4. Verificar `status`.
5. Se `status = ok`, usar apenas os campos do packet para a analise.
6. Se `status != ok`, parar antes de redigir conclusoes definitivas.
7. Passar o packet para `linkedin-automotive-posts` quando a tarefa for redacao.

## Criterios de bloqueio

Nao gerar analise definitiva quando:

- o packet retornar `status != ok`
- o escopo pedido nao existir na RPC
- faltarem `source_page_url` ou `source_url`
- os blocos essenciais `totals`, `channel_mix` ou `model_leaders` vierem indisponiveis para o escopo solicitado

## Checklist minimo

- O cliente GPT consegue chamar `get_fenabrave_monthly_packet`.
- O cliente GPT nao precisa de SQL bruto.
- O packet chega com JSON estavel para o mesmo `(reference_period, scope)`.
- A skill `linkedin-automotive-posts` recebe o packet e nao inventa dados fora dele.
