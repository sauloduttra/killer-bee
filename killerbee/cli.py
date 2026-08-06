"""CLI do Killer Bee: `python -m killerbee validate|build|catalog|inspect`.

- ``validate`` — carrega + valida; exit 0/1 com erros legíveis, um por linha.
- ``build``    — valida e emite em ``dist/<pack>/``:
    * ``<persona>.agent.json`` e ``<persona>.agent.png`` por persona
    * ``<team>.team.json`` e ``<team>.team.png`` por team (membros embutidos)
    * ``acp-rules.toml`` — regras buzz-acp com menção SEMPRE explícita
    * ``catalog.json`` — índice para o site (Waggle) gerar páginas em build,
      com sha256 e tamanho de cada artefato
- ``catalog``  — agrega todos os packs num JSON único para o site.
- ``inspect``  — abre um ``.agent.json/.png`` ou ``.team.json/.png`` (nosso ou
  de terceiro) e mostra o que há dentro ANTES de importar. É a tese do projeto
  em forma de comando: leia antes de rodar.

O build mede cada team contra o limite de 256 KB do corpo de evento
(ingest.rs:1868) e AVISA quando o snapshot não caberia num kind 30178 — falha
barulhenta em build é infinitamente mais barata que na demo (Q-006). A medida
usa a forma COMPACTA (separators sem espaço), que é o que iria num evento — o
arquivo em disco continua pretty.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from . import AGENT_PNG_KEYWORD, AGENT_SNAPSHOT_FORMAT, TEAM_PNG_KEYWORD, __version__
from .acp_rules import rules_file
from .event30178 import unsigned_event
from .imeta import imeta_tag, mime_for
from .loader import PackLoadError, load_pack
from .pngtext import read_snapshot_from_png, snapshot_png
from .snapshot import agent_snapshot, team_snapshot
from .validate import (
    AGENT_JSON_MAX_BYTES,
    EVENT_CONTENT_MAX_BYTES,
    TEAM_JSON_MAX_BYTES,
    validate_pack,
)


def _stdio_utf8() -> None:
    """Os relatórios usam '→'; no Windows, stdout/stderr em pipe nascem cp1252
    e o print vira UnicodeEncodeError. O contrato do CLI é emitir UTF-8 sempre —
    o CI (Linux) nunca vê a falha, então ela é reproduzida em teste com
    PYTHONIOENCODING=cp1252."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _compact_bytes(snapshot: dict) -> int:
    """Tamanho da projeção que iria num corpo de evento: JSON compacto.

    Medir o pretty-printed (indent=2) superestimava — um team que coubesse
    compacto podia ser marcado como fitsIn30178=false.
    """
    return len(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _serialize_json(payload: dict) -> bytes:
    """A serialização canônica dos .json emitidos — UM lugar só.

    build e catalog hasheiam estes bytes; se as duas serializações divergissem,
    o hash publicado no site não bateria com o arquivo baixado.
    """
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _file_entry(name: str, raw: bytes) -> dict:
    """Entrada de artefato para o catálogo: nome + sha256 + tamanho.

    O hash é o que torna o download verificável e é exatamente o `x` que o
    card de snapshot no chat do Buzz exige para habilitar Import
    (markdownFileCard.ts:101-103 recusa imeta sem sha256 de 64 hex).
    """
    return {
        "name": name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


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
        raw = _serialize_json(payload)
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

    build_errors: list[str] = []
    for persona in manifest.personas:
        snapshot = agent_snapshot(persona)
        raw = write_json(f"{persona.name}.agent.json", snapshot)
        if len(raw) > AGENT_JSON_MAX_BYTES:
            build_errors.append(
                f"persona '{persona.name}': .agent.json com {len(raw):,} bytes excede "
                f"o cap de import do desktop ({AGENT_JSON_MAX_BYTES:,}, PROTOCOL-NOTES §10.8)"
            )
        png = snapshot_png(AGENT_PNG_KEYWORD, snapshot)
        (out_dir / f"{persona.name}.agent.png").write_bytes(png)
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
                "files": [
                    _file_entry(f"{persona.name}.agent.json", raw),
                    _file_entry(f"{persona.name}.agent.png", png),
                ],
            }
        )

    warnings: list[str] = []
    for team in manifest.teams:
        snapshot = team_snapshot(team, manifest)
        raw = write_json(f"{team.id}.team.json", snapshot)
        if len(raw) > TEAM_JSON_MAX_BYTES:
            build_errors.append(
                f"team '{team.id}': .team.json com {len(raw):,} bytes excede o cap "
                f"de import do desktop ({TEAM_JSON_MAX_BYTES:,}, PROTOCOL-NOTES §10.8)"
            )
        png = snapshot_png(TEAM_PNG_KEYWORD, snapshot)
        (out_dir / f"{team.id}.team.png").write_bytes(png)
        emitted.append(f"{team.id}.team.png")
        # Q-006: cabe num corpo de evento 30178? Mede a forma COMPACTA.
        event_bytes = _compact_bytes(snapshot)
        if event_bytes > EVENT_CONTENT_MAX_BYTES:
            warnings.append(
                f"team '{team.id}': snapshot com {event_bytes:,} bytes compactos NÃO cabe "
                f"no corpo de um kind 30178 (limite {EVENT_CONTENT_MAX_BYTES:,}, "
                "ingest.rs:1868). Publicação L3 exigirá projeção reduzida."
            )
        catalog["teams"].append(
            {
                "id": team.id,
                "name": team.name,
                "description": team.description,
                "members": list(team.members),
                "fitsIn30178": event_bytes <= EVENT_CONTENT_MAX_BYTES,
                "files": [
                    _file_entry(f"{team.id}.team.json", raw),
                    _file_entry(f"{team.id}.team.png", png),
                ],
            }
        )

    if build_errors:
        return _fail(build_errors)

    (out_dir / "acp-rules.toml").write_text(rules_file(manifest.personas), encoding="utf-8")
    emitted.append("acp-rules.toml")
    write_json("catalog.json", catalog)

    print(f"build: {manifest.name} v{manifest.version} → {out_dir}")
    for name in emitted:
        print(f"  {name}")
    for warning in warnings:
        print(f"AVISO: {warning}", file=sys.stderr)
    return 0


