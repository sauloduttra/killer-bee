"""Construção de AgentSnapshot / TeamSnapshot. Pura: modelo → dict JSON.

Schema-alvo verificado no fonte @ ed4b3e7a:

- `AgentSnapshot` — agent_snapshot.rs:163-175: `format`, `version`, `definition`,
  `profile`, `memory`; serde `rename_all = "camelCase"`.
- `definition` — campos materializados por `build_snapshot`
  (agent_snapshot.rs:188-211): name, sourceIsBuiltIn, systemPrompt, runtime,
  model, provider, parallelism, respondTo, respondToAllowlist, namePool,
  idleTimeoutSeconds, maxTurnDurationSeconds.
- `profile` — displayName, about, avatarDataUrl, avatarUrl.
- `memory` — level (snake_case: none|core|everything) + entries
  (agent_snapshot.rs:142-157). Emitimos sempre `level: "none"` — pack de
  catálogo não carrega memória de ninguém.
- `TeamSnapshot` — team_snapshot.rs:76-87: format, version, team{name,
  description?, instructions?}, members: Vec<AgentSnapshot> — EMBUTIDOS.

Detalhe fiel ao emissor upstream: `definition.name` recebe o display name
(agent_snapshot.rs:195-198 usa display_name com fallback para name), não o slug.
"""

from __future__ import annotations

from . import AGENT_SNAPSHOT_FORMAT, SNAPSHOT_VERSION, TEAM_SNAPSHOT_FORMAT
from .model import PackManifest, Persona, Team, split_model
from .profile import compile_to_definition


def agent_snapshot(persona: Persona) -> dict:
    """Monta o dict pronto para virar `.agent.json`."""
    provider, model_id = split_model(persona.model)
    compiled = compile_to_definition(persona.profile)

    definition: dict = {
        "name": persona.display_name,
        "sourceIsBuiltIn": False,
        "systemPrompt": persona.system_prompt,
        "parallelism": compiled["parallelism"],
        "respondTo": compiled["respondTo"],
        "respondToAllowlist": [],
        "namePool": [],
        "idleTimeoutSeconds": compiled["idleTimeoutSeconds"],
        "maxTurnDurationSeconds": compiled["maxTurnDurationSeconds"],
    }
    # Opcionais entram só quando existem — espelha o skip_serializing_if do
    # emissor Rust e evita afirmar `null` onde o upstream omitiria.
    if persona.runtime:
        definition["runtime"] = persona.runtime
    if model_id:
        definition["model"] = model_id
    if provider:
        definition["provider"] = provider

    return {
        "format": AGENT_SNAPSHOT_FORMAT,
        "version": SNAPSHOT_VERSION,
        "definition": definition,
        "profile": {
            "displayName": persona.display_name,
            "about": persona.description,
        },
        "memory": {"level": "none", "entries": []},
    }


def team_snapshot(team: Team, manifest: PackManifest) -> dict:
    """Monta o dict pronto para virar `.team.json`, membros embutidos e em ordem."""
    members = []
    for member_name in team.members:
        persona = manifest.persona_by_name(member_name)
        if persona is None:
            raise ValueError(f"team '{team.id}' referencia persona inexistente '{member_name}'")
        members.append(agent_snapshot(persona))
    if not members:
        # O import upstream rejeita team sem membro; falhar aqui é mais cedo e
        # com mensagem melhor.
        raise ValueError(f"team '{team.id}' precisa de ao menos 1 membro")

    team_meta: dict = {"name": team.name}
    if team.description:
        team_meta["description"] = team.description
    if team.instructions:
        team_meta["instructions"] = team.instructions

    return {
        "format": TEAM_SNAPSHOT_FORMAT,
        "version": SNAPSHOT_VERSION,
        "team": team_meta,
        "members": members,
    }
