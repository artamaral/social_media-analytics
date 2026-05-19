# Organização de tabelas e SQL no GitHub

## Objetivo

Organizar os artefatos de banco de dados no GitHub de forma que:

- fique fácil localizar tabelas, views, functions e scripts operacionais;
- mudanças estruturais sejam separadas de consultas do dia a dia;
- o repositório vire a fonte oficial do banco, e não o editor SQL do Supabase;
- seja simples entender o que cria estrutura, o que carrega dados, o que faz manutenção e o que documenta o processo.

---

## Problema do modelo atual

Hoje você comentou que tem apenas o schema dentro da pasta `sql`.

Isso costuma gerar alguns problemas:

- o schema vira um arquivo grande e difícil de navegar;
- fica difícil saber o que é tabela, o que é função e o que é script operacional;
- alterações pequenas acabam se perdendo;
- scripts importantes ficam espalhados no Supabase SQL Editor, em conversas, blocos de notas ou mensagens;
- não existe trilha clara entre “estrutura do banco” e “rotina operacional”.

Na prática, isso reduz governança e aumenta risco de retrabalho.

---

## Princípio recomendado

A organização ideal é separar o banco em camadas:

1. **estrutura permanente**
2. **scripts operacionais**
3. **manutenção e correção**
4. **documentação**
5. **visões consolidadas do schema**

Ou seja:

- arquivos que **criam objetos** do banco ficam separados;
- arquivos que **executam rotinas do dia a dia** ficam separados;
- arquivos que **corrigem problemas** ficam separados;
- documentação do processo fica junto do código;
- o schema completo pode continuar existindo, mas como referência, não como único ponto de organização.

---

## Estrutura recomendada

```text
/sql
  /schema
    full_schema_snapshot.sql
    README.md

  /ddl
    /tables
      001_create_entities.sql
      002_create_sub_niches.sql
      003_create_creators.sql
      004_create_posts.sql
      005_create_post_metrics_history.sql
      006_create_entity_sub_niches.sql
      007_create_pipeline_state.sql
      008_create_post_update_queue.sql
      009_create_entity_intake.sql

    /views
      001_create_v_entity_intake_review.sql

    /functions
      001_create_publish_entity_intake_function.sql

    /indexes
      001_create_unique_entities_normalized_name.sql

    /constraints
      001_add_business_constraints.sql

  /dml
    review_entity_intake.sql
    publish_entity_intake_manual_run.sql
    intake_normalization_check.sql

  /maintenance
    deduplicate_entities.sql
    validate_entity_links.sql
    audit_entities_without_sub_niche.sql

  /seed
    001_seed_sub_niches.sql

  /docs
    entity_intake_process.md
    sql_conventions.md
    table_organization.md
```

---

## O papel de cada pasta

### `/sql/schema`

Essa pasta guarda uma **visão consolidada** do banco.

Exemplo:

- `full_schema_snapshot.sql`

#### Para que serve
- consultar o estado geral do banco;
- facilitar leitura macro do schema;
- servir como referência rápida.

#### O que não fazer
- não usar essa pasta como único lugar para desenvolver;
- não concentrar toda manutenção só nesse arquivo.

#### Por quê
Porque um schema único é bom para referência, mas ruim para operação e evolução.

---

### `/sql/ddl`

Essa é a pasta mais importante.

DDL significa objetos estruturais do banco:

- tabelas
- views
- functions
- indexes
- constraints

#### Por que separar por tipo
Porque isso melhora muito a navegação.

Você sabe exatamente onde procurar:

- tabela -> `/ddl/tables`
- view -> `/ddl/views`
- função -> `/ddl/functions`
- índice -> `/ddl/indexes`

---

### `/sql/ddl/tables`

Aqui ficam os arquivos de criação de tabelas.

Exemplos:

- `001_create_entities.sql`
- `002_create_sub_niches.sql`
- `003_create_creators.sql`

