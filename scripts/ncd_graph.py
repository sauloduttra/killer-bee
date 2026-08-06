"""Gera o grafo de similaridade do hero: `site/data/ncd-graph.json`.

O hero antigo plotava cada persona como um traço isolado. Este desenha o que
está ENTRE elas: a distância de compressão normalizada que a auditoria já mede.

    NCD(x,y) = [C(xy) - min(C(x),C(y))] / max(C(x),C(y))          (zstd-19)

Uma aresta existe **se e somente se** o par mede abaixo do limiar robusto
publicado (mediana menos 3 MADs sobre os 1128 pares). Nada é desenhado por estética:
posição sai de relaxação sobre essas arestas, tamanho do nó sai de
``recruitment``, espessura da aresta sai de quão abaixo do limiar o par mediu.
**Ausência também é informação** — persona sem aresta é persona sem parente
medido no catálogo, e ela aparece sozinha de propósito.

Uma definição por número, de propósito:

- o limiar vem de ``ncd_catalog.robust_threshold`` — a MESMA função que o
  CATALOG-AUDIT usa para publicar o seu;
- a curva de tamanho vem de ``killerbee.signature.length_from_recruitment`` — a
  MESMA que rasteriza o corpo dos `.agent.png`, travada por golden em
  test_signature. Nenhuma cópia nova de `0.28 + 0.72·raiz(...)` entra aqui;
- a chave impressa no rodapé é gerada CHAMANDO as mesmas funções que desenham o
  dado. Escala aproximada mente sobre o próprio gráfico.

Determinismo: nenhum RNG, nenhum relógio. A condição inicial é o catálogo (as
posições exatas do hero antigo), não uma semente. Dentro do laço só entram as
quatro operações e a raiz quadrada. Trigonometria aparece duas vezes, ambas
FORA do laço e quantizadas: no círculo inicial (6 casas) e nos hexágonos, que
usam apenas raiz de 3 sobre 2, sem seno. O teste prova determinismo na mesma
plataforma; entre implementações de libm a quantização absorve diferença de ULP
na prática -- afirmação mais modesta, e honesta, que "bit-idêntico em qualquer
lugar".

Uso: ``uv run python scripts/ncd_graph.py`` (chamado pelo prepare-data.mjs).
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from ncd_catalog import (  # noqa: E402
    ZSTD_LEVEL,
    load_catalog_bodies,
    pairwise_ncd,
    robust_threshold,
    zstd_size_bytes,
)

from killerbee.signature import length_from_recruitment  # noqa: E402

# ── moldura (unidades do viewBox) ────────────────────────────────────────────
# Alto maior que largo porque a faixa de escala mora embaixo do desenho, fora
# do disco: escala impressa DENTRO do dado disputaria tinta com ele.
VIEWBOX_W = 320
VIEWBOX_H = 336
CENTER_X = 160.0
CENTER_Y = 138.0
FRAME_RADIUS = 118.0

# ── nó ───────────────────────────────────────────────────────────────────────
R_MIN = 3.4
R_MAX = 8.0
# Folga do alvo de toque por lado. Era 3,5, e a 3,5 as seis células de
# `recruitment` 1 ficavam em 22,3 px no desktop — abaixo do mínimo, num desenho
# que declarava cumpri-lo.
#
# 6,5 saiu de medir, não de estimar. O que decide não é o telefone: em duas
# colunas a figura é MENOR (448 px num viewport de 1280) do que em coluna única
# (703 px em 820), então o laptop comum é o caso apertado. A 6,5 o alvo dá
# 27,7 px a 1280 e o ponteiro só desliga abaixo de 388 px de figura. Custo
# medido nos aglomerados, que são o SENTIDO do desenho: aresta média sai de 28,8%
# para 30,2% da distância média entre pares — dentro do ruído. A 8,0 já seria
# 32,1% e o desenho começaria a se soltar.
HIT_PAD = 6.5
# WCAG 2.5.8 (AA): alvo de ponteiro de 24 x 24 px CSS.
MIN_TOUCH_TARGET_PX = 24.0
STROKE_BY_PERSISTENCE = {"short": 0.7, "medium": 1.2, "long": 1.8}

# ── aresta ───────────────────────────────────────────────────────────────────
W_MIN = 0.65
W_SPAN = 1.35
HATCH_LEN = 5.0

# ── faixa de escala ──────────────────────────────────────────────────────────
PLATE_Y = 272

# ── relaxação ────────────────────────────────────────────────────────────────
ITERATIONS = 300
K_SPRING = 16.0
GRAVITY = 1.0
TEMP0 = FRAME_RADIUS / 10.0
MIN_DISTANCE = 0.01
SEPARATION_SWEEPS = 80
SEPARATION_STEP = 0.4

# ── tempo (ms) — ORDEM é o que o tempo codifica; duração é constante ─────────
EDGE_DELAY_BASE = 210
EDGE_DELAY_STEP = 14
CELL_LEAD = 90

SQRT3_2 = math.sqrt(3.0) / 2.0

# Par-controle: as duas personas escritas à mão para serem máximas em diferença.
# Aresta abaixo DELE é um par gerado mais parecido que dois colegas desenhados
# para divergir — o defeito conhecido que o D-036 aceitou e que o site imprime.
CONTROL_PAIR = ("crossfire-review/adversary", "crossfire-review/guard")


@dataclass
class Node:
    key: str
    pack: str
    persona: str
    display_name: str
    recruitment: int
    persistence: str
    x: float = 0.0
    y: float = 0.0
    r: float = R_MIN
    degree: int = 0
    delay_ms: int | None = None
    neighbours: list[str] = field(default_factory=list)


# ── camada pura ──────────────────────────────────────────────────────────────


def radius_from_recruitment(recruitment: int) -> float:
    """Circunraio do hexágono, em unidades do viewBox.

    Remapeia a curva de comprimento da dança (0,28..1,0) para R_MIN..R_MAX. A
    compressão por raiz é dela, não nossa: a diferença entre 1 e 4 conversas
    paralelas importa muito mais que entre 28 e 32.
    """
    length = length_from_recruitment(recruitment)
    return R_MIN + (R_MAX - R_MIN) * (length - 0.28) / 0.72


def width_from_ncd(ncd: float, threshold: float, ncd_min: float) -> float:
    """Espessura da aresta: quão ABAIXO do limiar o par mediu.

    Piso em W_MIN para o par mais fraco continuar sendo uma linha, e não um
    artefato de antialiasing. Se limiar e mínimo coincidirem (catálogo de um
    par só), devolve o piso em vez de dividir por zero em silêncio.
    """
    span = threshold - ncd_min
    if span <= 0.0:
        return W_MIN
    return W_MIN + W_SPAN * (threshold - ncd) / span


def hexagon_path(cx: float, cy: float, r: float) -> str:
    """Hexágono regular de topo pontudo, como o favo do fundo do site.

    Sem trig: os seis vértices de um hexágono de topo pontudo são
    (0,±r) e (±r·√3/2, ±r/2). Uma raiz só, correta por IEEE-754.
    """
    dx = r * SQRT3_2
    dy = r / 2.0
    pts = [
        (cx, cy - r),
        (cx + dx, cy - dy),
        (cx + dx, cy + dy),
        (cx, cy + r),
        (cx - dx, cy + dy),
        (cx - dx, cy - dy),
    ]
    head = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    rest = " ".join(f"L{x:.2f} {y:.2f}" for x, y in pts[1:])
    return f"{head} {rest} Z"


def initial_positions(count: int, recruitments: list[int]) -> list[tuple[float, float]]:
    """O campo de dança do hero antigo, na moldura nova.

    Mesma construção: ângulo pela posição no catálogo com meio passo de
    deslocamento, raio pela curva de `recruitment` a partir de um hub em 0,18.
    **Não é cópia coordenada a coordenada** do desenho removido — a moldura
    mudou de tamanho e de centro, então as posições saem reescaladas; o que se
    preserva é a FORMA e a ordem, não os números.

    O ponto que importa: não há semente aleatória. A condição inicial é o
    próprio catálogo, e é por isso que o resultado é reproduzível.
    """
    if count == 0:
        return []
    hub = 0.18  # o mesmo HUB de killerbee/signature.py
    inner = (FRAME_RADIUS + 22.0) * hub
    outer = (FRAME_RADIUS + 22.0) - inner
    step = 360.0 / count
    out: list[tuple[float, float]] = []
    for i, recruitment in enumerate(recruitments):
        angle = math.radians(i * step + step / 2.0 - 90.0)
        radius = inner + outer * length_from_recruitment(recruitment)
        # Quantizado ANTES do laço: diferença de 1 ULP em libm não propaga.
        x = round(CENTER_X + radius * math.cos(angle), 6)
        y = round(CENTER_Y + radius * math.sin(angle), 6)
        out.append((x, y))
    return out


def clamp_to_frame(x: float, y: float) -> tuple[float, float]:
    dx = x - CENTER_X
    dy = y - CENTER_Y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist <= FRAME_RADIUS or dist == 0.0:
        return x, y
    scale = FRAME_RADIUS / dist
    return CENTER_X + dx * scale, CENTER_Y + dy * scale


def relax(
    positions: list[tuple[float, float]],
    radii: list[float],
    edges: list[tuple[int, int, float]],
    iterations: int = ITERATIONS,
) -> list[tuple[float, float]]:
    """Spring embedder de Fruchterman-Reingold com gravidade de enquadramento.

    Repulsão entre todos os pares, atração só nas arestas medidas (ponderada
    por quão abaixo do limiar o par está), gravidade para o centro — sem ela os
    15 componentes voam para sempre, e ela é enquadramento declarado, não dado:
    **a posição em si não mede nada**, só a vizinhança mede.

    Puro: recebe listas, devolve lista. Sem relógio, sem random, sem I/O.
    """
    pos = [(x, y) for x, y in positions]
    n = len(pos)
    if n == 0:
        return []

    for step_index in range(iterations):
        temp = TEMP0 * (1.0 - step_index / iterations)
        disp = [[0.0, 0.0] for _ in range(n)]

        for i in range(n):
            xi, yi = pos[i]
            for j in range(i + 1, n):
                xj, yj = pos[j]
                dx = xi - xj
                dy = yi - yj
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < MIN_DISTANCE:
                    # Determinístico e sem NaN: separa no eixo x. Alcançável
                    # apenas com dois nós coincidentes, o que o círculo inicial
                    # não produz — mas o guarda fica, porque a alternativa é
                    # divisão por zero. `test_layout_nunca_produz_nan_nem_infinito`
                    # força exatamente esse caso.
                    dx, dy, dist = MIN_DISTANCE, 0.0, MIN_DISTANCE
                force = (K_SPRING * K_SPRING) / dist
                ux = dx / dist
                uy = dy / dist
                disp[i][0] += ux * force
                disp[i][1] += uy * force
                disp[j][0] -= ux * force
                disp[j][1] -= uy * force

        for i, j, weight in edges:
            xi, yi = pos[i]
            xj, yj = pos[j]
            dx = xi - xj
            dy = yi - yj
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < MIN_DISTANCE:
                dx, dy, dist = MIN_DISTANCE, 0.0, MIN_DISTANCE
            force = weight * dist * dist / K_SPRING
            ux = dx / dist
            uy = dy / dist
            disp[i][0] -= ux * force
            disp[i][1] -= uy * force
            disp[j][0] += ux * force
            disp[j][1] += uy * force

        for i in range(n):
            disp[i][0] += (CENTER_X - pos[i][0]) * GRAVITY
            disp[i][1] += (CENTER_Y - pos[i][1]) * GRAVITY

        for i in range(n):
            dx, dy = disp[i]
            magnitude = math.sqrt(dx * dx + dy * dy)
            if magnitude > MIN_DISTANCE:
                capped = min(magnitude, temp)
                nx = pos[i][0] + (dx / magnitude) * capped
                ny = pos[i][1] + (dy / magnitude) * capped
                pos[i] = clamp_to_frame(nx, ny)

    # Enquadrar ANTES de separar: a separação trabalha em unidades absolutas
    # (raio + folga), então precisa ver o desenho no tamanho final. Na ordem
    # inversa a escala reabriria ou fecharia as folgas que ela acabou de impor.
    return separate(fit_to_frame(pos, radii), radii)


def separate(
    positions: list[tuple[float, float]], radii: list[float], sweeps: int = SEPARATION_SWEEPS
) -> list[tuple[float, float]]:
    """Empurra nós até nenhum par de células se tocar.

    A folga ALVO é ``r_i + r_j + 2·HIT_PAD``, para os alvos de toque também não
    se sobreporem. Se as varreduras acabarem antes disso, o desenho continua
    válido — o que o chamador garante depois é o invariante FRACO (célula não
    encosta em célula), que é satisfazível por construção; o alvo forte vira
    número relatado no JSON, não portão de build. Invariante geométrico duro
    quebra o deploy no dia em que alguém edita um prompt.
    """
    pos = [(x, y) for x, y in positions]
    n = len(pos)
    for _ in range(sweeps):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[i][0] - pos[j][0]
                dy = pos[i][1] - pos[j][1]
                dist = math.sqrt(dx * dx + dy * dy)
                need = radii[i] + radii[j] + 2.0 * HIT_PAD
                if dist >= need:
                    continue
                if dist < MIN_DISTANCE:
                    dx, dy, dist = MIN_DISTANCE, 0.0, MIN_DISTANCE
                push = min((need - dist) / 2.0, SEPARATION_STEP)
                ux = dx / dist
                uy = dy / dist
                pos[i] = clamp_to_frame(pos[i][0] + ux * push, pos[i][1] + uy * push)
                pos[j] = clamp_to_frame(pos[j][0] - ux * push, pos[j][1] - uy * push)
                moved = True
        if not moved:
            break
    return pos


def fit_to_frame(
    positions: list[tuple[float, float]], radii: list[float], margin: float = 2.0
) -> list[tuple[float, float]]:
    """Centraliza e escala o desenho até encostar na moldura.

    Semelhança pura: uma translação e UMA escala uniforme, a mesma para todo
    mundo. Nenhuma distância relativa muda de ordem, nenhum par troca de
    vizinho — o que a relaxação decidiu continua decidido. O que muda é só
    quanto do quadro o desenho ocupa, e o equilíbrio de molas não tem opinião
    sobre isso: ele é fixado pela constante da mola, não pelo tamanho do papel.

    Sem isto o grafo fica encolhido no meio de uma moldura vazia — que foi o
    que a primeira renderização mostrou.
    """
    if not positions:
        return []
    cx = sum(x for x, _ in positions) / len(positions)
    cy = sum(y for _, y in positions) / len(positions)
    reach = 0.0
    for (x, y), r in zip(positions, radii, strict=True):
        dx = x - cx
        dy = y - cy
        reach = max(reach, math.sqrt(dx * dx + dy * dy) + r)
    if reach <= 0.0:
        return [(CENTER_X, CENTER_Y) for _ in positions]
    scale = (FRAME_RADIUS - margin) / reach
    return [(CENTER_X + (x - cx) * scale, CENTER_Y + (y - cy) * scale) for x, y in positions]


def min_clearance(positions: list[tuple[float, float]], radii: list[float]) -> float:
    """Menor folga entre bordas de células. Negativa = sobreposição."""
    worst = float("inf")
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dx = positions[i][0] - positions[j][0]
            dy = positions[i][1] - positions[j][1]
            gap = math.sqrt(dx * dx + dy * dy) - radii[i] - radii[j]
            worst = min(worst, gap)
    return worst if worst != float("inf") else 0.0


def hatch_segment(
    ax: float, ay: float, bx: float, by: float, length: float = HATCH_LEN
) -> dict[str, float]:
    """Tique perpendicular no meio da aresta.

    O `--redline` nunca é só cor: quem não distingue vermelho precisa ver a
    marca. Regra do projeto, não gosto pessoal.
    """
    mx = (ax + bx) / 2.0
    my = (ay + by) / 2.0
    dx = bx - ax
    dy = by - ay
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < MIN_DISTANCE:
        dist = MIN_DISTANCE
    nx = -dy / dist
    ny = dx / dist
    half = length / 2.0
    return {
        "x1": round(mx - nx * half, 2),
        "y1": round(my - ny * half, 2),
        "x2": round(mx + nx * half, 2),
        "y2": round(my + ny * half, 2),
    }


# ── camada de I/O ────────────────────────────────────────────────────────────


def load_nodes(catalog_path: Path) -> list[Node]:
    """Personas na ORDEM DO CATÁLOGO — a mesma ordem do hero antigo e da lista."""
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    nodes: list[Node] = []
    for pack in data["packs"]:
        for persona in pack["personas"]:
            profile = persona["profile"]
            nodes.append(
                Node(
                    key=f"{pack['name']}/{persona['name']}",
                    pack=pack["name"],
                    persona=persona["name"],
                    display_name=persona["displayName"],
                    recruitment=int(profile["recruitment"]),
                    persistence=str(profile["persistence"]),
                )
            )
    if not nodes:
        raise SystemExit("ERRO(2): catálogo sem personas — falha de coleta, não grafo vazio")
    return nodes


def build_graph(packs_root: Path, catalog_path: Path) -> dict:
    nodes = load_nodes(catalog_path)
    bodies = load_catalog_bodies(packs_root)

    catalog_keys = {n.key for n in nodes}
    missing = sorted(catalog_keys - set(bodies))
    if missing:
        raise SystemExit(
            f"ERRO(2): {len(missing)} persona(s) do catálogo sem corpo em packs/: "
            f"{', '.join(missing[:3])}. Falha de coleta, não ausência de dado."
        )
    # O MANIFESTO é a autoridade sobre o que existe, não o glob do disco. Um
    # .persona.md ainda não listado no killerbee.yaml é rascunho: não aparece no
    # catálogo, logo não aparece no grafo — e não pode derrubar o build do site
    # (derrubava, com mensagem que culpava o catálogo).
    bodies = {key: body for key, body in bodies.items() if key in catalog_keys}

    # A MESMA função que produz a matriz do CATALOG-AUDIT, e não uma segunda
    # implementação. Isso não é preciosismo de DRY: C(xy) != C(yx) num
    # compressor real, então concatenar na ordem do catálogo em vez da ordem
    # canônica do audit dava OUTRO limiar e OUTRA contagem de arestas (medido:
    # 68 arestas sob 0,8369 contra as 71 sob 0,8376 que o audit publica). Duas
    # verdades nascendo — exatamente o que este projeto não pode ter na home.
    index_of = {n.key: i for i, n in enumerate(nodes)}
    pairs: list[tuple[int, int, float]] = [
        (index_of[a], index_of[b], ncd) for ncd, a, b in pairwise_ncd(bodies, zstd_size_bytes)
    ]

    values = [v for _, _, v in pairs]
    median, mad, threshold = robust_threshold(values)
    ncd_min = min(values)

    control_ncd: float | None = None
    for i, j, ncd in pairs:
        if {nodes[i].key, nodes[j].key} == set(CONTROL_PAIR):
            control_ncd = ncd
            break
    if control_ncd is not None and control_ncd >= threshold:
        # O controle saiu do desenho: ele não está abaixo do limiar, então
        # "mais parecido que o controle" deixaria de separar coisa alguma —
        # TODA aresta ficaria vermelha, e a amostra dele na chave teria
        # espessura negativa. Sem controle desenhável, sem redline.
        control_ncd = None

    drawn = sorted(
        ((i, j, ncd) for i, j, ncd in pairs if ncd < threshold),
        key=lambda t: (t[2], nodes[t[0]].key, nodes[t[1]].key),
    )

    radii = [radius_from_recruitment(n.recruitment) for n in nodes]
    weights = [
        (i, j, (threshold - ncd) / (threshold - ncd_min) if threshold > ncd_min else 1.0)
        for i, j, ncd in drawn
    ]
    positions = relax(initial_positions(len(nodes), [n.recruitment for n in nodes]), radii, weights)
    clearance = min_clearance(positions, radii)
    # Invariante FRACO garantido por construção; o alvo forte é relatado.
    hit_pad = min(HIT_PAD, max(0.0, clearance / 2.0))

    for node, (x, y), r in zip(nodes, positions, radii, strict=True):
        node.x = round(x, 2)
        node.y = round(y, 2)
        node.r = round(r, 2)

    for rank, (i, j, _) in enumerate(drawn):
        delay = EDGE_DELAY_BASE + EDGE_DELAY_STEP * rank
        for index in (i, j):
            current = nodes[index].delay_ms
            candidate = max(0, delay - CELL_LEAD)
            nodes[index].delay_ms = candidate if current is None else min(current, candidate)
        nodes[i].degree += 1
        nodes[j].degree += 1
        nodes[i].neighbours.append(nodes[j].display_name)
        nodes[j].neighbours.append(nodes[i].display_name)

    edges_out = []
    same_pack = 0
    redlined = 0
    for rank, (i, j, ncd) in enumerate(drawn):
        a, b = nodes[i], nodes[j]
        crosses = a.pack != b.pack
        same_pack += 0 if crosses else 1
        below_control = control_ncd is not None and ncd < control_ncd
        if below_control:
            redlined += 1
        kind = "redline" if below_control else ("cross" if crosses else "same")
        edges_out.append(
            {
                "ax": a.x,
                "ay": a.y,
                "bx": b.x,
                "by": b.y,
                "ncd": round(ncd, 4),
                "width": round(width_from_ncd(ncd, threshold, ncd_min), 2),
                "kind": kind,
                "delayMs": EDGE_DELAY_BASE + EDGE_DELAY_STEP * rank,
                # Vírgula decimal: é assim que a chave e a legenda imprimem,
                # dois centímetros abaixo.
                "title": f"{a.display_name} ~ {b.display_name} — NCD {ncd:.4f}".replace(
                    f"{ncd:.4f}", f"{ncd:.4f}".replace(".", ",")
                ),
                "hatch": hatch_segment(a.x, a.y, b.x, b.y) if below_control else None,
            }
        )

    nodes_out = []
    for node in nodes:
        shown = sorted(node.neighbours)[:4]
        if node.degree == 0:
            kin = "no measured kin in the catalog"
        elif node.degree <= len(shown):
            kin = f"{node.degree} measured kin: {', '.join(shown)}"
        else:
            # Dizer "8 measured kin" e listar 4 sem avisar é contagem que não
            # bate com a lista logo ao lado.
            kin = (
                f"{node.degree} measured kin, including "
                f"{', '.join(shown)} and {node.degree - len(shown)} more"
            )
        nodes_out.append(
            {
                "key": node.key,
                "pack": node.pack,
                "persona": node.persona,
                "displayName": node.display_name,
                "href": f"/personas/{node.pack}/{node.persona}/",
                "x": node.x,
                "y": node.y,
                "r": node.r,
                "d": hexagon_path(node.x, node.y, node.r),
                "hitR": round(node.r + hit_pad, 2),
                "strokeWidth": STROKE_BY_PERSISTENCE.get(node.persistence, 1.2),
                "degree": node.degree,
                "isolated": node.degree == 0,
                # Isolada NÃO anima: ela já estava lá e continua sem parente. O
                # estado final dela é verdadeiro desde o quadro zero.
                "delayMs": None if node.degree == 0 else node.delay_ms,
                # O nome acessível carrega a RELAÇÃO, não só a identidade.
                # `aria-label` num <a> suprime o <title> irmão: com o rótulo
                # curto, quem usa leitor de tela ouvia 48 vezes "Fulano in
                # pack" e nunca soube quem se liga a quem — que é o conteúdo
                # da figura. Agora as duas strings são a mesma frase.
                "ariaLabel": f"{node.display_name} in {node.pack} — {kin}",
                "title": f"{node.display_name} — {node.pack} — {kin}",
            }
        )

    # A chave é gerada CHAMANDO as mesmas funções que desenham o dado. Escala
    # desenhada por outra fórmula mentiria sobre o próprio gráfico.
    key_sizes = [
        {"recruitment": r, "r": round(radius_from_recruitment(r), 2), "d": hexagon_path(0, 0, 1)}
        for r in (1, 8, 32)
    ]
    key_ncds = (
        [threshold, control_ncd, ncd_min] if control_ncd is not None else [threshold, ncd_min]
    )
    key_widths = [
        {"ncd": round(v, 4), "width": round(width_from_ncd(v, threshold, ncd_min), 2)}
        for v in key_ncds
    ]

    return {
        "meta": {
            "personas": len(nodes),
            "pairs": len(pairs),
            "edges": len(drawn),
            "samePack": same_pack,
            "crossPack": len(drawn) - same_pack,
            "isolates": sum(1 for n in nodes if n.degree == 0),
            "threshold": round(threshold, 4),
            "median": round(median, 4),
            "mad": round(mad, 4),
            "ncdMin": round(ncd_min, 4),
            "control": None if control_ncd is None else round(control_ncd, 4),
            "redlined": redlined,
            "compressor": f"zstd-{ZSTD_LEVEL}",
            "viewBoxW": VIEWBOX_W,
            "viewBoxH": VIEWBOX_H,
            "plateY": PLATE_Y,
            "minClearance": round(clearance, 2),
            "hitPad": round(hit_pad, 2),
            # Largura RENDERIZADA (px CSS) a partir da qual até a MENOR célula
            # cumpre o alvo de 24 px do WCAG 2.5.8. Abaixo disso o CSS desliga o
            # ponteiro na figura inteira: alvo miúdo e colado erra de persona, e
            # errar de link é pior que não ter link — a lista do catálogo, na
            # mesma página, continua sendo o caminho.
            #
            # O número está espelhado numa @container em globals.css (CSS não lê
            # JSON) e um teste do site falha se os dois divergirem.
            "minInteractiveWidthPx": math.ceil(
                MIN_TOUCH_TARGET_PX * VIEWBOX_W / (2.0 * min(radii) + 2.0 * hit_pad)
            ),
            "lastBeatMs": (
                EDGE_DELAY_BASE + EDGE_DELAY_STEP * max(0, len(drawn) - 1) if drawn else 0
            ),
        },
        "nodes": nodes_out,
        "edges": edges_out,
        "key": {"sizes": key_sizes, "widths": key_widths},
    }


def main(argv: list[str] | None = None) -> int:
    # Windows com stdout em pipe cai para cp1252; acento e seta explodem o
    # processo e derrubam o build do site. Mesma classe de bug já paga no CLI.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = argv if argv is not None else sys.argv[1:]
    out_path = ROOT / "site" / "data" / "ncd-graph.json"
    if args:
        out_path = Path(args[0])
    graph = build_graph(ROOT / "packs", ROOT / "site" / "data" / "catalog.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = graph["meta"]
    print(
        f"grafo: {meta['personas']} nós · {meta['edges']}/{meta['pairs']} arestas "
        f"(limiar {meta['threshold']}) · {meta['isolates']} isoladas · "
        f"folga mínima {meta['minClearance']} → {out_path.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
