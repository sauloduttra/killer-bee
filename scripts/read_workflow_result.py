"""Extrai os resultados estruturados de um `journal.jsonl` de workflow.

Uso:
    uv run --no-project scripts/read_workflow_result.py <journal.jsonl> [--jq campo]

Existe porque o journal de um workflow com muitos agentes chega a centenas de
milhares de tokens — ler o arquivo inteiro estoura a janela de contexto e
esconde o que interessa. Este script isola só os valores de retorno.

Puro o suficiente: `extract_results` recebe texto e devolve objetos; só `main`
toca disco.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path


def extract_results(journal_text: str) -> list[object]:
    """Devolve o valor de retorno de cada agente concluído, em ordem.

    Uma linha malformada é pulada em silêncio: o journal é escrito
    incrementalmente e a última linha pode estar parcial enquanto o workflow
    ainda roda.
    """
    results: list[object] = []
    for line in journal_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "result":
            continue
        value = entry.get("value", entry.get("result"))
        if isinstance(value, str):
            # Alguns runners serializam o retorno como string JSON; quando não é
            # JSON, a string crua já é o resultado.
            with contextlib.suppress(json.JSONDecodeError):
                value = json.loads(value)
        results.append(value)
    return results


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("journal", type=Path)
    parser.add_argument("--field", help="imprime só este campo de topo de cada resultado")
    args = parser.parse_args()

    if not args.journal.is_file():
        print(f"journal não encontrado: {args.journal}", file=sys.stderr)
        return 2

    results = extract_results(args.journal.read_text(encoding="utf-8", errors="replace"))
    print(f"# {len(results)} resultado(s)\n", file=sys.stderr)

    for index, result in enumerate(results, start=1):
        if args.field and isinstance(result, dict):
            result = result.get(args.field, f"<sem campo {args.field}>")
        print(f"{'=' * 90}\n# resultado {index}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
