# Streamlit dashboard execution plan

## Objetivo

Iniciar a fase de execucao do dashboard analitico interno do projeto, usando Streamlit Community Cloud e Supabase sob demanda.

O foco desta fase e entregar uma primeira versao online, segura e util para estudos de mercado automotivo, sem transformar o dashboard em produto SaaS publico.

## Premissas atuais

- O dashboard sera uma ferramenta interna de analise de mercado.
- O numero de acessos sera baixo.
- A complexidade deve crescer em fontes de dados, perguntas analiticas e profundidade das views.
- O Supabase continua sendo a fonte de dados principal.
- O app nao deve expor `SUPABASE_SERVICE_ROLE_KEY`.
- Rankings e graficos devem sempre considerar qualidade dos dados antes de gerar conclusoes.
- A identidade visual deve usar fundo em escala de cinza, sidebar escura, cards contrastados, acento coral e pictos.

## Etapa 0 - Pre-flight do repositorio

Objetivo:

- garantir que a base local esta organizada para iniciar o app sem misturar pipeline, SQL e UI.

Status do pre-flight em 2026-06-16:

- estrutura encontrada em `dashboard/`:
  - `streamlit_app.py`
  - `requirements.txt`
  - `README.md`
- estrutura recomendada ainda incompleta:
  - `.streamlit/config.toml` nao existe
  - `.streamlit/secrets.toml.example` nao existe
- o app ja deixou de ser placeholder puro:
  - `Overview` existe, mas ainda combina KPIs reais de Data Quality com blocos placeholder
  - `Creators` tem navegacao e layout reais, mas a visao geral ainda usa mock local
  - `Criador individual` ja consome `v_dashboard_creator_summary` e `v_dashboard_creator_weekly_activity`
  - `YouTube > Melhores videos 7d` deixa de ser placeholder e passa a consumir a `v_dashboard_post_growth_7d`
- views encontradas no repositorio para o MVP:
  - `v_dashboard_guardrail_coverage_status`
  - `v_dashboard_dead_post_validation_status`
  - `v_dashboard_creator_summary`
  - `v_dashboard_post_growth_7d`
  - `v_dashboard_unavailable_video_review`
  - `v_dashboard_fenabrave_monthly_segments`
  - apoio adicional ja disponivel para creators:
    - `v_dashboard_creator_weekly_timeseries`
    - `v_dashboard_creator_weekly_activity`
    - `v_dashboard_creator_weekly_audience`

Leitura do pre-flight:

- o repositorio esta apto para iniciar o Sprint 3 sem nova reorganizacao de pastas
- a principal lacuna nao e estrutural; e de consolidacao do app para trocar mocks/placeholders por views reais
- a ordem mais segura para o MVP continua:
  1. validar as views no Supabase
  2. fechar `Overview`
  3. trocar `Creators` para dados reais em toda a visao geral
  4. implementar `YouTube > Melhores videos 7d`

Definicoes atuais para `YouTube > Melhores videos 7d`:

- `Todos` mostra os `10` melhores videos no ranking geral
- `Long` mostra os `10` melhores videos `long`
- `Short` mostra os `10` melhores videos `short`
- a janela nao deve incluir o dia atual parcial
- a leitura oficial da tela deve usar `7` dias completos fechados
- a implementacao da `v_dashboard_post_growth_7d` deve excluir o dia atual pela data local de `America/Sao_Paulo`
- regra final da janela na view: converter `collected_at` de UTC para `America/Sao_Paulo` e filtrar `::date >= (now() at time zone 'America/Sao_Paulo')::date - 7` e `::date < (now() at time zone 'America/Sao_Paulo')::date`
- a janela precisa aparecer claramente na interface
- a ordenacao continua por crescimento de views em `7d`
- a ordenacao oficial deve vir da consulta no Supabase com `order by views_growth_pct_7d desc`
- o Streamlit nao deve reordenar todas as linhas em memoria; ele deve apenas aplicar o filtro `Todos`, `Long` ou `Short` na consulta e pedir o `top 10`
- a exibicao de `views`, `likes` e `comentarios` deve usar os valores absolutos do ultimo snapshot
- a tela deve mostrar `ultimo snapshot` e `quantidade de snapshots` da janela
- ponto em aberto: a regra fina de desempate do ranking permanece provisoria e deve ser rechecada apos avaliacao visual da tela em uso real
- causa raiz resolvida: o Supabase estava em `UTC`, enquanto a regra de negocio era lida em `America/Sao_Paulo`; a versao anterior da view usava `date_trunc('day', now())` e deixava entrar snapshots que ainda eram "hoje" no Brasil
- validacao observada: depois do ajuste final por data local de `America/Sao_Paulo`, posts de ontem puxados apenas por snapshot de hoje deixaram de aparecer na tela

