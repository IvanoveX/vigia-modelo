"""Baseline geometrico v1: regras sobre o esqueleto, sem aprendizado.

Funcoes puras: recebem pontos normalizados (x, y, conf) e o poligono do
leito em fracoes; os calculos de distancia e angulo usam pixels.
"""
import cv2
import numpy as np

OMBROS = (5, 6)
QUADRIS = (11, 12)
CONF_MIN = 0.5

JANELA_S = 2.0
PASSO_S = 0.5
FRACAO_FIM = 0.25  # ultimo quarto da janela, usado na regra de queda

FRAC_VALIDOS_MIN = 0.5
INCL_REPOUSO = 35
INCL_QUEDA = 45
INCL_ERETO = 55
ALTURA_SENTADO = 0.8
DIST_PERTO = 1.0


def _par(pontos, indices):
    """Meio dos pontos indicados, em coordenadas normalizadas."""
    return np.mean([pontos[i][:2] for i in indices], axis=0)


def _quadro_valido(pontos):
    if pontos is None:
        return False
    return all(pontos[i][2] >= CONF_MIN for i in OMBROS + QUADRIS)


def _normal_para_cima(a, b):
    """Normal unitaria da reta a-b, apontando para menor y (acima)."""
    d = b - a
    n = np.array([d[1], -d[0]]) / np.hypot(*d)
    return n if n[1] <= 0 else -n


def _inclinacao(tronco, lado):
    cos = abs(np.dot(tronco, lado)) / (np.linalg.norm(tronco) * np.linalg.norm(lado))
    return float(np.degrees(np.arccos(min(1.0, cos))))


def features_do_quadro(pontos, poligono, largura, altura):
    """Features em pixels de um quadro, ou None se o quadro for invalido.

    Alem das features do JSON devolve tronco_px e o centroide (cx, cy), que
    gerar_janelas precisa para normalizar pelo tronco e calcular a velocidade.
    """
    if not _quadro_valido(pontos):
        return None
    escala = np.array([largura, altura])
    ombros, quadris = _par(pontos, OMBROS) * escala, _par(pontos, QUADRIS) * escala
    tronco = quadris - ombros
    poli = np.array(poligono, dtype=np.float32) * np.float32(escala)
    lado = poli[1] - poli[0]
    if np.linalg.norm(tronco) == 0 or np.linalg.norm(lado) == 0:
        return None
    sinal = cv2.pointPolygonTest(poli.reshape(-1, 1, 2), tuple(map(float, quadris)), True)
    centroide = (ombros + quadris) / 2
    return {
        "inclinacao_graus": _inclinacao(tronco, lado),
        "altura_px": float(np.dot(_normal_para_cima(poli[0], poli[1]), quadris - poli[0])),
        "dentro_leito": bool(sinal >= 0),
        "distancia_px": float(max(0.0, -sinal)),
        "tronco_px": float(np.linalg.norm(tronco)),
        "cx": float(centroide[0]),
        "cy": float(centroide[1]),
    }


def classificar_janela(f):
    """Aplica a tabela de regras na ordem. Chaves *_fim servem so a queda."""
    if f["frac_validos"] < FRAC_VALIDOS_MIN:
        return "indefinido"
    if _e_queda(f):
        return "queda"
    inc, dentro = f["inclinacao_graus"], f["dentro_leito"]
    if inc is None or dentro is None:
        return "indefinido"
    if inc <= INCL_REPOUSO and dentro:
        return "repouso"
    if inc >= INCL_ERETO:
        return _classe_ereto(f, dentro)
    return "indefinido"


def _e_queda(f):
    inc, alt, dentro = f.get("inclinacao_fim"), f.get("altura_fim"), f.get("dentro_leito_fim")
    if inc is None or alt is None or dentro is None:
        return False
    return inc <= INCL_QUEDA and not dentro and alt < 0


def _classe_ereto(f, dentro):
    if dentro:
        return "sentando" if f["altura_quadril"] <= ALTURA_SENTADO else "levantando"
    return "levantando" if f["distancia_leito"] <= DIST_PERTO else "fora"


def _mediana(valores):
    return float(np.median(valores)) if valores else None


def _maioria(valores):
    return bool(np.mean(valores) >= 0.5) if valores else None


def _resumo(validos, tronco, chave_altura="altura_px", chave_dist="distancia_px"):
    """Mediana das features de uma lista de quadros validos."""
    return {
        "inclinacao_graus": _mediana([f["inclinacao_graus"] for f in validos]),
        "altura_quadril": _mediana([f[chave_altura] / tronco for f in validos]),
        "dentro_leito": _maioria([f["dentro_leito"] for f in validos]),
        "distancia_leito": _mediana([f[chave_dist] / tronco for f in validos]),
    }


def _velocidades(tempos, feats, tronco):
    """Velocidade vertical para baixo por quadro, em troncos/s (None se invalido)."""
    idx = [i for i, f in enumerate(feats) if f is not None]
    cy = np.array([feats[i]["cy"] for i in idx])
    suave = [np.median(cy[max(0, k - 2):k + 3]) for k in range(len(cy))]
    vel = [None] * len(feats)
    for k in range(1, len(idx)):
        dt = tempos[idx[k]] - tempos[idx[k - 1]]
        if dt > 0:
            vel[idx[k]] = (suave[k] - suave[k - 1]) / dt / tronco
    return vel


def _arredonda(d):
    return {k: round(v, 2) if isinstance(v, float) else v for k, v in d.items()}


def _janela(t_ini, tempos, feats, vel, tronco):
    t_fim = t_ini + JANELA_S
    dentro = [i for i, t in enumerate(tempos) if t_ini <= t < t_fim]
    fim = [i for i in dentro if tempos[i] >= t_fim - JANELA_S * FRACAO_FIM]
    validos = [feats[i] for i in dentro if feats[i] is not None]
    validos_fim = [feats[i] for i in fim if feats[i] is not None]
    frac = len(validos) / len(dentro) if dentro else 0.0
    vels = [vel[i] for i in dentro if vel[i] is not None]
    f = _resumo(validos, tronco)
    f["vel_max"] = max(0.0, max(vels)) if vels else None
    f["frac_validos"] = frac
    fim_resumo = _resumo(validos_fim, tronco)
    para_regra = dict(f, inclinacao_fim=fim_resumo["inclinacao_graus"],
                      altura_fim=fim_resumo["altura_quadril"],
                      dentro_leito_fim=fim_resumo["dentro_leito"])
    return {"t_ini": round(t_ini, 2), "t_fim": round(t_fim, 2),
            "classe": classificar_janela(para_regra), "features": _arredonda(f)}


def gerar_janelas(quadros, poligono, largura, altura):
    """Janelas de 2 s com passo de 0,5 s a partir de t = 0."""
    tempos = [q["t"] for q in quadros]
    if not tempos or tempos[-1] < JANELA_S:
        return []
    feats = [features_do_quadro(q["pontos"], poligono, largura, altura) for q in quadros]
    troncos = [f["tronco_px"] for f in feats if f is not None]
    tronco = float(np.median(troncos)) if troncos else 1.0
    vel = _velocidades(tempos, feats, tronco) if troncos else [None] * len(feats)
    n = int((tempos[-1] - JANELA_S) / PASSO_S + 1e-9) + 1
    return [_janela(i * PASSO_S, tempos, feats, vel, tronco) for i in range(n)]
