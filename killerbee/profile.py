"""Compilação do perfil scutellata para campos nativos do Buzz. Pura.

O perfil NÃO pode viajar como campo próprio: o frontmatter da persona rejeita
chave desconhecida com erro fatal (persona.rs:174-176), e o import de snapshot
aceita chave extra mas a DESCARTA na reserialização
(desktop/src-tauri/src/commands/personas/snapshot/import.rs:410). Logo, o perfil
vive no manifesto (L1) e compila para os campos que o runtime realmente lê.

O contrato completo, incluindo o que NÃO compila, está em
docs/PROFILE-COMPILATION.md — este módulo é a implementação daquele documento.
"""

from __future__ import annotations

from .model import (
    PERSISTENCE_VALUES,
    PROPAGATION_VALUES,
    RECRUITMENT_MAX,
    RECRUITMENT_MIN,
    THRESHOLD_VALUES,
    ScutellataProfile,
)

# persistence → (idleTimeoutSeconds, maxTurnDurationSeconds).
#
# Valores NOSSOS, não do upstream — o snapshot só define os campos
# (agent_snapshot.rs, definition.idle_timeout_seconds/max_turn_duration_seconds);
# a semântica de "curto/médio/longo" é decisão do Killer Bee, documentada e
# ajustável sem quebrar formato.
_PERSISTENCE_SECONDS: dict[str, tuple[int, int]] = {
    "short": (300, 600),
    "medium": (900, 1800),
    "long": (3600, 7200),
}

# threshold → respondTo do snapshot ({owner-only, allowlist, anyone} — valores
# validados no import, ver PROTOCOL-NOTES §10.8).
#
# Nota honesta de semântica: threshold é "quanto estímulo dispara"; respondTo é
# "quem pode disparar". O snapshot não tem campo de gatilho (mentions/keywords/
# all_messages são do formato persona-pack e da regra ACP, não do snapshot),
# então no snapshot o threshold só consegue se expressar pelo eixo QUEM:
# low/medium → qualquer membro; high → só o dono. O eixo O-QUÊ compila na regra
# ACP (ver compile_acp_trigger) e, onde nem isso alcança, é responsabilidade do
# system prompt autoral.
_THRESHOLD_RESPOND_TO: dict[str, str] = {
    "low": "anyone",
    "medium": "anyone",
    "high": "owner-only",
}


def validate_profile(profile: ScutellataProfile) -> list[str]:
    """Devolve a lista de erros do perfil; vazia = válido."""
    errors: list[str] = []
    if profile.threshold not in THRESHOLD_VALUES:
        errors.append(f"threshold '{profile.threshold}' inválido; use um de {THRESHOLD_VALUES}")
    if not isinstance(profile.recruitment, int) or isinstance(profile.recruitment, bool):
        errors.append(f"recruitment deve ser inteiro, veio {type(profile.recruitment).__name__}")
    elif not RECRUITMENT_MIN <= profile.recruitment <= RECRUITMENT_MAX:
        errors.append(
            f"recruitment {profile.recruitment} fora da faixa nativa "
            f"{RECRUITMENT_MIN}..={RECRUITMENT_MAX} (default em types.rs:812; "
            "faixa validada em types.rs:967)"
        )
    if profile.persistence not in PERSISTENCE_VALUES:
        errors.append(
            f"persistence '{profile.persistence}' inválida; use uma de {PERSISTENCE_VALUES}"
        )
    if profile.propagation not in PROPAGATION_VALUES:
        errors.append(
            f"propagation '{profile.propagation}' inválida; use uma de {PROPAGATION_VALUES}"
        )
    return errors


def compile_to_definition(profile: ScutellataProfile) -> dict:
    """Compila o perfil para os campos do ``definition`` do AgentSnapshot.

    Devolve APENAS os campos que o perfil governa; o chamador faz o merge com
    identidade e prompt. ``propagation`` deliberadamente não aparece — é metadado
    de catálogo, sem alvo de runtime.
    """
    errors = validate_profile(profile)
    if errors:
        raise ValueError("; ".join(errors))

    idle_timeout, max_turn = _PERSISTENCE_SECONDS[profile.persistence]
    return {
        "parallelism": profile.recruitment,
        "respondTo": _THRESHOLD_RESPOND_TO[profile.threshold],
        "idleTimeoutSeconds": idle_timeout,
        "maxTurnDurationSeconds": max_turn,
    }


def compile_acp_trigger(profile: ScutellataProfile) -> dict:
    """Compila o eixo O-QUÊ do threshold para a regra ACP.

    - ``require_mention`` SEMPRE presente e explícito — nunca herdado do default,
      porque o `impl Default` do campo é `false` (filter.rs:122) e uma regra TOML
      sem ele nasce casando TODAS as mensagens do canal, não só menções.
      Ver DECISIONS D-007.
    - threshold ``low``  → reage a tudo no canal (``require_mention: false``)
    - ``medium``/``high`` → só menção (``require_mention: true``)
    """
    errors = validate_profile(profile)
    if errors:
        raise ValueError("; ".join(errors))
    return {"require_mention": profile.threshold != "low"}
