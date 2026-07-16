# Proposta de Layout Futuro do Streamlit

Referencia visual registrada a partir do mockup enviado em 2026-05-20.

Este documento pertence a branch `codex/dashboard-streamlit-mvp` enquanto a
proposta visual ainda nao estiver implementada como contrato estavel. Ele deve
ir para a `main` somente quando deixar de ser ideia de design e virar contrato
real do dashboard.

## Objetivo

Registrar a direcao visual futura do dashboard e organizar a implementacao de
forma faseada, usando o stack atual:

- `streamlit` para estrutura de paginas, navegacao, filtros e tabelas
- `plotly` para graficos de barras, linhas, rosca e series temporais
- `pandas` para transformacao e modelagem dos dados no app
- CSS customizado via `st.markdown(..., unsafe_allow_html=True)` para
  aproximar a identidade visual

## Veredito de Viabilidade

E viavel seguir a direcao do mockup com Streamlit, desde que ele seja tratado
como referencia de alta fidelidade, e nao como requisito pixel-perfect
imediato.

O stack atual ja cobre o necessario para:

- sidebar escura
- cards de KPI
- grids visuais
- filtros globais
- tabelas interativas
- graficos com Plotly
- estados de erro, vazio e conexao
- blocos futuros de insights

## Limitacoes Praticas

- Streamlit nao oferece liberdade total de layout como React.
- CSS global precisa ser controlado para nao afetar componentes nativos.
- Paginacao rica, animacoes e interacoes complexas podem exigir componentes
  customizados.
- Algumas paginas do mockup ainda dependem de contratos SQL adicionais ou de
  evolucao de metricas que nao fazem parte do estado atual do app.

## Mapeamento do Mockup

### 1. Sidebar Fixa

Viavel com `st.sidebar` e navegacao por `radio` ou multipage nativo.

Uso recomendado agora:

- manter navegacao simples
- destacar apenas paginas com dado real ou placeholder explicito
- evitar excesso de paginas antes dos contratos SQL

### 2. Barra Superior com Filtros

Viavel com `st.columns`, `selectbox`, `multiselect`, `date_input` e botoes.

Uso recomendado agora:

- filtros por pagina, nao uma barra global ainda
- filtros globais so quando mais de uma pagina usar o mesmo periodo ou nicho

### 3. Cards de KPI

Viavel com HTML e CSS customizado, ja iniciado no app atual.

Uso recomendado agora:

- criar helper unico para cards
- padronizar titulo, valor, legenda, picto e cor
- evitar HTML duplicado por pagina

### 4. Tabelas de Ranking e Outliers

Viavel com `st.dataframe`.

Uso recomendado agora:

- usar tabelas nativas
- formatar colunas
- adiar paginacao customizada

### 5. Graficos

Viavel com Plotly.

Uso recomendado agora:

- criar funcao comum de tema Plotly
- aplicar fundo, fonte, grid e margens de forma consistente
- nao repetir `fig.update_layout` em cada pagina

### 6. Blocos de IA Insights

Viavel, mas fora do MVP visual imediato.

Pre-condicoes:

- definir quais views podem alimentar o contexto
- impedir SQL arbitrario
- montar `context packet` por pagina
- registrar data de referencia e filtros usados

### 7. Data Health

Viavel e ja alinhado ao app atual.

Contrato inicial:

- `v_dashboard_guardrail_coverage_status`
- `v_dashboard_dead_post_validation_status`

## Metricas Visiveis no Mockup

Os valores abaixo foram lidos visualmente da referencia e sao exemplos de
layout, nao contrato de negocio.

### Overview

- creators ativos
- novos videos
- crescimento medio
- engajamento medio
- creators em aceleracao
- nicho em alta
- evolucao temporal
- top movers
- insights rapidos

### Creator Ranking

- creator
- subnicho
- subscribers
- variacao de views
- engajamento
- videos
- score

### Creator Detail

- subscribers
- crescimento de views
- engajamento
- videos no periodo
- frequencia
- desde quando o creator existe
- top videos
- distribuicao de conteudo

### Content Analytics

- desempenho por conteudo
- growth
- engajamento
- outlier score
- data

### Outliers

- growth observado
- valor esperado
- outlier score
- baseline por video

### Niche Trends

- creators por subnicho
- videos
- crescimento medio
- engajamento
- aceleracao

### AI Insights

- tendencia
- oportunidade
- alerta
- recomendacao
- resumo executivo

### Data Health

- status de pipeline
- gaps de coleta
- qualidade dos dados
- cobertura por creators, posts e historico

## Alinhamento com a Documentacao Atual

### Alinhado

- Overview com KPIs e visao operacional
- ranking de creators e crescimento semanal
- Data Quality antes de analises fortes
- linguagem visual escura, com cards e pictos
- uso de Supabase sob demanda
- `Hot now` como ranking separado da logica operacional da fila

### Parcialmente Alinhado

- AI Insights ainda precisa virar escopo funcional
- Niche Trends e Outliers precisam de contrato SQL
- Creator Detail avancado esta acima do MVP atual

## Plano de Implementacao Proposto

### Decisao de Escopo

Implementar primeiro uma base visual reutilizavel e paginas conectadas apenas
quando ja existir view SQL estavel.

Nao implementar ainda:

- AI Insights completo
- Creator Detail avancado
- Niche Trends completo
- Outliers dedicado
- paginacao customizada
- componentes Streamlit customizados

Esses itens dependem de contrato de dados, definicao de metricas e validacao de
valor analitico antes de virar UI.

## Fase 0 - Preparacao Visual

Objetivo:

