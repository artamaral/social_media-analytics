# GESTAO DO PROJETO

## Regra de sprint ativo

A execucao do projeto deve seguir a agenda de sprints registrada em
`07_SPRINT_AGENDA.md`.

Regra obrigatoria:

- Apenas atividades relacionadas ao sprint ativo devem ser executadas.
- Se uma demanda nao tiver relacao clara com o sprint ativo, o GPT deve perguntar antes de prosseguir.
- Sem confirmacao explicita do usuario, demandas fora do sprint ativo devem ser tratadas como ideias para backlog/roadmap, nao como execucao.

Pergunta padrao:

```text
Esta atividade nao esta relacionada ao sprint ativo. Deseja prosseguir mesmo assim ou prefere registrar no backlog/roadmap?
```

## Estrutura

`/docs` contem toda a gestao do projeto:

- `01_BACKLOG.md` -> ideias
- `02_ROADMAP.md` -> prioridades
- `03_DATA_QUALITY_CHECKS.md` -> validacao
- `04_PIPELINE_STATUS.md` -> operacao
- `05_DECISOES_TECNICAS.md` -> historico
- `07_SPRINT_AGENDA.md` -> agenda de execucao por sprint

---

## Fluxo de uso

1. Ideia -> BACKLOG
2. Priorizar -> ROADMAP
3. Organizar execucao -> SPRINT AGENDA
4. Validar dados -> DATA QUALITY
5. Executar -> PIPELINE
6. Decidir -> DECISOES

---

## Regras

- Nao executar fora do roadmap.
- Nao executar fora do sprint ativo sem confirmacao do usuario.
- Nao analisar sem validar dados.
- Nao misturar ideias com execucao.
