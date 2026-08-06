/**
 * Testes sobre o HTML EXPORTADO, não sobre o fonte.
 *
 * Roda depois de `next build`, contra `out/`. É o que prova que o export estático
 * de fato contém o conteúdo — um teste de componente passaria mesmo se o export
 * cuspisse uma casca vazia dependente de JS.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";

const OUT = "out";

async function read(path) {
  return readFile(join(OUT, path), "utf8");
}

const catalog = JSON.parse(await readFile("data/catalog.json", "utf8"));
const firstPack = catalog.packs[0];

test("o export existe", () => {
  assert.ok(existsSync(OUT), "next build --output export deve produzir out/");
  assert.ok(existsSync(join(OUT, "index.html")));
});

test("nenhum metadado usa http://", async () => {
  // O defeito nº 2 que atribuímos ao buzzdir não existia — os metadados dele já
  // eram https. Mantemos a asserção porque o modo de falha é silencioso: um
  // canonical http:// não quebra nada visivelmente e envenena o SEO e a segurança.
  const html = await read("index.html");
  const head = html.slice(0, html.indexOf("</head>"));
  const offenders = [...head.matchAll(/(?:href|content|property="og:url"[^>]*content)="(http:\/\/[^"]+)"/g)];
  assert.equal(
    offenders.length,
    0,
    `metadado com http:// no <head>: ${offenders.map((m) => m[1]).join(", ")}`,
  );
});

test("o catálogo vai server-rendered, não montado por JS", async () => {
  const html = await read("index.html");
  for (const pack of catalog.packs) {
    assert.ok(html.includes(pack.name), `pack ausente do HTML estático: ${pack.name}`);
  }
});

/** Decodifica as entidades que o React emite. */
function decodeEntities(text) {
  return text
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&");
}

/** Texto de cada `<li class="vline">` do bloco verbatim, na ordem. */
function verbatimLines(html) {
  const block = /<ol class="verbatim-lines"[^>]*>([\s\S]*?)<\/ol>/.exec(html);
  if (!block) return null;
  return [...block[1].matchAll(/<li\b[^>]*class="vline"[^>]*>([\s\S]*?)<\/li>/g)].map((match) =>
    decodeEntities(match[1].replace(/<[^>]+>/g, "")),
  );
}

test("o system prompt está no HTML CARACTERE A CARACTERE", async () => {
  // Transparência é o produto. O renderizador verbatim promete que nenhum
  // caractere é apagado — este teste é o que transforma a promessa em contrato.
  //
  // Comparar a string contígua não serve: o texto está distribuído por linha,
  // cada uma com sua âncora. Extraímos o texto de cada `<li>` e comparamos com a
  // linha correspondente da fonte.
  for (const persona of firstPack.personas) {
    const html = await read(join("personas", firstPack.name, persona.name, "index.html"));
    const rendered = verbatimLines(html);
    assert.ok(rendered, `bloco verbatim ausente na página de ${persona.name}`);

    const source = persona.systemPrompt.replace(/\s+$/, "").replace(/\r\n/g, "\n").split("\n");
    assert.equal(
      rendered.length,
      source.length,
      `${persona.name}: ${source.length} linhas na fonte, ${rendered.length} renderizadas`,
    );

    source.forEach((line, index) => {
      // Igualdade EXATA, inclusive linha em branco: o renderizador não injeta
      // caractere nenhum. A primeira versão devolvia um espaço não-quebrável
      // para a linha não colapsar, e isso fazia "copiar prompt" trazer um
      // U+00A0 inexistente na fonte. A altura vem do CSS.
      assert.equal(
        rendered[index],
        line,
        `${persona.name} linha ${index + 1} divergiu:\n  fonte:       ${JSON.stringify(line)}\n  renderizada: ${JSON.stringify(rendered[index])}`,
      );
    });
  }
});

test("os arquivos baixáveis existem para cada persona e team", async () => {
  for (const pack of catalog.packs) {
    for (const persona of pack.personas) {
      for (const ext of ["json", "png"]) {
        const path = join(OUT, "downloads", pack.name, `${persona.name}.agent.${ext}`);
        assert.ok(existsSync(path), `faltando ${path}`);
      }
    }
    for (const team of pack.teams) {
      for (const ext of ["json", "png"]) {
        const path = join(OUT, "downloads", pack.name, `${team.id}.team.${ext}`);
        assert.ok(existsSync(path), `faltando ${path}`);
      }
    }
  }
});

test("o snapshot baixável é um buzz-agent-snapshot v1 válido", async () => {
  // O arquivo servido tem que ser o mesmo que o desktop importa. Se o pipeline
  // servir outra coisa, o botão de download mente.
  const persona = firstPack.personas[0];
  const raw = await read(join("downloads", firstPack.name, `${persona.name}.agent.json`));
  const snapshot = JSON.parse(raw);
  assert.equal(snapshot.format, "buzz-agent-snapshot");
  assert.equal(snapshot.version, 1);
  assert.equal(snapshot.definition.systemPrompt.trim(), persona.systemPrompt.trim());
});

test("cada página de pack e persona foi exportada", async () => {
  for (const pack of catalog.packs) {
    assert.ok(existsSync(join(OUT, "packs", pack.name, "index.html")));
    for (const persona of pack.personas) {
      assert.ok(existsSync(join(OUT, "personas", pack.name, persona.name, "index.html")));
    }
  }
});

