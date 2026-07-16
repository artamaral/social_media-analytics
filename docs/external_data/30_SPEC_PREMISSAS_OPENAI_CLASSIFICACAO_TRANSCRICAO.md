# Spec — Premissas de uso da OpenAI para classificação e transcrição de vídeos

## 1. Objetivo

Documentar as premissas operacionais para a etapa de enriquecimento de vídeos do projeto `social_media-analytics`, usando neste momento apenas OpenAI para:

1. classificação inicial de nicho/subnicho com dados já existentes;
2. transcrição de áudio quando necessária;
3. reclassificação após transcrição;
4. controle de custo, TPM/RPM e risco operacional em conta Tier 1.

Esta decisão substitui, por enquanto, a avaliação de múltiplos provedores como DeepSeek, Google Speech-to-Text, AWS Transcribe, Deepgram ou Whisper local.

---

## 2. Decisão atual

Nesta fase, o projeto usará somente OpenAI para a camada de IA/transcrição.

### Motivos

- O usuário já possui créditos na OpenAI.
- O custo estimado da classificação e da transcrição parcial é baixo.
- Adicionar outro provedor agora aumentaria complexidade operacional.
- O principal risco não é custo, mas limite de TPM/RPM em Tier 1.
- O método ainda está em validação com amostra pequena.

### Decisão operacional

Não otimizar por custo nesta fase.

Prioridade:

1. validar método;
2. evitar erro de rate limit;
3. manter implementação simples;
4. garantir rastreabilidade;
5. evitar retrabalho com múltiplas APIs.

---

## 3. Premissas de conta e limite

O usuário está em Tier 1 na API da OpenAI e já observou problemas de TPM em outros fluxos, especialmente no Hermes.

Segundo a documentação da OpenAI, rate limits são aplicados por organização e podem limitar tanto requests por minuto quanto tokens por minuto. Requisições malsucedidas também podem contribuir para o limite por minuto. Portanto, o pipeline deve evitar rajadas, retries agressivos e execução paralela excessiva.

### Premissa crítica

O pipeline de classificação de vídeos não deve competir agressivamente com o Hermes pelo mesmo limite de tokens.

Se possível, executar:

- em horários diferentes;
- com batches pequenos;
- com baixa concorrência;
- com controle de retry/backoff;
- com limite diário de processamento.

---

## 4. Modelos sugeridos nesta fase

### 4.1 Classificação inicial

Modelo sugerido:

```text
gpt-5-nano ou gpt-5.4-nano
```

Uso:

- classificar nicho;
- classificar subnicho;
- classificar sub-subnicho, se aplicável;
- identificar tipo de conteúdo;
- identificar intenção da audiência;
- identificar marca/modelo, se disponível;
- calcular componentes do confidence score.

Premissa:

A classificação inicial é uma tarefa estruturada, curta e repetitiva. Portanto, deve usar modelo barato e rápido, não modelo avançado.

---

### 4.2 Transcrição

Modelo sugerido:

```text
gpt-4o-mini-transcribe
```

Uso:

- transcrever apenas vídeos que não atingiram confiança mínima;
- começar com trecho curto;
- não transcrever vídeo inteiro na primeira fase.

Premissa:

A transcrição só é acionada quando a classificação inicial não é suficiente ou quando o vídeo tem alta relevância analítica.

Ponto de atenção operacional:

- no `gpt-4o-mini-transcribe`, o principal consumo de tokens vem do áudio de
  entrada, não do texto final transcrito
- quando não houver `prompt` textual adicional, o input manual tende a ser
  desprezível perto do áudio enviado
- a saída textual costuma ser pequena em relação ao input de áudio, então o
  risco de `TPM` deve ser lido principalmente como função de minutos de áudio
  processados por janela, e não apenas pelo tamanho do transcript
- em teste manual do projeto com um vídeo de `176s`, a resposta transcrita
  ficou em cerca de `290` a `300` tokens de saída, enquanto a estimativa de
  input ficou em torno de `7k` audio tokens
- conclusão prática: para esta frente, o gargalo provável de tokens tende a ser
  volume de áudio e paralelismo, não comprimento do texto retornado

---

### 4.3 Reclassificação pós-transcrição

Modelo sugerido:

```text
gpt-5-nano ou gpt-5.4-nano
```

Uso:

- reavaliar classificação com evidência adicional da transcrição;
- comparar classificação inicial versus nova evidência;
- atualizar confidence score;
- decidir aprovação, nova iteração ou revisão humana.

---

## 5. Fluxo operacional

```text
Vídeo catalogado
↓
Classificação inicial com dados existentes
↓
Calcula confidence_score
↓
Se confidence alto: aprova
↓
Se confidence médio/baixo: tenta transcrição parcial
↓
Reclassifica com transcrição
↓
Se confidence alto: aprova
↓
Se confidence ainda médio: busca +30s, uma vez
↓
Se confidence continua baixo: revisão humana
```

---

## 6. Dados usados na classificação inicial

A primeira classificação deve usar somente dados existentes:

