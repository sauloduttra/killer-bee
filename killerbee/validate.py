"""Validação de um pack carregado. Pura: modelo → lista de erros legíveis.

Cada regra existe por um motivo verificado no upstream; a citação vai no
próprio erro quando ajuda quem lê a entender de onde a regra veio.
"""

from __future__ import annotations

import re
import uuid

from .model import PackManifest
from .profile import validate_profile

# Gramática do `d` tag de persona no relay: ^[a-z0-9][a-z0-9_-]{0,63}$
# (crates/buzz-relay/src/handlers/ingest.rs:1130-1148 @ ed4b3e7a). Sem ponto —
# a versão anterior deste regex aceitava '.', que o relay rejeita.
_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

# team.id vira nome de arquivo em `killerbee build` ({id}.team.json/.png).
# O upstream é DELIBERADAMENTE mais frouxo no d-tag de team — aceita ':' para
# UUIDs e `builtin-team:welcome` (handlers/ingest.rs:1159-1162) — mas ':' é
# ilegal em nome de arquivo no Windows e '../' seria path traversal. A restrição
# extra é decisão do Killer Bee (DECISIONS D-023): id de team publicável em L3
# que precise de ':' ganhará um campo próprio quando o emissor L3 existir.
_TEAM_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

# Nomes de dispositivo reservados do Windows: 'nul.agent.json' não é um arquivo
# comum em NTFS. Vale para o primeiro segmento antes do ponto.
_WINDOWS_RESERVED = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)}
)

_SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")

# Import do desktop rejeita snapshot acima destes tamanhos (PROTOCOL-NOTES §10.8).
# Aplicados de verdade em cmd_build — constante definida e não usada é promessa
# de validação que ninguém cumpre.
AGENT_JSON_MAX_BYTES = 5 * 1024 * 1024
TEAM_JSON_MAX_BYTES = 25 * 1024 * 1024

# Corpo de evento no relay: ingest.rs:1868 (@ ed4b3e7a). Relevante para L3.
EVENT_CONTENT_MAX_BYTES = 256 * 1024


def _reserved_filename(stem: str) -> bool:
    return stem.split(".")[0].lower() in _WINDOWS_RESERVED


def validate_pack(manifest: PackManifest) -> list[str]:
    """Todas as violações de uma vez — nunca 'conserta um, descobre o próximo'."""
    errors: list[str] = []

    # ── Manifesto ────────────────────────────────────────────────────────
    if not manifest.name.strip():
        errors.append("manifesto: 'name' é obrigatório")
    elif not _SLUG.match(manifest.name):
        errors.append(
            f"manifesto: name '{manifest.name}' não segue a gramática de slug "
            "^[a-z0-9][a-z0-9_-]{0,63}$ (handlers/ingest.rs:1130-1148)"
        )
    elif _reserved_filename(manifest.name):
        errors.append(
            f"manifesto: name '{manifest.name}' é nome de dispositivo reservado no Windows"
        )
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
        if not persona.name.strip():
            errors.append(f"{where}: frontmatter sem 'name' (obrigatório no formato nativo)")
        elif not _SLUG.match(persona.name):
            errors.append(
                f"{where}: name não segue a gramática de slug do d-tag de persona "
                "^[a-z0-9][a-z0-9_-]{0,63}$ (handlers/ingest.rs:1130-1148); "
                "é também o que vira nome de arquivo no build"
            )
        elif _reserved_filename(persona.name):
            errors.append(f"{where}: name é nome de dispositivo reservado no Windows")
        if persona.name in seen:
            errors.append(f"{where}: name duplicado no pack")
        seen.add(persona.name)
        # trim, não falsy: o parser nativo rejeita "   " (persona.rs:229-237) e o
        # import de snapshot valida com .trim() (agent_snapshot.rs:400-406) —
        # checagem falsy aceitava um display_name só de espaços que o app recusa.
        if not persona.display_name.strip():
            errors.append(f"{where}: 'display_name' é obrigatório (persona.rs:232-234)")
        if not persona.description.strip():
            errors.append(f"{where}: 'description' é obrigatória (persona.rs:235-237)")
        if not persona.system_prompt.strip():
            errors.append(f"{where}: corpo markdown vazio — o system prompt É o corpo")
        if persona.model is not None and ":" not in persona.model:
            errors.append(
                f"{where}: model '{persona.model}' sem ':' — o formato upstream é "
                "'provider:model-id' (persona.rs:141-143)"
            )
        # channels: ou exatamente ["all"], ou lista de UUIDs de canal — o
        # formato que filter.rs aceita. Misturar "all" com UUID, ou canal com
        # caractere de controle, geraria um acp-rules.toml inválido ou com
        # entrada morta que nunca casa.
        if persona.channels != ("all",):
            for channel in persona.channels:
                if channel == "all":
                    errors.append(
                        f"{where}: 'all' misturado com canais específicos — "
                        'ou a lista é ["all"] sozinho, ou só UUIDs'
                    )
                    continue
                try:
                    uuid.UUID(channel)
                except (ValueError, AttributeError, TypeError):
                    errors.append(
                        f"{where}: channel '{channel}' não é UUID — filter.rs "
                        'aceita "all" ou lista de UUIDs de canal'
                    )
        errors.extend(f"{where}: {e}" for e in validate_profile(persona.profile))

    # ── Teams ────────────────────────────────────────────────────────────
    team_ids: set[str] = set()
    for team in manifest.teams:
        where = f"team '{team.id or '?'}'"
        if not team.id.strip():
            errors.append(f"{where}: 'id' é obrigatório")
        elif len(team.id) > 64:
            errors.append(
                f"{where}: id com {len(team.id)} chars — o tag d do kind 30178 aceita "
                "até 64 (handlers/ingest.rs:1163, single_bounded_d_tag)"
            )
        elif not _TEAM_ID.match(team.id):
            errors.append(
                f"{where}: id '{team.id}' com caractere fora de [a-z0-9._-] — o id "
                "vira nome de arquivo no build (restrição do Killer Bee, D-023; "
                "o d-tag upstream aceita mais, handlers/ingest.rs:1159-1162)"
            )
        elif _reserved_filename(team.id):
            errors.append(f"{where}: id é nome de dispositivo reservado no Windows")
        if team.id in team_ids:
            errors.append(f"{where}: id duplicado no pack")
        team_ids.add(team.id)
        if not team.name.strip():
            errors.append(
                f"{where}: 'name' é obrigatório — o import valida com trim "
                "(team_snapshot.rs:209-211); só espaços também é vazio"
            )
        if not team.members:
            errors.append(f"{where}: team sem membros — o import upstream rejeita")
        for member in team.members:
            if manifest.persona_by_name(member) is None:
                errors.append(f"{where}: membro '{member}' não existe entre as personas")

    return errors
