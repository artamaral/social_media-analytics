# Transcricoes 90s para Enriquecimento da Taxonomia V2 - R1

## Objetivo

Gerar transcricoes locais dos primeiros `90s` dos `10` videos selecionados no
doc `44`, para repetir a extracao de termos da Taxonomia V2 usando evidencia
mais rica que o titulo.

Esta entrega nao altera banco, workbook, pipeline nem CSVs v1. O resultado e
insumo para curadoria taxonomica e futura revisao dos CSVs V2 `42` e `43`.

## Fonte

- shortlist: `docs/external_data/44_ENRIQUECIMENTO_TAXONOMIA_V2_TITULOS_E_PROXIMA_TRANSCRICAO.md`
- transcricoes: `docs/external_data/45_TRANSCRICOES_90S_ENRIQUECIMENTO_TAXONOMIA_V2_R1.csv`
- metodo: `yt-dlp+faster-whisper-local`
- modelo: `small`
- idioma: `pt`
- `compute_type`: `int8`

## Resultado

- videos esperados: `10`
- videos transcritos com sucesso: `10`
- falhas finais: `0`
- videos menores que `90s` foram transcritos na duracao completa
- audio temporario nao foi versionado

Observacao operacional:

- o video `6qSnrkGd70I` falhou na primeira tentativa com erro de `ffmpeg`, mas
  teve sucesso em retry pontual

## Videos transcritos

| `post_id` | URL | Duracao de entrada | Duracao transcrita | Status |
| --- | --- | ---: | ---: | --- |
| `nKEuKTAX-eA` | `https://www.youtube.com/watch?v=nKEuKTAX-eA` | `38` | `38` | `success` |
| `ITBdyKnV5Pg` | `https://www.youtube.com/watch?v=ITBdyKnV5Pg` | `117` | `90` | `success` |
| `aXbFPJMVGKw` | `https://www.youtube.com/watch?v=aXbFPJMVGKw` | `1731` | `90` | `success` |
| `nP0q6x1Uqs0` | `https://www.youtube.com/watch?v=nP0q6x1Uqs0` | `179` | `90` | `success` |
| `xKNbBoiDt5g` | `https://www.youtube.com/watch?v=xKNbBoiDt5g` | `2495` | `90` | `success` |
| `RTZHxSE2t5M` | `https://www.youtube.com/watch?v=RTZHxSE2t5M` | `1392` | `90` | `success` |
| `3AjI62lO8b8` | `https://www.youtube.com/watch?v=3AjI62lO8b8` | `952` | `90` | `success` |
| `6qSnrkGd70I` | `https://www.youtube.com/watch?v=6qSnrkGd70I` | `851` | `90` | `success` |
| `Ffmnzmm4Sf8` | `https://www.youtube.com/watch?v=Ffmnzmm4Sf8` | `489` | `90` | `success` |
| `uZVDGJXqrgU` | `https://www.youtube.com/watch?v=uZVDGJXqrgU` | `436` | `90` | `success` |

## Proxima etapa

Executar a extracao semantica sobre o CSV `45`, separando:

- `extracted_raw_terms`
- `candidate_canonical_terms`
- `rejected_terms`
- `suggested_topic_path`
- `suggested_topic_path_secondary`
- `suggested_automotive_system`
- `suggested_component`
- `suggested_problem`
- `taxonomy_gaps`
- `validation_issues`
- `needs_human_review`

Regras ja fixadas:

- `motorhome`, `4x4` e `carros_descartaveis` continuam fora da lista canonica
- termos editoriais devem ser separados de termos tecnicos
- componente e problema so devem ser sugeridos quando forem compativeis com o
  sistema automotivo
- nenhuma categoria canonica nova deve ser criada automaticamente apenas por
  aparecer no transcript
