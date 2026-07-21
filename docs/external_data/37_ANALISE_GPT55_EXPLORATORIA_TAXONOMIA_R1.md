# Analise GPT 5.5 Exploratoria da Taxonomia - Round 1

## Objetivo

Registrar uma rodada exploratoria com `gpt-5.5` para evoluir a taxonomia do
Sprint 6 sem criar pipeline, scripts robustos ou benchmark final contra a API
`gpt-5.4-mini`.

Esta rodada deve ser lida como insumo de desenho taxonomico. Ela nao substitui
a avaliacao futura por API, nem calcula `agreement_score`.

## Fontes usadas

- amostra canonica dos `10` videos:
  `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv`
- taxonomia v1:
  `docs/external_data/31_TAXONOMIA_PILOTO_VIDEO_V1.csv`
- dimensoes complementares v1:
  `docs/external_data/32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.csv`
- resultado desta rodada:
  `docs/external_data/37_RESULTADO_GPT55_EXPLORATORIO_TAXONOMIA_R1.csv`

O baseline humano nao foi usado como entrada da classificacao GPT 5.5.

## Escopo executado

Foram registrados `20` resultados:

- `10` linhas para `gpt55_entrega_1_descricao`
- `10` linhas para `gpt55_entrega_2_90s_iniciais`

Na pratica, somente a etapa 1 recebeu classificacao efetiva. O CSV do doc `33`
ainda nao possui `description` real, entao a evidencia disponivel foi limitada
a titulo e metadados. A etapa 2 foi preservada no arquivo, mas marcada como
`sem_evidencia_90s`, porque nao existe transcricao textual dos primeiros `90s`
versionada no repositorio e a rodada nao deveria chamar API de transcricao.

## Leitura dos resultados

### Pontos fortes da v1

- `powertrain` funcionou melhor que `eletrica_eletronica` para videos sobre
  eletricos, autonomia, flex e motorizacao.
- `manutencao > arrefecimento` resolveu bem o caso de limpeza/manutencao de
  radiador.
- `compra_venda > carro_popular` cobriu bem o video sobre carro popular quando
  a evidencia era comercial.
- `review` e `mercado` se mostraram necessarios como temas separados, mesmo
  quando o titulo tem gancho editorial agressivo.

### Lacunas recorrentes

- Falta uma categoria explicita para conteudo fora do escopo automotivo. O caso
  `pINW53ErjQI` nao deve ser forcado em `alerta` automotivo sem evidencia.
- Falta representar custo, orcamento, retifica e reparo pesado sem transformar
  `motor` em componente solto.
- Falta granularidade de eletrificados para autonomia, bateria de tracao,
  capacidade de bateria e teste de consumo de energia.
- Falta `radiador` como componente canonico ligado a `arrefecimento`.
- Falta separar melhor `lancamento`, `review`, `preco` e `powertrain` quando
  todos aparecem no mesmo video.
- Falta campo proprio para valor temporal real quando a taxonomia usa
  `exact_year`, porque `exact_year:2026` mistura codigo e valor.

### Conflitos estruturais

- Um unico `niche` continua insuficiente para videos que cruzam mercado,
  review e powertrain.
- `content_type` ajuda, mas nao resolve sozinho os casos em que o tema principal
  e o formato editorial puxam para rotas diferentes.
- `sub_niche` ainda mistura naturezas diferentes: tipo de veiculo, tipo de
  motorizacao, procedimento, avaliacao e leitura de mercado.
- A relacao entre `automotive_system`, `component` e `problem` precisa virar
  matriz de compatibilidade antes da persistencia automatica.
- Marca e modelo precisam ser tratados como entidades canonicas, nao como
  texto livre validado apenas pelo prompt.

## Recomandacao para Taxonomia v2

A proxima versao deve separar decisao editorial, estrutura tecnica e entidades:

1. `automotive_domain`
   - exemplo: `manutencao_reparo`, `mercado_produto`, `powertrain`, `fora_escopo`
2. `activity_type`
   - exemplo: `diagnostico`, `manutencao_preventiva`, `reparo_corretivo`,
     `avaliacao`, `lancamento`, `comparacao`, `alerta`
3. `topic_path`
   - arvore legivel para o humano, por exemplo
     `manutencao_reparo > arrefecimento > radiador`
4. `technical_context`
   - `automotive_system`, `component`, `problem` com compatibilidade formal
5. `vehicle_entity`
   - marca, modelo e ano/geracao como referencias canonicas ou valores
     controlados com status de validacao

Para a v2, a decisao mais promissora continua sendo evitar multi-niche livre e
testar primeiro a separacao entre dominio e tipo de atividade. Se ainda houver
ambiguidade, usar `primary_topic` e `secondary_topic` com combinacoes
permitidas.

## Proximo passo

Antes de novo round de fine tuning conceitual:

- corrigir os metadados truncados do doc `33`
- capturar `description` real dos `10` videos
- decidir se `fora_escopo` entra como dominio canonico
- desenhar a arvore v2 separando navegacao humana de campos canonicos
- adicionar os primeiros relacionamentos de compatibilidade:
  `topic_path -> automotive_system -> component -> problem`

Depois disso, rodar um segundo round com o mesmo formato simples, ainda sem
automatizar pipeline, para comparar se a taxonomia v2 reduz termos livres e
incompatibilidades.
