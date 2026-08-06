"""Renderiza SPEC-VS-IMPL.md e NEGATIVE-SPACE.md a partir de docs/evidence/*.json.

Os JSONs são a evidência bruta da rodada de verificação de 2026-08-06 (leque de
leitores + céticos adversariais sobre block/buzz @ ed4b3e7a), no espírito do P6:
o dado estruturado mora ao lado do markdown, e o markdown é DERIVADO — editar os
docs à mão diverge; edite o JSON ou regenere.

Stdlib-only. Determinístico. `uv run python scripts/evidence_to_docs.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PIN = "ed4b3e7afafb5f5a688c210f39b90d747e6f0f00"

STATE_PT = {
    "implemented": "✅ documentado E implementado",
    "absent": "⛔ documentado e AUSENTE",
    "divergent": "≠ documentado DIVERGENTE do implementado",
    "confirmed": "🗓 documentado como futuro (e de fato ausente)",
    "refuted": "❌ REFUTADA — nosso doc estava errado",
    "partial": "⚠️ parcial — precisa de nuance",
}


def cite(e: dict) -> str:
    return f"`{e['file']}:{e['lines']}`"


def first_cites(row: dict, n: int = 2) -> str:
    return " · ".join(cite(e) for e in row.get("evidence", [])[:n]) or "—"


def trim(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_spec(ev_dir: Path) -> str:
    rows = json.loads((ev_dir / "spec_rows.json").read_text(encoding="utf-8"))
    reverse = json.loads((ev_dir / "reverse_gaps.json").read_text(encoding="utf-8"))
    order = {"absent": 0, "divergent": 1, "confirmed": 2, "implemented": 3}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["id"]))
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    out: list[str] = []
    out.append("# Spec vs implementação — `PERSONA_PACK_SPEC.md` contra o código\n")
    out.append(f"**Commit:** `{PIN[:12]}` · **Gerado por** `scripts/evidence_to_docs.py` a partir")
    out.append("de [`evidence/spec_rows.json`](evidence/spec_rows.json) — edite lá, não aqui.\n")
    out.append("O documento que ninguém tem: uma linha por funcionalidade que o spec descreve,")
    out.append("quatro estados, citação dos dois lados. Um mantenedor lê isto e vê em cinco")
    out.append("minutos onde a própria casa está desalinhada.\n")
    out.append("| estado | linhas |")
    out.append("|---|---|")
    for status in ("implemented", "divergent", "absent", "confirmed"):
        out.append(f"| {STATE_PT[status]} | {counts.get(status, 0)} |")
    out.append(f"| [+] implementado e NÃO documentado (direção reversa) | {len(reverse)} |")
    out.append("")

    for status in ("absent", "divergent", "confirmed", "implemented"):
        out.append(f"\n## {STATE_PT[status]} ({counts.get(status, 0)})\n")
        out.append("| id | funcionalidade | evidência | nota |")
        out.append("|---|---|---|---|")
        for r in rows:
            if r["status"] != status:
                continue
            out.append(
                f"| {r['id']} | {trim(r['claim'], 120)} | {first_cites(r)} "
                f"| {trim(r.get('notes', ''), 260)} |"
            )

    out.append("\n## [+] Implementado e não documentado no spec (direção reversa)\n")
    out.append("| id | comportamento | evidência | nota |")
    out.append("|---|---|---|---|")
    for r in reverse:
        out.append(
            f"| {r['id']} | {trim(r['claim'], 140)} | {first_cites(r)} "
            f"| {trim(r.get('notes', ''), 260)} |"
        )
    out.append("")
    return "\n".join(out)


def render_negative(ev_dir: Path) -> str:
    rows = json.loads((ev_dir / "neg_rows.json").read_text(encoding="utf-8"))
    order = {"refuted": 0, "partial": 1, "confirmed": 2}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["id"]))
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    out: list[str] = []
    out.append("# Espaço negativo — toda afirmação de ausência, com o método junto\n")
    out.append(f"**Commit:** `{PIN[:12]}` · **Gerado por** `scripts/evidence_to_docs.py` a partir")
    out.append("de [`evidence/neg_rows.json`](evidence/neg_rows.json) — edite lá, não aqui.\n")
    out.append("Afirmação negativa é a mais frágil e a mais valiosa. Sem o método de busca")
    out.append("junto, é ausência de evidência vendida como evidência de ausência. Cada")
    out.append("entrada carrega: o que foi buscado, quantos falsos positivos foram")
    out.append("descartados, e **o que a tornaria falsa**.\n")
    out.append(
        f"Placar da re-verificação adversarial (2026-08-06): {counts.get('confirmed', 0)} "
        f"confirmadas · {counts.get('partial', 0)} parciais · "
        f"**{counts.get('refuted', 0)} refutadas** — as refutadas estavam publicadas e "
        "foram corrigidas ([D-035](DECISIONS.md)). O detector funcionando é a notícia boa."
    )

    for r in rows:
        out.append(f"\n---\n\n## [{r['id']}] {STATE_PT.get(r['status'], r['status'])}\n")
        out.append(f"**Afirmação:** {r['claim']}\n")
        if r.get("evidence"):
            out.append("**Evidência:** " + " · ".join(cite(e) for e in r["evidence"][:5]) + "\n")
        sm = r.get("search_method")
        if sm:
            out.append("**Método de busca:**\n")
            for c in sm.get("commands", []):
                out.append(f"- `{trim(c, 220)}`")
            if sm.get("false_positives"):
                out.append(f"\n**Falsos positivos:** {trim(sm['false_positives'], 400)}\n")
            if sm.get("falsifier"):
                out.append(f"**O que a tornaria falsa:** {trim(sm['falsifier'], 400)}\n")
        if r.get("notes"):
            out.append(f"**Nota:** {trim(r['notes'], 700)}\n")
    out.append("")
    return "\n".join(out)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    ev_dir = repo_root / "docs" / "evidence"
    for name in ("spec_rows.json", "neg_rows.json", "reverse_gaps.json"):
        if not (ev_dir / name).is_file():
            print(f"ERRO: falta {ev_dir / name} — nada gerado (falha ruidosa, não doc vazio)")
            return 2
    (repo_root / "docs" / "SPEC-VS-IMPL.md").write_text(render_spec(ev_dir), encoding="utf-8")
    (repo_root / "docs" / "NEGATIVE-SPACE.md").write_text(render_negative(ev_dir), encoding="utf-8")
    print("gerados: docs/SPEC-VS-IMPL.md e docs/NEGATIVE-SPACE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
