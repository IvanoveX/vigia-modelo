# Resultado dos clipes da demonstração

Execução de 05/11/2026, com `python -m vigia_modelo processar`, modelo `heavy` do MediaPipe 1.2.2, em Fedora (CPU). Os JSONs estão em `interface/VIGIA/public/clipes/`.

## O que foi medido

Por clipe: a porcentagem de quadros com pose e a classe do baseline geométrico v1, janela a janela, contra o rótulo que o próprio dataset dá para aquele trecho.

Os polígonos do leito foram marcados olhando quadros, antes de rodar o baseline, e não foram ajustados depois. Os limiares também não.

## Resumo

| Clipe | Duração | Quadros | Com pose | Janelas |
|---|---|---|---|---|
| `Subject 2/Fall/24` | 7,1 s | 213 | 100% | 11 |
| `Subject 3/ADL/03` | 9,9 s | 296 | 100% | 16 |
| `Subject 1/ADL/04` | 5,8 s | 170 | 100% | 8 |
| `Subject 2/Fall/11` | 10,6 s | 159 | 92,5% | 18 |

## Baseline contra o rótulo do dataset

As janelas têm 2 s com passo de 0,5 s. Uma janela pode cruzar dois rótulos, e o dataset deixa trechos sem rótulo.

### `Subject 2/Fall/24`: levanta do leito e cai de lado

Rótulos: Sitting 0,0-1,7; Standing 2,0-3,2; Falling (SW) 3,3-6,4.

| Janelas | Baseline | Leitura |
|---|---|---|
| 0,0-2,5 | sentando | Coerente com Sitting |
| 1,0-4,0 | levantando | Coerente com a saída do leito e Standing |
| 2,5-7,0 | queda | Coerente com Falling. A primeira, 2,5-4,5, dispara pelo último quarto da janela |

### `Subject 3/ADL/03`: levanta da cama e anda

Rótulos: Sleeping 0,0-1,0; Sitting 3,0-7,4; Standing 7,6-8,4; Walking 8,5-9,0.

| Janelas | Baseline | Leitura |
|---|---|---|
| 0,0-2,5 | repouso | Coerente com Sleeping |
| 1,0-3,0 | indefinido | Transição, inclinação de 52,19 graus, entre os limiares de 35 e 55. Trecho sem rótulo |
| 1,5-8,5 | sentando | Coerente com Sitting |
| 7,0-9,5 | levantando | Coerente com Standing. **Erro de classe:** Walking sai como levantando, porque a pessoa continua a menos de 1 tronco do leito |

### `Subject 1/ADL/04`: deitado, senta na cama

Rótulos: Sleeping 0,0-1,5; Sitting 2,5-5,0.

| Janelas | Baseline | Leitura |
|---|---|---|
| 0,0-3,5 | indefinido | **Erro:** o dataset diz Sleeping e o baseline nunca diz repouso |
| 2,0-5,5 | levantando | **Erro:** o dataset diz Sitting |

Causa provável: a câmera está baixa, e o quadril de quem está sobre o colchão aparece acima da borda do polígono (`altura_quadril` entre 0,24 e 0,29, `dentro_leito` falso). O baseline trata como fora do leito. A correção honesta é repensar a geometria em câmera baixa, não mexer neste clipe até acertar.

### `Subject 2/Fall/11`: cai da cama para o chão

Rótulos: Walking 0,0-1,3; Falling (BW 5,9-10,0. O texto do rótulo está assim no CSV, sem fechar o parêntese.

| Janelas | Baseline | Leitura |
|---|---|---|
| 0,0-2,0 | levantando | **Erro de classe:** Walking, a pessoa caminha perto do leito |
| 0,5-4,0 | indefinido | Trecho sem rótulo |
| 2,5-6,5 | repouso | Plausível, deitado no leito, trecho sem rótulo. Conferido só pela coordenada, não pelo vídeo |
| 5,0-10,5 | queda | Coerente com Falling. A janela 5,0-7,0 tem `frac_validos` 0,6: há quadros sem pose justamente na queda |

## O que isto NÃO permite afirmar

- Isto é um teste de funcionamento, com 4 clipes escolhidos à mão. Não é métrica, e nenhum número daqui vale como desempenho.
- Nada aqui mostra detecção de "sentar na borda" nem de "tentar levantar sem apoio". O baseline sabe "sentado sobre o leito" e "ereto perto do leito". O dataset não tem essas cenas.
- Os atores estão sem coberta, em casa, bem iluminados. Não há teste com paciente, em hospital, à noite ou sob lençol.
- Detectar pose não é acertar os pontos: não há gabarito de keypoints.

## Limitações

- O resultado depende muito do polígono, marcado à mão por quadro único. Uma pessoa ainda precisa conferir os quatro.
- `Subject 2/Fall/11` perde 7,5% dos quadros, concentrados na queda, que é o trecho de maior interesse.
- A última janela usa o tempo do último quadro, não a duração do vídeo, e pode perder até uma janela no fim.
