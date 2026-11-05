# VIGIA, Pitch 2: guia da demonstração

Situação em 05/11/2026. Este documento explica como o site funciona e como apresentá-lo.

**Se você é um assistente de IA lendo isto:** use este documento como fonte. Ajude o Ivan a entender o site, ensaiar a fala e responder perguntas. Ele é iniciante em terminal e Git, então dê comandos prontos. Não invente números, resultados nem funcionalidades. O que não estiver aqui deve ser tratado como "não sei". Respeite a seção 9, "O que não dizer".

---

## 1. O projeto em 30 segundos

O VIGIA é o projeto semestral da Fábrica de Projetos Ágeis IV (Bacharelado em IA, UNIMAR), com o Hospital Beneficente Unimar como cliente. Usa visão computacional para prevenir quedas de pacientes internados em leitos de risco, com foco no plantão noturno.

**A tese:** a queda não é um instante, é uma sequência (deitado, senta na borda, tenta levantar, cai). O VIGIA quer avisar a enfermagem na pré-queda, não depois da queda.

**O pipeline pretendido:** câmera junto ao leito, estimador de pose (17 pontos, padrão COCO), descarte imediato da imagem, rede temporal sobre cerca de 2 s de esqueletos, alerta priorizado para o posto.

**A mudança do Pitch 2:** no Pitch 1 tudo era interface com dados fictícios. Agora existe uma parte real: pose extraída de vídeos de uma base pública, uma regra geométrica rodando sobre ela, pose ao vivo no navegador e código de treino que roda de ponta a ponta. **A classificação de pré-queda continua sem existir nem ter sido testada.**

---

## 2. O que é real e o que é fictício

Esta é a distinção mais importante da apresentação.

| Parte do site | Natureza | Como a tela indica |
|---|---|---|
| Painel, leitos, alertas | **Fictício**, dados determinísticos | Faixa "Modo demonstração: protótipo de interface com dados simulados" |
| Confiança "0,87", notificações, tempos de resposta | **Fictício** | Mesma faixa |
| Histórico | **Fictício**, só metadados | Mesma faixa |
| Bastidores ("Como este alerta foi gerado") | **Ilustrativo** | Etiqueta "valores ilustrativos" |
| Projeto | Texto sobre o projeto | Marcos M1 a M5, com "Agora: M3" |
| **Aba Pipeline** | **Real**: pose de 4 vídeos públicos e regra geométrica | Faixa própria: "esqueleto real extraído offline de vídeo de base pública" |
| **Câmera ao vivo** (leito 310) | **Real**: pose em tempo real no navegador, sem classificação | "Classificação de risco: não ativa nesta etapa" |
| Trilha "Modelo" no Pipeline | **Pendente de propósito** | Texto "pendente" |

---

## 3. Como abrir a demo

### Opção recomendada: rodar no notebook

É a opção testada e não depende da Vercel. Abra o PowerShell e cole o bloco inteiro:

```
cd "C:\Users\Ivan Del Roio\vigia-projeto\interface\VIGIA"
npm run build
npm run preview
```

Esperado: `built in ...` e depois `Local: http://localhost:4173/`. Abra esse endereço no Chrome. Deixe o terminal aberto durante a apresentação. Para encerrar, use `Ctrl+C`.

A câmera ao vivo precisa de internet, porque baixa o modelo de pose e o wasm na hora. Segundo o README, o resto funciona offline depois de carregado; isso não foi testado sem internet nesta máquina.

### Os links da Vercel

| Link | O que abre | Limite |
|---|---|---|
| https://vigia-99usnywm9-ivan-43d1.vercel.app | Pitch 2 (preview da branch `pitch2`) | **Só abre logado na conta da Vercel.** Quem não estiver logado cai no login |
| https://vigia-green-pi.vercel.app | **Pitch 1**, sem a aba Pipeline | É o público, mas segue a `main`, que não recebeu o Pitch 2 |

Para o professor abrir um link sozinho, há duas saídas:

- **Desligar a proteção do preview:** no painel da Vercel, em Settings, Deployment Protection.
- **Publicar em produção:** isso substitui o Pitch 1 no link público. Só o Ivan decide e executa:

