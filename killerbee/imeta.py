"""Bloco imeta pronto por artefato. Puro: valores → tag, sem I/O.

A forma é a que o desktop do Buzz emite e consome quando um snapshot viaja
num canal de chat (desktop/tests/e2e/agent-snapshot-recipient.spec.ts:118-126
@ ed4b3e7a; o descriptor com o MIME em :74-82):

    ["imeta", "url …", "m …", "x <sha256>", "size …", "filename …"]

e o conteúdo da mensagem é o link markdown ``[filename](url)`` (spec :117).
O card de snapshot no chat RECUSA imeta sem sha256 de 64 hex
(markdownFileCard.ts:101-103) — o ``x`` não é decoração, é o que habilita o
botão Import. O catálogo já publica o hash; este módulo o embala na forma
que qualquer canal Buzz aceita colar.

Publicar o EVENTO continua fora: assinar exige chave (🔴). O bloco pronto é
o máximo que dá para emitir offline, e é exatamente o que falta para um pack
ser postável como card importável.
"""

from __future__ import annotations

import re

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")

# MIME por sufixo dos artefatos que o catálogo lista. IANA: application/json
# (RFC 8259), image/png (RFC 2083). O upstream usa "application/json" para
# .agent.json no descriptor citado acima.
MIME_BY_SUFFIX = {
    ".json": "application/json",
    ".png": "image/png",
}


def mime_for(filename: str) -> str:
    """MIME do artefato pelo sufixo. Sufixo desconhecido é erro, não chute."""
    for suffix, mime in MIME_BY_SUFFIX.items():
        if filename.endswith(suffix):
            return mime
    raise ValueError(
        f"sem MIME conhecido para '{filename}' — sufixos aceitos: {sorted(MIME_BY_SUFFIX)}"
    )


def imeta_tag(
    *,
    url: str,
    mime: str,
    sha256_hex: str,
    size_bytes: int,
    filename: str,
) -> list[str]:
    """A tag imeta completa, na ordem do e2e upstream.

    Entrada inválida levanta ValueError dizendo qual valor e por quê — um
    imeta com `x` malformado produziria um card com Import desabilitado e
    nenhuma mensagem de erro para o autor do pack.
    """
    if not url.startswith(("https://", "http://")):
        raise ValueError(f"url deve ser http(s) absoluta, veio {url!r}")
    if not _SHA256_HEX.match(sha256_hex):
        raise ValueError(
            f"sha256_hex deve ter 64 hex minúsculos, veio {sha256_hex!r} — "
            "markdownFileCard.ts:101-103 recusa qualquer outra coisa"
        )
    if size_bytes <= 0:
        raise ValueError(f"size_bytes deve ser positivo, veio {size_bytes}")
    if not filename or " " in filename:
        raise ValueError(f"filename vazio ou com espaço: {filename!r}")
    return [
        "imeta",
        f"url {url}",
        f"m {mime}",
        f"x {sha256_hex}",
        f"size {size_bytes}",
        f"filename {filename}",
    ]
