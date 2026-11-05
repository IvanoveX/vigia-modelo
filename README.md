# VIGIA: modelo

Pipeline offline do VIGIA. Extrai a pose (17 pontos, formato COCO) de vídeos, descarta as imagens, calcula o baseline geométrico e exporta um JSON por clipe. O front lê esses JSONs como arquivos estáticos. O contrato é `schema/clipe.schema.json`.

O baseline é uma regra geométrica, não é o modelo. Os JSONs guardam só coordenadas e metadados, nenhuma imagem.

## Como rodar do zero num Mac

Todos os comandos abaixo são digitados no Terminal, dentro da pasta `modelo/` do projeto.

1. Entrar na pasta (ajuste o caminho para onde o projeto está no seu Mac):

   ```
   cd ~/caminho/do/projeto/modelo
   ```

   Esperado: nenhuma mensagem. `pwd` deve terminar em `/modelo`.

2. Criar o ambiente Python isolado (só na primeira vez):

   ```
   python3 -m venv .venv
   ```

   Esperado: nenhuma mensagem; aparece a pasta `.venv`.

3. Ativar o ambiente (a cada terminal novo):

   ```
   source .venv/bin/activate
   ```

   Esperado: o prompt passa a começar com `(.venv)`.

4. Instalar as dependências (só na primeira vez; leva alguns minutos, o PyTorch é grande):

   ```
   pip install -r requirements.txt
   ```

   Esperado: termina com `Successfully installed ...` e sem a palavra ERROR.

5. Conferir que está tudo certo:

   ```
   pytest
   ```

   Esperado: uma linha final como `NN passed` (os testes de integração com MediaPipe ficam de fora por padrão).

6. Colocar o dataset em `dados/brutos/extraidos/` (veja Dataset abaixo). Os comandos usam por padrão a pasta
   `dados/brutos/extraidos/ekramalam-GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos-5abac76`,
   que deve conter `Subject 1`, `Subject 2` etc.

7. Baixar o modelo de pose (só na primeira vez):

   ```
   python -m vigia_modelo baixar-modelo --modelo heavy --pasta modelos
   ```

   Esperado: `Modelo pronto em modelos/pose_landmarker_heavy.task`. O SHA-256 é conferido; se divergir, o arquivo é apagado e o comando falha.

8. Gerar os JSONs dos clipes de demonstração:

   ```
   python -m vigia_modelo processar --manifesto clipes.json --saida ../interface/VIGIA/public/clipes
   ```

   Esperado: uma linha por clipe, como `gmdcsa24-s2-fall-24: NN% dos quadros com pose, NNN KB`, e os arquivos `.json` mais o `indice.json` na pasta de saída. Se algum JSON for inválido, o comando mostra o erro, não grava esse clipe e sai com código diferente de zero.

9. Validar a pasta de publicação:

   ```
   python -m vigia_modelo validar ../interface/VIGIA/public/clipes
   ```

   Esperado: `<arquivo>.json: ok` para cada clipe. Qualquer `INVÁLIDO` vem com a lista de erros.

## Comandos

Todos rodam como `python -m vigia_modelo <comando>`. Use `--help` em qualquer um para ver as opções.

| Comando | O que faz |
| --- | --- |
| `baixar-modelo --modelo heavy --pasta modelos` | Baixa o modelo de pose e confere o SHA-256. |
| `processar --manifesto clipes.json --brutos <raiz> --saida ../interface/VIGIA/public/clipes --modelo heavy` | Gera um JSON por clipe do manifesto (com leito e baseline) e o `indice.json`. |
| `processar-treino --brutos <raiz> --saida dados/processados --modelo heavy [--sujeito N]` | Gera JSONs de todos os vídeos listados nos CSVs, sem leito nem baseline, para treino. Pula os que já existem e os vídeos ausentes no disco; um clipe com falha é reportado e os outros continuam. |
| `quadros --arquivo <mp4> --saida dados/conferencia --n 6` | Grava PNGs locais de quadros espaçados, para marcar o polígono do leito. A pasta não vai para o git. |
| `validar <pasta>` | Valida cada JSON da pasta (schema e regras extras). Sai com código diferente de zero se houver erro. |

O `clipes.json` lista os clipes de demonstração: `id_clipe`, `titulo`, `arquivo` (relativo à raiz do dataset) e o polígono do leito em frações da largura e da altura. O primeiro lado do polígono é a borda superior do colchão.

## Estimador de pose

O MediaPipe Pose Landmarker é usado na demonstração. Ele não foi escolhido como estimador do produto: o estimador do produto segue em avaliação. O JSON registra o estimador, o modelo e a versão usados em cada clipe.

Do model card do MediaPipe: o modelo "is not intended for human life-critical decisions". O mesmo vale para este projeto, que é um protótipo acadêmico.

## Créditos

- O mapeamento dos 33 pontos do MediaPipe para os 17 pontos COCO e a configuração do detector vêm do notebook dos colegas do grupo, que fizeram a primeira versão desse trabalho.
- Dataset: GMDCSA-24, E. Alam, A. Sufian, P. Dutta, M. Leo, I. A. Hameed. *GMDCSA24: A Dataset for Human Fall Detection in Videos*. Data in Brief, 2024. Licença CC BY 4.0, em https://zenodo.org/records/13354453. Os JSONs derivados trazem essa origem, licença e citação no campo `origem`.
- O pacote do dataset no GitHub traz um `LICENSE` MIT (Ekram Alam). Cumprimos as duas licenças: a CC BY 4.0 dos dados, com a atribuição acima, e o aviso de copyright e permissão da MIT que acompanha o pacote.