Evidencia operacional da correcao:

- `current_setting('TIMEZONE')` no Supabase retornou `UTC`
- um caso real do video `_B7xWH5n8UI` ainda aparecia com `latest_collected_at = 2026-06-18 10:00:11.782639`
- isso provou que a versao anterior da view ainda aceitava snapshots de "hoje" quando o corte era calculado apenas pelo dia UTC do banco
- a correcao definitiva passou a filtrar pela data local de `America/Sao_Paulo` aplicada ao proprio `collected_at`

Definicao de negocio para engajamento:

- para leitura de negocio no dashboard, `engajamento` representa o quanto a
  audiencia reagiu ao conteudo proporcionalmente ao total de views
- em termos executivos, ele responde menos a pergunta "quem teve mais volume?"
  e mais a pergunta "quem conseguiu fazer uma parcela maior da propria
  audiencia interagir?"
- a formula oficial usada hoje nas views comparativas e no criador individual e:
  `((likes + comments) / views) * 100`
- interpretacao pratica:
  - videos ou creators com muito volume podem ter engajamento baixo se a maior
    parte da audiencia assistir sem reagir
  - videos ou creators menores podem ter engajamento alto se conseguirem gerar
    mais likes e comentarios por view
- portanto:
  - `views` medem escala
  - `engajamento` mede resposta proporcional da audiencia
  - os dois indicadores devem ser lidos em conjunto, nao como substitutos

Status consolidado do Sprint 3 em 2026-06-18:

- `Overview` pode ser tratada como frente materialmente concluida no escopo do
  MVP atual
- `Criador individual` segue apoiado em views reais e coerente com a proposta
  do sprint
- `Creators > Visao geral` passou a consumir `v_dashboard_creator_summary` e
  deixou de depender de `get_creator_mock_rows()`
- `YouTube > Melhores videos 7d` deixou de ser placeholder e passou a operar
  com ranking semanal real sobre `v_dashboard_post_growth_7d`
- a etapa de `Melhores videos 7d` pode ser considerada concluida nesta rodada
- o fechamento final de UX, estados vazios, mensagens de erro e smoke test foi
  aceito como suficiente para o uso pessoal atual do dashboard
- o Sprint 3 pode ser tratado como encerrado no escopo aprovado

Decisao de escopo em 2026-06-20:

- a exigencia de embutir `Data Quality` dentro de cada ranking foi removida do
  Sprint 3
- para o uso pessoal atual do dashboard, a view dedicada `Data quality` e
  suficiente como superficie de diagnostico operacional
- essa mudanca foi registrada como decisao de projeto para evitar que o sprint
  carregue requisitos nascidos apenas dentro da propria agenda

Entrega complementar de avatar em creators:

- foi adicionada a coluna `avatar_url` em `public.creators`
- `v_dashboard_creator_summary` passou a expor `avatar_url`
- o scraper principal de YouTube foi ajustado para capturar o avatar do canal a
  partir de `channels.list(part=snippet,contentDetails)`
- foi criado o backfill offline `scripts/offline_backfill/backfill_creator_avatars.py`
  para popular creators ja existentes sem misturar esse fluxo com os scripts de
  producao
- resultado observado em 2026-06-19:
  - lote 1: `20` creators atualizados com sucesso, `0` erros
  - lote 2: nenhum creator restante sem `avatar_url`, status `completed`

Leitura executiva:

