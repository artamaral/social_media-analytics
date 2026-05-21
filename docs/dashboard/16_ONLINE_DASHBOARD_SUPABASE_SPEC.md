# Dashboard analitico interno com Supabase e Streamlit

## Objetivo

Criar um sistema de visualizacao online para estudos de mercado automotivo, consumindo dados do Supabase sob demanda e sem copiar metricas para uma base paralela no MVP.

O dashboard, neste momento, nao tem objetivo de virar produto SaaS publico. Ele deve funcionar como uma bancada analitica interna para investigar creators, videos, crescimento, engajamento, nichos e qualidade da coleta.

## Principios

- O dashboard le dados agregados do Supabase em tempo de consulta.
- O app nunca expoe `SUPABASE_SERVICE_ROLE_KEY`.
- Toda consulta passa por views SQL, RPCs ou queries controladas.
- Toda analise visual deve exibir estado de qualidade dos dados antes dos rankings.
- O MVP prioriza estudo de mercado, exploracao analitica e confiabilidade dos dados antes de acabamento visual de produto.
- A evolucao esperada e aumentar fontes de dados e profundidade analitica, nao numero de acessos.

## Arquitetura recomendada

```text
Usuario
  -> Streamlit Community Cloud
  -> queries Python controladas
  -> Supabase views/RPCs
  -> tabelas analiticas e historico
```

## App online

Recomendacao para MVP:

- Streamlit Community Cloud
- Python
- Pandas para analises exploratorias
- Supabase Python client ou conexao Postgres read-only
- secrets gerenciados no proprio Streamlit Cloud
- cache de consultas com TTL curto para reduzir leituras repetidas

## Direcao visual

Referencia visual:

- dashboard com composicao editorial, sidebar escura, cards claros, cabecalhos escuros nos cards e acentos coral/salmao
- adaptar para um visual mais escuro que a referencia, usando escala de cinza no background geral
- manter o layout denso, organizado e funcional para analise de mercado, sem parecer landing page

Principios de layout:

- sidebar fixa escura para navegacao principal
- conteudo central em grid com cards de raio baixo
- cards de KPI no topo para leitura rapida
- area principal com graficos maiores e tabelas abaixo
- filtros na sidebar ou no topo, sempre compactos
- data quality deve aparecer como bloco visivel antes dos rankings

Paleta inicial:

- background geral: cinza escuro `#15171c`
- sidebar: grafite quase preto `#20212b`
- superficie de pagina: cinza medio escuro `#24272f`
- cards: cinza claro frio `#f4f6f7` quando o dado precisar de contraste
- cards escuros: `#2a2c36` para blocos operacionais
- texto principal em fundo escuro: `#f5f7fa`
- texto secundario em fundo escuro: `#aeb4bf`
- texto principal em cards claros: `#252733`
- acento principal: coral `#ff8069`
- acento positivo: verde suave `#98df96`
- alerta: amarelo queimado `#f2c14e`
- erro: vermelho coral `#ff6f61`

Pictos e icones:

- usar pictos sempre que ajudarem a leitura de secoes, KPIs e navegacao
- preferir icones lineares simples, inspirados em dashboard/editorial, com stroke consistente
- evitar excesso de emojis como linguagem principal da interface
- exemplos de pictos por area:
  - overview: gauge ou home
  - creators: user ou users
  - videos: play ou film
  - crescimento: trending-up
  - engajamento: heart ou message-circle
  - qualidade dos dados: shield-check ou alert-triangle
  - fila operacional: list-check ou refresh-cw
  - fontes externas: database ou table

Diretriz para Streamlit:

- usar `st.set_page_config(layout="wide")`
- aplicar CSS customizado para fundo, sidebar, cards e metricas
- usar componentes HTML leves para cards quando `st.metric` nao permitir controle visual suficiente
- evitar cards arredondados demais; raio alvo entre `6px` e `8px`
- manter tipografia condensada apenas em titulos curtos; textos analiticos devem ser legiveis
- usar graficos com fundo transparente ou cinza escuro, sem molduras pesadas
- reservar acento coral para highlights, selecao, icones e variacao positiva/negativa relevante

