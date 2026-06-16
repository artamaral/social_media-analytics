# Proposta de Layout Futuro do Streamlit

Referência visual registrada a partir do mockup enviado em 2026-05-20.

Este documento pertence à branch `codex/dashboard-streamlit-mvp` enquanto a proposta visual ainda não estiver implementada. Ele deve ir para a `main` somente quando deixar de ser ideia de design e virar contrato real do dashboard.

## Objetivo

Registrar a direção visual futura do dashboard e organizar a implementação de forma faseada, usando o stack atual:

- `streamlit` para estrutura de páginas, navegação, filtros e tabelas
- `plotly` para gráficos de barras, linhas, rosca e séries temporais
- `pandas` para transformação e modelagem dos dados no app
- CSS customizado via `st.markdown(..., unsafe_allow_html=True)` para aproximar a identidade visual

## Veredito de Viabilidade

É viável seguir a direção do mockup com Streamlit, desde que ele seja tratado como referência de alta fidelidade, não como requisito pixel-perfect imediato.

O stack atual já cobre o necessário para:

- sidebar escura
- cards de KPI
- grids visuais
- filtros globais
- tabelas interativas
- gráficos com Plotly
- estados de erro, vazio e conexão
- blocos futuros de insights

## Limitações Práticas

- Streamlit não oferece liberdade total de layout como React.
- CSS global precisa ser controlado para não afetar componentes nativos.
- Paginação rica, animações e interações complexas podem exigir componentes customizados.
- Algumas páginas do mockup dependem de views SQL que ainda não existem.

## Mapeamento do Mockup

### 1. Sidebar Fixa

Viável com `st.sidebar` e navegação por `radio` ou multipage nativo.

Uso recomendado agora:

- manter navegação simples
- destacar apenas páginas com dado real ou placeholder explícito
- evitar excesso de páginas antes dos contratos SQL

### 2. Barra Superior com Filtros

Viável com `st.columns`, `selectbox`, `multiselect`, `date_input` e botões.

Uso recomendado agora:

- filtros por página, não uma barra global ainda
- filtros globais só quando mais de uma página usar o mesmo período/nicho

### 3. Cards de KPI

Viável com HTML/CSS customizado, já iniciado no app atual.

Uso recomendado agora:

- criar helper único para cards
- padronizar título, valor, legenda, picto e cor
- evitar HTML duplicado por página

### 4. Tabelas de Ranking e Outliers

Viável com `st.dataframe`.

Uso recomendado agora:

- usar tabelas nativas
- formatar colunas
- adiar paginação customizada

### 5. Gráficos

Viável com Plotly.

Uso recomendado agora:

- criar função comum de tema Plotly
- aplicar fundo, fonte, grid e margens de forma consistente
- não repetir `fig.update_layout` em cada página

### 6. Blocos de IA Insights

Viável, mas fora do MVP visual imediato.

Pré-condições:

- definir quais views podem alimentar o contexto
- impedir SQL arbitrário
- montar `context packet` por página
- registrar data de referência e filtros usados

### 7. Data Health

Viável e já alinhado ao app atual.

Contrato inicial:

- `v_dashboard_guardrail_coverage_status`
- `v_dashboard_dead_post_validation_status`

## Métricas Visíveis no Mockup

Os valores abaixo foram lidos visualmente da referência e são exemplos de layout, não contrato de negócio.

### Overview

- Creators ativos
- Novos vídeos
- Crescimento médio
- Engajamento médio
- Creators em aceleração
- Nicho em alta
- evolução temporal
- top movers
- insights rápidos

### Creator Ranking

- creator
- subnicho
- subscribers
- variação de views
- engajamento
- vídeos
- score

### Creator Detail

- subscribers
- crescimento de views
- engajamento
- vídeos no período
- frequência
- desde quando o creator existe
- top vídeos
- distribuição de conteúdo

### Content Analytics

- desempenho por conteúdo
- growth
- engajamento
- outlier score
- data

### Outliers

- growth observado
- valor esperado
- outlier score
- baseline por vídeo

### Niche Trends

- creators por subnicho
- vídeos
- crescimento médio
- engajamento
- aceleração

### AI Insights

- tendência
- oportunidade
- alerta
- recomendação
- resumo executivo

### Data Health

- status de pipeline
- gaps de coleta
- qualidade dos dados
- cobertura por creators/posts/histórico

## Alinhamento com a Documentação Atual

### Alinhado

- Overview com KPIs e visão operacional
- Ranking de creators e crescimento semanal
- Data Quality antes de análises fortes
- linguagem visual escura, com cards e pictos
- uso de Supabase sob demanda

### Parcialmente Alinhado

- AI Insights ainda precisa virar escopo funcional.
- Niche Trends e Outliers precisam de contrato SQL.
- Creator Detail avançado está acima do MVP inicial.

## Plano de Implementação Proposto

### Decisão de Escopo

Implementar primeiro uma base visual reutilizável e páginas conectadas apenas quando já existir view SQL estável.

Não implementar ainda:

- AI Insights completo
- Creator Detail avançado
- Niche Trends completo
- Outliers dedicado
- paginação customizada
- componentes Streamlit customizados

