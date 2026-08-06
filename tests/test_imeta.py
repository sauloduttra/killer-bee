"""imeta: a forma que o chat do Buzz aceita, emitida offline por artefato.

Golden shape contra o e2e do upstream (agent-snapshot-recipient.spec.ts:118-126
@ ed4b3e7a) e concordância com o catálogo: o `x` do imeta É o sha256 publicado,
que É o hash dos bytes que o build grava.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from killerbee.cli import main  # noqa: E402
from killerbee.imeta import imeta_tag, mime_for  # noqa: E402

PACK = ROOT / "packs" / "crossfire-review"


def test_forma_golden_do_e2e_upstream():
    """Os seis itens, na ordem e no formato 'chave valor' do spec :120-125."""
    tag = imeta_tag(
        url="https://mock.relay/media/aa.json",
        mime="application/json",
        sha256_hex="a" * 64,
        size_bytes=1234,
        filename="e2e-agent.agent.json",
    )
    assert tag == [
        "imeta",
        "url https://mock.relay/media/aa.json",
        "m application/json",
        f"x {'a' * 64}",
        "size 1234",
        "filename e2e-agent.agent.json",
    ]


@pytest.mark.parametrize(
    ("kwargs", "motivo"),
    [
        ({"url": "ftp://x/y.json"}, "url não-http"),
        ({"sha256_hex": "abc"}, "sha curto"),
        ({"sha256_hex": "A" * 64}, "hex maiúsculo — o regex do card é minúsculo"),
        ({"size_bytes": 0}, "tamanho zero"),
        ({"filename": "com espaço.json"}, "espaço quebra o par chave-valor"),
    ],
)
def test_entrada_invalida_levanta_valueerror(kwargs, motivo):
    base = {
        "url": "https://x/y.json",
        "mime": "application/json",
        "sha256_hex": "a" * 64,
        "size_bytes": 1,
        "filename": "y.json",
    }
    with pytest.raises(ValueError):
        imeta_tag(**{**base, **kwargs})


def test_mime_por_sufixo():
    assert mime_for("forager.agent.json") == "application/json"
    assert mime_for("crossfire-review.team.png") == "image/png"
    with pytest.raises(ValueError):
        mime_for("acp-rules.toml")


# ---------------------------------------------------------------------------
# Catálogo: com a flag, todo arquivo carrega imeta consistente; sem, nenhum
# ---------------------------------------------------------------------------


def _all_file_entries(catalog: dict) -> list[dict]:
    entries = []
    for pack in catalog["packs"]:
        for persona in pack["personas"]:
            entries.extend(persona["files"])
        for team in pack["teams"]:
            entries.extend(team["files"])
    return entries


def test_catalogo_com_flag_emite_imeta_consistente(tmp_path):
    out_file = tmp_path / "catalog.json"
    assert (
        main(
            [
                "catalog",
                "--packs",
                str(PACK.parent),
                "--out",
                str(out_file),
                "--imeta-base-url",
                "https://killer-bee-4rn.pages.dev/",
            ]
        )
        == 0
    )
    catalog = json.loads(out_file.read_text(encoding="utf-8"))
    entries = _all_file_entries(catalog)
    assert entries, "catálogo sem arquivos — nada para ter imeta"
    for entry in entries:
        tag = entry["imeta"]
        assert tag[0] == "imeta" and len(tag) == 6
        # barra final da base não pode duplicar; o caminho é o que o site serve
        assert tag[1] == (
            f"url https://killer-bee-4rn.pages.dev/downloads/crossfire-review/{entry['name']}"
        )
        assert tag[3] == f"x {entry['sha256']}"
        assert tag[4] == f"size {entry['bytes']}"
        assert tag[5] == f"filename {entry['name']}"


def test_imeta_x_bate_com_os_bytes_do_build(tmp_path):
    """A cadeia inteira: bytes gravados → sha256 do catálogo → x do imeta."""
    assert main(["build", str(PACK), "--out", str(tmp_path / "dist")]) == 0
    out_file = tmp_path / "catalog.json"
    assert (
        main(
            [
                "catalog",
                "--packs",
                str(PACK.parent),
                "--out",
                str(out_file),
                "--imeta-base-url",
                "https://example.org",
            ]
        )
        == 0
    )
    catalog = json.loads(out_file.read_text(encoding="utf-8"))
    dist = tmp_path / "dist" / "crossfire-review"
    for entry in _all_file_entries(catalog):
        raw = (dist / entry["name"]).read_bytes()
        assert entry["imeta"][3] == f"x {hashlib.sha256(raw).hexdigest()}", entry["name"]


def test_catalogo_sem_flag_nao_tem_imeta(tmp_path):
    out_file = tmp_path / "catalog.json"
    assert main(["catalog", "--packs", str(PACK.parent), "--out", str(out_file)]) == 0
    catalog = json.loads(out_file.read_text(encoding="utf-8"))
    for entry in _all_file_entries(catalog):
        assert "imeta" not in entry
