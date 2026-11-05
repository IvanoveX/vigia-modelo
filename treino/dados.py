"""Leitura dos clipes processados e montagem das janelas de treino."""
import json
import re
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

# ATENÇÃO: estas 4 classes são as do dataset público (GMDCSA-24), não as do produto.
# O mapeamento para as 6 classes do produto (repouso, sentando na borda, tentando
# levantar, queda, fora do leito há mais de N minutos, acompanhante presente) está
# PENDENTE de dados próprios. Rótulos de atividade (Drinking, Eating, Reading,
# Writing, Exercising) não são postura e ficam de fora.
CLASSES = ["deitado", "sentado", "em_pe", "caindo"]
_POR_ROTULO = {"sleeping": "deitado", "sitting": "sentado", "standing": "em_pe", "walking": "em_pe"}

OMBROS, QUADRIS = [5, 6], [11, 12]
TRONCO_MINIMO = 1e-3
COBERTURA_MINIMA = 0.5
EPS = 1e-9


def classe_do_rotulo(rotulo: str) -> int | None:
    nome = rotulo.strip().lower()
    # Os CSVs trazem variações como "Falling (SW)", "Fall (FW)" e "Falling (BW" sem fechar.
    if nome.startswith("fall"):
        return CLASSES.index("caindo")
    destino = _POR_ROTULO.get(nome)
    return None if destino is None else CLASSES.index(destino)


def normalizar(pontos: np.ndarray, largura: int = 1, altura: int = 1) -> np.ndarray:
    """(T, 17, 3) -> mesmo formato, centrado nos quadris e escalado pelo tronco.

    x e y chegam em fração do quadro; vão a pixels antes, porque o dataset mistura
    resoluções e o tronco medido em fração distorce com o aspecto.
    """
    pontos = np.array(pontos, dtype=np.float32)
    pontos[..., 0] *= largura
    pontos[..., 1] *= altura
    saida = np.zeros_like(pontos)
    for i, quadro in enumerate(pontos):
        if np.isnan(quadro).any():
            continue
        centro = quadro[QUADRIS, :2].mean(axis=0)
        tronco = np.linalg.norm(quadro[OMBROS, :2].mean(axis=0) - centro)
        saida[i, :, :2] = (quadro[:, :2] - centro) / max(tronco, TRONCO_MINIMO)
        saida[i, :, 2] = quadro[:, 2]
    return saida


def _cobertura_por_classe(rotulos: list[dict], t_ini: float, t_fim: float) -> dict[int, float]:
    cobertura: dict[int, float] = {}
    for r in rotulos:
        classe = classe_do_rotulo(r["rotulo"])
        if classe is None:
            continue
        sobre = min(t_fim, r["t_fim"]) - max(t_ini, r["t_ini"])
        if sobre > 0:
            cobertura[classe] = cobertura.get(classe, 0.0) + sobre / (t_fim - t_ini)
    return cobertura


def rotulo_da_janela(rotulos: list[dict], t_ini: float, t_fim: float) -> int | None:
    """Classe de maior sobreposição com cobertura mínima de 50%; queda tem prioridade."""
    cobertura = _cobertura_por_classe(rotulos, t_ini, t_fim)
    queda = CLASSES.index("caindo")
    if cobertura.get(queda, 0.0) >= COBERTURA_MINIMA - EPS:
        return queda
    if not cobertura:
        return None
    melhor = max(cobertura, key=cobertura.get)
    return melhor if cobertura[melhor] >= COBERTURA_MINIMA - EPS else None


def _pontos_do_clipe(clipe: dict) -> np.ndarray:
    vazio = [[np.nan] * 3] * 17
    return np.array([q["pontos"] or vazio for q in clipe["quadros"]], dtype=np.float32)


def _duracao_do_clipe(tempos: np.ndarray) -> float:
    # O último quadro dura um intervalo de amostragem.
    return float(tempos[-1] + (tempos[-1] / (len(tempos) - 1) if len(tempos) > 1 else 0))


def janelas_do_clipe(clipe, duracao=2.0, passo=0.5, quadros=60):
    """Devolve (X, y): X de forma (N, quadros, 51) e y de forma (N,)."""
    tempos = np.array([q["t"] for q in clipe["quadros"]])
    pontos = _pontos_do_clipe(clipe)
    com_pose = ~np.isnan(pontos).any(axis=(1, 2))
    video = clipe["video"]
    normalizado = normalizar(pontos, video["largura"], video["altura"])
    fim = _duracao_do_clipe(tempos)
    X, y = [], []
    for inicio in np.arange(0, fim - duracao + EPS, passo):
        alvo = inicio + np.arange(quadros) * duracao / quadros
        idx = np.abs(tempos[None, :] - alvo[:, None]).argmin(axis=1)
        if com_pose[idx].mean() < COBERTURA_MINIMA:
            continue
        classe = rotulo_da_janela(clipe["rotulos_origem"], inicio, inicio + duracao)
        if classe is not None:
            X.append(normalizado[idx].reshape(quadros, -1))
            y.append(classe)
    if not X:
        return np.zeros((0, quadros, 51), np.float32), np.zeros((0,), np.int64)
    return np.stack(X), np.array(y, dtype=np.int64)


def sujeito_do_clipe(clipe: dict) -> int:
    return int(re.search(r"Subject (\d+)", clipe["origem"]["arquivo"])[1])


def carregar_pastas(pastas) -> list[dict]:
    """Lê os JSONs das pastas; ignora os sem 'quadros' e repetidos (mesmo arquivo de origem)."""
    clipes, vistos = [], set()
    for pasta in pastas:
        for caminho in sorted(Path(pasta).glob("*.json")):
            dado = json.loads(caminho.read_text(encoding="utf-8"))
            if not isinstance(dado, dict) or "quadros" not in dado:
                continue
            origem = dado["origem"]["arquivo"]
            if origem not in vistos:
                vistos.add(origem)
                clipes.append(dado)
    return clipes


def dividir_por_sujeito(clipes: list[dict], n_teste: int):
    """Reserva os n_teste sujeitos de maior número. Devolve (treino, teste, sujeitos_teste)."""
    sujeitos = sorted({sujeito_do_clipe(c) for c in clipes})
    if not 0 < n_teste < len(sujeitos):
        raise ValueError(f"--sujeitos-teste deve estar entre 1 e {len(sujeitos) - 1}; há {len(sujeitos)} sujeitos")
    sujeitos_teste = sujeitos[-n_teste:]
    treino = [c for c in clipes if sujeito_do_clipe(c) not in sujeitos_teste]
    teste = [c for c in clipes if sujeito_do_clipe(c) in sujeitos_teste]
    return treino, teste, sujeitos_teste


class JanelasDataset(Dataset):
    def __init__(self, clipes: list[dict]):
        pares = [janelas_do_clipe(c) for c in clipes]
        vazio = (np.zeros((0, 60, 51), np.float32), np.zeros((0,), np.int64))
        X = np.concatenate([p[0] for p in pares] or [vazio[0]])
        y = np.concatenate([p[1] for p in pares] or [vazio[1]])
        self.X, self.y = torch.from_numpy(X), torch.from_numpy(y)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        return self.X[i], self.y[i]