- o Sprint 3 ja entregou a maior parte do valor analitico do MVP
- o status atual e de sprint encerrado, nao mais de consolidacao parcial
- estimativa qualitativa atual: `100%` do sprint concluido no escopo aprovado

Query de validacao recomendada apos apply:

```sql
select
  post_id,
  title,
  first_collected_at,
  latest_collected_at,
  snapshot_count,
  views_delta_7d,
  views_growth_pct_7d
from public.v_dashboard_post_growth_7d
where latest_collected_at::date = current_date;
```

Leitura esperada da validacao:

- a query acima nao deve retornar registros que so entram por snapshot do dia atual no fuso de `America/Sao_Paulo`

Expansao controlada fora do escopo minimo original:

- incluir thumbnail real do video no ranking
- tornar clicavel a thumbnail para abrir o video no YouTube
- tornar clicavel o titulo do video para abrir o video no YouTube

Escopo funcional da expansao:

- a tela `Melhores videos 7d` deve exibir thumbnail real quando houver URL disponivel
- o clique na thumbnail e no titulo deve abrir o mesmo destino do video
- a navegacao deve preservar o foco analitico da tela, sem adicionar novos filtros nem alterar a regra do ranking
- na ausencia de thumbnail, a tela deve manter placeholder visual sem quebrar o layout
- na ausencia de link, thumbnail e titulo devem continuar visiveis, mas sem comportamento clicavel

Dependencias tecnicas da expansao:

- decisao tomada: manter essa feature inteiramente no Streamlit, sem alterar a `v_dashboard_post_growth_7d`
- usar `post_id` como `video_id` do YouTube para composicao das URLs
- `video_url`: `https://www.youtube.com/watch?v=VIDEO_ID`
- `thumbnail_url`: `https://i.ytimg.com/vi/VIDEO_ID/mqdefault.jpg`
- impacto operacional esperado: nenhum ajuste no banco ou na view; toda a composicao fica na camada de apresentacao

Etapas de implementacao da expansao:

1. Validar que `post_id` do YouTube corresponde ao `video_id` esperado para link e thumbnail.
2. Compor no Streamlit:
   - `video_url` a partir de `post_id`
   - `thumbnail_url` a partir de `post_id`
3. Atualizar o bloco visual da linha:
   - thumbnail real no lugar do placeholder
   - titulo com ancora clicavel
   - thumbnail com ancora clicavel
4. Tratar fallback:
   - sem thumbnail
   - sem link
   - link invalido
5. Validar no desktop e mobile que o clique nao compromete leitura nem alinhamento do ranking.

Criterio de pronto da expansao:

- cada linha do ranking abre o video pelo clique no titulo ou na thumbnail quando houver link disponivel
- a thumbnail real aparece quando o dado existir
- a ausencia de thumbnail ou link nao quebra o layout nem impede leitura da linha

Tarefas:

- revisar `docs/dashboard/16_ONLINE_DASHBOARD_SUPABASE_SPEC.md`
- revisar `docs/project/02_ROADMAP.md`
- confirmar quais views SQL ja existem no repositorio
- confirmar se as views ja foram aplicadas no Supabase de producao
- criar estrutura inicial recomendada:

```text
dashboard/
  streamlit_app.py
  requirements.txt
  README.md
  .streamlit/
    config.toml
```

Criterio de pronto:

- estrutura de pastas definida
- lista de views disponiveis confirmada
- decisoes visuais e de seguranca revisadas

## Etapa 1 - Conta e ambiente online

Objetivo:

- preparar o ambiente onde o dashboard sera publicado.

Status:

- conta Streamlit Community Cloud ja esta linkada ao GitHub
- branch de trabalho criada: `codex/dashboard-streamlit-mvp`
- app principal ativo em `dashboard/streamlit_app.py`
- Streamlit e Supabase ja foram confirmados como conectados e funcionando
- branch e caminho do app passaram a ser tratados como definidos para o MVP atual:
  - branch: `codex/dashboard-streamlit-mvp`
  - main file path: `dashboard/streamlit_app.py`

Tarefas:

