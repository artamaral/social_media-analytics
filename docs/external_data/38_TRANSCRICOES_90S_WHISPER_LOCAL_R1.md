# Transcricoes 90s Whisper Local - Round 1

## Objetivo

Registrar as transcricoes locais dos primeiros `90s` dos `10` videos do piloto
do Sprint 6, sem usar chave OpenAI e sem chamar API de transcricao.

O artefato serve para evoluir a taxonomia e alimentar um novo round GPT 5.5. Ele
nao e benchmark final do fluxo automatizado futuro.

## Fonte e metodo

- amostra: `docs/external_data/33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv`
- saida canonica: `docs/external_data/38_TRANSCRICOES_90S_WHISPER_LOCAL_R1.csv`
- utilitario: `scripts/external_data/transcribe_pilot_90s_whisper.py`
- origem do audio: `https://www.youtube.com/watch?v={post_id}`
- transcricao: Whisper local via `faster-whisper`
- modelo: `small`
- idioma: `pt`
- compute type: `int8`

O audio temporario fica em `tmp/whisper_pilot_90s` e nao deve ser versionado.

## Resultado da execucao

Execucao realizada em 2026-07-20:

- videos processados: `10`
- transcricoes com `success`: `10`
- transcricoes com `partial`: `0`
- transcricoes com `failed`: `0`
- videos com duracao completa por terem menos de `90s`: `2`
  (`pINW53ErjQI` e `_j1gOOnjgcU`)
- arquivos temporarios de audio preservados no Git: `0`

O modelo local foi baixado pelo `faster-whisper` para o cache do usuario e nao
foi versionado no repositorio.

## Contrato do CSV

Cada linha representa um video primario da amostra e preserva falhas sem remover
o item do lote:

```text
post_id
video_url
transcription_status
input_duration_seconds
transcribed_duration_seconds
transcript_90s
language
whisper_model
compute_type
source_method
error_message
created_at
```

Valores esperados para `transcription_status`:

- `success`: transcript preenchido
- `partial`: audio processado, mas transcript vazio ou incompleto
- `failed`: download ou transcricao falhou, com `error_message`

## Uso

Instalar as dependencias no ambiente local e executar:

```powershell
C:\ProgramData\miniforge3\python.exe -m pip install yt-dlp faster-whisper imageio-ffmpeg
C:\ProgramData\miniforge3\python.exe scripts\external_data\transcribe_pilot_90s_whisper.py
```

## Validacao esperada

- exatamente `10` linhas no CSV
- todos os `post_id` primarios do doc `33` aparecem uma vez
- sucessos possuem `transcript_90s` preenchido
- videos menores que `90s` usam duracao completa
- nenhum arquivo de audio, video ou cache entra no Git

## Observacao

Como a transcricao roda localmente, a qualidade pode variar conforme audio,
ruido, musica de fundo, fala simultanea e disponibilidade do download pelo
YouTube. Erros devem ser preservados no CSV para decisao manual de fallback.

Nesta rodada, o Whisper local apresentou algumas imprecisoes de reconhecimento
em nomes proprios e termos automotivos. Isso e aceitavel para calibracao
taxonomica, mas deve ser considerado ao comparar a classificacao GPT 5.5 com o
baseline humano.
