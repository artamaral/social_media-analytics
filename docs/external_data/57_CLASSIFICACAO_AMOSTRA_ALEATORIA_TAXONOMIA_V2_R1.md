# Classificacao amostra aleatoria Taxonomia V2 - R1

## Objetivo

Rodar uma amostra aleatoria de `10` videos ainda nao usados, seguindo as
restricoes documentadas da amostra metodologica:

- excluir `Acelerados`, `ACF` e `Tcar`;
- exigir `followers >= 150000`;
- exigir `engagement_pct >= 2.0`;
- manter apenas `video_type` preenchido como `long` ou `short`;
- excluir todos os `post_id` ja usados nas rodadas anteriores.

Semente usada para a aleatoriedade:

- `20260723`

## Artefatos

- `55_AMOSTRA_ALEATORIA_TAXONOMIA_V2_10_VIDEOS_R1.csv`
- `56_TRANSCRICOES_90S_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv`
- `57_CLASSIFICACAO_AMOSTRA_ALEATORIA_TAXONOMIA_V2_R1.csv`

## Validacao da rodada

| Check | Resultado |
| --- | ---: |
| Videos elegiveis no universo filtrado | 3091 |
| Videos usados anteriormente excluidos | 29 |
| Videos sorteados | 10 |
| `post_id` duplicado na amostra | 0 |
| Intersecao com rodadas anteriores | 0 |
| Transcricoes com sucesso | 10 |
| Classificacoes por titulo/metadados | 10 |
| Classificacoes por 90s | 10 |

## Resultado comparativo

| post_id | Titulo/metadados | Conf. titulo | 90s | Conf. 90s | Leitura |
| --- | --- | ---: | --- | ---: | --- |
| `KwZFtY1w8FY` | `review_teste > review_veiculo`, GR Yaris manual | 0.90 | Mantem review e adiciona motor 1.6 turbo, cambio manual/automatico e tracao integral | 0.96 | Bom caso para contexto tecnico de review |
| `0YeiiIpSrP0` | Review de Jeep Commander hibrido/MHEV | 0.92 | Confirma Commander 2027 Overland MHEV, consumo, desempenho e explicacao do sistema | 0.97 | Abre lacuna de `mhev`/`hibrido_leve` |
| `KONPXAjlkn8` | Comparativo/opiniao T-Cross vs chineses | 0.84 | 90s mostra mais mercado/percepcao de SUVs que teste tecnico | 0.89 | Mudou dominio principal para `mercado_produto` |
| `cwQIxaJDJAE` | Motos classicas | 0.78 | Confirma cultura sobre duas rodas | 0.86 | Fora do escopo atual de carros; lacuna de motos |
| `cLH17x4LiCA` | Review Toyota Yaris Cross XR 2026 | 0.95 | Confirma versao de entrada, showroom, preco e pontos positivos/negativos | 0.97 | Taxonomia cobre bem |
| `fvt-UH964yA` | Comparativo Tiggo 7 2027 | 0.91 | Confirma comparativo de versoes e cita PHEV ausente | 0.95 | Taxonomia cobre, mas falta atributo de versao/garantia |
| `Yel1puu2qGQ` | Picape Volkswagen camuflada | 0.84 | Confirma prototipo de picape, plataforma MQB e hibrido leve especulado | 0.88 | Bom caso de lancamento/flagra/prototipo |
| `UMEYwVvLsGM` | Lotus eletrico extremo | 0.85 | Confirma Lotus Evija eletrico, carbono, aerodinamica e freios especiais | 0.94 | Cobre powertrain, mas abre atributos de hipercarro |
| `Sth4l0Kc2NY` | Titulo ambiguo | 0.62 | 90s revela pista de testes da Changan simulando Brasil para suspensao | 0.89 | 90s muda muito a classificacao |
| `yAytAka2dfg` | Oficina/alinhamento 3D | 0.82 | Confirma curso profissional de geometria/alinhamento | 0.90 | Falta separar audiencia profissional/oficina |

## Principais aprendizados

- A taxonomia atual classificou todos os videos sem criar novo `topic_path`
  canonico na hora.
- A transcricao foi decisiva nos casos de titulo ambiguo:
  - `Sth4l0Kc2NY`;
  - `KONPXAjlkn8`;
  - `Yel1puu2qGQ`.
- Os casos de review continuaram bem cobertos por `review_teste >
  review_veiculo` e por `topic_path_secondary`.
- A aleatoriedade trouxe dois tipos de lacuna que nao tinham aparecido com
  tanta forca:
  - conteudo de moto/duas rodas;
  - conteudo B2B/profissional para oficina.
- `mhev`/`hibrido_leve`, `prototipo/flagra`, `pista_teste` e
  `calibracao_suspensao` devem ficar inicialmente como `taxonomy_gaps` ou
  atributos, nao como novos subnichos imediatos.

## Decisao apos revisao humana

A rodada confirmou que a base atual esta boa e que a melhor decisao agora e
evitar novas aberturas estruturais.

Regras consolidadas:

- nao expandir `topic_path` nesta rodada;
- nao criar `audience_context` agora;
- nao criar `estagio_produto`;
- nao criar `engineering_context`;
- motos e duas rodas permanecem fora de escopo;
- prototipo, flagra e camuflado ficam como evidencia textual ou
  `taxonomy_gaps`, sem categoria propria;
- pista de teste, calibracao e tropicalizacao ficam em
  `review_teste > avaliacao_tecnica`, quando houver evidencia clara;
- ano/modelo segue a regra ja estabelecida nas bases externas: se a informacao
  estiver disponivel e confiavel, usar; se nao estiver, deixar vazio;
- atributos tecnicos de review devem reaproveitar termos existentes ou ja
  aprovados na matriz tecnica, sem criar uma lista ampla nova.

Termos aprovados nesta rodada para contexto tecnico de review:

- `cambio_automatico`;
- `cambio_cvt`;
- `tracao_traseira`;
- `tracao_dianteira`;
- `tracao_integral`.

Os demais termos sugeridos na analise ficam apenas como evidencia textual,
observacao ou `taxonomy_gaps` ate nova recorrencia justificar promocao.
