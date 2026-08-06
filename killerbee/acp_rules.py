"""Regras de subscrição do buzz-acp em TOML. Puro: modelo → texto.

Formato-alvo verificado @ ed4b3e7a:

- o arquivo é `TomlConfig { rules: Vec<SubscriptionRule> }`
  (crates/buzz-acp/src/config.rs:1158, lido por `load_rules` em :1161)
  → chave de topo `[[rules]]`, no máximo 100 regras (:1169)
- `SubscriptionRule` (crates/buzz-acp/src/filter.rs): `name` (String),
  `channels` ("all" ou lista de UUIDs), `kinds` (Vec<u32>, default vazio =
  wildcard), `require_mention` (bool, `#[serde(default)]` → **false**),
  `filter` (evalexpr opcional), `prompt_tag` (opcional)

A regra inegociável (DECISIONS D-007): **`require_mention` sai SEMPRE escrito**,
nunca herdado do default. O default do struct é `false` (filter.rs:122) — uma
regra gerada sem o campo nasce surda a menção, e o crossfire inteiro depende de
menção funcionar. O teste que trava isso é test_acp_rules.py.
"""

from __future__ import annotations

from .model import Persona
from .profile import compile_acp_trigger


def _toml_string(value: str) -> str:
    """Escapa uma string para TOML básico (aspas duplas)."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def rule_for_persona(persona: Persona) -> str:
    """Uma entrada `[[rules]]` para a persona, com menção explícita."""
    trigger = compile_acp_trigger(persona.profile)
    lines = [
        "[[rules]]",
        f"name = {_toml_string(persona.name)}",
    ]
    if persona.channels == ("all",):
        lines.append('channels = "all"')
    else:
        rendered = ", ".join(_toml_string(channel) for channel in persona.channels)
        lines.append(f"channels = [{rendered}]")
    # SEMPRE explícito — ver docstring do módulo.
    lines.append(f"require_mention = {'true' if trigger['require_mention'] else 'false'}")
    lines.append(f"prompt_tag = {_toml_string(persona.name)}")
    return "\n".join(lines)


def rules_file(personas: list[Persona] | tuple[Persona, ...]) -> str:
    """O arquivo de regras completo para um pack."""
    if len(personas) > 100:
        # Cap do upstream (config.rs:1169). Falhar aqui, não no load do agente.
        raise ValueError(f"buzz-acp aceita no máximo 100 regras; pack tem {len(personas)}")
    header = (
        "# Regras de subscrição buzz-acp geradas pelo Killer Bee.\n"
        "# require_mention é SEMPRE explícito: o default do campo é false\n"
        "# (crates/buzz-acp/src/filter.rs:122) e uma regra sem ele nasce surda.\n"
        "# Uso: buzz-acp --subscribe config --rules <este arquivo>\n"
    )
    return header + "\n" + "\n\n".join(rule_for_persona(p) for p in personas) + "\n"
