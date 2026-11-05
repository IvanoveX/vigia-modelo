import json

from vigia_modelo.exportar import ORIGEM_GMDCSA, escrever_clipe, escrever_indice, montar_clipe


def test_campos_fixos(clipe):
    assert clipe["versao_schema"] == "1.0.0"
    assert clipe["predicao_modelo"] is None
    assert clipe["baseline"]["versao"] == "1"
    assert clipe["baseline"]["descricao"] == "regra geométrica, não é o modelo"
    assert clipe["gerado_por"]["estimador"] == "mediapipe-pose-landmarker"
    assert clipe["gerado_por"]["modelo"] == "heavy"
    assert clipe["origem"]["dataset"] == "exemplo-de-teste"
    assert clipe["origem"]["arquivo"] == "Subject 9/ADL/01.mp4"


def test_origem_padrao_e_gmdcsa(entrada, extracao):
    del entrada["origem"]
    c = montar_clipe(entrada, extracao, [], [], "heavy")
    assert c["origem"]["dataset"] == ORIGEM_GMDCSA["dataset"] == "GMDCSA-24"
    assert c["origem"]["licenca"] == "CC BY 4.0"


def test_treino_sem_leito_tem_baseline_nulo(entrada, extracao):
    entrada["leito"] = None
    c = montar_clipe(entrada, extracao, [], None, "heavy")
    assert c["leito"] is None and c["baseline"] is None


def test_json_sem_espacos_e_acentos(clipe, tmp_path):
    destino = escrever_clipe(clipe, tmp_path)
    assert destino.name == "exemplo-1.json"
    texto = destino.read_text(encoding="utf-8")
    assert texto == json.dumps(clipe, ensure_ascii=False, separators=(",", ":"))
    assert "geométrica" in texto
    assert json.loads(texto) == clipe


def test_indice_na_ordem(clipe, tmp_path):
    b = dict(clipe, id_clipe="b")
    a = dict(clipe, id_clipe="a")
    destino = escrever_indice([("Segundo", b), ("Primeiro", a)], tmp_path)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["versao_schema"] == "1.0.0"
    assert [c["id"] for c in dados["clipes"]] == ["b", "a"]
    assert dados["clipes"][0] == {"id": "b", "titulo": "Segundo", "duracao_s": 3.0,
                                  "dataset": "exemplo-de-teste"}
