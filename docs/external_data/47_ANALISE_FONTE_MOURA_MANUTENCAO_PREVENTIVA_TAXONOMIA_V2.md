# Analise fonte Moura para enriquecimento da Taxonomia V2

Data: 2026-07-23

Fonte avaliada:

- https://www.moura.com.br/blog/checklist-de-manutencao-preventiva-carro

## Objetivo

Avaliar uma fonte editorial automotiva externa sobre manutencao preventiva e
usar os termos observados para enriquecer a Taxonomia V2 de videos
automotivos.

Esta entrega atualiza os CSVs operacionais da V2 e o guia de classificacao,
sem alterar banco, workbook ou pipeline.

## Leitura da fonte

A pagina da Moura e um artigo educativo sobre checklist de manutencao
preventiva a cada `10.000 km`.

O conteudo combina quatro tipos de sinal:

- revisao periodica ampla por quilometragem;
- itens preventivos por sistema ou componente;
- sintomas que devem disparar diagnostico entre revisoes;
- contexto de custo, garantia, oficina e controle de manutencao.

Classificacao metodologica da propria fonte:

```text
automotive_domain = manutencao_reparo
activity_type = manutencao_preventiva
topic_path = manutencao_reparo > manutencao_preventiva > revisao_10k
content_type = educativo
audience_intent = evitar_prejuizo
topic_path_secondary = manutencao_reparo > manutencao_preventiva > controle_revisao
```

## Termos brutos relevantes

Termos de manutencao preventiva:

- revisao de 10 mil km
- checklist
- oleo do motor
- filtro de oleo
- filtro de ar
- filtro de combustivel
- freios
- alinhamento
- balanceamento
- suspensao
- correias
- tensores
- arrefecimento
- bateria
- sistema eletrico basico

Termos de diagnostico ou sintomas:

- luzes do painel
- ruidos
- barulhos
- vibracoes
- perda de potencia
- consumo anormal de combustivel
- carro puxando para um lado

Termos de contexto comercial/operacional:

- custo de revisao
- concessionaria
- oficina
- rede autorizada
- garantia
- notas fiscais
- checklist impresso ou digital
- planilha
- app de controle de manutencao

## Termos promovidos

Novos `topic_path_code` criados no CSV `42`:

```text
manutencao_reparo__manutencao_preventiva__revisao_10k
manutencao_reparo__manutencao_preventiva__oleo_filtros
manutencao_reparo__manutencao_preventiva__filtro_ar
manutencao_reparo__manutencao_preventiva__filtro_combustivel
manutencao_reparo__manutencao_preventiva__alinhamento_balanceamento
manutencao_reparo__manutencao_preventiva__correias_tensores
manutencao_reparo__manutencao_preventiva__controle_revisao
diagnostico__luzes_painel
diagnostico__perda_potencia
diagnostico__vibracao
diagnostico__direcao_puxando
```

Regra aplicada:

- `revisao_10k` cobre conteudo de checklist amplo por quilometragem;
- itens especificos continuam como rotas de manutencao preventiva quando forem
  o foco principal;
- sintomas viram rotas de diagnostico apenas quando o video tiver promessa de
  identificar causa ou problema;
- em conteudo preventivo, sintomas podem ficar em `problem` ou
  `example_signals`, sem deslocar automaticamente o dominio para diagnostico.

## Matriz tecnica atualizada

O CSV `43` recebeu compatibilidades para:

- `motor`: oleo, filtros, correias e tensores;
- `combustivel_injecao`: filtro de combustivel, bomba e injetor;
- `freios`: pastilha, disco e fluido;
- `rodagem_direcao`: alinhamento, balanceamento, volante e pneu;
- `suspensao`: bucha, amortecedor, pivo, folga e desgaste;
- `arrefecimento`: fluido, aditivo, nivel baixo e fluido vencido;
- `eletrica_eletronica`: bateria 12v, polo, carga, mau contato e falha de
  partida.

## Termos nao promovidos

Termos mantidos fora da taxonomia canonica nesta rodada:

- `sistema_hidraulico`: a fonte cita o termo, mas ele e amplo demais sem
  evidencia de direcao hidraulica, freio hidraulico ou outro subsistema.
- `concessionaria`: contexto de pos-venda/custo, nao tema principal desta
  fonte.
- `oficina`: contexto operacional, ja coberto por custo/reparo ou pos-venda.
- `notas_fiscais`: sinal de controle e garantia, nao rota principal.
- `planilha` e `app`: sinais de controle de revisao, nao categorias separadas.
- `barulho`: continua como sinonimo/sinal textual; `ruido` permanece o codigo
  canonico para sintoma sonoro.

## Regras de classificacao derivadas

Quando o conteudo for checklist amplo:

```text
topic_path = manutencao_reparo > manutencao_preventiva > revisao_10k
```

Quando o conteudo focar em um item especifico do checklist:

```text
topic_path = manutencao_reparo > manutencao_preventiva > oleo_filtros
topic_path = manutencao_reparo > manutencao_preventiva > freios
topic_path = manutencao_reparo > manutencao_preventiva > suspensao
topic_path = manutencao_reparo > manutencao_preventiva > arrefecimento
topic_path = manutencao_reparo > manutencao_preventiva > bateria_12v
```

Quando o conteudo for sobre sintoma entre revisoes:

```text
topic_path = diagnostico > luzes_painel
topic_path = diagnostico > vibracao
topic_path = diagnostico > perda_potencia
topic_path = diagnostico > direcao_puxando
```

Cuidados:

- nao preencher `automotive_system`, `component` ou `problem` se o video so
  mencionar uma lista ampla sem detalhe tecnico;
- `motor` continua proibido como tema solto e entra apenas como sistema ou rota
  contextualizada;
- `filtro_ar` e `filtro_combustivel` nao devem ser misturados com freios,
  suspensao ou arrefecimento;
- `bateria_12v` continua em `eletrica_eletronica`, nao em `powertrain`;
- `barulho` continua sinal textual, nao codigo canonico.

## Impacto na Taxonomia V2

A principal melhoria e separar melhor tres familias de conteudo preventivo:

1. checklist amplo por periodo ou quilometragem;
2. manutencao preventiva especifica por item;
3. sintomas que podem surgir entre revisoes e exigir diagnostico.

Essa separacao reduz classificacoes forcadas e prepara a proxima etapa de
validacao por matriz de compatibilidade.

## Arquivos atualizados

- `docs/external_data/40_TAXONOMIA_VIDEO_V2_GUIA_CLASSIFICACAO.md`
- `docs/external_data/42_TAXONOMIA_VIDEO_V2_TOPIC_PATHS.csv`
- `docs/external_data/43_TAXONOMIA_VIDEO_V2_COMPATIBILIDADE_TECNICA.csv`
- `docs/README.md`
- `docs/project/07_SPRINT_AGENDA.md`

