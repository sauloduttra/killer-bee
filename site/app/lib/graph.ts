/**
 * O grafo de similaridade do catálogo, lido em tempo de build.
 *
 * Gerado por `uv run python scripts/ncd_graph.py` (chamado pelo
 * prepare-data.mjs depois do catálogo): distância de compressão normalizada
 * entre os corpos de prompt, aresta onde o par mede abaixo do limiar robusto
 * que o CATALOG-AUDIT publica — a MESMA função de limiar, não uma segunda.
 *
 * **Toda a geometria já vem pronta do gerador.** Coordenada, raio, caminho do
 * hexágono, espessura, atraso: nada é calculado aqui. Isso não é preguiça de
 * runtime, é regra de uma verdade só — fórmula duplicada em duas linguagens
 * diverge no dia em que alguém corrige uma delas, e a escala impressa passaria
 * a mentir sobre o próprio desenho. Este módulo só dá tipo ao JSON.
 */
import graphJson from "@/data/ncd-graph.json";

export interface GraphMeta {
  personas: number;
  pairs: number;
  edges: number;
  samePack: number;
  crossPack: number;
  isolates: number;
  /** Limiar robusto: mediana menos 3 MADs sobre todos os pares. */
  threshold: number;
  median: number;
  mad: number;
  ncdMin: number;
  /** O par escrito à mão para ser máximo em diferença. `null` se o pack sair. */
  control: number | null;
  /** Arestas medidas ABAIXO do par-controle — defeito conhecido, impresso. */
  redlined: number;
  compressor: string;
  viewBoxW: number;
  viewBoxH: number;
  /** Topo da faixa de escala, em unidades do viewBox. */
  plateY: number;
  minClearance: number;
  hitPad: number;
  /** Largura de figura (px CSS) a partir da qual a MENOR célula cumpre 24 px.
   *  Espelhado na `@container` de globals.css; teste do site pina os dois. */
  minInteractiveWidthPx: number;
  lastBeatMs: number;
}

export interface GraphNode {
  key: string;
  pack: string;
  persona: string;
  displayName: string;
  href: string;
  x: number;
  y: number;
  r: number;
  /** Caminho do hexágono, já fechado, em unidades do viewBox. */
  d: string;
  hitR: number;
  strokeWidth: number;
  degree: number;
  isolated: boolean;
  /** `null` para isolada: ela não anima, porque já estava lá sem parente. */
  delayMs: number | null;
  ariaLabel: string;
  title: string;
}

export type EdgeKind = "same" | "cross" | "redline";

export interface GraphEdge {
  ax: number;
  ay: number;
  bx: number;
  by: number;
  ncd: number;
  width: number;
  kind: EdgeKind;
  delayMs: number;
  title: string;
  /** Tique perpendicular: `--redline` nunca é só cor. */
  hatch: { x1: number; y1: number; x2: number; y2: number } | null;
}

export interface GraphKey {
  sizes: { recruitment: number; r: number; d: string }[];
  widths: { ncd: number; width: number }[];
}

export interface CatalogGraph {
  meta: GraphMeta;
  nodes: GraphNode[];
  edges: GraphEdge[];
  key: GraphKey;
}

export const graph = graphJson as CatalogGraph;

/** Formata NCD com vírgula decimal e 4 casas, como o CATALOG-AUDIT imprime. */
export function formatNcd(value: number): string {
  return value.toFixed(4).replace(".", ",");
}
