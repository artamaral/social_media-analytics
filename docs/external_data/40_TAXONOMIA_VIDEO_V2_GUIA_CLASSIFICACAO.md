# Taxonomia Video V2 e Guia de Classificacao

## Objetivo

Definir a proposta metodologica da Taxonomia V2 para classificacao de videos
automotivos, consolidando os aprendizados do piloto humano, da rodada GPT 5.5 e
das transcricoes Whisper dos primeiros `90s`.

Este documento nao substitui ainda os CSVs canonicos da v1:

- `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.csv`
- `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.csv`

A V2 deve ser validada contra o piloto antes de virar workbook ou contrato de
pipeline. Em 2026-07-23, a V2 passou tambem a ter um contrato operacional de
banco para uso controlado pelo classificador GPT, sem alterar coleta, dashboard
ou workbook.

## Por que a v2 existe

A v1 tentou classificar um video principalmente por `niche`, `sub_niche` e
`sub_sub_niche`. O piloto mostrou que isso e insuficiente para videos que
misturam naturezas diferentes, por exemplo:

- `review` de um lancamento com detalhe de `powertrain`
- `mercado` de eletrificados com preco e decisao de compra
- `manutencao` que nasce de um `diagnostico` e termina em custo de reparo
- video de transito que cita carro, mas nao e conteudo automotivo classificavel

Na V2, a classificacao deixa de depender de um unico `niche`. O video passa a
ser descrito por eixos separados:

```text
automotive_domain
activity_type
topic_path
content_type
audience_intent
vehicle_brand
vehicle_model
vehicle_year
year_reference_type
automotive_system
component
problem
taxonomy_gaps
validation_issues
needs_human_review
```

## Regra central

Nao usar uma unica categoria para representar varias naturezas ao mesmo tempo.

O `topic_path` organiza a arvore de navegacao humana. Os outros campos carregam
o contexto editorial, tecnico e de entidade.

Exemplo:

```text
Video: review do Caoa Changan Uni-T flex estreando no Brasil
automotive_domain = mercado_produto
activity_type = lancamento
topic_path = mercado_produto > lancamentos
content_type = review
audience_intent = acompanhar_lancamento
vehicle_brand = Caoa Changan
vehicle_model = Uni-T
automotive_system = powertrain
component = null
problem = null
taxonomy_gaps = motor_flex; tropicalizacao
```

O video nao precisa escolher entre `review`, `mercado` e `powertrain` como se
fossem o mesmo tipo de informacao. Cada eixo guarda uma parte da leitura.

## Campos da V2

### `automotive_domain`

Responde: sobre qual dominio automotivo o video trata?

Valores propostos:

- `fora_escopo`
- `manutencao_reparo`
- `diagnostico`
- `review_teste`
- `mercado_produto`
- `powertrain`
- `pos_venda_reparacao`
- `off_road`

Regra:

- escolher um dominio principal por video
- usar o dominio que melhor explica a promessa central do conteudo
- nao usar o dominio para guardar formato editorial

### `activity_type`

Responde: que tipo de atividade, abordagem ou acao aparece?

Valores iniciais propostos:

- `nao_aplicavel`
- `manutencao_preventiva`
- `reparo_corretivo`
- `diagnostico`
- `orcamento`
- `teste`
- `review`
- `comparacao`
- `lancamento`
- `analise_mercado`
- `opiniao`
- `alerta`
- `entretenimento`

Regra:

- `activity_type` pode revelar sobreposicoes que antes viravam multi-niche
- quando um video tem diagnostico dentro de manutencao, usar
  `automotive_domain = manutencao_reparo` e `activity_type = diagnostico` ou
  `reparo_corretivo`, conforme a evidencia dominante

### `topic_path`

Responde: qual e o caminho hierarquico mais especifico com evidencia?

O `topic_path` e a arvore apresentada ao humano. Deve usar codigos em
`snake_case`, separados por ` > `.

O `topic_path` deve permanecer curto, estavel e navegavel. Ele nao deve tentar
absorver toda a profundidade tecnica do video.

