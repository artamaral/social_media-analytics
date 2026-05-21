# Proposta de layout futuro (referência visual enviada em 2026-05-20)

## Objetivo
Registrar a referência de UI enviada pelo time como **proposta futura** do dashboard e avaliar se é viável implementar com Streamlit + bibliotecas Python já usadas no repositório.

## Veredito de viabilidade
**Sim, é viável** implementar o layout proposto usando:
- `streamlit` (estrutura de páginas, colunas, containers, filtros e tabelas interativas);
- `plotly` (gráficos de linha, barras, rosca e sparklines);
- `pandas` (modelagem e transformação dos dados);
- CSS customizado injetado via `st.markdown(..., unsafe_allow_html=True)` para aproximar identidade visual (sidebar escura, cards, badges e tipografia).

Bibliotecas já presentes no projeto (`dashboard/requirements.txt`) cobrem praticamente tudo que aparece no mockup.

## Mapeamento do mockup para recursos técnicos

### 1) Sidebar fixa com navegação
- **Possível em Streamlit** com `st.sidebar` + controle de página por `radio/selectbox` (ou multipage nativo).
- Estilização escura e destaque do item ativo: possível via CSS customizado.

### 2) Barra superior com filtros globais
- **Possível** usando `st.columns` para distribuir filtros (`selectbox`, `multiselect`, `date_input`).
- Botões "Filtrar" e "Exportar": `st.button` + geração CSV em memória com `st.download_button`.

### 3) Cards de KPI (Overview e Creator Detail)
- **Possível** com `st.metric` ou cards HTML/CSS como já existe em `dashboard/streamlit_app.py`.
- Delta positivo/negativo e indicadores em cor: possível com lógica condicional e classes CSS.

### 4) Tabelas de ranking/outliers
- **Possível** com `st.dataframe` (ordenação, largura fluida, colunas configuradas).
- Paginação "estética" igual ao mockup não é nativa; opções:
  1. paginação lógica manual em pandas;
  2. componente customizado (maior esforço).

### 5) Gráficos de evolução, distribuição e tendências
- **Possível** com Plotly:
  - linhas multi-série (views/subscribers/engagement);
  - barras agrupadas;
  - pizza/rosca para distribuição;
  - mini sparklines para cards laterais.

### 6) Blocos de IA insights
- **Possível** como cards com prioridade/severidade (`success`, `warning`, `danger`) usando HTML/CSS.
- Botão "Gerar insights" pode acionar pipeline já existente no backend (ou placeholder inicial).

### 7) Data Health / qualidade de dados
- **Possível** com cards de status, percentuais e tabelas resumidas.
- Já existe base técnica no app atual para guardrail/posts mortos, reduzindo esforço inicial.

## Limitações práticas (não bloqueantes)
1. **Pixel-perfect** do mockup pode exigir iterações de CSS (Streamlit não é framework front-end livre como React).
2. Alguns comportamentos avançados (ex.: drag-and-drop complexo, paginação rica nativa, animações detalhadas) podem exigir componente customizado.
3. Consistência visual depende de padronizar tokens de design (cores, espaçamentos, tipografia) em um único bloco de tema.

## Estratégia recomendada de implementação

### Fase 1 — Estrutura visual (rápida)
- Implementar navegação lateral e páginas: Overview, Creator Ranking, Creator Detail, Content Analytics, Outliers, Niche Trends, AI Insights, Data Health.
- Criar tema base (cores, cards, tabela, filtros).
- Ligar dados reais apenas onde já houver view consolidada.

### Fase 2 — Componentes analíticos
- Construir KPIs e gráficos por página com Plotly.
- Incluir exportação CSV e estados de loading/empty/error.
- Padronizar formatação (número, %, variação por período).

### Fase 3 — Refino e escala
- Melhorar UX (responsividade, densidade, tooltips, performance).
- Introduzir componentes customizados apenas se houver gap crítico de UX.
- Definir baseline de performance e monitorar tempo de carregamento por página.

## Conclusão
A proposta é **tecnicamente factível** com o stack atual do projeto, sem necessidade obrigatória de trocar Streamlit nesta etapa. O principal cuidado é tratar o mockup como **guia visual** (alta fidelidade), e não como requisito de pixel-perfect imediato.


## Extração de métricas visíveis no mockup (por view)

