# Taxonomia Piloto de Videos v1

## Objetivo

Definir a taxonomia canonica inicial do piloto de `10` videos do Sprint 6.

Esta taxonomia existe para a fase metodologica de validacao humano vs IA.

Ela ainda nao e uma modelagem de banco, nao substitui `public.sub_niches` e nao
deve gerar seed, migration ou integracao automatica nesta etapa.

## Fonte de verdade desta fase

Os artefatos canonicos desta fase sao:

- este documento
- `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.csv`

Se houver divergencia entre exemplos antigos de outras specs e esta taxonomia
piloto, a taxonomia piloto v1 deve prevalecer para a rodada inicial de `10`
videos.

## Regras canonicas

### Regra 1 - Um termo, um significado

Cada codigo taxonomico deve ter um unico significado.

Termos ambiguos nao entram como categoria canonica.

### Regra 2 - Tema e formato sao coisas diferentes

- `niche`, `sub_niche` e `sub_sub_niche` descrevem o tema automotivo principal
- `content_type` descreve o formato editorial do conteudo

`review`, `comparativo`, `noticia` e `tutorial` nao substituem o tema
automotivo principal quando houver evidencias suficientes para classificacao
tematica.

### Regra 3 - Marca e modelo nao viram subnicho

`vehicle_brand` e `vehicle_model` continuam sendo dimensoes complementares.

Exemplo:

- correto:
  - `niche = diagnostico`
  - `sub_niche = diagnostico_cambio`
  - `vehicle_brand = Jeep`
  - `vehicle_model = Compass`
- incorreto:
  - `sub_niche = jeep_compass`

### Regra 4 - `powertrain` cobre apenas motorizacao

`powertrain` passa a ser o niche usado para tipo de motorizacao:

- `eletrico`
- `hibrido`
- `combustao`
- `flex`
- `diesel`

Nesta v1, `powertrain` nao absorve performance, manutencao, diagnostico ou
arquitetura ampla.

### Regra 5 - `eletrica_eletronica` nao cobre motorizacao

`eletrica_eletronica` continua valida, mas restrita a temas como:

- bateria `12v`
- sensores
- modulos
- chicote
- falhas eletricas e eletronicas em geral

Videos sobre carros eletricos ou hibridos devem cair em `powertrain`, nao em
`eletrica_eletronica`.

### Regra 6 - `motor` e `cambio` nunca aparecem soltos

Os termos `motor` e `cambio` sao proibidos como `sub_niche` isolado.

Eles devem aparecer apenas em formas contextualizadas:

- `manutencao_motor`
- `diagnostico_motor`
- `manutencao_cambio`
- `diagnostico_cambio`

Isso evita colisao entre manutencao e diagnostico.

### Regra 7 - Scanner continua sendo diagnostico

Se o video for sobre `scanner obd2` e o problema estiver no motor ou no
cambio, o tema principal continua sendo diagnostico.

Exemplo:

- `niche = diagnostico`
- `sub_niche = scanner_obd2`
- `automotive_system = motor` ou `transmissao`

Nao usar `motor` ou `cambio` como atalho ambiguo do subnicho.

### Regra 8 - `sub_sub_niche` e opcional

`sub_sub_niche` so deve ser preenchido quando houver evidencia forte e
especifica.

Quando nao houver clareza suficiente, usar `null`.

## Taxonomia v1 fechada

### `niche`

- `manutencao`
- `diagnostico`
- `review`
- `mercado`
- `powertrain`
- `eletrica_eletronica`
- `off_road`
- `compra_venda`

### `sub_niche`

#### `manutencao`

- `troca_oleo`
- `freios`
- `suspensao`
- `pneus`
- `arrefecimento`
- `manutencao_motor`
- `manutencao_cambio`

#### `diagnostico`

- `scanner_obd2`
- `injecao_eletronica`
- `diagnostico_motor`
- `diagnostico_cambio`
- `falha_eletrica`

#### `review`

- `test_drive`
- `comparativo`

#### `mercado`

- `mercado_usados`
- `lancamentos`

#### `powertrain`

- `eletrico`
- `hibrido`
- `combustao`
- `flex`
- `diesel`

#### `eletrica_eletronica`

- `bateria_12v`
- `sensores_modulos`

#### `off_road`

- `preparacao_off_road`

#### `compra_venda`

- `carro_popular`
- `carro_premium`
- `suv`
- `picape`

### `sub_sub_niche`

- `troca_pastilha`
- `problema_cronico`
- `limpeza_bico_injetor`
- `cambio_automatico`
- `sistema_hibrido`
- `falha_sensor`

### `content_type`

- `educativo`
- `tutorial`
- `review`
- `comparativo`
- `noticia`
- `opiniao`
- `entretenimento`
- `alerta`
- `ranking`
- `case`

### `audience_intent`

- `resolver_problema`
- `evitar_prejuizo`
- `aprender_manutencao`
- `decidir_compra`
- `comparar_opcoes`
- `acompanhar_lancamento`
- `entender_powertrain`
- `entender_mercado`
- `entretenimento`

## Regras de uso no piloto

- `niche` e `sub_niche` devem ser sempre preenchidos
- `sub_sub_niche` pode ficar `null`
- um `sub_niche` deve pertencer a exatamente um `niche`
- casos hibridos devem escolher o tema principal do video
- nao criar categoria nova no meio da rodada de `10` videos
- lacunas devem ser registradas para revisao da taxonomia apos a rodada

## Casos-guia obrigatorios

### 1. Carro eletrico ou hibrido

Deve cair em:

- `niche = powertrain`

Exemplos de `sub_niche`:

- `eletrico`
- `hibrido`

### 2. Falha detectada por scanner

Deve cair em:

- `niche = diagnostico`

Exemplos de `sub_niche`:

- `scanner_obd2`
- `diagnostico_motor`
- `diagnostico_cambio`

### 3. Troca ou reparo preventivo

Deve cair em:

- `niche = manutencao`

Exemplos de `sub_niche`:

- `manutencao_motor`
- `manutencao_cambio`
- `freios`
- `troca_oleo`

### 4. Modulo, sensor ou bateria 12v

Deve cair em:

- `niche = eletrica_eletronica`

Exemplos de `sub_niche`:

- `bateria_12v`
- `sensores_modulos`
- `falha_eletrica`

## Criterio de aceite do item 1

O item 1 do Sprint 6 so deve ser considerado implementado e pronto para uso no
piloto se:

- os `10` videos puderem ser classificados sem criacao ad hoc de categoria
- `eletrico` e `hibrido` nao aparecerem em `eletrica_eletronica`
- `motor` e `cambio` nao aparecerem como rotulos isolados
- videos de scanner/OBD2 preservarem a logica de diagnostico
- o CSV permanecer coerente com este documento

## Fora de escopo desta v1

- integracao com `public.sub_niches`
- seed de banco
- migration SQL
- versionamento automatico da taxonomia
- pipeline de classificacao
- prompt final da IA
- persistencia definitiva da classificacao
