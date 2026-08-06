"""Modelo de dados de um Killer Bee Pack. Puro: sem I/O, sem parsing.

O manifesto (`killerbee.yaml`) é a camada L1 — o que se revisa em PR. As personas
são `.persona.md` no formato nativo do Buzz (frontmatter YAML + corpo markdown),
DELIBERADAMENTE sem nenhuma chave extra: o parser upstream usa
`deny_unknown_fields` (crates/buzz-persona/src/persona.rs:174-176) e uma chave
nossa seria erro fatal lá. Tudo que é do Killer Bee — perfil scutellata, tags,
avatar, procedência — mora no manifesto, nunca no arquivo de persona.
"""

from __future__ import annotations

from dataclasses import dataclass, field

THRESHOLD_VALUES = ("low", "medium", "high")
PERSISTENCE_VALUES = ("short", "medium", "long")
PROPAGATION_VALUES = ("low", "medium", "high")

# Faixa nativa de paralelismo por agente no Buzz Desktop
# (desktop/src-tauri/src/managed_agents/types.rs): default em :812,
# faixa 1..=32 validada em :967 e :974.
RECRUITMENT_MIN = 1
RECRUITMENT_MAX = 32


@dataclass(frozen=True)
class ScutellataProfile:
    """Os quatro traços mensuráveis da africanizada, como campos declarativos.

    - ``threshold``   — quanto estímulo dispara o agente
    - ``recruitment`` — fan-out de paralelismo (inteiro, mapeia direto no campo nativo)
    - ``persistence`` — quanto tempo insiste antes de desistir
    - ``propagation`` — facilidade de replicação do pack (metadado de catálogo;
      não compila para runtime nenhum)
    """

    threshold: str = "medium"
    recruitment: int = 1
    persistence: str = "medium"
    propagation: str = "medium"


@dataclass(frozen=True)
class Persona:
    """Uma persona: identidade + system prompt + configuração comportamental.

    ``name``/``display_name``/``description`` seguem os campos obrigatórios do
    formato nativo (crates/buzz-persona/src/persona.rs:101-113). ``model`` usa o
    formato upstream ``"provider:model-id"``, split no primeiro ``:``
    (persona.rs:324).
    """

    name: str
    display_name: str
    description: str
    system_prompt: str
    model: str | None = None
    runtime: str | None = None
    profile: ScutellataProfile = field(default_factory=ScutellataProfile)
    # Sugestão de canais para a regra ACP gerada; "all" = todos.
    channels: tuple[str, ...] = ("all",)


@dataclass(frozen=True)
class Team:
    """Um team: metadado + membros por nome de persona (resolvidos no build).

    No snapshot emitido os membros são EMBUTIDOS inteiros
    (team_snapshot.rs:76-87) — a referência por nome existe só aqui no manifesto.
    """

    id: str
    name: str
    description: str = ""
    instructions: str = ""
    members: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackManifest:
    """O killerbee.yaml materializado."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = ""
    tags: tuple[str, ...] = ()
    buzz_commit: str = ""
    personas: tuple[Persona, ...] = ()
    teams: tuple[Team, ...] = ()

    def persona_by_name(self, name: str) -> Persona | None:
        for persona in self.personas:
            if persona.name == name:
                return persona
        return None


def split_model(model: str | None) -> tuple[str | None, str | None]:
    """Divide ``"provider:model-id"`` no PRIMEIRO ``:``, como o upstream.

    Fonte do comportamento: crates/buzz-persona/src/persona.rs:324 (`split_model`).
    Sem ``:``, o valor inteiro é tratado como model-id sem provider — o snapshot
    aceita ambos como opcionais.
    """
    if model is None or model == "":
        return None, None
    if ":" not in model:
        return None, model
    provider, model_id = model.split(":", 1)
    return (provider or None), (model_id or None)