## Banco

Consumir preferencialmente:

- `v_dashboard_creator_summary`
- `v_dashboard_post_growth_7d`
- `v_dashboard_guardrail_coverage_status`
- `v_dashboard_dead_post_validation_status`
- `v_dashboard_unavailable_video_review`
- `v_dashboard_fenabrave_monthly_segments`

Essas views deixam o dashboard simples e evitam repetir logica analitica no app.

Para estudos mais exploratorios, o Streamlit pode complementar as views com Pandas, desde que nao carregue historico bruto sem filtros de periodo.

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

### 4. Qualidade operacional da fila

Objetivo:

- identificar videos que nao voltaram da YouTube API
- facilitar revisao humana sem depender de logs do Cloud Run
- evitar que posts indisponiveis fiquem presos no guardrail ou na fila normal

Componentes:

- tabela de `unavailable_candidate` e `unavailable`
- `post_id`
- `youtube_url` completa e clicavel
- `failure_count`
- `last_failure_reason`
- `first_failed_at` e `last_failed_at`
- `human_review_status`
- `human_review_notes`

View recomendada:

- `public.v_dashboard_unavailable_video_review`

Referencia tecnica:

- `docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`

### 5. Fenabrave

Objetivo:

- acompanhar emplacamentos mensais por categoria principal
- usar Fenabrave como leitura estruturada de mercado automotivo
- comparar categorias em blocos e em grafico mensal

Categorias iniciais:

- Autos
- Comerciais leves
- Caminhoes
- Onibus
- Motos
- Implementos rodoviarios

Componentes:

- seis blocos de consolidado por categoria
- picto por categoria inspirado no padrao visual da tabela Fenabrave
- valor mensal do ultimo periodo disponivel
- acumulado do ano por categoria
- grafico de barras mensal por categoria

View recomendada:

- `public.v_dashboard_fenabrave_monthly_segments`

## Consultas sob demanda

O MVP deve consultar o Supabase apenas quando:

- o usuario abre uma pagina
- altera filtros
- muda ordenacao ou periodo
- solicita refresh manual

Evitar:

- polling frequente sem necessidade
- carregar historico bruto sem filtros
- calcular crescimento linha a linha no app quando uma view SQL puder resolver
- consultas abertas sem limite de periodo

## Atualizacao de dados no Streamlit

Comportamento atual:

- o app nao faz polling automatico em intervalo fixo
- o app consulta o Supabase quando a pagina carrega ou quando o usuario interage com a interface
- as leituras usam cache do Streamlit com TTL inicial de `300` segundos
- dentro do TTL, o app tende a reutilizar o resultado em cache
- depois do TTL, a proxima interacao ou reload pode disparar nova leitura do Supabase
- as views SQL sao recalculadas pelo Supabase/Postgres no momento da consulta

Fluxo atual:

```text
Streamlit
  -> Supabase Python client
  -> PostgREST
  -> views SQL
  -> cache Streamlit por 300s
```

RPC:

- o app ainda nao usa RPC para as views atuais
- o acesso atual usa `client.table("nome_da_view").select("*").execute()`
- RPC deve ser considerada quando a consulta precisar de parametros complexos, regras de negocio encapsuladas, resposta muito customizada ou execucao transacional controlada

Quando considerar outro padrao:

- leitura simples de view pequena: manter `select` em view
- filtros simples em colunas expostas: usar view + filtros do Supabase client
- consulta parametrizada complexa: considerar RPC
- pergunta analitica ad hoc com GPT: gerar contexto controlado a partir de views permitidas, nao liberar SQL arbitrario no app
- necessidade de quase tempo real: avaliar botao manual de refresh antes de polling automatico