- criar ou confirmar conta no Streamlit Community Cloud
- conectar o Streamlit ao repositorio GitHub
- definir se o app ficara publico por link ou privado conforme disponibilidade da conta
- confirmar branch de deploy
- confirmar arquivo principal do app, inicialmente `dashboard/streamlit_app.py`

Criterio de pronto:

- Streamlit Community Cloud conectado ao repositorio
- branch de deploy definida
- caminho do app definido
- app online abrindo com sucesso

Resultado observado:

- etapa considerada concluida
- ambiente online do dashboard esta operacional
- o proximo gargalo deixou de ser deploy e passou a ser consolidacao do MVP com views reais

Pendencias:

- nenhuma pendencia estrutural bloqueante nesta etapa
- manter apenas verificacao eventual de ambiente se houver troca futura de branch de deploy

## Etapa 2 - Ligacao segura com Supabase

Objetivo:

- permitir leitura sob demanda do Supabase sem expor credenciais sensiveis.

Status:

- metodo inicial definido: Supabase Python client com `SUPABASE_URL` e `SUPABASE_ANON_KEY`
- app preparado para abrir mesmo sem secrets configurados
- primeira leitura de data quality redesenhada para dois KPIs:
  - `v_dashboard_guardrail_coverage_status`
  - `v_dashboard_dead_post_validation_status`
- cache inicial configurado com TTL de 300 segundos
- conexao online validada no Streamlit Cloud
- `v_dashboard_data_quality_status` foi validada, mas deixou de ser a view alvo do Data Quality do dashboard
- Streamlit e Supabase confirmados como conectados e funcionando no estado atual do app

Tarefas:

- definir o metodo de conexao inicial:
  - Supabase Python client com anon key e RLS/grants, ou
  - conexao Postgres com usuario read-only
- criar ou validar usuario/chave de leitura
- garantir que `SUPABASE_SERVICE_ROLE_KEY` nao sera usada no app
- configurar secrets no Streamlit Cloud:

```toml
SUPABASE_URL = "..."
SUPABASE_ANON_KEY = "..."
```

ou, se for conexao Postgres:

```toml
SUPABASE_DB_URL = "postgresql://..."
```

- criar `.streamlit/secrets.toml.example` sem valores reais
- garantir que nenhum segredo real entre no Git

Criterio de pronto:

- app local consegue autenticar com credenciais seguras
- Streamlit Cloud possui secrets configurados
- nenhuma credencial real esta versionada

Resultado observado:

- etapa considerada funcionalmente concluida
- a conexao segura basica com Supabase esta resolvida para o MVP
- o foco agora deve migrar para validacao das views reais e substituicao de mocks/placeholders

Pendencias:

- validar retorno real das views principais do MVP no app online, nao mais a conexao em si
- revisar grants/RLS apenas se alguma view especifica falhar durante a consolidacao do MVP

## Etapa 3 - Analise de seguranca e permissao

Objetivo:

- reduzir risco antes de publicar o dashboard online.

Status:

- iniciada apos validacao da conexao com Supabase
- a anon key ja conseguiu ler `v_dashboard_data_quality_status`
- proximo passo e validar escopo minimo de leitura para as demais views do MVP

Tarefas:

- confirmar RLS/grants para as views do dashboard
- permitir leitura apenas das views necessarias ao MVP
- bloquear acesso direto a tabelas sensiveis quando possivel
- validar que o app nao permite escrita no Supabase
- revisar logs e prints para evitar vazamento de secrets
- confirmar que tabelas brutas pesadas nao sao carregadas sem filtro
- registrar resultado dos dois KPIs de data quality:
  - posts legados abaixo de 3 checagens em `v_dashboard_guardrail_coverage_status`
  - `pending_human_review` em `v_dashboard_dead_post_validation_status`

Views minimas:

- `public.v_dashboard_guardrail_coverage_status`
- `public.v_dashboard_dead_post_validation_status`
- `public.v_dashboard_creator_summary`
- `public.v_dashboard_post_growth_7d`
- `public.v_dashboard_unavailable_video_review`
- `public.v_dashboard_fenabrave_monthly_segments`