- título;
- descrição;
- nome do canal;
- creator;
- duração;
- short_or_long;
- views;
- likes;
- comments;
- data de publicação;
- contexto básico do creator, se disponível;
- taxonomia permitida.

Não usar transcrição na primeira chamada.

---

## 7. Campos classificados

A IA deve retornar, no mínimo:

```text
niche
sub_niche
sub_sub_niche
content_type
audience_intent
vehicle_brand
vehicle_model
vehicle_year_or_generation
automotive_system
component
problem
confidence_score
confidence_components
reason_short
needs_transcript
needs_human_review
```

Marca e modelo devem ser tratados como dimensões próprias, não como subnichos.

Exemplo:

```json
{
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
  "problem": "falha_cronica",
  "confidence_score": 0.84,
  "needs_transcript": false,
  "needs_human_review": false
}
```

---

## 8. Confidence score

O confidence score não deve depender apenas da confiança declarada pelo modelo.

A confiança inicial deve ser composta por componentes explícitos:

```text
confidence_score =
  0.35 * metadata_clarity_score +
  0.25 * taxonomy_fit_score +
  0.20 * evidence_score +
  0.10 * creator_context_score +
  0.10 * model_self_confidence
```

### Componentes

#### metadata_clarity_score

Mede se título e descrição são claros.

#### taxonomy_fit_score

Mede se o conteúdo encaixa claramente em uma categoria existente da taxonomia.

#### evidence_score

Mede se múltiplos campos apontam para a mesma classificação.

#### creator_context_score

Mede se a classificação faz sentido com o histórico ou perfil do canal.

#### model_self_confidence

Confiança declarada pelo modelo, com peso menor.

---

## 9. Thresholds iniciais

### Classificação sem transcrição

```text
confidence_score >= 0.85
→ aprovado automático

confidence_score >= 0.75 e < 0.85
→ aprovado provisório / amostragem humana

confidence_score >= 0.60 e < 0.75
→ enviar para transcrição parcial

confidence_score < 0.60
→ revisão humana ou transcrição se vídeo for relevante
```

### Depois da transcrição

```text
confidence_score >= 0.80
→ aprovado

confidence_score >= 0.70 e < 0.80
→ buscar +30s uma única vez

confidence_score < 0.70
→ revisão humana
```

### Limite de iteração automática

```text
Máximo de 2 tentativas automáticas:
1. transcrição inicial curta
2. +30s adicional
```

Depois disso, o vídeo deve ir para revisão humana ou ser marcado como incerto.

---

## 10. Estratégia de transcrição

A transcrição não deve ser aplicada em todos os vídeos.

### Transcrever quando

- confidence_score inicial < 0.75;
- vídeo tem alta performance relativa;
- vídeo é de creator estratégico;
- título/descrição são ambíguos;
- subnicho é incerto, mas nicho parece correto;
- vídeo pode alimentar insight relevante.

### Não transcrever quando

- classificação inicial é clara;
- vídeo tem baixa prioridade;
- vídeo é antigo e sem crescimento;
- título e descrição resolvem o subnicho;
- vídeo não é relevante para análise atual.

---

## 11. Controle de TPM/RPM

Como a conta é Tier 1 e já existem problemas de TPM no Hermes, o pipeline deve ser conservador.

### Regras obrigatórias

1. Não processar os 4k vídeos em uma única execução.
2. Começar com amostra de 10 vídeos.
3. Depois testar lote de 50 vídeos.
4. Depois testar lote de 100 vídeos.
5. Usar concorrência 1 no início.
6. Implementar backoff exponencial em erro 429.
7. Evitar retry imediato.
8. Registrar tokens estimados por chamada.
9. Separar horários do Hermes.
10. Definir limite diário de vídeos classificados.

---

## 12. Configuração inicial recomendada

### Validação metodológica

```text
batch_size = 10
concurrency = 1
max_retries = 3
retry_backoff = exponencial
max_videos_per_day = 10 a 50
```

### Teste controlado

```text
batch_size = 25
concurrency = 1
max_retries = 3
max_videos_per_day = 100
```

### Escala inicial segura

```text
batch_size = 50
concurrency = 1 ou 2
max_videos_per_day = 250 a 500
```

Aumentar apenas após observar consumo real de TPM e ausência de 429.

---

## 13. Estimativa conservadora de tokens

### Classificação inicial por vídeo

```text
Input estimado: 1.500 a 2.500 tokens
Output estimado: 300 a 600 tokens
```

### Reclassificação com transcrição curta

```text
Input estimado: 3.000 a 5.000 tokens
Output estimado: 400 a 700 tokens
```

### Observação importante

A taxonomia enviada no prompt pode aumentar muito o input.

No caso da transcrição, porém, o cuidado principal não é o tamanho do prompt
textual. O ponto mais importante é que a entrada dominante é o próprio áudio.
Portanto:

- classificação e reclassificação escalam com texto
- transcrição escala primeiro com minutos de áudio
- o transcript final adiciona custo, mas normalmente pesa menos que o áudio de
  entrada