def pack_catalog_entry(manifest, *, imeta_base_url: str | None = None) -> dict:
    """Projeção de um pack para o catálogo do site. Pura.

    O `systemPrompt` vai **inteiro**. Transparência é o produto: o visitante lê o
    prompt completo antes de instalar, e truncar aqui esvaziaria a promessa.

    Os `files` carregam sha256 + tamanho de cada artefato, computados sobre os
    MESMOS bytes que `build` grava (`_serialize_json` / `snapshot_png` são
    determinísticos) — o site publica o hash ao lado do botão de download e o
    teste de export confere o hash contra o arquivo servido.

    Com ``imeta_base_url``, cada entrada de arquivo ganha também o bloco imeta
    PRONTO (ver killerbee/imeta.py): a URL aponta para
    ``{base}/downloads/{pack}/{arquivo}`` — o caminho onde o próprio site serve
    o artefato — e o ``x`` é o mesmo sha256 da entrada. Cada host publica imeta
    apontando para si mesmo; o hash não muda de host para host.
    """
    personas = []
    for p in manifest.personas:
        snapshot = agent_snapshot(p)
        raw = _serialize_json(snapshot)
        png = snapshot_png(AGENT_PNG_KEYWORD, snapshot)
        personas.append(
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
                "files": [
                    _file_entry(f"{p.name}.agent.json", raw),
                    _file_entry(f"{p.name}.agent.png", png),
                ],
            }
        )

    teams = []
    for t in manifest.teams:
        snapshot = team_snapshot(t, manifest)
        raw = _serialize_json(snapshot)
        png = snapshot_png(TEAM_PNG_KEYWORD, snapshot)
        teams.append(
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "instructions": t.instructions,
                "members": list(t.members),
                "fitsIn30178": _compact_bytes(snapshot) <= EVENT_CONTENT_MAX_BYTES,
                "files": [
                    _file_entry(f"{t.id}.team.json", raw),
                    _file_entry(f"{t.id}.team.png", png),
                ],
            }
        )

    if imeta_base_url is not None:
        base = imeta_base_url.rstrip("/")
        for group in (personas, teams):
            for item in group:
                for entry in item["files"]:
                    entry["imeta"] = imeta_tag(
                        url=f"{base}/downloads/{manifest.name}/{entry['name']}",
                        mime=mime_for(entry["name"]),
                        sha256_hex=entry["sha256"],
                        size_bytes=entry["bytes"],
                        filename=entry["name"],
                    )

    return {
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "author": manifest.author,
        "license": manifest.license,
        "tags": list(manifest.tags),
        "buzzCommit": manifest.buzz_commit,
        "personas": personas,
        "teams": teams,
    }


