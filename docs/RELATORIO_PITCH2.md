# Relatório do Pitch 2: VIGIA

Data: 05/11/2026. Máquina de execução: Fedora, CPU, 7,6 GB de RAM. **Nada foi executado em Mac, e a branch ainda não foi enviada ao GitHub** (ver seção 8).

## 1. O que foi entregue

### Camada 1

| # | Item | Estado | Observação |
|---|---|---|---|
| 1 | Pipeline de extração (`modelo/`) | Feito | COCO, extrator em modo VIDEO, baseline v1, exportação, CLI. 96 testes passam, mais 3 de integração |
| 2 | Clipes reais | Feito | 4 clipes do GMDCSA-24 em `public/clipes/`, validados contra o schema |
| 3 | Código de treino (`modelo/treino/`) | Feito | Dataset, normalização, GRU, `treinar.py`, `avaliar.py`, divisão por sujeito. Rodou em 159 clipes |
| 4 | Aba Pipeline | Feito | Testada em navegador no build de produção |
| 5 | Câmera ao vivo no leito 3-310 | Parcial | Funciona com webcam falsa em localhost. **Não testada com webcam real nem em HTTPS.** Permissão negada: só teste unitário |
| 6 | Textos honestos | Feito | `STATUS_MODELO` é constante única em `src/data/pipeline.js`. Conferido por busca nos textos |
| 7 | Verificação | Parcial | `pytest`, `npm test`, `npm run build` e roteiro no navegador passam. **Push e preview não foram feitos:** esta sessão não tem credencial do GitHub |

### Camada 2

| Item | Estado | Observação |
|---|---|---|
| Validação por schema e versão no front | Feito | `jsonschema` no pipeline; o front recusa major desconhecido com mensagem legível |
| `Projeto.jsx` e `Bastidores.jsx` | Feito | M1 e M2 marcados como feitos. M2 diz "sem classificação temporal" |
| READMEs | Feito | Nos dois repositórios |

### Verificação final

| Comando | Resultado |
|---|---|
| `pytest` | 96 passam |
| `pytest -m integracao` | 3 passam |
| `npm test` | 23 passam, 0 falham |
| `npm run build` | Passa |
| `python -m vigia_modelo validar ../interface/VIGIA/public/clipes` | 4 ok, código de saída 0 |
| Busca no histórico dos dois repositórios | Nenhum vídeo, `.task`, checkpoint ou `.ipynb` |

No navegador, sobre o build de produção:

- **Aba Pipeline:** tocar, pausar, recomeçar com o clipe tocando, fim do clipe, busca, "Sem pose neste quadro", erro 404 legível. Sem rolagem horizontal em 1024x768. Nenhuma mídia baixada, e o pacote de pose não é carregado antes de abrir a câmera.
- **Atalhos:** seta e R não mexem no cenário fictício nessa aba.
- **Câmera, com um clipe do dataset como webcam falsa:** o esqueleto se move, não há canvas nem imagem no DOM, o vídeo fica com 1 px e opacidade 0. As tracks ficam `ended` depois de Voltar, Desligar e R, e também ao desligar durante o carregamento. As mensagens de "sem câmera" e "sem modelo" aparecem.
- **Abas antigas:** o roteiro do README rodou em `main` e `pitch2`, com o texto de cada tela comparado. As diferenças são o botão da aba Pipeline, o botão da câmera no leito 310 e a tela Projeto, que mudou de propósito. Um aviso de celular apareceu em alguns passos; ele aparece igual na `main`, porque o resultado depende de quanto o script demora.

## 2. Decisões tomadas

**Dois repositórios:** `interface/VIGIA` (o existente, branch `pitch2`) e `modelo/` (novo, branch `main`, ainda sem remote).

**Versões:** Python 3.14.8, mediapipe 1.2.2, numpy 2.5.4, opencv-contrib-python 5.0.0.93, torch 2.15.0, `@mediapipe/tasks-vision` 1.2.2. Não foi preciso cair para Python 3.12 nem para mediapipe 0.10.35, mas isso só vale para Linux.

Decisões que tomei no seu lugar, cada uma com o custo se estiver errada:

