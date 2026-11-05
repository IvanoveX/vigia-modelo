from pathlib import Path

import pytest

from vigia_modelo.rotulos import clipes_do_csv, rotulos_do_clipe

CABECALHO = "File Name,Length (seconds),Time of Recording,Attire,Description, Classes\n"

# Linhas escritas à mão, no formato dos CSVs do GMDCSA-24 (fixture de teste).
LINHAS = [
    "01.mp4,06,Day,T-Shirt,Fall, with comma; and semicolon, Falling (SW)[1.4 to 6]; Standing[0.4 to 1.2]",
    "02.mp4,08,Day,T-Shirt,Sitting, Sitting[ 0 to 8]; Writing[0 to 8]",
    "03.mp4,07,Day,T-Shirt,Sitting, Sitting [0 to 7]",
    "04.mp4,11,Day,T-Shirt,Drinking, Drinking[10.5 to 11]; Sitting [0 to 11];",
    "05.mp4,10,Day,T-Shirt,Broken, Falling (BW[5.9 to 10]",
]


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    pasta = tmp_path / "Subject 2"
    pasta.mkdir()
    (pasta / "Fall.csv").write_text(CABECALHO + "\n".join(LINHAS) + "\n", encoding="utf-8")
    return tmp_path


def test_ordena_por_t_ini_e_mantem_texto_original(raiz):
    r = rotulos_do_clipe(raiz, "Subject 2/Fall/01.mp4")
    assert r == [
        {"t_ini": 0.4, "t_fim": 1.2, "rotulo": "Standing"},
        {"t_ini": 1.4, "t_fim": 6.0, "rotulo": "Falling (SW)"},
    ]


def test_espaco_dentro_dos_colchetes_e_antes(raiz):
    assert rotulos_do_clipe(raiz, "Subject 2/Fall/02.mp4") == [
        {"t_ini": 0.0, "t_fim": 8.0, "rotulo": "Sitting"},
        {"t_ini": 0.0, "t_fim": 8.0, "rotulo": "Writing"},
    ]
    assert rotulos_do_clipe(raiz, "Subject 2/Fall/03.mp4")[0]["rotulo"] == "Sitting"


def test_ponto_e_virgula_final_e_decimais(raiz):
    r = rotulos_do_clipe(raiz, "Subject 2/Fall/04.mp4")
    assert [x["rotulo"] for x in r] == ["Sitting", "Drinking"]
    assert r[1]["t_ini"] == 10.5


def test_parenteses_sem_fechar(raiz):
    assert rotulos_do_clipe(raiz, "Subject 2/Fall/05.mp4") == [
        {"t_ini": 5.9, "t_fim": 10.0, "rotulo": "Falling (BW"},
    ]


def test_arquivo_fora_do_csv(raiz):
    with pytest.raises(ValueError, match="99.mp4"):
        rotulos_do_clipe(raiz, "Subject 2/Fall/99.mp4")


def test_lista_clipes_do_csv(raiz):
    nomes = clipes_do_csv(raiz / "Subject 2" / "Fall.csv")
    assert nomes == ["01.mp4", "02.mp4", "03.mp4", "04.mp4", "05.mp4"]


RAIZ_REAL = next(Path("dados/brutos/extraidos").glob("ekramalam-*"), None)


@pytest.mark.integracao
@pytest.mark.skipif(RAIZ_REAL is None, reason="dataset local ausente")
def test_todos_os_csvs_reais_tem_rotulo_em_cada_clipe():
    for csv in sorted(RAIZ_REAL.glob("Subject */*.csv")):
        sujeito, tipo = csv.parent.name, csv.stem
        for nome in clipes_do_csv(csv):
            assert rotulos_do_clipe(RAIZ_REAL, f"{sujeito}/{tipo}/{nome}"), (csv, nome)
