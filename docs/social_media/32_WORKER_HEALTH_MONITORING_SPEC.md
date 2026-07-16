# Worker Health Monitoring Spec

## Objetivo

Definir como monitorar indiretamente se o worker de metricas esta funcionando
sem depender do retorno do script.

A ideia e observar os efeitos do worker no banco e na fila. Se os efeitos
aparecem, o worker provavelmente esta ativo. Se os efeitos param, o worker
pode estar parado, travado ou executando sem impacto real.

## Principio

Nao confiar apenas em:

- retorno do script
- log de terminal
- existencia do agendamento

Confiar principalmente em:

- inserts novos em `post_metrics_history`
- atualizacao de `collected_at`
- movimento na fila `v_post_update_queue_batch`
- variacao do volume de posts processados ao longo do tempo

## Sinais observaveis

## Frequencia operacional atual

- Worker `postMetrics`: execucao a cada `30 minutos`
- Worker `youtube_main_scraper`: execucao a cada `3 horas`
- Configuracao Cloud Run usada como base FinOps: maximo `1 vCPU` e `256 MB`
  de RAM por worker

Essa configuracao permite aumentar a cadencia sem duplicar workers nem misturar
discovery com atualizacao de metricas.

### Contrato atual do discovery com heartbeat

O worker `youtube_main_scraper` comprova resultado no banco quando insere ou
atualiza posts em `public.posts`, mas agora tambem persiste heartbeat em
`public.youtube_discovery_heartbeats`.

Contrato minimo persistido por execucao:

- `started_at`
- `finished_at`
- `status`
- `processed_creators`
- `attempted_creators`
- `inserted_or_updated_posts`
- `errors`
- `cursor_start`
- `cursor_end`
- `error_summary`

Uso do heartbeat no dashboard:

- diferenciar `rodou sem novidades` de `nao rodou`
- sinalizar `falhou antes de gerar resultado` quando o ultimo heartbeat ficar
  em `failed`
- manter `posts.created_at` e `creator_metrics_history` apenas como fallback
  quando nao houver heartbeat recente disponivel

Validacao inicial em producao:

- data: `2026-07-16`
- resultado observado:
  - `heartbeat_id = 2`
  - `processed = 3`
  - `errors = 0`
  - `inserted_or_updated_posts = 150`
  - `cursor 3 -> 6`
- a leitura do Streamlit ficou coerente para o caso `success` com posts novos
- permanecem sem evidencia real ate o momento:
  - `partial_error`
  - `failed`
  - `success` sem novos posts

### 1. Evidencia de snapshot novo

Indicador principal:

- `ultima_evidencia_de_execucao`

Como medir:

- maior `created_at` em `post_metrics_history`
- ou maior `collected_at` em posts atualizados

Leitura:

- `ok`: evidencia recente dentro da janela esperada
- `atencao`: evidencia um pouco atrasada, mas ainda em movimento
- `nok`: nenhuma evidencia nova alem do limite tolerado

### 2. Volume atualizado nas ultimas 24h

Indicador principal:

- `posts_atualizados_24h`

Como medir:

- contar `post_id` distintos com snapshot novo no periodo

Leitura:

- `ok`: volume compativel com a operacao normal
- `atencao`: volume abaixo do esperado, mas ainda existente
- `nok`: zero atualizacoes ou queda abrupta fora do padrao

### 3. Movimento da fila

Indicador principal:

- `movimento_da_fila`

Como medir:

- quantidade de linhas elegiveis na `v_post_update_queue_batch`
- mudanca da composicao da fila entre leituras
- presenca de `next_check` avancando

Leitura:

- `ok`: fila muda entre leituras e posts avancam
- `atencao`: fila muda pouco, mas ainda ha sinais de processamento
- `nok`: fila parada por tempo acima do limite

### 4. Idade da ultima evidencia

Indicador principal:

- `idade_da_ultima_evidencia`

Como medir:

- diferenca entre `now()` e o ultimo `created_at` ou `collected_at`

Leitura inicial recomendada:

- `ok`: ate 30 minutos
- `atencao`: acima de 30 minutos e ate 2 horas
- `nok`: acima de 2 horas

Com o worker `postMetrics` rodando a cada `30 minutos`, esses limites continuam
adequados para detectar atraso sem gerar falso positivo em uma unica execucao
perdida. Se a frequencia mudar novamente, recalibrar esses thresholds.

## Padrao de cor

Usar a mesma semantica em qualquer dashboard ou card que represente o
monitoramento do worker:

- `ok` -> verde
- `atencao` -> amarelo
- `nok` -> vermelho

Regra de leitura:

- `ok` significa que ha evidencia consistente de funcionamento
- `atencao` significa degradacao, atraso ou volume abaixo do esperado
- `nok` significa ausencia de evidencia ou parada provavel

## View sugerida

Nome recomendado para consolidar essa leitura em uma view unica:

```text
public.v_dashboard_worker_health_status
```

Campos sugeridos:

- `checked_at`
- `ultima_evidencia_de_execucao`
- `idade_da_ultima_evidencia_minutos`
- `posts_atualizados_24h`
- `fila_total_itens`
- `fila_itens_prontos`
- `fila_itens_atrasados`
- `status_code`
- `status_label`
- `status_color`

## Regras de interpretacao

### Ok

Usar quando:

- existe snapshot novo recente
- ha atualizacao real em `post_metrics_history`
- a fila ainda mostra movimentacao esperada

### Atencao

Usar quando:

- o worker ainda produz efeito, mas com atraso
- o volume atualizado caiu abaixo do esperado
- a fila apresenta pouca rotacao

### Nok

Usar quando:

- nao ha evidencia nova alem do limite tolerado
- a fila nao muda
- o banco nao recebe inserts esperados
- o estado sugere worker parado, falhando ou sem efeito

## Uso recomendado no dashboard

O card do worker nao deve depender da resposta do script.

Ele deve mostrar:

- ultimo snapshot
- posts atualizados nas ultimas 24h
- idade da ultima evidencia
- status geral com cor `ok / atencao / nok`

## Relacao com os outros blocos

Esse monitoramento complementa:

- `Data quality`, que mostra problemas dos dados
- `Sanitizacao operacional`, que trata casos humanos e confirmacao manual
- `04_PIPELINE_STATUS.md`, que registra o estado operacional global

## Validacao minima

Antes de considerar essa leitura pronta:

- confirmar que o ultimo snapshot realmente muda quando o worker roda
- confirmar que a fila muda entre leituras
- confirmar que a ausencia de insert altera o status para `atencao` ou `nok`
- confirmar que a representacao visual usa a mesma cor em toda a interface
