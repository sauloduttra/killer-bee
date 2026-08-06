"""O gerador de packs: o que ele materializa tem que VALIDAR e BUILDAR.

`scripts/packs_from_specs.py` transforma especificações de persona (uma por
repositório-lab) em packs completos. O teste que importa não é "escreveu
arquivo" — é que a saída passa pelo mesmo `killerbee validate` que um pack
escrito à mão, incluindo o contrato de frontmatter nativo que o parser upstream
aplica com `deny_unknown_fields`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from packs_from_specs import PILLARS  # noqa: E402
from packs_from_specs import main as generate  # noqa: E402
from packs_from_specs import validate as validate_specs  # noqa: E402

from killerbee.cli import main as cli_main  # noqa: E402
from killerbee.loader import load_pack  # noqa: E402
from killerbee.validate import validate_pack  # noqa: E402


def _spec(**overrides) -> dict:
    base = dict(
        repo="convexity-lab",
        slug="convexity",
        display_name="Convexity",
        description="Black-Scholes-Merton analytics with the full Greek set.",
        system_prompt=(
            "## Who you are\nYou are Convexity, an option analytics specialist whose "
            "scope is exactly what the convexity-lab repository implements.\n\n"
            "## What you know\nBlack-Scholes-Merton closed-form pricing with every "
            "first and second order Greek, including the Gamma convexity surface. "
            "Monte Carlo validation with antithetic variates. Implied volatility by "
            "Newton-Raphson with a Brent fallback. Heston stochastic volatility priced "
            "by Fourier inversion of the characteristic function.\n\n"
            "## How you answer\nThe formula comes before the number, the assumptions "
            "come with the formula, and the regime where it stops holding is named.\n\n"
            "## What you do not do\nNo investment advice, no invented market data."
        ),
        threshold="medium",
        recruitment=4,
        persistence="medium",
        propagation="high",
        profile_rationale="responde quando chamada",
        pillar="derivatives-microstructure",
    )
    base.update(overrides)
    return base


def _write_specs(tmp_path: Path, personas: list[dict]) -> Path:
    path = tmp_path / "specs.json"
    path.write_text(json.dumps({"personas": personas}), encoding="utf-8")
    return path


def test_pack_gerado_valida_e_builda(tmp_path):
    """O contrato inteiro: gerar → validar → buildar, sem intervenção."""
    specs = _write_specs(tmp_path, [_spec(), _spec(slug="lob", repo="lob-engine")])
    out = tmp_path / "packs"
    assert generate([str(specs), "--out", str(out)]) == 0

    pack = out / "derivatives-microstructure"
    assert cli_main(["validate", str(pack)]) == 0
    assert cli_main(["build", str(pack), "--out", str(tmp_path / "dist")]) == 0

    manifest = load_pack(pack)
    assert len(manifest.personas) == 2
    assert len(manifest.teams) == 1
    assert manifest.teams[0].members == ("convexity", "lob")
    assert validate_pack(manifest) == []


def test_frontmatter_so_tem_chaves_nativas(tmp_path):
    """Uma chave nossa no frontmatter é erro FATAL no parser upstream
    (persona.rs:174-176). O gerador não pode ser a porta por onde ela entra."""
    specs = _write_specs(tmp_path, [_spec()])
    out = tmp_path / "packs"
    generate([str(specs), "--out", str(out)])

    persona_file = out / "derivatives-microstructure" / "personas" / "convexity.persona.md"
    raw = persona_file.read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(raw.split("---")[1])
    assert set(frontmatter) <= {"name", "display_name", "description", "model", "runtime"}
    # E o perfil scutellata NÃO vazou para lá — ele vive no manifesto.
    assert "threshold" not in frontmatter
    assert "profile" not in frontmatter


def test_prompt_vai_verbatim_para_o_corpo(tmp_path):
    """O corpo É o prompt. Truncar ou reformatar aqui esvaziaria a promessa de
    transparência que o catálogo publica."""
    spec = _spec()
    specs = _write_specs(tmp_path, [spec])
    out = tmp_path / "packs"
    generate([str(specs), "--out", str(out)])

    persona_file = out / "derivatives-microstructure" / "personas" / "convexity.persona.md"
    raw = persona_file.read_text(encoding="utf-8")
    body = raw.split("---", 2)[2].lstrip("\n")
    assert body.strip() == spec["system_prompt"].strip()


def test_model_e_omitido_de_proposito(tmp_path):
    """Forçar provider que o importador não configurou troca uma persona que
    funciona por um erro de credencial. Os campos têm serde default."""
    specs = _write_specs(tmp_path, [_spec()])
    out = tmp_path / "packs"
    generate([str(specs), "--out", str(out)])
    manifest = load_pack(out / "derivatives-microstructure")
    assert manifest.personas[0].model is None


def test_personas_sao_agrupadas_por_pilar(tmp_path):
    specs = _write_specs(
        tmp_path,
        [
            _spec(),
            _spec(slug="var", repo="var-lab", pillar="risk-portfolio"),
            _spec(slug="port", repo="port-lab", pillar="risk-portfolio"),
        ],
    )
    out = tmp_path / "packs"
    assert generate([str(specs), "--out", str(out)]) == 0
    assert (out / "derivatives-microstructure").is_dir()
    assert len(load_pack(out / "risk-portfolio").personas) == 2


# ---------------------------------------------------------------------------
# Entrada inválida falha ANTES de escrever qualquer arquivo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "motivo"),
    [
        (dict(slug="Convexity"), "slug maiúsculo"),
        (dict(slug="my.persona"), "ponto no slug"),
        (dict(recruitment=99), "recruitment fora de 1..=32"),
        (dict(pillar="inventado"), "pilar desconhecido"),
        (dict(system_prompt="curto demais"), "prompt raso"),
        (dict(display_name=""), "campo obrigatório vazio"),
    ],
)
def test_spec_invalida_e_recusada(overrides, motivo):
    assert validate_specs([_spec(**overrides)]), f"aceitou: {motivo}"


def test_slug_duplicado_e_recusado():
    assert validate_specs([_spec(), _spec(repo="outro")])


def test_nada_e_escrito_quando_a_spec_e_invalida(tmp_path):
    specs = _write_specs(tmp_path, [_spec(slug="INVALIDO")])
    out = tmp_path / "packs"
    assert generate([str(specs), "--out", str(out)]) == 1
    assert not out.exists(), "escreveu arquivo apesar da spec inválida"


def test_todo_pilar_declarado_tem_titulo_e_texto():
    for pillar, value in PILLARS.items():
        title, blurb = value
        assert title.strip() and blurb.strip(), pillar
