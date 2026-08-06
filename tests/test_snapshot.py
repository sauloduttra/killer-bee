"""Snapshots: o dict emitido tem que casar com o schema verificado no fonte.

Referência: PROTOCOL-NOTES §10 (@ block/buzz ed4b3e7a).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killerbee.model import PackManifest, Persona, ScutellataProfile, Team
from killerbee.snapshot import agent_snapshot, team_snapshot


def make_persona(name: str = "scout", **overrides) -> Persona:
    defaults = dict(
        name=name,
        display_name=name.title(),
        description="A test persona",
        system_prompt="You are a test persona.",
        model="anthropic:claude-sonnet-5",
        runtime="claude",
        profile=ScutellataProfile(),
    )
    defaults.update(overrides)
    return Persona(**defaults)


def test_envelope_do_agent_snapshot():
    snapshot = agent_snapshot(make_persona())
    # Discriminadores exatos do formato (agent_snapshot.rs:163-175).
    assert snapshot["format"] == "buzz-agent-snapshot"
    assert snapshot["version"] == 1
    assert set(snapshot) == {"format", "version", "definition", "profile", "memory"}


def test_definition_carrega_o_prompt_inteiro_e_o_split_do_modelo():
    prompt = "Linha 1\n\nLinha 3 com ```código``` e --- separador\n" * 50
    snapshot = agent_snapshot(make_persona(system_prompt=prompt))
    definition = snapshot["definition"]
    assert definition["systemPrompt"] == prompt  # sem truncagem — transparência
    # split no PRIMEIRO ':' (persona.rs:324)
    assert definition["provider"] == "anthropic"
    assert definition["model"] == "claude-sonnet-5"


def test_model_com_dois_pontos_no_id_split_so_no_primeiro():
    snapshot = agent_snapshot(make_persona(model="openrouter:deepseek/deepseek-chat:free"))
    assert snapshot["definition"]["provider"] == "openrouter"
    assert snapshot["definition"]["model"] == "deepseek/deepseek-chat:free"


def test_sem_model_omite_em_vez_de_null():
    """Espelha o skip_serializing_if do emissor Rust: ausente, não null."""
    snapshot = agent_snapshot(make_persona(model=None, runtime=None))
    assert "model" not in snapshot["definition"]
    assert "provider" not in snapshot["definition"]
    assert "runtime" not in snapshot["definition"]


def test_memory_sempre_none_e_vazia():
    """Pack de catálogo não carrega memória de ninguém. level=none + entries=[]
    é a única combinação que o import aceita para 'none' (§10.8)."""
    snapshot = agent_snapshot(make_persona())
    assert snapshot["memory"] == {"level": "none", "entries": []}


def test_definition_name_recebe_display_name_como_o_emissor_upstream():
    """agent_snapshot.rs:198-201: definition.name = display_name, não o slug."""
    snapshot = agent_snapshot(make_persona(name="guard", display_name="Guard 🛡"))
    assert snapshot["definition"]["name"] == "Guard 🛡"
    assert snapshot["profile"]["displayName"] == "Guard 🛡"


def test_arrays_vazias_sao_omitidas_como_no_emissor_upstream():
    """agent_snapshot.rs:112-115: skip_serializing_if = Vec::is_empty para
    respondToAllowlist e namePool. Emitir `[]` divergia do exportador de
    referência — o preview do app descartava os campos na reserialização
    (observado em §10.9). Auditoria 2026-08-06."""
    definition = agent_snapshot(make_persona())["definition"]
    assert "respondToAllowlist" not in definition
    assert "namePool" not in definition


def test_perfil_scutellata_compila_para_campos_nativos():
    persona = make_persona(
        profile=ScutellataProfile(
            threshold="low", recruitment=8, persistence="long", propagation="high"
        )
    )
    definition = agent_snapshot(persona)["definition"]
    assert definition["parallelism"] == 8
    assert definition["respondTo"] == "anyone"
    assert definition["idleTimeoutSeconds"] == 3600
    # propagation não vaza para o runtime
    assert "propagation" not in str(definition)


def _manifest_with_team(members: tuple[str, ...]) -> tuple[Team, PackManifest]:
    personas = tuple(make_persona(n) for n in ("forager", "adversary", "guard"))
    team = Team(id="crossfire", name="Crossfire", members=members)
    manifest = PackManifest(name="test-pack", version="0.1.0", personas=personas, teams=(team,))
    return team, manifest


def test_team_snapshot_embute_membros_inteiros_em_ordem():
    team, manifest = _manifest_with_team(("guard", "forager"))
    snapshot = team_snapshot(team, manifest)
    assert snapshot["format"] == "buzz-team-snapshot"
    assert snapshot["version"] == 1
    # Embutidos e NA ORDEM do manifesto (team_snapshot.rs: "Order is preserved").
    names = [m["definition"]["name"] for m in snapshot["members"]]
    assert names == ["Guard", "Forager"]
    # Cada membro é um AgentSnapshot completo, não uma referência.
    for member in snapshot["members"]:
        assert member["format"] == "buzz-agent-snapshot"
        assert member["definition"]["systemPrompt"]


def test_team_com_membro_inexistente_falha_cedo_e_com_nome():
    team, manifest = _manifest_with_team(("forager", "fantasma"))
    with pytest.raises(ValueError, match="fantasma"):
        team_snapshot(team, manifest)


def test_team_sem_membros_falha():
    team, manifest = _manifest_with_team(())
    with pytest.raises(ValueError, match="ao menos 1 membro"):
        team_snapshot(team, manifest)
