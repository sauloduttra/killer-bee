"""Camada L3 offline: evento kind 30178 NÃO ASSINADO + projeção de membro.

O relay especifica só o envelope — "The content schema is defined by the
client that publishes it" (docs/nips/NIP-AP.md:223 @ ed4b3e7a). A projeção
de membro não existe em lugar nenhum do upstream (a única forma abençoada é
a fixture ``{"v":1,"name":...,"members":[]}``, com members VAZIO, em
e2e_team_catalog.rs:35 e ingest.rs:4111). Este módulo define a projeção do
Killer Bee — publicada como JSON Schema em
``schema/kind-30178-content.schema.json`` — e emite o evento pronto para
assinar. Assinar e publicar ficam FORA: exigem chave, e chave é 🔴.

O desenho, registrado em DECISIONS D-029:

- **Corpo** = ``{"v": 1, "name", "description"?, "instructions"?, "members"}``
  — extensão da fixture upstream, campos de team sanitizados como a
  NIP-AP.md:242 manda.
- **Projeção de membro** = o AgentSnapshot que o emissor já produz
  (snapshot.py) MENOS ``respondTo`` e ``respondToAllowlist``. A NIP-AP:242
  bane os pubkeys da allowlist por texto; ``respondTo`` sem a lista
  afirmaria uma política que o leitor não consegue reconstruir, então os
  dois saem juntos. Env vars, paths e ids locais o emissor nunca escreveu.
  O RESTO mantém a forma do snapshot DE PROPÓSITO: um leitor grava a
  projeção como ``.agent.json`` e o desktop importa sem tradução — os oito
  campos obrigatórios do parse (PROTOCOL-NOTES §10.1) estão presentes, e os
  removidos têm ``#[serde(default)]``.
- **Envelope**: ``tags = [["d", <team.id>]]`` + ``["shared","true"]``
  opcional na forma EXATA de 2 elementos (ingest.rs:1163); ``d`` não-vazio,
  ≤ 64 caracteres, sem control chars nem whitespace; content compacto
  ≤ 256 KiB (ingest.rs:1868). Violação levanta ValueError aqui — falha
  barulhenta no build é mais barata que ``invalid:`` do relay na demo.
- **``created_at = 0`` por default.** Evento não assinado é template; quem
  assina carimba o relógio. O emissor não lê relógio (AUTONOMIA §2.5).
"""

from __future__ import annotations

import json

from .model import PackManifest, Persona, Team
from .snapshot import agent_snapshot
from .validate import EVENT_CONTENT_MAX_BYTES

KIND_TEAM_CATALOG = 30178
CONTENT_VERSION = 1

_SANITIZED_OUT = ("respondTo", "respondToAllowlist")
_D_TAG_MAX_CHARS = 64


def member_projection(persona: Persona) -> dict:
    """AgentSnapshot menos o que a NIP-AP:242 sanitiza. Pura."""
    snapshot = agent_snapshot(persona)
    definition = {k: v for k, v in snapshot["definition"].items() if k not in _SANITIZED_OUT}
    return {**snapshot, "definition": definition}


def team_content(team: Team, manifest: PackManifest) -> dict:
    """O corpo (ainda dict) do 30178: v + campos de team + projeções em ordem."""
    members = []
    for member_name in team.members:
        persona = manifest.persona_by_name(member_name)
        if persona is None:
            raise ValueError(f"team '{team.id}' referencia persona inexistente '{member_name}'")
        members.append(member_projection(persona))
    if not members:
        raise ValueError(f"team '{team.id}' precisa de ao menos 1 membro")

    content: dict = {"v": CONTENT_VERSION, "name": team.name}
    if team.description:
        content["description"] = team.description
    if team.instructions:
        content["instructions"] = team.instructions
    content["members"] = members
    return content


def _validate_d_tag(team_id: str) -> None:
    if not team_id:
        raise ValueError("tag d vazia — o relay rejeita e o NIP-33 colapsaria no coordinate ''")
    if len(team_id) > _D_TAG_MAX_CHARS:
        raise ValueError(
            f"tag d com {len(team_id)} caracteres — o relay aceita até "
            f"{_D_TAG_MAX_CHARS} (ingest.rs:1163, single_bounded_d_tag)"
        )
    for ch in team_id:
        if ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F:
            raise ValueError(f"tag d com whitespace ou control char ({ch!r}) — o relay rejeita")


def unsigned_event(
    team: Team,
    manifest: PackManifest,
    *,
    shared: bool = True,
    pubkey: str = "",
    created_at: int = 0,
) -> dict:
    """O evento 30178 completo, MENOS id e sig — pronto para o signatário.

    ``pubkey`` vazio por default: preenchê-lo é papel de quem assina.
    O content vai COMPACTO (separators sem espaço), a forma que conta contra
    os 256 KiB do relay.
    """
    _validate_d_tag(team.id)
    content_compact = json.dumps(
        team_content(team, manifest), ensure_ascii=False, separators=(",", ":")
    )
    content_bytes = len(content_compact.encode("utf-8"))
    if content_bytes > EVENT_CONTENT_MAX_BYTES:
        raise ValueError(
            f"content com {content_bytes:,} bytes estoura o corpo de evento "
            f"({EVENT_CONTENT_MAX_BYTES:,}, ingest.rs:1868) — o team precisa encolher"
        )

    tags = [["d", team.id]]
    if shared:
        tags.append(["shared", "true"])  # forma EXATA de 2 elementos (ingest.rs:1163)

    return {
        "kind": KIND_TEAM_CATALOG,
        "pubkey": pubkey,
        "created_at": created_at,
        "tags": tags,
        "content": content_compact,
    }
