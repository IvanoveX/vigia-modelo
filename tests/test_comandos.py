"""Testes da CLI com extração simulada (sem MediaPipe) e dados de fixture."""
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from tests.conftest import POLIGONO, ORIGEM_TESTE, esqueleto_deitado
from vigia_modelo import comandos
from vigia_modelo.__main__ import main

CSV_ADL = "File Name,Length (seconds),Time of Recording,Attire,Description, Classes\n"


@pytest.fixture
def brutos(tmp_path):
    """Raiz de exemplo com dois clipes no CSV, mas só 01.mp4 existe no disco."""
    raiz = tmp_path / "brutos"
    (raiz / "Subject 9" / "ADL").mkdir(parents=True)
    (raiz / "Subject 9" / "ADL.csv").write_text(
        CSV_ADL + "01.mp4,03,Day,x,Dormindo, Sleeping[0 to 3]\n02.mp4,03,Day,x,Dormindo, Sleeping[0 to 3]\n",
        encoding="utf-8")
    (raiz / "Subject 9" / "ADL" / "01.mp4").write_bytes(b"x")
    return raiz


@pytest.fixture
def extracao_falsa(monkeypatch, extracao):
    monkeypatch.setattr(comandos, "baixar_modelo", lambda nome, pasta: Path(pasta) / "m.task")
    monkeypatch.setattr(comandos, "extrair_clipe", lambda caminho, modelo: extracao)


def manifesto(tmp_path, leito=True):
    item = {"id_clipe": "exemplo-1", "titulo": "Exemplo de teste", "arquivo": "Subject 9/ADL/01.mp4",
            "leito": {"poligono": POLIGONO} if leito else None, "origem": ORIGEM_TESTE}
    caminho = tmp_path / "clipes.json"
    caminho.write_text(json.dumps([item]), encoding="utf-8")
    return caminho


def rodar(*args):
    return main([str(a) for a in args])


def test_processar_grava_clipe_e_indice(tmp_path, brutos, extracao_falsa, capsys):
    saida = tmp_path / "saida"
    codigo = rodar("processar", "--manifesto", manifesto(tmp_path), "--brutos", brutos, "--saida", saida)
    assert codigo == 0
    assert (saida / "exemplo-1.json").is_file() and (saida / "indice.json").is_file()
    assert "100%" in capsys.readouterr().out


def test_processar_sem_pasta_pai_da_saida_falha_sem_criar_arvore(tmp_path, brutos, extracao_falsa, capsys):
    saida = tmp_path / "nao_existe" / "clipes"
    codigo = rodar("processar", "--manifesto", manifesto(tmp_path), "--brutos", brutos, "--saida", saida)
    assert codigo == 1
    assert not (tmp_path / "nao_existe").exists()
    assert "nao_existe" in capsys.readouterr().out


def test_processar_recusa_json_invalido(tmp_path, brutos, monkeypatch, extracao_falsa, extracao):
    extracao["quadros"][1]["t"] = extracao["quadros"][0]["t"]
    saida = tmp_path / "saida"
    codigo = rodar("processar", "--manifesto", manifesto(tmp_path), "--brutos", brutos, "--saida", saida)
    assert codigo != 0
    assert not (saida / "exemplo-1.json").exists()


def test_treino_pula_ausentes_e_existentes(tmp_path, brutos, extracao_falsa, capsys):
    saida = tmp_path / "proc"
    args = ("processar-treino", "--brutos", brutos, "--saida", saida)
    assert rodar(*args) == 0
    clipe = json.loads((saida / "gmdcsa24-s9-adl-01.json").read_text(encoding="utf-8"))
    assert clipe["leito"] is None and clipe["baseline"] is None
    assert clipe["rotulos_origem"][0]["rotulo"] == "Sleeping"
    assert not (saida / "gmdcsa24-s9-adl-02.json").exists()
    assert "ausente" in capsys.readouterr().out
    assert rodar(*args) == 0
    assert "já existe" in capsys.readouterr().out


