import Link from "next/link";
import { packs } from "@/app/lib/catalog";
import { HUB, danceTraces, tracePath, traceEnd, ringRadius } from "@/app/lib/dance";

/**
 * O hero: cada persona do catálogo plotada como um traço de dança.
 *
 * SVG server-rendered — sem JavaScript, sem canvas, sem biblioteca. Funciona com
 * JS desligado, é indexável, e cada traço é um link de verdade. A alternativa
 * (canvas animado) seria mais vistosa e diria menos.
 *
 * Estático de propósito — NÃO há animação (um doc-comment anterior descrevia
 * uma animação de stroke-dashoffset que nunca existiu; corrigido na auditoria
 * 2026-08-06). O desenho parado já carrega a informação inteira.
 *
 * Acessibilidade: o SVG NÃO usa role="img" — role img torna os descendentes
 * presentacionais, e aqui cada traço é um LINK que precisa ser exposto à
 * árvore de acessibilidade. O nome do conjunto vem do figcaption via
 * aria-labelledby no <figure>; o role="group" agrupa os links.
 */
export function WaggleField() {
  const traces = danceTraces(packs);
  if (traces.length === 0) return null;

  const size = 320;
  const center = size / 2;
  const radius = center - 34;

  // Rótulo por traço só cabe enquanto há poucos traços. Medido no navegador
  // com o catálogo de 51 personas: 50 PARES de rótulos sobrepostos — o gráfico
  // continuava correto e o texto virava sopa. Acima do limiar os nomes saem do
  // desenho e passam a viver no <title> de cada link (tooltip nativo), com o
  // aria-label intacto: some o rótulo, não a informação nem a acessibilidade.
  const LABEL_BUDGET = 14;
  const showLabels = traces.length <= LABEL_BUDGET;

  return (
    <figure className="waggle" aria-labelledby="waggle-caption">
      <svg
        viewBox={`0 0 ${size} ${size}`}
        className="waggle-svg"
        role="group"
        aria-label={`${traces.length} personas plotted as waggle-dance traces — each trace is a link`}
      >
        {/* Anéis de escala: 8, 16, 24 e 32 conversas paralelas.
            A faixa é impressa ANTES do dado — sem ela o comprimento do traço é
            um comprimento, não uma grandeza.

            O raio usa exatamente a mesma função que o traço
            (`lengthFromRecruitment`), senão a escala mentiria sobre o próprio
            desenho — que é o pecado que este site inteiro existe para não
            cometer. */}
        {[8, 16, 24, 32].map((mark) => (
          <circle
            key={mark}
            cx={center}
            cy={center}
            r={ringRadius(mark, radius)}
            className="waggle-ring"
          />
        ))}

        <circle cx={center} cy={center} r={radius * HUB} className="waggle-hub" />

        {traces.map((trace) => (
          <g key={`${trace.packName}/${trace.personaName}`} className="waggle-trace">
            <Link href={trace.href} aria-label={`${trace.displayName} in ${trace.packName}`}>
              <title>{`${trace.displayName} — ${trace.packName}`}</title>
              {/* Alvo de toque generoso e invisível, por cima do traço fino. */}
              <path
                d={tracePath(trace, center, center, radius)}
                className="waggle-hit"
                strokeWidth={16}
              />
              <path
                d={tracePath(trace, center, center, radius)}
                className="waggle-line"
                strokeWidth={trace.weight}
              />
              {showLabels ? (
                <text
                  {...(() => {
                    const end = traceEnd(trace, center, center, radius);
                    return { x: end.x, y: end.y, textAnchor: end.anchor };
                  })()}
                  className="waggle-label"
                  dominantBaseline="middle"
                >
                  {trace.displayName}
                </text>
              ) : null}
            </Link>
          </g>
        ))}
      </svg>

      <figcaption id="waggle-caption" className="waggle-caption">
        <p>
          Every persona in the catalog, plotted the way a forager reports a find. Angle
          separates personas; <strong>length is recruitment</strong> — how many conversations
          the agent holds at once, 1 to 32. <strong>Thickness is persistence</strong>, how long
          it keeps at a task. <strong>Waggle count is threshold</strong>, how little it takes to
          get a response.
        </p>
        <p className="waggle-note">
          Every value is a real field from the pack manifest. None of it is decoration.
          {showLabels ? null : ` At ${traces.length} personas the names no longer fit on the
          drawing — hover a trace, or open a pack below.`}
        </p>
      </figcaption>
    </figure>
  );
}
