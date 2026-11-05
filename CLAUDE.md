# VIGIA: modelo

Backend offline do VIGIA. Extrai pose de vídeo, calcula o baseline geométrico, exporta um JSON por clipe e contém o código de treino. O contrato é `schema/clipe.schema.json`. A referência do projeto está no `CLAUDE.md` da pasta acima.

## Regras de código

- Legível por um dev pleno. Funções curtas, com uma responsabilidade (~40 linhas no máximo).
- Comentários curtos, só quando o porquê não é óbvio.
- Nenhum emoji em código, logs ou commits.
- Arquivos organizados por responsabilidade. Sem Colab nem Jupyter.
- Nenhum dado inventado com random fora de fixture de teste rotulada.
- JSON novo ou alterado: atualizar o schema e validar antes de seguir.
- Números de teste só em relatório, descritos como teste de funcionamento. Nunca na interface.
- O MediaPipe é usado na demonstração. Nenhum texto pode dizer que ele foi escolhido como estimador do produto.

## Git

- Conventional Commits, em português, pequenos, sem emoji e sem menção a ferramentas de IA.
- Nunca versionar vídeos, modelos `.task`, checkpoints, datasets nem `.ipynb`. O notebook dos colegas contém a foto de uma pessoa.
