"""Rede temporal pequena: GRU sobre a sequência de esqueletos."""
import torch
from torch import nn


class ClassificadorGRU(nn.Module):
    def __init__(self, entrada=51, oculto=64, camadas=1, classes=4):
        super().__init__()
        self.gru = nn.GRU(entrada, oculto, camadas, batch_first=True)
        self.saida = nn.Linear(oculto, classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        estados, _ = self.gru(x)
        return self.saida(estados[:, -1])
