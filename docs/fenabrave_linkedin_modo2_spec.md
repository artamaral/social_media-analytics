# Fenabrave / LinkedIn — Especificação (Modo 2: script na VPS + sync externo)

**Projeto:** Bugiga_Bot  
**Rotina:** Fenabrave/LinkedIn  
**Arquivo:** `spec.md`  
**Modo recomendado:** Modo 2 — script na VPS + sync externo

## 1. Objetivo

Gerar o post mensal Fenabrave para LinkedIn (autos + comerciais leves, foco em varejo) e entregar a versão final para Telegram via Hermes.

## 2. Premissas de execução (restrições)

- Não rodar `git fetch/pull/reset` dentro do prompt do cron.
- Não usar repositório local desatualizado se houver mecanismo de sync autorizado via HTTP/raw/conector.
- O cron deve executar em UMA rotina (uma única execução), com fluxo determinístico para dados e LLM apenas para redação.

## 3. Modo 2 (recomendado): script na VPS

### 3.1. Onde ficam os scripts

- O ETL/script de download, extração e cálculo fica na VPS (ex.: `/opt/venv/...` ou `/opt/hermes/fenabrave_etl/`).

### 3.2. Sync do script (fora do prompt, via etapas determinísticas)

- A rotina cron deve primeiro atualizar o script ETL na VPS por **sync HTTP raw** (ou conector autorizado que copie arquivos para a VPS), apontando para a **branch/ref ativa configurada na execução do Hermes**.
- O prompt NÃO executa `git`.

### 3.3. Se sync falhar

Parar a rotina com erro operacional claro, informando:

1. qual permissão/conector está faltando (ex.: acesso HTTP raw ao GitHub / autenticação para acessar endpoint),
2. em qual etapa parou (Etapa: Sync do script),
3. qual ação humana é necessária (ex.: habilitar conector/credencial autorizada para raw GitHub ou fornecer env autorizada).

## 4. Flow da rotina (uma execução)

### Etapa A — Sync

1. Baixar/atualizar o script ETL na VPS (atomicamente: tmp + rename).
2. Registrar `hash` do script baixado (opcional, mas recomendado para auditoria).

### Etapa B — ETL (sem LLM)

1. Definir período alvo:
   - `month_target` = mês anterior ao mês corrente (override opcional se fornecido).
2. Limitar escopo:
   - somente Autos + Comerciais Leves
   - foco em Varejo
   - não misturar outros segmentos.
3. Baixar dados oficiais da Fenabrave (fonte primária: página oficial de emplacamentos).
4. Extrair/calcular apenas métricas determinísticas necessárias para o Pacote de Fatos.
5. Gerar `pacote_fatos.json` no contrato mínimo (se algum dado obrigatório não existir, usar `null` e preencher `data_quality.missing_required_items`).

### Etapa C — LLM (apenas redação)

- LLM recebe somente:
  1. `pacote_fatos.json` (contrato mínimo e compacto)
  2. regras editoriais compactas (inclusas no pacote)
- A LLM deve produzir a saída final única (sem rascunhos intermediários):
  1. Post LinkedIn (curto, gancho forte, poucos bullets)
  2. Resumo técnico (fonte, período, escopo, limites, limitações por dados faltantes)

### Etapa D — Entrega

- Se Telegram estiver configurado: enviar a versão final.
- Se Telegram não estiver configurado: retornar a mensagem pronta para copiar incluindo exatamente:

```text
Telegram nao configurado ou nao disponivel nesta execucao.
```

## 5. Contrato mínimo — Pacote de Fatos (para reduzir tokens)

- Tamanho alvo do pacote: 5–10 KB (JSON compacto).
- Regras:
  - listas limitadas (Top N)
  - sem tabelas longas
  - se faltar dado obrigatório: `null` + registro em `data_quality.missing_required_items`.

### 5.1. Estrutura recomendada (JSON)

```json
{
  "meta": {
    "month_target": "YYYY-MM",
    "month_previous": "YYYY-MM",
    "year_previous_same_month": "YYYY-MM",
    "scope": "Autos + Comerciais Leves",
    "focus": "Varejo"
  },
  "totals": {
    "varejo_month_target": "<number|null>",
    "varejo_month_previous": "<number|null>",
    "delta_varejo_abs": "<number|null>",
    "delta_varejo_pct": "<number|null>"
  },
  "mix": {
    "varejo_share_pct": "<number|null>",
    "direct_share_pct": "<number|null>"
  },
  "top_brands": [
    { "brand": "string", "month_target_varejo": "<number|null>" }
  ],
  "top_models": [
    { "model": "string", "brand": "string", "month_target_varejo": "<number|null>" }
  ],
  "ytd": {
    "varejo_ytd_month_target_year": "<number|null>",
    "varejo_ytd_prev_year_equivalent": "<number|null>"
  },
  "rule_10pct": {
    "discrepancy_10pct_triggered": "<boolean>",
    "same_month_prev_year_varejo_total": "<number|null>",
    "delta_pct_vs_same_month_prev_year": "<number|null>"
  },
  "data_quality": {
    "missing_required_items": ["string", "..."]
  },
  "editorial_rules": {
    "recorte": "Autos + Comerciais Leves; foco em Varejo",
    "comparacoes": [
      "month_target vs month_previous",
      "ytd vs ytd equivalente do ano anterior",
      "rule_10pct: se discrepância >=10%, comentar vs mesmo mês do ano anterior",
      "mix: venda direta vs varejo"
    ],
    "restricoes": [
      "não citar elétricos/híbridos a menos que apareçam nos tops",
      "não inventar números; se faltar dado obrigatório, declarar limitação",
      "tom não sensacionalista; poucos bullets; leitura executiva"
    ],
    "output_format": { "linkedin_bullets_max": 4 }
  }
}
```

> Observação: no JSON real, os placeholders `"<number|null>"` e `"<boolean>"` devem ser substituídos por valores JSON válidos, sem aspas quando forem numéricos, booleanos ou `null`.

### 5.2. Limites recomendados para listas

- `top_brands`: Top 3 (máx. 5)
- `top_models`: Top 5 (máx. 7)

## 6. Regras editoriais (devem estar no pacote)

- Recorte explícito: Autos + Comerciais Leves; foco em Varejo
- Comparações obrigatórias:
  - varejo `month_target` vs `month_previous`
  - acumulado do ano (YTD) vs equivalente do ano anterior
  - percentual venda direta vs varejo
  - se discrepância >=10%: comparar com mesmo mês do ano anterior
- Restrições:
  - Não mencionar elétricos/híbridos a menos que apareçam entre tops analisados
  - Não inventar números
  - Se dado obrigatório ausente: declarar limitação no resumo técnico

## 7. Critérios de qualidade (pré-entrega)

- Período correto: “mês anterior ao mês corrente”
- Fonte correta: Fenabrave (página oficial)
- Escopo correto: autos + comerciais leves; varejo
- Comparações obrigatórias presentes ou explicitamente limitadas por dados faltantes
- Post curto para LinkedIn; sem sensacionalismo; poucos bullets
