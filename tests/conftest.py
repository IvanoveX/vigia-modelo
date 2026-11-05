"""Fixtures escritas à mão, sem dados sorteados. Rotuladas como exemplo de teste."""
import pytest

ORIGEM_TESTE = {
    "dataset": "exemplo-de-teste",
    "licenca": "n/a",
    "url": "https://example.org/exemplo",
    "citacao": "Fixture de teste escrita à mão.",
}
POLIGONO = [[0.2, 0.4], [0.8, 0.4], [0.8, 0.8], [0.2, 0.8]]


def esqueleto_deitado():
    """17 pontos de exemplo, com ombros e quadris na horizontal."""
    pontos = [[0.5, 0.6, 0.9] for _ in range(17)]
    pontos[5], pontos[6] = [0.4, 0.6, 0.9], [0.4, 0.62, 0.9]
    pontos[11], pontos[12] = [0.6, 0.6, 0.9], [0.6, 0.62, 0.9]
    return pontos


@pytest.fixture
def entrada():
    return {"id_clipe": "exemplo-1", "titulo": "Exemplo de teste", "arquivo": "Subject 9/ADL/01.mp4",
            "leito": {"poligono": POLIGONO}, "origem": ORIGEM_TESTE}


@pytest.fixture
def extracao():
    quadros = [{"t": round(i / 10, 4), "pontos": esqueleto_deitado()} for i in range(30)]
    video = {"fps": 10.0, "largura": 1280, "altura": 720, "total_quadros": 30, "duracao_s": 3.0}
    return {"video": video, "quadros": quadros}


@pytest.fixture
def clipe(entrada, extracao):
    from vigia_modelo.baseline import gerar_janelas
    from vigia_modelo.exportar import montar_clipe
    janelas = gerar_janelas(extracao["quadros"], POLIGONO, 1280, 720)
    rotulos = [{"t_ini": 0.0, "t_fim": 3.0, "rotulo": "Sleeping"}]
    return montar_clipe(entrada, extracao, rotulos, janelas, "heavy")
