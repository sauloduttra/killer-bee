"""NCD do catálogo: a fórmula, a extração de corpo e as propriedades do detector.

Regra do repo (D-032): teste novo se verifica MATANDO a mutação correspondente.
Cada teste abaixo diz, no docstring, qual mutação ele mata.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from ncd_catalog import (  # noqa: E402
    bottom_k_overlap,
    load_catalog_bodies,
    ncd_from_sizes,
    pairwise_ncd,
    strip_frontmatter,
    zstd_size_bytes,
)

# ── fórmula pura ─────────────────────────────────────────────────────────────


def test_formula_valor_exato_assimetrico():
    """Mata: trocar min por max (daria (90-80)/70, negativo) ou inverter o
    denominador. Com c_x=70, c_y=80, c_xy=90: (90-70)/80 = 0.25 exato."""
    assert ncd_from_sizes(70, 80, 90) == pytest.approx(0.25)


def test_formula_simetrica_nos_argumentos_singulares():
    """Mata: usar c_x onde a fórmula pede min/max (quebraria a simetria x↔y)."""
    assert ncd_from_sizes(70, 80, 90) == ncd_from_sizes(80, 70, 90)


def test_formula_rejeita_tamanho_nao_positivo():
    """Mata: remover o guarda (0 viraria divisão por zero ou NCD absurdo)."""
    with pytest.raises(ValueError, match="não-positivo"):
        ncd_from_sizes(0, 80, 90)
    with pytest.raises(ValueError, match="não-positivo"):
        ncd_from_sizes(70, 80, -1)


# ── propriedades com o compressor real ───────────────────────────────────────


def test_identidade_fica_perto_de_zero():
    """NCD(x,x) pequeno com zstd real. Mata: concatenar errado (x+x comprime
    quase como x; se c_xy usasse 2*c_x a identidade subiria para ~1)."""
    x = ("um prompt de persona com estrutura, papel e regras de estilo. " * 40).encode()
    ncd_xx = ncd_from_sizes(zstd_size_bytes(x), zstd_size_bytes(x), zstd_size_bytes(x + x))
    assert ncd_xx < 0.1


def test_ordenacao_similar_antes_de_dissimilar():
    """Par quase-idêntico tem NCD menor que par sem relação. Mata: inverter o
    sinal da fórmula ou a ordenação do ranking."""
    base = ("Você é um revisor de código quantitativo; cite arquivo e linha. " * 30).encode()
    quase = base.replace(b"quantitativo", "estatístico".encode())
    outro = ("Receita de bolo: farinha, ovos, açúcar; asse por quarenta minutos. " * 30).encode()
    bodies = {"a/base": base, "b/quase": quase, "c/outro": outro}
    pairs = pairwise_ncd(bodies, zstd_size_bytes)
    assert (pairs[0][1], pairs[0][2]) == ("a/base", "b/quase")
    assert pairs[0][0] < pairs[-1][0]


def test_pairwise_e_deterministico():
    """Duas execuções, bytes idênticos de resultado. Mata: introduzir estado
    (nível variável, dicionário treinado, ordem de dict não-ordenada)."""
    bodies = {
        "p/a": b"x" * 500 + b"conteudo alfa " * 20,
        "p/b": b"y" * 500 + b"conteudo beta " * 20,
        "p/c": b"z" * 500 + b"conteudo gama " * 20,
    }
    assert pairwise_ncd(bodies, zstd_size_bytes) == pairwise_ncd(bodies, zstd_size_bytes)


# ── extração de corpo ────────────────────────────────────────────────────────


def test_strip_frontmatter_devolve_so_o_corpo():
    """Mata: devolver o arquivo inteiro (o frontmatter inflaria a similaridade
    estrutural entre todas as personas)."""
    text = "---\nname: x\nmodel: 'a:b'\n---\n\nO corpo do prompt.\n"
    assert strip_frontmatter(text, origin="t") == "O corpo do prompt."


@pytest.mark.parametrize(
    ("text", "erro"),
    [
        ("sem frontmatter\n", "sem frontmatter"),
        ("---\nname: x\n", "não fechado"),
        ("---\nname: x\n---\n\n  \n", "corpo vazio"),
    ],
)
def test_strip_frontmatter_falha_ruidoso(text: str, erro: str):
    """Mata: qualquer caminho silencioso — corpo vazio comparado renderia
    NCD sem sentido com aparência de número."""
    with pytest.raises(ValueError, match=erro):
        strip_frontmatter(text, origin="t")


# ── carga do catálogo real ───────────────────────────────────────────────────


def test_catalogo_real_carrega_e_exclui_template():
    """O catálogo do repo carrega inteiro e TEMPLATE fica fora. Mata: remover
    a exclusão do TEMPLATE (o glob acharia 52) ou quebrar o parse de qualquer
    persona publicada."""
    bodies = load_catalog_bodies(ROOT / "packs")
    assert len(bodies) == 51
    assert not any(key.startswith("TEMPLATE/") for key in bodies)


def test_bottom_k_overlap_e_fracao():
    """Mata: dividir pelo tamanho errado ou comparar rankings inteiros."""
    a = [(0.1, "x", "y"), (0.2, "x", "z"), (0.9, "y", "z")]
    b = [(0.1, "x", "y"), (0.3, "y", "z"), (0.8, "x", "z")]
    assert bottom_k_overlap(a, b, 2) == pytest.approx(0.5)
    with pytest.raises(ValueError, match="positivo"):
        bottom_k_overlap(a, b, 0)
