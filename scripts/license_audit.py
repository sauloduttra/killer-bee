"""Auditoria de licenciamento dos repositórios de uma conta GitHub.

Uso:
    uv run --no-project scripts/license_audit.py sauloduttra > docs/LICENSE-AUDIT.md

Levanta, para cada repo público:

- licença detectada pelo GitHub e presença de arquivo ``LICENSE``/``NOTICE``
- se é fork (fork herda a licença do upstream; repo original sem licença é
  "todos os direitos reservados")
- **contribuidores externos** — o item crítico: enquanto o dono for autor único
  ele detém 100% do copyright e pode relicenciar à vontade. No primeiro PR
  externo aceito sem DCO/CLA, relicenciar vira negociação.
- headers SPDX, via uma única busca de código na conta inteira

Só lê. Não escreve em repositório nenhum, não aplica licença, não faz commit.
Aplicar licença é decisão do dono (VERMELHO na política de autonomia).

Requer ``gh`` autenticado.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Camada pura: classificação
# ---------------------------------------------------------------------------


@dataclass
class Repo:
    name: str
    is_fork: bool
    is_archived: bool
    license_spdx: str | None
    language: str | None
    pushed_at: str
    description: str
    root_files: list[str] = field(default_factory=list)
    contributors: list[str] = field(default_factory=list)
    has_spdx_headers: bool = False
    license_text: str | None = None
    # True quando a listagem da raiz veio da API com sucesso. Sem isso não dá
    # para afirmar AUSENTE — só DESCONHECIDO. A diferença entre os dois foi a
    # causa de dois relatórios errados hoje.
    contents_fetched: bool = False

    @property
    def actual_license(self) -> str:
        """A licença real, lida do arquivo — não o palpite do GitHub.

        AUSENTE só é afirmado quando a listagem da raiz foi obtida COM SUCESSO e
        não continha arquivo de licença. Qualquer falha de coleta vira
        DESCONHECIDO: já houve duas rodadas desta auditoria reportando "49 repos
        sem licença" quando o que faltava era a resposta da API, não o arquivo.
        """
        if not self.contents_fetched:
            return "DESCONHECIDO"
        if not has_license_file(self):
            return "AUSENTE"
        if self.license_text is None:
            # Existe LICENSE na raiz mas o conteúdo não veio — não é ausência.
            return "DESCONHECIDO"
        return classify_license_text(self.license_text)


def external_contributors(repo: Repo, owner: str) -> list[str]:
    """Contribuidores que não são o dono. Puro."""
    owner_lower = owner.lower()
    return [c for c in repo.contributors if c.lower() != owner_lower and not c.endswith("[bot]")]


def has_license_file(repo: Repo) -> bool:
    """Puro: há arquivo de licença na raiz?"""
    return any(f.upper().startswith(("LICENSE", "COPYING")) for f in repo.root_files)


# Assinaturas textuais, em ordem de especificidade. A primeira que casar vence —
# por isso AGPL vem antes de GPL e Apache antes de qualquer coisa genérica.
_LICENSE_SIGNATURES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AGPL-3.0", ("GNU AFFERO GENERAL PUBLIC LICENSE",)),
    ("LGPL-3.0", ("GNU LESSER GENERAL PUBLIC LICENSE",)),
    ("GPL-3.0", ("GNU GENERAL PUBLIC LICENSE", "VERSION 3")),
    ("GPL-2.0", ("GNU GENERAL PUBLIC LICENSE", "VERSION 2")),
    ("Apache-2.0", ("APACHE LICENSE", "VERSION 2.0")),
    ("MPL-2.0", ("MOZILLA PUBLIC LICENSE",)),
    ("BSD-3-Clause", ("REDISTRIBUTION AND USE IN SOURCE AND BINARY FORMS", "NEITHER THE NAME")),
    ("BSD-2-Clause", ("REDISTRIBUTION AND USE IN SOURCE AND BINARY FORMS",)),
    ("ISC", ("ISC LICENSE",)),
    ("Unlicense", ("THIS IS FREE AND UNENCUMBERED SOFTWARE",)),
    ("MIT", ("MIT LICENSE",)),
    ("MIT", ("PERMISSION IS HEREBY GRANTED, FREE OF CHARGE",)),
)


def classify_license_text(text: str | None) -> str:
    """Identifica a licença pelo TEXTO do arquivo. Puro.

    Existe porque o campo ``licenseInfo`` do ``gh repo list`` vem ``null`` mesmo
    quando há um ``LICENSE`` MIT perfeitamente válido na raiz — confiar nele produz
    um falso "todos os direitos reservados" em massa. O arquivo é a verdade;
    o metadado do GitHub é palpite.
    """
    if not text or not text.strip():
        return "AUSENTE"
    upper = " ".join(text.upper().split())
    for spdx, needles in _LICENSE_SIGNATURES:
        if all(needle in upper for needle in needles):
            return spdx
    if "ALL RIGHTS RESERVED" in upper:
        return "PROPRIETÁRIA"
    return "NÃO IDENTIFICADA"


def copyright_line(text: str | None) -> str:
    """Extrai a primeira linha de copyright do texto da licença. Puro."""
    if not text:
        return "—"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("copyright"):
            return stripped
    return "—"


def suggest_tier(repo: Repo, owner: str) -> tuple[str, str]:
    """Propõe um tier e o motivo. Puro.

    O tier é **proposta**, não decisão — a escolha é do dono. A heurística:

    - fork  -> herda a licença do upstream; não é nosso para relicenciar
    - infra/ferramenta genérica -> permissiva convida adoção
    - lab quantitativo original -> onde mora o valor; decisão do dono

    Deliberadamente não sugerimos copyleft forte: AGPL dentro do ecossistema
    Killer Bee (Apache-2.0) contaminaria o projeto inteiro.
    """
    if repo.is_fork:
        return "HERDA", "fork — a licença é a do upstream; não relicenciar"
    if repo.is_archived:
        return "REVISAR", "arquivado — decidir se vale licenciar ou despublicar"
    if external_contributors(repo, owner):
        return "URGENTE", "tem contribuidor externo — relicenciar já exige negociação"

    name = repo.name.lower()
    if name == owner.lower():
        return "N/A", "repo de perfil (README da conta)"

    actual = repo.actual_license
    if actual == "DESCONHECIDO":
        return "RECOLETAR", "a API falhou — isto é lacuna de coleta, não diagnóstico"
    if actual == "AUSENTE":
        return "AGIR", "público sem licença — todos os direitos reservados hoje"
    if actual in ("PROPRIETÁRIA", "NÃO IDENTIFICADA"):
        return "REVISAR", f"licença {actual.lower()} — ler o texto e decidir"
    if not repo.license_spdx:
        return "OK*", f"{actual}, mas o GitHub não detecta — badge não aparece"
    if not repo.has_spdx_headers:
        return "OK", f"{actual}; falta header SPDX nos fontes"
    return "OK", f"{actual}, completo"


# ---------------------------------------------------------------------------
# Camada de I/O: gh
# ---------------------------------------------------------------------------


API_FAILURES = 0
"""Contador global de falhas de API. Vai para o cabeçalho do relatório: um
relatório com falhas silenciadas foi exatamente o que produziu conclusão errada
duas vezes hoje — nunca de novo."""


def assert_jq_projection(args: list[str]) -> None:
    """A guarda do `--jq`, pura — recebe args, levanta ou não. Sem subprocess.

    Separada de `gh_json` para que o teste da guarda não execute `gh` de
    verdade (rede + retries + sleep num teste era o oposto de hermético).
    """
    if "--jq" in args:
        expression = args[args.index("--jq") + 1] if args.index("--jq") + 1 < len(args) else ""
        if not expression.strip().startswith("["):
            raise ValueError(
                f"--jq com projeção escalar produz saída não-JSON: {expression!r}. "
                "Peça o objeto inteiro e indexe em Python."
            )


def gh_json(args: list[str]) -> object:
    """Chama `gh` e devolve JSON. None em falha — mas a falha é CONTADA e logada.

    Retry com backoff: uma rajada de ~370 chamadas dispara o rate limit
    secundário do GitHub e derruba todas as chamadas de uma janela inteira —
    aconteceu na segunda execução desta auditoria e transformou 49 repos MIT em
    falso "AUSENTE". Duas tentativas extras com espera cobrem o transitório.
    """
    global API_FAILURES

    # Guarda contra o bug que esta auditoria cometeu DUAS vezes: `--jq` que
    # projeta um escalar (`.content`, `.license.spdx_id`) imprime a string CRUA,
    # sem aspas, e isso não é JSON. `json.loads` falha, a chamada conta como erro,
    # e o repositório é reportado como "sem licença" quando o dado estava lá.
    #
    # Regra: `--jq` só é permitido quando a projeção é objeto ou array. Para
    # escalar, peça o objeto inteiro e indexe em Python. A guarda vive em
    # `assert_jq_projection` (pura, testável sem subprocess) — não a remova.
    assert_jq_projection(args)

    last_error = ""
    for attempt in range(3):
        if attempt:
            time.sleep(4 * attempt)
        try:
            # encoding explícito: no Windows o default é cp1252 e a saída do `gh`
            # (descrições de repo com emoji/acento) quebra a decodificação.
            out = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            last_error = str(exc)
            continue
        if out.returncode != 0:
            last_error = out.stderr[:200]
            continue
        try:
            return json.loads(out.stdout)
        except json.JSONDecodeError:
            last_error = f"stdout não-JSON: {out.stdout[:100]!r}"
            continue
    API_FAILURES += 1
    print(f"<!-- gh FALHOU 3x em {args[:3]}: {last_error} -->", file=sys.stderr)
    return None


def fetch_repos(owner: str) -> list[Repo]:
    raw = gh_json(
        [
            "repo",
            "list",
            owner,
            "--limit",
            "200",
            "--json",
            "name,visibility,licenseInfo,isFork,isArchived,primaryLanguage,pushedAt,description",
        ]
    )
    if not isinstance(raw, list):
        return []
    repos = []
    for r in raw:
        if r.get("visibility") != "PUBLIC":
            continue
        lic = (r.get("licenseInfo") or {}).get("spdxId")
        repos.append(
            Repo(
                name=r["name"],
                is_fork=bool(r.get("isFork")),
                is_archived=bool(r.get("isArchived")),
                license_spdx=lic,
                language=(r.get("primaryLanguage") or {}).get("name"),
                pushed_at=(r.get("pushedAt") or "")[:10],
                description=(r.get("description") or "").strip(),
            )
        )
    return sorted(repos, key=lambda x: x.name)


def enrich(owner: str, repo: Repo) -> None:
    """Preenche root_files e contributors. Uma chamada de API cada.

    Pacing de 0,15s entre repos: rajada contínua dispara o rate limit
    secundário e derruba a janela inteira.
    """
    time.sleep(0.15)
    contents = gh_json(["api", f"repos/{owner}/{repo.name}/contents", "--jq", "[.[].name]"])
    if isinstance(contents, list):
        repo.root_files = [str(c) for c in contents]
        repo.contents_fetched = True

    # A detecção de licença do GitHub, da fonte certa.
    #
    # `gh repo list --json licenseInfo` devolve `null` para repositórios que a
    # própria API REST classifica como MIT — verificado em `almgren-chriss` e
    # `var-lab`, onde `/repos/{o}/{r}`, `/repos/{o}/{r}/license` e o GraphQL
    # `licenseInfo` os três respondem "MIT". Usar o campo da listagem produziria
    # a conclusão falsa de que 48 repositórios estão com o badge invisível.
    # Sem `--jq`: ver a nota em `gh_json` sobre escalar cru.
    meta = gh_json(["api", f"repos/{owner}/{repo.name}"])
    if isinstance(meta, dict):
        license_field = meta.get("license")
        if isinstance(license_field, dict):
            spdx = license_field.get("spdx_id")
            # A API devolve a string "NOASSERTION" quando encontra um arquivo de
            # licença que não sabe classificar. Não é um SPDX id.
            if isinstance(spdx, str) and spdx not in ("", "NOASSERTION"):
                repo.license_spdx = spdx

    contributors = gh_json(
        ["api", f"repos/{owner}/{repo.name}/contributors?per_page=100", "--jq", "[.[].login]"]
    )
    if isinstance(contributors, list):
        repo.contributors = [str(c) for c in contributors]

    # O texto do LICENSE é a fonte da verdade; licenseInfo do gh é palpite e vem
    # nulo com frequência. Só pagamos a chamada quando o arquivo existe.
    #
    # SEM `--jq '.content'`: jq emite a string base64 CRUA, sem aspas, e isso não
    # é JSON válido — `json.loads` falhava em toda chamada de licença e o repo
    # caía como "sem licença". Pedimos o objeto inteiro e indexamos aqui.
    if has_license_file(repo):
        name = next(f for f in repo.root_files if f.upper().startswith(("LICENSE", "COPYING")))
        payload = gh_json(["api", f"repos/{owner}/{repo.name}/contents/{name}"])
        if isinstance(payload, dict) and isinstance(payload.get("content"), str):
            try:
                repo.license_text = base64.b64decode(payload["content"]).decode(
                    "utf-8", errors="replace"
                )
            except (ValueError, TypeError):
                repo.license_text = None


def find_spdx(owner: str) -> set[str]:
    """Uma única busca de código: quais repos já têm header SPDX."""
    result = gh_json(
        [
            "api",
            f"/search/code?q=SPDX-License-Identifier+user:{owner}&per_page=100",
            "--jq",
            "[.items[].repository.name]",
        ]
    )
    return set(result) if isinstance(result, list) else set()


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------


def main() -> int:
    owner = sys.argv[1] if len(sys.argv) > 1 else "sauloduttra"
    repos = fetch_repos(owner)
    if not repos:
        print("Nenhum repo público encontrado (ou `gh` não autenticado).", file=sys.stderr)
        return 2

    spdx_repos = find_spdx(owner)
    for repo in repos:
        enrich(owner, repo)
        repo.has_spdx_headers = repo.name in spdx_repos

    originals = [r for r in repos if not r.is_fork]
    forks = [r for r in repos if r.is_fork]
    unlicensed_originals = [r for r in originals if r.actual_license == "AUSENTE"]
    with_external = [r for r in originals if external_contributors(r, owner)]

    distribution: dict[str, int] = defaultdict(int)
    for r in originals:
        distribution[r.actual_license] += 1

    # Onde o metadado do GitHub discorda do arquivo real.
    ghost = [r for r in originals if r.actual_license != "AUSENTE" and not r.license_spdx]

    unknown = [r for r in originals if r.actual_license == "DESCONHECIDO"]

    print("# Auditoria de licenciamento — repositórios públicos\n")
    print(f"Conta: `{owner}`. Gerado por `scripts/license_audit.py` (somente leitura).\n")
    print("> **Nada foi aplicado.** Escolher ou alterar licença é decisão do dono.\n")

    if API_FAILURES or unknown:
        print(
            f"> ⚠️ **{API_FAILURES} chamadas de API falharam após 3 tentativas; "
            f"{len(unknown)} repositórios ficaram DESCONHECIDO.** Linhas DESCONHECIDO "
            "não são diagnóstico — são falha de coleta. Reexecute antes de decidir "
            "qualquer coisa sobre elas.\n"
        )

    print("## Resumo\n")
    print(f"- **{len(repos)}** repositórios públicos")
    print(f"- **{len(originals)}** originais · **{len(forks)}** forks")
    print(f"- **{len(unlicensed_originals)}** originais **sem licença nenhuma**")
    print(f"- **{len(with_external)}** com contribuidor externo")
    print(f"- **{len(spdx_repos)}** com header SPDX em algum arquivo\n")
    print("Licenças reais dos originais, lidas do arquivo:\n")
    for spdx in sorted(distribution, key=lambda k: (-distribution[k], k)):
        print(f"- **{spdx}** — {distribution[spdx]}")
    print()

    if ghost:
        print("## ⚠️ Divergência entre o arquivo e a detecção do GitHub\n")
        print(
            f"Em **{len(ghost)}** repositórios existe um `LICENSE` reconhecível na raiz que a\n"
            "API do GitHub **não** classifica. Nesses casos o badge de licença não aparece na\n"
            "interface, e um `LICENSE` que o visitante não vê tem quase o efeito prático de\n"
            "não existir. Vale investigar o arquivo: BOM, linha extra antes do cabeçalho ou\n"
            "nome fora do padrão costumam ser a causa.\n"
        )
    else:
        print("## Sobre o campo `licenseInfo` do `gh repo list`\n")
        print(
            "Esta auditoria **não** usa `gh repo list --json licenseInfo`: aquele campo volta\n"
            "`null` mesmo para repositórios que a própria API classifica como MIT. Confirmado\n"
            "em `almgren-chriss` e `var-lab`, onde `/repos/{owner}/{repo}`,\n"
            "`/repos/{owner}/{repo}/license` e o GraphQL `licenseInfo` respondem **MIT** aos\n"
            'três. Confiar na listagem produziria um falso "todos os direitos reservados" em\n'
            "massa — foi o que aconteceu nas três primeiras rodadas desta auditoria.\n"
        )
        print(
            "As colunas abaixo vêm de duas fontes independentes que **concordam**: o texto\n"
            "do arquivo (`classify_license_text`) e a detecção do GitHub em\n"
            "`/repos/{owner}/{repo}`.\n"
        )

    print("## O que 'sem licença' significa\n")
    print(
        "Repositório público sem `LICENSE` é **todos os direitos reservados**. O código fica\n"
        "visível, mas ninguém pode legalmente usar, modificar ou redistribuir. Público não é\n"
        "open source. É o pior dos dois mundos: o trabalho está exposto e é inutilizável por\n"
        "terceiros — não gera adoção, não gera citação, não gera contribuição, e ainda assim\n"
        "está lá para quem quiser ler.\n"
    )
    print(
        "Licença cobre **implementação, não ideia**. Avellaneda-Stoikov é paper publicado;\n"
        "qualquer um reimplementa legalmente. A licença impede o copy-paste, não a releitura.\n"
        "Isso deve baixar a ansiedade sobre quanto blindar.\n"
    )
    print(
        "**Fork herda a licença do upstream.** Os forks desta lista não são seus para\n"
        "relicenciar — a coluna de tier marca `HERDA` e eles saem da decisão.\n"
    )

    print("## Urgência\n")
    if with_external:
        print("⚠️ **Estes já têm contribuidor externo — relicenciar exige negociação:**\n")
        for r in with_external:
            ext = ", ".join(external_contributors(r, owner))
            print(f"- `{r.name}` — {ext}")
        print()
    else:
        print(
            "✅ **Nenhum repositório original tem contribuidor externo.** O dono detém 100% do\n"
            "copyright e pode relicenciar o que quiser, quando quiser. Essa janela fecha no\n"
            "primeiro PR externo aceito sem DCO ou CLA. Licenciar agora, antes de ganhar\n"
            "visibilidade, é barato; depois vira negociação com cada contribuidor.\n"
        )

    print("## Repositórios originais\n")
    print(
        "`licença real` vem do texto do arquivo. `GitHub vê` é o que a API reporta — quando"
        " diverge, o badge não aparece na interface.\n"
    )
    print(
        "| repo | licença real | GitHub vê | titular | SPDX | contrib. externos "
        "| linguagem | último push | tier | motivo |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    problematic = ("AUSENTE", "PROPRIETÁRIA", "NÃO IDENTIFICADA", "DESCONHECIDO")
    for r in originals:
        tier, why = suggest_tier(r, owner)
        ext = external_contributors(r, owner)
        actual = r.actual_license
        cell = f"**{actual}**" if actual in problematic else actual
        print(
            f"| `{r.name}` | {cell} | {r.license_spdx or '—'} | "
            f"{copyright_line(r.license_text)} | "
            f"{'sim' if r.has_spdx_headers else 'não'} | "
            f"{', '.join(ext) if ext else '—'} | {r.language or '—'} | {r.pushed_at} | "
            f"{tier} | {why} |"
        )

    print("\n## Forks (licença herdada do upstream — fora da decisão)\n")
    by_lang: dict[str, list[str]] = defaultdict(list)
    for r in forks:
        by_lang[r.language or "—"].append(r.name)
    for lang in sorted(by_lang):
        print(f"- **{lang}**: {', '.join(f'`{n}`' for n in sorted(by_lang[lang]))}")

    print("\n## Compatibilidade dentro do Killer Bee\n")
    print(
        "Killer Bee é Apache-2.0. Pode incorporar **MIT** e **Apache-2.0** sem fricção.\n"
        "**Não pode** incorporar **AGPL** sem se tornar AGPL — e AGPL no Killer Bee mata a\n"
        "adoção corporativa e qualquer chance de a Block encostar. Se um lab que a gente\n"
        "queira expor como ferramenta MCP for copyleft forte, ou ele fica fora do pacote, ou\n"
        "o projeto inteiro muda de licença. É uma decisão de arquitetura, não de burocracia.\n"
    )

    print("## Aplicação — depois do OK, por tier\n")
    print("Para cada repo aprovado:\n")
    print("1. `LICENSE` na raiz, texto íntegro, ano e titular corretos")
    print("2. Header no topo de cada fonte: `SPDX-License-Identifier: <ID>`")
    print("3. Apache-2.0: `NOTICE` na raiz quando houver terceiros")
    print("4. Seção de licença explícita no `README` — ninguém deve precisar abrir o `LICENSE`")
    print("5. Commit único por repo: `chore: add <licença>`\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