def test_treino_continua_apos_falha(tmp_path, brutos, extracao_falsa, monkeypatch):
    (brutos / "Subject 9" / "ADL" / "02.mp4").write_bytes(b"x")
    chamadas = []

    def extrair(caminho, modelo):
        chamadas.append(caminho.name)
        if caminho.name == "01.mp4":
            raise RuntimeError("falha simulada")
        return monkeypatch_extracao

    monkeypatch_extracao = comandos.extrair_clipe(Path("x"), Path("m"))
    monkeypatch.setattr(comandos, "extrair_clipe", extrair)
    saida = tmp_path / "proc"
    assert rodar("processar-treino", "--brutos", brutos, "--saida", saida) != 0
    assert chamadas == ["01.mp4", "02.mp4"]
    assert (saida / "gmdcsa24-s9-adl-02.json").is_file()


def test_treino_filtra_sujeito(tmp_path, brutos, extracao_falsa):
    saida = tmp_path / "proc"
    assert rodar("processar-treino", "--brutos", brutos, "--saida", saida, "--sujeito", 3) == 0
    assert not saida.exists() or not list(saida.glob("*.json"))


def test_validar_codigo_de_saida(tmp_path, clipe):
    (tmp_path / "ok.json").write_text(json.dumps(clipe), encoding="utf-8")
    assert rodar("validar", tmp_path) == 0
    clipe["quadros"][0]["pontos"].pop()
    (tmp_path / "ruim.json").write_text(json.dumps(clipe), encoding="utf-8")
    assert rodar("validar", tmp_path) != 0


def test_quadros_grava_pngs(tmp_path):
    video = tmp_path / "v.mp4"
    escritor = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 48))
    for i in range(20):  # quadros sintéticos de fixture: cinza crescente
        escritor.write(np.full((48, 64, 3), i * 10, dtype=np.uint8))
    escritor.release()
    saida = tmp_path / "conf"
    assert rodar("quadros", "--arquivo", video, "--saida", saida, "--n", 4) == 0
    assert len(list(saida.glob("*.png"))) == 4


def test_processar_continua_apos_runtime_error(tmp_path, brutos, extracao_falsa, extracao, monkeypatch):
    itens = [{"id_clipe": f"exemplo-{k}", "titulo": "Exemplo", "arquivo": f"Subject 9/ADL/0{k}.mp4",
              "leito": {"poligono": POLIGONO}, "origem": ORIGEM_TESTE} for k in (1, 2)]
    caminho = tmp_path / "dois.json"
    caminho.write_text(json.dumps(itens), encoding="utf-8")

    def extrair(arquivo, modelo):
        if arquivo.name == "01.mp4":
            raise RuntimeError("falha simulada do MediaPipe")
        return extracao

    monkeypatch.setattr(comandos, "extrair_clipe", extrair)
    saida = tmp_path / "saida"
    assert rodar("processar", "--manifesto", caminho, "--brutos", brutos, "--saida", saida) != 0
    assert (saida / "exemplo-2.json").is_file() and not (saida / "indice.json").exists()


def test_validar_pasta_inexistente(tmp_path, capsys):
    assert rodar("validar", tmp_path / "nada") != 0
    assert "não existe" in capsys.readouterr().out


def test_validar_pasta_sem_json(tmp_path, capsys):
    assert rodar("validar", tmp_path) != 0
    assert "nenhum JSON" in capsys.readouterr().out


def test_validar_json_malformado(tmp_path, capsys):
    (tmp_path / "quebrado.json").write_text("{nao e json", encoding="utf-8")
    assert rodar("validar", tmp_path) != 0
    assert "quebrado.json" in capsys.readouterr().out


def test_quadros_so_diz_fora_do_git_em_dados(tmp_path, capsys):
    video = tmp_path / "v.mp4"
    escritor = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 48))
    for i in range(5):
        escritor.write(np.full((48, 64, 3), i * 10, dtype=np.uint8))
    escritor.release()
    rodar("quadros", "--arquivo", video, "--saida", tmp_path / "conf", "--n", 2)
    assert "fora do git" not in capsys.readouterr().out
