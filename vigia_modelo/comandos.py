"""Comandos da CLI. Cada um devolve o código de saída (0 = tudo certo)."""
import json
from pathlib import Path

import cv2

from vigia_modelo.baseline import gerar_janelas
from vigia_modelo.exportar import escrever_clipe, escrever_indice, montar_clipe
from vigia_modelo.extrator import extrair_clipe
from vigia_modelo.modelo_pose import baixar_modelo
from vigia_modelo.rotulos import clipes_do_csv, rotulos_do_clipe
from vigia_modelo.validar import validar_clipe, validar_pasta, validar_publicacao


def baixar(args) -> int:
    destino = baixar_modelo(args.modelo, Path(args.pasta))
    print(f"Modelo pronto em {destino}")
    return 0


def _pct_com_pose(clipe: dict) -> float:
    quadros = clipe["quadros"]
    return 100 * sum(q["pontos"] is not None for q in quadros) / len(quadros)


def _processar_um(entrada: dict, args, modelo: Path) -> dict:
    """Extrai, monta e valida um clipe de publicação; levanta ValueError se inválido."""
    raiz = Path(args.brutos)
    extracao = extrair_clipe(raiz / entrada["arquivo"], modelo)
    video = extracao["video"]
    janelas = gerar_janelas(extracao["quadros"], entrada["leito"]["poligono"],
                            video["largura"], video["altura"])
    rotulos = rotulos_do_clipe(raiz, entrada["arquivo"])
    clipe = montar_clipe(entrada, extracao, rotulos, janelas, args.modelo)
    erros = validar_publicacao(clipe)
    if erros:
        raise ValueError("JSON inválido, nada foi gravado: " + "; ".join(erros[:5]))
    return clipe


def processar(args) -> int:
    entradas = json.loads(Path(args.manifesto).read_text(encoding="utf-8"))
    modelo = baixar_modelo(args.modelo, Path(args.pasta_modelos))
    gerados, falhas = [], 0
    for entrada in entradas:
        try:
            clipe = _processar_um(entrada, args, modelo)
        except Exception as erro:  # um clipe ruim não pode parar o lote
            print(f"ERRO {entrada['id_clipe']}: {erro}")
            falhas += 1
            continue
        destino = escrever_clipe(clipe, Path(args.saida))
        print(f"{clipe['id_clipe']}: {_pct_com_pose(clipe):.0f}% dos quadros com pose, "
              f"{destino.stat().st_size / 1024:.0f} KB")
        gerados.append((entrada["titulo"], clipe))
    if gerados and not falhas:
        escrever_indice(gerados, Path(args.saida))
    return 1 if falhas else 0


def _id_de_treino(arquivo: str) -> str:
    sujeito, tipo, nome = arquivo.split("/")
    return f"gmdcsa24-s{sujeito.split()[-1]}-{tipo.lower()}-{Path(nome).stem}"


def _arquivos_de_treino(raiz: Path, sujeito) -> list[str]:
    arquivos = []
    for csv in sorted(raiz.glob("Subject */*.csv")):
        if sujeito is not None and csv.parent.name != f"Subject {sujeito}":
            continue
        arquivos += [f"{csv.parent.name}/{csv.stem}/{n}" for n in clipes_do_csv(csv)]
    return arquivos


def _treinar_um(arquivo: str, args, modelo: Path) -> Path:
    raiz = Path(args.brutos)
    extracao = extrair_clipe(raiz / arquivo, modelo)
    entrada = {"id_clipe": _id_de_treino(arquivo), "arquivo": arquivo, "leito": None}
    clipe = montar_clipe(entrada, extracao, rotulos_do_clipe(raiz, arquivo), None, args.modelo)
    erros = validar_clipe(clipe)
    if erros:
        raise ValueError("; ".join(erros[:5]))
    return escrever_clipe(clipe, Path(args.saida))


def processar_treino(args) -> int:
    raiz, saida = Path(args.brutos), Path(args.saida)
    modelo = baixar_modelo(args.modelo, Path(args.pasta_modelos))
    falhas = 0
    for arquivo in _arquivos_de_treino(raiz, args.sujeito):
        id_clipe = _id_de_treino(arquivo)
        if not (raiz / arquivo).is_file():
            print(f"{id_clipe}: vídeo ausente, pulado")
        elif (saida / f"{id_clipe}.json").exists():
            print(f"{id_clipe}: já existe, pulado")
        else:
            falhas += _tentar_treinar(arquivo, id_clipe, args, modelo)
    return 1 if falhas else 0


def _tentar_treinar(arquivo: str, id_clipe: str, args, modelo: Path) -> int:
    """Devolve 1 se o clipe falhou, sem interromper os demais."""
    try:
        destino = _treinar_um(arquivo, args, modelo)
    except Exception as erro:  # um clipe ruim não pode parar o lote
        print(f"ERRO {id_clipe}: {erro}")
        return 1
    print(f"{id_clipe}: gravado ({destino.stat().st_size / 1024:.0f} KB)")
    return 0


def _indices_espacados(total: int, n: int) -> list[int]:
    return sorted({round(i * (total - 1) / max(n - 1, 1)) for i in range(n)})


def quadros(args) -> int:
    arquivo = Path(args.arquivo)
    captura = cv2.VideoCapture(str(arquivo))
    total = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
    if not arquivo.is_file() or total < 1:
        print(f"ERRO: não foi possível ler {arquivo}")
        return 1
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    base = f"{arquivo.parent.parent.name}_{arquivo.parent.name}_{arquivo.stem}".replace(" ", "_")
    for k, indice in enumerate(_indices_espacados(total, args.n), start=1):
        captura.set(cv2.CAP_PROP_POS_FRAMES, indice)
        ok, quadro = captura.read()
        if ok:
            cv2.imwrite(str(saida / f"{base}-{k}.png"), quadro)
    captura.release()
    aviso = " (pasta local, fora do git)" if "dados" in saida.parts else ""
    print(f"Quadros gravados em {saida}{aviso}")
    return 0


def validar(args) -> int:
    pasta = Path(args.pasta)
    if not pasta.is_dir():
        print(f"ERRO: a pasta {pasta} não existe")
        return 1
    resultado = validar_pasta(pasta)
    if not resultado:
        print(f"ERRO: nenhum JSON de clipe em {pasta}")
        return 1
    for nome, erros in resultado.items():
        print(f"{nome}: " + ("ok" if not erros else "INVÁLIDO"))
        for erro in erros:
            print(f"  - {erro}")
    return 1 if any(resultado.values()) else 0