Observação: os valores abaixo foram lidos visualmente da imagem de referência e devem ser tratados como **exemplo de layout**, não como contrato de negócio.

### View 1 — Overview
Métricas visíveis no cabeçalho:
- Creators Ativos: **285**
- Novos Vídeos: **124**
- Crescimento Médio: **+3.6 p.p.**
- Engajamento Médio: **3.2%**
- Creators em Aceleração: **28**
- Nicho em Alta: **Elétricos** com **+18.5%**

Blocos adicionais visíveis:
- Evolução temporal de Views, Subscribers, Vídeos e Engajamento.
- Lista “Top Movers (Crescimento de Views)”.
- Bloco “Insights Rápidos” com cards de trend/oportunidade/atenção.

### View 2 — Creator Ranking
Métricas e colunas visíveis:
- Tabela com creator, subnicho, subscribers, variação de views, engajamento, vídeos e score.
- Paginação no rodapé e filtro por período/plataforma/nicho/subnicho/tipo de creator.

### View 3 — Creator Detail
Métricas visíveis:
- Subscribers: **1.45M**
- Views Growth (30d): **+42.1%**
- Engajamento: **4.2%**
- Vídeos (30d): **8**
- Frequência: **1.1 vídeos/dia**
- “Desde”: **2012**

Blocos adicionais visíveis:
- Evolução de métricas por aba (Views/Conteúdo/Tendências/Audiência etc.).
- Top vídeos.
- Distribuição de conteúdo.
- Insights do creator (IA).

### View 4 — Content Analytics
Métricas/estrutura visível:
- Tabela de desempenho de conteúdo com colunas de growth, engajamento, outlier score e data.
- Filtros por subnicho/tipo de conteúdo/tipo de vídeo.

### View 5 — Outliers
Métricas/estrutura visível:
- Tabela com growth, esperado, outlier score e baseline por vídeo.
- Resumo com cards (ex.: “Outliers encontrados”, “Score médio”, “% acima do esperado”).

### View 6 — Niche Trends
Métricas visíveis:
- Tabela por subnicho com creators, vídeos, avg growth, engajamento e aceleração.
- Blocos laterais “Subnicho em Alta” (ex.: Elétricos +18.5%) e “Acelerando Mais”.

### View 7 — AI Insights
Estrutura visível:
- Cards de insights por categoria (tendência, oportunidade, alerta, recomendação).
- Bloco de “Resumo Executivo (IA)” e botão para gerar relatório.

### View 8 — Data Health
Métricas visíveis:
- Pipeline status (scraper/processamento/enriquecimento/agregações).
- Gaps de coleta (itens sem coleta e histórico).
- Qualidade dos dados com score geral (ex.: **92%**).
- Resumo de cobertura (creators, posts, registros, cobertura 30d).

## Alinhamento com a documentação atual

### Alinhado
- **Overview com KPIs e visão operacional** está alinhado ao MVP descrito no spec de dashboard (creators, posts, views, engajamento e status de qualidade). 
- **Creators/Ranking e Crescimento** estão alinhados com o escopo do MVP (comparativo de creators e crescimento semanal).
- **Data Health/Data Quality** está alinhado com a exigência de indicadores na tela inicial e com a direção de qualidade operacional.
- **Linguagem visual editorial** (sidebar escura, cards, contraste) está alinhada com a direção visual já documentada.

### Parcialmente alinhado (exige formalização extra)
- **AI Insights**: o spec atual descreve regras de uso de GPT no dashboard, mas o mockup adiciona produto visual mais completo (cards prontos, resumo executivo e fluxo de relatório). Deve virar item explícito de escopo funcional.
- **Niche Trends e Outliers dedicados**: há referência conceitual na documentação, porém o detalhamento de métricas/queries por página ainda precisa virar contrato de dados (views SQL e definições de campo).
- **Creator Detail avançado**: o mockup propõe uma profundidade analítica maior (top vídeos, distribuição, abas), acima do MVP inicial; recomenda-se fasear.

## Recomendação de ajuste documental
Para reduzir ambiguidade entre mockup e entrega técnica:
1. Atualizar o spec principal com uma tabela “Métrica -> definição -> view SQL -> periodicidade”.
2. Marcar explicitamente o que é **MVP** vs **fase 2/3** para cada uma das 8 views do mockup.
3. Fixar quais métricas são obrigatórias já na primeira versão (ex.: Data Quality principal, ranking creators, crescimento 7d).
