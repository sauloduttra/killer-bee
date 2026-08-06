"""Compara primeiro e segundo leitor de uma verificação bibliográfica.

Uso:
    uv run --no-project scripts/diff_bibliografia.py <journal.jsonl>

Imprime só onde os dois leitores **divergem** ou onde o veredito não é
CONFIRMADO. O ponto de ter um segundo leitor é achar o que o primeiro errou;
listar as concordâncias esconde isso no meio do ruído.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from read_workflow_result import extract_results


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print("uso: diff_bibliografia.py <journal.jsonl>", file=sys.stderr)
        return 2

    journal = Path(sys.argv[1])
    results = extract_results(journal.read_text(encoding="utf-8", errors="replace"))

    # O retorno final do workflow é uma lista de {grupo, primeiro, segundo}.
    pares = [r for r in results if isinstance(r, dict) and "segundo" in r]
    if not pares:
        # Fallback: os resultados individuais dos agentes, na ordem em que saíram.
        pares = [r for r in results if isinstance(r, dict) and "referencias" in r]
        for bloco in pares:
            print(f"\n{'=' * 88}\nGRUPO: {bloco.get('grupo')}")
            for ref in bloco.get("referencias", []):
                print(f"  [{ref.get('veredito')}] {ref.get('mecanismo', '')[:70]}")
        return 0

    for par in pares:
        primeiro = {
            r.get("mecanismo", "")[:60]: r
            for r in (par.get("primeiro") or {}).get("referencias", [])
        }
        segundo = (par.get("segundo") or {}).get("referencias", [])
        print(f"\n{'=' * 88}\nGRUPO: {par.get('grupo')}")
        for ref in segundo:
            chave = ref.get("mecanismo", "")[:60]
            v2 = ref.get("veredito")
            v1 = (primeiro.get(chave) or {}).get("veredito", "?")
            marca = "  " if v1 == v2 == "CONFIRMADO" else "!!"
            print(f"{marca} {chave}")
            print(f"     1o leitor: {v1}   |   2o leitor: {v2}")
            if v2 != "CONFIRMADO" or v1 != v2:
                print(f"     correto: {ref.get('correto', '')[:400]}")
                nota = ref.get("nota", "")
                if nota:
                    print(f"     nota: {nota[:700]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
