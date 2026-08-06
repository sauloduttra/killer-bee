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


# Cada regra é (nome, severidade, regex compilada, explicação, exclusão-de-contexto).
#
# A severidade "alta" significa: isto sozinho impede o arquivo de entrar num repo
# público. "media" pede olho humano. "baixa" é ruído frequente que ainda assim vale
# listar porque o custo de um falso negativo é maior que o de um falso positivo.
#
# A exclusão-de-contexto (5º campo, opcional) suprime a regra quando a LINHA
# casa com ela — existe para o `bare_hex_64` não gritar em cada sha256 legítimo
# do catálogo. Exclusão é por linha e por regra, nunca global.
#
# Fora do alcance DECLARADO: conteúdo base64/binário (inclusive o payload dos
# .agent.png que este projeto gera) e entropia de Shannon — segredo embutido em
# base64 não é detectado por estas regras. Auditoria 2026-08-06.
_RULES: tuple[tuple[str, str, re.Pattern[str], str, re.Pattern[str] | None], ...] = (
    (
        "nostr_nsec",
        "alta",
        re.compile(r"\bnsec1[02-9ac-hj-np-z]{58,}\b"),
        "chave privada Nostr bech32 — identidade completa, não config",
        None,
    ),
    (
        "nostr_ncryptsec",
        "alta",
        re.compile(r"\bncryptsec1[02-9ac-hj-np-z]{20,}\b"),
        "chave privada Nostr criptografada (NIP-49) — ainda é a chave",
        None,
    ),
    (
        "bare_hex_64",
        "media",
        re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])"),
        "64 hex nu — formato de chave privada secp256k1/Nostr sem rótulo",
        # sha256/checksum/id de evento têm o mesmo formato; contexto decide.
        re.compile(r"(?i)sha-?256|checksum|hash|integrity|digest|commit|event[_-]?id|\"x\s"),
    ),
    (
        "hex_privkey_64",
        "alta",
        re.compile(r"(?i)\b(?:priv(?:ate)?[_-]?key|secret[_-]?key|nsec)\b\W{0,4}([0-9a-f]{64})\b"),
        "64 hex nomeado como chave privada",
        None,
    ),
    (
        "aws_access_key",
        "alta",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "AWS access key id",
        None,
    ),
    (
        "github_token",
        "alta",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        "token do GitHub",
        None,
    ),
    (
        "openai_key",
        "alta",
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
        "chave de API estilo OpenAI",
        None,
    ),
    (
        "anthropic_key",
        "alta",
        re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
        "chave de API Anthropic",
        None,
    ),
    (
        "stripe_live_key",
        "alta",
        re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}\b"),
        "chave live do Stripe",
        None,
    ),
    (
        "npm_token",
        "alta",
        re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b"),
        "token do npm",
        None,
    ),
    (
        "gitlab_pat",
        "alta",
        re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
        "personal access token do GitLab",
        None,
    ),
    (
        "sendgrid_key",
        "alta",
        re.compile(r"\bSG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b"),
        "chave de API SendGrid",
        None,
    ),
    (
        "google_api_key",
        "media",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
        "chave de API Google — muitas são restringíveis, mas olho humano decide",
        None,
    ),
    (
        "slack_token",
        "alta",
        re.compile(r"\bxox[abcprs]-[A-Za-z0-9-]{10,}\b"),
        "token do Slack",
        None,
    ),
    (
        "private_key_block",
        "alta",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
        "bloco PEM de chave privada",
        None,
    ),
    (
        "jwt",
        "media",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
        "JWT — pode carregar claim identificável mesmo expirado",
        None,
    ),
    (
        "generic_assignment",
        "media",
        # O nome casa por SUFIXO (`[\w.-]*`) de propósito: a primeira versão listava
        # só `access_token`/`auth_token` e deixava passar `SEMGREP_TOKEN: "..."`,
        # `GITHUB_TOKEN`, `BUZZ_S3_SECRET_KEY` — exatamente a forma que aparece em
        # `.env` e em config de MCP server. O valor casa entre aspas OU nu até o fim
        # da linha (estilo `.env`: `API_KEY=valor` sem aspas — a versão só-com-aspas
        # não via exatamente o formato do arquivo que mais carrega segredo).
        # `os.getenv("X")` e `${X}` continuam rebaixados pelo detector de placeholder.
        # `[_-]key` (com separador obrigatório) em vez de `key` solto: pega
        # `BUZZ_S3_SECRET_KEY` e `signing-key` sem casar com `monkey` ou `keyboard`.
        re.compile(
            r"(?i)\b[\w.-]*(?:api[_-]?key|apikey|[_-]key|token|password|passwd|senha|secret|passphrase)\b"
            r"\s*[:=]\s*(?:[\"']([^\"'\s]{8,})[\"']|([^\s\"'#]{8,})\s*$)"
        ),
        "credencial atribuída a literal no fonte",
        None,
    ),
    (
        "connection_string",
        "media",
        re.compile(
            r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@/]+:[^\s@/]+@"
        ),
        "string de conexão com senha embutida",
        None,
    ),
    (
        "cpf",
        "media",
        re.compile(r"(?<!\d)\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)"),
        "CPF formatado — dado pessoal",
        None,
    ),
    (
        "email",
        "baixa",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "e-mail — verificar se é de terceiro",
        None,
    ),
    (
        "private_ip_url",
        "baixa",
        re.compile(r"\bhttps?://(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)[^\s\"']+"),
        "URL para host de rede interna",
        None,
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
        # O allow-marker é checado ANTES de qualquer janela/truncagem: a versão
        # anterior truncava primeiro, e um marcador (ou um segredo) depois da
        # coluna 4000 ficava invisível — JSON minificado e .env de linha única
        # são exatamente onde segredo mora.
        if _ALLOW_MARKER.search(line):
            continue
        is_placeholder = bool(_PLACEHOLDER.search(line))

        # Linha longa é varrida em janelas com sobreposição, nunca truncada.
        # A sobreposição (256) é maior que o maior token que as regras casam,
        # então nenhum segredo escapa por cair na fronteira entre janelas.
        if len(line) <= 4000:
            windows = [line]
        else:
            windows = [line[i : i + 4096] for i in range(0, len(line), 4096 - 256)]

        seen_in_line: set[tuple[str, str]] = set()
        for window in windows:
            for rule, severity, pattern, why, context_exclusion in _RULES:
                match = pattern.search(window)
                if match is None:
                    continue
                if context_exclusion is not None and context_exclusion.search(line):
                    continue
                # O último grupo casado isola o valor; sem grupos, o casamento todo.
                value = match.group(match.lastindex or 0)
                key = (rule, value)
                if key in seen_in_line:
                    continue  # mesma suspeita vista em duas janelas sobrepostas
                seen_in_line.add(key)
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


def _extension_eligible(path: Path, extensions: set[str]) -> bool:
    """Elegibilidade por extensão, com o caso que `suffix` não cobre.

    `Path(".env").suffix` é `""` e `Path(".env.local").suffix` é `".local"` —
    ou seja, com o filtro só por suffix os arquivos chamados `.env` (a casa
    natural de credencial) NUNCA eram varridos, apesar de `.env` constar na
    lista de extensões. Auditoria 2026-08-06.
    """
    if not extensions:
        return True
    name = path.name.lower()
    if name == ".env" or name.startswith(".env."):
        return ".env" in extensions
    return path.suffix.lower() in extensions


def iter_files(root: Path, extensions: set[str], max_bytes: int):
    """Percorre a árvore devolvendo arquivos elegíveis. Só isto toca o disco."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if not _extension_eligible(path, extensions):
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
    parser.add_argument(
        "--fail-on",
        choices=("alta", "media"),
        default="alta",
        help="severidade mínima que derruba o exit code (media inclui alta)",
    )
    args = parser.parse_args()

    if not args.root.exists():
        print(f"caminho inexistente: {args.root}", file=sys.stderr)
        return 2

    extensions = {e.strip().lower() for e in args.ext.split(",") if e.strip()}
    max_bytes = int(args.max_mb * 1024 * 1024)

    gating = {"alta"} if args.fail_on == "alta" else {"alta", "media"}
    total_gating = 0
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
            if finding.severity in gating:
                total_gating += 1
            print(
                f"[{finding.severity:5}] {relative}:{finding.line_number} "
                f"{finding.rule} -> {finding.masked}  ({finding.why})"
            )

    print(
        f"\n{scanned} arquivos varridos; {total_gating} achados em "
        f"severidade gatilho ({args.fail_on}+)."
    )
    return 1 if total_gating else 0


if __name__ == "__main__":
    raise SystemExit(main())