Criterio de pronto:

- checklist de seguranca aprovado
- consulta de leitura funciona
- tentativa de escrita nao e necessaria nem implementada
- Data Quality explicado pelos dois KPIs definidos, nao por checks genericos de frescor

## Etapa 4 - Validacao das views existentes

Objetivo:

- garantir que a camada SQL atual suporta a primeira versao do app.

Tarefas:

- executar no Supabase:

```sql
SELECT * FROM public.v_dashboard_guardrail_coverage_status;
```

Resultado esperado para guardrail:

```text
intervalo_video | total_checagens | total_posts
```

Com intervalos em portugues:

- `Novos: 0 a 3 dias`
- `Recentes: 4 a 7 dias`
- `Em aquecimento: 8 a 30 dias`
- `Legado: mais de 30 dias`

Observacao:

- esta view usa `DROP VIEW IF EXISTS` antes de `CREATE VIEW`, porque o contrato de colunas mudou durante a evolucao do dashboard
- ao reaplicar no Supabase SQL Editor, executar o arquivo completo
- o arquivo tambem aplica `GRANT SELECT` para `anon` e `authenticated`

```sql
SELECT * FROM public.v_dashboard_dead_post_validation_status;
```

```sql
SELECT *
FROM public.v_dashboard_creator_summary
ORDER BY total_views DESC
LIMIT 20;
```

```sql
SELECT *
FROM public.v_dashboard_post_growth_7d
ORDER BY views_delta_7d DESC
LIMIT 20;
```

```sql
SELECT *
FROM public.v_dashboard_unavailable_video_review
LIMIT 20;
```

```sql
SELECT *
FROM public.v_dashboard_fenabrave_monthly_segments
ORDER BY reference_period, segment_sort;
```

- validar tempo de resposta
- validar nomes de colunas esperados pelo app
- validar se nulos e zeros estao tratados de forma aceitavel
- documentar qualquer gap antes da construcao da UI

Criterio de pronto:

- views retornam dados sem erro
- colunas principais confirmadas
- tempo de resposta aceitavel para uso sob demanda

## Etapa 5 - Primeira view nova: hot now

Objetivo:

- criar a primeira view analitica nova orientada ao dashboard, separada da logica operacional da fila.

Status em 2026-06-20:

- SQL versionada criada em `sql/ddl/views/020_create_v_dashboard_hot_now.sql`
- view alvo: `public.v_dashboard_hot_now`
- contrato inicial definido no Sprint 4:
  - metrica principal baseada em views por hora
  - baseline `6h` aceito entre `6h` e `8h`
  - baseline `24h` aceito entre `18h` e `30h`
  - snapshot atual com no maximo `12h`
  - `hot_now_rank_score = velocity_6h + greatest(acceleration, 0)`
  - likes e comentarios como contexto, sem peso no score v1
- view aplicada e validada no Supabase
- pagina `YouTube > Hot now` conectada no Streamlit em
  `dashboard/streamlit_app.py`
- a tela consome apenas linhas `is_hot_now_eligible = true`, com limite `10` e
  filtros `Todos`, `Long` e `Short`

Racional:

- a documentacao atual prioriza analise temporal para responder o que esta quente agora
- o ranking deve usar velocidade recente e aceleracao, nao apenas volume absoluto

Tarefas:

- desenhar view SQL para:
  - `velocity_6h`
  - `previous_velocity`
  - `acceleration`
  - `views_delta_recent`
  - `likes_delta_recent`
  - `comments_delta_recent`
- criar arquivo em `sql/ddl/views/`
- validar contra `post_metrics_history`
- garantir filtros por historico minimo para evitar falsos positivos
- documentar limitacoes da view

Nome sugerido:

- `v_dashboard_hot_now`

Criterio de pronto:

- view retorna ranking temporal coerente
- posts com historico insuficiente sao tratados explicitamente
- view nao altera a fila operacional

## Etapa 5.1 - Politica de refresh e contexto para GPT

Objetivo:

- registrar como os dados sao atualizados no Streamlit e preparar o desenho futuro de um GPT interno ao dashboard.

