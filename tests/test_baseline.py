"""Testes do baseline geometrico com esqueletos construidos a mao (fixture)."""
import pytest

from vigia_modelo.baseline import (
    classificar_janela,
    features_do_quadro,
    gerar_janelas,
)

L, A = 1280, 720
# Primeiro lado horizontal (y = 288 px); o colchao fica abaixo dele.
POLIGONO = [[0.2, 0.4], [0.8, 0.4], [0.8, 0.8], [0.2, 0.8]]


def esqueleto(ombro, quadril, conf=0.9):
    """17 pontos normalizados; ombros e quadris vem de pixels (x, y)."""
    pontos = [[0.5, 0.5, 0.0] for _ in range(17)]
    for i in (5, 6):
        pontos[i] = [ombro[0] / L, ombro[1] / A, conf]
    for i in (11, 12):
        pontos[i] = [quadril[0] / L, quadril[1] / A, conf]
    return pontos


def quadros(n, fps, pontos):
    return [{"t": i / fps, "pontos": pontos} for i in range(n)]


def test_tronco_paralelo_ao_lado_da_zero():
    f = features_do_quadro(esqueleto((500, 500), (600, 500)), POLIGONO, L, A)
    assert f["inclinacao_graus"] == pytest.approx(0, abs=0.01)


def test_tronco_perpendicular_da_noventa():
    f = features_do_quadro(esqueleto((600, 350), (600, 500)), POLIGONO, L, A)
    assert f["inclinacao_graus"] == pytest.approx(90, abs=0.01)


def test_correcao_de_aspecto_em_pixels():
    # 100 px por 100 px: 45 graus em pixels, 60,6 se usasse fracoes.
    f = features_do_quadro(esqueleto((600, 300), (700, 400)), POLIGONO, L, A)
    assert f["inclinacao_graus"] == pytest.approx(45, abs=0.01)


def test_altura_positiva_acima_da_reta_e_dentro_do_leito():
    f = features_do_quadro(esqueleto((600, 150), (600, 250)), POLIGONO, L, A)
    assert f["altura_px"] == pytest.approx(38)  # 288 - 250
    assert f["dentro_leito"] is False
    assert f["distancia_px"] == pytest.approx(38)


def test_quadril_dentro_do_leito():
    f = features_do_quadro(esqueleto((500, 500), (600, 500)), POLIGONO, L, A)
    assert f["dentro_leito"] is True
    assert f["distancia_px"] == 0
    assert f["altura_px"] < 0


def test_ombro_com_conf_baixa_da_none():
    p = esqueleto((500, 500), (600, 500))
    p[5][2] = 0.4
    assert features_do_quadro(p, POLIGONO, L, A) is None


def test_sem_pose_da_none():
    assert features_do_quadro(None, POLIGONO, L, A) is None


def feats(inc, altura=0.0, dentro=True, dist=0.0, frac=1.0, **fim):
    d = {"inclinacao_graus": inc, "altura_quadril": altura,
         "dentro_leito": dentro, "distancia_leito": dist, "vel_max": 0.0,
         "frac_validos": frac}
    d.update(inclinacao_fim=inc, altura_fim=altura, dentro_leito_fim=dentro)
    d.update(fim)
    return d


@pytest.mark.parametrize("f, esperado", [
    (feats(10, frac=0.49), "indefinido"),                                # 1
    (feats(45, -0.1, False, 0.5), "queda"),                              # 2, limite 45
    (feats(45.01, -0.1, False, 0.5), "indefinido"),
    (feats(80, 0.0, False, 0.5, inclinacao_fim=30, altura_fim=-1.0,
           dentro_leito_fim=False), "queda"),                            # usa o fim
    (feats(10, -0.1, False, 0.5, altura_fim=0.0), "indefinido"),
    (feats(35, 0.0, True), "repouso"),                                   # 3, limite 35
    (feats(35.01, 0.0, True), "indefinido"),                             # 8
    (feats(55, 0.8, True), "sentando"),                                  # 4, limites
    (feats(55, 0.81, True), "levantando"),                               # 5
    (feats(55, 0.5, False, 1.0), "levantando"),                          # 6
    (feats(54.99, 0.5, False, 1.0), "indefinido"),
    (feats(55, 0.5, False, 1.01), "fora"),                               # 7
])
def test_regras_da_tabela(f, esperado):
    assert classificar_janela(f) == esperado


def test_features_nulas_dao_indefinido():
    f = feats(None, None, None, None, frac=0.0)
    f.update(inclinacao_fim=None, altura_fim=None, dentro_leito_fim=None)
    assert classificar_janela(f) == "indefinido"


DEITADO = esqueleto((500, 500), (600, 500))


def test_deitado_no_leito_e_repouso_com_janelas_de_2s_passo_meio():
    janelas = gerar_janelas(quadros(31, 10, DEITADO), POLIGONO, L, A)
    assert [j["t_ini"] for j in janelas] == [0.0, 0.5, 1.0]
    assert all(j["t_fim"] - j["t_ini"] == 2.0 for j in janelas)
    assert all(j["classe"] == "repouso" for j in janelas)
    assert set(janelas[0]["features"]) == {
        "inclinacao_graus", "altura_quadril", "dentro_leito",
        "distancia_leito", "vel_max", "frac_validos"}
    assert janelas[0]["features"]["frac_validos"] == 1.0


def test_clipe_de_um_segundo_e_meio_nao_gera_janela():
    assert gerar_janelas(quadros(16, 10, DEITADO), POLIGONO, L, A) == []


def test_sessenta_por_cento_nulos_da_indefinido():
    qs = quadros(21, 10, DEITADO)
    for q in qs[:13]:
        q["pontos"] = None
    primeira = gerar_janelas(qs, POLIGONO, L, A)[0]
    assert primeira["classe"] == "indefinido"
    assert primeira["features"]["frac_validos"] < 0.5


def test_tudo_nulo_nao_quebra():
    qs = [{"t": i / 10, "pontos": None} for i in range(26)]
    janelas = gerar_janelas(qs, POLIGONO, L, A)
    assert len(janelas) == 2
    for j in janelas:
        assert j["classe"] == "indefinido"
        assert j["features"]["frac_validos"] == 0
        assert j["features"]["inclinacao_graus"] is None
        assert j["features"]["vel_max"] is None


def test_queda_usa_o_ultimo_quarto_da_janela():
    # Deitado no leito, depois no chao (abaixo do leito, y > 576) a partir de 1,5 s.
    chao = esqueleto((500, 650), (600, 650))
    qs = quadros(15, 10, DEITADO) + quadros(16, 10, chao)
    for i, q in enumerate(qs):
        q["t"] = i / 10
    j = gerar_janelas(qs, POLIGONO, L, A)[0]
    assert j["classe"] == "queda"
    assert "inclinacao_fim" not in j["features"]