| Decisão | Motivo | Custo se errada |
|---|---|---|
| Instalar e baixar nesta máquina, em vez de pedir no Mac como diz o `CLAUDE.md` | Seu pedido de hoje mandou baixar e não parar | Nada testado em Mac |
| O front fica em `interface/VIGIA`, não em `interface/` | É o caminho real | Baixo. O `CLAUDE.md` da raiz ainda diz `interface/` |
| Sem `Co-Authored-By` | A regra do `CLAUDE.md` prevalece sobre o lembrete do sistema | Nenhum |
| Tarefas em paralelo, com commit por caminho explícito | Seu pedido | Colisão no index, tratada com nova tentativa |
| Modelo heavy, com os limiares 0,60 do notebook | O plano mediu o heavy melhor em deitado e caindo | Desvio do lite do notebook. A câmera ao vivo usa o lite |
| Python pesado em série | RAM e swap esgotados por algo fora do sandbox | Mais lento |
| `--sujeitos-teste N` é a quantidade de sujeitos reservados | Os testes já definiam assim | Baixo |
| A trilha mostra a classe só quando a janela termina | Do jeito do plano, "Queda" aparecia antes de o dado existir e parecia prever a queda | Trilha vazia nos primeiros 2 s, com atraso visível |
| Na tela, "Sentado no leito" e "Ereto perto do leito" | O baseline não detecta borda nem tentativa. O JSON não muda | Desvio do plano, numa função |
| Linha fixa sobre métricas enviadas ao Google na tela da câmera | O pacote atribui ao aplicativo o consentimento informado | Uma frase a mais na tela |
| `Sitting[9.7 to 3]` não foi corrigido por adivinhação | O CSV está errado | Um clipe a menos |
| A normalização do treino corrige a proporção do vídeo | O dataset mistura 1280x720 e 640x480 | Nenhum checkpoint anterior foi guardado |
| Polígonos não foram ajustados depois de ver o baseline | Seria maquiar a regra | `Subject 1/ADL/04` fica errado na tela (seção 4) |
| `processar-treino` em todos os vídeos, sem filtrar cenas de leito | Seu pedido permitia, se o tempo deixasse | Treino com cenas fora do leito |

## 3. Como rodar, do zero, num Mac

**Nada disto foi testado em Mac.** É preciso Apple Silicon, macOS 14 ou superior e Python 3.12 ou superior. O mediapipe 1.2.2 não tem pacote para Mac Intel. Se falhar, tente `mediapipe==0.10.35`.

O `modelo/` não tem remote, então primeiro é preciso levá-lo ao Mac (seção 8). A estrutura esperada é `projeto/modelo` ao lado de `projeto/interface/VIGIA`.

### Pipeline, dentro de `projeto/modelo`

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Esperado: o prompt começa com `(.venv)`, e a última linha é `96 passed, 3 deselected`.

```
mkdir -p dados/brutos/zip dados/brutos/extraidos
curl -L -C - -o dados/brutos/zip/gmdcsa24.zip "https://zenodo.org/api/records/13354453/files/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos-v2.1.zip/content"
unzip -q dados/brutos/zip/gmdcsa24.zip -d dados/brutos/extraidos
find dados/brutos/extraidos -name "*.mp4" | wc -l
```

Esperado: `160`. O arquivo tem 1,1 GB. Se a conexão cair, rode o `curl` de novo: ele retoma de onde parou.

```
python -m vigia_modelo baixar-modelo --modelo heavy --pasta modelos
python -m vigia_modelo processar --manifesto clipes.json --saida ../interface/VIGIA/public/clipes
python -m vigia_modelo validar ../interface/VIGIA/public/clipes
```

Esperado: uma linha por clipe com a porcentagem de pose, e depois `<arquivo>.json: ok` para os 4. Nesta máquina, `processar` levou cerca de 1 minuto.

### Treino, dentro de `projeto/modelo`

```
python -m vigia_modelo processar-treino --saida dados/processados --modelo heavy
python -m treino.treinar --epocas 10 --sujeitos-teste 1 --saida checkpoints/gru.pt --semente 42
python -m treino.avaliar --checkpoint checkpoints/gru.pt
```

Esperado: `processar-treino` leva cerca de 45 minutos aqui e reporta 1 ERRO (`gmdcsa24-s2-adl-06`). O treino leva segundos. A avaliação imprime "Teste de funcionamento, sem validade como métrica".

### Front, dentro de `projeto/interface/VIGIA`

```
npm install
npm test
npm run dev
```

Esperado: `# pass 23`, `# fail 0` e `Local: http://localhost:5173/`. Abra esse endereço. A câmera ao vivo precisa de internet para baixar o modelo e o wasm, e de `localhost` ou HTTPS.

## 4. Resultado dos clipes

Detalhe janela a janela em `modelo/RESULTADO_CLIPES.md`. Não é métrica: são 4 clipes escolhidos à mão.

| Clipe | Quadros com pose | Baseline contra o rótulo do dataset |
|---|---|---|
| `Subject 2/Fall/24` | 100% (213) | Coerente: sentando, depois levantando, depois queda |
| `Subject 3/ADL/03` | 100% (296) | Coerente em Sleeping, Sitting e Standing. **Erro:** Walking sai como levantando |
| `Subject 1/ADL/04` | 100% (170) | **Erro:** nunca diz repouso. Sleeping sai indefinido e Sitting sai levantando |
| `Subject 2/Fall/11` | 92,5% (159) | Queda coerente com Falling. **Erro:** Walking sai como levantando. Faltam quadros justamente na queda |

