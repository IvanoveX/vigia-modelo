# Pitch 2: entrega mínima

Fonte da verdade: o pedido do Ivan de 05/11/2026, que passa por cima de `PLANO_PITCH2.md` em conflito. Dois repositórios: `modelo/` (novo) e `interface/VIGIA/` (branch `pitch2`).

## Global Constraints

- Funções de até ~40 linhas, com uma responsabilidade. Comentários curtos, só para o porquê. Nenhum emoji em código, logs, commits ou interface. Legível por dev pleno, sem abstração prematura.
- Nenhum dado inventado com random fora de fixture de teste rotulada. Nenhuma métrica de desempenho na interface.
- Textos de interface em pt-BR.
- Commits em Conventional Commits, em português, pequenos, sem emoji, SEM `Co-Authored-By` e sem qualquer menção a Claude ou IA. Não alterar `git config`. Faça `git add` e commit só dos arquivos da sua tarefa, por caminho explícito (`git commit <caminhos> -m ...`), porque outra tarefa pode estar rodando no mesmo repositório.
- Nunca versionar vídeos, `.task`, checkpoints, datasets, `.ipynb`.
- Nunca abrir `VIGIA.ipynb`: contém a foto de uma pessoa.
- Nenhum texto pode dizer que o MediaPipe foi escolhido como estimador do produto.
- Contrato: `modelo/schema/clipe.schema.json`.
- Python: sempre `.venv/bin/python` de `modelo/`. Rede em comando Bash: declare os hosts em `allowed_domains`.
- Sem push. O controlador faz o push da branch.

## Task 1: Mapeamento COCO, modelo de pose e extrator

Repositório `modelo/`. Criar `vigia_modelo/__init__.py`, `vigia_modelo/coco.py`, `vigia_modelo/modelo_pose.py`, `vigia_modelo/extrator.py`, `tests/test_coco.py`, `tests/test_extrator.py`.

`coco.py`: `INDICES_MEDIAPIPE = [0,2,5,7,8,11,12,13,14,15,16,23,24,25,26,27,28]`, `NOMES_COCO` (nomes em inglês do schema, nessa ordem) e `selecionar_coco(landmarks) -> list[list[float]]`, que devolve `[x, y, conf]` com x e y arredondados em 4 casas e `conf` (o `visibility` do MediaPipe) em 2 casas, limitando `conf` a 0-1. Docstring curta creditando o notebook dos colegas como origem do mapeamento.

`modelo_pose.py`: `baixar_modelo(nome: str, pasta: Path) -> Path`. URL `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_<nome>/float16/1/pose_landmarker_<nome>.task`. Verifica SHA-256 e recusa arquivo divergente (apaga e levanta `ValueError`); se o arquivo já existe e confere, não baixa de novo.
- lite `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`
- full `5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`
- heavy `64437af838a65d18e5ba7a0d39b465540069bc8aae8308de3e318aad31fcbc7b`

`extrator.py`: `timestamps_ms(n: int, fps: float) -> list[int]`, estritamente crescente, calculada por índice do quadro / fps (nunca `CAP_PROP_POS_MSEC`); `ValueError` para fps 0, negativo ou NaN. `extrair_clipe(caminho: Path, modelo: Path) -> dict` devolve `{"video": {...}, "quadros": [{"t": segundos com 4 casas, "pontos": lista ou None}]}` na forma do schema. Detector novo por clipe, `RunningMode.VIDEO`, `num_poses=1`, `min_pose_detection_confidence=0.60`, `min_pose_presence_confidence=0.60`, `min_tracking_confidence=0.60` (configuração do notebook dos colegas), `output_segmentation_masks=False`. Converter BGR para RGB. Liberar `VideoCapture` e fechar o detector também em erro. `FileNotFoundError` com caminho inexistente. A imagem nunca é salva nem devolvida.