#### Vantagem
Quando você quiser revisar a estrutura de `entities`, vai direto ao arquivo da tabela, em vez de procurar dentro de um schema gigante.

#### Recomendação
Um arquivo por tabela.

#### Por quê
Porque tabela é um ativo estrutural principal do banco. Separar por tabela melhora:
- manutenção;
- revisão;
- histórico no Git;
- entendimento do impacto de mudanças.

---

### `/sql/ddl/views`

Aqui ficam as views permanentes.

Exemplo:

- `001_create_v_entity_intake_review.sql`

#### Por quê
Views não são tabelas nem scripts operacionais. Elas são objetos estruturais reutilizáveis.

Separá-las evita confusão entre:
- lógica persistente do banco;
- consulta manual do dia a dia.

---

### `/sql/ddl/functions`

Aqui ficam funções SQL ou PL/pgSQL permanentes.

Exemplo:

- `001_create_publish_entity_intake_function.sql`

#### Por quê
Funções são lógica de negócio embutida no banco. Elas merecem pasta própria, porque costumam ser críticas e reutilizáveis.

---

### `/sql/ddl/indexes`

Aqui ficam os índices criados por motivo técnico ou de integridade.

Exemplo:

- `001_create_unique_entities_normalized_name.sql`

#### Por quê
Separar índices ajuda a entender:
- performance;
- unicidade;
- mecanismos de proteção contra duplicidade.

Também facilita auditoria estrutural.

---

### `/sql/ddl/constraints`

Opcional, mas útil quando você tiver muitas regras adicionais.

Exemplo:
- checks adicionais;
- foreign keys adicionadas depois;
- validações de integridade específicas.

#### Por quê
Nem toda constraint nasce junto com a tabela. Em projetos que evoluem, separar constraints facilita.

---

### `/sql/dml`

Aqui ficam os scripts operacionais do dia a dia.

Exemplos:

- `review_entity_intake.sql`
- `publish_entity_intake_manual_run.sql`
- `intake_normalization_check.sql`

#### O que entra aqui
Consultas e comandos usados rotineiramente para:
- revisar;
- publicar;
- consultar;
- rodar operações manuais.

#### O que não entra aqui
- criação de tabela;
- criação de função;
- scripts de reparo histórico.

#### Por quê
Porque DML é operação, não estrutura.

---

### `/sql/maintenance`

Aqui entram scripts menos frequentes, porém importantes.

Exemplos:
- deduplicação;
- auditoria;
- reparo de vínculos;
- validação extraordinária.

#### Por quê
Esses scripts geralmente:
- não são usados todo dia;
- podem ter alto impacto;
- exigem mais cuidado.

Separá-los reduz o risco de uso indevido.

---

### `/sql/seed`

Aqui ficam cargas iniciais e cadastros base.

Exemplo:

- `001_seed_sub_niches.sql`

#### Quando usar
Quando houver tabelas cujo conteúdo é relativamente estável e precisa existir no ambiente:
- sub_niches
- classificações fixas
- valores base

#### Por quê
Isso separa estrutura de conteúdo inicial.

---

### `/sql/docs`

Aqui fica a documentação operacional e arquitetural do banco.

Exemplos:

- `entity_intake_process.md`
- `sql_conventions.md`
- `table_organization.md`

#### Por quê
Documentação perto do código reduz dependência de memória e evita que o processo fique “só na cabeça”.

---

## Como organizar as tabelas especificamente

Hoje sua dúvida é sobre como organizar as tabelas também no GitHub.

A melhor prática é:

### 1. Um arquivo por tabela
Exemplo:

```text
/sql/ddl/tables/001_create_entities.sql
/sql/ddl/tables/002_create_sub_niches.sql
/sql/ddl/tables/003_create_creators.sql
/sql/ddl/tables/004_create_posts.sql
```

### 2. Nome padronizado
Use padrão:

