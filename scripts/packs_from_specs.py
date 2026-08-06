#!/usr/bin/env python3
"""Gera packs do Killer Bee a partir de especificações de persona em JSON.

Cada repositório-lab do autor vira uma persona; personas do mesmo pilar viram
um pack com um team. O trabalho de LER os repos e escrever os prompts é de
quem produz o JSON de entrada (com verificação por segundo leitor, como manda
o CONTRIBUTING); este script só materializa, e materializa igual toda vez.

Entrada: JSON com ``{"personas": [...]}``, cada item com

    repo, slug, display_name, description, system_prompt,
    threshold, recruitment, persistence, propagation, pillar

Saída, por pilar:

    packs/<pilar>/killerbee.yaml
    packs/<pilar>/personas/<slug>.persona.md
    packs/<pilar>/README.md
    packs/<pilar>/CHANGELOG.md

Deliberadamente **sem `model`** no frontmatter: forçar um provider que o
importador talvez não tenha configurado troca uma persona que funciona por um
erro de credencial. O snapshot omite o campo e o app usa o default do usuário
(os campos são `#[serde(default)]`, PROTOCOL-NOTES §10.1).

Uso:
    uv run --no-project scripts/packs_from_specs.py specs.json
    uv run --no-project scripts/packs_from_specs.py specs.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

REQUIRED = (
    "repo",
    "slug",
    "display_name",
    "description",
    "system_prompt",
    "threshold",
    "recruitment",
    "persistence",
    "propagation",
    "pillar",
)

# Título e uma linha de contexto por pilar. Escrito aqui e não gerado, porque é
# texto de catálogo que um humano lê — e o gerador não deve inventar prosa.
PILLARS = {
    "derivatives-microstructure": (
        "Derivatives & Microstructure",
        "Option analytics, the order book itself, and the models that decide how a "
        "trade meets the market: optimal market making, optimal execution, order flow.",
    ),
    "valuation-fundamentals": (
        "Valuation & Fundamentals",
        "From the time value of money to equity valuation, statement analysis and "
        "forensic accounting — the CFA-curriculum spine, implemented rather than quoted.",
    ),
    "risk-portfolio": (
        "Risk & Portfolio",
        "Value at Risk with real backtests, portfolio construction beyond Markowitz, "
        "factor attribution, credit risk and the copulas that tie the tails together.",
    ),
    "options-volatility": (
        "Options & Volatility",
        "Four independent routes to an option price — PDE, Monte Carlo, lattices, "
        "least-squares MC — plus the volatility models the price feeds on.",
    ),
    "rates-term-structure": (
        "Rates & Term Structure",
        "Short-rate models, the two-factor Gaussian workhorse, the HJM no-arbitrage "
        "drift condition, and the market model practitioners actually quote from.",
    ),
    "timeseries-stat-trading": (
        "Time Series & Statistical Trading",
        "Inference from first principles, state-space filtering, cointegration for "
        "pairs, self-exciting processes, and an event-driven backtester to run it on.",
    ),
    "applied-macro": (
        "Applied Macro",
        "Central-bank and labour releases read like a quant reads them: surprise "
        "decomposition, Taylor gaps, expectation de-anchoring — on live official data.",
    ),
    "systems-cs": (
        "Systems & Computer Science",
        "The other half of the bench: TCP, Raft, an LSM-tree, a SAT solver, a path "
        "tracer, autodiff. Written from scratch, because that is how you learn them.",
    ),
}

LICENSE = "Apache-2.0"
AUTHOR = "Saulo Duttra"
BUZZ_COMMIT = "ed4b3e7afafb5f5a688c210f39b90d747e6f0f00"


def _yaml_block(text: str, indent: str = "      ") -> str:
    """Escalar de bloco YAML (``>-``), com a indentação certa e sem escapar."""
    words = " ".join(text.split())
    lines: list[str] = []
    current = indent
    for word in words.split(" "):
        if len(current) + len(word) + 1 > 88 and current != indent:
            lines.append(current)
            current = indent + word
        else:
            current = f"{current} {word}" if current != indent else indent + word
    if current.strip():
        lines.append(current)
    return "\n".join(lines)


def validate(personas: list[dict]) -> list[str]:
    """Todas as violações de uma vez — nunca 'conserta uma, descobre a próxima'."""
    errors: list[str] = []
    seen: set[str] = set()
    for index, persona in enumerate(personas):
        where = f"personas[{index}] ({persona.get('slug', '?')})"
        for key in REQUIRED:
            if not persona.get(key) and persona.get(key) != 0:
                errors.append(f"{where}: campo obrigatório ausente: {key}")
        slug = persona.get("slug", "")
        if slug and not SLUG.match(slug):
            errors.append(f"{where}: slug fora da gramática ^[a-z0-9][a-z0-9_-]{{0,63}}$")
        if slug in seen:
            errors.append(f"{where}: slug duplicado")
        seen.add(slug)
        pillar = persona.get("pillar", "")
        if pillar and pillar not in PILLARS:
            errors.append(f"{where}: pilar desconhecido: {pillar}")
        recruitment = persona.get("recruitment")
        if isinstance(recruitment, int) and not 1 <= recruitment <= 32:
            errors.append(f"{where}: recruitment {recruitment} fora de 1..=32")
        prompt = persona.get("system_prompt", "")
        if prompt and len(prompt.split()) < 80:
            errors.append(
                f"{where}: system_prompt com {len(prompt.split())} palavras — raso demais"
            )
    return errors


def write_pack(pillar: str, personas: list[dict], out_root: Path, *, dry_run: bool) -> Path:
    title, blurb = PILLARS[pillar]
    pack_dir = out_root / pillar
    personas_dir = pack_dir / "personas"

    manifest = [
        "# yaml-language-server: $schema=../../schema/killerbee.schema.json",
        "#",
        f"# {title} — gerado por scripts/packs_from_specs.py a partir dos",
        "# repositórios-lab do autor. Cada persona corresponde a um repo público:",
        "# o prompt descreve o que aquele código REALMENTE faz, lido no repo e",
        "# conferido por um segundo leitor antes de entrar aqui.",
        "",
        f"name: {pillar}",
        "version: 0.1.0",
        "description: >-",
        _yaml_block(blurb, indent="  "),
        f"author: {AUTHOR}",
        f"license: {LICENSE}",
        f"tags: [{', '.join(sorted({pillar.split('-')[0], 'quant', 'reference'}))}]",
        "",
        "compat:",
        f"  buzz_commit: {BUZZ_COMMIT}",
        "",
        "personas:",
    ]

    for persona in personas:
        manifest += [
            f"  - file: personas/{persona['slug']}.persona.md",
            f"    # {persona['repo']} — {persona['profile_rationale']}"
            if persona.get("profile_rationale")
            else f"    # {persona['repo']}",
            "    profile:",
            f"      threshold: {persona['threshold']}",
            f"      recruitment: {persona['recruitment']}",
            f"      persistence: {persona['persistence']}",
            f"      propagation: {persona['propagation']}",
        ]

    manifest += [
        "",
        "teams:",
        f"  - id: {pillar}",
        f"    name: {title}",
        "    description: >-",
        _yaml_block(blurb),
        "    instructions: >-",
        _yaml_block(
            "You are one specialist among several on the same desk. Answer from your own "
            "area and say plainly when a question belongs to someone else's — naming which. "
            "Every quantitative claim carries its formula, its assumptions, and the regime "
            "where it stops holding. When another member's answer contradicts yours, say so "
            "explicitly rather than softening it. None of you gives investment advice.",
        ),
        f"    members: [{', '.join(p['slug'] for p in personas)}]",
        "",
    ]

    readme = [
        f"# {title}",
        "",
        blurb,
        "",
        f"{len(personas)} personas, one per public repository. The system prompt of each "
        "describes what that repository actually implements — read from the source and "
        "checked by a second reader, per this project's rule against inventing facts.",
        "",
        "| Persona | Repository | What it covers |",
        "|---|---|---|",
    ]
    for persona in personas:
        readme.append(
            f"| **{persona['display_name']}** "
            f"| [`{persona['repo']}`](https://github.com/{AUTHOR.split()[0].lower()}duttra/{persona['repo']}) "
            f"| {persona['description']} |"
        )
    readme += [
        "",
        "## Importing",
        "",
        "Import the **team** or the individual **personas**, never both — the team "
        "snapshot embeds every member in full, and importing it after the personas "
        "creates duplicates.",
        "",
        f"Built by [{AUTHOR}](https://github.com/sauloduttra).",
        "",
    ]

    changelog = [
        f"# Changelog — {pillar}",
        "",
        "## 0.1.0",
        "",
        f"- First release: {len(personas)} personas generated from the author's public "
        "lab repositories.",
        "",
    ]

    if dry_run:
        print(f"[dry-run] {pack_dir}: {len(personas)} personas")
        return pack_dir

    personas_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "killerbee.yaml").write_text("\n".join(manifest), encoding="utf-8")
    (pack_dir / "README.md").write_text("\n".join(readme), encoding="utf-8")
    (pack_dir / "CHANGELOG.md").write_text("\n".join(changelog), encoding="utf-8")

    for persona in personas:
        # Frontmatter com chaves NATIVAS apenas: o parser upstream usa
        # deny_unknown_fields e uma chave nossa seria erro fatal lá
        # (buzz-persona persona.rs:174-176).
        body = persona["system_prompt"].strip()
        content = (
            "---\n"
            f"name: {persona['slug']}\n"
            f"display_name: {persona['display_name']}\n"
            f"description: {json.dumps(persona['description'], ensure_ascii=False)}\n"
            "---\n"
            f"{body}\n"
        )
        (personas_dir / f"{persona['slug']}.persona.md").write_text(content, encoding="utf-8")

    return pack_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specs", type=Path, help="JSON com {'personas': [...]}")
    parser.add_argument("--out", type=Path, default=ROOT / "packs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    data = json.loads(args.specs.read_text(encoding="utf-8"))
    personas = data["personas"] if isinstance(data, dict) else data

    errors = validate(personas)
    if errors:
        for error in errors:
            print(f"ERRO: {error}", file=sys.stderr)
        print(f"\n{len(errors)} erro(s). Nada foi escrito.", file=sys.stderr)
        return 1

    by_pillar: dict[str, list[dict]] = {}
    for persona in personas:
        by_pillar.setdefault(persona["pillar"], []).append(persona)

    for pillar in sorted(by_pillar):
        group = by_pillar[pillar]
        pack_dir = write_pack(pillar, group, args.out, dry_run=args.dry_run)
        print(f"{pillar}: {len(group)} persona(s) -> {pack_dir}")

    print(f"\n{len(personas)} persona(s) em {len(by_pillar)} pack(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
