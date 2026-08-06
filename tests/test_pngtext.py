"""PNG portátil: estrutura, posição do chunk e round-trip."""

from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killerbee.pngtext import (
    PNG_SIGNATURE,
    build_png_with_text,
    iter_chunks,
    read_snapshot_from_png,
    snapshot_png,
)


def test_estrutura_basica_e_crc():
    png = build_png_with_text("buzz_agent_snapshot", "aGVsbG8=")
    assert png.startswith(PNG_SIGNATURE)
    # iter_chunks valida o CRC de cada chunk; basta consumir sem exceção.
    types = [t for t, _ in iter_chunks(png)]
    assert types == [b"IHDR", b"tEXt", b"IDAT", b"IEND"]


def test_text_vem_antes_do_idat():
    """Exigência do decoder upstream: media_snapshot_png.rs:55-58."""
    png = build_png_with_text("buzz_team_snapshot", "eA==")
    types = [t for t, _ in iter_chunks(png)]
    assert types.index(b"tEXt") < types.index(b"IDAT")


def test_idat_decodifica_para_a_imagem_declarada():
    """O PNG tem que ser imagem VÁLIDA, não só transporte: 1 byte de filtro
    por linha + RGBA por pixel."""
    width, height = 3, 2
    png = build_png_with_text("k", "eA==", width_px=width, height_px=height)
    idat = next(d for t, d in iter_chunks(png) if t == b"IDAT")
    raw = zlib.decompress(idat)
    assert len(raw) == height * (1 + 4 * width)


def test_ihdr_correto():
    png = build_png_with_text("k", "eA==", width_px=5, height_px=7)
    ihdr = next(d for t, d in iter_chunks(png) if t == b"IHDR")
    width, height, depth, color_type = struct.unpack(">IIBB", ihdr[:10])
    assert (width, height, depth, color_type) == (5, 7, 8, 6)  # RGBA 8-bit


def test_round_trip_do_snapshot():
    snapshot = {
        "format": "buzz-agent-snapshot",
        "version": 1,
        "definition": {"name": "Tést ünïcode 🐝", "systemPrompt": "x" * 10_000},
    }
    png = snapshot_png("buzz_agent_snapshot", snapshot)
    assert read_snapshot_from_png(png, "buzz_agent_snapshot") == snapshot


def test_keyword_fora_do_limite_png_e_erro():
    with pytest.raises(ValueError, match=r"1\.\.=79"):
        build_png_with_text("", "eA==")
    with pytest.raises(ValueError, match=r"1\.\.=79"):
        build_png_with_text("k" * 80, "eA==")


def test_keyword_errada_no_round_trip_e_erro_claro():
    png = snapshot_png("buzz_agent_snapshot", {"a": 1})
    with pytest.raises(ValueError, match="buzz_team_snapshot"):
        read_snapshot_from_png(png, "buzz_team_snapshot")
