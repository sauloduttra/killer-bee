"""Regras ACP: o teste que trava o DoD — menção explícita em TODA regra gerada.

Motivo (DECISIONS D-007): o default do campo `require_mention` é `false`
(crates/buzz-acp/src/filter.rs:122). Regra TOML sem o campo nasce surda a
menção, e o crossfire depende de menção funcionar.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killerbee.acp_rules import rule_for_persona, rules_file
from killerbee.model import Persona, ScutellataProfile


def make_persona(name: str, threshold: str = "medium", channels=("all",)) -> Persona:
    return Persona(
        name=name,
        display_name=name.title(),
        description="d",
        system_prompt="p",
        profile=ScutellataProfile(threshold=threshold),
        channels=channels,
    )


def test_DoD_toda_regra_gerada_tem_require_mention_escrito():
    """O item de DoD, literal: falha se qualquer regra sair sem o campo."""
    personas = [make_persona("a", "low"), make_persona("b", "medium"), make_persona("c", "high")]
    text = rules_file(personas)
    parsed = tomllib.loads(text)
    assert len(parsed["rules"]) == 3
    for rule_text in re.split(r"\n\n", text):
        if "[[rules]]" in rule_text:
            assert "require_mention" in rule_text, f"regra sem require_mention:\n{rule_text}"


def test_o_arquivo_parseia_como_o_upstream_parsearia():
    """Chave de topo `rules` — TomlConfig { rules: Vec<...> } (config.rs:1158)."""
    parsed = tomllib.loads(rules_file([make_persona("scout")]))
    assert set(parsed) == {"rules"}
    rule = parsed["rules"][0]
    # Só campos que SubscriptionRule conhece (filter.rs) — nada inventado.
    assert set(rule) <= {"name", "channels", "kinds", "require_mention", "filter", "prompt_tag"}


def test_threshold_governa_o_gatilho():
    low = tomllib.loads(rules_file([make_persona("a", "low")]))["rules"][0]
    high = tomllib.loads(rules_file([make_persona("b", "high")]))["rules"][0]
    assert low["require_mention"] is False
    assert high["require_mention"] is True


def test_channels_all_vira_string_lista_vira_array():
    """ChannelScope aceita "all" ou lista de ids (filter.rs, ChannelScope)."""
    all_rule = tomllib.loads(rules_file([make_persona("a")]))["rules"][0]
    assert all_rule["channels"] == "all"
    listed = make_persona("b", channels=("123e4567-e89b-12d3-a456-426614174000",))
    list_rule = tomllib.loads(rules_file([listed]))["rules"][0]
    assert list_rule["channels"] == ["123e4567-e89b-12d3-a456-426614174000"]


def test_cap_de_100_regras_do_upstream():
    """config.rs:1169 rejeita >100; falhamos no build, não no load do agente."""
    many = [make_persona(f"p{i}") for i in range(101)]
    with pytest.raises(ValueError, match="100"):
        rules_file(many)


def test_escape_de_aspas_no_nome():
    rule = rule_for_persona(make_persona("scout"))
    weird = Persona(
        name="we-ird",
        display_name='Has "quotes"',
        description="d",
        system_prompt="p",
    )
    # nome vai como string TOML válida mesmo com conteúdo estranho
    parsed = tomllib.loads(rule_for_persona(weird) + "\n")
    assert parsed["rules"][0]["name"] == "we-ird"
    assert tomllib.loads(rule + "\n")["rules"][0]["name"] == "scout"
