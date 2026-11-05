"""Avaliação nos sujeitos de teste gravados no checkpoint. Uso: python -m treino.avaliar --checkpoint checkpoints/gru.pt"""
import argparse
from pathlib import Path

import torch

from treino.dados import JanelasDataset, carregar_pastas, sujeito_do_clipe
from treino.rede import ClassificadorGRU
from treino.treinar import PASTAS_PADRAO

CABECALHO = "Teste de funcionamento, sem validade como métrica"


def _carregar_rede(ckpt: dict) -> ClassificadorGRU:
    h = ckpt["hiperparametros"]
    rede = ClassificadorGRU(h["entrada"], h["oculto"], h["camadas"], h["classes"])
    rede.load_state_dict(ckpt["state_dict"])
    return rede.eval()


def _confusao(real: torch.Tensor, previsto: torch.Tensor, n: int) -> torch.Tensor:
    matriz = torch.zeros(n, n, dtype=torch.long)
    for r, p in zip(real.tolist(), previsto.tolist()):
        matriz[r, p] += 1
    return matriz


def _imprimir(classes: list[str], matriz: torch.Tensor, sujeitos: list[int]):
    print(CABECALHO)
    print(f"sujeitos de teste: {sujeitos}")
    print("janelas por classe: " + ", ".join(f"{c}={int(matriz[i].sum())}" for i, c in enumerate(classes)))
    print("matriz de confusão (linhas = real, colunas = previsto):")
    print(" " * 10 + "".join(f"{c:>10}" for c in classes))
    for i, c in enumerate(classes):
        print(f"{c:<10}" + "".join(f"{int(v):>10}" for v in matriz[i]))
    print(f"fração de acerto: {matriz.diag().sum().item() / matriz.sum().item():.3f}")


def avaliar(pastas, checkpoint):
    ckpt = torch.load(checkpoint, weights_only=False)
    pastas = [pastas] if isinstance(pastas, (str, Path)) else list(pastas)
    clipes = [c for c in carregar_pastas(pastas) if sujeito_do_clipe(c) in ckpt["sujeitos_teste"]]
    dataset = JanelasDataset(clipes)
    if len(dataset) == 0:
        raise ValueError(f"nenhuma janela de teste para os sujeitos {ckpt['sujeitos_teste']} nas pastas dadas")
    with torch.no_grad():
        previsto = _carregar_rede(ckpt)(dataset.X).argmax(dim=1)
    _imprimir(ckpt["classes"], _confusao(dataset.y, previsto, len(ckpt["classes"])), ckpt["sujeitos_teste"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", nargs="+", default=PASTAS_PADRAO)
    p.add_argument("--checkpoint", default="checkpoints/gru.pt")
    a = p.parse_args()
    avaliar(a.dados, a.checkpoint)


if __name__ == "__main__":
    main()
