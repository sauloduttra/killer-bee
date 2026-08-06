"""Camada pura de `scripts/license_audit.py`.

Esta auditoria produziu conclusão errada **cinco vezes**, sempre da mesma forma:
falha de coleta reportada como ausência de dado. Os testes aqui existem para que
a sexta seja pega por CI e não por leitura de relatório.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from license_audit import (
    Repo,
    classify_license_text,
    copyright_line,
    external_contributors,
    gh_json,
    has_license_file,
    suggest_tier,
)

MIT = """MIT License

Copyright (c) 2026 Saulo Duttra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction.
"""

APACHE = """                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/
"""

AGPL = """                    GNU AFFERO GENERAL PUBLIC LICENSE
                       Version 3, 19 November 2007
"""


def make_repo(**overrides) -> Repo:
    defaults = dict(
        name="some-lab",
        is_fork=False,
        is_archived=False,
        license_spdx=None,
        language="Python",
        pushed_at="2026-06-01",
        description="",
    )
    defaults.update(overrides)
    return Repo(**defaults)


# ---------------------------------------------------------------------------
# Classificação por texto
# ---------------------------------------------------------------------------


def test_reconhece_mit():
    assert classify_license_text(MIT) == "MIT"


def test_reconhece_apache():
    assert classify_license_text(APACHE) == "Apache-2.0"


def test_agpl_vence_gpl():
    """A ordem das assinaturas importa: AGPL contém 'GENERAL PUBLIC LICENSE'."""
    assert classify_license_text(AGPL) == "AGPL-3.0"


def test_texto_vazio_e_ausente():
    assert classify_license_text("") == "AUSENTE"
    assert classify_license_text(None) == "AUSENTE"


def test_todos_os_direitos_reservados_e_proprietaria():
    assert classify_license_text("Copyright 2026. All rights reserved.") == "PROPRIETÁRIA"


def test_texto_irreconhecivel_nao_vira_ausente():
    """Não saber classificar é diferente de não haver licença."""
    assert classify_license_text("Faça o que quiser, mas me pague um café.") == "NÃO IDENTIFICADA"


def test_extrai_titular():
    assert copyright_line(MIT) == "Copyright (c) 2026 Saulo Duttra"


# ---------------------------------------------------------------------------
# A distinção que custou cinco relatórios errados
# ---------------------------------------------------------------------------


def test_falha_de_coleta_nao_e_ausencia():
    """Listagem da raiz não obtida → DESCONHECIDO, nunca AUSENTE."""
    repo = make_repo()  # contents_fetched fica False
    assert repo.actual_license == "DESCONHECIDO"


def test_ausencia_real_exige_coleta_bem_sucedida():
    repo = make_repo(root_files=["README.md", "src"], contents_fetched=True)
    assert repo.actual_license == "AUSENTE"


def test_license_presente_mas_conteudo_nao_veio_e_desconhecido():
    """Existe LICENSE na raiz e o corpo não chegou. Isso não é ausência."""
    repo = make_repo(root_files=["LICENSE"], contents_fetched=True, license_text=None)
    assert repo.actual_license == "DESCONHECIDO"


def test_desconhecido_pede_recoleta_nao_acao():
    repo = make_repo()
    tier, motivo = suggest_tier(repo, "sauloduttra")
    assert tier == "RECOLETAR"
    assert "coleta" in motivo


def test_ausente_de_verdade_pede_acao():
    repo = make_repo(root_files=["README.md"], contents_fetched=True)
    tier, _ = suggest_tier(repo, "sauloduttra")
    assert tier == "AGIR"


# ---------------------------------------------------------------------------
# A guarda contra o bug do jq escalar
# ---------------------------------------------------------------------------


def test_jq_escalar_e_recusado_antes_de_chamar_a_api():
    """`--jq '.content'` imprime base64 cru, sem aspas — não é JSON.

    Este erro derrubou 118 chamadas numa rodada e 123 em outra, e as duas vezes o
    sintoma foi "repositório sem licença". A guarda falha alto em vez de contar
    como erro de rede.
    """
    with pytest.raises(ValueError, match="escalar"):
        gh_json(["api", "repos/x/y/contents/LICENSE", "--jq", ".content"])
    with pytest.raises(ValueError, match="escalar"):
        gh_json(["api", "repos/x/y", "--jq", ".license.spdx_id"])


def test_jq_de_array_continua_permitido():
    """`[.[].name]` produz JSON válido e não deve ser bloqueado.

    Não chamamos a API aqui — só checamos que a guarda não dispara. O `gh` pode
    até falhar depois, e nesse caso a função devolve None, que é o contrato.
    """
    try:
        gh_json(["api", "repos/does-not-exist-xyz/nope/contents", "--jq", "[.[].name]"])
    except ValueError as exc:  # pragma: no cover
        pytest.fail(f"a guarda bloqueou uma projeção de array válida: {exc}")


# ---------------------------------------------------------------------------
# Contribuidores e forks
# ---------------------------------------------------------------------------


def test_bot_nao_conta_como_contribuidor_externo():
    repo = make_repo(contributors=["sauloduttra", "dependabot[bot]"])
    assert external_contributors(repo, "sauloduttra") == []


def test_contribuidor_externo_e_urgente():
    repo = make_repo(contributors=["sauloduttra", "outra-pessoa"], contents_fetched=True)
    tier, motivo = suggest_tier(repo, "sauloduttra")
    assert tier == "URGENTE"
    assert "negocia" in motivo


def test_fork_nao_e_nosso_para_relicenciar():
    tier, _ = suggest_tier(make_repo(is_fork=True), "sauloduttra")
    assert tier == "HERDA"


def test_has_license_file_aceita_copying():
    assert has_license_file(make_repo(root_files=["COPYING"]))
    assert not has_license_file(make_repo(root_files=["README.md"]))