Regra:

- escolher o caminho mais especifico sustentado por evidencia
- nao preencher nivel profundo por inferencia fraca
- quando o caminho ainda nao existir, manter o melhor pai canonico e registrar
  o termo em `taxonomy_gaps`
- nao promover automaticamente pecas, sintomas, insumos, procedimentos,
  marcas, modelos ou termos de fala para subnicho
- usar `topic_path` para responder "qual e o tipo de conteudo?", nao "todos os
  termos tecnicos citados"

Exemplo:

```text
topic_path = manutencao_reparo > reparo_corretivo > troca_motor
```

Esse caminho nao precisa virar:

```text
manutencao_reparo > reparo_corretivo > troca_motor > oleo_motor > borra > folga_axial
```

`oleo_motor`, `borra` e `folga_axial` pertencem ao contexto tecnico, nao a uma
profundidade infinita de subnichos.

### `content_type`

Responde: qual e o formato editorial do video?

Valores iniciais:

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

Regra:

- `content_type` nao substitui o tema automotivo
- um video pode ser `content_type = review` e
  `automotive_domain = mercado_produto`
- quando o video demonstra procedimento passo a passo, preferir `tutorial`
- quando explica conceitos sem passo a passo, preferir `educativo`

### `audience_intent`

Responde: o que a audiencia provavelmente busca ao consumir o video?

Valores iniciais:

- `resolver_problema`
- `evitar_prejuizo`
- `aprender_manutencao`
- `decidir_compra`
- `comparar_opcoes`
- `acompanhar_lancamento`
- `entender_powertrain`
- `entender_mercado`
- `entretenimento`

Regra:

- inferir pela promessa do titulo, descricao e fala inicial
- nao preencher intencao de compra apenas porque ha marca/modelo
- quando a evidencia for fraca, deixar nulo e marcar revisao se o campo for
  importante para a analise

### Entidades do veiculo

Campos:

- `vehicle_brand`
- `vehicle_model`
- `year_reference_type`
- `vehicle_year`
- `vehicle_generation`

Regras:

- preencher marca e modelo apenas quando explicitamente citados ou visiveis com
  evidencia forte
- `vehicle_model` precisa pertencer a `vehicle_brand` quando houver cadastro
  canonico
- separar tipo de referencia temporal do valor:
  - `year_reference_type = exact_year`
  - `vehicle_year = 2026`
- nao usar `exact_year:2026` como codigo composto
- se houver alias ou erro de transcricao, registrar em `validation_issues`

### Contexto tecnico

Campos:

- `technical_context[]`
- `automotive_system` como resumo legado quando necessario
- `component` como resumo legado quando necessario
- `problem` como resumo legado quando necessario

Regra:

- preencher apenas quando houver evidencia tecnica
- cada item de `technical_context[]` representa uma combinacao coerente de
  sistema, componente e problema
- `technical_context[]` captura a profundidade tecnica do video sem inflar a
  arvore de `topic_path`
- sistema filtra componente e problema dentro de cada item
- componente nao deve contradizer sistema
- problema nao deve contradizer sistema
- termos tecnicos evidenciados devem ser preservados como contexto, vocabulario
  tecnico, sinonimo ou lacuna, mas nao promovidos automaticamente para
  subnicho
- `motor` e `cambio` nao devem ser rotulos soltos de tema; devem aparecer como
  sistema tecnico ou em caminhos contextualizados como `reparo_motor` e
  `diagnostico_cambio`

Exemplo coerente:

```text
topic_path = manutencao_reparo > reparo_corretivo > reparo_motor
automotive_system = motor
component = motor_conjunto
problem = falha_de_motor
```

Exemplo incoerente:

```text
topic_path = diagnostico > luz_injecao
automotive_system = suspensao
component = pastilha_freio
problem = consumo_alto
```

Nesse caso, o resultado deve ir para `validation_issues` e
`needs_human_review = true`.

## Hierarquia `topic_path`

