"""CLI do Killer Bee: `python -m killerbee validate|build <pack>`.

- ``validate`` — carrega + valida; exit 0/1 com erros legíveis, um por linha.
- ``build``    — valida e emite em ``dist/<pack>/``:
    * ``<persona>.agent.json`` e ``<persona>.agent.png`` por persona
    * ``<team>.team.json`` e ``<team>.team.png`` por team (membros embutidos)
    * ``acp-rules.toml`` — regras buzz-acp com menção SEMPRE explícita
    * ``catalog.json`` — índice para o site (Waggle) gerar páginas em build

O build mede cada team contra o limite de 256 KB do corpo de evento
(ingest.rs:1868) e AVISA quando o snapshot não caberia num kind 30178 — falha
barulhenta em build é infinitamente mais barata que na demo (Q-006).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import AGENT_PNG_KEYWORD, TEAM_PNG_KEYWORD, __version__
from .acp_rules import rules_file
from .loader import PackLoadError, load_pack
from .pngtext import snapshot_png
from .snapshot import agent_snapshot, team_snapshot
from .validate import EVENT_CONTENT_MAX_BYTES, validate_pack


def _fail(messages: list[str]) -> int:
    for message in messages:
        print(f"ERRO: {message}", file=sys.stderr)
    print(f"\n{len(messages)} erro(s). Nada foi emitido.", file=sys.stderr)
    return 1


def cmd_validate(pack_dir: Path) -> int:
    try:
        manifest = load_pack(pack_dir)
    except PackLoadError as exc:
        return _fail([str(exc)])
    errors = validate_pack(manifest)
    if errors:
        return _fail(errors)
    print(
        f"OK: {manifest.name} v{manifest.version} — "
        f"{len(manifest.personas)} persona(s), {len(manifest.teams)} team(s)"
    )
    return 0


def cmd_build(pack_dir: Path, out_root: Path) -> int:
    try:
        manifest = load_pack(pack_dir)
    except PackLoadError as exc:
        return _fail([str(exc)])
    errors = validate_pack(manifest)
    if errors:
        return _fail(errors)

    out_dir = out_root / manifest.name
    out_dir.mkdir(parents=True, exist_ok=True)
    emitted: list[str] = []

    def write_json(name: str, payload: dict) -> bytes:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        (out_dir / name).write_bytes(raw)
        emitted.append(name)
        return raw

    catalog: dict = {
        "pack": {
            "name": manifest.name,
            "version": manifest.version,
            "description": manifest.description,
            "author": manifest.author,
            "license": manifest.license,
            "tags": list(manifest.tags),
            "buzzCommit": manifest.buzz_commit,
        },
        "personas": [],
        "teams": [],
    }

    for persona in manifest.personas:
        snapshot = agent_snapshot(persona)
        write_json(f"{persona.name}.agent.json", snapshot)
        (out_dir / f"{persona.name}.agent.png").write_bytes(
            snapshot_png(AGENT_PNG_KEYWORD, snapshot)
        )
        emitted.append(f"{persona.name}.agent.png")
        catalog["personas"].append(
            {
                "name": persona.name,
                "displayName": persona.display_name,
                "description": persona.description,
                # Transparência é o produto: o prompt inteiro vai para o catálogo.
                "systemPrompt": persona.system_prompt,
                "model": persona.model,
                "runtime": persona.runtime,
                "profile": {
                    "threshold": persona.profile.threshold,
                    "recruitment": persona.profile.recruitment,
                    "persistence": persona.profile.persistence,
                    "propagation": persona.profile.propagation,
                },
                "files": [f"{persona.name}.agent.json", f"{persona.name}.agent.png"],
            }
        )

    warnings: list[str] = []
    for team in manifest.teams:
        snapshot = team_snapshot(team, manifest)
        raw = write_json(f"{team.id}.team.json", snapshot)
        (out_dir / f"{team.id}.team.png").write_bytes(snapshot_png(TEAM_PNG_KEYWORD, snapshot))
        emitted.append(f"{team.id}.team.png")
        # Q-006: cabe num corpo de evento 30178?
        if len(raw) > EVENT_CONTENT_MAX_BYTES:
            warnings.append(
                f"team '{team.id}': snapshot com {len(raw):,} bytes NÃO cabe no corpo "
                f"de um kind 30178 (limite {EVENT_CONTENT_MAX_BYTES:,}, ingest.rs:1868). "
                "Publicação L3 exigirá projeção reduzida."
            )
        catalog["teams"].append(
            {
                "id": team.id,
                "name": team.name,
                "description": team.description,
                "members": list(team.members),
                "fitsIn30178": len(raw) <= EVENT_CONTENT_MAX_BYTES,
                "files": [f"{team.id}.team.json", f"{team.id}.team.png"],
            }
        )

    (out_dir / "acp-rules.toml").write_text(rules_file(manifest.personas), encoding="utf-8")
    emitted.append("acp-rules.toml")
    write_json("catalog.json", catalog)

    print(f"build: {manifest.name} v{manifest.version} → {out_dir}")
    for name in emitted:
        print(f"  {name}")
    for warning in warnings:
        print(f"AVISO: {warning}", file=sys.stderr)
    return 0


def pack_catalog_entry(manifest) -> dict:
    """Projeção de um pack para o catálogo do site. Pura.

    O `systemPrompt` vai **inteiro**. Transparência é o produto: o visitante lê o
    prompt completo antes de instalar, e truncar aqui esvaziaria a promessa.
    """
    return {
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "author": manifest.author,
        "license": manifest.license,
        "tags": list(manifest.tags),
        "buzzCommit": manifest.buzz_commit,
        "personas": [
            {
                "name": p.name,
                "displayName": p.display_name,
                "description": p.description,
                "systemPrompt": p.system_prompt,
                "model": p.model,
                "runtime": p.runtime,
                "profile": {
                    "threshold": p.profile.threshold,
                    "recruitment": p.profile.recruitment,
                    "persistence": p.profile.persistence,
                    "propagation": p.profile.propagation,
                },
            }
            for p in manifest.personas
        ],
        "teams": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "instructions": t.instructions,
                "members": list(t.members),
            }
            for t in manifest.teams
        ],
    }


def cmd_catalog(packs_root: Path, out_file: Path) -> int:
    """Agrega todos os packs num catálogo único para o site consumir no build."""
    pack_dirs = sorted(d for d in packs_root.iterdir() if (d / "killerbee.yaml").is_file())
    if not pack_dirs:
        return _fail([f"nenhum pack encontrado em {packs_root}"])

    entries = []
    errors: list[str] = []
    for pack_dir in pack_dirs:
        try:
            manifest = load_pack(pack_dir)
        except PackLoadError as exc:
            errors.append(str(exc))
            continue
        pack_errors = validate_pack(manifest)
        if pack_errors:
            errors.extend(f"{pack_dir.name}: {e}" for e in pack_errors)
            continue
        entries.append(pack_catalog_entry(manifest))

    if errors:
        return _fail(errors)

    catalog = {
        "generatedFrom": str(packs_root).replace("\\", "/"),
        "packs": entries,
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    personas = sum(len(e["personas"]) for e in entries)
    teams = sum(len(e["teams"]) for e in entries)
    print(f"catalog: {len(entries)} pack(s), {personas} persona(s), {teams} team(s) → {out_file}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="killerbee", description=__doc__)
    parser.add_argument("--version", action="version", version=f"killerbee {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="valida um pack; exit 0/1")
    p_validate.add_argument("pack", type=Path)

    p_build = sub.add_parser("build", help="valida e emite snapshots em dist/")
    p_build.add_argument("pack", type=Path)
    p_build.add_argument("--out", type=Path, default=Path("dist"))

    p_catalog = sub.add_parser("catalog", help="agrega todos os packs num JSON para o site")
    p_catalog.add_argument("--packs", type=Path, default=Path("packs"))
    p_catalog.add_argument("--out", type=Path, default=Path("site/data/catalog.json"))

    args = parser.parse_args(argv)
    if args.command == "validate":
        return cmd_validate(args.pack)
    if args.command == "catalog":
        return cmd_catalog(args.packs, args.out)
    return cmd_build(args.pack, args.out)
