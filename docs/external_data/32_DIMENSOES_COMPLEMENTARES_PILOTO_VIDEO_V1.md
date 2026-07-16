# Dimensoes Complementares Piloto de Videos v1

## Objetivo

Definir o contrato canonico das dimensoes complementares do piloto de `10`
videos do Sprint 6:

- `vehicle_brand`
- `vehicle_model`
- `vehicle_year_or_generation`
- `automotive_system`
- `component`
- `problem`

Estas dimensoes complementam a taxonomia principal do piloto, mas nao a
substituem.

## Fonte de verdade desta fase

Os artefatos canonicos desta fase sao:

- este documento
- `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.csv`

Eles devem ser usados junto com:

- `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.md`
- `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.csv`

## Papel destas dimensoes

### Regra 1 - Dimensoes complementares nao redefinem o tema

O tema principal continua sendo definido por:

- `niche`
- `sub_niche`
- `sub_sub_niche`

As dimensoes complementares apenas refinam a leitura tecnica do video.

### Regra 2 - Quando faltar evidencia, usar `null`

Nenhuma destas dimensoes deve ser inferida de forma agressiva.

Se a informacao nao estiver clara no titulo, descricao ou contexto forte do
video, o campo deve ficar `null`.

### Regra 3 - Marca e modelo nao sao inferidos pelo canal

`vehicle_brand` e `vehicle_model` so devem ser preenchidos quando o video
indicar isso explicitamente ou com evidencia muito forte.

Nao usar:

- nome do canal
- nicho recorrente do creator
- repertorio historico do creator

como justificativa suficiente para preencher marca ou modelo.

### Regra 4 - `automotive_system` e `component` nao podem contradizer o subnicho

Exemplo correto:

- `niche = diagnostico`
- `sub_niche = scanner_obd2`
- `automotive_system = motor`
- `component = sensor_oxigenio`
- `problem = luz_injecao`

Exemplo incorreto:

- `sub_niche = manutencao_motor`
- `automotive_system = transmissao`

### Regra 5 - `problem` descreve o sintoma ou falha principal

`problem` nao deve descrever:

- o metodo de diagnostico
- o formato editorial
- a categoria do nicho

Ele deve capturar o problema central do caso quando aplicavel.

## Contrato por dimensao

### `vehicle_brand`

Tipo:

- semifechado no piloto

Regra:

- preencher apenas quando a marca estiver explicita
- registrar o nome canonicamente em `Title Case`
- se houver duvida, usar `null`

Exemplos validos:

- `Fiat`
- `Volkswagen`
- `Toyota`
- `Jeep`
- `BYD`
- `GWM`

### `vehicle_model`

Tipo:

- semifechado no piloto

Regra:

- preencher apenas quando o modelo estiver explicito
- registrar o nome do modelo no formato publicamente reconhecido
- nao inferir o modelo apenas pela marca

Exemplos validos:

- `Toro`
- `Compass`
- `Corolla Cross`
- `Hilux`
- `Onix`
- `Nivus`
- `Dolphin`

### `vehicle_year_or_generation`

Tipo:

- hibrido entre valor exato e descritor controlado

Regra:

- usar ano exato quando explicitamente citado
- quando nao houver ano exato, usar apenas descritores controlados do piloto
- nao inventar geracao ou facelift se o video nao deixar isso claro

Descritores controlados do piloto:

- `geracao_atual`
- `geracao_anterior`
- `facelift`
- `pre_facelift`
- `modelo_antigo`
- `modelo_novo`

### `automotive_system`

Tipo:

- fechado no piloto

Valores canonicos:

- `motor`
- `transmissao`
- `freios`
- `suspensao`
- `eletrica_eletronica`
- `arrefecimento`
- `combustivel`
- `direcao`
- `rodas_pneus`
- `carroceria`
- `powertrain`

Regra:

- escolher apenas um sistema principal por video
- usar `powertrain` quando o conteudo for claramente sobre propulsao eletrica,
  hibrida, flex, diesel ou combustao como arquitetura de motorizacao

### `component`

Tipo:

- fechado no piloto

Valores canonicos:

- `pastilha_freio`
- `disco_freio`
- `bateria_12v`
- `alternador`
- `bobina`
- `vela`
- `bico_injetor`
- `sensor_oxigenio`
- `cambio_automatico`
- `modulo_injecao`
- `turbina`

Regra:

- preencher apenas quando a peca ou componente estiver explicito
- se o video falar de sistema, mas nao de peca especifica, usar `null`
- `component` deve ser coerente com `automotive_system`

### `problem`

Tipo:

- fechado no piloto

Valores canonicos:

- `falha_de_motor`
- `luz_injecao`
- `barulho_suspensao`
- `superaquecimento`
- `consumo_alto`
- `perda_potencia`
- `problema_cronico`
- `falha_eletrica`
- `desgaste_prematuro`
- `tranco_cambio`

Regra:

- preencher apenas quando houver problema claro ou sintoma central
- videos puramente review, comparativo ou noticia podem deixar `problem = null`

## Regras de relacionamento

### Scanner e diagnostico

Se o video for sobre `scanner obd2`:

- o `sub_niche` continua em diagnostico
- `automotive_system` pode ser `motor`, `transmissao` ou outro sistema
- `component` e `problem` refinam o caso, sem trocar o tema principal

### Powertrain e motorizacao

Se o video for sobre eletrico, hibrido, flex, diesel ou combustao como tipo de
motorizacao:

- `niche = powertrain`
- `sub_niche` deve usar a taxonomia de motorizacao do item 1
- `automotive_system = powertrain`

### Eletrica e eletronica

Se o video for sobre sensor, modulo, chicote ou bateria `12v`:

- `niche` e `sub_niche` seguem a taxonomia principal
- `automotive_system = eletrica_eletronica`
- `component` e `problem` refinam o caso quando houver clareza

## Casos-guia obrigatorios

### 1. Scanner OBD2 com falha no motor

- `niche = diagnostico`
- `sub_niche = scanner_obd2`
- `automotive_system = motor`
- `component = sensor_oxigenio` quando houver evidencia
- `problem = luz_injecao` ou `perda_potencia` quando houver evidencia

### 2. Video sobre carro hibrido

- `niche = powertrain`
- `sub_niche = hibrido`
- `automotive_system = powertrain`

### 3. Troca preventiva de oleo do cambio

- `niche = manutencao`
- `sub_niche = manutencao_cambio`
- `automotive_system = transmissao`
- `component = cambio_automatico` apenas se isso estiver explicito

### 4. Sensor ou modulo com falha

- `niche = diagnostico` ou `eletrica_eletronica`, conforme o tema principal
- `automotive_system = eletrica_eletronica`
- `component = modulo_injecao` ou `sensor_oxigenio`, se explicito
- `problem = falha_eletrica`, se aplicavel

## Criterio de aceite do item 2

O item 2 do Sprint 6 so deve ser considerado implementado e pronto para uso no
piloto se:

- as `6` dimensoes complementares tiverem contrato claro
- `vehicle_brand` e `vehicle_model` nao forem preenchidos por inferencia fraca
- `automotive_system`, `component` e `problem` nao contradisserem o tema
  principal
- videos de `scanner_obd2` preservarem a logica de diagnostico
- videos de eletrico/hibrido usarem `automotive_system = powertrain`
- o CSV permanecer coerente com este documento

## Fora de escopo desta v1

- tabela definitiva de marcas
- tabela definitiva de modelos
- taxonomia completa de geracoes por modelo
- cruzamento automatico com Fenabrave, Carros na Web ou base de entities
- persistencia definitiva destas dimensoes no banco
