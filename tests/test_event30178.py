"""L3 offline: o 30178 não assinado, a projeção sanitizada, e o schema.

Três contratos, cada um com dono: o ENVELOPE é do relay (ingest.rs:1163,
:1868 — d-tag, shared exato, 256 KiB); o CORPO é nosso e está publicado em
schema/kind-30178-content.schema.json; a PROJEÇÃO tem a propriedade que a
justifica — é o AgentSnapshot menos exatamente {respondTo,
respondToAllowlist}, e nada mais (NIP-AP.md:242).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from killerbee.cli import main  # noqa: E402
from killerbee.event30178 import (  # noqa: E402
    member_projection,
    team_content,
    unsigned_event,
)
from killerbee.loader import load_pack  # noqa: E402
from killerbee.model import Team  # noqa: E402
from killerbee.snapshot import agent_snapshot  # noqa: E402
from killerbee.validate import EVENT_CONTENT_MAX_BYTES  # noqa: E402

PACK = ROOT / "packs" / "crossfire-review"
SCHEMA = json.loads(
    (ROOT / "schema" / "kind-30178-content.schema.json").read_text(encoding="utf-8")
)
MANIFEST = load_pack(PACK)
TEAM = MANIFEST.teams[0]


def test_o_schema_e_um_draft_2020_12_valido():
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_projecao_e_snapshot_menos_exatamente_os_dois_campos():
    """A propriedade que justifica o desenho: nenhum campo além dos dois some,
    nenhum campo novo aparece — um leitor reconstrói um .agent.json."""
    for persona in MANIFEST.personas:
        snapshot = agent_snapshot(persona)
        projection = member_projection(persona)
        assert set(snapshot) == set(projection)  # topo intacto
        removed = set(snapshot["definition"]) - set(projection["definition"])
        assert removed <= {"respondTo", "respondToAllowlist"}
        assert "respondTo" not in projection["definition"]
        assert "respondToAllowlist" not in projection["definition"]
        for key, value in projection["definition"].items():
            assert snapshot["definition"][key] == value  # nada é alterado, só removido
        assert projection["profile"] == snapshot["profile"]
        assert projection["memory"] == {"level": "none", "entries": []}


def test_corpo_do_team_real_valida_contra_o_schema_publicado():
    content = team_content(TEAM, MANIFEST)
    jsonschema.validate(content, SCHEMA)
    assert content["v"] == 1
    assert len(content["members"]) == 3
    # ordem dos membros é a ordem do manifesto — o schema não vê ordem
    names = [m["profile"]["displayName"] for m in content["members"]]
    assert names == ["Forager", "Adversary", "Guard"]


def test_corpo_com_respondto_e_rejeitado_pelo_schema():
    """O schema TRAVA a sanitização: um corpo com o campo banido não valida."""
    content = team_content(TEAM, MANIFEST)
    content["members"][0]["definition"]["respondTo"] = "anyone"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(content, SCHEMA)


def test_envelope_do_evento_nao_assinado():
    event = unsigned_event(TEAM, MANIFEST)
    assert event["kind"] == 30178
    assert event["pubkey"] == ""  # preencher é papel do signatário
    assert event["created_at"] == 0  # template determinístico; sem relógio
    assert "id" not in event and "sig" not in event
    assert event["tags"][0] == ["d", TEAM.id]
    assert ["shared", "true"] in event["tags"]  # forma EXATA de 2 elementos
    # o content é string JSON compacta que re-parseia no corpo validado
    body = json.loads(event["content"])
    jsonschema.validate(body, SCHEMA)
    assert '": ' not in event["content"]  # compacto de verdade


def test_unshared_omite_a_tag_inteira():
    event = unsigned_event(TEAM, MANIFEST, shared=False)
    assert [t for t in event["tags"] if t and t[0] == "shared"] == []


def test_content_do_team_real_cabe_no_relay():
    event = unsigned_event(TEAM, MANIFEST)
    assert len(event["content"].encode("utf-8")) <= EVENT_CONTENT_MAX_BYTES


@pytest.mark.parametrize(
    ("team_id", "motivo"),
    [
        ("x" * 65, "65 chars — o relay corta em 64"),
        ("tem espaco", "whitespace"),
        ("tab\tid", "control char"),
        ("", "vazio — colapsaria no coordinate ''"),
    ],
)
def test_d_tag_invalida_levanta_valueerror(team_id, motivo):
    team = Team(id=team_id, name="X", members=("forager",))
    with pytest.raises(ValueError):
        unsigned_event(team, MANIFEST)


def test_determinismo_do_evento():
    a = unsigned_event(TEAM, MANIFEST)
    b = unsigned_event(TEAM, MANIFEST)
    assert a == b


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_event_emite_arquivo_por_team(tmp_path, capsys):
    assert main(["event", str(PACK), "--out", str(tmp_path)]) == 0
    out_file = tmp_path / "crossfire-review" / "crossfire-review.30178.json"
    assert out_file.is_file()
    event = json.loads(out_file.read_text(encoding="utf-8"))
    jsonschema.validate(json.loads(event["content"]), SCHEMA)
    out = capsys.readouterr().out
    assert "NÃO ASSINADO" in out


def test_cli_event_unshared(tmp_path):
    assert main(["event", str(PACK), "--out", str(tmp_path), "--unshared"]) == 0
    event = json.loads(
        (tmp_path / "crossfire-review" / "crossfire-review.30178.json").read_text(encoding="utf-8")
    )
    assert [t for t in event["tags"] if t and t[0] == "shared"] == []


def test_cli_event_em_pack_sem_team_sai_um(tmp_path, capsys):
    """Um pack só de personas não tem o que projetar em 30178."""
    import shutil

    solo = tmp_path / "solo"
    shutil.copytree(PACK, solo)
    manifest_text = (solo / "killerbee.yaml").read_text(encoding="utf-8")
    (solo / "killerbee.yaml").write_text(
        manifest_text[: manifest_text.index("teams:")], encoding="utf-8"
    )
    assert main(["event", str(solo), "--out", str(tmp_path / "out")]) == 1
    assert "não tem teams" in capsys.readouterr().err