### 1. `fora_escopo`

Usar quando o video nao deve entrar na taxonomia automotiva principal, mesmo que
mencione carro de forma incidental.

```text
fora_escopo
fora_escopo > nao_automotivo
fora_escopo > transito_comportamento
fora_escopo > entretenimento_sem_tema_tecnico
```

Regras:

- se o tema principal e golpe, briga, comportamento ou narrativa de transito,
  nao forcar manutencao ou diagnostico por mencoes incidentais
- citar carro, marcha, radiador ou documento nao basta para classificar como
  conteudo tecnico automotivo

### 2. `manutencao_reparo`

Usar quando o foco e preservar, corrigir ou executar servico em um veiculo.

```text
manutencao_reparo
manutencao_reparo > manutencao_preventiva
manutencao_reparo > manutencao_preventiva > revisao_10k
manutencao_reparo > manutencao_preventiva > oleo_filtros
manutencao_reparo > manutencao_preventiva > filtro_ar
manutencao_reparo > manutencao_preventiva > filtro_combustivel
manutencao_reparo > manutencao_preventiva > alinhamento_balanceamento
manutencao_reparo > manutencao_preventiva > correias_tensores
manutencao_reparo > manutencao_preventiva > controle_revisao
manutencao_reparo > manutencao_preventiva > arrefecimento
manutencao_reparo > manutencao_preventiva > bateria_12v
manutencao_reparo > manutencao_preventiva > sensores
manutencao_reparo > manutencao_preventiva > velas_ignicao
manutencao_reparo > manutencao_preventiva > limpeza_componentes
manutencao_reparo > manutencao_preventiva > pneus
manutencao_reparo > manutencao_preventiva > freios
manutencao_reparo > manutencao_preventiva > suspensao
manutencao_reparo > reparo_corretivo
manutencao_reparo > reparo_corretivo > reparo_motor
manutencao_reparo > reparo_corretivo > retifica_motor
manutencao_reparo > reparo_corretivo > troca_motor
manutencao_reparo > reparo_corretivo > reparo_cambio
manutencao_reparo > reparo_corretivo > troca_cambio
manutencao_reparo > custo_reparo
manutencao_reparo > custo_reparo > orcamento_manutencao
manutencao_reparo > custo_reparo > custo_pecas
manutencao_reparo > custo_reparo > custo_mao_obra
```

Regras:

- se o video ensina procedimento preventivo, usar `manutencao_preventiva`
- se o video e checklist amplo por periodo ou quilometragem, usar
  `manutencao_preventiva > revisao_10k` ou outra rota de revisao periodica
  existente, sem forcar um unico componente
- se o video fala de oleo e varios filtros juntos, usar `oleo_filtros`; se o
  foco for apenas um filtro, usar `filtro_ar` ou `filtro_combustivel`
- se mostra uma falha ja instalada e reparo, usar `reparo_corretivo`
- se a promessa central e "quanto custa", usar `custo_reparo` ou registrar
  `orcamento_manutencao`
- se diagnostico aparece como etapa do reparo, guardar em `activity_type` ou
  `problem`, sem mover automaticamente para `diagnostico`

### 3. `diagnostico`

Usar quando o foco principal e identificar causa, sintoma, leitura de erro ou
falha.

```text
diagnostico
diagnostico > scanner_obd2
diagnostico > luz_injecao
diagnostico > luzes_painel
diagnostico > falha_motor
diagnostico > perda_potencia
diagnostico > falha_cambio
diagnostico > falha_eletrica
diagnostico > consumo_alto
diagnostico > vibracao
diagnostico > direcao_puxando
diagnostico > problema_cronico
diagnostico > diagnostico_sensor
diagnostico > ruido
diagnostico > ruido > ruido_suspensao
```

Regras:

- `scanner_obd2` e metodo de diagnostico
- `luz_injecao` e sinal/problema
- `luzes_painel` e rota generica quando ha alerta no painel, mas a luz
  especifica ainda nao foi identificada
