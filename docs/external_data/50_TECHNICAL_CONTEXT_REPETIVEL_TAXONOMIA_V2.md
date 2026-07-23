# Technical context repetivel da Taxonomia V2

Data: 2026-07-23

## Objetivo

Definir `technical_context[]` como estrutura repetivel para representar
multiplos sistemas, componentes, problemas e evidencias em videos automotivos.

Esta entrega resolve o gargalo identificado na rodada dos `20` videos com a
Taxonomia V2 enriquecida, sem alterar banco, workbook ou pipeline.

Artefato operacional:

- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.csv`

## Decisao

Os campos agregados:

- `automotive_system`
- `component`
- `problem`

continuam existindo em resultados resumidos, como o CSV `48`, mas passam a ser
tratados como leitura legada/compatibilidade.

A fonte operacional detalhada passa a ser `technical_context[]`, materializada
nesta fase como CSV filho em formato longo:

```text
uma linha = um contexto tecnico coerente
```

Isso evita celulas com multiplos valores separados por `;` e permite validar
cada combinacao contra a matriz tecnica do CSV `43`.

## Regra anti-explosao de subnichos

A Taxonomia V2 separa duas camadas:

- `topic_path`: arvore curta, estavel e navegavel para classificar o tipo de
  conteudo.
- `technical_context[]`: camada profunda e expansivel para registrar os termos
  tecnicos que o video realmente trata.

Nem todo termo novo deve virar `topic_path`, `sub_niche` ou novo nivel da
arvore.

Termos como estes devem ser preservados em `technical_context[]`,
`taxonomy_gaps`, sinonimos ou vocabulario tecnico controlado:

- pecas: `filtro_oleo`, `bomba_oleo`, `pivo_suspensao`;
- sintomas: `borra`, `folga_axial`, `vibracao`, `ruido`;
- procedimentos: `retifica`, `limpeza`, `desmontagem`;
- insumos/produtos: `limpa_radiador`, `aditivo_arrefecimento`;
- entidades: marca, modelo, ano, versao ou tipo de uso do veiculo.

O criterio para promover um termo a `topic_path` deve ser mais forte:

- o termo representa um tipo recorrente de conteudo, nao apenas uma peca;
- ajuda a navegacao humana;
- reduz ambiguidade metodologica;
- pode ser validado contra exemplos suficientes;
- nao duplica informacao que ja cabe melhor em `technical_context[]`.

Exemplo:

```text
topic_path = manutencao_reparo > reparo_corretivo > troca_motor

