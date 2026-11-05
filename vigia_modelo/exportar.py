"""Monta e grava o JSON de cada clipe e o índice da pasta de publicação."""
import json
from pathlib import Path

import mediapipe

from vigia_modelo.coco import NOMES_COCO

VERSAO_SCHEMA = "1.0.0"

ORIGEM_GMDCSA = {
    "dataset": "GMDCSA-24",
    "licenca": "CC BY 4.0",
    "url": "https://zenodo.org/records/13354453",
    "citacao": ("E. Alam, A. Sufian, P. Dutta, M. Leo, I. A. Hameed. GMDCSA24: A Dataset for "
                "Human Fall Detection in Videos. Data in Brief, 2024."),
}


def _baseline(janelas):
    if janelas is None:
        return None
    return {"descricao": "regra geométrica, não é o modelo", "versao": "1", "janelas": janelas}


def montar_clipe(entrada: dict, extracao: dict, rotulos: list, janelas, nome_modelo: str) -> dict:
    """entrada: item do manifesto; 'origem' é opcional e só as fixtures de teste a usam."""
    origem = dict(entrada.get("origem", ORIGEM_GMDCSA), arquivo=entrada["arquivo"])
    return {
        "versao_schema": VERSAO_SCHEMA,
        "id_clipe": entrada["id_clipe"],
        "origem": origem,
        "gerado_por": {"estimador": "mediapipe-pose-landmarker", "modelo": nome_modelo,
                       "versao": mediapipe.__version__},
        "video": extracao["video"],
        "leito": entrada.get("leito"),
        "keypoints": list(NOMES_COCO),
        "quadros": extracao["quadros"],
        "rotulos_origem": rotulos,
        "baseline": _baseline(janelas),
        "predicao_modelo": None,
    }


def _gravar_json(dados: dict, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return destino


def escrever_clipe(clipe: dict, pasta: Path) -> Path:
    return _gravar_json(clipe, Path(pasta) / f"{clipe['id_clipe']}.json")


def escrever_indice(clipes: list, pasta: Path) -> Path:
    """clipes: pares (titulo, clipe), na ordem do manifesto."""
    itens = [{"id": c["id_clipe"], "titulo": titulo, "duracao_s": c["video"]["duracao_s"],
              "dataset": c["origem"]["dataset"]} for titulo, c in clipes]
    return _gravar_json({"versao_schema": VERSAO_SCHEMA, "clipes": itens}, Path(pasta) / "indice.json")
