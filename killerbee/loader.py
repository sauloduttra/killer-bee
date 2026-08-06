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

# Limites do parser upstream (persona.rs:21 e :24 @ ed4b3e7a), medidos em bytes
# UTF-8 — `len()` de um `&str` em Rust conta bytes, não chars.
MAX_FRONTMATTER_BYTES = 1_048_576
MAX_BODY_BYTES = 262_144

_PROFILE_KEYS = {"threshold", "recruitment", "persistence", "propagation"}


class PackLoadError(Exception):
    """Erro de carga com caminho e motivo — nunca um stack trace seco."""


def parse_frontmatter(text: str, *, source: str) -> tuple[dict, str]:
    """Separa frontmatter YAML e corpo markdown de um `.persona.md`.

    Espelha o contrato upstream (persona.rs:277-319 @ ed4b3e7a) regra a regra:

    - abre com ``---`` seguido de newline (``\\r`` opcional antes do ``\\n``);
      ``---lixo`` na primeira linha NÃO abre frontmatter (persona.rs:283-285);
    - fecha com ``---`` **em linha própria** — seguido de ``\\n``, ``\\r`` ou
      EOF; uma linha ``---junk`` NÃO fecha (persona.rs:287-307);
    - exatamente um ``\\n`` ou ``\\r\\n`` após o fechamento é consumido; o resto
      do arquivo é o corpo, byte a byte (persona.rs:312-316) — a versão anterior
      fazia ``lstrip("\\n")``, o que apagava linhas em branco intencionais no
      início do prompt;
    - frontmatter ≤ 1 MiB e corpo ≤ 256 KiB (persona.rs:21, :24, :211-214).

    Pura — recebe texto, devolve ``(dict, corpo)``.
    """
    if text.startswith("﻿"):
        raise PackLoadError(
            f"{source}: arquivo começa com BOM UTF-8 — salve sem BOM. O parser "
            "upstream exige '---' no primeiro byte (persona.rs:278-281), e sem "
            "esta checagem o erro seria o enganoso 'sem frontmatter' num arquivo "
            "que visivelmente tem frontmatter."
        )
    if not text.startswith("---"):
        raise PackLoadError(f"{source}: persona sem frontmatter (esperava '---' na linha 1)")
    rest = text[3:]
    if rest.startswith("\r"):
        rest = rest[1:]
    if not rest.startswith("\n"):
        raise PackLoadError(
            f"{source}: a abertura '---' precisa estar sozinha na linha — "
            "'---texto' não abre frontmatter (persona.rs:283-285)"
        )
    rest = rest[1:]

    search_from = 0
    while True:
        pos = rest.find("\n---", search_from)
        if pos == -1:
            raise PackLoadError(
                f"{source}: frontmatter sem fechamento '---' em linha própria (persona.rs:287-307)"
            )
        after = pos + 4
        if after >= len(rest) or rest[after] in ("\n", "\r"):
            close = pos
            break
        search_from = after  # '---junk' não é delimitador — continua procurando

    raw_yaml = rest[:close]
    after_close = rest[close + 4 :]
    if after_close.startswith("\r\n"):
        body = after_close[2:]
    elif after_close.startswith("\n"):
        body = after_close[1:]
    else:
        body = after_close

    if len(raw_yaml.encode("utf-8")) > MAX_FRONTMATTER_BYTES:
        raise PackLoadError(
            f"{source}: frontmatter excede {MAX_FRONTMATTER_BYTES:,} bytes — "
            "o parser upstream rejeita (persona.rs:211-213)"
        )
    if len(body.encode("utf-8")) > MAX_BODY_BYTES:
        raise PackLoadError(
            f"{source}: corpo excede {MAX_BODY_BYTES:,} bytes — "
            "o parser upstream rejeita (persona.rs:214-216)"
        )

    try:
        data = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as exc:
        raise PackLoadError(f"{source}: YAML inválido no frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise PackLoadError(f"{source}: frontmatter não é um mapeamento YAML")
    return data, body


def _str_or_none(value: object, *, source: str, key: str) -> str | None:
    """`model: 123` não pode virar TypeError três camadas depois."""
    if value is None or isinstance(value, str):
        return value
    raise PackLoadError(
        f"{source}: '{key}' deve ser string, veio {type(value).__name__} ({value!r})"
    )


def _list_of(value: object, *, source: str, key: str, item_type: type = str) -> list:
    """Coleção do manifesto: ausente/nula → lista vazia; escalar é erro.

    Dois modos de falha silenciosa que isto elimina: `tags: abc` virava
    ``tuple('a','b','c')`` na conversão cega (catálogo com tags corrompidas em
    caracteres soltos), e uma seção presente mas nula (`personas:` sem valor,
    estado comum durante edição) estourava TypeError com traceback cru.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise PackLoadError(
            f"{source}: '{key}' deve ser lista, veio {type(value).__name__} ({value!r})"
        )
    for item in value:
        if not isinstance(item, item_type):
            raise PackLoadError(
                f"{source}: item de '{key}' deve ser {item_type.__name__}, "
                f"veio {type(item).__name__} ({item!r})"
            )
    return value


def _load_persona(pack_dir: Path, entry: object, manifest_path: Path) -> Persona:
    if not isinstance(entry, dict):
        raise PackLoadError(
            f"{manifest_path}: entrada de persona deve ser mapeamento, "
            f"veio {type(entry).__name__} ({entry!r})"
        )
    if "file" not in entry:
        raise PackLoadError(f"{manifest_path}: entrada de persona sem a chave 'file'")
    persona_path = pack_dir / str(entry["file"])
    if not persona_path.is_file():
        raise PackLoadError(f"persona não encontrada: {persona_path}")

    source = str(persona_path)
    frontmatter, body = parse_frontmatter(persona_path.read_text(encoding="utf-8"), source=source)

    profile_data = entry.get("profile") or {}
    if not isinstance(profile_data, dict):
        raise PackLoadError(f"{source}: 'profile' no manifesto deve ser um mapeamento")
    unknown = set(profile_data) - _PROFILE_KEYS
    if unknown:
        raise PackLoadError(f"{source}: chaves desconhecidas no profile: {sorted(unknown)}")

    if "channels" in entry:
        channels = _list_of(entry["channels"], source=source, key="channels")
        if not channels:
            raise PackLoadError(
                f"{source}: 'channels: []' é ambíguo — remova a chave para "
                "'todos os canais' ou liste os canais. Lista vazia NÃO vira "
                "'all' em silêncio (o autor que pediu nenhum canal não pode "
                "ganhar uma regra inscrita em todos)."
            )
    else:
        channels = ["all"]

    return Persona(
        name=str(frontmatter.get("name", "")),
        display_name=str(frontmatter.get("display_name", "")),
        description=str(frontmatter.get("description", "")),
        system_prompt=body,
        model=_str_or_none(frontmatter.get("model"), source=source, key="model"),
        runtime=_str_or_none(frontmatter.get("runtime"), source=source, key="runtime"),
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

    src = str(manifest_path)
    personas = tuple(
        _load_persona(pack_dir, entry, manifest_path)
        for entry in _list_of(data.get("personas"), source=src, key="personas", item_type=dict)
    )

    teams = []
    for team_data in _list_of(data.get("teams"), source=src, key="teams", item_type=dict):
        team_id = str(team_data.get("id", ""))
        members = _list_of(team_data.get("members"), source=src, key=f"teams['{team_id}'].members")
        teams.append(
            Team(
                id=team_id,
                name=str(team_data.get("name", "")),
                description=str(team_data.get("description", "")),
                instructions=str(team_data.get("instructions", "")),
                members=tuple(members),
            )
        )

    compat = data.get("compat") or {}
    if not isinstance(compat, dict):
        raise PackLoadError(f"{src}: 'compat' deve ser um mapeamento")

    return PackManifest(
        name=str(data.get("name", "")),
        version=str(data.get("version", "")),
        description=str(data.get("description", "")),
        author=str(data.get("author", "")),
        license=str(data.get("license", "")),
        tags=tuple(_list_of(data.get("tags"), source=src, key="tags")),
        buzz_commit=str(compat.get("buzz_commit", "")),
        personas=personas,
        teams=tuple(teams),
    )