Testes obrigatórios: ordem do mapeamento COCO (33 landmarks falsos com x = índice devolvem os índices da lista, nessa ordem), arredondamento, timestamps estritamente crescentes para fps 29.84, 15.02 e 30 por 1.000 quadros, fps inválido, arquivo inexistente. Teste `integracao` gerando por OpenCV, em `tmp_path`, um vídeo sem pessoa com 10 quadros: 10 quadros, todos `pontos: null`, `t` crescente. Baixe o heavy em `modelos/` para rodá-lo (host `storage.googleapis.com`).

## Task 2: Baseline geométrico v1

Repositório `modelo/`. Criar `vigia_modelo/baseline.py`, `tests/test_baseline.py`. Função pura, sem MediaPipe. Constantes de limiar no topo do arquivo. Não ajustar limiares olhando clipes.

Interfaces: `features_do_quadro(pontos, poligono, largura, altura) -> dict | None`, `classificar_janela(features: dict) -> str`, `gerar_janelas(quadros, poligono, largura, altura) -> list[dict]`. Índices COCO: ombros 5 e 6, quadris 11 e 12.

Features por quadro, em pixels (corrige o aspecto). Quadro válido se ombros e quadris têm `conf` >= 0,5; senão `None`.
- `inclinacao_graus`: ângulo entre o tronco (meio dos ombros até meio dos quadris) e o primeiro lado do polígono do leito, dobrado em 0-90. 0 é deitado, 90 é ereto.
- `altura_quadril`: distância com sinal do meio dos quadris à reta do primeiro lado, em comprimentos de tronco. Positivo é acima (menor y na imagem).
- `dentro_leito`: meio dos quadris dentro do polígono.
- `distancia_leito`: distância do meio dos quadris ao polígono, em comprimentos de tronco; 0 se dentro.
- `vel_max`: maior velocidade vertical para baixo do centroide (ombros e quadris), em comprimentos de tronco por segundo, com mediana móvel de 5 quadros. Exportada; não entra nas regras v1.

O comprimento de tronco é a mediana do clipe (entre quadros válidos).

Janelas de 2,0 s com passo de 0,5 s, a partir de t = 0. Usa a mediana da janela; para a regra de `queda`, usa a mediana do último quarto da janela. `frac_validos` é a fração de quadros válidos da janela. Clipe com menos de 2 s não gera janela. Tudo `null` não quebra: gera janelas `indefinido`, com features nulas, conforme o schema (`frac_validos` 0). Forma da janela: `{"t_ini", "t_fim", "classe", "features": {inclinacao_graus, altura_quadril, dentro_leito, distancia_leito, vel_max, frac_validos}}`, números arredondados a 2 casas.

Regras, na ordem:

| # | Condição | Classe |
|---|---|---|
| 1 | frac_validos < 0,5 | indefinido |
| 2 | inclinação <= 45, fora do leito, altura < 0 | queda |
| 3 | inclinação <= 35, dentro do leito | repouso |
| 4 | inclinação >= 55, dentro do leito, altura <= 0,8 | sentando |
| 5 | inclinação >= 55, dentro do leito, altura > 0,8 | levantando |
| 6 | inclinação >= 55, fora, distância <= 1,0 | levantando |
| 7 | inclinação >= 55, fora, distância > 1,0 | fora |
| 8 | caso contrário | indefinido |

Para `classificar_janela`, as features da regra 2 ficam em chaves `inclinacao_fim`, `altura_fim` e `dentro_leito_fim` (só internas: não exportar no JSON). Testes usam esqueletos construídos à mão (fixture rotulada): tronco paralelo dá ~0; perpendicular dá ~90; correção de aspecto em 1280x720; um teste com a classe exata para cada linha da tabela, incluindo os limites 35, 45, 55, 0,8 e 1,0; ombro com conf 0,4 dá `None`; 60% dos quadros nulos dá `indefinido`; clipe de 1,5 s dá `[]`; janelas com duração 2,0 e passo 0,5; tudo nulo não quebra.

## Task 3: Rótulos, exportação, validação e CLI

