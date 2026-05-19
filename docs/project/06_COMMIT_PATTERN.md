# 📝 PADRÃO DE COMMITS — SOCIAL MEDIA ANALYTICS (AUTOMOTIVO)

## 🎯 OBJETIVO

Padronizar os commits para garantir:

* clareza sobre mudanças
* rastreabilidade técnica
* facilidade de debug
* organização conforme o projeto escala
* histórico utilizável como documentação

---

## 🧱 FORMATO OBRIGATÓRIO

```
tipo(escopo): descrição curta no presente
```

---

## 📌 EXEMPLOS CORRETOS

```
fix(pipeline): corrige loop no fim da lista de creators
feat(sql): adiciona auditoria para posts sem historico
refactor(scraper): reorganiza fluxo de coleta
docs(roadmap): atualiza prioridades da semana
perf(migration): cria indice para normalized_name
```

---

## ❌ EXEMPLOS PROIBIDOS

```
update geral
ajustes
mudancas
teste
corrigindo coisas
sql novo
```

---

## 🧩 TIPOS DE COMMIT

### 🚀 feat — nova funcionalidade

```
feat(pipeline): adiciona retry para falhas da youtube api
feat(analytics): cria ranking semanal de crescimento
feat(sql): cria view de creators com maior engajamento
```

---

### 🐛 fix — correção de bug

```
fix(scraper): corrige paginação de videos
fix(queue): impede timeout ao final da lista
fix(sql): corrige update de collected_at
fix(api): corrige endpoint do supabase rest v1
```

---

### ♻️ refactor — melhoria interna sem mudar comportamento

```
refactor(pipeline): separa funcoes de ingestao e persistencia
refactor(sql): simplifica cte de crescimento
refactor(repo): reorganiza estrutura de pastas
```

---

### 📚 docs — documentação

```
docs(backlog): adiciona ideias de classificacao
docs(roadmap): redefine prioridades
docs(workflow): adiciona regras de git
```

---

### ⚙️ chore — tarefas operacionais

```
chore(repo): adiciona gitignore
chore(env): atualiza variaveis de ambiente
chore(deps): atualiza requirements.txt
```

---

### 🧪 test — validações e auditorias

```
test(sql): valida posts sem historico
test(pipeline): testa lote de 3 creators
test(data-quality): valida collected_at nulo
```

---

### ⚡ perf — performance

```
perf(sql): adiciona indice para normalized_name
perf(api): reduz chamadas repetidas
perf(queue): melhora selecao por prioridade
```

---

### 🏗️ build — build e deploy

```
build(cloud-run): ajusta entrypoint
build(requirements): adiciona functions-framework
build(deploy): ajusta configuracao do cloud run
```

---

### 🔄 ci — automação / integração contínua

```
ci(github): adiciona workflow de validacao
ci(deploy): automatiza deploy cloud run
```

---

## 🧠 ESCOPOS PADRÃO DO PROJETO

Use sempre um escopo relevante:

### Infraestrutura

* pipeline
* scraper
* scheduler
* queue
* api
* cloud-run
* supabase
* youtube

### Banco / SQL

* sql
* schema
* migration

### Dados

* data-quality
* analytics

### Entidades

* entities
* creators
* posts
* history

### Gestão

* docs
* backlog
* roadmap
* workflow
* repo

---

## 📌 EXEMPLOS REAIS DO SEU PROJETO

### Pipeline

```
fix(pipeline): corrige atualizacao da fila apos coleta
refactor(scraper): separa coleta de metricas e persistencia
feat(queue): adiciona controle de prioridade dinamico
```

---

### SQL / Banco

```
feat(sql): cria auditoria para creators sem coleta recente
fix(schema): corrige tipo de post_id para texto
perf(migration): cria indice unico em normalized_name
fix(posts): atualiza collected_at com base no historico
```

---

### Analytics

```
feat(analytics): cria ranking de crescimento em 7 dias
feat(analytics): adiciona deteccao de outliers
refactor(analytics): melhora calculo de delta
```

---

### Data Quality

```
test(data-quality): valida posts sem historico
fix(data-quality): remove registros invalidos
docs(data-quality): documenta validacoes obrigatorias
```

---

### Infra / Cloud

```
fix(cloud-run): corrige erro de inicializacao na porta 8080
build(cloud-run): adiciona functions-framework
fix(scheduler): ajusta frequencia de execucao
```

---

### Gestão / Docs

```
docs(backlog): adiciona melhorias de classificacao
docs(roadmap): prioriza estabilidade do pipeline
docs(workflow): define padrao de commits
```

---

## 📏 TAMANHO E BOAS PRÁTICAS

### ✔ Faça:

* commits pequenos
* uma mudança por commit
* mensagens específicas
* usar verbo no presente

---

### ❌ Evite:

* commits grandes demais
* misturar SQL + pipeline + docs
* mensagens genéricas
* múltiplos problemas em um commit

---

## 🧪 REGRA DE VALIDAÇÃO DO COMMIT

Antes de commitar, pergunte:

1. O que foi feito está claro?
2. Onde foi feito está claro?
3. O motivo está implícito?

Se não estiver → reescreva.

---

## 🔁 PADRÃO DIÁRIO

Exemplo real:

```
git commit -m "fix(queue): impede timeout ao final da lista"
git commit -m "feat(sql): adiciona auditoria de gaps de coleta"
git commit -m "perf(migration): cria indice para normalized_name"
git commit -m "docs(roadmap): atualiza prioridades"
```

---

## 🧭 DIRETRIZ FINAL

> O commit é a memória técnica do projeto.

Se você não consegue entender um commit depois de 30 dias, ele está errado.

Este padrão é obrigatório para manter:

* clareza
* controle
* escalabilidade
* confiabilidade do projeto
