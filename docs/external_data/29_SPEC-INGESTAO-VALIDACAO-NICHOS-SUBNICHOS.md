# Spec — Ingestão e Validação de Nichos/Subnichos de Vídeos

## Projeto

**social_media-analytics — inteligência automotiva para conteúdo e creators**

## Objetivo

Definir o método inicial para ingestão, classificação e validação de dados de **nicho**, **subnicho** e dimensões complementares dos vídeos catalogados no projeto.

Esta spec cobre a fase metodológica anterior à implementação definitiva em banco, pipeline ou dashboard.

O foco é validar se a classificação automática por IA consegue se aproximar da classificação humana usando, inicialmente, apenas os dados já existentes dos vídeos, sem uso de transcrição.

---

## Contexto atual

O projeto já possui mais de **4.000 vídeos catalogados**.

Para muitos vídeos, já existem dados como:

- `post_id` / `video_id`
- título
- descrição
- creator / canal
- data de publicação
- duração
- classificação short/long, quando disponível
- views
- likes
- comentários
- histórico de métricas, quando disponível

Esses dados já permitem uma primeira classificação por contexto, mesmo antes de extrair transcrição do vídeo.

---

## Princípio metodológico

A classificação de nicho e subnicho deve ser tratada como uma **dimensão analítica**, não apenas como uma etiqueta descritiva.

O objetivo não é apenas dizer:

> Este vídeo é sobre freios.

O objetivo é permitir análises como:

- quais subnichos automotivos estão crescendo;
- quais creators dominam cada subnicho;
- quais formatos performam melhor em cada tema;
- quais marcas e modelos aparecem com maior frequência;
- quais temas têm alta demanda e baixa oferta;
- quais conteúdos justificam análise mais profunda com transcrição.

---

## Escopo desta spec

Esta spec cobre:

1. Seleção inicial de vídeos para validação.
2. Classificação humana dos vídeos.
3. Classificação por IA usando dados já existentes.
4. Comparação humano vs IA.
5. Cálculo de `agreement_score`.
6. Cálculo de `confidence_score`.
7. Critérios para aceitar classificação sem transcrição.
8. Critérios para enviar vídeo para transcrição.
9. Critérios para revisão humana.
10. Iteração do método antes de escalar para os mais de 4.000 vídeos.

Esta spec **não cobre ainda**:

- desenho final das tabelas SQL;
- implementação do pipeline;
- escolha de modelo LLM;
- custos de API;
- dashboard;
- automação em produção.

Esses temas devem ser tratados em uma etapa posterior.

---

## Estratégia inicial

A validação deve começar com uma amostra pequena de **10 vídeos**.

A escolha por 10 vídeos tem como objetivo:

- reduzir custo e complexidade;
- facilitar revisão humana;
- identificar erros conceituais cedo;
- ajustar taxonomia e prompt antes de escalar;
- testar se os dados existentes são suficientes para classificação inicial.

A amostra de 10 vídeos não tem objetivo estatístico. Ela serve para validar o método.

---

## Seleção dos 10 vídeos iniciais

A amostra inicial deve ser variada.

Sugestão de composição:

| Grupo | Quantidade | Critério |
|---|---:|---|
| Vídeos recentes | 2 | Publicados recentemente |
| Vídeos com alta performance absoluta | 2 | Maiores views no período |
| Vídeos com alta performance relativa | 2 | Acima da média do próprio creator |
| Vídeos de título claro | 2 | Ex.: “Como trocar pastilha de freio” |
| Vídeos de título ambíguo | 2 | Ex.: “Esse problema custa caro” |

Essa composição ajuda a testar a IA em casos fáceis e difíceis.

---

## Fontes usadas na primeira fase

Na primeira fase, a IA deve usar somente dados já existentes.

### Fontes permitidas

- título do vídeo;
- descrição do vídeo;
- nome do canal;
- creator;
- data de publicação;
- duração;
- short/long, se disponível;
- views;
- likes;
- comentários;
- histórico básico do canal, se disponível;
- nicho conhecido do creator, se disponível.

### Fontes não usadas na primeira fase

- transcrição;
- áudio;
- comentários completos;
- análise visual do vídeo;
- thumbnail, salvo se já estiver disponível como texto/metadado;
- dados externos não catalogados.

---

## Dimensões de classificação

Cada vídeo deve ser classificado nas seguintes dimensões.

### Dimensões principais

- `niche`
- `sub_niche`
- `sub_sub_niche`
- `content_type`
- `audience_intent`

