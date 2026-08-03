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

### Como as tabelas se ligam

O contrato operacional usa uma estrutura em cadeia:

```text
video_taxonomy_versions
  1:N -> video_classification_runs
           1:N -> video_classification_results
                    1:N -> video_classification_technical_contexts
                    1:N -> video_classification_vehicle_entities
```

Ligacoes principais:

- `video_classification_runs.taxonomy_version_id` aponta para
  `video_taxonomy_versions.id`.
- `video_classification_results.run_id` aponta para
  `video_classification_runs.id`.
- `video_classification_results.taxonomy_version_id` aponta para
  `video_taxonomy_versions.id`.
- `video_classification_results.post_id` aponta para `posts.post_id`.
- `video_classification_technical_contexts.classification_result_id` aponta
  para `video_classification_results.id`.
- `video_classification_vehicle_entities.classification_result_id` aponta para
  `video_classification_results.id`.

Ligacoes taxonomicas:

- `video_classification_results.topic_path` e
  `topic_path_secondary` apontam para
  `video_taxonomy_topic_paths.topic_path_code` dentro da mesma
  `taxonomy_version_id`.
- `video_classification_technical_contexts.topic_path` e
  `topic_path_secondary` seguem a mesma regra.

Ligacao com Carros na Web:

- `video_classification_vehicle_entities.catalog_row_id` referencia o
  identificador exposto por `v_carrosnaweb_vehicle_catalog.catalog_row_id`.
- Esse `catalog_row_id` vem de `market_carrosnaweb_model_years.id`.
- `video_classification_vehicle_entities.catalog_model_id` referencia o modelo
  canonico em `market_carrosnaweb_models.id` quando o texto nao sustenta ano.
- Como `v_carrosnaweb_vehicle_catalog` e uma view, essa ligacao e preenchida
  pelo harness e auditada por status/confidence, nao por FK direta no banco.

Em termos praticos:

- um `post` pode ter varias classificacoes ao longo de rodadas e estagios;
- cada classificacao pertence a uma rodada e a uma versao da taxonomia;
- cada classificacao pode ter zero ou mais contextos tecnicos;
- cada classificacao pode ter zero ou mais entidades de veiculo;
- cada entidade de veiculo pode apontar para um item canonico do catalogo
  Carros na Web quando o match for seguro.

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
- `public.posts` nao possui descricao nesta etapa; portanto o executor envia
- `description = null` por padrao e nao tenta capturar esse dado
  implicitamente.
- Em rodadas manuais de calibracao, o executor pode receber um CSV externo de
  descricoes obtidas pela YouTube Data API e adicionar `description` ao JSON do
  harness. Essa opcao nao altera `public.posts`, nao cria ingestao oficial e
  deve preservar `input_evidence_level = title_description` quando a descricao
  estiver preenchida.
- Se uma informacao nao estiver no input, ela nao pode ser inventada.

## Decisao operacional de estagio

Para uso operacional do classificador, o estagio principal passa a ser uma
unica chamada `transcript_90s`, combinando:

- titulo;
- metadados confiaveis;
- `description = null` enquanto o campo nao existir em `public.posts`, exceto
  rodadas manuais com CSV externo de descricoes;
- transcricao textual dos primeiros `90s`, gerada localmente por
  `faster-whisper`.

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
- gerar a transcricao operacional com `faster-whisper`, modelo `small`, CPU e
  `compute_type=int8`, antes da chamada classificadora;
- nao gravar duas classificacoes como se ambas fossem resultado operacional
  equivalente, salvo rodada experimental com `round_id` separado.

## Skill GPT

A skill do classificador e o conjunto de instrucoes enviado na chamada da API.
Ela deve ser referenciada pelo executor manual da VPS e versionada como
contrato, nao como skill local do Codex.

Versao inicial:

- `prompt_contract_version = video_taxonomy_v2_classifier_r2`
- `output_schema_version = video_taxonomy_v2_output_schema_r2`
- modelo de classificacao por titulo/metadados: `gpt-5-nano`
- modelo de transcricao local dos `90s`: `faster-whisper small`
- fallback de transcricao local: `faster-whisper medium`, acionado uma unica
  vez por gatilhos objetivos de qualidade ou perda de informacao
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
- usar `faster-whisper small` localmente para transformar audio em texto, sem
  chamada OpenAI de transcricao
- usar `faster-whisper medium` como fallback automatico quando a tentativa
  `small` indicar risco objetivo: `transcript_quality_score < 0.70`,
  `quality_status=poor|empty`, `topic_path` generico, entidade de veiculo mal
  resolvida, contexto tecnico em `needs_review` ou termo tecnico estrategico sem
  contexto preenchido
- usar `gpt-5-nano` para a classificacao operacional `transcript_90s`, com
  titulo, metadados e transcricao no mesmo input
- nao aplicar fallback automatico para `gpt-5.4-mini` nesta fase
- avaliar a qualidade real do `gpt-5-nano` depois da primeira implementacao e
  comparar com o baseline humano/GPT ja documentado

