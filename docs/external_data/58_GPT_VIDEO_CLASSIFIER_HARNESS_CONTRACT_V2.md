# Harness GPT de Classificacao Automotiva V2

## Objetivo

Definir o contrato operacional para classificar videos automotivos com GPT
usando a Taxonomia Video V2 como referencia obrigatoria.

Este documento descreve entradas, saida aceitavel, validacoes e estrutura de
banco. Ele nao implementa metodo de ingestao, coleta de dados, worker, cloud
job, dashboard ou pipeline automatizado.

O classificador deve atuar como especialista da industria automotiva. A funcao
dele nao e opinar, prever ou completar lacunas por plausibilidade; e classificar
somente o que estiver sustentado por evidencia textual disponivel.

## Fontes canonicas da Taxonomia V2

A versao operacional inicial da V2 usa:

- `docs/external_data/42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv`
- `docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`
- `docs/external_data/40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md`
- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.md`

Snapshot documentado:

- topic paths: `104`
- regras de compatibilidade tecnica: `91`
- sha256 `42`: `E35004D64E81AAFB8B1FF8615FA67D52B1994D0D859F25C803FEEB43E6793298`
- sha256 `43`: `F3376D76F841871C961BEEA6B4CEDAF308A0755E43DE816C122B81BCCDAF5AB2`

## Estrutura Supabase

A DDL oficial desta etapa esta em:

- `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
- `sql/ddl/views/023_create_v_video_classification_latest.sql`
- `sql/ddl/tests/011_test_video_taxonomy_classification.sql`

Tabelas de referencia:

- `video_taxonomy_versions`
- `video_taxonomy_topic_paths`
- `video_taxonomy_technical_compatibility`
- `video_taxonomy_terms`

Tabelas de classificacao:

- `video_classification_runs`
- `video_classification_results`
- `video_classification_technical_contexts`
- `video_classification_vehicle_entities`

Views:

- `v_video_classification_latest`
- `v_video_classification_quality`

## Entrada do harness

Cada chamada classifica um unico video em um unico estagio.

Campos minimos:

- `post_id`
- `evaluation_stage`: `title_metadata` ou `transcript_90s`
- `title`
- `creator`
- `video_type`
- `duration`
- `description`, quando disponivel
- `transcript_90s`, obrigatorio apenas para `transcript_90s`
- `taxonomy_version`
- lista valida de `topic_path`
- matriz valida de compatibilidade tecnica
- termos controlados de `content_type`, `audience_intent`, `context_role` e
  `compatibility_status`

Regra de evidencia:

- `title_metadata` classifica apenas com titulo, descricao disponivel e
  metadados.
- `transcript_90s` classifica com titulo, descricao disponivel, metadados e
  transcricao dos primeiros `90s`.
- Se uma informacao nao estiver no input, ela nao pode ser inventada.

## Decisao operacional de estagio

Para uso operacional do classificador, o estagio principal passa a ser uma
unica chamada `transcript_90s`, combinando:

- titulo;
- metadados confiaveis;
- descricao quando existir;
- transcricao textual dos primeiros `90s`, gerada por GPT Transcribe.

O estagio `title_metadata` permanece valido, mas com finalidade diagnostica,
amostral e de calibracao. Ele serve para medir o quanto titulo/metadados
sozinhos induzem acertos, erros conservadores, `fora_escopo` ou
`sem_match_taxonomico`.

Motivo da decisao:

- uma unica classificacao combinada evita duplicar prompt, taxonomia, matriz de
  compatibilidade e JSON de saida;
- a transcricao reduz inferencias ruins em titulos vagos ou sensacionalistas;
- o custo por chamada aumenta em relacao ao titulo puro porque ha mais tokens de
  entrada, mas tende a ser menor que executar duas classificacoes completas
  separadas para o mesmo video;
- a saida operacional continua sendo uma unica resposta imputavel no Supabase.

Regra pratica:

- usar `title_metadata` apenas quando o objetivo explicito for auditoria,
  comparacao metodologica ou priorizacao previa de lote;
- usar `transcript_90s` como classificacao oficial quando a transcricao estiver
  disponivel;
- gerar a transcricao operacional com `gpt-4o-mini-transcribe`, ou modelo GPT
  de transcricao definido posteriormente, antes da chamada classificadora;
- nao gravar duas classificacoes como se ambas fossem resultado operacional
  equivalente, salvo rodada experimental com `round_id` separado.

## Skill GPT

A skill do classificador e o conjunto de instrucoes enviado na chamada da API.
Ela deve ser referenciada pelo executor futuro do Google Cloud e versionada como
contrato, nao como skill local do Codex.

Versao operacional r2:

- `prompt_contract_version = video_taxonomy_v2_classifier_r2`
- `output_schema_version = video_taxonomy_v2_output_schema_r2`
- modelo de classificacao por titulo/metadados: `gpt-5-nano`
- modelo de transcricao dos `90s`: `gpt-4o-mini-transcribe`
- modelo de classificacao operacional com titulo/metadados/transcricao:
  `gpt-5-nano`
