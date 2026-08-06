"""A assinatura de dança rasterizada — o corpo visível dos .agent.png/.team.png.

O card de snapshot no chat do Buzz usa o PRÓPRIO arquivo como thumbnail, e o
nosso corpo era 1x1 transparente (achado de baixa prioridade da auditoria
2026-08-06): o instalável não se explicava. Este módulo desenha, em Python
puro (zlib/struct/bytes — sem Pillow), o sistema de coordenadas polares da
dança da abelha:

- **ângulo**      = posição no campo, distribuída no círculo com meio passo
- **comprimento** = ``0.28 + 0.72·√(recruitment normalizado 1..=32)``
- **espessura**   = persistence (short 1.4 · medium 2.4 · long 3.6)
- **requebrado**  = threshold (high 2 · medium 4 · low 7 zigue-zagues)
- taper ``sin(πt)`` nas pontas; amplitude fixa (a informação está na CONTAGEM)
- hub em 0.18 do raio; anéis de escala em recruitment 8/16/24/32

**Este módulo passou a ser a única implementação da dança** em 2026-08-06:
o site trocou o hero radial pelo grafo de similaridade (D-037) e o
``site/app/lib/dance.ts``, que era o espelho em TypeScript, ficou órfão e foi
removido. Módulo sem chamador com três doc-comments apontando para ele é
exatamente o apodrecimento que este projeto combate. A tabela de constantes
continua travada por golden em test_signature; o que sumiu foi a cópia, não a
verificação. Documentado em D-030 e D-037.

A dança não saiu do produto: ela é o corpo de cada .agent.png/.team.png, que é
o thumbnail que o card de snapshot do chat do Buzz exibe.

Consequência no import (leitura de fonte, segundo leitor conferiu): quando o
manifesto não traz avatar inline — nosso caso — o corpo do PNG é ADOTADO
como avatar do agente importado (import.rs:242-261). Os limites dessa adoção
(snapshot_avatar.rs:5-7) são MENORES que o cap de import: lado > 2048 px
FALHA o import; > 2 MiB não vira avatar. 512 px passa com folga e o teste
trava os dois tetos. Ver no app rodando continua pendente (D-017).

Determinismo multiplataforma: sin/cos são polinômios próprios (Taylor com
redução de argumento) — só +, -, *, / e math.sqrt, todas operações IEEE-754 com
arredondamento correto em qualquer plataforma. libm (math.sin) varia por
sistema no último bit, e um bit diferente mudaria o sha256 publicado. O
golden test trava o hash do RASTER CRU; o PNG passa por zlib, cuja saída é
estável na prática mas não é contrato — por isso o golden é do raster.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import pairwise

from .model import ScutellataProfile

# ── As constantes que carregam informação — travadas por golden em test_signature ──
HUB = 0.18
PERSISTENCE_WEIGHT = {"short": 1.4, "medium": 2.4, "long": 3.6}
THRESHOLD_WAGGLES = {"high": 2, "medium": 4, "low": 7}
RECRUITMENT_MIN = 1
RECRUITMENT_MAX = 32
AMPLITUDE = 3.2
SCALE_RING_MARKS = (8, 16, 24, 32)

# ── Geometria do WaggleField (viewBox 320, raio = centro - 34) ───────────────
_VIEWBOX = 320.0
_RADIUS_MARGIN = 34.0

# ── Cores (globals.css, tema escuro — o chat do Buzz é escuro) ───────────────
_COLOR_TRACE = (0xC0, 0x8A, 0x33)  # --burn (dark)
_COLOR_GRID = (0x43, 0x60, 0x5F)  # --grid (light — neutro que lê nos dois)
_ALPHA_RING = 0.22  # --grid-faint = grid a 22%
_ALPHA_HUB = 0.75
_STROKE_RING = 0.6
_STROKE_HUB = 1.0

_TWO_PI = 2.0 * math.pi


def _sin(x: float) -> float:
    """Seno determinístico: redução para [-pi/2, pi/2] + Taylor até x¹³.

    Erro < 1e-7 no intervalo reduzido — invisível a 1/255 de alpha — e só
    usa aritmética IEEE básica, idêntica em qualquer plataforma (libm não é).
    """
    x = x - _TWO_PI * math.floor((x + math.pi) / _TWO_PI)
    if x > math.pi / 2.0:
        x = math.pi - x
    elif x < -math.pi / 2.0:
        x = -math.pi - x
    x2 = x * x
    # Horner sobre 1/3!… 1/15! — coeficientes exatos em float.
    return x * (
        1.0
        + x2
        * (
            -1.0 / 6.0
            + x2
            * (
                1.0 / 120.0
                + x2
                * (
                    -1.0 / 5040.0
                    + x2 * (1.0 / 362880.0 + x2 * (-1.0 / 39916800.0 + x2 * (1.0 / 6227020800.0)))
                )
            )
        )
    )


def _cos(x: float) -> float:
    return _sin(x + math.pi / 2.0)


def length_from_recruitment(recruitment: int) -> float:
    """Comprimento do traço a partir de recruitment (1..=32).

    Também é a curva de tamanho das células do hero (scripts/ncd_graph.py a
    importa daqui em vez de recopiá-la).
    """
    clamped = min(max(recruitment, RECRUITMENT_MIN), RECRUITMENT_MAX)
    normalized = (clamped - RECRUITMENT_MIN) / (RECRUITMENT_MAX - RECRUITMENT_MIN)
    return 0.28 + 0.72 * math.sqrt(normalized)


def trace_polyline(
    profile: ScutellataProfile,
    angle_deg: float,
    cx: float,
    cy: float,
    radius: float,
    amplitude: float = AMPLITUDE,
) -> list[tuple[float, float]]:
    """Os pontos do traço: a reta radial com o requebrado sobreposto."""
    radians = (angle_deg - 90.0) * math.pi / 180.0
    dir_x = _cos(radians)
    dir_y = _sin(radians)
    normal_x = -dir_y
    normal_y = dir_x

    inner = radius * HUB
    outer = inner + (radius - inner) * length_from_recruitment(profile.recruitment)
    waggles = THRESHOLD_WAGGLES.get(profile.threshold, 4)

    points: list[tuple[float, float]] = []
    segments = waggles * 2
    for i in range(segments + 1):
        t = i / segments
        r = inner + (outer - inner) * t
        taper = _sin(math.pi * t)
        offset = (1.0 if i % 2 == 0 else -1.0) * amplitude * taper
        points.append((cx + dir_x * r + normal_x * offset, cy + dir_y * r + normal_y * offset))
    return points


class _Layer:
    """Cobertura em alpha de uma cor só; blend por máximo (traço uniforme)."""

    def __init__(self, size: int) -> None:
        self.size = size
        self.alpha = [0.0] * (size * size)

    def stamp(self, x: float, y: float, half_width: float) -> None:
        r_out = half_width + 0.5
        px_min = max(0, int(x - r_out - 1.0))
        px_max = min(self.size - 1, int(x + r_out + 1.0))
        py_min = max(0, int(y - r_out - 1.0))
        py_max = min(self.size - 1, int(y + r_out + 1.0))
        for py in range(py_min, py_max + 1):
            row = py * self.size
            dy = py + 0.5 - y
            for px in range(px_min, px_max + 1):
                dx = px + 0.5 - x
                distance = math.sqrt(dx * dx + dy * dy)
                coverage = half_width + 0.5 - distance
                if coverage <= 0.0:
                    continue
                if coverage > 1.0:
                    coverage = 1.0
                index = row + px
                if coverage > self.alpha[index]:
                    self.alpha[index] = coverage

    def stroke(self, points: Sequence[tuple[float, float]], width: float) -> None:
        """Carimbos anti-serrilhados ao longo da polilinha; linecap redondo."""
        half = width / 2.0
        step = 0.35
        for (x0, y0), (x1, y1) in pairwise(points):
            seg_dx = x1 - x0
            seg_dy = y1 - y0
            seg_len = math.sqrt(seg_dx * seg_dx + seg_dy * seg_dy)
            stamps = max(1, int(seg_len / step))
            for i in range(stamps + 1):
                t = i / stamps
                self.stamp(x0 + seg_dx * t, y0 + seg_dy * t, half)

    def circle(self, cx: float, cy: float, radius: float, width: float) -> None:
        """Anel: carimbos ao longo da circunferência."""
        half = width / 2.0
        step = 0.35
        stamps = max(8, int(_TWO_PI * radius / step))
        for i in range(stamps + 1):
            angle = _TWO_PI * i / stamps
            self.stamp(cx + radius * _cos(angle), cy + radius * _sin(angle), half)


def field_raster(
    profiles: Sequence[ScutellataProfile],
    draw_indices: Sequence[int] | None = None,
    size: int = 512,
) -> bytes:
    """O campo de dança como RGBA flat (size*size*4 bytes), fundo transparente.

    ``profiles`` define o CÍRCULO (todos ganham ângulo, como no site);
    ``draw_indices`` escolhe quais traços aparecem — ``None`` = todos. Um
    .agent.png desenha só o traço da sua persona, com o ângulo que ela tem no
    campo do pack; um .team.png desenha todos os membros. Anéis de escala e
    hub aparecem sempre: sem a escala, comprimento é só comprimento.
    """
    if not profiles:
        raise ValueError("campo sem personas — não há o que desenhar")
    if draw_indices is None:
        draw_indices = range(len(profiles))

    scale = size / _VIEWBOX
    center = size / 2.0
    radius = (size / 2.0) - _RADIUS_MARGIN * scale

    rings = _Layer(size)
    hub = _Layer(size)
    traces = _Layer(size)

    inner = radius * HUB
    for mark in SCALE_RING_MARKS:
        ring_r = inner + (radius - inner) * length_from_recruitment(mark)
        rings.circle(center, center, ring_r, _STROKE_RING * scale)
    hub.circle(center, center, inner, _STROKE_HUB * scale)

    step_deg = 360.0 / len(profiles)
    for index in draw_indices:
        profile = profiles[index]
        angle = index * step_deg + step_deg / 2.0
        weight = PERSISTENCE_WEIGHT.get(profile.persistence, 2.4)
        points = trace_polyline(profile, angle, center, center, radius, AMPLITUDE * scale)
        traces.stroke(points, weight * scale)

    # Composição "over" de baixo para cima: anéis → hub → traços.
    out = bytearray(size * size * 4)
    layers = (
        (rings, _COLOR_GRID, _ALPHA_RING),
        (hub, _COLOR_GRID, _ALPHA_HUB),
        (traces, _COLOR_TRACE, 1.0),
    )
    for layer, (red, green, blue), layer_alpha in layers:
        alpha = layer.alpha
        for index in range(size * size):
            source_a = alpha[index] * layer_alpha
            if source_a <= 0.0:
                continue
            base = index * 4
            dest_a = out[base + 3] / 255.0
            out_a = source_a + dest_a * (1.0 - source_a)
            if out_a <= 0.0:
                continue
            for channel, value in enumerate((red, green, blue)):
                dest_c = out[base + channel]
                out[base + channel] = round(
                    (value * source_a + dest_c * dest_a * (1.0 - source_a)) / out_a
                )
            out[base + 3] = round(out_a * 255.0)
    return bytes(out)