```
cd "C:\Users\Ivan Del Roio\vigia-projeto\interface\VIGIA"
git switch main
git merge pitch2
git push origin main
git switch pitch2
```

---

## 4. O site, tela por tela

### Painel

Tela inicial: Torre 3, 3º andar, Clínica Médica, com "9 de 24 leitos monitorados". Tem os cartões dos leitos (sem nome de paciente), a fila de alertas à direita e, embaixo, a legenda com os três grupos de estado: Movimento, Contexto e Sensor. O relógio simulado começa em 03:40:00. O seletor no topo troca a torre e o posto.

### Detalhe do leito

Abre ao clicar num cartão. Mostra o esqueleto SVG (nunca imagem), o estado, a confiança fictícia e os botões "Estou indo", "Atendido", "Falso alarme" e "Pausar 15 min". Embaixo fica o elemento mais forte do protótipo: a **sequência do movimento** (Repouso, Sentando na borda, Tentando levantar, Queda), com a **Janela de prevenção** e o rótulo "Aqui começam os detectores de queda comuns" sob a Queda.

Só o leito **310** tem o botão **"Câmera ao vivo (demonstração)"**.

### Cenário fictício

Avança pelo botão "Próxima etapa" ou pela seta para a direita. A faixa sempre diz qual é o próximo passo.

Ordem completa: Reiniciar, Próxima etapa, abrir o leito 312, Próxima etapa, "Estou indo", "Atendido", **botão "← Painel"**, Próxima etapa, Histórico, clicar na linha do 312, Fechar, Projeto.

Ele mostra três coisas:

- O leito 312 sobe de "Sentando na borda" para "Tentando levantar", e o alerta aparece no "Celular do plantão".
- O atendimento acontece dentro da janela de prevenção.
- O leito 318, com acompanhante, é atenuado e só vira registro. Queda nunca é atenuada.

### Histórico

Tabela só com metadados, com filtros. Rodapé com "O que o VIGIA guarda" e "O que o VIGIA nunca guarda". Clicar numa linha abre os **Bastidores**, que explicam o pipeline em 5 passos com valores ilustrativos.

### Projeto

Por que é viável, escopo do semestre (entregamos e não entregamos), marcos com "Agora: M3" e a frase final.

### Pipeline (a parte real)

- **Esquerda:** os 4 clipes.
- **Centro:** o esqueleto real sobre o polígono do leito, com botões Tocar/Pausar e Recomeçar.
- **Direita:** origem e licença dos dados, e notas.
- **Embaixo:** três trilhas alinhadas no tempo, **Rótulo do dataset** (o que a base diz), **Baseline geométrico** (o que a regra diz) e **Modelo** (pendente), mais a barra de tempo.

Pontos em anel com linha tracejada são os de baixa confiança.

### Câmera ao vivo

Caminho: Painel, leito 310, "Câmera ao vivo (demonstração)", "Ligar câmera". A imagem nunca aparece, só o esqueleto. Em "Ligada", o `<video>` de captura fica com 1 px e opacidade 0, sem canvas nem `<img>`. A tela avisa que a biblioteca envia ao Google métricas de uso e desempenho, sem imagem.

### Atalhos

| Tecla | Ação | Observação |
|---|---|---|
| Seta direita | Próxima etapa | Não vale na aba Pipeline |
| R | Reiniciar (relógio volta a 03:40:00) | Não vale na aba Pipeline |
| F | Tela cheia | Não responde com o foco na barra de tempo; use o botão |
| Esc | Fecha os Bastidores | |
| F5 | Volta tudo ao início | |

### Armadilhas conhecidas

1. **A aba "Painel" não fecha um leito aberto.** Para sair do detalhe, use o botão **"← Painel"**.
2. **Em 1366x768, as trilhas do Pipeline ficam abaixo da dobra.** Depois de escolher o clipe, **role a página até o fim**: esqueleto, botões e as três trilhas ficam visíveis juntos. O zoom do navegador não resolve, porque o esqueleto cresce junto.
3. **Na tela da câmera, não aperte a seta para a direita.** Ela avança o cenário fictício e pode mostrar o aviso de celular por cima.
4. **O "Celular do plantão" cobre o canto inferior direito por 6 s**, inclusive o cartão "Queda". Espere sumir antes de apontar para ele.

