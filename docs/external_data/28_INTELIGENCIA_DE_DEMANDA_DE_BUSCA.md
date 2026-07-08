# Inteligência de Demanda de Busca — Google Search + YouTube Search

## 1. Objetivo do módulo

Este documento define a proposta conceitual para incluir uma nova camada de inteligência no projeto **Social Media Analytics Automotivo**: a camada de **Inteligência de Demanda de Busca**.

A ideia central não é apenas coletar palavras-chave do Google Trends, mas entender como os sinais de busca podem ser conectados com o restante do projeto para gerar:

- antecipação de tendências automotivas;
- identificação de temas emergentes;
- leitura de intenção do consumidor;
- descoberta de oportunidades editoriais para vídeo;
- análise de saturação de conteúdo;
- inteligência regional de interesse;
- avaliação de timing dos creators;
- suporte à criação de conteúdo e análises de mercado.

O Google Trends deve ser tratado como uma camada de **demanda do mercado**, enquanto os dados do YouTube já coletados pelo projeto representam a camada de **oferta de conteúdo** e **validação social**.

---

## 2. Papel estratégico do Google Trends no projeto

Hoje o projeto olha principalmente para:

1. creators monitorados;
2. vídeos publicados;
3. métricas de performance;
4. crescimento de views, likes e comentários;
5. classificação de vídeos por nicho, subnicho e tipo;
6. identificação de padrões de performance.

Essas informações mostram o que já foi publicado e como o público reagiu.

A camada de Google Trends adiciona uma etapa anterior:

> O que o público está começando a procurar antes dos creators transformarem isso em conteúdo?

Essa diferença é importante porque busca é um sinal de intenção. Antes de uma pessoa comprar, comparar, reclamar, pesquisar preço ou assistir a um vídeo, normalmente ela começa fazendo uma busca.

Portanto, o Google Trends pode funcionar como um sensor inicial de mercado.

---

## 3. Três camadas principais de inteligência

A proposta é organizar o sistema em três grandes camadas:

```text
1. Demanda de busca
   O que as pessoas estão procurando?

2. Oferta de conteúdo
   O que os creators estão publicando?

3. Performance social
   O que está performando melhor?
```

Hoje o projeto já atua fortemente nas camadas 2 e 3.

Com Google Trends, o projeto passa a atuar também na camada 1.

Isso permite análises mais completas, como:

```text
busca do público → conteúdo publicado → performance real
```

---

## 4. Google Search geral vs YouTube Search

A proposta deve considerar duas fontes diferentes dentro do universo de busca:

```text
Google Search geral = intenção ampla de mercado
YouTube Search = intenção de consumo de vídeo
```

As duas são importantes, mas respondem perguntas diferentes.

---

## 5. Google Search geral como radar de mercado

O Google Search geral ajuda a responder:

> O que o consumidor está tentando entender?

Exemplos de buscas automotivas relevantes:

```text
carro híbrido vale a pena
BYD Dolphin problema
IPVA carro elétrico
seguro carro elétrico
financiamento carro usado
motor 3 cilindros é bom
câmbio CVT problema
carro elétrico usado bateria
Jeep Compass problema crônico
Corolla Cross consumo
```

Essas buscas podem indicar:

- intenção de compra;
- preocupação com preço;
- medo de problema mecânico;
- comparação entre modelos;
- interesse por lançamento;
- dúvida sobre manutenção;
- preocupação com custo de posse;
- percepção negativa sobre marca ou tecnologia;
- demanda regional por determinado tema.

O Google Search geral é, portanto, o melhor sensor para entender a demanda ampla do mercado automotivo.

---

## 6. YouTube Search como radar de pauta em vídeo

O YouTube Search ajuda a responder:

> O que as pessoas querem assistir?

Exemplos de buscas com intenção mais clara de vídeo:

```text
BYD Dolphin review
Corolla Cross vs Compass
melhores SUVs usados
carro elétrico vale a pena
teste de consumo Onix turbo
motor 3 cilindros problemas
carro híbrido usado vale a pena
```

Essas buscas podem indicar:

- desejo de assistir review;
- intenção de comparar modelos;
- busca por opinião de dono;
- procura por teste prático;
- necessidade de explicação visual;
- interesse por vídeos educativos;
- potencial de pauta para criadores.