### Dimensões automotivas complementares

- `vehicle_brand`
- `vehicle_model`
- `vehicle_year_or_generation`
- `automotive_system`
- `component`
- `problem`

### Dimensões de controle

- `confidence_score`
- `evidence_summary`
- `needs_transcript`
- `needs_human_review`
- `review_notes`

---

## Definição das dimensões

### `niche`

Categoria macro do conteúdo.

Exemplos iniciais:

- `manutencao`
- `diagnostico`
- `performance`
- `review`
- `mercado`
- `eletrica_eletronica`
- `off_road`
- `acessorios`
- `funilaria_pintura`
- `compra_venda`

### `sub_niche`

Categoria intermediária e principal dimensão analítica.

Exemplos iniciais:

- `troca_oleo`
- `freios`
- `suspensao`
- `pneus`
- `bateria`
- `scanner`
- `injecao_eletronica`
- `motor`
- `cambio`
- `arrefecimento`
- `turbo`
- `remap`
- `preparacao_off_road`
- `test_drive`
- `comparativo`
- `carros_eletricos`
- `carros_hibridos`
- `suv`
- `picape`
- `carro_popular`
- `carro_premium`
- `mercado_usados`
- `lancamentos`
- `pecas_aftermarket`

### `sub_sub_niche`

Classificação mais granular, usada apenas quando houver evidência suficiente.

Exemplos:

- `troca_pastilha`
- `falha_de_motor`
- `problema_cronico`
- `scanner_obd2`
- `limpeza_bico_injetor`
- `cambio_automatico`
- `remap_stage_2`
- `lift_kit`
- `bateria_12v`
- `sistema_hibrido`

### `content_type`

Tipo de conteúdo apresentado.

Exemplos:

- `educativo`
- `tutorial`
- `review`
- `comparativo`
- `noticia`
- `opinião`
- `entretenimento`
- `alerta`
- `ranking`
- `case`

### `audience_intent`

Intenção provável da audiência ao consumir o conteúdo.

Exemplos:

- `resolver_problema`
- `evitar_prejuizo`
- `aprender_manutencao`
- `decidir_compra`
- `comparar_opcoes`
- `acompanhar_lancamento`
- `melhorar_performance`
- `entender_mercado`
- `entretenimento`

### `vehicle_brand`

Marca do veículo citado, quando disponível.

Exemplos:

- `Fiat`
- `Volkswagen`
- `Toyota`
- `Jeep`
- `Chevrolet`
- `Honda`
- `BYD`
- `GWM`

Quando não houver evidência clara, usar `null`.

### `vehicle_model`

Modelo do veículo citado, quando disponível.

Exemplos:

- `Toro`
- `Compass`
- `Corolla Cross`
- `Hilux`
- `Onix`
- `Nivus`
- `Dolphin`

Quando não houver evidência clara, usar `null`.

### `vehicle_year_or_generation`

Ano, geração ou versão do veículo, quando disponível.

Exemplos:

- `2022`
- `2024`
- `geracao atual`
- `modelo antigo`
- `hibrido`
- `flex`
- `diesel`

Quando não houver evidência clara, usar `null`.

### `automotive_system`

Sistema automotivo principal tratado no vídeo.

Exemplos:

- `motor`
- `transmissao`
- `freios`
- `suspensao`
- `eletrica`
- `eletronica`
- `arrefecimento`
- `combustivel`
- `direcao`
- `rodas_pneus`
- `carroceria`

### `component`

Peça ou componente específico citado, quando houver.

Exemplos:

- `pastilha_freio`
- `disco_freio`
- `bateria`
- `alternador`
- `bobina`
- `vela`
- `bico_injetor`
- `sensor_oxigenio`
- `cambio_automatico`
- `turbina`

### `problem`

Problema principal tratado, quando aplicável.

Exemplos:

- `falha_de_motor`
- `luz_injecao`
- `barulho_suspensao`
- `superaquecimento`
- `consumo_alto`
- `perda_potencia`
- `problema_cronico`
- `falha_eletrica`
- `desgaste_prematuro`

---

## Classificação humana

Antes da IA, o humano deve classificar manualmente os 10 vídeos.

Essa classificação funciona como referência inicial para comparação.

### Campos da classificação humana

- `human_niche`
- `human_sub_niche`
- `human_sub_sub_niche`
- `human_content_type`
- `human_audience_intent`
- `human_vehicle_brand`
- `human_vehicle_model`
- `human_vehicle_year_or_generation`
- `human_automotive_system`
- `human_component`
- `human_problem`
- `human_confidence`
- `human_note`

