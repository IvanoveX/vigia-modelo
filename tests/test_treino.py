"""Testes do código de treino. Fixtures construídas à mão, sem dado real e sem random."""
import json

import numpy as np
import pytest
import torch

from treino.avaliar import avaliar
from treino.dados import (
    CLASSES, JanelasDataset, carregar_pastas, classe_do_rotulo, dividir_por_sujeito,
    janelas_do_clipe, normalizar, rotulo_da_janela, sujeito_do_clipe,
)
from treino.rede import ClassificadorGRU
from treino.treinar import treinar

torch.set_num_threads(1)


def pose_fixa(deslocamento=0.0):
    """17 pontos: ombros em y=0.2, quadris em y=0.6 (tronco de 0.4)."""
    pontos = [[0.5 + deslocamento, 0.4, 0.9] for _ in range(17)]
    for i in (5, 6):
        pontos[i] = [0.5 + deslocamento, 0.2, 0.9]
    for i in (11, 12):
        pontos[i] = [0.5 + deslocamento, 0.6, 0.9]
    return pontos


def clipe(arquivo, rotulos, segundos=6, fps=10, sem_pose=(), largura=640, altura=480):
    quadros = [
        {"t": i / fps, "pontos": None if i in sem_pose else pose_fixa()}
        for i in range(int(segundos * fps))
    ]
    return {
        "origem": {"arquivo": arquivo},
        "video": {"largura": largura, "altura": altura},
        "quadros": quadros,
        "rotulos_origem": [
            {"t_ini": a, "t_fim": b, "rotulo": r} for a, b, r in rotulos
        ],
    }


def grava_clipes(pasta, clipes):
    pasta.mkdir(exist_ok=True)
    for i, c in enumerate(clipes):
        (pasta / f"c{i}.json").write_text(json.dumps(c))
    return pasta


def clipes_sinteticos():
    """Quatro sujeitos; o rótulo muda de classe conforme o sujeito."""
    rotulos = ["Sleeping", "Sitting", "Standing", "Falling (SW)"]
    return [
        clipe(f"Subject {s}/Activity/1.mp4", [(0, 6, rotulos[s - 1])])
        for s in (1, 2, 3, 4)
    ]


def test_normalizar_centra_quadril_e_escala_pelo_tronco():
    pontos = np.array([pose_fixa(0.3)] * 2)
    saida = normalizar(pontos)
    quadril = saida[:, [11, 12], :2].mean(axis=1)
    assert np.allclose(quadril, 0)
    assert np.allclose(saida[:, 5, 1], -1.0)  # ombro a um tronco acima do quadril
    assert np.allclose(saida[:, :, 2], 0.9)


def test_normalizar_quadro_nulo_vira_zeros_sem_nan():
    pontos = np.array([pose_fixa(), np.full((17, 3), np.nan)])
    saida = normalizar(pontos)
    assert not np.isnan(saida).any()
    assert np.all(saida[1] == 0)


def test_normalizar_tronco_zero_nao_divide_por_zero():
    pontos = np.full((1, 17, 3), 0.5)
    assert np.isfinite(normalizar(pontos)).all()


def test_mapeamento_de_rotulos():
    assert CLASSES[classe_do_rotulo("Falling (SW)")] == "caindo"
    assert CLASSES[classe_do_rotulo("Falling (BW")] == "caindo"
    assert CLASSES[classe_do_rotulo("Fall (FW)")] == "caindo"
    assert CLASSES[classe_do_rotulo("Sleeping")] == "deitado"
    assert CLASSES[classe_do_rotulo("Sitting")] == "sentado"
    assert CLASSES[classe_do_rotulo("Standing")] == "em_pe"
    assert CLASSES[classe_do_rotulo("Walking")] == "em_pe"
    assert classe_do_rotulo("Drinking") is None


def test_rotulo_da_janela_por_sobreposicao():
    rotulos = [
        {"t_ini": 0, "t_fim": 3, "rotulo": "Sitting"},
        {"t_ini": 3, "t_fim": 6, "rotulo": "Standing"},
    ]
    assert CLASSES[rotulo_da_janela(rotulos, 0.5, 2.5)] == "sentado"
    assert CLASSES[rotulo_da_janela(rotulos, 3.5, 5.5)] == "em_pe"


def test_rotulo_da_janela_cobertura_insuficiente():
    rotulos = [{"t_ini": 0, "t_fim": 3, "rotulo": "Sitting"}]
    assert CLASSES[rotulo_da_janela(rotulos, 2.0, 4.0)] == "sentado"  # 50% exato vale
    assert rotulo_da_janela(rotulos, 2.5, 4.5) is None
    assert rotulo_da_janela([{"t_ini": 0, "t_fim": 3, "rotulo": "Drinking"}], 0, 2) is None


def test_rotulo_da_janela_queda_tem_prioridade():
    rotulos = [
        {"t_ini": 0, "t_fim": 2, "rotulo": "Standing"},
        {"t_ini": 1, "t_fim": 2, "rotulo": "Falling (FW)"},
    ]
    assert CLASSES[rotulo_da_janela(rotulos, 0, 2)] == "caindo"


def test_janelas_do_clipe_forma_e_rotulo():
    X, y = janelas_do_clipe(clipe("Subject 1/A/1.mp4", [(0, 6, "Sleeping")]))
    assert X.shape[1:] == (60, 51)
    assert len(X) == len(y) == 9  # janelas de 2 s, passo 0,5 s, em 6 s
    assert set(y.tolist()) == {CLASSES.index("deitado")}


