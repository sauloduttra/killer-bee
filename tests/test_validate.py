"""Validação: as regras que existem porque o IMPORT do app as aplica.

O princípio (auditoria 2026-08-06): tudo que `killerbee validate` aprova tem
que passar no import do Buzz Desktop — um pack "válido" que o app rejeita é a
pior espécie de bug, porque explode na mão do usuário final.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Sem isto o módulo só importa quando outro arquivo de teste insere o path
# primeiro — rodar este arquivo sozinho falhava na coleção.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killerbee.model import PackManifest, Persona, Team
from killerbee.validate import validate_pack


def make_persona(name: str = "bot", **overrides) -> Persona:
    defaults = dict(
        name=name,
        display_name="Bot",
        description="A bot.",
        system_prompt="You are Bot.",
        model="anthropic:claude-sonnet-5",
    )
    defaults.update(overrides)
    return Persona(**defaults)


def make_manifest(**overrides) -> PackManifest:
    defaults = dict(
        name="demo-pack",
        version="0.1.0",
        license="Apache-2.0",
        personas=(make_persona(),),
    )
    defaults.update(overrides)
    return PackManifest(**defaults)


def errors_of(manifest: PackManifest) -> str:
    return "\n".join(validate_pack(manifest))


def test_pack_valido_nao_tem_erros():
    assert validate_pack(make_manifest()) == []


# ---------------------------------------------------------------------------
# trim, não falsy — o que o app valida com .trim(), nós validamos com .strip()
# ---------------------------------------------------------------------------


def test_display_name_so_de_espacos_e_rejeitado():
    """agent_snapshot.rs:400-406 valida com trim(); checagem falsy aceitava
    '   ' e o snapshot emitido era rejeitado NO IMPORT, não no validate."""
    manifest = make_manifest(personas=(make_persona(display_name="   "),))
    assert "display_name" in errors_of(manifest)


def test_description_so_de_espacos_e_rejeitada():
    manifest = make_manifest(personas=(make_persona(description=" \t "),))
    assert "description" in errors_of(manifest)


def test_team_name_so_de_espacos_e_rejeitado():
    manifest = make_manifest(
        teams=(Team(id="t1", name="  ", members=("bot",)),),
    )
    assert "team_snapshot.rs" in errors_of(manifest)


# ---------------------------------------------------------------------------
# Slug de persona: a gramática REAL do relay (handlers/ingest.rs:1130-1148)
# ---------------------------------------------------------------------------


def test_slug_com_ponto_e_rejeitado():
    """A gramática do d-tag é ^[a-z0-9][a-z0-9_-]{0,63}$ — sem ponto. O regex
    anterior aceitava '.', que o relay rejeita."""
    manifest = make_manifest(personas=(make_persona(name="my.bot"),))
    assert "gramática de slug" in errors_of(manifest)


def test_slug_maiusculo_e_rejeitado():
    manifest = make_manifest(personas=(make_persona(name="MyBot"),))
    assert "gramática de slug" in errors_of(manifest)


def test_nome_de_dispositivo_windows_e_rejeitado():
    """'nul.agent.json' não é um arquivo comum em NTFS."""
    manifest = make_manifest(personas=(make_persona(name="nul"),))
    assert "reservado no Windows" in errors_of(manifest)


# ---------------------------------------------------------------------------
# team.id vira nome de arquivo — restrição NOSSA, documentada (D-023)
# ---------------------------------------------------------------------------


def test_team_id_com_path_traversal_e_rejeitado():
    """`id: ../x` escreveria fora de dist/ — passava na validação anterior."""
    manifest = make_manifest(teams=(Team(id="../x", name="T", members=("bot",)),))
    assert "[a-z0-9._-]" in errors_of(manifest)


def test_team_id_com_dois_pontos_e_rejeitado():
    """O upstream aceita ':' no d-tag de team (handlers/ingest.rs:1159-1162);
    nós não, porque ':' é ilegal em nome de arquivo no Windows. Restrição
    consciente e documentada — não uma cópia errada da regra upstream."""
    manifest = make_manifest(teams=(Team(id="builtin-team:welcome", name="T", members=("bot",)),))
    assert "[a-z0-9._-]" in errors_of(manifest)


def test_team_id_normal_passa():
    manifest = make_manifest(teams=(Team(id="crossfire-review", name="T", members=("bot",)),))
    assert validate_pack(manifest) == []


# ---------------------------------------------------------------------------
# channels: "all" sozinho ou UUIDs — o que filter.rs aceita
# ---------------------------------------------------------------------------


def test_channel_uuid_valido_passa():
    manifest = make_manifest(
        personas=(make_persona(channels=("123e4567-e89b-42d3-a456-426614174000",)),)
    )
    assert validate_pack(manifest) == []


def test_channel_que_nao_e_uuid_e_rejeitado():
    manifest = make_manifest(personas=(make_persona(channels=("general",)),))
    assert "não é UUID" in errors_of(manifest)


def test_all_misturado_com_uuid_e_rejeitado():
    manifest = make_manifest(
        personas=(make_persona(channels=("all", "123e4567-e89b-42d3-a456-426614174000")),)
    )
    assert "misturado" in errors_of(manifest)
