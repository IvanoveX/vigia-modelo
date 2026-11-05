"""Lê os rótulos de tempo dos CSVs do GMDCSA-24."""
import re
from pathlib import Path

# O texto do rótulo pode ter parêntese sem fechar, ex.: "Falling (BW[5.9 to 10]".
INTERVALO = re.compile(r"^\s*(.+?)\s*\[\s*([\d.]+)\s*to\s*([\d.]+)\s*\]")


def _linhas_de_dados(csv: Path) -> list[str]:
    linhas = csv.read_text(encoding="utf-8-sig").splitlines()
    return [l for l in linhas[1:] if l.strip()]


def _nome_da_linha(linha: str) -> str:
    return linha.split(",", 1)[0].strip()


def _rotulos_da_linha(linha: str) -> list[dict]:
    # A descrição tem vírgulas; a coluna de classes é sempre a última.
    classes = linha.rsplit(",", 1)[1]
    rotulos = []
    for trecho in classes.split(";"):
        m = INTERVALO.match(trecho)
        if m:
            rotulos.append({"t_ini": float(m[2]), "t_fim": float(m[3]), "rotulo": m[1].strip()})
    return sorted(rotulos, key=lambda r: r["t_ini"])


def clipes_do_csv(csv: Path) -> list[str]:
    """Nomes dos arquivos (ex.: '24.mp4') listados no CSV, na ordem."""
    return [_nome_da_linha(l) for l in _linhas_de_dados(csv)]


def rotulos_do_clipe(raiz: Path, arquivo: str) -> list[dict]:
    """arquivo no formato 'Subject 2/Fall/24.mp4'."""
    sujeito, tipo, nome = arquivo.split("/")
    csv = Path(raiz) / sujeito / f"{tipo}.csv"
    for linha in _linhas_de_dados(csv):
        if _nome_da_linha(linha) == nome:
            return _rotulos_da_linha(linha)
    raise ValueError(f"{nome} não consta em {csv}")