- skill: `docs/external_data/58_GPT_VIDEO_CLASSIFIER_SKILL_V2.md`
- schema: `docs/external_data/58_GPT_VIDEO_CLASSIFIER_OUTPUT_SCHEMA_V2.json`

O schema privilegia estrutura, campos obrigatorios e enumeracoes. Regras
semanticas mais fortes, como existencia de `topic_path`, faixa de
`confidence_score`, proibicao de `barulho` como problema canonico e ausencia de
valores concatenados por `;`, devem ser verificadas pelo harness e pelas
constraints SQL antes da gravacao.

Decisao operacional:

- usar `gpt-5-nano` para `title_metadata` apenas em diagnostico/calibracao
- usar `gpt-4o-mini-transcribe` somente para transformar audio em texto; nao
  usar Whisper/local como fonte operacional desta fase
- usar `gpt-5-nano` para a classificacao operacional `transcript_90s`, com
  titulo, metadados e transcricao no mesmo input
- nao aplicar fallback automatico para `gpt-5.4-mini` nesta fase
- avaliar a qualidade real do `gpt-5-nano` depois da primeira implementacao e
  comparar com o baseline humano/GPT ja documentado

Instrucao central da skill:

```text
Voce e um classificador da industria automotiva. Classifique o video apenas com
base nas evidencias textuais fornecidas. Use somente a Taxonomia Video V2 e a
matriz de compatibilidade tecnica recebidas no input. Quando a evidencia nao
sustentar uma classificacao, deixe o campo vazio/null quando permitido e registre
o motivo em validation_issues. Termos fora da taxonomia devem ir para
taxonomy_gaps, nunca para campos canonicos.
```

## Saida aceitavel

A resposta deve ser JSON estruturado e imputavel diretamente no banco:

```json
{
  "classification_result": {
    "post_id": "string",
    "evaluation_stage": "title_metadata",
    "input_evidence_level": "metadata_only",
    "automotive_domain": "review_teste",
    "activity_type": "review",
    "topic_path": "review_teste__review_veiculo",
    "content_type": "review",
    "audience_intent": "decidir_compra",
    "confidence_score": 0.85,
    "evidence_summary": "Titulo indica avaliacao de veiculo; metadados nao trazem falha tecnica.",
    "taxonomy_gaps": null,
    "validation_issues": null,
    "needs_human_review": false,
    "taxonomy_version": "taxonomia_video_v2"
  },
  "technical_contexts": [],
  "vehicle_entities": []
}
```

Campos de saida:

- `classification_result`: linha principal para
  `video_classification_results`.
- `technical_contexts[]`: linhas filhas para
  `video_classification_technical_contexts`.
- `vehicle_entities[]`: linhas filhas para
  `video_classification_vehicle_entities`.

## Regras obrigatorias

- Nao inferir sem evidencia textual explicita.
- Nao usar conhecimento externo para completar marca, modelo, ano, sistema,
  componente ou problema.
- `topic_path` deve existir na Taxonomia V2.
- `topic_path_secondary` nao faz parte desta revisao de contrato.
- Termo fora da Taxonomia V2 entra em `taxonomy_gaps`, nao em campo canonico.
- `fora_escopo` tem precedencia quando houver evidencia textual de moto,
  nao-automotivo, transito/comportamento ou entretenimento sem tema tecnico,
  comercial ou produto automotivo principal.
- `sem_match_taxonomico` deve ser usado quando o input for automotivo ou
  possivelmente automotivo, mas nao houver match seguro em nenhum `topic_path`
  especifico da Taxonomia V2.
- `sem_match_taxonomico` exige `needs_human_review=true`,
  `confidence_score < 0.50`, `technical_contexts=[]` e registro do motivo em
  `validation_issues`.
- Titulos genericos como alerta, cuidado, perigo ou entretenimento nao
  autorizam inferir diagnostico, luz de painel, scanner, motor, cambio,
  sistema ou componente sem sinal textual direto.
- `technical_contexts[]` so entra quando houver evidencia explicita de sistema,
  componente ou problema.
- Cada item tecnico representa uma unica combinacao coerente de sistema,
  componente e problema.
- Nenhum campo tecnico pode conter multiplos valores concatenados.
- Marca, modelo, ano e geracao so entram quando aparecerem explicitamente no
  titulo, descricao, transcricao ou metadado confiavel.
- `motor` e `cambio` nunca sao rotulos soltos; entram apenas como sistema,
  componente ou rota contextualizada.
- Videos de moto permanecem `fora_escopo`.
- Videos fora do escopo automotivo nao devem receber contexto tecnico principal.
- `confidence_score` mede a forca da evidencia disponivel, nao a plausibilidade
  externa.

## Nivel de evidencia

Valores recomendados para `input_evidence_level`:

- `metadata_only`: titulo e metadados, sem descricao.
- `title_description`: titulo, metadados e descricao.
- `transcript_90s`: titulo, metadados e transcricao dos primeiros 90s.
- `insufficient_evidence`: input insuficiente para classificacao confiavel.