Repositório `modelo/`. Criar `vigia_modelo/rotulos.py`, `vigia_modelo/exportar.py`, `vigia_modelo/validar.py`, `vigia_modelo/__main__.py`, `clipes.json`, `tests/test_rotulos.py`, `tests/test_exportar.py`, `README.md` mínimo. Depende das Tasks 1 e 2 (`extrair_clipe`, `gerar_janelas`, `baixar_modelo`).

`rotulos.py`: lê os CSVs do dataset em `<raiz>/Subject N/{ADL,Fall}.csv`. A última coluna tem texto como `Sitting[3 to 7.4]; Sleeping[0 to 1]`, `Falling (SW)[1.4 to 6]`, `Sitting [0 to 7]`, `Sitting[ 0 to 8]`, com `;` final opcional. Linhas têm vírgulas na descrição, portanto extraia com regex sobre a linha. `rotulos_do_clipe(raiz, arquivo: "Subject 2/Fall/24.mp4") -> list[dict]`, ordenado por `t_ini`, com o rótulo original sem espaços nas pontas. `ValueError` claro se o arquivo não estiver no CSV.

`validar.py`: `validar_clipe(clipe: dict) -> list[str]` (jsonschema + `t` estritamente crescente + `total_quadros` igual a `len(quadros)` + `t_fim >= t_ini` nas janelas e rótulos), `validar_publicacao(clipe) -> list[str]` (além do anterior, exige leito e baseline não nulos e `predicao_modelo` nulo ou válido) e `validar_pasta(pasta) -> dict[str, list[str]]` (publicação; ignora `indice.json`).

`exportar.py`: constante `ORIGEM_GMDCSA` com `dataset: "GMDCSA-24"`, `licenca: "CC BY 4.0"`, `url: "https://zenodo.org/records/13354453"`, `citacao: "E. Alam, A. Sufian, P. Dutta, M. Leo, I. A. Hameed. GMDCSA24: A Dataset for Human Fall Detection in Videos. Data in Brief, 2024."`. `montar_clipe(entrada, extracao, rotulos, janelas, nome_modelo) -> dict` com `versao_schema "1.0.0"`, `gerado_por` (`estimador: "mediapipe-pose-landmarker"`, `versao` lida de `mediapipe.__version__`), `baseline.descricao "regra geométrica, não é o modelo"`, `baseline.versao "1"`, `predicao_modelo: None`. `escrever_clipe(clipe, pasta) -> Path` (JSON sem espaços, `ensure_ascii=False`). `escrever_indice(clipes, pasta) -> Path` grava `indice.json`: `{"versao_schema", "clipes": [{"id", "titulo", "duracao_s", "dataset"}]}`, ordenado como no manifesto.

`clipes.json` (manifesto): lista com `{"id_clipe": "gmdcsa24-s2-fall-24", "titulo": "...", "arquivo": "Subject 2/Fall/24.mp4", "leito": {"poligono": [...]}}`. Por ora, os 4 clipes (`Subject 2/Fall/24`, `Subject 3/ADL/03`, `Subject 1/ADL/04`, `Subject 2/Fall/11`) com polígono de placeholder de retângulo central: o controlador marca os reais olhando quadros na Task 4.

CLI (`python -m vigia_modelo`, argparse), funções curtas:
- `baixar-modelo --modelo heavy --pasta modelos`
- `processar --manifesto clipes.json --brutos <raiz> --saida ../interface/VIGIA/public/clipes --modelo heavy`: por clipe imprime porcentagem de quadros com pose e tamanho do arquivo; recusa gravar JSON inválido (erro claro, código de saída diferente de 0); grava o índice ao fim.
- `processar-treino --brutos <raiz> --saida dados/processados --modelo heavy [--sujeito N]`: percorre todos os mp4 listados nos CSVs (ou só os do sujeito N), `leito: null`, `baseline: null`, id `gmdcsa24-s<N>-<adl|fall>-<NN>`, pula os que já existem, usa `validar_clipe`. Um clipe que falhar é reportado e não interrompe os outros.
- `quadros --arquivo <mp4> --saida dados/conferencia --n 6`: grava PNGs locais de quadros uniformemente espaçados, para marcar o leito. Pasta ignorada pelo git.
- `validar <pasta>`: imprime por arquivo, sai com código diferente de 0 se houver erro.

