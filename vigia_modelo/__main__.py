"""Ponto de entrada: python -m vigia_modelo <comando>."""
import argparse
import sys

from vigia_modelo import comandos

BRUTOS_PADRAO = ("dados/brutos/extraidos/"
                 "ekramalam-GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos-5abac76")


def _modelo(p) -> None:
    p.add_argument("--modelo", default="heavy", choices=["lite", "full", "heavy"])
    p.add_argument("--pasta-modelos", default="modelos")


def _parser() -> argparse.ArgumentParser:
    raiz = argparse.ArgumentParser(prog="vigia_modelo", description="Pipeline offline do VIGIA")
    sub = raiz.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("baixar-modelo", help="baixa o modelo de pose e confere o SHA-256")
    p.add_argument("--modelo", default="heavy", choices=["lite", "full", "heavy"])
    p.add_argument("--pasta", default="modelos")
    p.set_defaults(func=comandos.baixar)

    p = sub.add_parser("processar", help="gera os JSONs de publicação a partir do manifesto")
    p.add_argument("--manifesto", default="clipes.json")
    p.add_argument("--brutos", default=BRUTOS_PADRAO)
    p.add_argument("--saida", default="../interface/VIGIA/public/clipes")
    _modelo(p)
    p.set_defaults(func=comandos.processar)

    p = sub.add_parser("processar-treino", help="gera JSONs de todos os vídeos, sem leito, para treino")
    p.add_argument("--brutos", default=BRUTOS_PADRAO)
    p.add_argument("--saida", default="dados/processados")
    p.add_argument("--sujeito", type=int)
    _modelo(p)
    p.set_defaults(func=comandos.processar_treino)

    p = sub.add_parser("quadros", help="grava PNGs locais para marcar o leito")
    p.add_argument("--arquivo", required=True)
    p.add_argument("--saida", default="dados/conferencia")
    p.add_argument("--n", type=int, default=6)
    p.set_defaults(func=comandos.quadros)

    p = sub.add_parser("validar", help="valida os JSONs de uma pasta")
    p.add_argument("pasta")
    p.set_defaults(func=comandos.validar)
    return raiz


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
