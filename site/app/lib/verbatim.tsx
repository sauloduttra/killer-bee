/**
 * Renderizador **verbatim** do system prompt.
 *
 * A diferença em relação a um conversor de markdown é a tese inteira do site:
 * **nenhum caractere é apagado — só a tinta muda.** O `##` de um heading continua
 * na tela, em tinta apagada, enquanto a palavra ganha peso. As crases continuam
 * lá. O hífen da lista continua lá.
 *
 * Um conversor normal mostraria "Role" onde a fonte diz "## Role". Numa página
 * cujo produto é *o prompt exatamente como o agente o recebe*, apagar dois
 * caracteres já é uma pequena mentira — e a primeira versão deste arquivo fazia
 * isso.
 *
 * Consequências de desenho que caem de graça:
 *
 * - **A estrutura de linha é preservada.** Os `.persona.md` do repositório vêm
 *   hard-wrapped em 78–79 colunas; reflow mudaria o que a pessoa vê em relação ao
 *   que o agente recebe.
 * - **Cada linha é citável por URL** (`#L12`), o que torna possível discutir um
 *   prompt linha a linha num PR ou numa issue.
 * - **Não há caminho para HTML cru.** O conteúdo vem de pull request de terceiro;
 *   este renderizador só emite texto e elementos de uma lista fechada, então um
 *   `<script>` no prompt aparece como as letras `<script>`.
 *
 * Puro: recebe string, devolve nós.
 */
import type { ReactNode } from "react";

/** Classe da linha, usada só para tingir — não altera o conteúdo. */
export type LineKind = "heading" | "list" | "quote" | "fence" | "code" | "rule" | "text" | "blank";

export interface ClassifiedLine {
  text: string;
  kind: LineKind;
  /** Nível 1..6, só para heading. */
  level?: number;
}

/**
 * Classifica cada linha. Puro.
 *
 * O estado de "dentro de bloco de código cercado" é o único contexto que
 * atravessa linhas — dentro dele nada mais é marcação, que é o comportamento
 * correto e o que impede um bloco de exemplo de ser tingido como se fosse
 * estrutura do documento.
 */
export function classifyLines(source: string): ClassifiedLine[] {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const out: ClassifiedLine[] = [];
  let inFence = false;

  for (const text of lines) {
    if (/^\s*```/.test(text)) {
      out.push({ text, kind: "fence" });
      inFence = !inFence;
      continue;
    }
    if (inFence) {
      out.push({ text, kind: "code" });
      continue;
    }
    if (text.trim() === "") {
      out.push({ text, kind: "blank" });
      continue;
    }
    const heading = /^(#{1,6})\s/.exec(text);
    if (heading?.[1]) {
      out.push({ text, kind: "heading", level: heading[1].length });
      continue;
    }
    if (/^(-{3,}|_{3,}|\*{3,})\s*$/.test(text.trim())) {
      out.push({ text, kind: "rule" });
      continue;
    }
    if (/^\s*>/.test(text)) {
      out.push({ text, kind: "quote" });
      continue;
    }
    if (/^\s*(?:[-*+]|\d+[.)])\s/.test(text)) {
      out.push({ text, kind: "list" });
      continue;
    }
    out.push({ text, kind: "text" });
  }

  return out;
}

/**
 * Tinge marcação inline preservando os delimitadores.
 *
 * A ordem importa: código primeiro, porque dentro de crases nada mais é
 * marcação. Um `**` dentro de `` `código` `` tem que continuar sendo dois
 * asteriscos literais.
 */
function inkInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const parts = text.split(/(`[^`]*`)/g);

  parts.forEach((part, partIndex) => {
    if (part === "") return;
    const key = `${keyPrefix}.${partIndex}`;

    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      nodes.push(
        <span key={key} className="tok-code">
          <span className="syn">`</span>
          <code>{part.slice(1, -1)}</code>
          <span className="syn">`</span>
        </span>,
      );
      return;
    }

    const tokens = part.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g);
    tokens.forEach((token, tokenIndex) => {
      if (token === "") return;
      const tokenKey = `${key}.${tokenIndex}`;

      if (token.startsWith("**") && token.endsWith("**") && token.length > 4) {
        nodes.push(
          <span key={tokenKey}>
            <span className="syn">**</span>
            <strong>{token.slice(2, -2)}</strong>
            <span className="syn">**</span>
          </span>,
        );
        return;
      }
      if (token.startsWith("*") && token.endsWith("*") && token.length > 2) {
        nodes.push(
          <span key={tokenKey}>
            <span className="syn">*</span>
            <em>{token.slice(1, -1)}</em>
            <span className="syn">*</span>
          </span>,
        );
        return;
      }
      nodes.push(<span key={tokenKey}>{token}</span>);
    });
  });

  return nodes;
}