Status:

- app usa Supabase Python client com leitura direta de views
- app nao usa RPC nas views atuais
- app usa cache Streamlit com TTL inicial de `300` segundos
- app nao faz polling automatico

Tarefas:

- manter TTL de `300` segundos como padrao inicial
- adicionar futuramente botao manual de refresh por pagina
- definir quais paginas podem montar contexto para GPT
- criar funcao futura para gerar `context packet` por pagina
- impedir qualquer execucao de SQL arbitrario pelo GPT

Criterio de pronto:

- politica de refresh documentada
- contexto minimo para GPT documentado
- fluxo de pergunta/resposta definido sem expor secrets

## Etapa 5.2 - Integridade da coleta em Data quality

Objetivo:

- adicionar um topico dentro de `Data quality` para monitorar se a coleta esta produzindo efeito real no banco, sem depender do retorno do script

Escopo inicial:

- topico `Integridade da coleta` dentro de `Data quality`
- diferenciar explicitamente os 2 workers do projeto:
  - `Atualizacao de posts` com execucao a cada 30 minutos
  - `Descoberta de novos posts` com execucao a cada 3 horas
- 3 blocos principais:
  - `Integridade da coleta`
  - `Evidencia de processamento`
  - `Sinais operacionais`
- 5 sinais visiveis:
  - `Ultimo snapshot`
  - `Posts atualizados nas ultimas 24h`
  - `Posts descobertos nas ultimas 24h`
  - `Tempo da ultima coleta`
  - `Tempo da ultima descoberta`

Contrato sugerido:

- uma view inicial para o worker de atualizacao:

```text
public.v_dashboard_worker_health_status
```

- uma segunda view para o worker de descoberta de novos posts:

```text
public.v_dashboard_new_post_discovery_status
```

Campos minimos esperados:

- `ultima_evidencia_de_execucao`
- `posts_atualizados_24h`
- `idade_da_ultima_evidencia_minutos`
- `ultima_execucao_discovery`
- `creators_avaliados_24h`
- `ultima_descoberta_de_post`
- `novos_posts_24h`
- `idade_da_ultima_execucao_minutos`
- `idade_da_ultima_descoberta_minutos`
- `status_code`
- `status_label`

Leitura correta da fase atual:

- a view atual cobre apenas o worker de `Atualizacao de posts`
- o worker de `Descoberta de novos posts` deve aparecer no Streamlit com rotulo proprio
- a view dedicada do segundo worker deve usar:
  - `posts.created_at` como evidencia de resultado de descoberta
  - `creator_metrics_history.collected_at` como evidencia legada/auxiliar de
    snapshot de canal

Regra operacional:

- um ciclo do worker pode ser saudavel mesmo quando `novos_posts_24h` e baixo
- `posts.created_at` deve impedir falso `nok` quando houver posts novos nas
  ultimas 24h
- `posts.created_at` nao comprova que o worker rodou quando nao houve post novo
  inserido
- open point futuro: persistir heartbeat do `youtube_main_scraper` para separar
  "rodou sem novidades" de "nao rodou"

Escopo revisado para `Sinais operacionais` do worker de metricas:

- nao usar `fila_itens_prontos` como KPI principal
  - a `v_post_update_queue_batch` continua desenhada para devolver lote cheio e
    esse numero mascara a composicao real do fluxo
- nao usar `falhas_recentes_24h` como KPI principal
  - esse sinal sobrepoe o bloco de `Posts mortos e validacao humana`
- nao usar `recovery_low` como KPI principal
  - essa leitura ja e acompanhada pelo bloco de `Monitoramento de posts sem checagem`
- priorizar os 2 KPIs abaixo:
  - `itens_atrasados`
  - `at_risk_bootstrap`

Leitura esperada:

- `itens_atrasados`
  - mostra a fila em faixas de atraso `Ate 1h`, `Ate 6h` e `Ate 24h`
- `at_risk_bootstrap`
  - mostra posts novos em risco de nao atingir cobertura minima no tempo
    esperado

Separacao semantica obrigatoria:

