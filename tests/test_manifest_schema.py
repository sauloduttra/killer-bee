"""schema/killerbee.schema.json é o contrato de editor; killerbee validate é a
autoridade. Duas verdades divergem em silêncio — estes testes cobram a
concordância: o que um rejeita por motivo que o outro sabe expressar, o outro
rejeita também, e o pack real (e o TEMPLATE renomeado) passa nos dois.
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from killerbee.loader import PackLoadError, load_pack  # noqa: E402
from killerbee.validate import validate_pack  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "killerbee.schema.json").read_text(encoding="utf-8"))
PACK = ROOT / "packs" / "crossfire-review"
TEMPLATE = ROOT / "packs" / "TEMPLATE"


def _schema_errors(manifest: dict) -> list[str]:
    validator = jsonschema.Draft202012Validator(SCHEMA)
    return [e.message for e in validator.iter_errors(manifest)]


def test_o_schema_e_um_draft_2020_12_valido():
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_o_pack_real_passa_no_schema_e_no_validador():
    manifest_dict = yaml.safe_load((PACK / "killerbee.yaml").read_text(encoding="utf-8"))
    assert _schema_errors(manifest_dict) == []
    assert validate_pack(load_pack(PACK)) == []


def test_o_template_renomeado_passa_no_schema_e_no_validador(tmp_path):
    """O TEMPLATE promete '10 minutos'; um template que não valida após o
    rename é uma promessa quebrada no primeiro contato."""
    dest = tmp_path / "my-pack"
    shutil.copytree(TEMPLATE, dest)
    (dest / "killerbee.yaml.example").rename(dest / "killerbee.yaml")
    manifest_dict = yaml.safe_load((dest / "killerbee.yaml").read_text(encoding="utf-8"))
    assert _schema_errors(manifest_dict) == []
    assert validate_pack(load_pack(dest)) == []


def test_template_sem_rename_e_invisivel_para_o_catalogo():
    """A regra canônica — pack é diretório com killerbee.yaml — vale para o
    TEMPLATE: com o sufixo .example ele não é um pack."""
    assert not (TEMPLATE / "killerbee.yaml").exists()
    assert (TEMPLATE / "killerbee.yaml.example").is_file()


# ---------------------------------------------------------------------------
# Concordância cruzada: mutação quebrada cai NOS DOIS lados
# ---------------------------------------------------------------------------


def _mutate(base: dict, path: list, value) -> dict:
    mutated = copy.deepcopy(base)
    target = mutated
    for key in path[:-1]:
        target = target[key]
    if value is _DELETE:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return mutated


_DELETE = object()
_BASE = yaml.safe_load((PACK / "killerbee.yaml").read_text(encoding="utf-8"))

_BROKEN = {
    "name_maiusculo": (["name"], "CrossFire"),
    "name_reservado_windows": (["name"], "nul"),
    "version_nao_semver": (["version"], "v1"),
    "license_ausente": (["license"], _DELETE),
    "personas_vazias": (["personas"], []),
    "recruitment_zero": (["personas", 0, "profile", "recruitment"], 0),
    "recruitment_33": (["personas", 0, "profile", "recruitment"], 33),
    "threshold_invalido": (["personas", 0, "profile", "threshold"], "max"),
    "chave_desconhecida_no_profile": (["personas", 0, "profile", "swarm"], 9),
    "channels_vazio": (["personas", 0, "channels"], []),
    "channels_all_misturado": (["personas", 0, "channels"], ["all", "not-a-uuid"]),
    "team_id_com_dois_pontos": (["teams", 0, "id"], "builtin-team:welcome"),
    "team_sem_membros": (["teams", 0, "members"], []),
}


@pytest.mark.parametrize("case", sorted(_BROKEN))
def test_mutacao_quebrada_falha_no_schema(case):
    path, value = _BROKEN[case]
    assert _schema_errors(_mutate(_BASE, path, value)), (
        f"schema aceitou '{case}' — o validador rejeita, e o editor ficaria mudo"
    )


@pytest.mark.parametrize("case", sorted(_BROKEN))
def test_mutacao_quebrada_falha_no_caminho_python(case, tmp_path):
    """O mesmo YAML mutado, escrito em disco e carregado de verdade: ou o
    loader levanta PackLoadError, ou validate_pack devolve erro. Nunca passa."""
    path, value = _BROKEN[case]
    dest = tmp_path / "mutated"
    shutil.copytree(PACK, dest)
    (dest / "killerbee.yaml").write_text(
        yaml.safe_dump(_mutate(_BASE, path, value), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    try:
        manifest = load_pack(dest)
    except PackLoadError:
        return  # rejeitado no loader — concordância satisfeita
    assert validate_pack(manifest), (
        f"o caminho Python aceitou '{case}' que o schema rejeita — duas verdades"
    )