/** Tinge uma linha inteira, preservando indentação e marcadores. */
function inkLine(line: ClassifiedLine, key: string): ReactNode {
  const { text, kind } = line;

  // Linha em branco nao recebe caractere nenhum. A tentacao e devolver um espaco
  // nao-quebravel para a linha nao colapsar, e a primeira versao fazia isso — mas
  // ai copiar o prompt traz um U+00A0 que nao existe na fonte. Num renderizador
  // que promete verbatim, injetar caractere e o unico pecado imperdoavel. A
  // altura vem do CSS (.vline { min-block-size }).
  if (kind === "blank") return null;
  if (kind === "code" || kind === "fence") return <code className="tok-raw">{text}</code>;

  if (kind === "heading") {
    const match = /^(#{1,6})(\s+)(.*)$/.exec(text);
    if (!match?.[1]) return text;
    return (
      <>
        <span className="syn">{match[1]}</span>
        <span className="syn">{match[2]}</span>
        <span className="head-text">{inkInline(match[3] ?? "", key)}</span>
      </>
    );
  }

  if (kind === "list") {
    const match = /^(\s*)([-*+]|\d+[.)])(\s+)(.*)$/.exec(text);
    if (!match) return inkInline(text, key);
    return (
      <>
        <span>{match[1]}</span>
        <span className="syn marker">{match[2]}</span>
        <span>{match[3]}</span>
        {inkInline(match[4] ?? "", key)}
      </>
    );
  }

  if (kind === "quote") {
    const match = /^(\s*)(>+)(\s*)(.*)$/.exec(text);
    if (!match) return inkInline(text, key);
    return (
      <>
        <span>{match[1]}</span>
        <span className="syn marker">{match[2]}</span>
        <span>{match[3]}</span>
        {inkInline(match[4] ?? "", key)}
      </>
    );
  }

  if (kind === "rule") return <span className="syn">{text}</span>;

  return inkInline(text, key);
}

export function VerbatimPrompt({ source, id = "prompt" }: { source: string; id?: string }) {
  const lines = classifyLines(source.replace(/\s+$/, ""));

  return (
    <div className="verbatim">
      {/*
        Duas vistas do MESMO DOM, alternadas só por CSS — sem JavaScript, então
        funciona no HTML estático e antes de qualquer hidratação.

        - **Leitura** (padrão): Spectral, medida confortável, quebra natural.
        - **Bruta**: Azeret Mono, número por linha, sem quebra.

        Por que não numerar na coluna de leitura: os `.persona.md` vêm
        hard-wrapped em 78–79 colunas, e ~50% das linhas passam de 64ch. Com
        medida de leitura, metade do documento sofreria reflow e a numeração
        apontaria para linhas visuais que não são as linhas do arquivo. Na vista
        bruta a linha é real, e só ali o endereço `#L12` significa alguma coisa.
      */}
      <div className="verbatim-tools">
        <input type="checkbox" id={`${id}-raw`} className="raw-toggle" />
        <label htmlFor={`${id}-raw`}>Raw, with line numbers</label>
      </div>
      <ol className="verbatim-lines">
        {lines.map((line, index) => {
          const number = index + 1;
          return (
            <li
              key={number}
              id={`L${number}`}
              className="vline"
              data-kind={line.kind}
              data-level={line.level}
            >
              {/* O número é conteúdo gerado por CSS (`::before`) para não entrar
                  na seleção — copiar o prompt tem que copiar o prompt, não uma
                  coluna de números.

                  tabIndex={-1}: sem isto, um prompt de 50-200 linhas injetava
                  50-200 paradas de Tab invisíveis entre o toggle e o resto da
                  página (auditoria 2026-08-06). A âncora continua clicável e o
                  deep-link #Ln continua funcionando — o id está no <li>; ela
                  só sai da ordem de tabulação. */}
              <a
                className="vline-anchor"
                href={`#L${number}`}
                aria-label={`Line ${number}`}
                tabIndex={-1}
              />
              <span className="vline-text">{inkLine(line, `l${number}`)}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