O fallback `medium` nao altera o contrato do banco nem cria duas classificacoes
operacionais. A tentativa inicial fica apenas como metadado sanitizado em
`input_payload.video.transcription_metadata`, com motivo do fallback, modelo
inicial, modelo final, `topic_path` inicial e qualidade inicial. O transcript
completo continua fora do Supabase. Se o fallback falhar, a classificacao valida
do `small` pode ser gravada com `needs_human_review=true` e `fallback_error`.

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
    "topic_path_secondary": null,
    "content_type": "review",
    "audience_intent": "decidir_compra",
    "confidence_score": 0.85,
    "evidence_summary": "Titulo indica avaliacao de veiculo; metadados nao trazem falha tecnica.",
    "taxonomy_gaps": null,
    "validation_issues": null,
    "needs_human_review": false,
    "taxonomy_version": "taxonomia_video_v2"
  },
  "transcript_quality": {
    "quality_score": null,
    "quality_status": "not_evaluated",
    "issues": [],
    "impact_on_classification": "none",
    "needs_retranscription": false
  },
  "technical_contexts": [],
  "vehicle_entities": []
}
```

Campos de saida:

- `classification_result`: linha principal para
  `video_classification_results`.
- `transcript_quality`: avaliacao textual da transcricao; em `title_metadata`
  deve usar `not_evaluated`.
- `technical_contexts[]`: linhas filhas para
  `video_classification_technical_contexts`.
- `vehicle_entities[]`: linhas filhas para
  `video_classification_vehicle_entities`.

## Regras obrigatorias

- Nao inferir sem evidencia textual explicita.
- Nao usar conhecimento externo para completar marca, modelo, ano, sistema,
  componente ou problema.
- `topic_path` deve existir na Taxonomia V2.
- `topic_path` representa a proposta principal do video, nao o primeiro detalhe
  tecnico forte citado na transcricao.
- Quando houver evidencia clara de uma rota especifica, o classificador nao
  deve responder apenas com o no pai generico. Exemplos:
  `manutencao_reparo__reparo_corretivo__troca_motor` em vez de
  `manutencao_reparo`, `diagnostico__falha_motor` em vez de `diagnostico`, e
  `mercado_produto__compra_venda__carro_popular` em vez de
  `mercado_produto`.
- `topic_path_secondary` so entra quando houver segundo tema forte e explicito.
- Em videos de `review_teste` ou `mercado_produto`, motor, cambio, bateria,
  autonomia, turbo, flex ou eletrico devem ficar em `technical_contexts[]` ou
  `topic_path_secondary` quando forem atributos do veiculo ou argumentos dentro
  do review/mercado.
- `powertrain` so deve ser `topic_path` principal quando a proposta do video for
  explicitamente motorizacao, autonomia, recarga, consumo, cambio ou tecnologia
  de propulsao.
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
- Se houver varios sistemas, componentes ou problemas, cada combinacao deve
  virar uma linha separada em `technical_contexts[]`; se nao houver defeito ou
  sintoma explicito, `problem` deve ficar `null`.
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

Bloco obrigatorio no schema operacional:

```json
{
  "transcript_quality": {
    "quality_score": 0.0,
    "quality_status": "usable",
    "issues": [],
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

Valores controlados de `issues`:

- `too_short`
- `truncated`
- `incoherent`
- `degraded_entities`
- `degraded_technical_terms`
- `excessive_noise`

Regras:

- transcript vazio ou muito curto deve gerar `quality_status = empty` ou
  `poor`, `needs_retranscription = true` e `needs_human_review = true`.
- frases truncadas, palavras sem sentido, nomes de marca/modelo degradados ou
  trechos incoerentes devem reduzir `quality_score`.
- se a classificacao depender de um trecho confuso, reduzir tambem
  `confidence_score`.
- se titulo/metadados indicarem uma coisa e o transcript indicar outra, marcar
  `impact_on_classification = high`, `needs_human_review = true` e registrar a
  divergencia em `validation_issues`.
- impacto `medium` limita `confidence_score` a `0.69`; impacto `high` limita a
  `0.49`.
- nao usar `transcript_quality` para salvar o transcript completo; ela deve
  resumir apenas a confiabilidade da evidencia textual recebida.
- quando a evidencia do transcript for fraca, o classificador deve preferir
  `sem_match_taxonomico`, `validation_issues` ou revisao humana a uma
  classificacao por plausibilidade.

## Entidades de veiculo

`vehicle_entities[]` registra entidades extraidas, nao entidades imaginadas.
Essas entidades precisam ser reconciliadas pelo harness contra o catalogo
Carros na Web antes da gravacao, porque o identificador canonico do veiculo e
parte essencial da classificacao operacional.

Campos:

- `vehicle_brand_raw`
- `vehicle_model_raw`
- `vehicle_year`
- `vehicle_generation`
- `evidence_text`
- `entity_status`
- campos canônicos persistidos pelo harness:
  - `canonical_manufacturer_name`
  - `canonical_model_name`
  - `canonical_model_year`
  - `catalog_row_id`
  - `catalog_model_id`
  - `catalog_match_level`
  - `match_source`
  - `match_confidence`
  - `validation_issue`

Valores de `entity_status`:

- `extracted`: entidade explicita extraida, ainda sem homogeneizacao.
- `matched`: entidade reconciliada com catalogo externo.
- `not_found`: entidade explicita nao encontrada no catalogo usado.
- `needs_review`: entidade ambigua ou contraditoria.

O match com Carros na Web ocorre depois da extracao e antes da gravacao. O GPT
nao deve retornar `catalog_row_id`, `catalog_model_id`, nem trocar a grafia
bruta por uma grafia canonica sem evidencia. O identificador canonico deve vir
de consulta deterministica a `public.v_carrosnaweb_vehicle_catalog`.

O harness tambem executa uma extracao deterministica de veiculos a partir de
`title`, `description` e `transcript_90s`. Essa extracao por script e a fonte
operacional de verdade para marca/modelo canonicos, porque evita enviar a lista
Carros na Web ao GPT e evita uma segunda chamada de modelo.

Para evitar falsos positivos, modelos que tambem sao palavras comuns exigem
marca explicita e proxima no texto antes de virarem entidade. Na rodada Batch 1,
os termos condicionais iniciais sao `100`, `tipo`, `bora` e `link`. Exemplos:
`Audi 100`, `Fiat Tipo` e `Volkswagen Bora` podem ser aceitos; `100%`,
`bora para o canal`, `tipo SKD` e `link na descricao` nao devem gerar
`vehicle_entity`.

O harness pode aplicar reparos conservadores antes da gravacao quando o erro
for mecanico e nao semantico. `topic_path` e `topic_path_secondary` podem ser
corrigidos apenas quando houver um unico codigo canonico compativel na
Taxonomia V2; por exemplo, `mercado_procuto__lancamentos` pode ser reparado
para `mercado_produto__lancamentos`. `vehicle_entities[].entity_order` pode ser
reordenado pelo harness para garantir sequencia iniciando em `1`.

Obrigacao de extracao:

- se marca/modelo e ano-modelo estiverem explicitamente no titulo, descricao ou
  transcricao, o GPT deve preencher `vehicle_year`;
- deixar `vehicle_year = null` quando o ano aparece explicitamente deve ser
  tratado como erro de qualidade da classificacao ou motivo de reprocessamento;
- o ano extraido continua sendo evidencia textual, nao inferencia externa.
- quando o texto trouxer apenas o modelo, o script pode preencher a montadora
  canonica se o modelo for unico no catalogo; exemplo: `Kwid` resolve para
  `Renault/Kwid` em nivel de modelo.

Regra de prontidao:

- se marca, modelo e ano forem encontrados com match unico no catalogo, gravar
  `entity_status = matched`, `catalog_row_id`, `catalog_model_id`, nomes
  canonicos, `catalog_match_level = model_year` e
  `match_confidence` alto;
- se marca/modelo forem encontrados mas o ano estiver ausente, gravar
  `catalog_model_id`, nomes canonicos, `entity_status = matched`,
  `catalog_match_level = model` e deixar `catalog_row_id = null`;
- se a entidade explicita nao existir no catalogo, gravar
  `entity_status = not_found`, `catalog_match_level = not_found` e
  `validation_issue`;
- se houver varios matches possiveis, gravar `needs_review`.

Na pratica, a classificacao so deve ser considerada pronta para pesquisa de
mercado quando `vehicle_entities[]` trouxer o identificador do catalogo ou uma
justificativa explicita de `not_found`/`needs_review`.

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
  "topic_path_secondary": null,
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
- retornar `topic_path_secondary` inexistente;
- retornar contexto tecnico incompatibilizado sem `needs_human_review`;
- preencher marca/modelo/ano sem evidencia;
- preencher contexto tecnico principal em video `fora_escopo`;
- concatenar multiplos valores em uma celula/campo;
- usar `barulho` como `problem` canonico;
- usar `motor` ou `cambio` como rotulo solto de tema.

## Fora de escopo desta entrega

- Metodo de ingestao de videos.
- Ingestao persistente de transcricoes completas.
- Worker ou job Google Cloud.
- Mudanca no dashboard.
- Migracao de classificacoes historicas.
- Alteracao do workbook humano.

## Criterio de aceite

- A estrutura SQL recebe Taxonomia V2 e classificacoes por estagio.
- O contrato do harness define entradas e saidas sem ambiguidade.
- A saida GPT e imputavel diretamente no banco.
- A resposta aceitavel impede achismos e exige evidencia.
- O executor manual gera os `90s` com `faster-whisper` e usa uma unica chamada
  `gpt-5-nano` para qualidade textual e classificacao.
- O executor usa pausa padrao de `60s` entre videos em lote e fallback
  automatico `small -> medium` apenas no fluxo local de `transcript_90s`.
- O cron permanece desativado ate validacao manual do classificador.