- para estimativa operacional rápida, usar minutos de áudio por lote como
  proxy primária de `TPM`

Para controlar TPM:

- manter taxonomia enxuta;
- enviar apenas categorias ativas;
- evitar descrição longa de todos os subnichos;
- usar IDs curtos de taxonomia quando possível;
- não enviar transcrição inteira.

---

## 14. Estratégia para evitar TPM

### 14.1 Reduzir tamanho do prompt

- Taxonomia curta.
- Descrição truncada.
- Transcript excerpt limitado.
- JSON schema objetivo.
- Não enviar métricas irrelevantes.

### 14.2 Reduzir output

- Exigir JSON curto.
- Limitar `reason_short`.
- Não pedir explicação longa.
- Não pedir alternativas múltiplas.

### 14.3 Reduzir concorrência

- Começar com uma chamada por vez.
- Evitar workflows paralelos no n8n.
- Separar classificação e transcrição em filas.

### 14.4 Controlar retry

- Retry somente para erros transitórios.
- Backoff exponencial.
- Máximo de 3 tentativas.
- Não repetir imediatamente em erro de TPM.

### 14.5 Controlar agenda

- Rodar fora dos horários do Hermes.
- Pausar classificação quando Hermes estiver executando rotinas pesadas.
- Definir janelas horárias dedicadas.

---

## 15. Integração com n8n

O n8n deve orquestrar, não executar lógica pesada.

### Papel do n8n

- consultar views de candidatos;
- controlar lotes;
- chamar endpoint de classificação;
- chamar endpoint de transcrição;
- registrar status;
- encaminhar para revisão humana.

### Papel do serviço Python/API

- montar prompt;
- chamar OpenAI;
- calcular confidence score;
- validar JSON;
- registrar tentativa;
- controlar erros e retries técnicos.

### Papel do banco

- manter fonte da verdade;
- guardar status;
- guardar histórico de tentativas;
- indicar próximos itens via views;
- impedir duplicidade com lock/status.

---

## 16. Estados mínimos do fluxo

```text
pending_initial_classification
processing_initial_classification
classified_without_transcript
needs_transcript
transcribing
transcribed
processing_reclassification
approved
auto_approved_provisional
needs_more_transcript_context
needs_human_review
failed
```

---

## 17. Histórico obrigatório de tentativas

Cada tentativa deve registrar:

```text
post_id
attempt_type
model_name
prompt_version
input_token_estimate
output_token_estimate
confidence_score
classification_result
error_message
created_at
```

Isso é necessário para auditar custo, TPM e qualidade.

---

## 18. Risco principal

O risco principal nesta fase não é custo.

O risco principal é:

```text
estourar TPM/RPM em Tier 1 e causar falhas no pipeline ou no Hermes.
```

Mitigação:

```text
batch pequeno
concurrency baixa
backoff exponencial
execução fora do horário do Hermes
limite diário
logs de tokens
sem transcrição em massa
```

---

## 19. Critério para avançar de fase

### Fase 1 — 10 vídeos

Avançar quando:

```text
agreement_score médio >= 0.80
sem erro de TPM
sem erro de JSON recorrente
prompt estável
```

### Fase 2 — 50 vídeos

Avançar quando:

```text
429 = zero ou raro
confidence distribution faz sentido
menos de 20% caindo em revisão humana sem motivo
custo real validado
```

### Fase 3 — 100 a 500 vídeos

Avançar quando:

```text
pipeline estável
sem competição com Hermes
logs confiáveis
tempo de execução aceitável
```

---

## 20. Decisão registrada

Decisão:

Nesta fase, o projeto usará apenas OpenAI para classificação, transcrição e reclassificação de vídeos.

Motivo:

O usuário já possui créditos OpenAI, o custo estimado é baixo e o uso de múltiplos provedores aumentaria complexidade antes da validação do método.

Restrição:

Como a conta é Tier 1 e já existem problemas de TPM no Hermes, o pipeline deve ser desenhado com batch pequeno, baixa concorrência, backoff exponencial e execução controlada por agenda.

Próxima etapa:

Definir o método de implementação da classificação inicial, começando por 10 vídeos classificados manualmente e comparados com a IA.

---

## 21. Baseline humano em duas entregas

Decisao registrada em 2026-07-16:

O baseline humano do piloto sera produzido em duas entregas:

1. `entrega_1_descricao`: classificacao pela descricao, sem assistir ao video e
   sem usar transcricao.
2. `entrega_2_90s_iniciais`: nova classificacao com a evidencia dos `90s`
   iniciais do video; para videos menores, usar o conteudo completo.

A segunda entrega nao substitui a primeira. Os dois resultados devem ser
preservados para medir o ganho de evidencia e orientar o desenho do fluxo:

```text
classificacao inicial por texto
-> evidencia parcial de ate 90s
-> reclassificacao
-> comparacao das alteracoes por campo
```

Esse contrato antecipa, na execucao humana, o mesmo padrao metodologico previsto
para a IA: classificacao inicial com dados existentes e reclassificacao apos
transcricao parcial.
