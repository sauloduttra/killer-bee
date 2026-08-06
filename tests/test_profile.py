"""Perfil scutellata: validação e compilação. Tudo puro, nada toca disco."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killerbee.model import RECRUITMENT_MAX, RECRUITMENT_MIN, ScutellataProfile
from killerbee.profile import compile_acp_trigger, compile_to_definition, validate_profile


def test_perfil_default_e_valido():
    assert validate_profile(ScutellataProfile()) == []


def test_recruitment_mapeia_direto_para_parallelism():
    for value in (RECRUITMENT_MIN, 10, RECRUITMENT_MAX):
        compiled = compile_to_definition(ScutellataProfile(recruitment=value))
        assert compiled["parallelism"] == value


def test_recruitment_fora_da_faixa_nativa_e_erro():
    """A faixa é a do campo nativo do Buzz (1..=32, types.rs:812) — não nossa."""
    for value in (0, 33, -1):
        errors = validate_profile(ScutellataProfile(recruitment=value))
        assert any("faixa nativa" in e for e in errors), f"recruitment={value} passou"


def test_recruitment_booleano_e_rejeitado():
    """`True` é int em Python; um YAML `recruitment: true` não pode virar 1."""
    errors = validate_profile(ScutellataProfile(recruitment=True))
    assert any("inteiro" in e for e in errors)


def test_threshold_governa_respond_to():
    assert compile_to_definition(ScutellataProfile(threshold="low"))["respondTo"] == "anyone"
    assert compile_to_definition(ScutellataProfile(threshold="medium"))["respondTo"] == "anyone"
    assert compile_to_definition(ScutellataProfile(threshold="high"))["respondTo"] == "owner-only"


def test_persistence_e_monotonica():
    """Propriedade: mais persistência nunca produz timeout menor."""
    short = compile_to_definition(ScutellataProfile(persistence="short"))
    medium = compile_to_definition(ScutellataProfile(persistence="medium"))
    long = compile_to_definition(ScutellataProfile(persistence="long"))
    assert short["idleTimeoutSeconds"] < medium["idleTimeoutSeconds"] < long["idleTimeoutSeconds"]
    assert (
        short["maxTurnDurationSeconds"]
        < medium["maxTurnDurationSeconds"]
        < long["maxTurnDurationSeconds"]
    )


def test_propagation_nao_compila_para_runtime():
    """propagation é metadado de catálogo; não pode vazar para o snapshot."""
    compiled = compile_to_definition(ScutellataProfile(propagation="high"))
    assert "propagation" not in compiled


def test_valor_invalido_levanta_com_mensagem_que_diz_qual_e_por_que():
    with pytest.raises(ValueError, match="threshold 'urgente'"):
        compile_to_definition(ScutellataProfile(threshold="urgente"))


def test_trigger_acp_por_threshold():
    assert compile_acp_trigger(ScutellataProfile(threshold="low")) == {"require_mention": False}
    assert compile_acp_trigger(ScutellataProfile(threshold="medium")) == {"require_mention": True}
    assert compile_acp_trigger(ScutellataProfile(threshold="high")) == {"require_mention": True}


def test_compilacao_e_injetiva_salvo_propagation():
    """Round-trip da tabela: perfis distintos → definitions distintas, EXCETO
    quando a diferença é só propagation (o único eixo declarado inerte,
    PROFILE-COMPILATION.md) ou o colapso documentado low/medium→anyone do
    respondTo. Se alguém mudar a tabela e dois perfis distintos passarem a
    compilar igual sem estar nessas exceções, este teste acusa a perda de
    informação. Auditoria 2026-08-06 (lacuna metodológica: o eixo threshold
    não tinha NENHUMA propriedade travada)."""
    from itertools import product

    from killerbee.model import (
        PERSISTENCE_VALUES,
        PROPAGATION_VALUES,
        THRESHOLD_VALUES,
    )

    seen: dict[tuple, tuple] = {}
    for threshold, recruitment, persistence, propagation in product(
        THRESHOLD_VALUES, (1, 8, 32), PERSISTENCE_VALUES, PROPAGATION_VALUES
    ):
        profile = ScutellataProfile(
            threshold=threshold,
            recruitment=recruitment,
            persistence=persistence,
            propagation=propagation,
        )
        compiled = compile_to_definition(profile)
        trigger = compile_acp_trigger(profile)
        key = (
            compiled["parallelism"],
            compiled["respondTo"],
            compiled["idleTimeoutSeconds"],
            compiled["maxTurnDurationSeconds"],
            trigger["require_mention"],
        )
        source = (threshold, recruitment, persistence)  # sem propagation
        if key in seen:
            # Mesmo destino só é aceitável se a fonte (menos propagation)
            # for a mesma — propagation é inerte por contrato.
            assert seen[key] == source, (
                f"perda de informação: {seen[key]} e {source} compilam idêntico"
            )
        seen[key] = source


def test_threshold_low_e_medium_divergem_na_regra_acp():
    """low e medium colapsam no respondTo (ambos anyone) mas DIVERGEM no
    require_mention — é a regra ACP que carrega o eixo O-QUÊ. Se essa
    divergência sumir, threshold vira um eixo de dois valores."""
    low = compile_acp_trigger(ScutellataProfile(threshold="low"))
    medium = compile_acp_trigger(ScutellataProfile(threshold="medium"))
    assert low["require_mention"] != medium["require_mention"]
