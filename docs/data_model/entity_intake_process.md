# entity_intake_process.md

## Objetivo
Controlar o cadastro manual de entities e seus respectivos sub_niches sem inserir diretamente nas tabelas finais.

## Regra principal
Nunca inserir diretamente em:
- public.entities
- public.entity_sub_niches

Toda entrada manual deve passar por:
- public.entity_intake

## Fluxo operacional atual

### Caminho preferencial pelo Streamlit

Validado em 2026-05-26.

Tela:
- `Cadastro > Criadores`

Fluxo:

1. Checar se a entity ja existe.
2. Se a entity nao existir, enviar o registro para `public.entity_intake`.
3. Revisar o resultado pela propria UI, usando `public.v_entity_intake_review`.
4. Publicar uma linha por vez com `public.publish_entity_intake_entry(p_intake_id)`.
5. Cadastrar o criador com `public.create_creator_from_resolved_entity(...)`.
6. Validar que o criador aparece na view de criadores no Streamlit.
7. Se o criador for novo, chamar o worker de discovery inicial descrito em
   `docs/social_media/34_CREATOR_ONBOARDING_DISCOVERY_WORKER_SPEC.md`.

Caso validado:

- entity: `Autoesporte`
- creator_id: `55`
- entity_id: `52`
- channel_id: `UCc6jv88ebCrDVxJQUjZfGT`
- subnichos: `compra`, `noticia`, `review`, `teste`
- status: cadastro validado com subnicho e visivel na view de criadores

Pendente:

- implementar o worker separado de discovery inicial para reduzir a espera ate
  o ciclo normal de discovery/coleta.

Observacao sobre Streamlit:

- nao e necessario criar um arquivo separado apenas para a integracao com o
  Streamlit neste momento;
- a UI deve apenas acionar o worker com `creator_id` apos o cadastro controlado;
- o contrato do worker fica centralizado em
  `docs/social_media/34_CREATOR_ONBOARDING_DISCOVERY_WORKER_SPEC.md`.

### Caminho manual legado

### 1. Cadastrar manualmente no Supabase UI
Preencher linhas na tabela:
- public.entity_intake

Campos principais:
- raw_name
- sub_niche_name
- niche
- creator_type
- notes
- status

### 2. Revisar os dados antes da publicação
Executar:
- sql/dml/review_entity_intake.sql

Objetivo:
- verificar se a entity já existe
- verificar se o sub_niche existe
- verificar se o registro está pronto para inserção

### 3. Publicar os registros
Executar:
- sql/dml/publish_entity_intake_manual_run.sql

Esse script chama a função:
- public.publish_entity_intake()

### 4. Validar resultado
Executar:
- sql/maintenance/validate_entity_links.sql

## Objetos permanentes do banco

### Tabela
- sql/ddl/001_create_entity_intake.sql

### View
- sql/ddl/002_create_v_entity_intake_review.sql

### Function
- sql/ddl/003_create_publish_entity_intake_function.sql
- sql/ddl/functions/006_creator_intake_rpc_functions.sql

### Índice de proteção
- sql/ddl/004_create_unique_index_entities_normalized_name.sql

## Scripts de manutenção

### Deduplicação histórica
- sql/maintenance/deduplicate_entities.sql

### Validação de vínculos
- sql/maintenance/validate_entity_links.sql

## Regra de governança de SQL
O arquivo `.sql` salvo no repositório é a fonte oficial.

O Supabase SQL Editor deve ser usado apenas para execução.

## Convenção
- `/sql/ddl` = objetos permanentes do banco
- `/sql/dml` = operação manual do dia a dia
- `/sql/maintenance` = auditoria, correção, reparo
- `/sql/docs` = documentação operacional
