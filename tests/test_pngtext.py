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


# ---------------------------------------------------------------------------
# Endurecimento do leitor — `killerbee inspect` aceita arquivo de terceiro
# ---------------------------------------------------------------------------


def test_png_truncado_da_valueerror_nao_struct_error():
    """PNG cortado no meio de um chunk: ValueError com contexto, nunca
    struct.error cru (contrato §2.3 do AUTONOMIA)."""
    png = build_png_with_text("k", "eA==")
    with pytest.raises(ValueError, match="truncado"):
        list(iter_chunks(png[:20]))


def test_chunk_com_length_mentiroso_e_rejeitado():
    """length que aponta além do buffer é lixo ou ataque — erro nomeado."""
    png = bytearray(build_png_with_text("k", "eA=="))
    # Corrompe o length do IHDR (4 bytes big-endian logo após a assinatura).
    png[8:12] = struct.pack(">I", 2**24)
    with pytest.raises(ValueError, match=r"truncado|declara"):
        list(iter_chunks(bytes(png)))


def test_iteracao_para_no_iend():
    """Bytes anexados após o IEND não são chunks — o formato termina ali."""
    png = build_png_with_text("k", "eA==") + b"\x00" * 64
    types = [t for t, _ in iter_chunks(png)]
    assert types[-1] == b"IEND"


def test_texto_fora_de_latin1_da_valueerror_com_contexto():
    with pytest.raises(ValueError, match="Latin-1"):
        build_png_with_text("k", "snapshot com emoji \U0001f41d")
