"""Mapeamento dos 33 landmarks do MediaPipe para os 17 pontos COCO.

A tabela de índices tem origem no notebook dos colegas.
"""

INDICES_MEDIAPIPE = [0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]

NOMES_COCO = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]


def selecionar_coco(landmarks) -> list[list[float]]:
    """Devolve [x, y, conf] por ponto COCO; conf é o visibility, limitado a 0-1."""
    pontos = []
    for i in INDICES_MEDIAPIPE:
        lm = landmarks[i]
        conf = min(1.0, max(0.0, lm.visibility))
        pontos.append([round(lm.x, 4), round(lm.y, 4), round(conf, 2)])
    return pontos