Testes: parser cobre as variações acima; `montar_clipe` gera clipe aceito por `validar_clipe` com `predicao_modelo` `None`; JSON sem espaços; índice na ordem; JSON inválido (16 pontos, `t` repetido, x = 640, classe inexistente) é rejeitado; `validar_publicacao` rejeita `leito` nulo. Fixtures escritas à mão e rotuladas, com `origem.dataset = "exemplo-de-teste"`.

`README.md` mínimo: instalação, comandos, crédito aos colegas pelo notebook de origem do mapeamento 33->17 e da configuração do detector, crédito e licença do dataset (CC BY 4.0 no Zenodo, MIT no `LICENSE` do pacote: cumprir as duas), aviso de que o MediaPipe é usado na demonstração e que o estimador do produto segue em avaliação, trecho do model card ("not intended for human life-critical decisions").

## Task 4: Clipes reais

Executada pelo controlador: marcar os polígonos olhando PNGs, processar, validar, exportar para `interface/VIGIA/public/clipes/`, registrar `modelo/RESULTADO_CLIPES.md`, commitar JSONs em `interface` e manifesto em `modelo`.

## Task 5: Aba Pipeline

Repositório `interface/VIGIA`, branch `pitch2`. Criar `src/lib/clipes.js`, `src/lib/clipes.test.js`, `src/data/pipeline.js`, `src/components/EsqueletoReal.jsx`, `src/components/LinhaTempoClipe.jsx`, `src/components/Pipeline.jsx`. Modificar `src/App.jsx`, `src/components/Cabecalho.jsx`, `src/components/FaixaDemo.jsx`, `src/data/estados.js` só se precisar de `indefinido` fora da Legenda e da fila.

`src/data/pipeline.js`: textos da aba em um lugar só. `STATUS_MODELO = "Classificação temporal: código de treino pronto, aguardando dados rotulados próprios"` é a constante única de status do modelo. `TEXTO_DADOS = "17 pontos por quadro. O navegador não recebe nenhuma imagem do vídeo."`.

`src/lib/clipes.js`: `checarClipe(clipe) -> string | null` (major diferente de 1 ou pontos diferentes de 17); `quadroNoTempo(quadros, t) -> number` (busca binária, último quadro com `q.t <= t`); `trilhas(clipe) -> { origem, baseline, modelo }`, com `modelo` igual a `{ pendente: true }` se `predicao_modelo` for nulo, senão as janelas; `carregarIndice()` e `carregarClipe(id)`: `fetch` em `/clipes/`, com erro legível em pt-BR se status diferente de 200 ou o corpo não for JSON (o servidor de desenvolvimento devolve `index.html` em caminho inexistente). Testes com `node --test`: `quadroNoTempo` antes do início, entre quadros e depois do fim; `checarClipe` recusa `2.0.0`; `trilhas` com nulo dá pendente e preenchido devolve as janelas; `carregarClipe` com `fetch` falso devolvendo 404 e com HTML rejeita com mensagem em pt-BR. Fixture escrita à mão, com `origem.dataset = "exemplo-de-teste"`.

`EsqueletoReal({ pontos, largura, altura, poligono })`: componente novo; `Esqueleto.jsx` espera pixels e não trata ponto ausente. `viewBox` igual ao tamanho do vídeo, fundo neutro `var(--superficie-2)`, polígono do leito com `var(--sensor)`, sem deslocamento de lado, sem respiração nem balanço. Usa `ARESTAS` de `src/data/poses.js`. Confiança abaixo de 0,65: aresta tracejada e ponto vazado (`fill` igual a `var(--superficie)`), como em `Esqueleto.jsx`. `pontos` nulo não desenha esqueleto e mostra "Sem pose neste quadro". Ponto fora do quadro não estoura o layout (o SVG corta). Traços dimensionados em relação à largura do vídeo, para o mesmo aspecto em qualquer resolução.

