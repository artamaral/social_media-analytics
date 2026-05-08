# 🧭 ROADMAP

## ☠️  NON Negotiable -> Parar tudo pra fazer!

- [x] Validação da mudanca para FIFO dentro da banda ao inves de score. Usar arquivo "11_QUEUE_FIFO_VALIDATION_2026-05-08.md (line 1)." como referencia -> deixar rodas por dois dias. Validaçao em 2026_05_10

- [ ] Validar impacto FinOps e custos apos aumento do lote do worker para 40 posts por execucao. Medir Cloud Run, YouTube quota, Supabase writes, duracao media, erros e custo por snapshot antes de manter a mudanca como definitiva.
- [ ] Open point: reavaliar se o refill global da `v_post_update_queue_batch` deve continuar assim ou migrar para cascata por banda. Hoje, cotas nao usadas por uma banda vao para um pool global ordenado por antiguidade, e nao automaticamente para a proxima banda mais alta.
- [ ] Avaliar score hibrido em modo analitico sem segundo Cloud Run. Usar simulacao `v2` apenas no banco e validar com SQL + Excel/Pandas antes de qualquer troca no modelo ativo.

# Finalizar toda a documentacao no Github
- [x] Documentacao do SQL -> Incluir tabelas com extensao correta, deletar atual. Usar VScode para ficar com extensao correta
- [x] Documentacao do SQL -> Entender e documentar os trigger do banco de dados e documenta-los.
- [x] Incluir os dois scripts de trigger no Github, verificar qual o local 
- [x] Checar a documentacao existente para o inclusao de novos dados, atualiza-la e gerar um arquivo.MD
- [ ] Criar readme principal

## 🔴 PRIORIDADE ALTA (infra / funcionamento)

- [ ] Como havaliar e garantir que os post estao sendo atualizados
    - [x] Nao estavam sendo atualizado, novo codigo rodando.
    - [ ]Existe teste pendende, descricao doque deve ser feito em 08_QUEUE_CAPACITY_TEST.md e QUEUE SLICING AND RESCHEDULING.md
- [ ] Garantir que scraper percorre TODOS creators
- [ ] Validar integridade de post_metrics_history
- [ ] Criar query de auditoria de coleta

## 🟡 MÉDIA (confiabilidade)

- [ ] Detectar gaps de coleta por post
- [ ] Validar atualização de collected_at

## 🟢 BAIXA (produto / insights)

- [ ] Dashboard inicial
- [ ] Ranking de crescimento semanal
