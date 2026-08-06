"""verify_citations: os três estados + os dois de coleta, contra um git real.

Regra do repo (D-032): cada teste nomeia a mutação que mata.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from verify_citations import (  # noqa: E402
    Upstream,
    compare_states,
    parse_citations,
    resolve_path,
    slice_lines,
    verify_doc,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def upstream_repo(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, str]:
    """Repo com dois commits: pin (v1) e head (v2 com deriva e remoção)."""
    repo = tmp_path_factory.mktemp("up")
    _git(repo, "init", "-q")
    src = repo / "crates" / "x" / "src"
    src.mkdir(parents=True)
    (src / "lib.rs").write_text("l1\nl2\nl3\nl4\nl5\n", encoding="utf-8")
    (src / "gone.rs").write_text("g1\ng2\n", encoding="utf-8")
    other = repo / "crates" / "y" / "src"
    other.mkdir(parents=True)
    # segundo lib.rs de propósito: basename solto "lib.rs" tem que ser ambíguo
    (other / "lib.rs").write_text("o1\n", encoding="utf-8")
    (repo / "unico.toml").write_text("a = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "v1")
    pin = (
        subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, check=True
        )
        .stdout.decode()
        .strip()
    )

    (src / "lib.rs").write_text("l1\nl2-MUDOU\nl3\nl4\nl5\n", encoding="utf-8")
    (src / "gone.rs").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "v2")
    head = (
        subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, check=True
        )
        .stdout.decode()
        .strip()
    )
    return repo, pin, head


# ── camadas puras ────────────────────────────────────────────────────────────


def test_parse_citations_intervalo_e_linha_unica():
    """Mata: regex sem o grupo de intervalo, ou 0-indexação do doc_line."""
    text = "veja `crates/x/src/lib.rs:2-4` e\ntambém tenant.rs:121."
    cits = parse_citations(text, "d.md")
    assert [(c.path, c.start, c.end, c.doc_line) for c in cits] == [
        ("crates/x/src/lib.rs", 2, 4, 1),
        ("tenant.rs", 121, 121, 2),
    ]


def test_slice_lines_bordas():
    """Mata: off-by-one no recorte (start-1) e o None de estouro virar ''."""
    assert slice_lines("a\nb\nc\n", 2, 2) == "b"
    assert slice_lines("a\nb\nc\n", 2, 99) == "b\nc"
    assert slice_lines("a\nb\nc\n", 4, 5) is None


def test_compare_states_os_quatro():
    """Mata: trocar a precedência (pin ausente TEM que ganhar de novo ausente)."""
    assert compare_states(None, "x")[0] == "quebrada@pin"
    assert compare_states(None, None)[0] == "quebrada@pin"
    assert compare_states("x", None)[0] == "quebrada"
    assert compare_states("x", "x")[0] == "confirmada"
    assert compare_states("x", "y")[0] == "deriva"


def test_resolve_path_unico_ambiguo_ausente():
    """Mata: basename casando por substring, ou ambíguo resolvendo calado."""
    tree = ["crates/x/src/lib.rs", "crates/y/src/lib.rs", "unico.toml"]
    assert resolve_path("crates/x/src/lib.rs", tree)[0] == "crates/x/src/lib.rs"
    assert resolve_path("x/src/lib.rs", tree)[0] == "crates/x/src/lib.rs"
    assert resolve_path("unico.toml", tree)[0] == "unico.toml"
    assert resolve_path("lib.rs", tree)[0] is None  # 2 candidatos
    assert resolve_path("nada.rs", tree)[0] is None  # 0 candidatos


# ── contra o git real ────────────────────────────────────────────────────────


def test_verify_doc_produz_os_cinco_estados(upstream_repo: tuple[Path, str, str], tmp_path: Path):
    """End-to-end: cada estado aparece exatamente onde deveria.
    Mata: cache de show vazando entre commits, e qualquer estado engolido."""
    repo, pin, head = upstream_repo
    doc = tmp_path / "doc.md"
    doc.write_text(
        "confirmada: `crates/x/src/lib.rs:3`\n"
        "deriva: `crates/x/src/lib.rs:2`\n"
        "quebrada: `crates/x/src/gone.rs:1`\n"
        "quebrada@pin: `crates/x/src/lib.rs:99`\n"
        "atalho com contexto: `lib.rs:1`; ilegível: `naoexiste.rs:1`\n",
        encoding="utf-8",
    )
    up = Upstream(repo)
    tree = up.ls_files(pin)
    states = {
        f"{v.citation.path}:{v.citation.start}": v.state
        for v in verify_doc(doc, up, pin, head, tree)
    }
    assert states == {
        "crates/x/src/lib.rs:3": "confirmada",
        "crates/x/src/lib.rs:2": "deriva",
        "crates/x/src/gone.rs:1": "quebrada",
        "crates/x/src/lib.rs:99": "quebrada@pin",
        "lib.rs:1": "confirmada",  # atalho herda o contexto qualificado do doc
        "naoexiste.rs:1": "ilegível",
    }


def test_atalho_resolve_por_contexto_do_doc(upstream_repo, tmp_path):
    """Basename ambíguo herda a última menção qualificada DO MESMO doc.
    Mata: popular o contexto antes de resolver (auto-referência) ou nunca."""
    repo, pin, head = upstream_repo
    doc = tmp_path / "d.md"
    doc.write_text(
        "qualificada: `crates/x/src/lib.rs:3`\ndepois o atalho `lib.rs:3`\n",
        encoding="utf-8",
    )
    up = Upstream(repo)
    verdicts = verify_doc(doc, up, pin, head, up.ls_files(pin))
    assert [v.state for v in verdicts] == ["confirmada", "confirmada"]
    assert verdicts[1].detail == "resolvida por contexto do doc"


def test_atalho_sem_contexto_continua_ilegivel(upstream_repo, tmp_path):
    """Sem menção qualificada anterior, ambíguo NÃO resolve — nada de chute.
    Mata: contexto global entre docs ou fallback para o primeiro candidato."""
    repo, pin, head = upstream_repo
    doc = tmp_path / "d.md"
    doc.write_text("só o atalho `lib.rs:3`\n", encoding="utf-8")
    up = Upstream(repo)
    verdicts = verify_doc(doc, up, pin, head, up.ls_files(pin))
    assert [v.state for v in verdicts] == ["ilegível"]


def test_citacao_local_verifica_no_nosso_repo(upstream_repo, tmp_path):
    """Caminho inexistente no upstream mas presente no projeto (raiz ou site/)
    vira local-ok/local-quebrada. Mata: tratar local como ilegível ou aceitar
    intervalo estourado em arquivo local."""
    repo, pin, head = upstream_repo
    project = tmp_path / "proj"
    (project / "site" / "app").mkdir(parents=True)
    (project / "site" / "app" / "layout.tsx").write_text("a\nb\n", encoding="utf-8")
    doc = tmp_path / "d.md"
    doc.write_text("`app/layout.tsx:2` e `app/layout.tsx:9`\n", encoding="utf-8")
    up = Upstream(repo)
    verdicts = verify_doc(doc, up, pin, head, up.ls_files(pin), project_root=project)
    assert [v.state for v in verdicts] == ["local-ok", "local-quebrada"]


def test_upstream_ilegivel_e_erro_ruidoso(tmp_path: Path):
    """Mata: assert_readable virar warning — coleta falha TEM que parar tudo."""
    up = Upstream(tmp_path / "nao-e-repo")
    with pytest.raises(SystemExit, match="ilegível"):
        up.assert_readable("HEAD")


def test_pin_igual_ao_head_confirma_o_proprio_catalogo(upstream_repo, tmp_path):
    """pin == at: tudo que resolve é confirmada (baseline sã do detector).
    Mata: comparar pin com working tree em vez de commit com commit."""
    repo, pin, _ = upstream_repo
    doc = tmp_path / "d.md"
    doc.write_text("`crates/x/src/lib.rs:1-5` e `crates/x/src/gone.rs:2`\n", encoding="utf-8")
    up = Upstream(repo)
    verdicts = verify_doc(doc, up, pin, pin, up.ls_files(pin))
    assert [v.state for v in verdicts] == ["confirmada", "confirmada"]
