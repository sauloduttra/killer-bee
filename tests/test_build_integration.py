"""Integração: o pack real do repo valida, builda, e o que sai é o que o
desktop importaria. Único teste que toca disco — e só em tmp_path e no pack
versionado (leitura).
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from killerbee.cli import main  # noqa: E402
from killerbee.pngtext import read_snapshot_from_png  # noqa: E402
from killerbee.validate import EVENT_CONTENT_MAX_BYTES  # noqa: E402

PACK = ROOT / "packs" / "crossfire-review"


def test_validate_do_pack_real_sai_zero(capsys):
    assert main(["validate", str(PACK)]) == 0
    assert "OK: crossfire-review" in capsys.readouterr().out


def test_validate_de_pack_quebrado_sai_um(tmp_path, capsys):
    """O DoD pede o CI falhando em pack inválido — este é o contrato."""
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "killerbee.yaml").write_text(
        "name: Broken Name\nversion: not-semver\npersonas: []\n", encoding="utf-8"
    )
    assert main(["validate", str(broken)]) == 1
    err = capsys.readouterr().err
    assert "slug" in err and "semver" in err and "licença" in err.lower()


def test_build_emite_tudo_e_no_formato_do_desktop(tmp_path):
    assert main(["build", str(PACK), "--out", str(tmp_path)]) == 0
    out = tmp_path / "crossfire-review"

    # ── agent.json de cada persona ───────────────────────────────────────
    for name in ("forager", "adversary", "guard"):
        agent = json.loads((out / f"{name}.agent.json").read_text(encoding="utf-8"))
        assert agent["format"] == "buzz-agent-snapshot"
        assert agent["version"] == 1
        assert agent["definition"]["systemPrompt"].strip()
        assert 1 <= agent["definition"]["parallelism"] <= 32
        # PNG carrega o MESMO snapshot
        png = (out / f"{name}.agent.png").read_bytes()
        assert read_snapshot_from_png(png, "buzz_agent_snapshot") == agent

    # ── team embute os três, na ordem do manifesto ───────────────────────
    team = json.loads((out / "crossfire-review.team.json").read_text(encoding="utf-8"))
    assert team["format"] == "buzz-team-snapshot"
    assert [m["definition"]["name"] for m in team["members"]] == [
        "Forager",
        "Adversary",
        "Guard",
    ]

    # ── três providers DISTINTOS — a tese do crossfire ───────────────────
    providers = {m["definition"]["provider"] for m in team["members"]}
    assert len(providers) == 3, f"crossfire degenerou em eco: {providers}"

    # ── regras ACP: menção explícita em toda regra ───────────────────────
    rules = tomllib.loads((out / "acp-rules.toml").read_text(encoding="utf-8"))
    assert len(rules["rules"]) == 3
    assert all("require_mention" in rule for rule in rules["rules"])

    # ── catálogo para o site, com prompt na íntegra ──────────────────────
    catalog = json.loads((out / "catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["personas"]) == 3
    for entry in catalog["personas"]:
        assert entry["systemPrompt"].strip()  # transparência é o produto


def test_team_real_cabe_em_um_evento_30178(tmp_path):
    """Q-006 respondida por medição, não por esperança."""
    main(["build", str(PACK), "--out", str(tmp_path)])
    raw = (tmp_path / "crossfire-review" / "crossfire-review.team.json").read_bytes()
    assert len(raw) <= EVENT_CONTENT_MAX_BYTES, (
        f"team snapshot com {len(raw):,} bytes estoura o corpo de evento "
        f"({EVENT_CONTENT_MAX_BYTES:,}); a projeção L3 precisa encolher"
    )


def test_build_e_deterministico(tmp_path):
    """Mesmo pack, mesmos bytes. Sem relógio, sem aleatoriedade no emissor."""
    main(["build", str(PACK), "--out", str(tmp_path / "a")])
    main(["build", str(PACK), "--out", str(tmp_path / "b")])
    for name in ("forager.agent.json", "crossfire-review.team.json", "acp-rules.toml"):
        first = (tmp_path / "a" / "crossfire-review" / name).read_bytes()
        second = (tmp_path / "b" / "crossfire-review" / name).read_bytes()
        assert first == second, f"{name} não é determinístico"


# ---------------------------------------------------------------------------
# sha256 no catálogo — o hash publicado TEM que bater com o arquivo emitido
# ---------------------------------------------------------------------------


def test_catalogo_do_build_publica_sha256_que_bate_com_o_arquivo(tmp_path):
    import hashlib

    assert main(["build", str(PACK), "--out", str(tmp_path)]) == 0
    out = tmp_path / "crossfire-review"
    catalog = json.loads((out / "catalog.json").read_text(encoding="utf-8"))
    entries = [f for p in catalog["personas"] for f in p["files"]]
    entries += [f for t in catalog["teams"] for f in t["files"]]
    assert entries, "catálogo sem files — o hash é o que torna o download verificável"
    for entry in entries:
        raw = (out / entry["name"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], entry["name"]
        assert len(raw) == entry["bytes"], entry["name"]


def test_catalog_do_site_publica_o_mesmo_sha256_do_build(tmp_path):
    """`catalog` (site) e `build` (downloads) serializam nos MESMOS bytes —
    se divergirem, o hash na página mente sobre o arquivo baixado."""
    import hashlib

    assert main(["build", str(PACK), "--out", str(tmp_path / "dist")]) == 0
    out_file = tmp_path / "catalog.json"
    assert main(["catalog", "--packs", str(PACK.parent), "--out", str(out_file)]) == 0
    site_catalog = json.loads(out_file.read_text(encoding="utf-8"))
    dist = tmp_path / "dist" / "crossfire-review"
    for pack in site_catalog["packs"]:
        for persona in pack["personas"]:
            for entry in persona["files"]:
                raw = (dist / entry["name"]).read_bytes()
                assert hashlib.sha256(raw).hexdigest() == entry["sha256"], entry["name"]


def test_catalog_nao_vaza_caminho_absoluto(tmp_path):
    out_file = tmp_path / "catalog.json"
    assert main(["catalog", "--packs", str(PACK.parent), "--out", str(out_file)]) == 0
    generated_from = json.loads(out_file.read_text(encoding="utf-8"))["generatedFrom"]
    assert ":" not in generated_from and not generated_from.startswith("/"), (
        f"generatedFrom vaza caminho da máquina: {generated_from!r}"
    )


def test_cli_sobrevive_a_console_cp1252(tmp_path):
    """Windows: stdout em pipe nasce cp1252 e o '→' dos relatórios crashava o
    CLI inteiro (UnicodeEncodeError) — visto no `npm run build` local, invisível
    no CI Linux. PYTHONIOENCODING=cp1252 reproduz a condição em qualquer
    plataforma; o reconfigure em main() tem que vencê-la."""
    import os
    import subprocess

    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    result = subprocess.run(
        [sys.executable, "-m", "killerbee", "build", str(PACK), "--out", str(tmp_path)],
        capture_output=True,
        env=env,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert "→" in result.stdout.decode("utf-8")


# ---------------------------------------------------------------------------
# killerbee inspect — leia antes de rodar, em forma de comando
# ---------------------------------------------------------------------------


def test_inspect_agent_json(tmp_path, capsys):
    assert main(["build", str(PACK), "--out", str(tmp_path)]) == 0
    target = tmp_path / "crossfire-review" / "forager.agent.json"
    assert main(["inspect", str(target)]) == 0
    out = capsys.readouterr().out
    assert "buzz-agent-snapshot" in out
    assert "Forager" in out
    assert "sha256:" in out
    assert "systemPrompt:" in out


def test_inspect_team_png_lista_membros(tmp_path, capsys):
    """O .team.png parece imagem e carrega três agentes — inspect mostra."""
    assert main(["build", str(PACK), "--out", str(tmp_path)]) == 0
    target = tmp_path / "crossfire-review" / "crossfire-review.team.png"
    assert main(["inspect", str(target)]) == 0
    out = capsys.readouterr().out
    assert "buzz-team-snapshot" in out
    assert "members: 3" in out
    assert "Adversary" in out


def test_inspect_prompt_imprime_o_prompt_verbatim(tmp_path, capsys):
    assert main(["build", str(PACK), "--out", str(tmp_path)]) == 0
    target = tmp_path / "crossfire-review" / "forager.agent.json"
    prompt = json.loads(target.read_text(encoding="utf-8"))["definition"]["systemPrompt"]
    assert main(["inspect", str(target), "--prompt"]) == 0
    assert prompt.splitlines()[0] in capsys.readouterr().out


def test_inspect_arquivo_que_nao_e_snapshot_sai_um(tmp_path, capsys):
    alien = tmp_path / "nada.agent.json"
    alien.write_text("não sou json", encoding="utf-8")
    assert main(["inspect", str(alien)]) == 1
    assert "nem PNG nem JSON" in capsys.readouterr().err
