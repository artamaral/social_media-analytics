---
name: fenabrave-monthly-source
description: Locate and validate the official Fenabrave monthly emplacamentos source for recurring automotive-market workflows. Use when Hermes or Codex needs the Fenabrave website, monthly PDF/download page, source URL, reference period, or provenance rules before ingesting data or writing monthly LinkedIn posts based on Fenabrave rankings.
---

# Fenabrave Monthly Source

## Overview

Use this skill before monthly Fenabrave ingestion or monthly LinkedIn post generation. It gives Hermes a stable starting point for finding the official Fenabrave emplacamentos page so the user does not need to provide the site every month. Hermes should run with access to this repository so it can read `.codex/skills/`, `AGENTS.md`, and the project documentation before executing the workflow.

## Official source

Primary page for monthly emplacamentos:

```text
https://www.fenabrave.org.br/Portal/conteudo/emplacamentos
Known project source-page fallback used in existing ingestion metadata:

https://www.fenabrave.org.br/portalv2/Conteudo/Emplacamentos%20
Treat the Fenabrave page as the source of truth for the monthly file. Use mirrors, news sites, or reposted PDFs only as a last resort and clearly mark them as non-official support links.

Monthly workflow for Hermes
Run after the 5th business day of the month, targeting the previous reference month.

Open the official Fenabrave emplacamentos page.

Find the latest month in the expected year block.

Prefer the official Download link for the PDF over Leia/reader links.

Capture both:

source_page_url: the official Fenabrave emplacamentos page;

source_url: the direct PDF/download URL when available.

Confirm that the PDF title, cover, or first page matches the intended reference month.

Filter the analytical scope to autos + comerciais leves (LCV) only. Do not include motorcycles, trucks, buses, implements, or total-market aggregates unless the user explicitly asks for them.

Extract the monthly analysis packet with these mandatory cuts:

retail sales (varejo) for the month versus month -1;

brand performance in retail for the month versus month -1;

top-selling cars/models in autos + LCV;

year-to-date autos + LCV versus the same accumulated period in the previous year;

percentage split between direct sales and retail sales.

If a key movement shows a discrepancy around or above 10%, add the same month of the previous year comparison (mes/ano versus mes/ano -1) before drawing conclusions.

Record provenance before any post is written: source name, reference month, retrieval date, source page URL, direct file URL, and any caveat.

Use linkedin-automotive-posts only after the source period and data points are explicit.

Safety rules
Do not guess a PDF URL pattern when the official page does not show the month yet.

Do not publish a monthly post using Fenabrave data without a confirmed reference month.

Do not mix months in the same post unless the comparison is part of the mandatory month vs month -1, accumulated year vs prior accumulated year, or discrepancy check against the same month of the previous year.

If the official page is unavailable, say that the official source could not be confirmed and stop before drafting definitive claims.

One-off Hermes call
For a one-time preview run, Hermes may be invoked with this intent: generate the monthly Fenabrave LinkedIn draft using the mandatory autos + LCV packet and deliver the final message to the user's Telegram. If a Telegram connector is not configured, return the final post plus a Telegram-ready message and state that automatic delivery requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID or an equivalent connector.

Handoff to the LinkedIn skill
Pass a compact packet to linkedin-automotive-posts:

Fonte: Fenabrave
Periodo: <mes/ano>
source_page_url: <url da pagina oficial>
source_url: <url do PDF/download>
Dados principais: <autos + LCV; varejo mes vs mes -1; marcas no varejo mes vs mes -1; tops modelos; acumulado ano vs acumulado ano anterior; % venda direta vs % varejo; comparacao mes/ano vs mes/ano -1 quando discrepancia >= ~10%>
Limites: emplacamento e proxy de mercado; dados sujeitos ao escopo do informe Fenabrave
Objetivo editorial: post mensal para LinkedIn em tom humanizado de analista de marketing automotivo

---

### Observação importante sobre o bloco acima

Como esse arquivo contém blocos internos de markdown com crases triplas, se você copiar pelo GitHub, garanta que o conteúdo comece exatamente em:

```text
---
name: fenabrave-monthly-source