- criar uma base visual consistente para todas as paginas atuais
- reduzir HTML e CSS duplicado no app
- aproximar o layout do mockup sem buscar pixel-perfect

Tarefas:

- criar helpers de UI para titulo, subtitulo, card, grid, secao, estado vazio
  e aviso de erro
- centralizar tokens de design no bloco de tema
- padronizar estilo Plotly
- revisar a sidebar atual e manter navegacao controlada
- aplicar os helpers em `Overview`, `Data quality` e `Fenabrave`

Criterio de pronto:

- paginas atuais usam os mesmos componentes base
- nao ha HTML renderizado como texto
- app compila sem erro
- layout nao quebra em desktop estreito
- nao ha mudanca de SQL

## Fase 1 - MVP Visual Conectado

Objetivo:

- transformar o app atual em uma primeira experiencia navegavel com dados reais

Paginas no escopo:

1. `Overview`
   - KPIs de Data Quality
   - bloco Fenabrave resumido
   - placeholders explicitos apenas onde ainda nao houver leitura consolidada

2. `Data quality`
   - KPI guardrail legado
   - KPI posts mortos e validacao
   - tabelas brutas das views atuais

3. `Fenabrave`
   - blocos por categoria
   - seletor de mes
   - acumulado do ano sempre baseado no ultimo mes disponivel
   - grafico de barras mensal por categoria

4. `Sanitizacao operacional`
   - tabela de videos indisponiveis baseada em
     `v_dashboard_unavailable_video_review`

Views usadas:

- `v_dashboard_guardrail_coverage_status`
- `v_dashboard_dead_post_validation_status`
- `v_dashboard_fenabrave_monthly_segments`
- `v_dashboard_unavailable_video_review`

Criterio de pronto:

- toda pagina do MVP consome apenas views aprovadas
- erros de secrets ou view aparecem como aviso amigavel
- carregamento usa cache com TTL documentado
- nao ha escrita no Supabase

Direcionamento atualizado para `Overview`:

- a home nao deve abrir com `Data Quality` como mensagem principal
- `Overview` deve priorizar grandes numeros da base monitorada, cobertura geral,
  atividade recente em janela curta e estado macro da operacao
- `Data Quality` continua importante, mas deve entrar como contexto secundario,
  CTA ou pagina dedicada
- evitar totais que possam sugerir cobertura integral de todos os videos de
  cada creator quando a base monitorada nao representa o universo completo

## Fase 2 - Analytics Social Media

Objetivo:

- consolidar as telas sociais sobre contratos SQL ja existentes e priorizar as
  evolucoes que ainda sao de UX, leitura e acabamento

Paginas no escopo:

1. `Creators`
   - ranking de creators
   - subscribers, views e posts quando disponiveis
   - filtros simples

2. `Videos em crescimento`
   - ranking por crescimento 7d
   - link do video
   - creator
   - views atuais e delta

3. `Hot now`
   - usar `v_dashboard_hot_now` no contrato `Hot now 24h`
   - separar velocidade analitica da logica operacional da fila

Views usadas:

- `v_dashboard_creator_summary`
- `v_dashboard_post_growth_7d`
- `v_dashboard_hot_now`

Criterio de pronto:

- cada tabela tem ordenacao padrao
- numeros sao formatados consistentemente
- filtros nao disparam consultas desnecessarias
- Data Quality segue visivel antes de conclusoes analiticas fortes

Leitura de status desta fase:

- `v_dashboard_post_growth_7d` ja sustenta `YouTube > Melhores videos 7d`
- `v_dashboard_hot_now` ja foi criada e ligada ao Streamlit
- as proximas iteracoes nao devem tratar essas views como pendentes de criacao,
  e sim como base entregue para refinamento visual e analitico

## Fase 3 - Mockup Avancado

Objetivo:

- aproximar as telas restantes do mockup depois de provar valor no MVP

Itens candidatos:

- Creator Detail
- Content Analytics
- Outliers
- Niche Trends
- AI Insights
- exportacao CSV por pagina
- resumo executivo gerado por GPT com `context packet`

Pre-condicao:

- cada pagina deve ter contrato de dados documentado antes da implementacao
- nenhuma pagina deve depender de SQL arbitrario gerado pelo app
- prompts e contextos de GPT devem citar views usadas e data de referencia

## Ordem Recomendada de Execucao Imediata

1. Refatorar componentes visuais comuns no `dashboard/streamlit_app.py`.
2. Ajustar `Overview` para usar os componentes e mostrar somente blocos reais.
3. Padronizar `Data quality` com os mesmos cards e tabelas.
4. Manter `Fenabrave` como primeira pagina de referencia visual conectada.
5. Consolidar `Sanitizacao operacional` e demais telas sociais no mesmo padrao
   visual.
6. Depois disso, priorizar evolucoes de `Creators`, `Videos em crescimento` e
   `Hot now` sem reabrir a discussao de views ja entregues.

## Regra de Controle

Nao criar pagina nova apenas porque ela existe no mockup.

Criar pagina nova somente quando pelo menos uma destas condicoes for verdadeira:

- a view SQL ja existe e foi validada
- a pagina e necessaria para validar uma view em desenvolvimento
- a pagina e um placeholder temporario explicitamente marcado como pendente

## Primeiro Pacote de Implementacao

Commit alvo:

```text
refactor(dashboard): padroniza componentes visuais
```

Arquivos provaveis:

- `dashboard/streamlit_app.py`
- `docs/dashboard/30_FUTURE_LAYOUT_PROPOSAL_STREAMLIT.md`

Resultado esperado:

- base visual mais limpa
- menos duplicacao
- componentes prontos para receber as proximas views
- nenhuma mudanca de banco