- `Monitoramento de posts sem checagem`
  - KPI de estoque e cobertura acumulada
- `Sinais operacionais`
  - KPI de fluxo, atraso e risco
- `Posts mortos e validacao humana`
  - KPI de indisponibilidade e acao manual

Passo a passo de implementacao:

1. criar e validar a view unica antes de pensar em detalhamento por tabela
2. conectar o topico em `Data quality` usando apenas `get_single_row_view`
3. renderizar primeiro os 3 blocos com texto executivo
4. aplicar cache no mesmo TTL das outras paginas
5. testar comportamento com view ausente, nulos e zeros
6. so depois discutir filtros, tabelas auxiliares ou drill-down

Sequencia minima de execucao:

1. criar primeiro a view de `Integridade da coleta` para `Atualizacao de posts`
2. criar a view de `Descoberta de novos posts`
3. criar a view ou contrato de `Sinais operacionais` do worker de metricas com
   faixas de atraso `Ate 1h`, `Ate 6h`, `Ate 24h` e `at_risk_bootstrap`
4. ligar cada bloco no Streamlit sem tabela detalhada no primeiro momento
5. validar texto, cor e semantica antes de abrir detalhamento tecnico

Regra de renderizacao complementar validada para `Data quality`:

- incluir abaixo dos blocos `Monitoramento de posts sem checagem` e
  `Posts mortos e validacao humana` uma leitura agregada de
  `v_dashboard_queue_bottleneck_status`
- renderizar um card por `priority_band`
- ordenar os cards da maior banda para a menor, exibindo `Banda 6` antes de
  `Banda 1`
- excluir da consolidacao as linhas onde:
  - `check_band = needs_coverage`
  - e `video_age_bucket` esteja em `new_0_3d` ou `recent_4_7d`
- por banda, mostrar:
  - soma de `total_posts`
  - media simples de `media_checagens`
  - pior `max_staleness_days`
  - soma de `posts_vencidos`
  - soma de `posts_no_batch_atual`

Regra de economia de tokens:

1. discutir primeiro o contrato da view, nao varias queries paralelas
2. trabalhar um arquivo por vez quando a mudanca for apenas visual
3. validar a hierarquia dos cards antes de abrir detalhamento tecnico
4. manter prompts curtos e fechados, por exemplo:
   - `ajuste apenas o bloco Integridade da coleta`
   - `nao leia arquivos fora de dashboard/streamlit_app.py e docs/dashboard/`
   - `nao refatore fora do escopo`

Criterio de pronto:

- o topico carrega sem quebrar mesmo quando a view ainda nao existe
- os 3 blocos aparecem com linguagem executiva clara
- os 5 sinais principais ficam visiveis na primeira dobra
- o app continua sem polling automatico e sem escrita no Supabase

## Etapa 6 - App local Streamlit MVP

Objetivo:

- criar o dashboard local antes de publicar.

Tarefas:

- criar `dashboard/requirements.txt`
- criar `dashboard/streamlit_app.py`
- configurar `st.set_page_config(layout="wide")`
- criar camada simples de conexao com Supabase
- aplicar cache com TTL curto nas queries
- criar navegacao inicial:
  - Overview
  - Creators
  - YouTube > Melhores videos 7d
  - Hot now
  - Data quality
  - Fila / videos indisponiveis
- criar tratamento de erro para falha de conexao

Criterio de pronto:

- app roda localmente
- cada pagina carrega ao menos uma view real
- falhas de conexao aparecem como mensagem clara

## Etapa 7 - Tema visual e componentes

Objetivo:

- aplicar a direcao visual definida pelo projeto.

Tarefas:

- criar CSS customizado para:
  - background cinza escuro
  - sidebar grafite
  - cards claros/escuros
  - cabecalhos de card escuros
  - acento coral
  - tabelas legiveis
- criar componentes reutilizaveis:
  - KPI card
  - status card
  - section header com picto
  - alert box de data quality
- escolher biblioteca de pictos:
  - primeira opcao: pictos via HTML/CSS simples ou caracteres seguros
  - alternativa: pacote leve de icones se fizer sentido no Streamlit