- `vibracao`, `perda_potencia` e `direcao_puxando` sao sintomas; preencher
  sistema e componente apenas quando houver evidencia tecnica compativel
- `ruido` e o codigo canonico para sintoma sonoro; `barulho` fica como
  sinonimo e sinal textual
- nao usar `motor` ou `cambio` isolado
- para caso de scanner envolvendo cambio, usar:
  - `automotive_domain = diagnostico`
  - `topic_path = diagnostico > scanner_obd2`
  - `automotive_system = transmissao`
  - `component = cambio_automatico`, se aplicavel
  - `problem = tranco_cambio`, se houver evidencia

### 4. `review_teste`

Usar quando o foco e avaliar, testar ou comparar experiencia/produto.

```text
review_teste
review_teste > review_veiculo
review_teste > test_drive
review_teste > comparativo
review_teste > teste_autonomia
review_teste > teste_consumo
review_teste > teste_desempenho
review_teste > teste_durabilidade
review_teste > avaliacao_tecnica
```

Regras:

- se o video testa autonomia de eletrico, usar
  `review_teste > teste_autonomia` como `topic_path`
- powertrain eletrico fica em `automotive_system = powertrain` e componente
  `bateria_tracao`, quando houver evidencia
- se o video e review com comparacao retorica no titulo, nao usar
  `comparativo` a menos que compare alternativas de fato

### 5. `mercado_produto`

Usar quando o foco e lancamento, posicionamento, preco, compra, vendas,
movimento de marcas ou leitura de mercado.

```text
mercado_produto
mercado_produto > lancamentos
mercado_produto > estreia_marca
mercado_produto > preco_posicionamento
mercado_produto > mercado_eletrificados
mercado_produto > mercado_chineses
mercado_produto > mercado_usados
mercado_produto > compra_venda
mercado_produto > compra_venda > carro_popular
mercado_produto > compra_venda > carro_premium
mercado_produto > compra_venda > suv
mercado_produto > compra_venda > picape
```

Regras:

- se a promessa e chegada de modelo/marca, usar `lancamentos` ou
  `estreia_marca`
- se a promessa e "vale a pena comprar", usar `compra_venda`
- eletrico, hibrido, flex e diesel devem ficar em `powertrain` como contexto,
  nao dentro de `eletrica_eletronica`
- preco pode ser `preco_posicionamento` quando e parte central do argumento

### 6. `powertrain`

Usar quando o foco principal e tipo de propulsao, motorizacao, bateria de
tracao, autonomia, combustivel ou transmissao.

```text
powertrain
powertrain > eletrico
powertrain > eletrico > bateria_tracao
powertrain > eletrico > autonomia
powertrain > eletrico > recarga
powertrain > eletrico > regeneracao
powertrain > eletrico > garantia_bateria
powertrain > hibrido
powertrain > hibrido > sistema_hibrido
powertrain > hibrido > hibrido_flex
powertrain > hibrido > plug_in
powertrain > combustao
powertrain > combustao > aspirado
powertrain > combustao > turbo
powertrain > combustao > flex
powertrain > combustao > diesel
powertrain > transmissao
powertrain > transmissao > cambio_manual
powertrain > transmissao > cambio_automatico
powertrain > transmissao > dupla_embreagem
powertrain > transmissao > cvt
```

Regras:

- `eletrico`, `hibrido`, `flex` e `diesel` sao powertrain
- nao colocar eletrico/hibrido em `eletrica_eletronica`
- se powertrain e apenas detalhe de um lancamento, manter
  `automotive_domain = mercado_produto` e registrar powertrain em
  `automotive_system` ou `topic_path_secondary` futuro
- bateria de tracao nao e bateria 12v

### 7. `pos_venda_reparacao`

Usar quando o foco e estrutura de reparacao, pecas, oficinas, rede de
assistencia ou nacionalizacao com impacto no pos-venda.

