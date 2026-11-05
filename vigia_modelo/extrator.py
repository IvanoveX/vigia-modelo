"""Extrai a pose de um vídeo, quadro a quadro, sem guardar imagem."""
import math
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

from vigia_modelo.coco import selecionar_coco

CONFIANCA_MINIMA = 0.60  # configuração do notebook dos colegas


def _validar_fps(fps: float) -> None:
    if not (fps > 0 and math.isfinite(fps)):
        raise ValueError(f"fps inválido: {fps}")


def _ts_ms(indice: int, fps: float) -> int:
    return round(indice * 1000 / fps)


def timestamps_ms(n: int, fps: float) -> list[int]:
    """Tempo de cada quadro em ms, pelo índice (nunca CAP_PROP_POS_MSEC)."""
    _validar_fps(fps)
    ts = [_ts_ms(i, fps) for i in range(n)]
    if any(b <= a for a, b in zip(ts, ts[1:])):
        raise ValueError(f"fps alto demais para timestamps em ms: {fps}")
    return ts


def _criar_detector(modelo: Path):
    opcoes = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(modelo)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=CONFIANCA_MINIMA,
        min_pose_presence_confidence=CONFIANCA_MINIMA,
        min_tracking_confidence=CONFIANCA_MINIMA,
        output_segmentation_masks=False,
    )
    return vision.PoseLandmarker.create_from_options(opcoes)


def _pontos_do_quadro(detector, quadro_bgr, ts_ms: int):
    rgb = cv2.cvtColor(quadro_bgr, cv2.COLOR_BGR2RGB)
    imagem = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    resultado = detector.detect_for_video(imagem, ts_ms)
    if not resultado.pose_landmarks:
        return None
    return selecionar_coco(resultado.pose_landmarks[0])


def _ler_quadros(captura):
    while True:
        ok, quadro = captura.read()
        if not ok:
            return
        yield quadro


def _metadados(captura) -> dict:
    fps = captura.get(cv2.CAP_PROP_FPS)
    return {
        "fps": fps,
        "largura": int(captura.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "altura": int(captura.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }


def extrair_clipe(caminho: Path, modelo: Path) -> dict:
    """Devolve {"video", "quadros"} no formato do schema; imagens são descartadas."""
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(caminho)
    captura = cv2.VideoCapture(str(caminho))
    detector = None
    try:
        video = _metadados(captura)
        _validar_fps(video["fps"])
        detector = _criar_detector(modelo)
        quadros = []
        for i, quadro in enumerate(_ler_quadros(captura)):
            ts = _ts_ms(i, video["fps"])
            quadros.append({"t": round(ts / 1000, 4), "pontos": _pontos_do_quadro(detector, quadro, ts)})
        video["total_quadros"] = len(quadros)
        video["duracao_s"] = round(len(quadros) / video["fps"], 4)
        return {"video": video, "quadros": quadros}
    finally:
        captura.release()
        if detector is not None:
            detector.close()
