/**
 * A waggle dance como projeção de dados — a signature do site.
 *
 * A dança da abelha codifica duas grandezas: **direção**, pelo ângulo em relação
 * ao sol, e **distância**, pela duração do trecho de requebrado. Isso é um sistema
 * de coordenadas polares feito por inseto, não metáfora.
 *
 * Aqui cada persona vira um traço:
 *
 * - **ângulo** = posição da persona na ordem do catálogo, distribuída no círculo.
 *   Personas do mesmo pack ficam adjacentes — o pack vira um setor legível.
 * - **comprimento** = `recruitment`, o paralelismo nativo (1..=32). É quantas
 *   conversas a persona sustenta ao mesmo tempo, ou seja, literalmente quanto
 *   enxame ela recruta.
 * - **espessura** = `persistence`, quanto tempo ela insiste antes de desistir.
 * - **densidade do requebrado** = `threshold`, quão baixo é o limiar de resposta.
 *
 * **Todo valor sai de campo real do manifesto.** Nenhum é decorativo, nenhum é
 * aleatório. Se um dia a signature precisar de um dado que não existe, ela está
 * errada e some — é a regra do projeto para metáfora biológica.
 *
 * Puro: recebe personas, devolve geometria. Sem DOM, sem relógio, sem random —
 * o mesmo catálogo gera sempre o mesmo desenho, o que também o torna testável.
 */
import type { Pack, Persona } from "./catalog";

export interface DanceTrace {
  packName: string;
  personaName: string;
  displayName: string;
  /** Graus, 0 = topo, sentido horário. */
  angleDeg: number;
  /** 0..1 — fração do raio disponível. */
  length: number;
  /** 1..4 — largura do traço. */
  weight: number;
  /** Número de zigue-zagues do requebrado. */
  waggles: number;
  href: string;
}

const PERSISTENCE_WEIGHT: Record<string, number> = { short: 1.4, medium: 2.4, long: 3.6 };
const THRESHOLD_WAGGLES: Record<string, number> = { high: 2, medium: 4, low: 7 };

/** Faixa nativa de paralelismo no Buzz — `types.rs:812`. */
const RECRUITMENT_MIN = 1;
const RECRUITMENT_MAX = 32;

/** Raio interno do disco central, em fração do raio total. */
const HUB = 0.18;

/**
 * Raio do anel de escala para um valor de `recruitment`.
 *
 * Usa a MESMA função de comprimento que o traço. Se a escala fosse desenhada
 * por outra fórmula — ou por uma aproximação — ela mentiria sobre o próprio
 * gráfico, que é exatamente o defeito que este site existe para não ter.
 */
export function ringRadius(recruitment: number, radius: number): number {
  const inner = radius * HUB;
  return inner + (radius - inner) * lengthFromRecruitment(recruitment);
}

function lengthFromRecruitment(recruitment: number): number {
  const clamped = Math.min(Math.max(recruitment, RECRUITMENT_MIN), RECRUITMENT_MAX);
  // Raiz quadrada porque a diferença entre 1 e 4 importa muito mais que entre 28
  // e 32 — a percepção de comprimento é comprimida, e a escala linear
  // desperdiçaria o traço todo nos valores altos, que são raros.
  const normalized = (clamped - RECRUITMENT_MIN) / (RECRUITMENT_MAX - RECRUITMENT_MIN);
  return 0.28 + 0.72 * Math.sqrt(normalized);
}

// O href é consumido por next/link no WaggleField, que já aplica o basePath do
// deploy — um parâmetro basePath aqui era peso morto que nenhum chamador
// passava (auditoria 2026-08-06).
export function danceTraces(packs: Pack[]): DanceTrace[] {
  const flat: { pack: Pack; persona: Persona }[] = packs.flatMap((pack) =>
    pack.personas.map((persona) => ({ pack, persona })),
  );
  if (flat.length === 0) return [];

  // Um golpe de sorte do assunto: a distribuição no círculo com um deslocamento
  // de meio passo evita que um traço aponte exatamente para cima, o que leria
  // como "norte" e sugeriria uma hierarquia que não existe.
  const step = 360 / flat.length;
  return flat.map(({ pack, persona }, index) => ({
    packName: pack.name,
    personaName: persona.name,
    displayName: persona.displayName,
    angleDeg: index * step + step / 2,
    length: lengthFromRecruitment(persona.profile.recruitment),
    weight: PERSISTENCE_WEIGHT[persona.profile.persistence] ?? 2.4,
    waggles: THRESHOLD_WAGGLES[persona.profile.threshold] ?? 4,
    href: `/personas/${pack.name}/${persona.name}/`,
  }));
}

/**
 * Caminho SVG de um traço: a reta radial com o requebrado sobreposto.
 *
 * `cx`/`cy`/`radius` em unidades do viewBox. O zigue-zague é perpendicular à
 * direção do traço, com amplitude fixa — a informação está na CONTAGEM de
 * zigue-zagues, não no tamanho deles.
 */
export function tracePath(
  trace: DanceTrace,
  cx: number,
  cy: number,
  radius: number,
  amplitude = 3.2,
): string {
  const radians = ((trace.angleDeg - 90) * Math.PI) / 180;
  const dirX = Math.cos(radians);
  const dirY = Math.sin(radians);
  // Normal unitária, para deslocar o zigue-zague perpendicularmente.
  const normalX = -dirY;
  const normalY = dirX;

  const innerRadius = radius * HUB;
  const outerRadius = innerRadius + (radius - innerRadius) * trace.length;

  const points: string[] = [];
  const segments = trace.waggles * 2;
  for (let i = 0; i <= segments; i += 1) {
    const t = i / segments;
    const r = innerRadius + (outerRadius - innerRadius) * t;
    // Amplitude vai a zero nas pontas: o traço nasce e morre na linha radial,
    // senão as extremidades ficam soltas e o desenho perde a direção.
    const taper = Math.sin(Math.PI * t);
    const offset = (i % 2 === 0 ? 1 : -1) * amplitude * taper;
    const x = cx + dirX * r + normalX * offset;
    const y = cy + dirY * r + normalY * offset;
    points.push(`${i === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`);
  }
  return points.join(" ");
}

/** Ponta do traço, onde vai o rótulo. */
export function traceEnd(
  trace: DanceTrace,
  cx: number,
  cy: number,
  radius: number,
): { x: number; y: number; anchor: "start" | "end" | "middle" } {
  const radians = ((trace.angleDeg - 90) * Math.PI) / 180;
  const innerRadius = radius * HUB;
  const r = innerRadius + (radius - innerRadius) * trace.length + 9;
  const x = cx + Math.cos(radians) * r;
  const y = cy + Math.sin(radians) * r;
  const normalizedAngle = ((trace.angleDeg % 360) + 360) % 360;
  const anchor =
    normalizedAngle < 12 || normalizedAngle > 348 || Math.abs(normalizedAngle - 180) < 12
      ? "middle"
      : normalizedAngle < 180
        ? "start"
        : "end";
  return { x, y, anchor };
}