```text
pos_venda_reparacao
pos_venda_reparacao > pecas_reposicao
pos_venda_reparacao > gargalo_oficinas
pos_venda_reparacao > nacionalizacao
pos_venda_reparacao > skd_ckd
pos_venda_reparacao > disponibilidade_pecas
pos_venda_reparacao > rede_assistencia
```

Regras:

- usar quando o video discute risco de falta de pecas ou gargalo em oficinas
- se o video fala de carros chineses importados e oficinas, nao reduzir tudo a
  `mercado_produto > lancamentos`
- se houver discussao de SKD/CKD, registrar como topico ou lacuna conforme a
  versao canonica disponivel

### 8. `off_road`

Usar quando o foco e uso fora de estrada, preparacao ou componentes voltados a
trilha.

```text
off_road
off_road > preparacao_off_road
off_road > trilha
off_road > pneus_off_road
off_road > suspensao_off_road
off_road > 4x4
```

## Guia passo a passo de classificacao

### Passo 1 - Confirmar se o video e automotivo

Pergunta:

```text
O tema principal do video e sobre veiculo, mercado automotivo, manutencao,
diagnostico, produto, tecnologia ou uso automotivo?
```

Se a resposta for nao:

```text
automotive_domain = fora_escopo
topic_path = fora_escopo > nao_automotivo
needs_human_review = false, se a evidencia for clara
```

Se o video menciona carro incidentalmente, mas o tema e golpe, briga, transito
ou comportamento, usar:

```text
topic_path = fora_escopo > transito_comportamento
```

Se o conteudo parece automotivo, mas o input disponivel nao sustenta nenhum
`topic_path` especifico da Taxonomia V2, usar a saida operacional:

```text
automotive_domain = sem_match_taxonomico
topic_path = sem_match_taxonomico
confidence_score < 0.50
needs_human_review = true
technical_contexts = []
```

`sem_match_taxonomico` nao e nicho nem tema. Ele existe para impedir que o
classificador force `diagnostico`, `manutencao_reparo`, `powertrain`,
`review_teste` ou `mercado_produto` quando a evidencia textual nao sustenta o
match.

Exemplo:

```text
MUITO CUIDADO AO DIRIGIR!
```

Esse titulo nao autoriza inferir `diagnostico`, `luz_injecao`, scanner, motor,
cambio ou componente tecnico. Com titulo/metadados apenas, deve ficar em
`fora_escopo > transito_comportamento` se o foco for comportamento/transito, ou
`sem_match_taxonomico` se o classificador apenas souber que parece automotivo
mas nao conseguir sustentar uma rota canonica.

### Passo 2 - Identificar o tema principal

Pergunta:

```text
Se eu tivesse que explicar o video em uma frase, ele fala principalmente de que?
```

Escolher um `automotive_domain` principal. Nao escolher pelo primeiro termo
tecnico citado. Escolher pela promessa do conteudo.

### Passo 3 - Identificar a atividade dominante

Pergunta:

```text
O video esta ensinando, diagnosticando, reparando, avaliando, comparando,
lancando, opinando ou alertando?
```

Preencher `activity_type`. Esse campo evita forcar multi-niche.

### Passo 4 - Escolher o `topic_path`

Escolher o caminho mais especifico sustentado por evidencia.

Exemplo:

```text
Fala de limpeza do sistema de arrefecimento com fluido e limpa radiador
topic_path = manutencao_reparo > manutencao_preventiva > arrefecimento
```

Se faltar codigo especifico:

```text
topic_path = manutencao_reparo > manutencao_preventiva > arrefecimento
taxonomy_gaps = radiador; fluido_arrefecimento
```

### Passo 5 - Preencher formato e intencao

`content_type` descreve o formato. `audience_intent` descreve o motivo de
consumo.

Exemplo:

```text
content_type = tutorial
audience_intent = aprender_manutencao
```

### Passo 6 - Preencher entidades explicitamente citadas

Preencher marca, modelo e ano apenas com evidencia.

Exemplo:

```text
vehicle_brand = Renault
vehicle_model = Kwid
year_reference_type = exact_year
vehicle_year = 2021
```