Esses itens dependem de contrato de dados, definição de métricas e validação de valor analítico antes de virar UI.

## Fase 0 - Preparação Visual

Objetivo:

- criar uma base visual consistente para todas as páginas atuais
- reduzir HTML/CSS duplicado no app
- aproximar o layout do mockup sem buscar pixel-perfect

Tarefas:

- criar helpers de UI para título, subtítulo, card, grid, seção, estado vazio e aviso de erro
- centralizar tokens de design no bloco de tema
- padronizar estilo Plotly
- revisar a sidebar atual e manter navegação controlada
- aplicar os helpers em `Overview`, `Data quality` e `Fenabrave`

Critério de pronto:

- páginas atuais usam os mesmos componentes base
- não há HTML renderizado como texto
- app compila sem erro
- layout não quebra em desktop estreito
- não há mudança de SQL

## Fase 1 - MVP Visual Conectado

Objetivo:

- transformar o app atual em uma primeira experiência navegável com dados reais.

Páginas no escopo:

1. `Overview`
   - KPIs de Data Quality
   - bloco Fenabrave resumido
   - placeholders explícitos para creators e crescimento

2. `Data quality`
   - KPI guardrail legado
   - KPI posts mortos/validação
   - tabelas brutas das views atuais

3. `Fenabrave`
   - blocos por categoria
   - seletor de mês
   - acumulado do ano sempre baseado no último mês disponível
   - gráfico de barras mensal por categoria

4. `Sanitizacao operacional`
   - tabela de vídeos indisponíveis quando `v_dashboard_unavailable_video_review` estiver validada

Views usadas:

- `v_dashboard_guardrail_coverage_status`
- `v_dashboard_dead_post_validation_status`
- `v_dashboard_fenabrave_monthly_segments`
- `v_dashboard_unavailable_video_review`

Critério de pronto:

- toda página do MVP consome apenas views aprovadas
- erros de secrets/view aparecem como aviso amigável
- carregamento usa cache com TTL documentado
- não há escrita no Supabase

Direcionamento atualizado para `Overview`:

- a home nao deve abrir com `Data Quality` como mensagem principal
- `Overview` deve priorizar grandes numeros da base monitorada, cobertura geral,
  atividade recente em janela curta e estado macro da operacao
- `Data Quality` continua importante, mas deve entrar como contexto secundario,
  CTA ou pagina dedicada
- evitar totais que possam sugerir cobertura integral de todos os videos de cada
  creator quando a base monitorada nao representa o universo completo

## Fase 2 - Analytics Social Media

Objetivo:

- conectar telas de creators e vídeos depois de validar os contratos de dados.

Páginas no escopo:

1. `Creators`
   - ranking de creators
   - subscribers/views/posts quando disponíveis
   - filtros simples

2. `Vídeos em crescimento`
   - ranking por crescimento 7d
   - link do vídeo
   - creator
   - views atuais e delta

3. `Hot now`
   - somente após criação de `v_dashboard_hot_now`
   - separar velocidade analítica da lógica operacional da fila

Views usadas:

- `v_dashboard_creator_summary`
- `v_dashboard_post_growth_7d`
- `v_dashboard_hot_now` ainda pendente

Critério de pronto:

- cada tabela tem ordenação padrão
- números são formatados consistentemente
- filtros não disparam consultas desnecessárias
- Data Quality segue visível antes de conclusões analíticas fortes

## Fase 3 - Mockup Avançado

Objetivo:

- aproximar as telas restantes do mockup depois de provar valor no MVP.

Itens candidatos:

- Creator Detail
- Content Analytics
- Outliers
- Niche Trends
- AI Insights
- exportação CSV por página
- resumo executivo gerado por GPT com `context packet`

Pré-condição:

- cada página deve ter contrato de dados documentado antes da implementação
- nenhuma página deve depender de SQL arbitrário gerado pelo app
- prompts/contextos de GPT devem citar views usadas e data de referência

## Ordem Recomendada de Execução Imediata

1. Refatorar componentes visuais comuns no `dashboard/streamlit_app.py`.
2. Ajustar `Overview` para usar os componentes e mostrar somente blocos reais.
3. Padronizar `Data quality` com os mesmos cards e tabelas.
4. Manter `Fenabrave` como primeira página de referência visual conectada.
5. Implementar `Sanitizacao operacional` com `v_dashboard_unavailable_video_review`.
6. Depois disso, iniciar `Creators` e `Vídeos em crescimento`.

## Regra de Controle

Não criar página nova apenas porque ela existe no mockup.

Criar página nova somente quando pelo menos uma destas condições for verdadeira:

- a view SQL já existe e foi validada
- a página é necessária para validar uma view em desenvolvimento
- a página é um placeholder temporário explicitamente marcado como pendente

## Primeiro Pacote de Implementação

Commit alvo:

```text
refactor(dashboard): padroniza componentes visuais
```

Arquivos prováveis:

- `dashboard/streamlit_app.py`
- `docs/dashboard/30_FUTURE_LAYOUT_PROPOSAL_STREAMLIT.md`

Resultado esperado:

- base visual mais limpa
- menos duplicação
- componentes prontos para receber as próximas views
- nenhuma mudança de banco
