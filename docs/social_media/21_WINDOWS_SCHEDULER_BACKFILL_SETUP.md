# WINDOWS SCHEDULER - LEGACY LOW BACKFILL PHASE 1

## Objetivo

Automatizar a execucao do script:

- `scripts/offline_backfill/legacy_low_backfill_phase1.py`

sem precisar rodar manualmente varias vezes.

---

## Arquivo de execucao recomendado

Use o launcher em PowerShell:

- `scripts/offline_backfill/run_legacy_low_backfill_phase1.ps1`

Motivo:

- fixa o diretorio correto
- chama o script Python pelo caminho certo
- reduz erro manual ao rodar pelo Agendador do Windows
- grava logs persistentes por execucao em `scripts/offline_backfill/logs`

---

## Pre-condicoes

Antes de criar a tarefa:

1. confirmar que existe o arquivo:
   - `scripts/offline_backfill/.env`
2. confirmar que o `.env` tem:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `YOUTUBE_API_KEY`
3. confirmar que o Python roda na maquina:
   - `py -3 --version`
   - ou `python --version`

---

## Frequencia recomendada

Com a observacao operacional mais recente, a frequencia recomendada para a fase
1 passa a ser:

- 1 execucao a cada `10` minutos

Motivo:

- o objetivo atual e drenar o `legacy_low` o mais rapido possivel antes da fase 2
- foi observado baixo consumo da API do YouTube mesmo com frequencia alta
- a fase 1 nao depende de janela de `6h`, entao pode rodar mais agressivamente
  do que a fase 2

---

## Criacao via interface grafica

No Agendador de Tarefas do Windows:

1. abrir `Agendador de Tarefas`
2. clicar em `Criar Tarefa`
3. aba `Geral`
   - Nome: `legacy-low-backfill-phase1`
   - marcar `Executar estando o usuario conectado ou nao`, se desejar
4. aba `Disparadores`
   - Novo
   - Iniciar: em um horario proximo
   - Repetir tarefa a cada: `10 minutos`
   - Duracao: `1 dia`
5. aba `Acoes`
   - Programa/script:
     - `powershell.exe`
   - Adicionar argumentos:
     - `-ExecutionPolicy Bypass -File "C:\social_media-analytics\scripts\offline_backfill\run_legacy_low_backfill_phase1.ps1"`
6. aba `Iniciar em`:
   - `C:\social_media-analytics\scripts\offline_backfill`
7. salvar

---

## Criacao via linha de comando

Comando sugerido:

```powershell
schtasks /Create /TN "legacy-low-backfill-phase1" /SC MINUTE /MO 10 /TR "powershell.exe -ExecutionPolicy Bypass -File \"C:\social_media-analytics\scripts\offline_backfill\run_legacy_low_backfill_phase1.ps1\"" /F
```

---

## Execucao manual de teste

Antes de confiar no scheduler, rode manualmente:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\social_media-analytics\scripts\offline_backfill\run_legacy_low_backfill_phase1.ps1"
```

---

## Logs obrigatorios de execucao

O launcher agora grava logs locais por execucao.

Arquivos esperados:

- `scripts/offline_backfill/logs/legacy_low_backfill_phase1_YYYY-MM-DD_HH-mm-ss.log`
- `scripts/offline_backfill/logs/legacy_low_backfill_phase1_latest.log`

Diretriz operacional:

- nenhuma rotina agendada deve rodar sem log persistente
- sem log, a rotina deve ser tratada como operacionalmente cega
- a validacao do scheduler precisa olhar banco e log

Comandos uteis:

```powershell
Get-Content "C:\social_media-analytics\scripts\offline_backfill\logs\legacy_low_backfill_phase1_latest.log" -Tail 200
```

```powershell
Get-Content "C:\social_media-analytics\scripts\offline_backfill\logs\legacy_low_backfill_phase1_latest.log" -Wait
```

---

## Validacao apos agendar

Depois da primeira execucao automatica, validar:

1. o historico recebeu novos snapshots:

```sql
select
  max(collected_at) as ultimo_snapshot
from post_metrics_history;
```

2. `legacy_low` caiu novamente:

```sql
select
  count(*) as total_legacy_low
from posts p
left join (
  select
    post_id,
    count(*) as total_checagens
  from post_metrics_history
  group by post_id
) h on h.post_id = p.post_id
where p.created_at < now() - interval '7 days'
  and coalesce(h.total_checagens, 0) <= 1;
```

3. a ultima execucao do scheduler terminou com sucesso no Windows

4. o log mais recente mostra inicio, selecao, chamada da YouTube API e insert

```powershell
Get-Content "C:\social_media-analytics\scripts\offline_backfill\logs\legacy_low_backfill_phase1_latest.log" -Tail 200
```

---

## Diagnostico minimo quando o scheduler parecer parado

1. confirmar a acao registrada:

```powershell
schtasks /Query /TN "legacy-low-backfill-phase1" /V /FO LIST
```

2. confirmar o comando correto:

- Programa/script:
  - `powershell.exe`
- Argumentos:
  - `-ExecutionPolicy Bypass -File "C:\social_media-analytics\scripts\offline_backfill\run_legacy_low_backfill_phase1.ps1"`
- Iniciar em:
  - `C:\social_media-analytics\scripts\offline_backfill`

3. confirmar se o log foi atualizado no horario esperado

4. confirmar inserts novos em `post_metrics_history`

Incidente registrado:

- foi identificado um periodo em que a tarefa do Windows estava com a acao malformada
- o scheduler aparentava rodar, mas nao executava o script corretamente
- a ausencia de log persistente atrasou o diagnostico e gerou perda de tempo operacional

Decisao:

- logs locais passam a ser parte obrigatoria do desenho da rotina
- revisao do log mais recente passa a ser etapa padrao de troubleshooting

---

## Quando pausar a tarefa

Pausar ou remover a tarefa quando:

- `legacy_low` estiver proximo de zero
- a fase 1 for considerada concluida
- o projeto for migrar para a fase 2

---

## Status

Este documento cobre apenas a automacao da fase 1 do backfill offline de
`legacy_low`.
