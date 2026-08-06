"""Leitura de um pack do disco. A ÚNICA camada deste pacote que faz I/O.

Formato no disco (camada L1):

    packs/<nome>/
      killerbee.yaml        # manifesto: metadado + perfis + teams
      personas/*.persona.md # formato NATIVO do Buzz: frontmatter YAML + corpo
      README.md             # opcional
      CHANGELOG.md          # opcional

Os `.persona.md` carregam SÓ chaves que o parser upstream conhece — o
frontmatter deles usa `deny_unknown_fields` (persona.rs:174-176), e manter os
arquivos compatíveis significa que `buzz pack validate` de amanhã pode lê-los
sem tradução. Tudo que é do Killer Bee mora no killerbee.yaml.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .model import PackManifest, Persona, ScutellataProfile, Team


class PackLoadError(Exception):
    """Erro de carga com caminho e motivo — nunca um stack trace seco."""


def parse_frontmatter(text: str, *, source: str) -> tuple[dict, str]:
    """Separa frontmatter YAML e corpo markdown de um `.persona.md`.

    Espelha o contrato upstream: o corpo (system prompt) é TUDO após o segundo
    `---`. Pura — recebe texto, devolve (dict, corpo).
    """
    if not text.startswith("---"):
        raise PackLoadError(f"{source}: persona sem frontmatter (esperava '---' na linha 1)")
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        raise PackLoadError(f"{source}: frontmatter sem fechamento '---'")
    raw_yaml = parts[0].removeprefix("---")
    body = parts[1]
    if len(parts) == 3:
        # O prompt pode legitimamente conter '---'; devolve o resto intacto.
        body = parts[1] + "\n---" + parts[2]
    try:
        data = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as exc:
        raise PackLoadError(f"{source}: YAML inválido no frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise PackLoadError(f"{source}: frontmatter não é um mapeamento YAML")
    return data, body.lstrip("\n")


def _load_persona(pack_dir: Path, entry: dict) -> Persona:
    if "file" not in entry:
        raise PackLoadError("entrada de persona no manifesto sem a chave 'file'")
    persona_path = pack_dir / entry["file"]
    if not persona_path.is_file():
        raise PackLoadError(f"persona não encontrada: {persona_path}")

    frontmatter, body = parse_frontmatter(
        persona_path.read_text(encoding="utf-8"), source=str(persona_path)
    )

    profile_data = entry.get("profile") or {}
    if not isinstance(profile_data, dict):
        raise PackLoadError(f"{persona_path}: 'profile' no manifesto deve ser um mapeamento")
    unknown = set(profile_data) - {"threshold", "recruitment", "persistence", "propagation"}
    if unknown:
        raise PackLoadError(f"{persona_path}: chaves desconhecidas no profile: {sorted(unknown)}")

    channels = entry.get("channels") or ["all"]
    if not isinstance(channels, list) or not all(isinstance(c, str) for c in channels):
        raise PackLoadError(f"{persona_path}: 'channels' deve ser lista de strings")

    return Persona(
        name=str(frontmatter.get("name", "")),
        display_name=str(frontmatter.get("display_name", "")),
        description=str(frontmatter.get("description", "")),
        system_prompt=body,
        model=frontmatter.get("model"),
        runtime=frontmatter.get("runtime"),
        profile=ScutellataProfile(**profile_data),
        channels=tuple(channels),
    )


def load_pack(pack_dir: str | Path) -> PackManifest:
    """Carrega `killerbee.yaml` + personas. Levanta PackLoadError com contexto."""
    pack_dir = Path(pack_dir)
    manifest_path = pack_dir / "killerbee.yaml"
    if not manifest_path.is_file():
        raise PackLoadError(f"manifesto não encontrado: {manifest_path}")

    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise PackLoadError(f"{manifest_path}: YAML inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise PackLoadError(f"{manifest_path}: manifesto não é um mapeamento YAML")

    personas = tuple(_load_persona(pack_dir, e) for e in data.get("personas", []))

    teams = []
    for team_data in data.get("teams", []):
        teams.append(
            Team(
                id=str(team_data.get("id", "")),
                name=str(team_data.get("name", "")),
                description=str(team_data.get("description", "")),
                instructions=str(team_data.get("instructions", "")),
                members=tuple(team_data.get("members", [])),
            )
        )

    compat = data.get("compat") or {}
    return PackManifest(
        name=str(data.get("name", "")),
        version=str(data.get("version", "")),
        description=str(data.get("description", "")),
        author=str(data.get("author", "")),
        license=str(data.get("license", "")),
        tags=tuple(data.get("tags", [])),
        buzz_commit=str(compat.get("buzz_commit", "")),
        personas=personas,
        teams=tuple(teams),
    )