technical_context[] =
- motor_conjunto / falha_de_motor
- oleo_motor / oleo_vencido
- motor_conjunto / desgaste
- motor_conjunto / folga_axial
- retifica_motor como procedimento citado
```

Nesse caso, `borra`, `carbonizacao`, `oleo_motor`, `folga_axial` e `retifica`
ajudam a entender o video, mas nao precisam virar niveis adicionais da arvore.

## Estrutura do CSV

Colunas:

- `context_id`: identificador unico da linha de contexto.
- `post_id`: video classificado.
- `source_lot`: lote de origem da rodada.
- `context_order`: ordem do contexto dentro do video/lote.
- `topic_path`: rota taxonomica usada para validar aquele contexto.
- `topic_path_secondary`: rota secundaria quando ajuda a explicar a evidencia.
- `automotive_system`: sistema tecnico.
- `component`: componente tecnico.
- `problem`: problema, sintoma ou atributo tecnico.
- `context_role`: papel do contexto no video.
- `evidence_text`: trecho resumido da evidencia usada.
- `compatibility_status`: resultado da validacao contra a matriz tecnica.
- `validation_issue`: problema ou ressalva de validacao.
- `needs_human_review`: se a linha exige revisao humana.
- `round_id`: rodada que gerou o contexto.

## Valores de `context_role`

Valores fechados:

- `primary`: contexto tecnico principal do video ou do trecho.
- `secondary`: segundo contexto forte e explicito.
- `supporting`: contexto tecnico complementar, citado como parte do procedimento.
- `incidental`: mencao tecnica incidental que nao deve contaminar o tema
  principal.

Regra:

- um video pode ter varios `supporting`;
- `fora_escopo` nao pode ter contexto `primary`;
- `incidental` pode ter campos tecnicos vazios quando a mencao nao deve virar
  classificacao tecnica.

## Regras de classificacao

Preencher `technical_context[]` somente quando houver evidencia explicita em:

- titulo;
- descricao;
- transcript;
- observacao humana documentada.

Cada linha deve representar uma unica combinacao coerente:

```text
automotive_system + component + problem
```

Nao usar `;` em `automotive_system`, `component` ou `problem`.

Quando o video citar varios componentes:

- criar uma linha por componente;
- preservar a ordem de aparicao ou organizacao em `context_order`;
- marcar `context_role` conforme o papel de cada item.

`context_order` nao e peso de importancia. Ele serve apenas para manter a
sequencia de evidencias ou uma ordenacao operacional estavel.

Quando a combinacao existir no CSV `43`:

- usar `compatibility_status = allowed` ou `allowed_with_evidence`, conforme a
  matriz.

Quando a combinacao ainda nao existir:

- usar `compatibility_status = needs_review`;
- preencher `validation_issue`;
- nao criar codigo canonico novo silenciosamente.

## Relacao com `topic_path`

O `topic_path` principal do video continua sendo a classificacao editorial ou
tematica mais importante.

No `technical_context[]`, o campo `topic_path` pode apontar para a rota tecnica
mais adequada para validar a linha.

Exemplo:

```text
video principal = manutencao_reparo > custo_reparo > manutencao_pesada
contexto tecnico = manutencao_reparo > manutencao_preventiva > cambio_cvt
```

Essa separacao evita forcar todos os componentes de uma manutencao pesada na
mesma rota principal.

## Exemplos obrigatorios

### `_j1gOOnjgcU`

O video cita varias manutencoes simples.

Resultado:

- bateria 12v;
- sensor de oxigenio;
- sensor MAF;
- vela.

Cada item vira uma linha propria no CSV `50`.

### `ITBdyKnV5Pg`

O video e uma manutencao pesada em Honda HR-V 2020.

Resultado:

- suspensao;
- freios;
- motor;
- transmissao/CVT.

O video permanece com revisao humana porque mistura muitos sistemas e ainda
depende de contrato futuro para sumarizacao automatica de contexto tecnico.

### `6qSnrkGd70I`

O video mostra procedimento de arrefecimento.

Resultado:

- fluido de arrefecimento;
- aditivo;
- limpa radiador;
- filtro de arrefecimento.

Cada item fica em linha separada.

### `pINW53ErjQI`

O video e `fora_escopo > transito_comportamento`.

Resultado:

- sem contexto tecnico principal;
- mencoes a carro fervendo e trambulador quebrado ficam incidentais.

### `RTZHxSE2t5M`

O video e setorial, sobre gargalo de oficinas e pecas.

Resultado:

- sem sistema tecnico de veiculo especifico;
- contexto permanece em `pos_venda_reparacao`.

## Impacto operacional

Com esta mudanca:

- o CSV `48` continua servindo como classificacao agregada dos `20` registros;
- o CSV `50` passa a ser a fonte detalhada para contexto tecnico;
- validacoes futuras podem operar linha a linha;
- o workbook e o banco ainda nao mudam.

## Validacao aplicada

A validacao desta entrega deve confirmar:

- todos os `20` registros da rodada aparecem no CSV `50`;
- nenhum campo `automotive_system`, `component` ou `problem` usa multiplos
  valores separados por `;`;
- todo `topic_path` e `topic_path_secondary` existe no CSV `42`;
- `barulho` nao aparece como `problem` canonico;
- `fora_escopo` nao possui contexto `primary`;
- banco, workbook e pipeline permanecem inalterados.

## Proximo passo

Depois de validar o CSV `50`, a proxima decisao metodologica e escolher como
levar `technical_context[]` para a execucao humana:

- atualizar o workbook com uma aba filha;
- ou manter o CSV separado ate a taxonomia V2 virar contrato de banco.
