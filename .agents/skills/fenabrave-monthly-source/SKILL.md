---
name: fenabrave-monthly-source
description: Locate and validate the official Fenabrave monthly emplacamentos source and the canonical Supabase packet contract for recurring automotive-market workflows. Use when Codex or ChatGPT Work needs the Fenabrave source provenance, reference period, supported scope, or packet fields before calling `get_fenabrave_monthly_packet(...)` or writing monthly analysis/posts based on Fenabrave rankings.
---

# Fenabrave Monthly Source

## Overview

Use this skill before monthly Fenabrave analysis or monthly LinkedIn post generation. The preferred operational flow is packet-first: the GPT client should call the canonical Supabase RPC `public.get_fenabrave_monthly_packet(reference_period, scope)` and use the official Fenabrave page/PDF only as provenance and audit support.

## Official source

Primary page for monthly emplacamentos:

```text
https://www.fenabrave.org.br/Portal/conteudo/emplacamentos
```

Known project source-page fallback used in existing ingestion metadata:

```text
https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos%20
```

Treat the Fenabrave page as the source of truth for the monthly file. Use mirrors, news sites, or reposted PDFs only as a last resort and clearly mark them as non-official support links.

## Preferred packet-first workflow

1. Resolve the requested `reference_period`.
2. Resolve the requested `scope`:
   - `autos`
   - `comerciais_leves`
   - `autos_comerciais_leves`
3. Call `public.get_fenabrave_monthly_packet(reference_period, scope)`.
4. If the packet returns `status != ok`, stop before drafting definitive claims.
5. Use `source_page_url` and `source_url` from the packet as provenance in the final analysis.
6. Use `linkedin-automotive-posts` only after the packet is explicit and usable.

Expected packet coverage:

- totals for the selected month and previous month
- direct versus retail split and delta versus month -1
- brand share in total market for the selected scope
- brand share in retail and direct for the selected scope
- top 5 vehicles in each relevant category for:
  - overall
  - retail
  - direct
- electrified summary and rankings when the validated data layer supports them

Editorial reading rules:

- When `scope = autos_comerciais_leves`, analyze `autos` and `comerciais leves` separately where model leadership differs.
- Do not include motorcycles, trucks, buses, implements, or broader total-market aggregates unless the user explicitly asks for them.
- Mention electrified highlights only when the packet includes them.

## Fallback provenance workflow

Use this only when the packet is unavailable or under validation:

1. Open the official Fenabrave emplacamentos page.
2. Find the latest month in the expected year block.
3. Prefer the official Download link for the PDF over Leia/reader links.
4. Capture both:
   - `source_page_url`: the official Fenabrave emplacamentos page
   - `source_url`: the direct PDF/download URL when available
5. Confirm that the PDF title, cover, or first page matches the intended reference month.
6. Confirm that the packet/RPC remains the preferred analysis source and the PDF is only provenance support.

## Safety rules

- Do not guess a PDF URL pattern when the official page does not show the month yet.
- Do not publish a monthly post using Fenabrave data without a confirmed reference month.
- Do not mix months in the same post unless the comparison is part of the packet or an explicit editorial comparison.
- If the canonical RPC is unavailable and the official page cannot be confirmed, stop before drafting definitive claims.
- Do not reconstruct the packet with ad-hoc raw SQL on the GPT client side. Prefer only the canonical RPC.

## Handoff to the LinkedIn skill

Pass a compact packet to `linkedin-automotive-posts`:

```text
Fonte: Fenabrave
Periodo: <mes/ano>
source_page_url: <url da pagina oficial>
source_url: <url do PDF/download>
Escopo: <autos | comerciais_leves | autos_comerciais_leves>
Packet RPC: <public.get_fenabrave_monthly_packet(...)>
Dados principais: <totais; varejo vs direta; share por marca; top 5 overall/varejo/direta; eletrificados quando disponivel>
Limites: emplacamento e proxy de mercado; dados sujeitos ao escopo do informe Fenabrave
Objetivo editorial: post mensal para LinkedIn em tom humanizado de analista de marketing automotivo
```

Use [monthly-packet-runbook.md](references/monthly-packet-runbook.md) when the task needs the operational sequence, input contract, or plugin-facing guidance for the direct packet flow.
