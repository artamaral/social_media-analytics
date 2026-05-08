# Online dashboard Supabase spec

## Objetivo

Criar um sistema de visualizacao online para transformar o projeto em uma plataforma de analytics automotivo, consumindo dados do Supabase sob demanda e sem copiar metricas para uma base paralela no MVP.

## Principios

- O dashboard le dados agregados do Supabase em tempo de consulta.
- O frontend nunca usa service role key.
- Toda consulta publica passa por views, RPCs ou API backend com escopo controlado.
- Toda analise visual deve exibir estado de qualidade dos dados antes dos rankings.
- O MVP prioriza crescimento, engajamento e confiabilidade operacional antes de graficos avancados.

## Arquitetura recomendada

```text
Usuario
  -> app web online
  -> camada de API/server actions
  -> Supabase views/RPCs
  -> tabelas analiticas e historico
```

### Frontend

Recomendacao para MVP:

- Next.js hospedado na Vercel ou Cloud Run
- Supabase JS client para consultas read-only
- Server-side rendering para paginas principais
- Revalidacao curta ou cache por rota para reduzir custo de leitura

### Banco

Consumir preferencialmente:

- `v_dashboard_creator_summary`
- `v_dashboard_post_growth_7d`
- `v_dashboard_data_quality_status`

Essas views deixam o dashboard simples e evitam repetir logica analitica no frontend.

## MVP de telas

### 1. Overview

Objetivo:

- mostrar se o sistema esta confiavel para analise
- resumir volume total de creators, posts, views e engajamento

Componentes:

- status de qualidade dos dados
- total de creators ativos
- total de posts monitorados
- total de views atuais
- media de engagement rate

### 2. Creators

Objetivo:

- comparar creators automotivos monitorados
- identificar quem merece acompanhamento comercial ou editorial

Componentes:

- ranking por views totais
- ranking por engagement rate
- posts monitorados por creator
- ultima coleta conhecida
- filtro por plataforma

### 3. Crescimento semanal

Objetivo:

- identificar videos com tracao recente
- separar volume absoluto de crescimento real

Componentes:

- ranking de delta de views em 7 dias
- crescimento percentual em 7 dias
- likes e comentarios incrementais
- link ou identificador do video
- creator associado

## Consultas sob demanda

O MVP deve consultar o Supabase apenas quando:

- o usuario abre uma pagina
- altera filtros
- muda ordenacao ou periodo
- solicita refresh manual

Evitar:

- polling frequente sem necessidade
- carregar historico bruto no navegador
- calcular crescimento no frontend linha a linha

## Segurança

Regras obrigatorias:

- usar anon key somente com RLS e permissoes de leitura controladas
- nunca expor `SUPABASE_SERVICE_ROLE_KEY` no browser
- criar grants especificos para views publicaveis
- se dados forem sensiveis, rotear tudo por backend autenticado

## Data quality antes de analytics

Antes de liberar rankings como sinal de negocio, validar:

- posts sem historico
- posts com `collected_at` nulo
- posts sem atualizacao nas ultimas 24h
- creators sem posts

O dashboard deve exibir esses indicadores na tela inicial.

## Roadmap tecnico

### Fase 1 - Base analitica

- criar views SQL de consumo
- criar indices para `post_metrics_history`
- validar data quality
- documentar contrato dos dados

### Fase 2 - App online MVP

- criar app web
- configurar Supabase read-only
- implementar overview, creators e crescimento semanal
- publicar em ambiente online

### Fase 3 - Produto analytics

- filtros por nicho e subnicho
- curvas temporais por creator
- deteccao de outliers
- comparativo entre creators
- exportacao CSV

## Stack recomendada

Escolha padrao:

- Next.js
- TypeScript
- Supabase JS
- Tailwind CSS
- Recharts ou Tremor para graficos

Motivo:

- deploy online simples
- boa integracao com Supabase
- facilidade para evoluir de dashboard para produto
- possibilidade de proteger consultas no server side

## Criterio de pronto do MVP

- app online acessivel por URL
- nenhum segredo exposto no frontend
- overview mostra qualidade dos dados
- ranking de creators funcionando
- ranking de crescimento semanal funcionando
- queries respondem sem leitura excessiva do historico
- limitacao conhecida de frescor dos dados documentada
