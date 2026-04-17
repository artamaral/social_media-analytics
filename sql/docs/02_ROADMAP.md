# 🧭 ROADMAP

## ☠️  NON Negotiable -> Parar tudo pra fazer!
# Finalizar toda a documentacao no Github
- [x] Documentacao do SQL -> Incluir tabelas com extensao correta, deletar atual. Usar VScode para ficar com extensao correta
- [x] Documentacao do SQL -> Entender e documentar os trigger do banco de dados e documenta-los.
- [x] Incluir os dois scripts de trigger no Github, verificar qual o local 
- [x] Checar a documentacao existente para o inclusao de novos dados, atualiza-la e gerar um arquivo.MD

## 🔴 PRIORIDADE ALTA (infra / funcionamento)

- [ ] Como havaliar e garantir que os post estao sendo atualizados
    - [x] Nao estavam sendo atualizado, novo codigo rodando.
    - [ ]Existe teste pendende, descricao doq ue deve ser feito em 08_QUEUE_CAPACITY_TEST.md
- [ ] Garantir que scraper percorre TODOS creators
- [ ] Validar integridade de post_metrics_history
- [ ] Criar query de auditoria de coleta

## 🟡 MÉDIA (confiabilidade)

- [ ] Detectar gaps de coleta por post
- [ ] Validar atualização de collected_at

## 🟢 BAIXA (produto / insights)

- [ ] Dashboard inicial
- [ ] Ranking de crescimento semanal