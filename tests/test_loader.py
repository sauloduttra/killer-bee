"""Testes do loader — o módulo com mais ramos de erro do emissor.

Até a auditoria de 2026-08-06 NENHUM caminho de PackLoadError era exercido.
Cada teste aqui é um estado real de edição (seção nula, escalar onde ia lista,
BOM invisível) que antes estourava TypeError com traceback cru ou, pior,
corrompia dado em silêncio.

`parse_frontmatter` é testada contra o contrato do parser upstream
(persona.rs:277-319 @ ed4b3e7a), casos espelhados dos testes de lá
(persona.rs:510-532).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Sem isto, o módulo só importa quando OUTRO arquivo de teste insere o path
# primeiro — `pytest tests/test_loader.py` sozinho falhava na coleção. Teste
# que depende da ordem de execução não é teste.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killerbee.loader import (
    MAX_BODY_BYTES,
    PackLoadError,
    load_pack,
    parse_frontmatter,
)

VALID = "---\nname: bot\ndisplay_name: Bot\ndescription: A bot.\n---\nYou are Bot.\n"


# ---------------------------------------------------------------------------
# parse_frontmatter — paridade com split_frontmatter do upstream
# ---------------------------------------------------------------------------


def test_frontmatter_valido():
    data, body = parse_frontmatter(VALID, source="t")
    assert data["name"] == "bot"
    assert body == "You are Bot.\n"


def test_fechamento_em_eof_sem_newline_e_valido():
    # persona.rs:296-298: '---' no EOF fecha.
    data, body = parse_frontmatter("---\nname: bot\n---", source="t")
    assert data["name"] == "bot"
    assert body == ""


def test_crlf_e_aceito():
    data, body = parse_frontmatter("---\r\nname: bot\r\n---\r\ncorpo\r\n", source="t")
    assert data["name"] == "bot"
    assert body == "corpo\r\n"


def test_abertura_com_lixo_na_mesma_linha_nao_abre():
    # persona.rs:283-285: '---texto' não é abertura.
    with pytest.raises(PackLoadError, match="sozinha na linha"):
        parse_frontmatter("---lixo\nname: bot\n---\n", source="t")


def test_fechamento_com_lixo_nao_fecha():
    # persona.rs:517-519: '---junk' não fecha; sem outro '---', é erro.
    with pytest.raises(PackLoadError, match="sem fechamento"):
        parse_frontmatter("---\nname: bot\n---junk\n", source="t")


def test_fechamento_com_lixo_e_pulado_ate_o_fechamento_real():
    # persona.rs:529-532: '---junk' dentro de block scalar é conteúdo, e o
    # '---' real mais adiante fecha.
    src = "---\nname: bot\ndescription: |\n  some text\n  ---junk\n---\nBody here.\n"
    data, body = parse_frontmatter(src, source="t")
    assert data["name"] == "bot"
    assert body == "Body here.\n"


def test_linha_em_branco_no_inicio_do_corpo_e_preservada():
    """O corpo é byte a byte após UM newline do fechamento (persona.rs:312-316).

    A versão anterior fazia lstrip('\\n') — um prompt que começa com linha em
    branco intencional perdia a linha, e o 'verbatim' do site deixava de ser
    verbatim em relação ao arquivo emitido.
    """
    _, body = parse_frontmatter("---\nname: bot\n---\n\n\ncorpo\n", source="t")
    assert body == "\n\ncorpo\n"


def test_bom_utf8_da_erro_especifico():
    with pytest.raises(PackLoadError, match="BOM"):
        parse_frontmatter("﻿" + VALID, source="t")


def test_sem_frontmatter():
    with pytest.raises(PackLoadError, match="sem frontmatter"):
        parse_frontmatter("You are Bot.\n", source="t")


def test_corpo_acima_do_limite_upstream_e_rejeitado():
    # persona.rs:24 + :214: corpo > 256 KiB não passa no parser do app.
    big = "x" * (MAX_BODY_BYTES + 1)
    with pytest.raises(PackLoadError, match="corpo excede"):
        parse_frontmatter(f"---\nname: bot\n---\n{big}", source="t")


def test_yaml_invalido_no_frontmatter():
    with pytest.raises(PackLoadError, match="YAML inválido"):
        parse_frontmatter("---\n: bad: yaml: here\n---\n", source="t")


# ---------------------------------------------------------------------------
# load_pack — estados de edição que não podem virar traceback nem corrupção
# ---------------------------------------------------------------------------


def make_pack(tmp_path, manifest_yaml: str, persona_md: str = VALID):
    pack = tmp_path / "demo-pack"
    (pack / "personas").mkdir(parents=True)
    (pack / "killerbee.yaml").write_text(manifest_yaml, encoding="utf-8")
    (pack / "personas" / "bot.persona.md").write_text(persona_md, encoding="utf-8")
    return pack


MANIFEST_OK = (
    "name: demo-pack\nversion: 0.1.0\nlicense: Apache-2.0\n"
    "personas:\n  - file: personas/bot.persona.md\n"
)


def test_pack_minimo_carrega(tmp_path):
    manifest = load_pack(make_pack(tmp_path, MANIFEST_OK))
    assert manifest.name == "demo-pack"
    assert manifest.personas[0].name == "bot"


def test_secao_personas_nula_e_erro_legivel(tmp_path):
    # `personas:` sem valor — estado comum no meio de uma edição.
    pack = make_pack(tmp_path, "name: demo\nversion: 0.1.0\npersonas:\n")
    manifest = load_pack(pack)  # nula → vazia; quem exige >=1 é o validate
    assert manifest.personas == ()


def test_personas_escalar_e_erro_nao_typeerror(tmp_path):
    pack = make_pack(tmp_path, "name: demo\nversion: 0.1.0\npersonas: oops\n")
    with pytest.raises(PackLoadError, match="deve ser lista"):
        load_pack(pack)


def test_tags_escalar_nao_vira_tupla_de_caracteres(tmp_path):
    # `tags: abc` virava tuple('a','b','c') — catálogo corrompido em silêncio.
    pack = make_pack(tmp_path, MANIFEST_OK + "tags: abc\n")
    with pytest.raises(PackLoadError, match="'tags' deve ser lista"):
        load_pack(pack)


def test_members_escalar_e_erro(tmp_path):
    pack = make_pack(
        tmp_path,
        MANIFEST_OK + "teams:\n  - id: t1\n    name: T\n    members: bot\n",
    )
    with pytest.raises(PackLoadError, match="deve ser lista"):
        load_pack(pack)


def test_channels_lista_vazia_nao_vira_all(tmp_path):
    # O autor que pediu "nenhum canal" não pode ganhar uma regra em TODOS.
    pack = make_pack(
        tmp_path,
        "name: demo\nversion: 0.1.0\npersonas:\n"
        "  - file: personas/bot.persona.md\n    channels: []\n",
    )
    with pytest.raises(PackLoadError, match="ambíguo"):
        load_pack(pack)


def test_channels_ausente_vira_all(tmp_path):
    manifest = load_pack(make_pack(tmp_path, MANIFEST_OK))
    assert manifest.personas[0].channels == ("all",)


def test_model_nao_string_e_erro_legivel(tmp_path):
    # `model: 123` estourava TypeError três camadas depois, no validate.
    persona = "---\nname: bot\ndisplay_name: Bot\ndescription: A.\nmodel: 123\n---\ncorpo\n"
    pack = make_pack(tmp_path, MANIFEST_OK, persona_md=persona)
    with pytest.raises(PackLoadError, match="'model' deve ser string"):
        load_pack(pack)


def test_profile_com_chave_desconhecida_e_erro(tmp_path):
    pack = make_pack(
        tmp_path,
        "name: demo\nversion: 0.1.0\npersonas:\n"
        "  - file: personas/bot.persona.md\n    profile:\n      aggression: 9\n",
    )
    with pytest.raises(PackLoadError, match="chaves desconhecidas"):
        load_pack(pack)


@pytest.mark.parametrize(
    ("valor", "motivo"),
    [
        ("[]", "lista vazia — falsy, engolida em silêncio pelo `or {}` anterior"),
        ("0", "zero — falsy"),
        ("false", "false — falsy"),
        ('""', "string vazia — falsy"),
        ("7", "truthy: já era erro antes, tem que continuar sendo"),
    ],
)
def test_profile_nao_mapeamento_e_erro(tmp_path, valor, motivo):
    """`profile: 0` virava "todos os defaults" calado enquanto `profile: 7` dava
    erro — o mesmo tipo de valor com dois destinos, decidido por truthiness.
    O JSON Schema já rejeitava os dois; o loader é que divergia."""
    pack = make_pack(
        tmp_path,
        "name: demo\nversion: 0.1.0\npersonas:\n"
        f"  - file: personas/bot.persona.md\n    profile: {valor}\n",
    )
    with pytest.raises(PackLoadError, match="'profile' deve ser um mapeamento"):
        load_pack(pack)


@pytest.mark.parametrize("valor", ["[]", "0", "false", '""', "7"])
def test_compat_nao_mapeamento_e_erro(tmp_path, valor):
    pack = make_pack(tmp_path, MANIFEST_OK + f"\ncompat: {valor}\n")
    with pytest.raises(PackLoadError, match="'compat' deve ser um mapeamento"):
        load_pack(pack)


def test_profile_e_compat_nulos_continuam_virando_defaults(tmp_path):
    """Ausente e nulo seguem sendo "use os defaults" — a chave presente e vazia
    durante edição é estado comum e não pode explodir."""
    pack = make_pack(
        tmp_path,
        "name: demo\nversion: 0.1.0\ncompat:\npersonas:\n"
        "  - file: personas/bot.persona.md\n    profile:\n",
    )
    manifest = load_pack(pack)
    assert manifest.buzz_commit == ""
    assert manifest.personas[0].profile.threshold == "medium"
