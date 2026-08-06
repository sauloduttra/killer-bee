"""PNG mínimo com chunk tEXt — o corpo de um `.agent.png` / `.team.png`. Puro.

Contrato do decoder upstream, verificado @ ed4b3e7a:

- chunk **tEXt** (não iTXt, não zTXt): o leitor usa só
  `info.uncompressed_latin1_text` (agent_snapshot.rs:362, team_snapshot.rs:156)
- keyword `buzz_agent_snapshot` (agent_snapshot.rs:53) /
  `buzz_team_snapshot` (team_snapshot.rs:49)
- payload = base64 STANDARD do JSON do manifesto (agent_snapshot.rs:324)
- o chunk tem que vir **antes do IDAT** (media_snapshot_png.rs:55-58)

Implementado à mão sobre zlib/struct da biblioteca padrão — sem Pillow — porque
o que precisamos é exatamente um PNG válido com um chunk de texto na posição
certa, e 60 linhas auditáveis valem mais que uma dependência de 10 MB.
"""

from __future__ import annotations

import base64
import json
import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Um chunk PNG: length + type + data + CRC32(type + data)."""
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def build_png_with_text(
    keyword: str,
    text: str,
    width_px: int = 1,
    height_px: int = 1,
    rgba: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> bytes:
    """PNG RGBA sólido com um chunk tEXt entre IHDR e IDAT.

    O upstream usa 1x1 transparente como corpo do `.team.png`; o default aqui é
    o mesmo. keyword segue a regra do PNG: 1 a 79 bytes, Latin-1. O texto também
    precisa ser Latin-1 — base64 é ASCII, então sempre passa.
    """
    if not 1 <= len(keyword) <= 79:
        raise ValueError(f"keyword tEXt deve ter 1..=79 bytes; '{keyword}' tem {len(keyword)}")
    if width_px < 1 or height_px < 1:
        raise ValueError(f"dimensões inválidas: {width_px}x{height_px}")

    # IHDR: bit depth 8, color type 6 (RGBA), compressão/filtro/entrelace 0.
    ihdr = struct.pack(">IIBBBBB", width_px, height_px, 8, 6, 0, 0, 0)
    text_data = keyword.encode("latin-1") + b"\x00" + text.encode("latin-1")
    # Cada linha da imagem: 1 byte de filtro (0 = None) + pixels RGBA.
    raw_row = b"\x00" + bytes(rgba) * width_px
    idat = zlib.compress(raw_row * height_px)

    return (
        PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"tEXt", text_data)  # antes do IDAT — exigência do decoder
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )


def snapshot_png(keyword: str, snapshot: dict) -> bytes:
    """Embala um snapshot (dict JSON) num PNG portátil, como o app faz."""
    payload = base64.standard_b64encode(
        json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return build_png_with_text(keyword, payload)


# ── Leitura (para testes de round-trip; o app não precisa disto) ────────────


def iter_chunks(png: bytes):
    """Itera (tipo, dados) validando assinatura e CRC de cada chunk."""
    if png[:8] != PNG_SIGNATURE:
        raise ValueError("não é PNG: assinatura errada")
    offset = 8
    while offset < len(png):
        (length,) = struct.unpack_from(">I", png, offset)
        chunk_type = png[offset + 4 : offset + 8]
        data = png[offset + 8 : offset + 8 + length]
        (crc,) = struct.unpack_from(">I", png, offset + 8 + length)
        if crc != zlib.crc32(chunk_type + data) & 0xFFFFFFFF:
            raise ValueError(f"CRC inválido no chunk {chunk_type!r}")
        yield chunk_type, data
        offset += 12 + length


def read_snapshot_from_png(png: bytes, keyword: str) -> dict:
    """Round-trip: extrai e decodifica o snapshot de um PNG gerado por nós."""
    for chunk_type, data in iter_chunks(png):
        if chunk_type != b"tEXt":
            continue
        found_keyword, _, payload = data.partition(b"\x00")
        if found_keyword.decode("latin-1") == keyword:
            return json.loads(base64.standard_b64decode(payload))
    raise ValueError(f"nenhum chunk tEXt com keyword '{keyword}'")