O YouTube Search é, portanto, o melhor sensor para identificar demanda de conteúdo em vídeo.

---

## 7. Funil de sinal de mercado

A camada de busca permite enxergar um funil de sinal antes do conteúdo performar.

```text
1. Google Search
   A dúvida nasce.

2. YouTube Search
   A dúvida vira intenção de assistir.

3. Publicação de vídeos
   Creators começam a responder.

4. Performance dos vídeos
   O mercado valida ou rejeita o tema.

5. Comentários e engajamento
   O público aprofunda a dor.
```

Esse funil é muito importante para antecipação de mercado.

Exemplo:

```text
1. Pessoas começam a buscar no Google:
   "carro elétrico usado bateria"

2. Depois aparecem buscas no YouTube:
   "carro elétrico usado vale a pena"

3. Depois creators publicam:
   "Comprei um elétrico usado: valeu a pena?"

4. Depois os vídeos começam a performar.

5. Depois os comentários revelam novas dúvidas sobre bateria, seguro, autonomia e manutenção.
```

Nesse cenário, quem captura o estágio 1 consegue antecipar a pauta antes da saturação.

---

## 8. Benefícios principais para o projeto

### 8.1. Antecipação de temas antes de virarem tendência em vídeos

O principal ganho é detectar temas antes que eles apareçam com força no YouTube.

Exemplo:

```text
Google Trends mostra crescimento em:
- carro híbrido usado
- BYD usado
- bateria carro elétrico preço

Mas o banco de vídeos ainda tem poucos vídeos recentes sobre esses temas.
```

Interpretação:

```text
Existe demanda surgindo, mas a oferta de conteúdo ainda está baixa.
```

Isso gera uma oportunidade editorial e analítica.

No dashboard, poderia aparecer como:

```text
Tema emergente com baixa saturação de conteúdo
```

---

### 8.2. Separar tendência real de hype de creator

Nem todo vídeo que performa bem representa uma tendência real de mercado.

Às vezes o vídeo cresce porque:

- o creator é grande;
- o tema é polêmico;
- a thumbnail foi muito eficiente;
- o algoritmo distribuiu bem;
- o assunto tem apelo momentâneo.

Com Google Trends, é possível comparar a performance do vídeo com o interesse real de busca.

Exemplos:

```text
Tema A:
- muitos vídeos performando bem
- Google Search subindo
- YouTube Search subindo
= tendência real de mercado
```

```text
Tema B:
- vídeo performou bem
- Google Search estável
- YouTube Search estável
= provável efeito do creator, formato ou distribuição
```

```text
Tema C:
- Google Search subindo
- YouTube Search ainda baixo
- vídeos ainda fracos
= oportunidade antecipada
```

---

### 8.3. Entender intenção do consumidor

As palavras buscadas ajudam a entender a intenção por trás do interesse.

Exemplo com o tema **BYD Dolphin**:

```text
BYD Dolphin preço
BYD Dolphin problema
BYD Dolphin autonomia
BYD Dolphin usado
BYD Dolphin seguro
BYD Dolphin manutenção
```

Cada busca representa uma intenção diferente:

| Termo | Intenção provável |
|---|---|
| BYD Dolphin preço | compra / comparação |
| BYD Dolphin problema | risco / medo |
| BYD Dolphin autonomia | uso prático |
| BYD Dolphin usado | mercado secundário |
| BYD Dolphin seguro | custo de posse |
| BYD Dolphin manutenção | pós-venda |

Isso permite enriquecer a classificação dos vídeos.

Hoje um vídeo poderia ser classificado como:

```text
Nicho: elétricos
Subnicho: BYD
Tipo: review
```

Com a camada de busca, o vídeo também poderia receber:

```text
Intenção de mercado: custo de posse
Dor principal: autonomia / seguro / manutenção
Estágio do consumidor: consideração de compra
```

---

### 8.4. Criar mapa de demanda por subnicho automotivo

A camada de busca pode ajudar a organizar o mercado automotivo por blocos de demanda.

Exemplo:

