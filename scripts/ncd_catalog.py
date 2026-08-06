"""NCD (Normalized Compression Distance) entre os prompts do catálogo.

FASE-2 §4.1: NCD(x,y) = [C(xy) - min(C(x),C(y))] / max(C(x),C(y)), com zstd.
Par com NCD baixa não é bug do detector — é o catálogo dizendo a verdade
sobre si mesmo. A DECISÃO de corte é do usuário; este script entrega números.

Divergência registrada (D-034): scripts/ era stdlib-only; o FASE-2 manda zstd,
então este script depende de `zstandard` (grupo dev). Rode com `uv run`.

Método, para o CATALOG-AUDIT.md poder citar:
- Unidade comparada: o CORPO do .persona.md (prompt), frontmatter removido.
  O frontmatter carrega nome/modelo e inflaria similaridade estrutural.
- Compressor primário: zstd nível 19 (determinístico para nível+entrada fixos).
- Cross-check: lzma preset 6 (D-014 — duas fontes independentes; a concordância
  é o resultado). Reportamos a sobreposição do fundo do ranking entre os dois.
- packs/TEMPLATE é excluído: é o caminho-de-10-minutos, não conteúdo de catálogo.

Saídas:
- docs/catalog-ncd-matrix.csv  (matriz simétrica completa, zstd)
- JSON em stdout com estatísticas, pares ordenados e concordância zstd vs lzma.

Falha ruidosa, nunca silêncio: zero personas, corpo vazio ou frontmatter
malformado levantam exceção dizendo qual arquivo e por quê.
"""

from __future__ import annotations

import csv
import json
import lzma
import statistics
import sys
from collections.abc import Callable
from pathlib import Path

import zstandard

ZSTD_LEVEL = 19
LZMA_PRESET = 6


# ── camada pura ──────────────────────────────────────────────────────────────


def ncd_from_sizes(c_x: int, c_y: int, c_xy: int) -> float:
    """NCD pela fórmula do FASE-2 §4.1, sobre tamanhos já comprimidos.

    Levanta ValueError para tamanhos não-positivos: tamanho comprimido de
    entrada não-vazia nunca é <= 0, então um zero aqui é bug do chamador —
    não vira NaN nem divisão por zero silenciosa.
    """
    if c_x <= 0 or c_y <= 0 or c_xy <= 0:
        raise ValueError(f"tamanho comprimido não-positivo: c_x={c_x} c_y={c_y} c_xy={c_xy}")
    return (c_xy - min(c_x, c_y)) / max(c_x, c_y)


def strip_frontmatter(persona_text: str, *, origin: str) -> str:
    """Devolve o corpo do .persona.md, sem o bloco de frontmatter YAML.

    O formato nativo do Buzz abre o arquivo com `---\\n ... \\n---\\n`.
    Arquivo sem esse bloco, ou com corpo vazio, é erro fatal com o caminho
    no texto — nunca um corpo vazio comparado em silêncio.
    """
    if not persona_text.startswith("---\n"):
        raise ValueError(f"{origin}: sem frontmatter YAML no início")
    end = persona_text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{origin}: frontmatter não fechado")
    body = persona_text[end + len("\n---\n") :].strip()
    if not body:
        raise ValueError(f"{origin}: corpo vazio após o frontmatter")
    return body


# ── camada de compressão (impura, determinística) ────────────────────────────


def zstd_size_bytes(data: bytes) -> int:
    return len(zstandard.ZstdCompressor(level=ZSTD_LEVEL).compress(data))


def lzma_size_bytes(data: bytes) -> int:
    return len(lzma.compress(data, preset=LZMA_PRESET))


