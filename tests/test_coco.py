from types import SimpleNamespace

from vigia_modelo.coco import INDICES_MEDIAPIPE, NOMES_COCO, selecionar_coco


def _landmarks_falsos():
    return [SimpleNamespace(x=float(i), y=0.0, visibility=1.0) for i in range(33)]


def test_ordem_do_mapeamento_coco():
    pontos = selecionar_coco(_landmarks_falsos())
    assert [p[0] for p in pontos] == [float(i) for i in INDICES_MEDIAPIPE]
    assert len(pontos) == len(NOMES_COCO) == 17


def test_arredondamento_e_limite_de_confianca():
    lm = _landmarks_falsos()
    lm[0] = SimpleNamespace(x=0.123456, y=0.987654, visibility=0.856)
    lm[2] = SimpleNamespace(x=0.5, y=0.5, visibility=1.7)
    lm[5] = SimpleNamespace(x=0.5, y=0.5, visibility=-0.2)
    pontos = selecionar_coco(lm)
    assert pontos[0] == [0.1235, 0.9877, 0.86]
    assert pontos[1][2] == 1.0
    assert pontos[2][2] == 0.0
