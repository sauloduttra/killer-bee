"""A assinatura de dança rasterizada: as constantes que carregam informação,
determinismo multiplataforma travado por golden do raster CRU (não do PNG —
zlib não é contrato), e o PNG emitido continuando um snapshot importável.

Estas constantes eram espelhadas de `site/app/lib/dance.ts`. Esse arquivo foi
removido em 2026-08-06 (D-037) quando o hero deixou de desenhar a dança;
`killerbee/signature.py` virou a única implementação, e este golden virou a
única guarda dela. Mudar um valor aqui muda o corpo de todo .agent.png.
"""

from __future__ import annotations

import hashlib
import math
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from killerbee.cli import main  # noqa: E402
from killerbee.loader import load_pack  # noqa: E402
from killerbee.pngtext import iter_chunks, read_snapshot_from_png  # noqa: E402
from killerbee.signature import (  # noqa: E402
    AMPLITUDE,
    HUB,
    PERSISTENCE_WEIGHT,
    SCALE_RING_MARKS,
    THRESHOLD_WAGGLES,
    _cos,
    _sin,
    field_raster,
    length_from_recruitment,
)

PACK = ROOT / "packs" / "crossfire-review"
MANIFEST = load_pack(PACK)
PROFILES = [p.profile for p in MANIFEST.personas]


# ---------------------------------------------------------------------------
# Os valores que carregam informação — mudá-los muda todo artefato já publicado
# ---------------------------------------------------------------------------


def test_constantes_que_carregam_informacao():
    """Golden das constantes da dança (antes espelhadas de dance.ts, D-037)."""
    assert HUB == 0.18
    assert PERSISTENCE_WEIGHT == {"short": 1.4, "medium": 2.4, "long": 3.6}
    assert THRESHOLD_WAGGLES == {"high": 2, "medium": 4, "low": 7}
    assert AMPLITUDE == 3.2
    assert SCALE_RING_MARKS == (8, 16, 24, 32)


def test_funcao_de_comprimento_e_a_mesma_do_site():
    assert length_from_recruitment(1) == 0.28
    assert length_from_recruitment(32) == 1.0
    assert length_from_recruitment(8) == pytest.approx(0.28 + 0.72 * math.sqrt(7 / 31))
    # clamp nos dois extremos, como o site
    assert length_from_recruitment(0) == length_from_recruitment(1)
    assert length_from_recruitment(99) == length_from_recruitment(32)


def test_trig_propria_concorda_com_libm():
    """A trig própria existe por DETERMINISMO, não por discordância: tem que
    casar com libm além de qualquer efeito visível (1/255 de alpha)."""
    xs = [i * 0.037 - 3.0 for i in range(200)] + [0.0, math.pi, -math.pi, 7.5, -11.2]
    assert max(abs(_sin(x) - math.sin(x)) for x in xs) < 1e-7
    assert max(abs(_cos(x) - math.cos(x)) for x in xs) < 1e-7


# ---------------------------------------------------------------------------
# Propriedades do raster
# ---------------------------------------------------------------------------


def test_raster_tem_forma_e_transparencia():
    raster = field_raster(PROFILES, draw_indices=[0])
    assert len(raster) == 512 * 512 * 4
    assert raster[3] == 0  # canto transparente — o fundo não é pintado
    assert any(raster[i] for i in range(3, len(raster), 4))  # algo foi desenhado


def test_perfis_distintos_desenham_rasters_distintos():
    """Espelho visual do teste de propriedade do profile: perfil distinto ⇒
    definição distinta ⇒ traço distinto."""
    hashes = {
        hashlib.sha256(field_raster(PROFILES, draw_indices=[i])).hexdigest()
        for i in range(len(PROFILES))
    }
    assert len(hashes) == len(PROFILES)


def test_team_cobre_mais_que_um_traco():
    single = field_raster(PROFILES, draw_indices=[0])
    team = field_raster(PROFILES)
    coverage = lambda r: sum(r[i] for i in range(3, len(r), 4))  # noqa: E731
    assert coverage(team) > coverage(single)


def test_campo_vazio_e_erro():
    with pytest.raises(ValueError):
        field_raster([])


def test_golden_do_raster_cru():
    """Determinismo MULTIPLATAFORMA: este teste rodando verde no CI (Linux) e
    na máquina local (Windows) é a prova de que a trig própria cumpriu o
    prometido. O golden é do raster cru de propósito — o PNG passa por zlib,
    cuja saída é estável na prática mas não é contrato entre plataformas."""
    goldens = {
        0: "66289464e328354f119bdbc4be37de96bd0e2f2b82aca88166d226b34471eef8",
        1: "75dc6271966f9bdce5bb286945b5aff03e5f8b9be83628ec96bb123779b7ed8f",
        2: "92a146aa2894da759e999333971c2b10b818b51b145ee4527a6cd1db83960606",
    }
    for index, expected in goldens.items():
        raster = field_raster(PROFILES, draw_indices=[index])
        assert hashlib.sha256(raster).hexdigest() == expected, f"agent[{index}] divergiu"
    team = field_raster(PROFILES)
    assert (
        hashlib.sha256(team).hexdigest()
        == "ccbc83cfa75e4aa7f3a08960c0ddbe9cb38c4dd09491f0989d64a454f7abb485"
    )


# ---------------------------------------------------------------------------
# O PNG emitido continua um snapshot importável
# ---------------------------------------------------------------------------


def _png_header_and_order(png: bytes) -> tuple[int, int, list[bytes]]:
    order = []
    width = height = 0
    for chunk_type, data in iter_chunks(png):
        order.append(chunk_type)
        if chunk_type == b"IHDR":
            width, height = struct.unpack_from(">II", data, 0)
    return width, height, order


def test_build_emite_png_512_com_text_antes_do_idat_e_round_trip(tmp_path):
    assert main(["build", str(PACK), "--out", str(tmp_path)]) == 0
    out = tmp_path / "crossfire-review"

    for name in ("forager", "adversary", "guard"):
        png = (out / f"{name}.agent.png").read_bytes()
        width, height, order = _png_header_and_order(png)
        assert (width, height) == (512, 512)
        assert order.index(b"tEXt") < order.index(b"IDAT")  # exigência do decoder upstream
        # o corpo mudou; o snapshot embutido NÃO — round-trip idêntico ao .json
        import json

        agent = json.loads((out / f"{name}.agent.json").read_text(encoding="utf-8"))
        assert read_snapshot_from_png(png, "buzz_agent_snapshot") == agent
        # cap de import do desktop: 10 MiB para .agent.png (PROTOCOL-NOTES §10.8)
        assert len(png) <= 10 * 1024 * 1024
        # O corpo é ADOTADO como avatar no import quando o manifesto não traz
        # avatar inline (import.rs:242-261) — nosso caso. Os limites dessa
        # adoção são MENORES que o cap de import (snapshot_avatar.rs:5-7):
        # lado > 2048 px FALHA o import; inline > 2 MiB não vira avatar.
        assert width <= 2048 and height <= 2048
        assert len(png) <= 2 * 1024 * 1024

    team_png = (out / "crossfire-review.team.png").read_bytes()
    width, height, order = _png_header_and_order(team_png)
    assert (width, height) == (512, 512)
    assert order.index(b"tEXt") < order.index(b"IDAT")
    assert len(team_png) <= 50 * 1024 * 1024