Nao inferir modelo pelo canal. Nao criar marca/modelo novo automaticamente.

### Passo 7 - Preencher contexto tecnico com compatibilidade

Preencher `technical_context[]` quando houver evidencia tecnica.

Nesta V2 enriquecida, `automotive_system`, `component` e `problem` continuam
existindo como resumo legado/compatibilidade. A leitura detalhada deve ser
repetivel:

```text
technical_context[] = [
  {
    automotive_system,
    component,
    problem,
    context_role,
    evidence_text,
    compatibility_status
  }
]
```

Regras minimas:

- cada item deve ter um unico `automotive_system`, um unico `component` e um
  unico `problem`
- nao usar `;` para juntar multiplos componentes em uma mesma celula
- `component` deve pertencer ao `automotive_system`
- `problem` deve ser plausivel para o `automotive_system`
- se houver varios componentes, criar varias linhas/objetos em
  `technical_context[]`
- se a combinacao ainda nao existir na matriz tecnica, marcar
  `compatibility_status = needs_review` e preencher `validation_issues`
- em `fora_escopo`, contexto tecnico so pode ser `incidental` ou vazio

### Passo 8 - Registrar lacunas sem virar canonico

Se aparecer termo relevante ainda fora da V2, registrar:

```text
taxonomy_gaps = termo_1; termo_2
needs_human_review = true
```

Nao transformar termo livre em codigo canonico sem revisao.

### Passo 9 - Marcar conflitos

Usar `validation_issues` quando houver combinacao estranha ou conflitante.

Exemplos:

```text
subtema de injecao com componente pastilha_freio
modelo citado nao pertence a marca
video parece fora_escopo, mas possui termos tecnicos incidentais
```

## Exemplos aplicados ao piloto

| `post_id` | Classificacao V2 recomendada |
| --- | --- |
| `pINW53ErjQI` | `automotive_domain = fora_escopo`; `activity_type = alerta`; `topic_path = fora_escopo > transito_comportamento`; observacao: mencoes a carro sao incidentais |
| `_j1gOOnjgcU` | `automotive_domain = manutencao_reparo`; `activity_type = manutencao_preventiva`; `topic_path = manutencao_reparo > manutencao_preventiva > limpeza_componentes`; componentes: `bateria_12v`, `sensor_oxigenio`, `sensor_maf`, `vela`; lacuna: multi-componentes |
| `z55GnDEg7_U` | `automotive_domain = manutencao_reparo`; `activity_type = reparo_corretivo`; `topic_path = manutencao_reparo > reparo_corretivo > troca_motor`; entidades: Renault Kwid 2021; sistema: `motor`; problema: `falha_de_motor`; lacunas: `orcamento_reparo`, `retifica_motor` |
| `CjFrJg6VCjc` | `automotive_domain = review_teste`; `activity_type = teste`; `topic_path = review_teste > teste_autonomia`; entidades: BYD Dolphin Mini 2026; sistema: `powertrain`; componente: `bateria_tracao` |
| `nP0q6x1Uqs0` | `automotive_domain = mercado_produto`; `activity_type = analise_mercado`; `topic_path = mercado_produto > mercado_eletrificados`; entidades: BYD Dolphin; sistema: `powertrain`; lacunas: `efeito_dolphin`, `garantia_bateria` |
| `JGzj254Kgs4` | `automotive_domain = review_teste`; `activity_type = review`; `topic_path = review_teste > review_veiculo`; entidades: Changan Lumin; sistema: `powertrain`; lacunas: `carro_urbano_eletrico`, `preco_baixo` |
| `6qSnrkGd70I` | `automotive_domain = manutencao_reparo`; `activity_type = manutencao_preventiva`; `topic_path = manutencao_reparo > manutencao_preventiva > arrefecimento`; sistema: `arrefecimento`; lacunas: `radiador`, `fluido_arrefecimento`, `limpa_radiador` |
| `aXbFPJMVGKw` | `automotive_domain = review_teste`; `activity_type = review`; `topic_path = review_teste > review_veiculo`; entidades: Changan Uni-T 2026; sistema: `powertrain`; lacunas: `motor_15_turbo_flex`, `dupla_embreagem`, `autopilotagem` |
| `RTZHxSE2t5M` | `automotive_domain = pos_venda_reparacao`; `activity_type = analise_mercado`; `topic_path = pos_venda_reparacao > gargalo_oficinas`; lacunas: `carros_chineses`, `eletrificados`, `hibridos`, `skd_ckd`, `pecas_reposicao` |
| `UtWYJfldWHA` | `automotive_domain = mercado_produto`; `activity_type = lancamento`; `topic_path = mercado_produto > lancamentos`; `content_type = review`; entidades: Caoa Changan Uni-T; sistema: `powertrain`; lacunas: `motor_flex`, `tropicalizacao` |