```text
Elétricos
- BYD
- GWM
- Dolphin
- Ora 03
- autonomia
- bateria
- carregador
- seguro carro elétrico

Manutenção
- troca de óleo
- motor 3 cilindros
- câmbio automático
- correia dentada
- barulho suspensão
- motor turbo problema

Compra e mercado
- carro usado
- financiamento
- SUV compacto
- carro até 50 mil
- seguro auto
- IPVA

Performance
- turbo
- remap
- stage 2
- downpipe
- preparação aspirada
- escapamento esportivo
```

Isso transforma a taxonomia do projeto em uma taxonomia guiada também por demanda real de busca.

---

## 9. Matriz demanda x oferta

Um dos principais produtos analíticos dessa camada deve ser a matriz:

```text
Demanda de busca x Oferta de conteúdo
```

Essa matriz cruza:

- Google Search;
- YouTube Search;
- quantidade de vídeos publicados;
- performance dos vídeos;
- volume de creators falando do tema;
- crescimento de métricas.

---

### 9.1. Alta demanda + baixa oferta

```text
O público está procurando, mas poucos creators publicaram.
```

Nome sugerido no dashboard:

```text
Oportunidade emergente
```

Uso:

- pauta de vídeo;
- post LinkedIn;
- alerta para marcas;
- monitoramento de mercado;
- recomendação editorial.

Esse é o quadrante mais valioso para antecipação.

---

### 9.2. Alta demanda + alta oferta

```text
O público está procurando e muitos creators já estão falando.
```

Nome sugerido no dashboard:

```text
Tema quente / competitivo
```

Uso:

- exige ângulo diferente;
- bom para análises comparativas;
- precisa de dados próprios;
- pode indicar saturação parcial;
- pode ser relevante para campanhas de curto prazo.

---

### 9.3. Baixa demanda + alta oferta

```text
Creators estão falando mais do que o público está buscando.
```

Nome sugerido no dashboard:

```text
Ruído de conteúdo
```

Uso:

- evitar pauta genérica;
- analisar bolha de nicho;
- avaliar influência artificial;
- separar hype interno de demanda real.

---

### 9.4. Baixa demanda + baixa oferta

```text
Pouca busca e pouco conteúdo.
```

Nome sugerido no dashboard:

```text
Tema de baixa prioridade
```

Uso:

- monitorar sem priorizar;
- manter em backlog;
- usar apenas se houver interesse estratégico específico.

---

## 10. Comparação entre Google Search e YouTube Search

A comparação entre Google Search e YouTube Search pode gerar insights próprios.

---

### 10.1. Google Search subindo, YouTube Search ainda baixo

Interpretação:

```text
O público tem dúvida, mas ainda não transformou isso em intenção clara de assistir vídeo.
```

Insight:

```text
Oportunidade de antecipação editorial.
```

Exemplo:

```text
seguro carro elétrico
bateria carro elétrico usado
IPVA carro híbrido
```

---

### 10.2. Google Search alto e YouTube Search alto

Interpretação:

```text
Tema quente, com demanda ampla e demanda por vídeo.
```

Insight:

```text
Tema relevante, mas provavelmente competitivo.
```

Exemplo:

```text
BYD Dolphin vale a pena
Corolla Cross vs Compass
melhor SUV compacto
```

---

### 10.3. Google Search baixo e YouTube Search alto

Interpretação:

```text
Tema mais visual, emocional ou de entretenimento.
```

Insight:

```text
Pode performar bem em vídeo mesmo sem grande demanda racional no Google.
```

Exemplo:

```text
ronco motor AP turbo
arrancada Civic turbo
carro rebaixado
projeto turbo
```

---

### 10.4. Google Search alto, YouTube Search baixo e poucos vídeos

Interpretação:

```text
Existe demanda real, mas pouca tradução em conteúdo audiovisual.
```

Insight:

```text
Oportunidade de conversão para vídeo.
```

Esse pode ser um dos melhores sinais para criação de pauta.

---

## 11. Conexão com o restante do projeto

A camada de busca deve se conectar com os módulos já existentes do projeto.

---

### 11.1. Conexão com classificação de vídeo

Cada vídeo pode ser conectado a termos de busca.

Exemplo:

```text
Vídeo:
"BYD Dolphin Mini vale a pena depois de 6 meses?"

Termos conectados:
- BYD Dolphin Mini
- BYD Dolphin vale a pena
- carro elétrico usado
- BYD manutenção
- autonomia BYD
```

Isso cria a ponte:

```text
busca do público → conteúdo publicado → performance real
```

---

### 11.2. Conexão com performance dos vídeos

Depois que os termos são conectados aos vídeos, o projeto pode responder perguntas como:

```text
Quando um termo sobe no Google Trends, os vídeos sobre esse termo crescem depois de quantos dias?
```

Ou:

```text
Quais vídeos performaram melhor em temas que estavam crescendo em busca?
```

Ou:

```text
Quais temas performaram bem sem crescimento correspondente em busca?
```

---

### 11.3. Conexão com creators

A camada de busca permite classificar creators de acordo com o timing em relação às tendências.

#### Creator antecipador

Publica sobre temas antes do pico de busca.

```text
Fala de carro elétrico usado antes do termo crescer.
```

#### Creator reativo

Publica depois que o tema já está em alta.

```text
Só entra quando todo mundo já está falando.
```

#### Creator amplificador

Não chega primeiro, mas quando publica gera muito impacto.

```text
O tema já existia, mas o vídeo dele explode.
```

#### Creator desalinhado

Publica muito, mas sobre temas que não têm demanda crescente.

```text
Alta frequência, baixa aderência ao interesse de busca.
```

Isso muda a leitura sobre creators.

Não é apenas:

```text
Quem teve mais views?
```

Mas sim:

```text
Quem entende melhor o timing do mercado?
```

---

### 11.4. Conexão com entidades, marcas e modelos

No mercado automotivo, muitos sinais de busca giram em torno de:

- marcas;
- modelos;
- motores;
- tecnologias;
- problemas;
- lançamentos;
- preços;
- comparações.

Exemplo:

```text
Termo: BYD Dolphin Mini preço
Marca: BYD
Modelo: Dolphin Mini
Intenção: compra
Tema: preço
Nicho: elétricos
```

Outro exemplo:

```text
Termo: motor 3 cilindros problema
Entidade: motor 3 cilindros
Intenção: risco / manutenção
Tema: confiabilidade
Nicho: manutenção
```

Essa conexão permite criar um mapa de mercado muito mais rico.

---

## 12. Métricas conceituais sugeridas

A camada de busca pode gerar novas métricas analíticas.

| Métrica | Pergunta que responde |
|---|---|
| `trend_capture_delay` | Quanto tempo o YouTube demora para reagir a uma busca crescente? |
| `trend_alignment_score` | O vídeo está alinhado com uma demanda real? |
| `early_mover_score` | O creator falou do tema antes dos outros? |
| `topic_saturation_score` | O tema já está saturado de conteúdo? |
| `search_to_video_gap` | Existe busca alta, mas baixa oferta de vídeos? |
| `video_demand_fit` | O conteúdo publicado corresponde ao que o público procura? |
| `regional_interest_score` | Em quais regiões o tema tem maior força relativa? |
| `consumer_pain_score` | O termo indica dor, medo, problema ou objeção de compra? |

---

## 13. Tipos de inteligência gerados

### 13.1. Inteligência editorial

Pergunta principal:

```text
Quais pautas têm maior chance de performar?
```

Uso:

- sugestão de vídeos;
- pauta para LinkedIn;
- roteiro de conteúdo;
- análise de oportunidade.

---

### 13.2. Inteligência de mercado

Pergunta principal:

```text
Quais preocupações estão crescendo entre consumidores?
```

Uso:

- análise de marcas;
- leitura de percepção de mercado;
- identificação de dores emergentes;
- acompanhamento de tecnologias automotivas.

---

### 13.3. Inteligência regional

Pergunta principal:

```text
Quais temas automotivos são mais fortes por estado ou região?
```

Uso:

- segmentação regional;
- planejamento de conteúdo local;
- análise por praça;
- suporte a marketing regional.

---

### 13.4. Inteligência competitiva

Pergunta principal:

```text
Quais marcas, modelos ou tecnologias estão ganhando interesse?
```

Uso:

- monitoramento de marcas;
- comparação de modelos;
- análise de lançamentos;
- identificação de riscos de percepção.

---