### Regra importante

A classificação humana não deve ser tratada como verdade absoluta. Ela é uma referência de calibração.

Se houver divergência entre humano e IA, a análise deve verificar se:

- a IA errou;
- o humano classificou com pouca evidência;
- a taxonomia é insuficiente;
- o vídeo é ambíguo;
- a descrição disponível é fraca;
- o subnicho correto ainda não existe.

---

## Classificação por IA

A IA deve classificar os mesmos 10 vídeos usando somente dados existentes.

### Regras para a IA

A IA deve:

- usar somente a taxonomia permitida;
- não inventar categorias novas;
- separar tema de marca/modelo;
- usar `null` quando não houver evidência;
- justificar brevemente a classificação;
- calcular componentes do `confidence_score`;
- indicar se precisa de transcrição;
- indicar se precisa de revisão humana.

### Saída esperada da IA

```json
{
  "post_id": "abc123",
  "niche": "diagnostico",
  "sub_niche": "cambio",
  "sub_sub_niche": "problema_cronico",
  "content_type": "educativo",
  "audience_intent": "evitar_prejuizo",
  "vehicle_brand": "Jeep",
  "vehicle_model": "Compass",
  "vehicle_year_or_generation": null,
  "automotive_system": "transmissao",
  "component": "cambio_automatico",
  "problem": "problema_cronico",
  "metadata_clarity_score": 0.85,
  "taxonomy_fit_score": 0.80,
  "evidence_score": 0.75,
  "creator_context_score": 0.70,
  "model_self_confidence": 0.80,
  "confidence_score": 0.78,
  "needs_transcript": true,
  "needs_human_review": false,
  "evidence_summary": "Título e descrição indicam problema crônico no câmbio de um Jeep Compass.",
  "review_notes": "Subnicho provável, mas transcrição pode confirmar o componente exato."
}
```

---

## `confidence_score`

O `confidence_score` representa a confiança matemática da classificação feita pela IA.

Ele não deve ser apenas uma percepção subjetiva do modelo.

### Fórmula inicial

```text
confidence_score =
  0.35 * metadata_clarity_score +
  0.25 * taxonomy_fit_score +
  0.20 * evidence_score +
  0.10 * creator_context_score +
  0.10 * model_self_confidence
```

### Componentes

#### `metadata_clarity_score`

Mede se título e descrição deixam claro o assunto do vídeo.

Exemplos de alta clareza:

- “Como trocar pastilha de freio do Onix”
- “Scanner mostra falha no sensor de oxigênio”

Exemplos de baixa clareza:

- “Olha o que aconteceu com esse carro”
- “Esse defeito custa caro”

#### `taxonomy_fit_score`

Mede se o vídeo encaixa claramente em uma categoria da taxonomia.

Alta confiança ocorre quando existe uma categoria evidente.

Baixa confiança ocorre quando o vídeo parece misturar vários temas ou quando a taxonomia não cobre bem o caso.

#### `evidence_score`

Mede a quantidade e consistência das evidências disponíveis.

Exemplo de evidências alinhadas:

- título fala “scanner”;
- descrição fala “diagnóstico”;
- canal é de oficina;
- tags mencionam “injeção eletrônica”.

Quanto mais fontes apontam para o mesmo tema, maior o score.

#### `creator_context_score`

Mede se a classificação faz sentido considerando o histórico do creator ou canal.

Exemplo:

- canal especializado em manutenção;
- vídeo classificado como manutenção;
- score tende a subir.

#### `model_self_confidence`

Confiança declarada pela IA.

Deve ter peso menor, pois o modelo pode estar confiante e ainda assim errado.

---

## `agreement_score`

O `agreement_score` mede a concordância entre a classificação humana e a classificação da IA.

Ele só existe nas etapas de validação, quando há classificação humana disponível.

### Pesos iniciais

| Campo | Peso |
|---|---:|
| Nicho | 0.25 |
| Subnicho | 0.30 |
| Sub-subnicho | 0.15 |
| Tipo de conteúdo | 0.10 |
| Intenção da audiência | 0.10 |
| Marca do veículo | 0.05 |
| Modelo do veículo | 0.05 |

Total: `1.00`

### Pontuação por campo

Cada campo pode receber:

| Valor | Significado |
|---:|---|
| 1.0 | Concordância exata |
| 0.5 | Concordância parcial |
| 0.0 | Divergência |
| N/A | Campo não aplicável |