- evitar poluir a UI com emojis excessivos

Criterio de pronto:

- app segue a referencia visual acordada
- layout funciona em tela larga
- data quality aparece antes de rankings

## Etapa 8 - Testes iniciais

Objetivo:

- validar que o MVP e confiavel para uso analitico.

Tarefas:

- testar carregamento local
- testar deploy no Streamlit Cloud
- testar conexao com secrets online
- testar ausencia de secrets no Git
- testar paginas com dados vazios
- testar ordenacao de rankings
- testar limites de linhas e filtros
- testar data quality antes dos rankings
- comparar amostras do dashboard com queries diretas no Supabase

Criterio de pronto:

- dados do dashboard batem com queries diretas
- app nao quebra com nulos ou listas vazias
- tempo de carregamento aceitavel
- nenhum segredo exposto

## Etapa 9 - Publicacao online

Objetivo:

- disponibilizar a primeira versao online.

Tarefas:

- publicar no Streamlit Community Cloud
- configurar branch e arquivo principal
- configurar secrets online
- testar URL final
- documentar URL e modo de acesso em `dashboard/README.md`
- registrar limitacoes conhecidas

Criterio de pronto:

- URL online funcionando
- app consome Supabase sob demanda
- primeira versao pronta para uso em estudos de mercado

## Etapa 10 - Revisao analitica pos-MVP

Objetivo:

- avaliar se o dashboard responde perguntas reais do projeto.

Perguntas de validacao:

- quais creators cresceram mais nos ultimos 7 dias?
- quais videos estao acelerando agora?
- quais videos tem alto engajamento relativo?
- quais creators tem volume alto mas engajamento baixo?
- ha problemas de coleta que tornam alguma analise arriscada?
- videos indisponiveis estao afetando a leitura de performance?

Entregaveis:

- lista de melhorias de layout
- lista de novas views necessarias
- lista de filtros prioritarios
- decisao sobre incluir dados externos automotivos no dashboard

## Ordem recomendada de execucao

1. Pre-flight do repositorio
2. Conta Streamlit e deploy placeholder
3. Ligacao segura com Supabase
4. Analise de seguranca
5. Validacao das views existentes
6. Criacao da view `v_dashboard_hot_now`
7. App local Streamlit MVP
8. Tema visual e componentes
9. Testes iniciais
10. Publicacao online
11. Revisao analitica pos-MVP

## Marco validado em 2026-05-26

Cadastro de criadores via Streamlit validado:

- tela: `Cadastro > Criadores`
- caso: `Autoesporte`
- `creator_id`: `55`
- `entity_id`: `52`
- `channel_id`: `UCc6jv88ebCrDVxJQUjZfGT`
- subnichos: `compra`, `noticia`, `review`, `teste`
- resultado: criador cadastrado, com subnicho, e visivel na view de criadores
  do Streamlit

Checkpoint pendente:

- acompanhar nos proximos dias se o worker passa a incorporar esse criador ao
  ciclo normal de discovery/coleta.

## Primeira entrega pratica sugerida

Primeiro sprint:

- criar estrutura `dashboard/`
- criar app Streamlit local com pagina Overview
- conectar em `v_dashboard_guardrail_coverage_status`
- conectar em `v_dashboard_dead_post_validation_status`
- exibir os 2 cards de data quality
- aplicar tema visual base
- rodar localmente

Motivo:

- valida conta, conexao, seguranca, layout e data quality com escopo pequeno
- evita construir rankings antes de confirmar confiabilidade dos dados
- cria base reaproveitavel para as proximas paginas

## Riscos principais

- usar service role key por conveniencia
- carregar historico bruto demais no Streamlit
- chamar dashboard de pronto apenas porque as views SQL existem
- ignorar data quality e interpretar ranking como verdade final
- criar UI bonita sem validar se responde perguntas reais de mercado
- misturar app do dashboard com scripts operacionais do pipeline

## Commit sugerido para a primeira implementacao

```bash
git commit -m "feat(dashboard): cria mvp streamlit inicial"
```