```text
NNN_create_nome_da_tabela.sql
```

Exemplos:
- `001_create_entities.sql`
- `002_create_sub_niches.sql`

### 3. Comentário no topo do arquivo
Cada arquivo deve começar com:

```sql
-- 001_create_entities.sql
```

### 4. Comentário explicando o papel da tabela
Antes da query:

```sql
-- Criar tabela mestre de entities.
-- Esta tabela representa a identidade canônica de creators no domínio automotivo.
```

### 5. Arquivo separado para índice relevante
Se o índice for importante e puder ser evoluído depois, prefira separar:
- tabela em um arquivo;
- índice em outro.

Isso ajuda a isolar mudanças.

---

## Exemplo prático de organização para suas tabelas atuais

```text
/sql/ddl/tables
  001_create_entities.sql
  002_create_sub_niches.sql
  003_create_creators.sql
  004_create_posts.sql
  005_create_post_metrics_history.sql
  006_create_entity_sub_niches.sql
  007_create_pipeline_state.sql
  008_create_post_update_queue.sql
  009_create_entity_intake.sql
```

---

## Como lidar com o schema completo

Você pode manter o schema completo, mas com nova função.

### Antes
- fonte principal;
- arquivo central de tudo.

### Depois
- snapshot de referência;
- consulta rápida;
- apoio de entendimento global.

### Nome sugerido
```text
/sql/schema/full_schema_snapshot.sql
```

### Regra
Ele não substitui os arquivos granulares.

---

## Fonte oficial do banco

A fonte oficial deve ser o GitHub.

Não:
- editor SQL do Supabase;
- histórico do chat;
- bloco de notas;
- arquivos soltos.

### Regra prática
1. criar ou editar o `.sql` no repositório;
2. revisar;
3. executar no Supabase;
4. manter versionado no Git.

---

## Vantagens dessa organização

### 1. Facilidade de navegação
Você encontra mais rápido o que precisa.

### 2. Melhor histórico no Git
Fica claro quando:
- uma tabela mudou;
- uma view foi criada;
- uma função foi ajustada.

### 3. Menor risco operacional
Scripts sensíveis ficam isolados em `maintenance`.

### 4. Melhor onboarding
No futuro, qualquer pessoa entende o projeto mais rápido.

### 5. Menos dependência de memória
Você não precisa lembrar onde estava cada SQL.

### 6. Evolução mais segura
Novos objetos entram no lugar certo.

---

## Convenção recomendada de arquivos

### Para tabelas
```text
001_create_entities.sql
002_create_sub_niches.sql
```

### Para views
```text
001_create_v_entity_intake_review.sql
```

### Para functions
```text
001_create_publish_entity_intake_function.sql
```

### Para índices
```text
001_create_unique_entities_normalized_name.sql
```

### Para scripts operacionais
```text
review_entity_intake.sql
publish_entity_intake_manual_run.sql
```

### Para manutenção
```text
deduplicate_entities.sql
validate_entity_links.sql
```

---

## Recomendação final para o seu caso

Para o seu projeto hoje, eu organizaria assim:

1. manter o schema completo em `/sql/schema`;
2. criar `/sql/ddl/tables` e separar cada tabela em um arquivo;
3. criar `/sql/ddl/views`, `/functions` e `/indexes`;
4. manter scripts de uso manual em `/sql/dml`;
5. manter scripts de correção em `/sql/maintenance`;
6. criar `/sql/docs` com documentação curta e objetiva.

Essa estrutura é simples o suficiente para seu estágio atual e robusta o bastante para crescer junto com o projeto.

---

## Próximo passo sugerido

Comece migrando apenas estes itens:

- `entities`
- `sub_niches`
- `creators`
- `entity_sub_niches`
- `entity_intake`
- `v_entity_intake_review`
- `publish_entity_intake()`

Depois expanda para o restante.

Assim você melhora a organização sem tentar reestruturar tudo de uma vez.
