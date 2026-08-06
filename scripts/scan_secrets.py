"""Varredura de contaminação: segredo, credencial e dado pessoal em uma árvore de arquivos.

Uso:
    uv run scripts/scan_secrets.py <caminho> [--ext .py,.md,.json] [--max-mb 8]

Serve a dois propósitos no Killer Bee:

1. Triagem de material externo antes de ele encostar no repo (bloco 4 de FASE-1.md).
2. Gate de CI contra chave versionada (item do DoD). Sai com código 1 se achar
   qualquer coisa de severidade ``alta``.

A função de decisão é pura — ``scan_text`` recebe texto e devolve achados, sem tocar
disco, rede ou relógio. Só a camada de percurso de diretório faz I/O. Isso é o que
permite testar o classificador sem fixture em disco.

O relatório NUNCA imprime o segredo inteiro: só um prefixo curto mascarado, o
suficiente para o humano localizar a linha e decidir.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Camada pura
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """Uma suspeita de contaminação, ancorada em linha."""

    rule: str
    severity: str  # "alta" | "media" | "baixa"
    line_number: int
    masked: str
    why: str


# Cada regra é (nome, severidade, regex compilada, explicação).
#
# A severidade "alta" significa: isto sozinho impede o arquivo de entrar num repo
# público. "media" pede olho humano. "baixa" é ruído frequente que ainda assim vale
# listar porque o custo de um falso negativo é maior que o de um falso positivo.
_RULES: tuple[tuple[str, str, re.Pattern[str], str], ...] = (
    (
        "nostr_nsec",
        "alta",
        re.compile(r"\bnsec1[02-9ac-hj-np-z]{58,}\b"),
        "chave privada Nostr bech32 — identidade completa, não config",
    ),
    (
        "hex_privkey_64",
        "alta",
        re.compile(r"(?i)\b(?:priv(?:ate)?[_-]?key|secret[_-]?key|nsec)\b\W{0,4}([0-9a-f]{64})\b"),
        "64 hex nomeado como chave privada",
    ),
    (
        "aws_access_key",
        "alta",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "AWS access key id",
    ),
    (
        "github_token",
        "alta",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        "token do GitHub",
    ),
    (
        "openai_key",
        "alta",
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
        "chave de API estilo OpenAI",
    ),
    (
        "anthropic_key",
        "alta",
        re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
        "chave de API Anthropic",
    ),
    (
        "slack_token",
        "alta",
        re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
        "token do Slack",
    ),
    (
        "private_key_block",
        "alta",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
        "bloco PEM de chave privada",
    ),
    (
        "jwt",
        "media",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
        "JWT — pode carregar claim identificável mesmo expirado",
    ),
    (
        "generic_assignment",
        "media",
        # O nome casa por SUFIXO (`[\w.-]*`) de propósito: a primeira versão listava
        # só `access_token`/`auth_token` e deixava passar `SEMGREP_TOKEN: "..."`,
        # `GITHUB_TOKEN`, `BUZZ_S3_SECRET_KEY` — exatamente a forma que aparece em
        # `.env` e em config de MCP server. O valor precisa ser literal entre aspas;
        # `os.getenv("X")` e `${X}` não casam, que é o comportamento desejado.
        # `[_-]key` (com separador obrigatório) em vez de `key` solto: pega
        # `BUZZ_S3_SECRET_KEY` e `signing-key` sem casar com `monkey` ou `keyboard`.
        re.compile(
            r"(?i)\b[\w.-]*(?:api[_-]?key|apikey|[_-]key|token|password|passwd|senha|secret|passphrase)\b"
            r"\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']"
        ),
        "credencial atribuída a literal no fonte",
    ),
    (
        "connection_string",
        "media",
        re.compile(
            r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@/]+:[^\s@/]+@"
        ),
        "string de conexão com senha embutida",
    ),
    (
        "cpf",
        "media",
        re.compile(r"(?<!\d)\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)"),
        "CPF formatado — dado pessoal",
    ),
    (
        "email",
        "baixa",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "e-mail — verificar se é de terceiro",
    ),
    (
        "private_ip_url",
        "baixa",
        re.compile(r"\bhttps?://(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)[^\s\"']+"),
        "URL para host de rede interna",
    ),
)

# Linhas que casam com isto não contam: são placeholder, exemplo ou referência.
_PLACEHOLDER = re.compile(
    r"(?i)(\bexample\b|\bplaceholder\b|\bdummy\b|\bfake\b|\byour[_-]|\bxxx+\b|\bTODO\b"
    r"|<[a-z_]+>|\$\{[A-Z_]+\}|\benv\.|getenv|environ)"
)

# Supressão inline explícita. Existe porque os testes DESTE scanner precisam de
# strings que casam com as regras — sem isto, a suíte que prova que o gate
# funciona é a mesma que deixa o gate vermelho para sempre.
#
# A alternativa seria excluir o arquivo de teste inteiro, e é exatamente assim
# que segredo de verdade passa despercebido. Marcador por LINHA é auditável:
# aparece no diff, o revisor vê, e cobre só aquela linha.
#
# `gitleaks:allow` é aceito para que um único comentário sirva aos dois gates.
_ALLOW_MARKER = re.compile(r"(?i)(scan-secrets:\s*allow|gitleaks:\s*allow|nosec\b)")


def mask(secret: str, keep: int = 4) -> str:
    """Devolve um prefixo curto seguido de comprimento, nunca o valor inteiro."""
    if len(secret) <= keep:
        return "*" * len(secret)
    return f"{secret[:keep]}…[{len(secret)} chars]"


def scan_text(text: str) -> list[Finding]:
    """Classifica um texto. Puro: sem I/O, sem estado, sem relógio.

    Devolve os achados em ordem de linha. Uma linha pode gerar mais de um achado se
    casar com mais de uma regra — não deduplicamos, porque regras diferentes pedem
    ações diferentes.
    """
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if len(line) > 4000:
            # Linha absurda quase sempre é dado serializado, não credencial escrita
            # à mão. Truncamos para o regex não degradar.
            line = line[:4000]
        if _ALLOW_MARKER.search(line):
            continue
        is_placeholder = bool(_PLACEHOLDER.search(line))
        for rule, severity, pattern, why in _RULES:
            match = pattern.search(line)
            if match is None:
                continue
            # O grupo 1 existe nas regras que isolam o valor; senão, o casamento todo.
            value = match.group(match.lastindex or 0)
            effective = severity
            if is_placeholder and severity != "alta":
                effective = "baixa"
            findings.append(
                Finding(
                    rule=rule,
                    severity=effective,
                    line_number=line_number,
                    masked=mask(value),
                    why=why + (" [linha parece placeholder]" if is_placeholder else ""),
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Camada de I/O
# ---------------------------------------------------------------------------

_SKIP_DIRS = {".git", "node_modules", "target", "__pycache__", ".next", "out", "dist", ".venv"}

_DEFAULT_EXT = (
    ".py,.js,.ts,.tsx,.jsx,.rs,.go,.java,.rb,.sh,.bat,.ps1,.md,.json,.yaml,.yml,"
    ".toml,.ini,.cfg,.env,.txt,.html,.css,.sql"
)


def iter_files(root: Path, extensions: set[str], max_bytes: int):
    """Percorre a árvore devolvendo arquivos elegíveis. Só isto toca o disco."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if extensions and path.suffix.lower() not in extensions:
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Varre uma árvore em busca de segredos.")
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--ext", default=_DEFAULT_EXT, help="extensões separadas por vírgula; vazio = todas"
    )
    parser.add_argument("--max-mb", type=float, default=8.0)
    args = parser.parse_args()

    if not args.root.exists():
        print(f"caminho inexistente: {args.root}", file=sys.stderr)
        return 2

    extensions = {e.strip().lower() for e in args.ext.split(",") if e.strip()}
    max_bytes = int(args.max_mb * 1024 * 1024)

    total_alta = 0
    scanned = 0
    for path in iter_files(args.root, extensions, max_bytes):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"!! ilegível: {path} ({exc})", file=sys.stderr)
            continue
        scanned += 1
        findings = scan_text(text)
        if not findings:
            continue
        relative = path.relative_to(args.root)
        for finding in findings:
            if finding.severity == "alta":
                total_alta += 1
            print(
                f"[{finding.severity:5}] {relative}:{finding.line_number} "
                f"{finding.rule} -> {finding.masked}  ({finding.why})"
            )

    print(f"\n{scanned} arquivos varridos; {total_alta} achados de severidade alta.")
    return 1 if total_alta else 0


if __name__ == "__main__":
    raise SystemExit(main())