### 13.5. Inteligência de timing

Pergunta principal:

```text
Quando um tema começa a crescer e quando os creators entram?
```

Uso:

- análise de antecipação;
- ranking de creators por timing;
- detecção de oportunidades antes da saturação.

---

### 13.6. Inteligência de saturação

Pergunta principal:

```text
O tema ainda tem espaço ou já está saturado de conteúdo?
```

Uso:

- priorização de pauta;
- escolha de ângulo;
- diferenciação editorial;
- análise de competição por atenção.

---

## 14. Exemplo prático de insight

Tema analisado:

```text
carro híbrido usado
```

Sinais encontrados:

```text
Google Search:
- crescimento forte nos últimos 30 dias

YouTube Search:
- crescimento moderado

YouTube publicado:
- poucos vídeos recentes

Métricas dos vídeos existentes:
- vídeos poucos, mas com crescimento acima da média
```

Interpretação:

```text
Demanda crescente + baixa oferta + validação inicial positiva
```

Insight gerado:

```text
Tema com alta oportunidade editorial:
"carro híbrido usado"
```

Possíveis ângulos:

```text
- Vale a pena comprar híbrido usado?
- Quanto custa a bateria de um híbrido usado?
- Corolla Hybrid usado vs Corolla flex
- Híbrido usado tem manutenção cara?
- O que olhar antes de comprar um híbrido usado?
```

---

## 15. Exemplo prático de leitura de dor

Tema analisado:

```text
motor 3 cilindros problema
```

Possíveis buscas no Google:

```text
motor 3 cilindros é ruim
motor 3 cilindros vibra
motor 3 cilindros problema crônico
motor 3 cilindros turbo dura quanto
```

Possíveis buscas no YouTube:

```text
motor 3 cilindros vale a pena
motor 3 cilindros problemas
motor 3 cilindros manutenção
```

Interpretação:

```text
Existe uma dor recorrente e racional no Google.
A demanda por vídeo existe, mas pode estar mal atendida.
```

Oportunidade:

```text
Vídeo educativo com dados, exemplos reais e explicação técnica acessível.
```

---

## 16. Dashboard sugerido

Tela sugerida:

```text
Radar de Tendências Automotivas
```

Blocos principais:

```text
1. Termos emergentes da semana
2. Temas com alta demanda e baixa oferta
3. Marcas/modelos em aceleração
4. Dores do consumidor em crescimento
5. Regiões com maior interesse relativo
6. Creators que capturaram tendências primeiro
7. Temas saturados
8. Sugestões de pauta para vídeo
9. Comparação Google Search vs YouTube Search
10. Mapa de intenção do consumidor
```

Exemplo de saída do dashboard:

```text
Radar de Tendências Automotivas — Brasil

Tema emergente:
"carro híbrido usado"

Sinal de busca:
Crescimento forte nos últimos 30 dias

Oferta no YouTube:
Baixa

Creators ativos no tema:
Poucos

Intenção dominante:
Compra / custo de manutenção

Sugestão:
Tema prioritário para vídeo educativo e análise de mercado
```

---

## 17. Papel da IA nessa camada

A IA pode ser usada para enriquecer os termos coletados.

Para cada termo, a IA pode classificar:

- nicho;
- subnicho;
- marca;
- modelo;
- tecnologia;
- intenção de busca;
- dor do consumidor;
- estágio da jornada;
- tipo de conteúdo recomendado;
- risco de ruído;
- relação com vídeos existentes.

Exemplo:

```text
Termo: BYD Dolphin seguro caro

Classificação:
- Nicho: elétricos
- Marca: BYD
- Modelo: Dolphin
- Intenção: custo de posse
- Dor: seguro / manutenção / viabilidade econômica
- Jornada: consideração de compra
- Conteúdo sugerido: análise educativa / comparativo de custo
```

---

## 18. Interpretação correta dos dados de Trends

O Google Trends não deve ser interpretado como volume absoluto de busca.

O dado representa interesse relativo dentro de um período, região e propriedade de busca.

Portanto, a leitura correta não é:

```text
São Paulo pesquisou mais em volume absoluto.
```

A leitura correta é:

```text
Esse termo tem maior relevância relativa em São Paulo do que em outras regiões.
```

