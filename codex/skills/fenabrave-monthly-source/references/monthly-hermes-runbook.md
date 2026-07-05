# Runbook mensal Hermes - Fenabrave para post LinkedIn

## Objetivo

Permitir que Hermes execute mensalmente a rotina de encontrar a fonte Fenabrave oficial, confirmar o periodo, preparar os dados principais e acionar a skill de post LinkedIn sem depender do usuario informar o site.

## Frequencia recomendada

Executar uma vez por mes, apos o 5o dia util, sempre olhando para o mes anterior.

## Entrada minima

- Mes/ano alvo, quando informado pelo usuario; ou
- Mes anterior ao mes corrente, quando a rotina for automatica.

## Saida esperada para o post

Hermes deve entregar para `linkedin-automotive-posts` um pacote curto com:

| Campo | Obrigatorio | Observacao |
| --- | --- | --- |
| Fonte | Sim | Usar `Fenabrave`. |
| Periodo | Sim | Mes e ano do informe. |
| URL da pagina oficial | Sim | Pagina de emplacamentos Fenabrave. |
| URL do PDF/download | Sim, quando disponivel | Link direto oficial preferencial. |
| Dados principais | Sim | Apenas autos + LCV: varejo mes vs mes -1, marcas no varejo, modelos mais vendidos, acumulado ano vs acumulado anterior, mix venda direta/varejo e comparacao anual quando houver discrepancia relevante. |
| Limites | Sim | Emplacamento como proxy de mercado; varejo como melhor sinal de intencao do consumidor. |
| Angulo editorial | Recomendado | Ex.: disputa de segmento, crescimento de marca, sinal para aftermarket. |

## Sequencia operacional

1. Confirmar periodo alvo.
2. Acessar a pagina oficial de emplacamentos Fenabrave.
3. Baixar ou localizar o PDF oficial do mes.
4. Conferir se o periodo do PDF bate com o periodo alvo.
5. Extrair apenas autos + LCV, priorizando resultado de varejo como sinal de intencao do consumidor.
6. Comparar mes contra mes -1, acumulado do ano contra acumulado equivalente do ano anterior e, quando houver discrepancia da ordem de 10% ou mais, comparar o mes/ano contra o mesmo mes do ano anterior.
7. Analisar obrigatoriamente os carros/modelos mais vendidos, marcas no varejo e a relacao percentual entre venda direta e varejo.
8. Separar fatos, sinais e hipoteses.
9. Acionar `linkedin-automotive-posts` para redigir o texto mensal.
10. Revisar se o texto esta humanizado, curto, com poucos bullets, sem dados inventados e sem mencao a eletricos/hibridos salvo quando aparecerem entre os tops analisados.



## Acesso do Hermes ao repositorio

Hermes precisa ter acesso ao repositorio antes de executar esta rotina, porque as skills ficam versionadas em `.codex/skills/` e as regras do projeto ficam em `AGENTS.md` e `docs/`.

Opcoes recomendadas, em ordem de preferencia:

1. **Conector GitHub/Git do proprio Hermes**: autorizar o repositorio `social_media-analytics` no conector, com permissao minima de leitura para executar a rotina. Dar permissao de escrita apenas se Hermes tambem for abrir PRs ou alterar arquivos.
2. **Workspace controlado pela plataforma**: executar Hermes dentro de um ambiente onde o repositorio esteja disponivel pela integracao da plataforma e sempre apontado para a branch ativa configurada na execucao.
3. **Deploy com checkout automatizado**: configurar o job do Hermes para fazer checkout do repositorio antes de rodar, usando uma chave SSH deploy key ou token com escopo minimo.


### Prompt para acesso persistente do Hermes ao repo

Nao usar `git clone` manual em cada execucao. Para automacao, conectar o Hermes uma unica vez ao repositorio pelo conector GitHub/Git da plataforma e manter o acesso persistente de leitura.

URL do repo para configurar no conector Hermes:

```text
https://github.com/<ORG_OU_USUARIO>/social_media-analytics
```

Se o Hermes exigir identificador em vez de URL, usar:

```text
<ORG_OU_USUARIO>/social_media-analytics
```

Prompt de bootstrap para Hermes apos conectar o repo:

```text
Voce tem acesso persistente ao repositorio:
https://github.com/<ORG_OU_USUARIO>/social_media-analytics

Nao faca git clone manual a cada execucao. Use o conector do repositorio para ler os arquivos atuais na branch ativa configurada para a rotina.

Use sempre a branch ativa configurada na execucao do Hermes. Nao trocar para outra branch por conta propria.

Antes de executar a rotina Fenabrave/LinkedIn, leia os documentos nesta ordem:

1. AGENTS.md
2. docs/project/07_SPRINT_AGENDA.md
3. docs/project/02_ROADMAP.md
4. docs/project/README_GESTAO_PROJETO.md
5. docs/data_model/03_DATA_QUALITY_CHECKS.md
6. docs/project/04_PIPELINE_STATUS.md
7. docs/project/05_DECISOES_TECNICAS.md
8. docs/README.md
9. .codex/skills/fenabrave-monthly-source/SKILL.md
10. .codex/skills/fenabrave-monthly-source/references/monthly-hermes-runbook.md
11. .codex/skills/linkedin-automotive-posts/SKILL.md
12. .codex/skills/linkedin-automotive-posts/references/persona-e-estilo.md

Depois gere uma previa unica do post mensal Fenabrave, usando apenas autos + comerciais leves, foco em varejo, comparacoes obrigatorias e regras editoriais do runbook. Envie o resultado para meu Telegram se o conector estiver configurado; caso contrario, retorne a mensagem pronta para copiar.
```

Substituir `<ORG_OU_USUARIO>` pela organizacao ou usuario real do GitHub/Git antes de colar o prompt no Hermes. Nao versionar token, chave SSH ou credencial do Telegram no repositorio.

Checklist minimo de acesso:

- Hermes consegue ler `.codex/skills/fenabrave-monthly-source/SKILL.md`.
- Hermes consegue ler `.codex/skills/linkedin-automotive-posts/SKILL.md`.
- Hermes consegue ler `.codex/skills/fenabrave-monthly-source/references/monthly-hermes-runbook.md`.
- Hermes consegue ler `AGENTS.md` para respeitar as regras operacionais do projeto.
- Hermes consegue ler `docs/project/07_SPRINT_AGENDA.md` e documentos relacionados quando a execucao exigir contexto de governanca.
- Hermes esta usando a branch ativa configurada para a rotina, sem assumir branch fixa.

Nao colocar tokens, chaves SSH ou credenciais do Telegram dentro do repositorio. Usar secrets do ambiente do Hermes, variaveis seguras ou o gerenciador de credenciais da plataforma.

## Chamada unica via Hermes com envio ao Telegram

Use este bloco quando quiser rodar a rotina uma vez para revisar o resultado antes de transformar em automacao mensal.

Prompt recomendado para Hermes:

```text
Use a skill fenabrave-monthly-source e depois a skill linkedin-automotive-posts.

Objetivo: gerar uma previa unica do post mensal Fenabrave para LinkedIn e enviar o resultado para meu Telegram.

Parametros:
- Periodo alvo: mes anterior ao mes corrente, salvo se eu informar outro periodo.
- Fonte: pagina oficial de emplacamentos da Fenabrave.
- Escopo: somente autos + comerciais leves (LCV).
- Analise obrigatoria: varejo mes vs mes -1, marcas no varejo, carros/modelos mais vendidos, acumulado ano vs acumulado equivalente anterior, percentual venda direta vs varejo e comparacao mes/ano vs mesmo mes do ano anterior quando houver discrepancia da ordem de 10% ou mais.
- Restricao editorial: nao mencionar eletricos ou hibridos a menos que aparecam entre os tops analisados.
- Saida: post humanizado para LinkedIn, curto, com poucos bullets, seguido de um resumo tecnico de fonte/periodo/limites.
- Entrega: enviar a mensagem final para meu Telegram.
```

Se Hermes tiver ferramenta/conector de Telegram, enviar a mensagem final diretamente. Se nao houver conector configurado, Hermes deve retornar:

1. o post final;
2. o resumo tecnico;
3. a mensagem pronta para copiar e colar no Telegram;
4. uma nota dizendo que o envio automatico depende de `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` ou de um conector equivalente ja configurado.

## Payload sugerido para entrega Telegram

```text
Titulo: Previa post Fenabrave <mes/ano>

<Post LinkedIn>

---
Fonte: Fenabrave
Periodo: <mes/ano>
Pagina: <source_page_url>
PDF: <source_url>
Limites: emplacamento como proxy; varejo usado como sinal de intencao do consumidor; recorte autos + LCV.
```

Evitar mandar para Telegram mensagens muito longas. Se o texto passar de aproximadamente 3.500 caracteres, Hermes deve enviar primeiro o post final e depois um segundo envio com fonte, periodo e limites.

## Criterios de bloqueio

Nao gerar post definitivo quando:

- a fonte oficial nao foi confirmada;
- o periodo do PDF nao bate com o periodo alvo;
- os numeros principais nao foram extraidos ou validados;
- o recorte mistura categorias fora de autos + LCV sem justificativa;
- falta a divisao percentual entre venda direta e varejo;
- o texto depende de dado externo nao fornecido ou nao confirmado.