def pairwise_ncd(
    bodies_utf8: dict[str, bytes], size_of: Callable[[bytes], int]
) -> list[tuple[float, str, str]]:
    """Todos os pares (NCD, a, b) com a < b, ordenados do mais próximo ao mais distante."""
    names = sorted(bodies_utf8)
    single = {n: size_of(bodies_utf8[n]) for n in names}
    pairs: list[tuple[float, str, str]] = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            c_xy = size_of(bodies_utf8[a] + bodies_utf8[b])
            pairs.append((ncd_from_sizes(single[a], single[b], c_xy), a, b))
    pairs.sort(key=lambda t: (t[0], t[1], t[2]))
    return pairs


# ── camada de I/O ────────────────────────────────────────────────────────────


def load_catalog_bodies(packs_root: Path) -> dict[str, bytes]:
    """{'pack/persona': corpo utf-8} para todo .persona.md fora de TEMPLATE."""
    bodies: dict[str, bytes] = {}
    for persona_path in sorted(packs_root.glob("*/personas/*.persona.md")):
        pack = persona_path.parent.parent.name
        if pack == "TEMPLATE":
            continue
        key = f"{pack}/{persona_path.stem.removesuffix('.persona')}"
        text = persona_path.read_text(encoding="utf-8")
        bodies[key] = strip_frontmatter(text, origin=str(persona_path)).encode("utf-8")
    if not bodies:
        raise SystemExit(f"nenhuma persona encontrada sob {packs_root} — isso é falha, não zero")
    return bodies


def write_matrix_csv(
    out_csv: Path, names: list[str], ncd_by_pair: dict[frozenset[str], float]
) -> None:
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["persona", *names])
        for a in names:
            row: list[str] = [a]
            for b in names:
                value = 0.0 if a == b else ncd_by_pair[frozenset((a, b))]
                row.append(f"{value:.4f}")
            writer.writerow(row)


def bottom_k_overlap(
    pairs_a: list[tuple[float, str, str]], pairs_b: list[tuple[float, str, str]], k: int
) -> float:
    """Fração de sobreposição entre os k pares mais próximos dos dois rankings."""
    if k <= 0:
        raise ValueError(f"k deve ser positivo, veio {k}")
    set_a = {(a, b) for _, a, b in pairs_a[:k]}
    set_b = {(a, b) for _, a, b in pairs_b[:k]}
    return len(set_a & set_b) / k


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    packs_root = repo_root / "packs"
    bodies = load_catalog_bodies(packs_root)

    zstd_pairs = pairwise_ncd(bodies, zstd_size_bytes)
    lzma_pairs = pairwise_ncd(bodies, lzma_size_bytes)

    names = sorted(bodies)
    ncd_by_pair = {frozenset((a, b)): v for v, a, b in zstd_pairs}
    out_csv = repo_root / "docs" / "catalog-ncd-matrix.csv"
    write_matrix_csv(out_csv, names, ncd_by_pair)

    values = [v for v, _, _ in zstd_pairs]
    median = statistics.median(values)
    mad = statistics.median([abs(v - median) for v in values])
    # Limiar robusto e declarado: 3 MADs abaixo da mediana. Não é veredito —
    # é onde o "fundo" começa a descolar do corpo da distribuição.
    threshold = median - 3.0 * mad
    flagged = [(v, a, b) for v, a, b in zstd_pairs if v < threshold]

    k = max(len(flagged), 10)
    summary = {
        "personas": len(bodies),
        "pares": len(zstd_pairs),
        "zstd_level": ZSTD_LEVEL,
        "lzma_preset": LZMA_PRESET,
        "min": min(values),
        "mediana": median,
        "max": max(values),
        "mad": mad,
        "limiar_mediana_menos_3mad": threshold,
        "pares_abaixo_do_limiar": [{"ncd": round(v, 4), "a": a, "b": b} for v, a, b in flagged],
        "top20_mais_proximos": [
            {"ncd": round(v, 4), "a": a, "b": b} for v, a, b in zstd_pairs[:20]
        ],
        "concordancia_zstd_lzma_bottom_k": {
            "k": k,
            "sobreposicao": bottom_k_overlap(zstd_pairs, lzma_pairs, k),
        },
        "matriz_csv": str(out_csv.relative_to(repo_root)),
    }
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