## Regras de coerencia

### Tema e formato

- `review_teste` pode ter `content_type = review`
- `mercado_produto` pode ter `content_type = review` se for um review de
  lancamento
- `content_type = comparativo` exige comparacao real, nao apenas titulo com
  provocacao contra concorrentes

### Powertrain

- `eletrico`, `hibrido`, `flex` e `diesel` pertencem a `powertrain`
- `bateria_tracao` pertence a `powertrain`
- `bateria_12v` pertence a `eletrica_eletronica`
- `cambio` deve ser `transmissao` como sistema ou `powertrain > transmissao`
  como topic path

### Manutencao e diagnostico

- manutencao preventiva ensina cuidado antes da falha grave
- reparo corretivo trata falha ja instalada
- diagnostico identifica causa, codigo, sintoma ou leitura tecnica
- um video pode ter `automotive_domain = manutencao_reparo` e
  `activity_type = diagnostico` se o diagnostico for etapa do reparo

### Sistema, componente e problema

Compatibilidades iniciais:

```text
automotive_system = motor
component = motor_conjunto | turbina | vela | oleo_motor | filtro_oleo | filtro_motor | filtro_ar | correia_dentada | tensor_correia
problem = falha_de_motor | perda_potencia | problema_cronico | desgaste | oleo_vencido | consumo_alto

automotive_system = combustivel_injecao
component = filtro_combustivel | bomba_combustivel | injetor
problem = entupimento | consumo_alto | perda_potencia

automotive_system = transmissao
component = cambio_automatico | cambio_dupla_embreagem | cambio_manual | cambio_cvt | oleo_cambio | filtro_cambio | carter_cambio
problem = tranco_cambio | oleo_degradado | limaria

automotive_system = arrefecimento
component = radiador | fluido_arrefecimento | bomba_agua | ventoinha | aditivo_arrefecimento | agua_desmineralizada | limpa_radiador | filtro_arrefecimento
problem = superaquecimento | sistema_sujo | nivel_baixo | fluido_vencido

automotive_system = eletrica_eletronica
component = bateria_12v | alternador | sensor_oxigenio | sensor_maf | modulo_injecao | polo_bateria | carga_bateria
problem = falha_eletrica | luz_injecao | bateria_fraca | falha_partida | mau_contato

automotive_system = powertrain
component = bateria_tracao | motor_eletrico | sistema_hibrido | sistema_hibrido_plug_in
problem = autonomia_baixa | degradacao_bateria

automotive_system = rodagem_direcao
component = alinhamento | balanceamento | volante | pneu
problem = vibracao | direcao_puxando | desgaste_irregular | consumo_alto

automotive_system = suspensao
component = pivo_suspensao | bieleta | bandeja_suspensao | terminal_axial | bucha_balanca | bucha_suspensao | mola | amortecedor
problem = ruido | batida_seca | trepidacao | suspensao_dura | carro_desconfortavel | folga | desgaste

automotive_system = freios
component = pastilha_freio | disco_freio | fluido_freio
problem = desgaste | disco_empenado | fluido_contaminado | frenagem_comprometida

automotive_system = pneus
component = pneu
problem = aderencia | durabilidade | conforto | resistencia | custo_beneficio
```