`LinhaTempoClipe({ duracao, tempo, trilhas, onBuscar })`: três linhas rotuladas (Rótulo do dataset, Baseline geométrico, Modelo), com segmentos proporcionais ao tempo, cursor de tempo e `<input type="range">`. Modelo pendente mostra "pendente". Rótulos do dataset são originais em inglês. As classes do baseline usam nomes de `ESTADOS` em `src/data/estados.js` quando existem (`fora`: `rotuloCurto`, já que o clipe não mede minutos), e `indefinido` aparece como "Indefinido" sem entrar na Legenda nem na fila. Janelas do baseline se sobrepõem (passo de 0,5 s): cada trecho de 0,5 s mostra a janela mais recente que o cobre. Rótulos podem se sobrepor: mostre o último que começou.

`Pipeline.jsx`: lista de clipes, esqueleto, trilhas, Tocar/Pausar, Recomeçar, barra de tempo; `requestAnimationFrame` cancelado ao desmontar; ao chegar ao fim, pausa; pré-carrega todos os clipes ao abrir; estados de carregando, erro (legível, nunca branco) e vazio; crédito do dataset (nome, licença, citação, link, lidos do JSON); `TEXTO_DADOS`; `STATUS_MODELO`; a frase "Acompanhante presente e fora do leito por N minutos: regras ainda não implementadas nesta etapa."; uma linha dizendo que o baseline é regra geométrica, não o modelo. Nenhuma métrica de desempenho. Botões seguem o padrão de `DetalheLeito.jsx`: `inline-flex min-h-11 items-center justify-center gap-2 rounded px-3 font-bold transition-colors`, forte `bg-marca text-white hover:bg-marca/90`, secundário `border border-linha bg-superficie text-tinta hover:border-secundario`. Cartão `rounded border border-linha bg-superficie p-3`. Sem rolagem horizontal em 1024x768.

Integração: entrada `pipeline`/`Pipeline` em `ABAS` (`Cabecalho.jsx:10-14`), e nessa aba o cabeçalho esconde "Plantão noturno", relógio, torres e posto. `FaixaDemo` recebe a aba; em `pipeline` mostra "Demonstração do pipeline: esqueleto real extraído offline de vídeo de base pública" e só o botão Tela cheia. `App.jsx`: renderiza `<Pipeline />` dentro de um `memo` (o App re-renderiza a cada 200 ms), ignora seta direita e R nessa aba (F continua), e não mostra `CelularPlantao` nem Bastidores nessa aba. O reducer já aceita a aba em `ABA`. As outras abas ficam inalteradas.

Verificação: `npm test`, `npm run build`. Se ainda não houver JSONs reais em `public/clipes/`, confira com JSON temporário no `/tmp` da sessão, sem commitar. Navegador headless pronto em `SCRATCHPAD/navegador` (playwright), se existir: abra, toque, troque de aba, confira os atalhos.

## Task 6: Câmera ao vivo no leito 3-310

Repositório `interface/VIGIA`, branch `pitch2`. Dependência `@mediapipe/tasks-vision@1.2.2`, já instalada com versão exata pelo controlador. Criar `src/lib/poseAoVivo.js`, `src/lib/poseAoVivo.test.js`, `src/data/cameraAoVivo.js`, `src/components/CameraAoVivo.jsx`. Modificar `src/components/DetalheLeito.jsx`.

Em UM leito (`3-310`), no `DetalheLeito`, um botão "Câmera ao vivo (demonstração)", junto aos botões do detalhe, abre a tela (estado local: `useState` no `DetalheLeito`), com botão de voltar ao detalhe. Nenhum outro leito mostra o botão. Nada de novo no reducer. Nenhuma classificação e nenhum alerta disparado por ela.

