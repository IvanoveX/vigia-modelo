import copy
import json

from vigia_modelo.validar import validar_clipe, validar_pasta, validar_publicacao


def test_clipe_montado_e_valido(clipe):
    assert validar_clipe(clipe) == []
    assert validar_publicacao(clipe) == []


def test_rejeita_16_pontos(clipe):
    clipe["quadros"][0]["pontos"].pop()
    assert validar_clipe(clipe)


def test_rejeita_x_fora_da_faixa(clipe):
    clipe["quadros"][0]["pontos"][0][0] = 640
    assert validar_clipe(clipe)


def test_rejeita_classe_inexistente(clipe):
    clipe["baseline"]["janelas"][0]["classe"] = "voando"
    assert validar_clipe(clipe)


def test_rejeita_t_repetido(clipe):
    clipe["quadros"][1]["t"] = clipe["quadros"][0]["t"]
    assert any("crescente" in e for e in validar_clipe(clipe))


def test_rejeita_total_quadros_diferente(clipe):
    clipe["video"]["total_quadros"] = 99
    assert any("total_quadros" in e for e in validar_clipe(clipe))


def test_rejeita_intervalo_invertido(clipe):
    clipe["rotulos_origem"][0]["t_fim"] = -1 + clipe["rotulos_origem"][0]["t_ini"]
    assert validar_clipe(clipe)
    clipe["rotulos_origem"][0].update(t_ini=2.0, t_fim=1.0)
    assert any("t_fim" in e for e in validar_clipe(clipe))


def test_publicacao_rejeita_leito_nulo(clipe):
    clipe["leito"] = None
    assert validar_clipe(clipe) == []
    assert any("leito" in e for e in validar_publicacao(clipe))


def test_publicacao_rejeita_baseline_nulo(clipe):
    clipe["baseline"] = None
    assert any("baseline" in e for e in validar_publicacao(clipe))


def test_validar_pasta_ignora_indice(tmp_path, clipe):
    ruim = copy.deepcopy(clipe)
    ruim["quadros"][0]["pontos"].pop()
    (tmp_path / "bom.json").write_text(json.dumps(clipe), encoding="utf-8")
    (tmp_path / "ruim.json").write_text(json.dumps(ruim), encoding="utf-8")
    (tmp_path / "indice.json").write_text("{}", encoding="utf-8")
    r = validar_pasta(tmp_path)
    assert set(r) == {"bom.json", "ruim.json"}
    assert r["bom.json"] == [] and r["ruim.json"]