Essas compatibilidades foram iniciadas no CSV `43` e ainda devem ser validadas
antes de persistencia automatica.

## Lacunas conhecidas

Termos identificados no piloto que devem ser avaliados para virar codigo:

```text
fora_escopo_automotivo
sensor_maf
sonda_lambda
radiador
fluido_arrefecimento
limpa_radiador
bateria_tracao
garantia_bateria
regeneracao
autonomia
consumo_energia
orcamento_reparo
retifica_motor
troca_motor
motor_conjunto
cambio_dupla_embreagem
autopilotagem
carro_urbano_eletrico
mercado_eletrificados
mercado_chineses
pecas_reposicao
gargalo_oficinas
nacionalizacao
skd_ckd
tropicalizacao
```

## Criterios de aceite da V2

A V2 so deve virar CSV canonico depois que:

- os `10` videos do piloto forem classificados sem termo livre essencial
- `topic_path` for compreensivel para preenchimento humano
- `automotive_domain` e `activity_type` reduzirem a necessidade de multi-niche
- marca, modelo e ano forem separados de codigos taxonomicos
- houver matriz inicial de compatibilidade tecnica
- resultados incoerentes forem enviados para revisao humana
- a v1 permanecer preservada como evidencia historica do primeiro teste

## Artefatos operacionais iniciais

A primeira resolucao operacional do gargalo da V2 foi publicada em:

- `docs/external_data/42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv`
- `docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`
- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.csv`
- `docs/external_data/50_TECHNICAL_CONTEXT_REPETIVEL_TAXONOMIA_V2.md`

O CSV `42` transforma a arvore `topic_path` em estrutura canonica para
validacao metodologica. O CSV `43` inicia a matriz de compatibilidade entre
`topic_path`, `automotive_system`, `component` e `problem`.

O CSV `50` materializa `technical_context[]` em formato longo, com uma linha
por contexto tecnico coerente. Ele resolve os casos de videos com multiplos
sistemas e componentes sem reabrir termos soltos ou listas separadas por `;`.

Esses CSVs tambem nao substituem retroativamente os CSVs v1 `31` e `32`.

`topic_path_secondary` fica documentado como campo opcional para casos em que
ha segundo tema forte e explicito, como `review_teste > review_veiculo` com
`mercado_produto > compra_venda > carro_popular`. Ele nao substitui
`topic_path` principal e nao reabre multi-nicho livre.

## Contrato Supabase e harness GPT

Em 2026-07-23, a V2 ganhou contrato operacional para uso por GPT:

- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_HARNESS_CONTRACT_V2.md`
- `docs/external_data/58_GPT_VIDEO_CLASSIFIER_OUTPUT_SCHEMA_V2.json`
- `sql/ddl/tables/022_create_video_taxonomy_classification.sql`
- `sql/ddl/views/023_create_v_video_classification_latest.sql`

O harness recebe um video por estagio (`title_metadata` ou `transcript_90s`) e
deve devolver JSON estruturado com:

- `classification_result`
- `technical_contexts[]`
- `vehicle_entities[]`

Regra adicional:

- o GPT atua como classificador da industria automotiva
- nao pode completar lacunas por plausibilidade externa
- todo campo preenchido deve ter evidencia textual no titulo, descricao,
  transcricao ou metadado confiavel
- a resposta so deve ser gravada depois de validar `topic_path`, matriz
  tecnica, entidades e schema JSON

Esse contrato altera a preparacao de banco para classificacao, mas nao cria
metodo de ingestao, rotina Google Cloud, worker, dashboard ou alteracao do
workbook.

## Proximo passo

Transformar estes artefatos em execucao controlada:

1. Carregar a Taxonomia V2 no Supabase pela rotina operacional definida fora
   deste documento.
2. Executar lote pequeno do classificador GPT com o contrato do doc `58`.
3. Validar se a resposta e gravavel sem ajuste manual.
4. Comparar resultados por `title_metadata` e `transcript_90s`.