def cmd_catalog(packs_root: Path, out_file: Path, imeta_base_url: str | None = None) -> int:
    """Agrega todos os packs num catálogo único para o site consumir no build."""
    if not packs_root.is_dir():
        return _fail([f"diretório de packs não existe: {packs_root}"])
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
        entries.append(pack_catalog_entry(manifest, imeta_base_url=imeta_base_url))

    if errors:
        return _fail(errors)

    # Nunca o caminho absoluto: `D:/EMPRESAS/...` vazaria a árvore local para
    # um JSON consumido pelo site e tornaria a saída dependente de como o
    # comando foi invocado. Relativo se der; senão, só o nome da pasta.
    try:
        generated_from = packs_root.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        generated_from = packs_root.name
    catalog = {
        "generatedFrom": generated_from,
        "packs": entries,
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    personas = sum(len(e["personas"]) for e in entries)
    teams = sum(len(e["teams"]) for e in entries)
    print(f"catalog: {len(entries)} pack(s), {personas} persona(s), {teams} team(s) → {out_file}")
    return 0


def _load_snapshot_file(path: Path) -> dict:
    """Lê um snapshot de .json ou .png, sniffando pelo CONTEÚDO (como o app:
    magic bytes, extensão ignorada — PROTOCOL-NOTES §10.8)."""
    raw = path.read_bytes()
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        for keyword in (AGENT_PNG_KEYWORD, TEAM_PNG_KEYWORD):
            try:
                return read_snapshot_from_png(raw, keyword)
            except ValueError:
                continue
        raise ValueError("PNG sem chunk tEXt de snapshot (nem agente, nem team)")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"nem PNG nem JSON válido: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON de snapshot deve ser um objeto")
    return data


def _print_agent(definition: dict, profile: dict, memory: dict, *, indent: str = "") -> None:
    prompt = definition.get("systemPrompt") or ""
    print(f"{indent}name:        {definition.get('name', '?')}")
    print(f"{indent}displayName: {profile.get('displayName', '?')}")
    if profile.get("about"):
        print(f"{indent}about:       {profile['about']}")
    provider = definition.get("provider", "—")
    model = definition.get("model", "—")
    print(f"{indent}model:       {provider} / {model}")
    print(f"{indent}runtime:     {definition.get('runtime', '—')}")
    print(f"{indent}parallelism: {definition.get('parallelism', '—')}")
    print(f"{indent}respondTo:   {definition.get('respondTo', '—')}")
    print(
        f"{indent}timeouts:    idle {definition.get('idleTimeoutSeconds', '—')}s · "
        f"turn {definition.get('maxTurnDurationSeconds', '—')}s"
    )
    entries = len(memory.get("entries", []))
    print(f"{indent}memory:      {memory.get('level', '?')} ({entries} entradas)")
    lines = prompt.count("\n") + 1 if prompt else 0
    print(f"{indent}systemPrompt: {len(prompt.encode('utf-8')):,} bytes, {lines} linha(s)")


