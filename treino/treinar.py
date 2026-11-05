"""Treino do classificador. Uso: python -m treino.treinar --epocas 10 --sujeitos-teste 1"""
import argparse
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from treino.dados import CLASSES, JanelasDataset, carregar_pastas, dividir_por_sujeito, sujeito_do_clipe
from treino.rede import ClassificadorGRU

PASTAS_PADRAO = ["dados/processados", "../interface/VIGIA/public/clipes"]
HIPERPARAMETROS = {"entrada": 51, "oculto": 64, "camadas": 1, "classes": len(CLASSES)}


def _pesos_de_classe(y: torch.Tensor) -> torch.Tensor:
    # Inverso da frequência no treino; classe ausente fica com contagem 1.
    contagem = torch.bincount(y, minlength=len(CLASSES)).clamp(min=1).float()
    return len(y) / (len(CLASSES) * contagem)


def _treinar_epoca(rede, carregador, perda, otimizador) -> float:
    total = 0.0
    for X, y in carregador:
        otimizador.zero_grad()
        valor = perda(rede(X), y)
        valor.backward()
        otimizador.step()
        total += valor.item() * len(y)
    return total / len(carregador.dataset)


def treinar(pasta, epocas, sujeitos_teste, saida, semente, lote=32, taxa=1e-3):
    """pasta: uma pasta ou lista de pastas. sujeitos_teste: quantidade reservada."""
    torch.manual_seed(semente)
    pastas = [pasta] if isinstance(pasta, (str, Path)) else list(pasta)
    treino, _, reservados = dividir_por_sujeito(carregar_pastas(pastas), sujeitos_teste)
    # Sem vazamento: nenhum sujeito de treino pode estar no teste.
    assert not {sujeito_do_clipe(c) for c in treino} & set(reservados)
    dataset = JanelasDataset(treino)
    if len(dataset) == 0:
        raise ValueError("nenhuma janela de treino: confira as pastas e os sujeitos reservados")
    rede = ClassificadorGRU(**HIPERPARAMETROS)
    perda = nn.CrossEntropyLoss(weight=_pesos_de_classe(dataset.y))
    otimizador = torch.optim.Adam(rede.parameters(), lr=taxa)
    carregador = DataLoader(dataset, batch_size=lote, shuffle=True)
    for epoca in range(1, epocas + 1):
        print(f"época {epoca}/{epocas}  perda {_treinar_epoca(rede, carregador, perda, otimizador):.4f}")
    _salvar(rede, saida, reservados, epocas, semente)
    print(f"treino com {len(dataset)} janelas; sujeitos de teste reservados: {reservados}")


def _salvar(rede, saida, sujeitos_teste, epocas, semente):
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": rede.state_dict(),
        "classes": CLASSES,
        "hiperparametros": {**HIPERPARAMETROS, "epocas": epocas, "semente": semente},
        "sujeitos_teste": sujeitos_teste,
    }, saida)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", nargs="+", default=PASTAS_PADRAO, help="uma ou mais pastas de JSONs")
    p.add_argument("--epocas", type=int, default=10)
    p.add_argument("--sujeitos-teste", type=int, default=1, help="quantos sujeitos (os de maior número) ficam para teste")
    p.add_argument("--saida", default="checkpoints/gru.pt")
    p.add_argument("--semente", type=int, default=42)
    a = p.parse_args()
    treinar(a.dados, a.epocas, a.sujeitos_teste, a.saida, a.semente)


if __name__ == "__main__":
    main()
