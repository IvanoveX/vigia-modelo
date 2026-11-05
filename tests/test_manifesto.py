import json
from pathlib import Path

MANIFESTO = Path(__file__).parent.parent / "clipes.json"


def test_manifesto_tem_campos_e_poligonos_validos():
    itens = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    assert len(itens) == 4
    assert len({i["id_clipe"] for i in itens}) == 4
    for i in itens:
        assert i["titulo"] and i["arquivo"].endswith(".mp4")
        poligono = i["leito"]["poligono"]
        assert len(poligono) >= 3
        assert all(0 <= v <= 1 for ponto in poligono for v in ponto)
