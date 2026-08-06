"""Validação de um pack carregado. Pura: modelo → lista de erros legíveis.

Cada regra existe por um motivo verificado no upstream; a citação vai no
próprio erro quando ajuda quem lê a entender de onde a regra veio.
"""

from __future__ import annotations

import re

from .model import PackManifest
from .profile import validate_profile

_SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")

# Import do desktop rejeita snapshot acima destes tamanhos (PROTOCOL-NOTES §10.8).
AGENT_JSON_MAX_BYTES = 5 * 1024 * 1024
TEAM_JSON_MAX_BYTES = 25 * 1024 * 1024

# Corpo de evento no relay: ingest.rs:1868 (@ ed4b3e7a). Relevante para L3.
EVENT_CONTENT_MAX_BYTES = 256 * 1024


def validate_pack(manifest: PackManifest) -> list[str]:
    """Todas as violações de uma vez — nunca 'conserta um, descobre o próximo'."""
    errors: list[str] = []

    # ── Manifesto ────────────────────────────────────────────────────────
    if not manifest.name:
        errors.append("manifesto: 'name' é obrigatório")
    elif not _SLUG.match(manifest.name):
        errors.append(f"manifesto: name '{manifest.name}' não é slug (minúsculas, sem espaço)")
    if not manifest.version:
        errors.append("manifesto: 'version' é obrigatória")
    elif not _SEMVER.match(manifest.version):
        errors.append(f"manifesto: version '{manifest.version}' não é semver (X.Y.Z)")
    if not manifest.license:
        errors.append("manifesto: 'license' é obrigatória — pack sem licença não é distribuível")
    if not manifest.personas:
        errors.append("manifesto: pack precisa de ao menos uma persona")

    # ── Personas ─────────────────────────────────────────────────────────
    seen: set[str] = set()
    for persona in manifest.personas:
        where = f"persona '{persona.name or '?'}'"
        if not persona.name:
            errors.append(f"{where}: frontmatter sem 'name' (obrigatório no formato nativo)")
        elif not _SLUG.match(persona.name):
            errors.append(f"{where}: name deve ser slug minúsculo (persona.rs:102-103)")
        if persona.name in seen:
            errors.append(f"{where}: name duplicado no pack")
        seen.add(persona.name)
        if not persona.display_name:
            errors.append(f"{where}: 'display_name' é obrigatório (persona.rs:106)")
        if not persona.description:
            errors.append(f"{where}: 'description' é obrigatória (persona.rs:113)")
        if not persona.system_prompt.strip():
            errors.append(f"{where}: corpo markdown vazio — o system prompt É o corpo")
        if persona.model is not None and ":" not in persona.model:
            errors.append(
                f"{where}: model '{persona.model}' sem ':' — o formato upstream é "
                "'provider:model-id' (persona.rs:141-143)"
            )
        errors.extend(f"{where}: {e}" for e in validate_profile(persona.profile))

    # ── Teams ────────────────────────────────────────────────────────────
    team_ids: set[str] = set()
    for team in manifest.teams:
        where = f"team '{team.id or '?'}'"
        if not team.id:
            errors.append(f"{where}: 'id' é obrigatório")
        elif len(team.id) > 64:
            errors.append(
                f"{where}: id com {len(team.id)} chars — o tag d do kind 30178 aceita "
                "até 64 (ingest.rs:1163, single_bounded_d_tag)"
            )
        if team.id in team_ids:
            errors.append(f"{where}: id duplicado no pack")
        team_ids.add(team.id)
        if not team.name:
            errors.append(f"{where}: 'name' é obrigatório")
        if not team.members:
            errors.append(f"{where}: team sem membros — o import upstream rejeita")
        for member in team.members:
            if manifest.persona_by_name(member) is None:
                errors.append(f"{where}: membro '{member}' não existe entre as personas")

    return errors