## Qualidade da transcricao como evidencia

Quando `evaluation_stage = transcript_90s`, o classificador deve avaliar a
qualidade textual do transcript recebido antes de usar essa evidencia para
classificar.

Essa avaliacao nao e uma nota de qualidade do audio, porque o GPT classificador
recebe texto, nao o audio original. Ela mede se o texto transcrito e suficiente,
coerente e especifico para sustentar a classificacao automotiva.

Campos recomendados para a proxima revisao do schema:

```json
{
  "transcript_quality": {
    "quality_score": 0.0,
    "quality_status": "usable",
    "issues": null,
    "impact_on_classification": "low",
    "needs_retranscription": false
  }
}
```

Escala de `quality_score`:

- `0.90` a `1.00`: transcript claro, coerente e especifico.
- `0.70` a `0.89`: transcript utilizavel, com pequenas incertezas.
- `0.50` a `0.69`: transcript parcialmente utilizavel; exige cuidado.
- abaixo de `0.50`: transcript ruim para classificacao; revisar ou
  retranscrever.

Valores de `quality_status`:

- `usable`
- `partially_usable`
- `poor`
- `empty`

Valores de `impact_on_classification`:

- `none`
- `low`
- `medium`
- `high`

Regras:

- transcript vazio ou muito curto deve gerar `quality_status = empty` ou
  `poor`, `needs_retranscription = true` e `needs_human_review = true`.
- frases truncadas, palavras sem sentido, nomes de marca/modelo degradados ou
  trechos incoerentes devem reduzir `quality_score`.
- se a classificacao depender de um trecho confuso, reduzir tambem
  `confidence_score`.
- se titulo/metadados indicarem uma coisa e o transcript indicar outra, marcar
  `needs_human_review = true` e registrar a divergencia em `validation_issues`.
- nao usar `transcript_quality` para salvar o transcript completo; ela deve
  resumir apenas a confiabilidade da evidencia textual recebida.
- quando a evidencia do transcript for fraca, o classificador deve preferir
  `sem_match_taxonomico`, `validation_issues` ou revisao humana a uma
  classificacao por plausibilidade.

## Entidades de veiculo

`vehicle_entities[]` registra entidades extraidas, nao entidades imaginadas.

Campos:

- `vehicle_brand_raw`
- `vehicle_model_raw`
- `vehicle_year`
- `vehicle_generation`
- `evidence_text`
- `entity_status`

Valores de `entity_status`:

- `extracted`: entidade explicita extraida, ainda sem homogeneizacao.
- `matched`: entidade reconciliada com catalogo externo.
- `not_found`: entidade explicita nao encontrada no catalogo usado.
- `needs_review`: entidade ambigua ou contraditoria.

O match com Carros na Web/Fenabrave ocorre depois da extracao. O GPT nao deve
trocar a grafia bruta por uma grafia canonica sem evidencia ou sem etapa de
matching.

## Technical context repetivel

`technical_contexts[]` deve seguir o contrato do doc `50`:

- uma linha por combinacao coerente de `automotive_system`, `component` e
  `problem`;
- `context_role` em `primary`, `secondary`, `supporting` ou `incidental`;
- `compatibility_status` em `allowed`, `allowed_with_evidence`,
  `not_applicable` ou `needs_review`;
- `barulho` pode aparecer como evidencia textual, mas o problema canonico e
  `ruido`.

Exemplo:

```json
{
  "context_order": 1,
  "topic_path": "manutencao_reparo__manutencao_preventiva__suspensao",
  "automotive_system": "suspensao",
  "component": "amortecedor",
  "problem": "ruido",
  "context_role": "primary",
  "evidence_text": "o titulo/transcricao menciona barulho na suspensao",
  "compatibility_status": "allowed_with_evidence",
  "validation_issue": null,
  "needs_human_review": false
}
```

## Validacao antes de gravar

A resposta deve ser rejeitada ou marcada para revisao quando:

- nao validar contra o schema JSON;
- retornar `topic_path` inexistente;
- retornar contexto tecnico incompatibilizado sem `needs_human_review`;
- preencher marca/modelo/ano sem evidencia;
- preencher contexto tecnico principal em video `fora_escopo`;
- concatenar multiplos valores em uma celula/campo;
- usar `barulho` como `problem` canonico;
- usar `motor` ou `cambio` como rotulo solto de tema.

## Fora de escopo desta entrega

- Metodo de ingestao de videos.
- Metodo de ingestao de transcricoes.
- Script de execucao local.
- Worker ou job Google Cloud.
- Mudanca no dashboard.
- Migracao de classificacoes historicas.
- Alteracao do workbook humano.

## Criterio de aceite

- A estrutura SQL recebe Taxonomia V2 e classificacoes por estagio.
- O contrato do harness define entradas e saidas sem ambiguidade.
- A saida GPT e imputavel diretamente no banco.
- A resposta aceitavel impede achismos e exige evidencia.
- A documentacao registra que a execucao futura sera feita por rotina Google
  Cloud separada.
