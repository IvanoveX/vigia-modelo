"""Validação dos JSONs de clipe contra o schema e regras que o schema não expressa."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA = json.loads((Path(__file__).parent.parent / "schema" / "clipe.schema.json").read_text(encoding="utf-8"))
_VALIDADOR = Draft202012Validator(SCHEMA)


def _erros_schema(clipe: dict) -> list[str]:
    erros = sorted(_VALIDADOR.iter_errors(clipe), key=lambda e: list(map(str, e.absolute_path)))
    return [f"{'/'.join(map(str, e.absolute_path)) or '(raiz)'}: {e.message[:120]}" for e in erros]


def _erros_quadros(clipe: dict) -> list[str]:
    quadros = clipe["quadros"]
    erros = []
    if clipe["video"]["total_quadros"] != len(quadros):
        erros.append(f"total_quadros ({clipe['video']['total_quadros']}) difere de len(quadros) ({len(quadros)})")
    tempos = [q["t"] for q in quadros]
    if any(b <= a for a, b in zip(tempos, tempos[1:])):
        erros.append("t dos quadros não é estritamente crescente")
    return erros


def _erros_intervalos(itens: list[dict], nome: str) -> list[str]:
    return [f"{nome}[{i}]: t_fim menor que t_ini" for i, x in enumerate(itens) if x["t_fim"] < x["t_ini"]]


def validar_clipe(clipe: dict) -> list[str]:
    """Lista de erros; vazia se o clipe é válido."""
    erros = _erros_schema(clipe)
    if erros:  # as regras abaixo supõem a estrutura correta
        return erros
    erros += _erros_quadros(clipe)
    erros += _erros_intervalos(clipe["rotulos_origem"], "rotulos_origem")
    if clipe["baseline"]:
        erros += _erros_intervalos(clipe["baseline"]["janelas"], "baseline.janelas")
    if clipe["predicao_modelo"]:
        erros += _erros_intervalos(clipe["predicao_modelo"]["janelas"], "predicao_modelo.janelas")
    return erros


def validar_publicacao(clipe: dict) -> list[str]:
    """Além de validar_clipe, exige leito e baseline, que a interface usa."""
    erros = validar_clipe(clipe)
    if erros:
        return erros
    if clipe["leito"] is None:
        erros.append("leito nulo: clipe de publicação precisa do polígono")
    if clipe["baseline"] is None:
        erros.append("baseline nulo: clipe de publicação precisa do baseline")
    return erros


def validar_pasta(pasta: Path) -> dict[str, list[str]]:
    """Erros por arquivo .json da pasta, exceto indice.json."""
    resultado = {}
    for arquivo in sorted(Path(pasta).glob("*.json")):
        if arquivo.name == "indice.json":
            continue
        try:
            clipe = json.loads(arquivo.read_text(encoding="utf-8"))
        except json.JSONDecodeError as erro:
            resultado[arquivo.name] = [f"JSON malformado: {erro}"]
            continue
        resultado[arquivo.name] = validar_publicacao(clipe)
    return resultado