Campos não aplicáveis devem ser removidos do denominador para não penalizar vídeos que não citam marca ou modelo.

### Fórmula

```text
agreement_score = soma_dos_pesos_atingidos / soma_dos_pesos_aplicaveis
```

### Exemplo

| Campo | Resultado | Peso | Pontuação |
|---|---:|---:|---:|
| Nicho | correto | 0.25 | 0.25 |
| Subnicho | correto | 0.30 | 0.30 |
| Sub-subnicho | parcial | 0.15 | 0.075 |
| Tipo | correto | 0.10 | 0.10 |
| Intenção | errado | 0.10 | 0.00 |
| Marca | correta | 0.05 | 0.05 |
| Modelo | N/A | removido | removido |

Nesse caso, o score é recalculado sem o campo modelo.

---

## Critérios de decisão

### Aceitar sem transcrição

Aceitar classificação provisória se:

```text
confidence_score >= 0.80
```

Na etapa de validação humana, o método é considerado bom se:

```text
agreement_score >= 0.80
```

### Enviar para transcrição

Enviar vídeo para transcrição se:

```text
0.60 <= confidence_score < 0.80
```

Ou se qualquer uma das condições abaixo ocorrer:

- título ambíguo;
- descrição fraca;
- subnicho incerto;
- vídeo de alta performance;
- vídeo com crescimento fora da curva;
- vídeo de creator estratégico;
- IA identifica múltiplas categorias possíveis;
- marca/modelo parecem importantes, mas não estão claros.

### Revisão humana direta

Enviar para revisão humana direta se:

```text
confidence_score < 0.60
```

Também enviar para revisão humana se, após transcrição:

```text
confidence_score < 0.75
```

---

## Fluxo de validação inicial

```text
Selecionar 10 vídeos
        ↓
Classificação humana
        ↓
Classificação IA sem transcrição
        ↓
Calcular confidence_score
        ↓
Calcular agreement_score
        ↓
Analisar divergências
        ↓
Ajustar taxonomia e prompt
        ↓
Repetir nos mesmos 10 vídeos
        ↓
Se agreement_score médio >= 0.80
        ↓
Avançar para amostra maior
```

---

## Critério para avançar de fase

### Fase 1 — 10 vídeos

Avançar se:

```text
agreement_score médio >= 0.80
```

E se:

```text
nenhuma categoria crítica estiver ausente da taxonomia
```

### Fase 2 — 50 vídeos

Objetivo:

- testar variedade maior;
- medir estabilidade do prompt;
- identificar categorias faltantes;
- avaliar distribuição de confiança.

Critério de avanço:

```text
agreement_score médio >= 0.80
```

E:

```text
menos de 20% dos vídeos classificados como geral/outros
```

### Fase 3 — 500 vídeos

Objetivo:

- validar escala;
- medir custo;
- identificar padrões de erro;
- separar vídeos que precisam de transcrição.

### Fase 4 — base completa

Rodar nos mais de 4.000 vídeos somente depois de validar as fases anteriores.

---

## Erros esperados na primeira rodada

A primeira rodada provavelmente revelará problemas como:

- IA confundindo tipo de conteúdo com subnicho;
- IA usando marca/modelo como subnicho;
- taxonomia insuficiente;
- excesso de vídeos classificados como `geral`;
- títulos muito ambíguos;
- descrições pouco informativas;
- falta de contexto do canal;
- confidence_score alto em resposta errada;
- divergência entre humano e IA em conteúdo híbrido.

Esses erros são esperados e fazem parte da calibração.

---

## Regras para revisão de taxonomia

A taxonomia deve ser revisada quando:

- muitos vídeos caírem em `geral` ou `outros`;
- a IA escolher categorias próximas, mas não exatas;
- o humano usar categorias que não existem;
- marca/modelo estiverem sendo tratados como tema;
- conteúdos híbridos forem frequentes;
- o mesmo tipo de vídeo receber classificações diferentes;
- o subnicho for amplo demais para análise útil.

### Regra importante

Marca e modelo **não devem virar subnicho**.

Exemplo:

```text
Jeep Compass com problema crônico no câmbio
```

Classificação correta:

```text
niche: diagnostico
sub_niche: cambio
sub_sub_niche: problema_cronico
vehicle_brand: Jeep
vehicle_model: Compass
automotive_system: transmissao
component: cambio_automatico
```

Classificação incorreta:

```text
sub_niche: Jeep Compass
```

---

## Planilha inicial de validação