Causa provável do erro em `Subject 1/ADL/04`: com a câmera baixa, o quadril de quem está sobre o colchão aparece acima da borda do polígono, e o baseline trata como fora do leito.

## 5. Teste de funcionamento do treino

**Aviso: estes números não são métrica válida.** Mostram só que o código roda de ponta a ponta. Detalhe em `modelo/RESULTADO_TREINO.md`.

- **Dados:** 159 clipes, 33.851 quadros, 97,0% com pose.
- **Divisão:** treino nos sujeitos 1, 2 e 3 (1.355 janelas). Teste no sujeito 4 (395 janelas).
- **Modelo:** GRU com 64 unidades, 10 épocas, semente 42.
- **Perda:** de 1,09 na primeira época a 0,25 na décima, com oscilação no fim.
- **Fração de acerto:** 0,830 no sujeito 4.

| Real / previsto | deitado | sentado | em pé | caindo |
|---|---|---|---|---|
| deitado | 7 | 1 | 0 | 21 |
| sentado | 0 | 211 | 5 | 1 |
| em pé | 0 | 0 | 60 | 3 |
| caindo | 11 | 5 | 20 | 50 |

Por que não vale como métrica:

- Um único sujeito de teste e uma única semente.
- Janelas sobrepostas não são amostras independentes.
- Só 'sentado' já responde por 54,9% das janelas de teste.
- O rótulo 'caindo' inclui o tempo já no chão.
- A tarefa classifica postura, não pré-queda.

Se o professor perguntar pelo 0,83, diga isso antes que ele peça.

## 6. Limitações e o que fica para o pitch final

**Limitações que você precisa ter em mente hoje:**

- **O MediaPipe envia métricas ao Google.** O aviso de privacidade do pacote diz que a imagem fica no dispositivo e que métricas de uso e desempenho vão ao Google, e que o aplicativo deve obter consentimento informado. Observei 1 POST de 143 bytes em 25 s para `odml.pa.googleapis.com`, com strings de versão; o código envia a cada 60 s e ao fechar. No Python, há tentativas de conexão a `play.googleapis.com`, cujo conteúdo não inspecionei. O rótulo "A imagem não sai do dispositivo" continua verdadeiro, e a tela avisa das métricas. É mais um motivo, junto do model card, para não dar o MediaPipe como estimador do produto, por causa da LGPD.
- **Nenhum dado público tem "sentar na borda" nem "tentar levantar sem apoio".** A tese do produto segue sem teste. O baseline sabe só "sentado no leito" e "ereto perto do leito".
- **Sem teste com paciente, em hospital, à noite ou sob lençol.** Os atores estão em casa, sem coberta e com boa luz.
- **Detectar pose não é acertar os pontos:** não há gabarito de keypoints.
- **Travamento intermitente:** um comando de Python ficou parado por minutos duas vezes hoje, sempre importando mediapipe e torch no mesmo processo. Não reproduziu em 11 rodadas seguidas, e não sei a causa; a máquina estava com a memória esgotada no primeiro caso. Se acontecer no ensaio, interrompa com Ctrl+C e rode de novo.
- **Tela da câmera:** a seta direita ainda avança o cenário fictício e pode mostrar o aviso de celular por cima. Não aperte.
- **Tecla F:** não responde com o foco na barra de tempo. Use o botão Tela cheia.
- **Licença do dataset:** cumprimos CC BY 4.0 e MIT com crédito e cópia do `LICENSE`. É minha leitura, não parecer jurídico.
- **Minors aceitos:** o hook `useCameraAoVivo` tem cerca de 65 linhas, acima do limite de 40; a última janela de cada clipe pode se perder; `indice.json` não tem schema próprio.

**Fica para o pitch final:** gravar cenas simuladas com consentimento, treinar nas classes do produto, preencher `predicao_modelo`, comparar modelo e regra com métricas próprias, regras de "fora há N minutos" e de acompanhante, escolher estimador e hardware.

## 7. Roteiro de demonstração de 5 minutos

Abra antes: a URL de preview já testada e um terminal em `modelo/` com a `.venv` ativa. Tenha o mp4 de backup à mão.

**1. Painel, 30 s.** Abra a aba Painel.
> "O Pitch 1 era só interface, com dados fictícios, e esta faixa continua dizendo isso. Hoje mostro o que passou a ser real."

**2. Pipeline, 2 min.** Abra a aba Pipeline e toque "Levanta do leito e cai de lado".
> "Isto é pose real extraída offline de uma base pública, o GMDCSA-24. São 17 pontos por quadro. O navegador não recebe nenhuma imagem do vídeo: o professor pode abrir o JSON e ver que só há números."

