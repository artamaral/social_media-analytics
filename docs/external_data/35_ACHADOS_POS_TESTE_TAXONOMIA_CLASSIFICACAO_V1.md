# Achados Pos-Teste da Taxonomia e Classificacao v1

## Objetivo

Registrar os aprendizados observados apos o primeiro uso humano da taxonomia do
Sprint 6 e orientar a revisao v2 sem alterar retroativamente os artefatos
utilizados no teste.

Este documento registra achados e requisitos. Ele nao substitui ainda os CSVs
canonicos `31` e `32`.

## Achado 1 - A taxonomia precisa de uma arvore legivel

A lista operacional deve apresentar os termos em uma hierarquia clara, por
exemplo:

```text
1. diagnostico
1.1 scanner_obd2
1.2 luz_injecao
```

A numeracao serve para leitura e navegacao humana. Os codigos canonicos
continuam em `snake_case` e nao devem incorporar o numero.

A arvore apresentada ao usuario pode reunir rotas de classificacao sem obrigar
que todos os itens pertencam a mesma dimensao tecnica. No exemplo:

- `diagnostico` identifica o contexto principal
- `scanner_obd2` identifica um metodo ou subtema de diagnostico
- `luz_injecao` identifica um problema ou sinal associado ao diagnostico

Essa separacao evita transformar sintoma, metodo, sistema e componente no mesmo
tipo de categoria apenas para obter uma lista visual simples.

## Achado 2 - Os campos precisam de coerencia referencial

Os valores nao podem ser combinados livremente. A classificacao futura deve
validar pelo menos estas relacoes:

```text
niche -> sub_niche
sub_niche -> sub_sub_niche
rota taxonomica -> automotive_system
automotive_system -> component
automotive_system -> problem
vehicle_brand -> vehicle_model
vehicle_model -> vehicle_year_or_generation
```

Exemplo invalido:

```text
contexto = diagnostico de injecao
automotive_system = suspensao
component = pastilha_freio
```

Exemplo coerente:

```text
contexto = diagnostico de injecao
automotive_system = motor | combustivel | eletrica_eletronica
component = bico_injetor | modulo_injecao | sensor_oxigenio
problem = luz_injecao | falha_de_motor | perda_potencia
```

As listas acima sao exemplos de coerencia e ainda precisam ser fechadas na
taxonomia v2.

## Achado 3 - As travas devem existir em mais de uma camada

O contrato futuro deve aplicar validacao progressiva:

1. Interface ou workbook:
   - dropdowns dependentes filtram apenas valores compativeis
   - marca filtra modelo
   - sistema filtra componente e problema
2. Servico de classificacao:
   - valida o resultado da IA contra as relacoes permitidas
   - resultado incoerente nao e corrigido silenciosamente
   - resultado incoerente recebe `needs_human_review = true`
3. Banco:
   - compara codigos com tabelas canonicas
   - usa chaves e relacoes de compatibilidade para impedir persistencia ilogica

Nem toda relacao deve ser modelada apenas com `parent_code`. Casos em que um
problema ou componente pode pertencer a mais de um contexto exigem tabelas de
compatibilidade muitos-para-muitos.

## Achado 4 - Marca e modelo devem vir do banco

`vehicle_brand`, `vehicle_model` e `vehicle_year_or_generation` devem ser
comparados futuramente com cadastros canonicos do banco.

Regras minimas:

- modelo precisa pertencer a marca selecionada
- geracao ou ano precisa ser valido para o modelo quando o dado existir
- aliases devem resolver para um codigo canonico antes da persistencia
- valor desconhecido deve seguir para revisao, nao virar novo cadastro
  automaticamente

A fonte definitiva e a estrategia de reconciliacao com Fenabrave, Carros na
Web e entidades existentes ainda precisam ser decididas.

## Achado 5 - `diagnostico` e `manutencao` se sobrepoem

O teste mostrou que os niches atuais misturam naturezas diferentes. Por
exemplo, diagnostico pode ser uma atividade dentro do dominio amplo de
manutencao e reparo.

Antes de permitir varios niches, a v2 deve avaliar a separacao em eixos:

```text
automotive_domain = manutencao_reparo
activity_type = diagnostico | manutencao_preventiva | reparo_corretivo
```

Essa e a alternativa recomendada porque reduz sobreposicao sem perder
informacao.

Se o teste mostrar que os eixos separados ainda nao resolvem os casos hibridos,
adotar:

- `niche_primary`: obrigatorio e unico
- `niche_secondary`: opcional e controlado
- tabela de combinacoes permitidas entre niche primario e secundario

Nao permitir array aberto de niches nem termos livres sem validacao.

## Decisoes para a taxonomia v2

Pontos que precisam ser fechados antes de alterar CSV, workbook ou banco:

1. Definir a arvore de apresentacao completa de niche, sub_niche e rotas
   associadas.
2. Separar dimensoes tecnicas de caminhos de navegacao apresentados ao humano.
3. Definir matrizes de compatibilidade entre tema, sistema, componente e
   problema.
4. Definir relacionamento canonico entre marca, modelo e geracao.
5. Escolher entre eixos `automotive_domain` + `activity_type` ou
   `niche_primary` + `niche_secondary`.
6. Revisar os `10` resultados do piloto contra a proposta antes de publicar a
   taxonomia v2.

## Criterios de aceite da proxima versao

- a arvore de classificacao e compreensivel sem conhecer o modelo de dados
- cada codigo canonico mantem um unico significado
- nenhuma combinacao ilogica de sistema e componente e aceita
- nenhum modelo e aceito para marca incompativel
- resultados invalidos da IA sao rejeitados ou enviados para revisao
- a decisao de multi-nicho fica explicita e testada com a amostra piloto
- a taxonomia v1 permanece preservada como evidencia da primeira rodada
