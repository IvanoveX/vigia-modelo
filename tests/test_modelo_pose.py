import pytest

from vigia_modelo import modelo_pose


def test_recusa_e_apaga_arquivo_divergente(tmp_path, monkeypatch):
    def baixar_falso(url, destino):
        destino.write_bytes(b"conteudo errado")

    monkeypatch.setattr(modelo_pose.urllib.request, "urlretrieve", baixar_falso)
    with pytest.raises(ValueError):
        modelo_pose.baixar_modelo("lite", tmp_path)
    assert not list(tmp_path.glob("*.task"))