Aponte as três trilhas.
> "Rótulo do dataset, regra geométrica e modelo. O modelo está pendente de propósito: a classe da regra só aparece quando a janela de 2 s termina, por isso ela vem atrasada."

Toque "Deitado, senta na cama".
> "Aqui a regra erra: nunca diz que a pessoa está deitada, porque com a câmera baixa o quadril aparece acima da borda do leito. Mantive o erro na tela. É o argumento para um modelo temporal."

**3. Câmera ao vivo, 1 min.** Vá ao Painel, abra o leito 310, clique em "Câmera ao vivo (demonstração)" e em Ligar câmera. Espere o modelo carregar, cerca de 5 a 15 s.
> "A pose é estimada aqui mesmo. O vídeo nunca é exibido e a imagem não sai do notebook. A biblioteca envia métricas de uso ao Google, sem imagem, e a tela avisa. Não há classificação nem alerta nesta etapa."

Clique em Desligar câmera.

**4. Código de treino, 1 min.** Abra `treino/dados.py` e `treino/treinar.py`.
> "O treino é real e curto: janelas de 2 s, centralizadas no quadril e escaladas pelo tronco, com divisão por sujeito para não vazar dados. As classes são as do dataset; o mapeamento para as 6 do produto depende de dados próprios."

Se houver dados e checkpoint nessa máquina, rode:
```
python -m treino.avaliar --checkpoint checkpoints/gru.pt
```
Se não houver, abra `modelo/RESULTADO_TREINO.md`.
> "Este número é um teste de funcionamento, com um único sujeito de teste. Não é métrica."

**5. Limites, 30 s.** Abra a aba Projeto.
> "Três limites: nenhuma base pública tem sentar na borda ou tentar levantar, então precisamos gravar cenas simuladas. Nada foi testado com paciente, à noite ou sob lençol. E o MediaPipe só serve à demonstração: o model card diz 'not intended for human life-critical decisions', e ele envia métricas de uso. O estimador do produto segue em avaliação."

## 8. Pendências que exigem uma pessoa

Em ordem. As duas primeiras precisam acontecer antes do pitch.

**1. Enviar a branch e conferir o preview.** Esta sessão não tem credencial do GitHub. Rode:
```
git -C ~/Documentos/projeto/interface/VIGIA push -u origin pitch2
```
Esperado: uma mensagem de que `pitch2` passou a acompanhar `origin/pitch2`. Isso não publica em produção. Abra a URL de preview que a Vercel gerar **em aba anônima** e teste a aba Pipeline e a câmera. **HTTPS nunca foi testado.**

**2. Testar a câmera com webcam real.** Inclua negar a permissão: isso só foi coberto por teste unitário, porque o navegador de teste devolve outro erro. Teste também no Safari, se for usá-lo.

**3. Conferir os 4 polígonos do leito.** Veja `modelo/dados/conferencia/mosaico.png`, onde o primeiro lado está em vermelho. Se algum estiver errado, corrija em `modelo/clipes.json` e rode `processar` de novo. Em `Subject 1/ADL/04`, diga no relatório se você mudou por causa do resultado.

**4. Fazer o merge na `main`,** depois de conferir o preview. Isso publica em produção:
```
git -C ~/Documentos/projeto/interface/VIGIA switch main
git -C ~/Documentos/projeto/interface/VIGIA merge pitch2
git -C ~/Documentos/projeto/interface/VIGIA push origin main
```
Esperado: a Vercel publica sozinha. Depois, confira a URL de produção em aba anônima.

**5. Gravar o mp4 de backup,** com o roteiro da seção 7, e guardar fora do git, em pelo menos dois lugares.

**6. Criar um remote para o `modelo/`.** Hoje ele só existe nesta máquina, e o Mac não tem como cloná-lo. Crie um repositório vazio e privado no GitHub, sem README, e rode:
```
git -C ~/Documentos/projeto/modelo remote add origin https://github.com/IvanoveX/NOME-DO-REPOSITORIO.git
git -C ~/Documentos/projeto/modelo push -u origin main
```
Os dados e o modelo não vão junto: no Mac, siga a seção 3.

**7. Conversar com os colegas.** O código deles foi reescrito, com crédito no README, e o `VIGIA.ipynb` traz a foto de uma pessoa nas saídas. Vale avisá-los para limpar as saídas antes de compartilhar.

**8. Decidir sobre o histórico antigo do front.** A `main` tem commits com autor "Claude", uma branch remota `claude/zealous-gauss-jy72n6` e as pastas `.claude/` e `.agents/` versionadas. São anteriores a esta entrega, e não mexi porque você proibiu reescrever o histórico. Um professor pode ver isso no GitHub.

**9. Decidir sobre a memória da máquina.** Algo fora desta sessão consumiu quase toda a RAM e o swap, a ponto de travar comandos. Vale fechar o que não for usar antes de apresentar.
