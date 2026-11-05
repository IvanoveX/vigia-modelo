"""Download verificado dos modelos de pose do MediaPipe."""
import hashlib
import urllib.request
from pathlib import Path

URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
       "pose_landmarker_{nome}/float16/1/pose_landmarker_{nome}.task")

SHA256 = {
    "lite": "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a",
    "full": "5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1",
    "heavy": "64437af838a65d18e5ba7a0d39b465540069bc8aae8308de3e318aad31fcbc7b",
}


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def baixar_modelo(nome: str, pasta: Path) -> Path:
    """Baixa o modelo se preciso e confere o SHA-256; arquivo divergente é apagado."""
    if nome not in SHA256:
        raise ValueError(f"modelo desconhecido: {nome}")
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"pose_landmarker_{nome}.task"
    if destino.exists() and _sha256(destino) == SHA256[nome]:
        return destino
    try:
        urllib.request.urlretrieve(URL.format(nome=nome), destino)
    except Exception:
        destino.unlink(missing_ok=True)  # não deixa arquivo parcial
        raise
    if _sha256(destino) != SHA256[nome]:
        destino.unlink()
        raise ValueError(f"SHA-256 divergente para o modelo {nome}")
    return destino
