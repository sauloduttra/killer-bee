import Link from "next/link";
import { formatNcd, graph } from "@/app/lib/graph";

/**
 * O hero: o catálogo se ligando a si mesmo.
 *
 * Cada célula é uma persona e é um link. Cada linha é um par cuja distância de
 * compressão normalizada (NCD) mediu abaixo do limiar robusto publicado no
 * CATALOG-AUDIT. **A rede não é ilustração de rede** — é o grafo de
 * similaridade do próprio catálogo, e quem o desenhou foi a medição:
 *
 * - posição: relaxação de molas sobre as arestas MEDIDAS, partindo das posições
 *   exatas do hero antigo (a dança solta do eixo). Os lobos que aparecem são os
 *   packs se reconhecendo, o que é exatamente o que a auditoria mediu — 55 das
 *   71 arestas ficam dentro de um pack. **A posição em si não mede nada**, e a
 *   legenda diz isso;
 * - célula: tamanho é `recruitment` (paralelismo nativo, 1..32), espessura da
 *   borda é `persistence`. Não desenhamos `threshold` nem `propagation`: os dois
 *   são quase constantes neste catálogo, e canal que não varia é decoração;
 * - linha: existe se NCD < limiar, e engrossa conforme mede ABAIXO dele;
 * - célula sem linha: persona sem parente medido. **Ausência é informação** —
 *   são as onze mais distintas do catálogo, e elas ficam sozinhas de propósito;
 * - vermelho: par medido mais próximo que `adversary~guard`, as duas personas
 *   escritas à mão para serem máximas em diferença. O site imprime na home o
 *   seu próprio defeito conhecido, com o número da decisão que o aceitou.
 *
 * Nada é calculado aqui: o gerador em Python entrega coordenada, caminho,
 * espessura e atraso prontos. Uma fórmula, um lugar.
 *
 * SVG server-rendered — sem JavaScript, sem canvas, sem biblioteca. Funciona
 * com JS desligado, é indexável, e cada célula é um link de verdade.
 *
 * Acessibilidade: o SVG NÃO usa role="img" — role img torna os descendentes
 * presentacionais, e aqui cada célula é um LINK que precisa existir na árvore
 * de acessibilidade. As arestas são aria-hidden, e por isso o nome acessível
 * de cada célula CARREGA a relação ("5 measured kin, including …"): um
 * `aria-label` num `<a>` suprime o `<title>` irmão, então um rótulo curto
 * deixaria quem usa leitor de tela sem o conteúdo da figura.
 *
 * Alvo de toque, resolvido em duas frentes (o desenho declarava cumprir 24 px
 * e não cumpria — a revisão adversarial mediu 22,3 px nas seis células de
 * `recruitment` 1):
 *
 * 1. **Onde cabe, o alvo cresce.** O padding subiu de 3,5 para 6,5, o que leva
 *    a menor célula a 27,7 px num laptop de 1280. O layout aceitou a folga extra
 *    sem perder os aglomerados.
 * 2. **Onde não cabe, o ponteiro desliga.** Abaixo de 388 px de figura — número
 *    calculado pelo gerador, não estimado — uma `@container` remove
 *    `pointer-events` das células. Alvo miúdo e colado não é difícil de
 *    acertar: é acertar a persona errada, e abrir a página errada é pior que
 *    não abrir nenhuma. A lista do catálogo, na mesma página, é o caminho —
 *    que é a exceção de controle equivalente do próprio critério. O teclado
 *    continua alcançando as células, porque quem navega por teclado não erra
 *    por precisão de dedo.
 *
 * Animação: a ordem é a única coisa que o tempo codifica — as arestas se
 * ligam do par mais próximo ao mais distante, que é a ordem em que o
 * CATALOG-AUDIT lista o fundo do ranking. Duração é constante e não codifica
 * nada. O estado FINAL é o que está no atributo; o CSS só subtrai no começo.
 * Sem CSS, sem animação ou com `prefers-reduced-motion`, o desenho servido já
 * é o desenho pronto.
 */