`src/lib/poseAoVivo.js`: funções puras e testáveis, sem React. `INDICES_MEDIAPIPE` como no Python, `selecionarCoco(landmarks)` devolve `[[x, y, conf]...]` com 17 pontos, `conf` a partir de `visibility`, e `mensagemDeErroCamera(erro)` traduz `NotAllowedError`/`SecurityError` (permissão negada), `NotFoundError`/`OverconstrainedError` (nenhuma câmera), `NotReadableError` (câmera em uso) e qualquer outra coisa, em mensagens pt-BR. `criarDetector()` faz import dinâmico de `@mediapipe/tasks-vision` (para o pacote não pesar nas outras abas) e usa `FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.2.2/wasm")` e `PoseLandmarker.createFromOptions`, modelo `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`, `runningMode: "VIDEO"`, `numPoses: 1`, delegate `CPU` se `GPU` falhar. A falha ao carregar vira mensagem própria que cita a necessidade de internet para baixar o modelo e o wasm. A versão do wasm fica numa constante e tem de ser igual à do `package.json`: um teste confere isso.

`CameraAoVivo.jsx`: botões Ligar câmera e Desligar câmera. A câmera só liga com clique. O `<video>` de captura fica oculto: nunca é exibido (`hidden` não basta em alguns navegadores para decodificar quadros: use um elemento fora da tela com `muted`, `playsInline`, largura e altura 1 px, `opacity: 0`, `position: absolute`, `pointer-events: none`, e rótulo `aria-hidden`). Nunca copie quadro para canvas, nunca grave e nunca envie a imagem. Laço com `requestAnimationFrame` chamando `detectForVideo(video, performance.now())` só quando `currentTime` muda; timestamps estritamente crescentes. O esqueleto usa `EsqueletoReal` da Task 5, com `poligono` nulo e o aspecto real do vídeo; desenha sobre fundo neutro e não mostra imagem nenhuma. Estado de esqueleto em ref + `useState` apenas para os pontos. Ao desmontar ou desligar: cancelar o laço, parar todas as tracks, limpar `srcObject`, fechar o detector. Trocar de aba, voltar e R desligam a câmera (desmontagem). Um clique duplo ou desligar durante o carregamento não pode deixar a câmera ligada. Estados legíveis: carregando modelo, pedindo permissão, ligada, desligada, erro.

Rótulos fixos, em `src/data/cameraAoVivo.js`: "Pose estimada em tempo real neste notebook. A imagem não sai do dispositivo e não é exibida." e "Classificação de risco: não ativa nesta etapa". Mensagens para permissão negada, ausência de câmera e falha ao carregar o modelo.

Verificação: `npm test`, `npm run build`, e `grep` confirmando que o `<video>` só existe em `CameraAoVivo.jsx`. Depende de `EsqueletoReal.jsx`: se ainda não existir quando chegar nessa parte, aguarde a Task 5 (o controlador avisa). Não faça a verificação no navegador: o controlador faz com câmera falsa.

## Task 7: Código de treino

Repositório `modelo/`. Criar `treino/__init__.py`, `treino/dados.py`, `treino/rede.py`, `treino/treinar.py`, `treino/avaliar.py`, `tests/test_treino.py`, e adicionar a seção de treino ao `README.md`. Lê JSONs no contrato: tanto `dados/processados/` quanto `../interface/VIGIA/public/clipes/`.

`treino/dados.py`:
- `CLASSES = ["deitado", "sentado", "em_pe", "caindo"]`, as classes do próprio dataset. Mapeamento de rótulo original: `Sleeping` -> deitado; `Sitting` -> sentado; `Standing` e `Walking` -> em_pe; qualquer um começando com `Fall` -> caindo. Outros rótulos (Drinking, Writing, Reading, Exercising etc.) são atividades e não postura: são ignorados. Bloco de comentário declarando que o mapeamento para as 6 classes do produto está PENDENTE de dados próprios.
- `normalizar(pontos: np.ndarray) -> np.ndarray`: entrada `(T, 17, 3)`; centraliza no meio dos quadris, escala pelo comprimento do tronco do quadro, mantém `conf`. Quadro sem pose (NaN) vira zeros, sem NaN na saída; tronco muito pequeno não divide por zero.
- `rotulo_da_janela(rotulos, t_ini, t_fim) -> int | None`: classe com maior sobreposição, exigindo cobertura de ao menos 50% da janela; caso contrário, `None` (janela descartada). Se rótulos se sobrepõem, `caindo` tem prioridade quando sua cobertura atinge 50%.
- `janelas_do_clipe(clipe, duracao=2.0, passo=0.5, quadros=60)`: corta janelas de 2 s com passo de 0,5 s, reamostra para um número fixo de quadros por índice mais próximo (os fps do dataset variam) e devolve `(X, y)`. Descarta janela com menos de 50% de quadros com pose.
- `sujeito_do_clipe(clipe) -> int`, lido de `origem.arquivo` (`"Subject 2/Fall/24.mp4"`).
- `carregar_pastas(pastas)`, `JanelasDataset(torch.utils.data.Dataset)`. Duplicatas de clipe entre pastas (mesmo `origem.arquivo`) entram uma só vez.