Antes de implementar em banco, usar uma planilha ou CSV simples com as seguintes colunas:

```text
post_id
title
description
creator
channel_title
post_date
views
likes
comments
duration
short_or_long
human_niche
human_sub_niche
human_sub_sub_niche
human_content_type
human_audience_intent
human_vehicle_brand
human_vehicle_model
human_vehicle_year_or_generation
human_automotive_system
human_component
human_problem
human_confidence
human_note
ai_niche
ai_sub_niche
ai_sub_sub_niche
ai_content_type
ai_audience_intent
ai_vehicle_brand
ai_vehicle_model
ai_vehicle_year_or_generation
ai_automotive_system
ai_component
ai_problem
metadata_clarity_score
taxonomy_fit_score
evidence_score
creator_context_score
model_self_confidence
ai_confidence_score
agreement_score
needs_transcript
needs_human_review
review_notes
```

---

## Resultado esperado da primeira validação

Ao final da primeira rodada com 10 vídeos, espera-se ter:

1. Os 10 vídeos classificados manualmente.
2. Os 10 vídeos classificados pela IA.
3. `agreement_score` por vídeo.
4. `confidence_score` por vídeo.
5. Lista de divergências humano vs IA.
6. Lista de categorias faltantes.
7. Lista de vídeos que precisariam de transcrição.
8. Ajustes necessários no prompt.
9. Ajustes necessários na taxonomia.
10. Decisão se o método pode avançar para 50 vídeos.

---

## Indicadores de qualidade do método

Durante a validação, acompanhar:

- `agreement_score` médio;
- mediana do `agreement_score`;
- menor `agreement_score`;
- percentual de vídeos com `agreement_score >= 0.80`;
- percentual de vídeos com `confidence_score >= 0.80`;
- percentual de vídeos enviados para transcrição;
- percentual de vídeos enviados para revisão humana;
- percentual de vídeos classificados como `geral` ou `outros`;
- divergências mais comuns por campo.

---

## Decisão operacional

A classificação automática de nichos e subnichos não deve ser escalada diretamente para os mais de 4.000 vídeos.

Antes, deve passar por validação controlada com 10 vídeos, comparando humano vs IA.

Apenas depois de atingir concordância aceitável o método deve avançar para amostras maiores e, posteriormente, para a base completa.

---

## Próxima etapa

Depois desta spec, a próxima discussão deve definir o método de implementação da classificação, incluindo:

- como selecionar os 10 vídeos;
- onde armazenar temporariamente a planilha de validação;
- como montar o prompt da IA;
- como calcular os scores automaticamente;
- como versionar a taxonomia;
- como registrar divergências;
- como decidir quando buscar transcrição;
- como transformar o método em pipeline.

---

## Sugestão de commit

```bash
git commit -m "docs(enrichment): define spec de validacao de nichos e subnichos"
```

---

## Duas entregas humanas do piloto

Decisao registrada em 2026-07-16:

A classificacao humana dos `10` videos sera feita em duas entregas separadas,
mantendo a mesma taxonomia, os mesmos campos e a mesma amostra.

### Entrega 1 - classificacao pela descricao

- classificar os `10` videos usando a descricao como evidencia semantica
  principal
- nao assistir ao video nem usar audio, transcricao ou os `90s` iniciais
- preservar duvidas e falta de evidencia em `observacoes`
- nao criar categoria ad hoc apenas para completar campos sem evidencia

### Entrega 2 - classificacao pelos `90s` iniciais

- classificar novamente os mesmos `10` videos depois de assistir e ouvir os
  `90s` iniciais
- quando o video tiver menos de `90s`, considerar o video completo
- registrar uma nova classificacao, sem sobrescrever a Entrega 1
- usar a evidencia audiovisual para confirmar, complementar ou revisar os
  campos preenchidos anteriormente

### Regra de comparacao

As duas entregas devem permanecer separadas para permitir:

- comparar classificacao por descricao versus classificacao com `90s` de
  conteudo
- identificar campos alterados com evidencia adicional
- medir se a descricao foi suficiente
- calibrar a futura classificacao inicial e a reclassificacao apos transcricao
  parcial

As entregas esperadas devem usar identificacao explicita:

- `entrega_1_descricao`
- `entrega_2_90s_iniciais`

A descricao dos videos precisa estar disponivel antes da Entrega 1. A amostra
canonica do doc `33` ainda nao contem esse campo, portanto sua aquisicao e
inclusao no artefato de execucao e um pre-requisito operacional.