test("as fontes são auto-hospedadas: @font-face aponta para caminho local", async () => {
  const cssDir = join(OUT, "_next", "static", "css");
  if (!existsSync(cssDir)) return; // sem CSS extraído, nada a checar
  const files = await readdir(cssDir);
  const css = (
    await Promise.all(files.filter((f) => f.endsWith(".css")).map((f) => read(join("_next", "static", "css", f))))
  ).join("\n");

  const faces = [...css.matchAll(/@font-face\s*{[^}]*}/g)].map((m) => m[0]);
  assert.ok(faces.length > 0, "nenhum @font-face — as fontes precisam ser auto-hospedadas");
  for (const face of faces) {
    assert.ok(
      !/url\(\s*['"]?https?:\/\//.test(face),
      `@font-face busca fonte remota: ${face.slice(0, 120)}`,
    );
    assert.ok(/font-display\s*:\s*swap/.test(face), "font-display: swap ausente num @font-face");
  }
});

test("nenhuma requisição a terceiro no HTML", async () => {
  // CSP restritiva só vale se o HTML de fato não pedir nada de fora.
  //
  // Só conta o que o navegador BUSCA: script, folha de estilo, preload, ícone,
  // imagem, iframe. `<link rel="canonical">` e `og:url` são metadados — apontam
  // para um endereço absoluto por definição e não geram requisição. Confundir os
  // dois foi a primeira versão deste teste, e ela reprovava o site correto.
  const html = await read("index.html");

  const fetching = [
    ...html.matchAll(/<script[^>]+src="(https?:\/\/[^"]+)"/g),
    ...html.matchAll(/<img[^>]+src="(https?:\/\/[^"]+)"/g),
    ...html.matchAll(/<iframe[^>]+src="(https?:\/\/[^"]+)"/g),
    ...[...html.matchAll(/<link\b[^>]*>/g)]
      .filter((tag) => /rel="(?:stylesheet|preload|prefetch|icon|apple-touch-icon|preconnect|dns-prefetch)"/.test(tag[0]))
      .flatMap((tag) => [...tag[0].matchAll(/href="(https?:\/\/[^"]+)"/g)]),
  ].map((match) => match[1]);

  assert.deepEqual(fetching, [], `recurso remoto no HTML: ${fetching.join(", ")}`);
});

test("todo link que abre em nova aba tem rel=noopener", async () => {
  // `window.opener` só existe quando o link abre em outro contexto. Link externo
  // em mesma aba não precisa de `noopener` — exigir isso foi a primeira versão
  // deste teste, e ela reprovava o rodapé, que está correto.
  for (const page of ["index.html", join("packs", firstPack.name, "index.html")]) {
    const html = await read(page);
    const blank = [...html.matchAll(/<a\b[^>]*target="_blank"[^>]*>/g)].map((m) => m[0]);
    for (const anchor of blank) {
      assert.ok(
        /rel="[^"]*noopener/.test(anchor),
        `target=_blank sem rel="noopener" em ${page}: ${anchor.slice(0, 120)}`,
      );
    }
  }
});

test("nenhum script de origem externa", async () => {
  // O renderizador verbatim é a única superfície onde HTML nasce de conteúdo
  // enviado por PR, e ele não tem caminho para HTML cru — um `<script>` no prompt
  // vira as letras `<script>`. Este teste guarda o resultado, não a intenção.
  const html = await read(join("personas", firstPack.name, firstPack.personas[0].name, "index.html"));
  const scripts = [...html.matchAll(/<script\b[^>]*>/g)].map((m) => m[0]);
  for (const tag of scripts) {
    const src = /src="([^"]+)"/.exec(tag)?.[1];
    assert.ok(
      src === undefined || src.startsWith("/"),
      `script com origem externa: ${tag.slice(0, 120)}`,
    );
  }
});

test("o prompt é verbatim: a sintaxe markdown continua na tela", async () => {
  // A tese da página. Um conversor mostraria "Role" onde a fonte diz "## Role";
  // aqui os dois caracteres têm que estar no HTML, apenas com tinta diferente.
  const persona = firstPack.personas.find((p) => /^#{1,6}\s/m.test(p.systemPrompt));
  if (!persona) return;
  const html = await read(join("personas", firstPack.name, persona.name, "index.html"));
  const marks = [...persona.systemPrompt.matchAll(/^(#{1,6})\s+(.+)$/gm)];
  assert.ok(marks.length > 0);
  for (const [, hashes, text] of marks.slice(0, 3)) {
    assert.ok(html.includes(`>${hashes}<`), `o marcador ${hashes} sumiu do HTML`);
    assert.ok(html.includes(text.trim().slice(0, 24)), "o texto do heading sumiu");
  }
});

test("cada linha do prompt tem endereço próprio", async () => {
  const persona = firstPack.personas[0];
  const html = await read(join("personas", firstPack.name, persona.name, "index.html"));
  const lines = persona.systemPrompt.replace(/\s+$/, "").split("\n").length;
  assert.ok(html.includes('id="L1"'), "faltando a âncora da primeira linha");
  assert.ok(html.includes(`id="L${lines}"`), `faltando a âncora da linha ${lines}`);
});
