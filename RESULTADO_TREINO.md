# Teste de funcionamento do treino

**Isto não é métrica de desempenho.** Mostra que o código de treino e de avaliação roda de ponta a ponta sobre poses reais. Nenhum número daqui vale como desempenho do VIGIA, e nenhum vai para a interface.

Execução de 05/11/2026, em Fedora (CPU), Python 3.14.8, torch 2.15.0.

```
python -m treino.treinar --epocas 10 --sujeitos-teste 1 --saida checkpoints/gru.pt --semente 42
python -m treino.avaliar --checkpoint checkpoints/gru.pt
```

## O que foi medido

- **Dados:** 159 clipes do GMDCSA-24, com 33.851 quadros, 97,0% deles com pose. Um clipe ficou de fora: `Subject 2/ADL/06` traz no CSV o intervalo `Sitting[9.7 to 3]`, com o fim antes do início. O valor não foi corrigido por adivinhação.
- **Modelo:** GRU com uma camada e 64 unidades, 10 épocas, semente 42.
- **Divisão por sujeito:** treino nos sujeitos 1, 2 e 3 e teste no sujeito 4, com a interseção conferida no código.
- **Classes:** as do próprio dataset (deitado, sentado, em pé, caindo). O mapeamento para as 6 classes do produto está pendente de dados próprios.

Janelas por sujeito e classe, com 2 s de duração e passo de 0,5 s:

| Sujeito | Uso | deitado | sentado | em pé | caindo |
|---|---|---|---|---|---|
| 1 | treino | 32 | 84 | 52 | 88 |
| 2 | treino | 18 | 157 | 260 | 185 |
| 3 | treino | 10 | 207 | 136 | 126 |
| 4 | teste | 29 | 217 | 63 | 86 |

A perda caiu de 1,09 na primeira época para 0,15 na nona e subiu para 0,25 na décima.

Matriz no sujeito 4 (linhas: real; colunas: previsto):

| | deitado | sentado | em pé | caindo |
|---|---|---|---|---|
| deitado | 7 | 1 | 0 | 21 |
| sentado | 0 | 211 | 5 | 1 |
| em pé | 0 | 0 | 60 | 3 |
| caindo | 11 | 5 | 20 | 50 |

Fração de acerto: 0,830 (328 de 395 janelas).

## O que isto NÃO permite afirmar

- **Que o modelo acerta 83%.** O teste tem um único sujeito e uma única semente. Janelas vizinhas se sobrepõem e não são amostras independentes, então as 395 janelas valem bem menos do que parecem.
- **Nada sobre a pré-queda.** O teste classifica postura. Não há "sentar na borda" nem "tentar levantar sem apoio" nestes dados.
- **Nada sobre o ambiente real.** Atores em casa, sem coberta, bem iluminados. Não há paciente, hospital, noite nem lençol.
- **Que o número seja bom.** Só 'sentado' já responde por 54,9% das janelas de teste. A classe mais rara é a que mais importa, e nela o resultado é fraco: 21 de 29 janelas de 'deitado' saem como 'caindo'.

## Limitações

- O rótulo 'caindo' do dataset inclui o tempo em que a pessoa já está no chão. Por isso 'deitado' e 'caindo' se confundem, e a tarefa não é a mesma do produto.
- A normalização não usa a confiança dos pontos. Quadril ou ombro com confiança baixa geram centro e escala arbitrários.
- O checkpoint não registra quais clipes usou.
- Sem busca de hiperparâmetros: os valores são iniciais, e a perda ainda oscila no fim.
- `predicao_modelo` continua nulo nos JSONs publicados. Este modelo não alimenta a interface.