def cmd_inspect(path: Path, *, show_prompt: bool) -> int:
    """Mostra o que há dentro de um snapshot ANTES do import.

    Um `.agent.png` parece imagem e carrega a definição inteira de um agente —
    quem recebe um por chat ou URL não tinha ferramenta para ler o conteúdo
    antes de clicar Import. `--prompt` imprime o system prompt integral.
    """
    if not path.is_file():
        return _fail([f"arquivo não encontrado: {path}"])
    try:
        snapshot = _load_snapshot_file(path)
    except ValueError as exc:
        return _fail([f"{path}: {exc}"])

    fmt = snapshot.get("format", "?")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"file:    {path.name}")
    print(f"sha256:  {sha}")
    print(f"format:  {fmt} v{snapshot.get('version', '?')}")

    if fmt == AGENT_SNAPSHOT_FORMAT:
        _print_agent(
            snapshot.get("definition") or {},
            snapshot.get("profile") or {},
            snapshot.get("memory") or {},
        )
        if show_prompt:
            print("\n--- systemPrompt (verbatim) ---")
            print((snapshot.get("definition") or {}).get("systemPrompt") or "")
        return 0

    team = snapshot.get("team") or {}
    members = snapshot.get("members") or []
    print(f"team:    {team.get('name', '?')}")
    if team.get("description"):
        print(f"desc:    {team['description']}")
    print(f"members: {len(members)}")
    for i, member in enumerate(members, 1):
        print(f"\n[{i}/{len(members)}]")
        _print_agent(
            member.get("definition") or {},
            member.get("profile") or {},
            member.get("memory") or {},
            indent="  ",
        )
        if show_prompt:
            print("\n  --- systemPrompt (verbatim) ---")
            prompt = (member.get("definition") or {}).get("systemPrompt") or ""
            print("  " + prompt.replace("\n", "\n  "))
    return 0


def cmd_event(pack_dir: Path, out_dir: Path, *, shared: bool, created_at: int) -> int:
    """Emite o kind 30178 NÃO ASSINADO por team, em ``<out>/<pack>/<id>.30178.json``.

    Valida o pack inteiro antes — um evento de pack inválido seria lixo
    assinável. Assinar e publicar ficam fora por decisão, não por falta:
    exigem chave (🔴). O desenho da projeção está em event30178.py e o
    schema publicado em schema/kind-30178-content.schema.json (D-029).
    """
    try:
        manifest = load_pack(pack_dir)
    except PackLoadError as exc:
        return _fail([str(exc)])
    errors = validate_pack(manifest)
    if errors:
        return _fail(errors)
    if not manifest.teams:
        return _fail([f"pack '{manifest.name}' não tem teams — o 30178 é projeção de team"])

    target = out_dir / manifest.name
    target.mkdir(parents=True, exist_ok=True)
    for team in manifest.teams:
        event = unsigned_event(team, manifest, shared=shared, created_at=created_at)
        out_file = target / f"{team.id}.30178.json"
        out_file.write_text(
            json.dumps(event, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        content_bytes = len(event["content"].encode("utf-8"))
        state = "shared" if shared else "unshared"
        print(f"event: {team.id} → {out_file} (content {content_bytes:,} B, {state}, NÃO ASSINADO)")
    return 0


def main(argv: list[str] | None = None) -> int:
    _stdio_utf8()
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
    p_catalog.add_argument(
        "--imeta-base-url",
        default=None,
        help="URL pública que serve downloads/ — com ela, cada arquivo do "
        "catálogo ganha o bloco imeta pronto para colar num canal Buzz",
    )

    p_event = sub.add_parser(
        "event", help="emite o kind 30178 NÃO ASSINADO por team (camada L3, offline)"
    )
    p_event.add_argument("pack", type=Path)
    p_event.add_argument("--out", type=Path, default=Path("dist"))
    p_event.add_argument(
        "--unshared",
        action="store_true",
        help="omite a tag ['shared','true'] — o evento fica autor-somente no relay",
    )
    p_event.add_argument(
        "--created-at",
        type=int,
        default=0,
        help="unix seconds; default 0 = template não assinado, quem assina carimba",
    )

    p_inspect = sub.add_parser(
        "inspect", help="mostra o conteúdo de um .agent.json/.png ou .team.json/.png"
    )
    p_inspect.add_argument("file", type=Path)
    p_inspect.add_argument(
        "--prompt", action="store_true", help="imprime também o system prompt integral"
    )

    args = parser.parse_args(argv)
    if args.command == "validate":
        return cmd_validate(args.pack)
    if args.command == "catalog":
        return cmd_catalog(args.packs, args.out, imeta_base_url=args.imeta_base_url)
    if args.command == "inspect":
        return cmd_inspect(args.file, show_prompt=args.prompt)
    if args.command == "event":
        return cmd_event(args.pack, args.out, shared=not args.unshared, created_at=args.created_at)
    return cmd_build(args.pack, args.out)