export function NcdField() {
  const { meta, nodes, edges, key } = graph;
  if (nodes.length === 0) return null;

  const plateY = meta.plateY;

  return (
    <figure className="ncd" aria-labelledby="ncd-caption">
      <svg
        viewBox={`0 0 ${meta.viewBoxW} ${meta.viewBoxH}`}
        className="ncd-svg"
        role="group"
        aria-label={`${meta.personas} personas as cells and ${meta.edges} measured similarity links — each cell is a link to that persona`}
      >
        {/* As arestas primeiro, para nenhuma linha passar por cima de uma
            célula: a célula é o objeto clicável, a linha é a medição. */}
        <g className="ncd-wires" aria-hidden="true">
          {edges.map((edge) => (
            <g key={`${edge.ax},${edge.ay}-${edge.bx},${edge.by}`}>
              <line
                x1={edge.ax}
                y1={edge.ay}
                x2={edge.bx}
                y2={edge.by}
                className={`ncd-edge ncd-edge-${edge.kind}`}
                strokeWidth={edge.width}
                pathLength="1"
                style={{ animationDelay: `${edge.delayMs}ms` }}
              >
                <title>{edge.title}</title>
              </line>
              {edge.hatch ? (
                <line
                  x1={edge.hatch.x1}
                  y1={edge.hatch.y1}
                  x2={edge.hatch.x2}
                  y2={edge.hatch.y2}
                  className="ncd-hatch"
                  pathLength="1"
                  style={{ animationDelay: `${edge.delayMs}ms` }}
                />
              ) : null}
            </g>
          ))}
        </g>

        <g className="ncd-cells">
          {nodes.map((node) => (
            <g
              key={node.key}
              className={node.isolated ? "ncd-node ncd-node-alone" : "ncd-node"}
            >
              <Link href={node.href} aria-label={node.ariaLabel}>
                <title>{node.title}</title>
                {/* Alvo de toque generoso e invisível. O passe de separação do
                    gerador garante que dois alvos nunca se sobrepõem. */}
                <circle cx={node.x} cy={node.y} r={node.hitR} className="ncd-hit" />
                <path
                  d={node.d}
                  className="ncd-cell"
                  strokeWidth={node.strokeWidth}
                  {...(node.delayMs === null
                    ? {}
                    : { style: { animationDelay: `${node.delayMs}ms` } })}
                />
              </Link>
            </g>
          ))}
        </g>

        {/* A faixa: escala impressa ANTES do dado, gerada CHAMANDO as mesmas
            funções que desenham o dado. Escala aproximada mentiria sobre o
            próprio gráfico — que é o pecado que este site existe para não
            cometer. */}
        <g className="ncd-plate" aria-hidden="true">
          <line x1={26} y1={plateY} x2={294} y2={plateY} className="ncd-rule" />

          {/* Linha 1 — o tamanho da célula. As três amostras saem da mesma
              função que dimensiona os nós, escaladas a partir do hexágono
              unitário que o gerador emitiu. */}
          {key.sizes.map((sample, index) => (
            <path
              key={sample.recruitment}
              d={sample.d}
              className="ncd-key-cell"
              transform={`translate(${32 + index * 19}, ${plateY + 17}) scale(${sample.r})`}
              strokeWidth={1.2 / sample.r}
            />
          ))}
          <text x={92} y={plateY + 20} className="ncd-key-label">
            recruitment 1 · 8 · 32
          </text>

          {/* Linha 2 — a espessura da aresta, amostrada nos três valores que o
              desenho de fato contém: o limiar, o par-controle e o mínimo. */}
          {key.widths.map((sample, index) => (
            <line
              key={sample.ncd}
              x1={26 + index * 24}
              y1={plateY + 36}
              x2={44 + index * 24}
              y2={plateY + 36}
              className="ncd-key-wire"
              strokeWidth={sample.width}
            />
          ))}
          <text x={104} y={plateY + 39} className="ncd-key-label">
            NCD {key.widths.map((sample) => formatNcd(sample.ncd)).join(" · ")}
          </text>

          {/* O defeito conhecido, impresso na home com o número da decisão que
              o aceitou. A contagem vive no figcaption; aqui fica só o que
              anota uma marca específica do desenho. */}
          {meta.redlined > 0 && meta.control !== null ? (
            <text x={26} y={plateY + 56} className="ncd-stamp ncd-stamp-redline">
              {meta.redlined} {meta.redlined === 1 ? "pair" : "pairs"} below the{" "}
              {formatNcd(meta.control)} control — kept (D-036)
            </text>
          ) : null}
        </g>
      </svg>

      <figcaption id="ncd-caption" className="ncd-caption">
        <p>
          All {meta.personas} personas in the catalog, wired to the ones they measurably
          resemble. Each line is a <strong>Normalized Compression Distance</strong> between
          two prompt bodies, {meta.compressor}: {meta.pairs} pairs measured,{" "}
          <strong>
            {meta.edges} below the published threshold {formatNcd(meta.threshold)}
          </strong>{" "}
          (median minus three MADs). Thicker means closer. {meta.samePack} stay inside a
          pack, {meta.crossPack} cross one, {meta.isolates} have no measured kin at all —
          those are the most distinctive prompts here, and they stand alone on purpose.
        </p>
        {meta.redlined > 0 && meta.control !== null ? (
          <p className="ncd-alert">
            {/* A faixa carrega este mesmo aviso, mas ela é aria-hidden e sai a
                7,8 px num telefone. Um site que existe para não esconder
                defeito não pode esconder o próprio numa tipografia miúda
                dentro de markup invisível ao leitor de tela. */}
            <strong>Known defect, printed here on purpose:</strong> {meta.redlined}{" "}
            {meta.redlined === 1 ? "pair measures" : "pairs measure"} closer than{" "}
            {formatNcd(meta.control)} — the distance between the two personas we wrote by
            hand to be maximally different. A generated pair below that line is more alike
            than two colleagues designed to disagree. Kept, with the number, under D-036.
          </p>
        ) : null}
        {/* Só aparece quando a figura é estreita demais para o alvo de 24 px —
            a mesma @container que desliga o ponteiro. Sem JS, e sem afirmar
            "no celular", que seria falso numa janela estreita de desktop. */}
        <p className="ncd-touch-note">
          This drawing is too small here for reliable tapping, so the cells are not
          tappable at this width — mis-hitting a neighbour would open the wrong persona.
          Use the catalog below; every persona is there. (Keyboard still reaches them.)
        </p>
        <p className="ncd-note">
          Cell size is recruitment; border weight is persistence. Amber lines stay inside a
          pack, paler ones cross packs. The layout relaxes from the old waggle field over
          the measured links, so position itself measures nothing — only who is joined to
          whom does. Method and full matrix:{" "}
          <a href="https://github.com/sauloduttra/killer-bee/blob/main/docs/CATALOG-AUDIT.md">
            CATALOG-AUDIT
          </a>
          . Cilibrasi &amp; Vitányi, 2005.
        </p>
      </figcaption>
    </figure>
  );
}
