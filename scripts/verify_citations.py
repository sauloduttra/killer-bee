"""Revalida citações `arquivo:linha` dos docs contra o upstream — P5 do FASE-2.

É exatamente o que o FASE-2 §1 promete: `git show` + comparação de string.
Sem modelo — verificador com não-determinismo não é verificador.

Nome com underscore (o FASE-2 escreve `verify-citations.py`): hífen não importa
em Python e os testes do repo importam o módulo, como em packs_from_specs.

Três estados por citação, NUNCA "ok" por omissão:
- ``confirmada`` — o texto das linhas citadas é idêntico entre o commit pinado e
  o commit novo.
- ``deriva``    — o arquivo existe no commit novo, mas o texto das linhas mudou.
- ``quebrada``  — o arquivo sumiu ou o intervalo saiu dos limites no commit novo.

E dois estados de coleta, reportados com o mesmo barulho (lição do gitleaks que
"varreu" zero bytes — falha de coleta NÃO é ausência de dado, D-014):
- ``quebrada@pin`` — a citação já não bate NO COMMIT PINADO: estava errada quando
  escrita, ou o pin está errado. É o pior estado e falha o build.
- ``ilegível``     — basename sem resolução única no upstream (zero ou 2+
  candidatos). Nunca é descartada em silêncio.

Saída: relatório por documento + contagens. Exit codes:
- 2: upstream ilegível OU zero citações coletadas (sabemos que os docs citam;
  zero coletado é falha do coletor, não catálogo limpo).
- 1: qualquer ``quebrada`` ou ``quebrada@pin`` (com ``--strict``, deriva também).
- 0: caso contrário; derivas são listadas mesmo assim.

Uso:
    uv run python scripts/verify_citations.py \
        --upstream D:/EMPRESAS/buzz/_upstream/buzz \
        [--pin <sha>] [--at <sha|HEAD>] [--strict] [--json] [docs...]

O pin default vem de packs/crossfire-review/killerbee.yaml (compat.buzz_commit),
que é a fonte pinada de verdade do projeto.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Extensões que aparecem em citações de código do upstream nos nossos docs.
CITATION_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_\-./]+\.(?:rs|ts|tsx|mjs|py|toml|ya?ml|json|conf|md))"
    r":(?P<start>\d+)(?:-(?P<end>\d+))?"
)


@dataclass(frozen=True)
class Citation:
    doc: str
    doc_line: int
    path: str
    start: int
    end: int


@dataclass
class Verdict:
    citation: Citation
    state: str  # confirmada | deriva | quebrada | quebrada@pin | ilegível
    detail: str
    resolved_path: str | None = None


# ── camada pura ──────────────────────────────────────────────────────────────


def parse_citations(doc_text: str, doc_name: str) -> list[Citation]:
    """Extrai toda citação `arquivo:linha[-linha]` de um markdown nosso."""
    found: list[Citation] = []
    for lineno, line in enumerate(doc_text.splitlines(), start=1):
        for m in CITATION_RE.finditer(line):
            start = int(m.group("start"))
            end = int(m.group("end") or start)
            if start <= 0 or end < start:
                # Intervalo sem sentido é citação quebrada por construção;
                # entra para o relatório em vez de sumir no parse.
                end = start
            found.append(
                Citation(doc=doc_name, doc_line=lineno, path=m.group("path"), start=start, end=end)
            )
    return found


def slice_lines(file_text: str, start: int, end: int) -> str | None:
    """Linhas [start, end] 1-indexadas, ou None se o intervalo estoura o arquivo."""
    lines = file_text.splitlines()
    if start > len(lines):
        return None
    return "\n".join(lines[start - 1 : min(end, len(lines))])


def compare_states(pin_slice: str | None, at_slice: str | None) -> tuple[str, str]:
    """Decide o estado a partir dos dois recortes (None = arquivo/intervalo ausente)."""
    if pin_slice is None:
        return "quebrada@pin", "arquivo ou intervalo inexistente no commit pinado"
    if at_slice is None:
        return "quebrada", "arquivo ou intervalo inexistente no commit novo"
    if pin_slice == at_slice:
        return "confirmada", ""
    return "deriva", "texto das linhas citadas mudou entre pin e novo"


# ── camada git (impura, isolada) ─────────────────────────────────────────────


class Upstream:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir

    def _git(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(self.repo_dir), *args],
            capture_output=True,
            timeout=120,
            check=False,
        )

    def assert_readable(self, commit: str) -> None:
        """Falha ruidosa se o upstream não puder ser lido — nunca 'ok' vazio."""
        probe = self._git("rev-parse", "--verify", f"{commit}^{{commit}}")
        if probe.returncode != 0:
            raise SystemExit(
                f"ERRO(2): upstream ilegível em {self.repo_dir} @ {commit}: "
                f"{probe.stderr.decode('utf-8', 'replace').strip()}"
            )

    def ls_files(self, commit: str) -> list[str]:
        out = self._git("ls-tree", "-r", "--name-only", commit)
        if out.returncode != 0:
            raise SystemExit(
                f"ERRO(2): git ls-tree falhou em {self.repo_dir} @ {commit}: "
                f"{out.stderr.decode('utf-8', 'replace').strip()}"
            )
        return out.stdout.decode("utf-8", "replace").splitlines()

    def show(self, commit: str, path: str) -> str | None:
        out = self._git("show", f"{commit}:{path}")
        if out.returncode != 0:
            return None
        return out.stdout.decode("utf-8", "replace")


def resolve_path(cited: str, tree_paths: list[str]) -> tuple[str | None, str]:
    """Resolve a citação para um caminho único da árvore pinada.

    Caminho com '/' precisa bater por sufixo exato; basename solto resolve se
    houver exatamente UM arquivo com aquele basename. 0 ou 2+ → ilegível.
    """
    if cited in tree_paths:
        return cited, ""
    if "/" in cited:
        matches = [p for p in tree_paths if p.endswith("/" + cited)]
    else:
        matches = [p for p in tree_paths if p.rsplit("/", 1)[-1] == cited]
    if len(matches) == 1:
        return matches[0], ""
    if not matches:
        return None, "nenhum arquivo com esse nome na árvore pinada"
    return None, f"{len(matches)} candidatos: {', '.join(sorted(matches)[:4])}…"


# ── orquestração ─────────────────────────────────────────────────────────────


def resolve_local(cited: str, project_root: Path) -> Path | None:
    """Citação do NOSSO repo (site/, killerbee/, tests/): caminho real ou None.

    Os docs citam o site com raiz implícita em ``site/`` (ex.: ``app/layout.tsx``).
    """
    for base in (project_root, project_root / "site"):
        candidate = base / cited
        if candidate.is_file():
            return candidate
    return None


def verify_doc(
    doc_path: Path,
    upstream: Upstream,
    pin: str,
    at: str,
    tree_at_pin: list[str],
    project_root: Path | None = None,
) -> list[Verdict]:
    text = doc_path.read_text(encoding="utf-8")
    verdicts: list[Verdict] = []
    show_cache: dict[tuple[str, str], str | None] = {}
    # O doc qualifica o caminho na primeira menção e abrevia depois; espelhamos
    # essa convenção: basename curto herda a última resolução qualificada do doc.
    seen_by_basename: dict[str, str] = {}

    def cached_show(commit: str, path: str) -> str | None:
        key = (commit, path)
        if key not in show_cache:
            show_cache[key] = upstream.show(commit, path)
        return show_cache[key]

    for cit in parse_citations(text, doc_path.name):
        context_note = ""
        resolved, why = resolve_path(cit.path, tree_at_pin)
        if resolved is None and "/" not in cit.path and cit.path in seen_by_basename:
            resolved, context_note = seen_by_basename[cit.path], "resolvida por contexto do doc"
        if resolved is None:
            local = resolve_local(cit.path, project_root) if project_root else None
            if local is not None:
                local_text = local.read_text(encoding="utf-8", errors="replace")
                if slice_lines(local_text, cit.start, cit.end) is None:
                    verdicts.append(
                        Verdict(cit, "local-quebrada", "intervalo fora do arquivo local")
                    )
                else:
                    verdicts.append(Verdict(cit, "local-ok", "", str(local)))
                continue
            verdicts.append(Verdict(cit, "ilegível", why))
            continue
        seen_by_basename[resolved.rsplit("/", 1)[-1]] = resolved
        pin_text = cached_show(pin, resolved)
        at_text = cached_show(at, resolved)
        pin_slice = slice_lines(pin_text, cit.start, cit.end) if pin_text is not None else None
        at_slice = slice_lines(at_text, cit.start, cit.end) if at_text is not None else None
        state, detail = compare_states(pin_slice, at_slice)
        if context_note:
            detail = f"{detail}; {context_note}" if detail else context_note
        verdicts.append(Verdict(cit, state, detail, resolved))
    return verdicts


def default_pin(repo_root: Path) -> str:
    manifest = repo_root / "packs" / "crossfire-review" / "killerbee.yaml"
    m = re.search(r"buzz_commit:\s*([0-9a-f]{40})", manifest.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"ERRO(2): compat.buzz_commit não encontrado em {manifest}")
    return m.group(1)


def main(argv: list[str] | None = None) -> int:
    # Windows com stdout em pipe cai para cp1252 e '→'/acentos explodem ou
    # viram mojibake — mesma classe de bug já paga no CLI (ver HANDOFF).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    repo_root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream", type=Path, default=Path("D:/EMPRESAS/buzz/_upstream/buzz"))
    ap.add_argument("--pin", default=None, help="commit em que as citações foram verificadas")
    ap.add_argument("--at", default="HEAD", help="commit novo contra o qual revalidar")
    ap.add_argument("--strict", action="store_true", help="deriva também falha (exit 1)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument(
        "docs",
        nargs="*",
        type=Path,
        default=None,
        help="markdowns a verificar (default: docs/PROTOCOL-NOTES.md)",
    )
    args = ap.parse_args(argv)

    pin = args.pin or default_pin(repo_root)
    docs = args.docs or [repo_root / "docs" / "PROTOCOL-NOTES.md"]

    upstream = Upstream(args.upstream)
    upstream.assert_readable(pin)
    upstream.assert_readable(args.at)
    tree_at_pin = upstream.ls_files(pin)

    all_verdicts: list[Verdict] = []
    for doc in docs:
        all_verdicts.extend(
            verify_doc(doc, upstream, pin, args.at, tree_at_pin, project_root=repo_root)
        )

    if not all_verdicts:
        print("ERRO(2): zero citações coletadas — falha de coleta não é ausência de dado")
        return 2

    counts: dict[str, int] = {}
    for v in all_verdicts:
        counts[v.state] = counts.get(v.state, 0) + 1

    if args.as_json:
        payload = {
            "pin": pin,
            "at": args.at,
            "contagens": counts,
            "vereditos": [
                {
                    "doc": v.citation.doc,
                    "doc_line": v.citation.doc_line,
                    "citação": f"{v.citation.path}:{v.citation.start}"
                    + (f"-{v.citation.end}" if v.citation.end != v.citation.start else ""),
                    "resolvida": v.resolved_path,
                    "estado": v.state,
                    "detalhe": v.detail,
                }
                for v in all_verdicts
            ],
        }
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=1)
    else:
        for v in all_verdicts:
            if v.state != "confirmada":
                loc = f"{v.citation.doc}:{v.citation.doc_line}"
                print(f"{v.state:<13} {loc:<28} {v.citation.path}:{v.citation.start} {v.detail}")
        parts = "  ".join(f"{k}={n}" for k, n in sorted(counts.items()))
        print(f"\npin={pin[:12]} at={args.at}  {parts}")

    hard_fail = (
        counts.get("quebrada", 0) + counts.get("quebrada@pin", 0) + counts.get("local-quebrada", 0)
    )
    if args.strict:
        hard_fail += counts.get("deriva", 0)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