---

## 5. Como funciona por dentro

**Dois repositórios:**

- **Interface** (`interface/VIGIA`, branch `pitch2`): React, Vite e Tailwind. Só front-end, sem backend. Lê arquivos JSON estáticos.
- **Modelo** (`modelo/`): Python, offline. Extrai pose, calcula o baseline, exporta os JSONs e contém o treino. Nenhum Python roda no site.

**O contrato entre os dois** é o JSON de cada clipe, definido em `modelo/schema/clipe.schema.json`. Ele guarda coordenadas e metadados, nenhuma imagem. O campo `predicao_modelo` está nulo em todos os clipes.

**Do vídeo à tela:**

1. Entra um vídeo da base pública GMDCSA-24 (160 vídeos, atores em casa).
2. O MediaPipe Pose Landmarker, modelo heavy, gera 33 pontos por quadro; o código reduz a 17 pontos no padrão COCO e descarta a imagem.
3. A regra geométrica avalia janelas de 2 s, com passo de 0,5 s.
4. Um JSON por clipe vai para `public/clipes/`, validado contra o schema.
5. O navegador só anima esses números.

**O baseline geométrico** (`vigia_modelo/baseline.py`) é regra, não aprendizado. Ele compara o tronco com o polígono do leito, marcado à mão em cada clipe:

| Classe no JSON | Nome na tela | Condição, em resumo |
|---|---|---|
| `queda` | Queda | No último quarto da janela: tronco a até 45° da borda do leito, quadril fora do leito e abaixo da borda |
| `repouso` | Deitado no leito | Tronco a até 35° da borda e quadril dentro do leito |
| `sentando` | Sentado no leito | Tronco a 55° ou mais, quadril dentro do leito e a até 0,8 tronco de altura |
| `levantando` | Ereto perto do leito | Tronco a 55° ou mais, com o quadril mais alto ou a até 1 tronco fora do leito |
| `fora` | Fora do leito | Tronco a 55° ou mais e a mais de 1 tronco do leito |
| `indefinido` | Indefinido | Menos de 50% dos quadros válidos, ou inclinação entre os limiares |

Regras de acompanhante e de "fora há N minutos" **não** estão implementadas nesta etapa.

**O treino** (`modelo/treino/`): janelas de 2 s, centralizadas no quadril e escaladas pelo tronco; rede GRU de uma camada com 64 unidades; divisão por sujeito, para não vazar dados entre treino e teste. Usa as classes do dataset (deitado, sentado, em pé, caindo), não as do produto. Existe um checkpoint de teste, `checkpoints/gru.pt`, que **não alimenta a interface**.

**A câmera ao vivo** roda no navegador com `@mediapipe/tasks-vision`, modelo lite. O wasm vem do jsDelivr e o modelo, do Google Storage. Só estima pose: não classifica nem dispara alerta.

**Sobre os colegas:** o notebook do grupo deu o mapeamento de 33 para 17 pontos e os limiares de confiança do detector; o código foi reescrito, com crédito no README.

---

## 6. O que cada clipe mostra

Não é métrica: são 4 clipes escolhidos à mão. Os polígonos e limiares não foram ajustados depois de ver o resultado.