Diretriz:

- o dashboard deve priorizar refresh manual ou TTL curto em vez de polling continuo
- para uso interno de estudo de mercado, `300` segundos e um valor inicial aceitavel
- se uma pagina precisar de dados mais frescos, adicionar botao `Atualizar dados` para limpar cache e recarregar as views daquela pagina

## Seguranca

Regras obrigatorias:

- nunca expor `SUPABASE_SERVICE_ROLE_KEY`
- usar uma chave/usuario de leitura quando possivel
- guardar credenciais apenas em Streamlit secrets
- criar grants especificos para views consumidas pelo dashboard
- aplicar filtros de periodo e limites nas consultas de historico

## Data quality antes de analytics

O bloco de Data Quality do dashboard deve ter exatamente dois KPIs principais:

1. Legado guardrail
   - fonte: `v_dashboard_guardrail_coverage_status`
   - mede a cobertura minima descrita em `docs/social_media/25_MINIMUM_HISTORY_COVERAGE_GUARDRAIL_SPEC.md`
   - KPI principal: total de posts legados abaixo de 3 checagens
   - tabela obrigatoria por `intervalo_video`, `total_checagens` e `total_posts`
   - intervalos exibidos em portugues:
     - `Novos: 0 a 3 dias`
     - `Recentes: 4 a 7 dias`
     - `Em aquecimento: 8 a 30 dias`
     - `Legado: mais de 30 dias`

2. Posts mortos
   - fonte: `v_dashboard_dead_post_validation_status`
   - mede candidatos/confirmados como indisponiveis e se ja passaram por validacao humana
   - KPI principal: `pending_human_review`
   - contexto: `total_dead_posts`, `confirmed_unavailable`, `available_on_manual_check`, `unclear`

O dashboard deve exibir esses indicadores na tela inicial.

## Data quality operacional

Dentro de `Data quality`, o bloco de integridade operacional deve diferenciar os
2 workers do projeto:

- `Atualizacao de posts`
  - worker horario
  - foco em evidencias de novos snapshots em `post_metrics_history`
- `Descoberta de novos posts`
  - worker com execucao a cada 6 horas
  - foco em evidencias de novos posts encontrados pelo fluxo principal

Regra importante:

- a view `v_dashboard_worker_health_status` cobre apenas o worker de
  `Atualizacao de posts`
- a view `v_dashboard_new_post_discovery_status` cobre o worker de
  `Descoberta de novos posts`
- o segundo worker deve usar `posts.created_at` como evidencia de descoberta

Para o worker de `Atualizacao de posts`, o subtipo `Sinais operacionais` deve
priorizar KPIs de fluxo e risco de cobertura, nao volume bruto de lote:

- `itens_atrasados`
  - mede quantos posts ja passaram do `next_check` alem da tolerancia definida
  - responde se o worker horario esta conseguindo respeitar o agendamento
- `at_risk_bootstrap`
  - mede posts novos em risco de nao atingir cobertura minima no tempo esperado
  - antecipa degradacao antes de virar passivo consolidado
- `recovery_low`
  - mede posts mais antigos que ja ficaram abaixo da cobertura minima
  - representa falha de cobertura ja consumada

Sinais que nao devem ser KPI principal neste bloco:

- `fila_itens_prontos`
  - a view de lote continua desenhada para devolver `50` linhas e esse total
    nao representa bem a saude real do fluxo
- `falhas_recentes_24h`
  - sobrepoe a leitura ja coberta por `Posts mortos` e validacao humana

Leitura correta dos blocos:

- `Monitoramento de posts sem checagem`
  - mostra estoque e cobertura acumulada
- `Sinais operacionais`
  - mostra fluxo, atraso e risco de degradacao do worker horario
- `Posts mortos`
  - mostra indisponibilidade e validacao humana

## GPT dentro do dashboard