def test_mesmo_corpo_em_resolucoes_diferentes_normaliza_igual():
    # Mesmos pixels em 1280x720 e em 640x480: as frações diferem, o resultado não.
    pixels = [[320.0 + 10 * i, 100.0 + 5 * i, 0.9] for i in range(17)]

    def clipe_em(largura, altura):
        c = clipe("Subject 1/A/1.mp4", [(0, 6, "Sleeping")], largura=largura, altura=altura)
        pose = [[x / largura, y / altura, v] for x, y, v in pixels]
        for q in c["quadros"]:
            q["pontos"] = pose
        return c

    grande, pequeno = (janelas_do_clipe(clipe_em(*r))[0] for r in ((1280, 720), (640, 480)))
    assert not np.isnan(grande).any()
    np.testing.assert_allclose(grande, pequeno, atol=1e-5)


def test_janelas_do_clipe_descarta_pouca_pose_e_aceita_clipe_sem_janela():
    c = clipe("Subject 1/A/1.mp4", [(0, 6, "Sleeping")], sem_pose=range(0, 30))
    X, _ = janelas_do_clipe(c)
    assert len(X) < 9
    vazio = clipe("Subject 1/A/1.mp4", [(0, 6, "Drinking")])
    X, y = janelas_do_clipe(vazio)
    assert X.shape == (0, 60, 51) and y.shape == (0,)


def test_sujeito_do_clipe():
    assert sujeito_do_clipe(clipe("Subject 2/Fall/24.mp4", [])) == 2


def test_carregar_pastas_ignora_duplicata_e_json_sem_quadros(tmp_path):
    c = clipe("Subject 1/A/1.mp4", [])
    a = grava_clipes(tmp_path / "a", [c])
    b = grava_clipes(tmp_path / "b", [c])
    (a / "clipes.json").write_text(json.dumps([{"id": "x"}]))
    assert len(carregar_pastas([a, b])) == 1


def test_divisao_por_sujeito_sem_intersecao():
    clipes = clipes_sinteticos() + [clipe("Subject 4/B/2.mp4", [])]
    treino, teste, sujeitos_teste = dividir_por_sujeito(clipes, 1)
    assert sujeitos_teste == [4]
    s_treino = {sujeito_do_clipe(c) for c in treino}
    assert s_treino == {1, 2, 3} and not s_treino & set(sujeitos_teste)
    assert len(teste) == 2


def test_carregar_pastas_aceita_pasta_unica_e_ignora_indice(tmp_path):
    pasta = grava_clipes(tmp_path / "a", [clipe("Subject 1/A/1.mp4", [])])
    (pasta / "indice.json").write_text(json.dumps({"clipes": []}))
    assert len(carregar_pastas([pasta])) == 1


def test_rede_devolve_lote_por_classes():
    saida = ClassificadorGRU()(torch.zeros(3, 60, 51))
    assert saida.shape == (3, 4)


def test_dataset_vazio_tem_tamanho_zero():
    assert len(JanelasDataset([])) == 0


def test_treinar_e_avaliar_ponta_a_ponta(tmp_path, capsys):
    pasta = grava_clipes(tmp_path / "dados", clipes_sinteticos())
    saida = tmp_path / "gru.pt"
    treinar(pasta, epocas=1, sujeitos_teste=1, saida=saida, semente=0)
    ckpt = torch.load(saida, weights_only=False)
    assert ckpt["sujeitos_teste"] == [4] and ckpt["classes"] == CLASSES
    avaliar([pasta], saida)
    texto = capsys.readouterr().out
    assert "Teste de funcionamento, sem validade como métrica" in texto
    assert "caindo" in texto


def test_treinar_sem_nenhuma_pasta_existente_da_erro_claro(tmp_path):
    with pytest.raises(ValueError, match="nenhuma pasta de dados"):
        treinar([tmp_path / "a", tmp_path / "b"], epocas=1, sujeitos_teste=1, saida=tmp_path / "x.pt", semente=0)


def test_treinar_avisa_da_pasta_ausente_entre_existentes(tmp_path, capsys):
    pasta = grava_clipes(tmp_path / "dados", clipes_sinteticos())
    treinar([pasta, tmp_path / "ausente"], epocas=1, sujeitos_teste=1, saida=tmp_path / "x.pt", semente=0)
    assert "AVISO: pasta de dados não encontrada" in capsys.readouterr().out


def test_treinar_sem_janela_de_treino_da_erro_claro(tmp_path):
    vazio = [clipe(f"Subject {s}/A/1.mp4", [(0, 6, "Drinking")]) for s in (1, 2)]
    pasta = grava_clipes(tmp_path / "dados", vazio)
    with pytest.raises(ValueError, match="nenhuma janela de treino"):
        treinar(pasta, epocas=1, sujeitos_teste=1, saida=tmp_path / "x.pt", semente=0)


def test_avaliar_sem_janela_de_teste_da_erro_claro(tmp_path):
    pasta = grava_clipes(tmp_path / "dados", clipes_sinteticos()[:3])
    saida = tmp_path / "gru.pt"
    treinar(pasta, epocas=1, sujeitos_teste=1, saida=saida, semente=0)
    outra = grava_clipes(tmp_path / "outra", clipes_sinteticos()[:2])  # sem o sujeito 3
    with pytest.raises(ValueError, match="nenhuma janela de teste"):
        avaliar([outra], saida)