| Clipe na tela | Rótulo do dataset | Baseline na tela | Leitura | Com pose |
|---|---|---|---|---|
| **Levanta do leito e cai de lado** (`Subject 2/Fall/24`) | Sitting, Standing, Falling (SW) | Sentado no leito, Ereto perto do leito, Queda | **Coerente.** Melhor clipe para abrir | 100% |
| **Levanta da cama e anda** (`Subject 3/ADL/03`) | Sleeping, Sitting, Standing, Walking | Deitado, Indefinido, Sentado, Ereto perto do leito | Coerente, com **erro**: andar sai como "Ereto perto do leito" | 100% |
| **Deitado, senta na cama** (`Subject 1/ADL/04`) | Sleeping, Sitting | Indefinido, Ereto perto do leito | **A regra erra.** Nunca diz deitado. Melhor clipe para o argumento | 100% |
| **Cai da cama para o chão** (`Subject 2/Fall/11`) | Walking, Falling (BW | Ereto, Indefinido, Deitado, Queda | Queda coerente. **Erro:** andar sai como "Ereto". Faltam quadros justamente na queda | 92,5% |

"Falling (BW" aparece sem fechar o parêntese porque o texto está assim no CSV do dataset.

**Causa provável do erro no "Deitado, senta na cama":** com a câmera baixa, o quadril de quem está sobre o colchão aparece acima da borda do polígono, e a regra entende como fora do leito.

---

## 7. Roteiro de 5 minutos

**Antes:** site aberto na aba Painel, em tela cheia. Terminal aberto, sem nada digitado, para a etapa 4. Se houver um colega navegando, ele clica e o Ivan fala.

### 1. Painel, 30 s

Mostre o Painel e aponte a faixa do topo.

> "O Pitch 1 era só interface, com dados fictícios, e esta faixa continua dizendo isso. Hoje mostro o que passou a ser real."

### 2. Pipeline, 2 min

Abra a aba **Pipeline**. Com "Levanta do leito e cai de lado" selecionado, **role a página até o fim** e clique em **Tocar**.

> "Isto é pose real extraída offline de uma base pública, o GMDCSA-24. São 17 pontos por quadro. O navegador não recebe nenhuma imagem do vídeo: quem quiser pode abrir o JSON e ver que só há números."

Aponte as três trilhas.

> "Rótulo do dataset, regra geométrica e modelo. O modelo está pendente de propósito. A classe da regra só vale quando a janela de 2 s termina, por isso ela vem atrasada em relação ao rótulo."

Clique em **"Deitado, senta na cama"**, role até o fim se preciso e clique em **Tocar**.

> "Aqui a regra erra: nunca diz que a pessoa está deitada, porque com a câmera baixa o quadril aparece acima da borda do leito. Mantive o erro na tela. É o argumento para um modelo temporal."

### 3. Câmera ao vivo, 1 min

Vá ao **Painel**, abra o leito **310**, clique em **"Câmera ao vivo (demonstração)"** e em **"Ligar câmera"**. Espere o modelo carregar. Afaste-se para o corpo caber no quadro.

> "A pose é estimada aqui mesmo. O vídeo nunca é exibido e a imagem não sai do notebook. A biblioteca envia métricas de uso ao Google, sem imagem, e a tela avisa. Não há classificação nem alerta nesta etapa."

Clique em **"Desligar câmera"**.

### 4. Código de treino, 1 min

Abra `treino/dados.py` e `treino/treinar.py` no editor.

> "O treino é real e curto: janelas de 2 s, centralizadas no quadril e escaladas pelo tronco, com divisão por sujeito para não vazar dados. As classes são as do dataset; o mapeamento para as 6 do produto depende de dados próprios."

Rode a avaliação no terminal:

```
cd "C:\Users\Ivan Del Roio\vigia-projeto\modelo"
.\.venv\Scripts\python.exe -m treino.avaliar --checkpoint checkpoints\gru.pt
```

Esperado: "Teste de funcionamento, sem validade como métrica", a matriz e `fração de acerto: 0.830`.

> "Este número é um teste de funcionamento, com um único sujeito de teste. Não é métrica."

### 5. Limites, 30 s

Abra a aba **Projeto**.

> "Três limites: nenhuma base pública tem sentar na borda ou tentar levantar, então precisamos gravar cenas simuladas. Nada foi testado com paciente, à noite ou sob lençol. E o MediaPipe só serve à demonstração: o model card diz 'not intended for human life-critical decisions', e ele envia métricas de uso. O estimador do produto segue em avaliação."

### Se sobrar tempo ou pedirem o protótipo

Rode o cenário da seção 4. Antes, deixe claro que os dados são fictícios.

### Se a câmera falhar ao vivo

Não insista. Diga: "A câmera depende de internet para baixar o modelo; o que importa desta parte já está no Pipeline." E siga para a etapa 4.

---

## 8. Perguntas difíceis

**"O que aqui é IA de verdade?"**
O estimador de pose é um modelo pronto, usado na demonstração. A regra do baseline não é IA. A rede temporal existe só como código e teste de funcionamento, e não aparece na tela.

**"Por que o Modelo está pendente, se vocês treinaram uma rede?"**
A rede de teste foi treinada com as classes de postura do dataset, não com as classes do produto. Serviu para provar que o código roda. Pôr isso na tela daria a impressão de que o modelo do produto existe.

**"Vocês têm 83% de acerto?"**
Não. O 0,830 vem de um único sujeito de teste e uma única semente, com janelas sobrepostas, que não são independentes. Só "sentado" já é 54,9% das janelas de teste. Só 50 de 86 janelas de "caindo" acertam, e 21 de 29 de "deitado" saem como "caindo". É uma tarefa de postura, não de pré-queda.

**"E esse 0,87 no leito 312?"**
É dado fictício do cenário, como diz a faixa. Não é saída de modelo nenhum.

**"A legenda diz 'reconhecido pelo modelo'. Qual modelo?"**
Essa legenda é do protótipo e descreve o produto pretendido. As telas com ela estão rotuladas como dados simulados. O que é real hoje está na aba Pipeline.

**"O bloco 'Queda' aparece antes do cursor chegar. Isso é previsão?"**
Não. O clipe foi processado offline, então a trilha inteira já vem desenhada, e o cursor só mostra o momento atual. Cada classe começa no fim da sua janela de 2 s. A regra classifica a janela que já passou; não prevê nada, e o VIGIA não faz contagem regressiva até a queda.

**"Isso detecta pré-queda?"**
Ainda não, e a tese segue sem teste. Nenhum dado público tem "sentar na borda" nem "tentar levantar sem apoio". A regra só sabe "sentado no leito" e "ereto perto do leito".

**"Por que a regra erra?"**
Depende muito do ângulo da câmera e do polígono marcado à mão. A correção honesta é repensar a geometria em câmera baixa, não ajustar o clipe até acertar. Andar perto do leito também sai como "Ereto", porque a pessoa continua a menos de 1 tronco dele.

**"Os pontos estão certos?"**
Não sabemos com precisão. Detectar pose não é acertar os pontos, porque não há gabarito de keypoints.

**"E a privacidade? LGPD?"**
Nos clipes, os vídeos já são públicos e só coordenadas saem deles. Na webcam, a imagem fica no dispositivo, mas a biblioteca envia ao Google métricas de uso e desempenho, sem imagem. Foi observado 1 POST de 143 bytes em 25 s para `odml.pa.googleapis.com`; o código envia a cada 60 s e ao fechar. No Python, houve tentativas de conexão a `play.googleapis.com`, com conteúdo não inspecionado. É um ponto a resolver antes de considerar o MediaPipe no produto.

**"Por que MediaPipe?"**
Serviu à demonstração: heavy no processamento offline, lite na câmera ao vivo. Ele não foi escolhido como estimador do produto, que segue em avaliação.

**"Como evitaram vazamento de dados no treino?"**
Divisão por sujeito: treino nos sujeitos 1, 2 e 3, teste no sujeito 4, com a interseção conferida no código. Um clipe (`Subject 2/ADL/06`) ficou de fora porque o CSV tem um intervalo inválido, que não foi corrigido por adivinhação.

**"E a licença dos dados?"**
GMDCSA-24, CC BY 4.0, com citação na tela e no JSON. O pacote no GitHub traz também uma licença MIT, copiada em `LICENSE-GMDCSA24`. É uma leitura do grupo, não parecer jurídico.

**"Próximos passos?"**
Gravar cenas simuladas com consentimento, treinar nas classes do produto, preencher `predicao_modelo`, comparar modelo e regra com métricas próprias, implementar as regras de acompanhante e de "fora há N minutos", e escolher estimador e hardware.

---

## 9. O que não dizer

- Que o VIGIA **detecta ou previne quedas** hoje. É o objetivo, não um resultado.
- Que o modelo **acerta 83%**, ou qualquer número como desempenho.
- Que o **MediaPipe foi escolhido** como estimador do produto.
- Que **nenhum dado sai do notebook**. A imagem não sai; as métricas de uso vão ao Google.
- Que foi **testado em hospital**, com paciente, à noite ou sob lençol.
- Que o **0,87** ou qualquer valor das telas fictícias veio de um modelo.
- Que a regra geométrica é o modelo.

Não projete `modelo/dados/conferencia/` nem o `VIGIA.ipynb`: têm imagens de pessoas. O notebook traz uma foto nas saídas e nunca vai para o git.

---

## 10. Checklist antes de apresentar

**Precisa ser feito por uma pessoa, porque ainda não foi testado:**

- [ ] **Câmera com webcam real.** Até agora só rodou com webcam falsa. Permita o acesso quando o navegador perguntar e veja o esqueleto seguir o corpo.
- [ ] **Permissão negada,** ao menos uma vez, para ver a mensagem.
- [ ] **Projetor real:** legibilidade e resolução.
- [ ] **Internet na sala,** para a câmera.
- [ ] **Polígonos dos 4 clipes:** abra `modelo/dados/conferencia/mosaico.png`, onde o primeiro lado está em vermelho. Não projete esse arquivo.
- [ ] **Ensaio completo** do roteiro, cronometrado.
- [ ] **Vídeo de backup:** grave a tela com `Win+Alt+R` durante o ensaio e guarde fora do git.

**Na hora:**

- [ ] Rodar o bloco da seção 3 e abrir `http://localhost:4173/`.
- [ ] Apertar F5 para partir do estado inicial, e usar Tela cheia.
- [ ] Fechar o que não for usar e silenciar notificações do Windows.

---

## 11. O que foi verificado

**Nesta máquina (Windows 11, Python 3.14.6, Node 24), em 05/11/2026:**

| Verificação | Resultado |
|---|---|
| `pytest` | 96 passam, 3 ficam de fora por padrão |
| `pytest -m integracao` (MediaPipe real) | 3 passam |
| `npm test` | 23 passam |
| `npm run build` | Passa |
| Validação dos 4 JSONs contra o schema | 4 ok |
| Reprocessar os 4 clipes em pasta temporária | Funciona. 3 idênticos aos publicados; 1 difere minimamente (cerca de 0,0001 nas coordenadas) |
| `treino.avaliar` com o checkpoint | 0,830, igual ao `RESULTADO_TREINO.md` |
| Roteiro completo em Chrome automatizado, build de produção, em 1366x768 e 1024x768 | Sem erro no console e sem rolagem horizontal |
| Câmera com webcam falsa (clipe do dataset), em `localhost` | Esqueleto desenhado; carregou em cerca de 5 a 6 s; stream solto ao desligar |

**Não verificado:**

- Webcam real e permissão negada.
- O preview em HTTPS: a proteção da Vercel impediu o teste automatizado.
- Funcionamento sem internet e projetor real.
- `treino.treinar` e `processar-treino` nesta máquina.
- Mac: nada foi executado nele.

---

## 12. Repositórios e comandos

| O quê | Onde |
|---|---|
| Interface | https://github.com/IvanoveX/VIGIA/tree/pitch2 (repositório **público**) |
| Modelo | https://github.com/IvanoveX/vigia-modelo (**privado**) |
| Pasta local | `C:\Users\Ivan Del Roio\vigia-projeto` |

Rodar os testes do modelo:

```
cd "C:\Users\Ivan Del Roio\vigia-projeto\modelo"
.\.venv\Scripts\python.exe -m pytest
```

Rodar o site em modo de desenvolvimento:

```
cd "C:\Users\Ivan Del Roio\vigia-projeto\interface\VIGIA"
npm run dev
```

Esperado: `Local: http://localhost:5173/`.

**Documentos de referência:** `modelo/docs/RELATORIO_PITCH2.md`, `modelo/RESULTADO_CLIPES.md`, `modelo/RESULTADO_TREINO.md` e `interface/VIGIA/SPEC.md` (seção 14).