Se um GPT/assistente for implementado dentro do Streamlit, ele nao deve depender de "ler a tela" de forma implicita. O app deve montar explicitamente um pacote de contexto com os dados relevantes da pagina atual.

Contexto minimo recomendado:

- pagina atual
- filtros ativos
- periodo selecionado
- views consultadas
- linhas agregadas visiveis ou top N linhas relevantes
- definicoes de metricas usadas na pagina
- alertas de Data Quality ativos
- timestamp da ultima consulta

Fluxo recomendado:

```text
Usuario faz pergunta
  -> Streamlit captura pergunta + estado da pagina
  -> app monta context packet com dados ja carregados ou queries permitidas
  -> modelo recebe pergunta + contexto + regras do projeto
  -> resposta cita quais dados/views usou
```

Regra de seguranca:

- o GPT nao deve receber `SUPABASE_SERVICE_ROLE_KEY`
- o GPT nao deve executar SQL arbitrario diretamente contra o banco
- perguntas devem ser respondidas com base em views aprovadas ou funcoes/RPCs controladas
- quando faltar dado, o GPT deve dizer que a view atual nao cobre a pergunta

Exemplo de context packet:

```json
{
  "page": "Data quality",
  "filters": {
    "period": "current",
    "platform": "youtube"
  },
  "views": [
    "v_dashboard_guardrail_coverage_status",
    "v_dashboard_dead_post_validation_status"
  ],
  "data_quality": {
    "guardrail_rows": [],
    "dead_post_status": {}
  },
  "last_refreshed_at": "2026-05-19T23:39:00Z"
}
```

Quando usar dados carregados vs nova consulta:

- se a pergunta for sobre o que esta visivel na pagina, usar o contexto ja carregado
- se a pergunta pedir comparacao ou filtro nao carregado, usar uma view/RPC permitida
- se a pergunta exigir dado inexistente, registrar como nova necessidade analitica em backlog

## Roadmap tecnico

### Fase 1 - Base analitica

- criar views SQL de consumo
- criar view de revisao de videos indisponiveis com URL completa
- criar views de resumo para guardrail legado e posts mortos
- criar indices para `post_metrics_history`
- validar data quality
- documentar contrato dos dados

### Fase 2 - App Streamlit MVP

- criar app Streamlit
- configurar secrets do Supabase
- implementar overview, creators e crescimento semanal
- publicar no Streamlit Community Cloud

### Fase 3 - Estudos avancados

- filtros por nicho e subnicho
- curvas temporais por creator
- deteccao de outliers
- comparativo entre creators
- exportacao CSV
- analises por fonte de dados adicional

## Stack recomendada

Escolha padrao:

- Streamlit Community Cloud
- Python
- Pandas
- Supabase Python client ou psycopg
- Plotly ou Altair para graficos

Motivo:

- deploy online simples e gratuito
- baixa complexidade de manutencao
- adequado para poucos acessos e muita exploracao analitica
- permite iterar rapidamente novas perguntas de mercado
- combina bem com SQL, Pandas e estudos automotivos por creator/video

## Alternativa futura

Se o dashboard deixar de ser ferramenta interna e passar a ser produto para terceiros, reavaliar:

- Next.js
- TypeScript
- Supabase JS
- Tailwind CSS
- Recharts ou Tremor

Essa alternativa deve ser tratada como evolucao de produto, nao como prioridade atual.

## Criterio de pronto do MVP

- app online acessivel por URL
- nenhum segredo exposto no codigo ou no navegador
- overview mostra qualidade dos dados
- ranking de creators funcionando
- ranking de crescimento semanal funcionando
- revisao de videos indisponiveis disponivel por view com URL clicavel
- queries respondem sem leitura excessiva do historico
- limitacao conhecida de frescor dos dados documentada
- identidade visual aplicada com fundo em escala de cinza, sidebar escura, cards contrastados e pictos consistentes
