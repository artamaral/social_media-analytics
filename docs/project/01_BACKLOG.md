# BACKLOG GERAL

## Pipeline

- [ ] Alta prioridade: tratar videos indisponiveis na YouTube API para evitar posts presos na fila. Casos observados: `BH0gnUODKwI` (`https://www.youtube.com/watch?v=BH0gnUODKwI`) e `lFodaSeTE9A` (`https://www.youtube.com/watch?v=lFodaSeTE9A`). Evidencia: os IDs entram na fila de atualizacao, mas a execucao processa apenas `38` itens de um lote de `40`, sugerindo que esses videos nao retornam no `videos.list`. Proposta inicial documentada em `docs/social_media/27_UNAVAILABLE_VIDEO_HANDLING_SPEC.md`: registrar IDs ausentes como `unavailable_candidate`, contar falhas recorrentes, expor `youtube_url` em view do dashboard e remover da fila ativa depois de limite definido.
- [ ] Melhorar controle de fim de lista no scraper
- [ ] Validar duplicidade de coleta
- [ ] Retry automatico para falhas API

## Dados / Qualidade

- [ ] Validar se todos posts possuem historico
- [ ] Checar consistencia de collected_at
- [ ] Identificar creators sem coleta recente

## Analytics

- [ ] Query de crescimento por intervalo
- [ ] Ranking de creators emergentes
- [ ] Identificacao de outliers

## Visualizacao / Estudos de mercado

- [ ] App Streamlit online consumindo Supabase sob demanda
- [ ] Tela inicial com status de qualidade dos dados
- [ ] Ranking de creators por views, engajamento e frequencia
- [ ] Ranking semanal de crescimento de videos
- [ ] Filtros por plataforma, creator, nicho e subnicho
- [ ] Exportacao CSV dos rankings principais

## IA / Classificacao

- [ ] Classificar videos por tipo
- [ ] Melhorar subnicho automatico