Essa informação é suficiente para análise de tendência, priorização editorial e leitura de mercado, mas não deve ser usada como estimativa exata de volume.

---

## 19. Nomes possíveis para o módulo

Opções em inglês:

```text
Search Demand Intelligence
Market Demand Intelligence
Automotive Search Intelligence
Trend Demand Radar
```

Opções em português:

```text
Inteligência de Demanda de Busca
Inteligência de Demanda Automotiva
Radar de Demanda Automotiva
Radar de Tendências Automotivas
```

Nome recomendado:

```text
Inteligência de Demanda de Busca
```

Nome recomendado para dashboard:

```text
Radar de Tendências Automotivas
```

---

## 20. Recomendação estratégica

A recomendação é incluir Google Search geral e YouTube Search como fontes complementares.

Não escolher entre uma ou outra.

Usar as duas com papéis diferentes:

```text
Google Search = sensor de mercado
YouTube Search = sensor de pauta
YouTube Videos = sensor de oferta
YouTube Metrics = sensor de validação
```

A camada completa responderia:

```text
O que o consumidor está tentando entender?
O que ele quer assistir?
Quais temas ainda não foram bem explorados em vídeo?
Quais creators capturam melhor essas demandas?
Quais marcas/modelos estão gerando dúvida, medo ou intenção de compra?
Quais temas estão saturados?
Quais assuntos podem antecipar movimentos do mercado?
```

---

## 21. Como registrar no sistema operacional do projeto

Como esta proposta ainda é uma ideia estratégica, ela deve entrar inicialmente no arquivo:

```text
/docs/01_BACKLOG.md
```

Depois, se for priorizada para execução, deve ser movida para:

```text
/docs/02_ROADMAP.md
```

Quando houver decisão técnica sobre fonte, modelagem, frequência e arquitetura, registrar também em:

```text
/docs/05_DECISOES_TECNICAS.md
```

Antes de usar os dados para análises reais, criar validações em:

```text
/docs/03_DATA_QUALITY_CHECKS.md
```

---

## 22. Item sugerido para o backlog

```md
## Inteligência de Demanda de Busca

Adicionar uma camada de inteligência baseada em Google Search e YouTube Search para identificar demanda de mercado, intenção do consumidor, temas emergentes e oportunidades editoriais no setor automotivo.

Objetivo:
- conectar sinais de busca com vídeos publicados e performance social;
- antecipar tendências antes da saturação no YouTube;
- identificar temas com alta demanda e baixa oferta de conteúdo;
- classificar termos por nicho, subnicho, entidade, intenção e dor do consumidor;
- criar o dashboard Radar de Tendências Automotivas.

Fontes conceituais:
- Google Search geral: sensor de mercado;
- YouTube Search: sensor de pauta em vídeo;
- YouTube Data API: oferta de conteúdo;
- métricas dos vídeos: validação social.

Principais entregáveis futuros:
- matriz demanda x oferta;
- ranking de oportunidades editoriais;
- análise de saturação de temas;
- ranking de creators por timing de tendência;
- mapa regional de interesse automotivo;
- sugestões de pauta para vídeos e posts.
```

---

## 23. Commit sugerido

```bash
git commit -m "docs(backlog): adiciona inteligencia de demanda de busca"
```

---

## 24. Resumo final

A camada de Google Trends não deve ser tratada como uma simples lista de palavras-chave.

Ela deve ser tratada como uma camada estratégica de:

```text
demanda latente
intenção do consumidor
sinal precoce de mercado
mapa regional de interesse
detecção de oportunidades editoriais
análise de saturação de conteúdo
inteligência competitiva automotiva
```

A conexão com o projeto fica assim:

```text
Google Search
→ mostra o que o público começa a buscar

YouTube Search
→ mostra o que o público quer assistir

YouTube Data
→ mostra o que os creators estão publicando

Métricas dos vídeos
→ mostram o que performou

Classificação por IA
→ organiza tema, nicho, intenção e entidade

Analytics
→ transforma tudo em oportunidade, alerta e recomendação
```

Esse módulo pode se tornar uma das partes mais valiosas do projeto, porque conecta marketing, conteúdo, creator analytics e inteligência de mercado automotivo.
