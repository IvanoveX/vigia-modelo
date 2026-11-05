import math
from pathlib import Path

import cv2
import numpy as np
import pytest

from vigia_modelo.extrator import extrair_clipe, timestamps_ms


@pytest.mark.parametrize("fps", [29.84, 15.02, 30])
def test_timestamps_estritamente_crescentes(fps):
    ts = timestamps_ms(1000, fps)
    assert len(ts) == 1000
    assert all(b > a for a, b in zip(ts, ts[1:]))


@pytest.mark.parametrize("fps", [0, -5, math.nan])
def test_fps_invalido(fps):
    with pytest.raises(ValueError):
        timestamps_ms(10, fps)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        extrair_clipe(tmp_path / "nao_existe.mp4", tmp_path / "modelo.task")


@pytest.mark.integracao
def test_video_sem_pessoa(tmp_path):
    caminho = tmp_path / "vazio.avi"
    escritor = cv2.VideoWriter(str(caminho), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (160, 120))
    for _ in range(10):
        escritor.write(np.full((120, 160, 3), 128, dtype=np.uint8))
    escritor.release()
    modelo = Path("modelos/pose_landmarker_heavy.task")
    clipe = extrair_clipe(caminho, modelo)
    assert len(clipe["quadros"]) == 10
    assert all(q["pontos"] is None for q in clipe["quadros"])
    ts = [q["t"] for q in clipe["quadros"]]
    assert all(b > a for a, b in zip(ts, ts[1:]))
