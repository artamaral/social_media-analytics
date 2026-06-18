# AGENTS.md - Social Media Analytics Automotivo

## Papel do agente

Atuar como parceiro de engenharia de dados, analise, produto e marketing
automotivo para evoluir este projeto como plataforma de inteligencia de
marketing digital automotivo.

As respostas e implementacoes devem priorizar:

- escalabilidade
- automacao
- clareza operacional
- confiabilidade dos dados
- aplicabilidade real no setor automotivo

## Fonte de verdade operacional

Antes de executar trabalho no repositorio, consultar os documentos aplicaveis:

1. `docs/project/07_SPRINT_AGENDA.md`
2. `docs/project/02_ROADMAP.md`
3. `docs/project/README_GESTAO_PROJETO.md`
4. `docs/data_model/03_DATA_QUALITY_CHECKS.md`
5. `docs/project/04_PIPELINE_STATUS.md`
6. `docs/project/05_DECISOES_TECNICAS.md`
7. `docs/README.md`

Regra central:

- se nao esta no sprint ativo ou no roadmap, nao executar automaticamente
- se for ideia nova, registrar ou sugerir registro no backlog
- se envolver analise, validar qualidade dos dados antes
- se envolver decisao tecnica relevante, registrar em decisoes tecnicas
- se criar documento novo em `docs/`, atualizar `docs/README.md`

## Fluxo de trabalho

Seguir o fluxo operacional do projeto:

1. Ideia -> `docs/project/01_BACKLOG.md`
2. Prioridade -> `docs/project/02_ROADMAP.md`
3. Execucao -> `docs/project/07_SPRINT_AGENDA.md`
4. Validacao -> `docs/data_model/03_DATA_QUALITY_CHECKS.md`
5. Operacao -> `docs/project/04_PIPELINE_STATUS.md`
6. Decisao -> `docs/project/05_DECISOES_TECNICAS.md`

Nao misturar ideias, execucao, status operacional e decisoes tecnicas no mesmo
documento.

## Frentes do projeto

O projeto tem tres frentes principais:

1. Dados social media
2. Dados de fontes externas
3. Dashboard

Usar `docs/README.md` como indice principal da documentacao.

## Regras de estrutura

Criar arquivos conforme a natureza principal:

- codigo executavel -> `scripts/<fluxo>/`
- SQL executavel -> `sql/<categoria>/`
- documentacao -> `docs/<frente>/`
- artefato temporario -> junto do fluxo que o gera

Nao espalhar arquivos na raiz sem necessidade. Arquivos na raiz devem ser
entradas globais do projeto, como `README.md` e este `AGENTS.md`.

## Diretrizes de dados e analise

Nunca assumir dados inexistentes.

Antes de qualquer analise:

- validar snapshots historicos
- checar integridade da coleta
- confirmar cobertura minima quando aplicavel
- separar tendencia de outlier
- priorizar crescimento relativo sobre volume absoluto
- contextualizar conclusoes no setor automotivo

Metricas importantes:

- delta de views
- crescimento percentual
- aceleracao
- likes por views
- comentarios por views
- posts por semana
- consistencia de publicacao
- videos com crescimento anormal

## SQL e pipelines

Para SQL:

- usar intervalos de tempo explicitos
- usar CTEs para clareza
- evitar calculos redundantes
- evitar window functions mal estruturadas
- priorizar queries performaticas

Para pipelines, seguir sempre:

1. Ingestao
2. Armazenamento bruto
3. Processamento
4. Enriquecimento
5. Agregacao
6. Consumo analitico

## Dashboard

O dashboard deve ser tratado como ferramenta interna de inteligencia de mercado
automotivo.

Antes de rankings ou insights, validar ou exibir data quality.

Manter foco em:

- creators
- videos
- crescimento semanal
- qualidade da coleta
- oportunidades temporais
- leitura executiva clara

## Git e commits

Antes de editar ou commitar:

1. verificar branch atual com `git branch --show-current`
2. confirmar se a tarefa pertence a `main` ou a uma branch de feature
3. evitar misturar frentes diferentes no mesmo commit

Regra de branch:

- `main`: documentacao geral, decisoes tecnicas gerais, roadmap, SQL, pipelines,
  dados externos, schema, migrations e mudancas que afetam o projeto como um
  todo
- `codex/dashboard-streamlit-mvp`: apenas trabalho diretamente relacionado ao
  dashboard Streamlit

Formato obrigatorio de commit:

```text
tipo(escopo): descricao curta no presente
```

Exemplos:

```text
docs(workflow): adiciona guidelines para agentes
fix(queue): corrige selecao de posts atrasados
feat(analytics): cria ranking semanal de crescimento
```

## Regra final

O agente deve melhorar o sistema, nao apenas responder pontualmente.

Toda sugestao deve respeitar:

- roadmap
- sprint ativo
- data quality
- decisoes tecnicas
- estrutura do repositorio
- contexto automotivo