`treino/rede.py`: `ClassificadorGRU(entrada=51, oculto=64, camadas=1, classes=4)`, com `GRU` e `Linear` sobre o último estado. Pequeno.

`treino/treinar.py` (executável com `python -m treino.treinar --dados dados/processados --epocas 10 --sujeitos-teste 4 --saida checkpoints/gru.pt --semente 42`): divisão por sujeito, sem vazamento: treino só em sujeitos fora de `--sujeitos-teste`, com asserção explícita de interseção vazia. Salva o checkpoint com `state_dict`, classes, hiperparâmetros e sujeitos de teste. Usa pesos de classe inversos à frequência no treino. Imprime perda por época. `torch.manual_seed` é a única fonte de aleatoriedade (embaralhar e inicializar), não gera dado.

`treino/avaliar.py` (`python -m treino.avaliar --dados ... --checkpoint ...`): carrega o checkpoint e avalia só nos sujeitos de teste gravados nele. Imprime número de janelas por classe, matriz de confusão e fração de acerto, sob o cabeçalho "Teste de funcionamento, sem validade como métrica".

Testes (pytest, sem dado real, fixture rotulada construída à mão, sem random): normalização centra quadril em zero e escala pelo tronco; quadro nulo não gera NaN; `rotulo_da_janela` por sobreposição e com cobertura insuficiente; mapeamento (`Falling (SW)`, `Fall (FW)`, `Sleeping`, atividade ignorada); forma de `janelas_do_clipe`; `ClassificadorGRU` devolve `(lote, 4)`; divisão por sujeito sem interseção; `treinar` de ponta a ponta em clipes sintéticos em `tmp_path`, por 1 época, salva checkpoint que `avaliar` carrega.

Execução real do treino: o controlador faz, depois de `processar-treino`.

## Task 8: Textos honestos

Repositório `interface/VIGIA`. Registrar exceções e alinhar textos. Modificar `src/components/Bastidores.jsx`, `src/components/Projeto.jsx`, `README.md`, conforme o estado real.

- `Bastidores.jsx:128`: "Estimador: MediaPipe na demonstração do pipeline; estimador do produto em avaliação (YOLO-pose, RTMPose, MediaPipe)".
- `Bastidores.jsx:148`: usar `STATUS_MODELO` de `src/data/pipeline.js` junto às candidatas.
- `Projeto.jsx:204`, `:220-221`, `:229-231` e `:307`: refletir o que é verdade. M1 feito. M2 feito só se os clipes reais estiverem publicados na branch. M3 "Próximo: modelo contra regra geométrica". O selo "Agora" sai de constante, não de texto fixo em M1.
- `README.md`: separar o que é protótipo (fictício) do que é real (aba Pipeline e câmera ao vivo), citar o repositório `modelo/`.
- Nenhum texto afirma que o MediaPipe é o estimador escolhido; nenhuma métrica; telas fictícias continuam rotuladas como protótipo.

## Task 9: Verificação e relatório

Executada pelo controlador: `pytest`, `npm test`, `npm run build`, roteiro completo em navegador, push da branch `pitch2`, preview em HTTPS, `RELATORIO_PITCH2.md`.
