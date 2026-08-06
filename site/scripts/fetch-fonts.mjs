/**
 * Baixa as fontes OFL e as auto-hospeda em `app/fonts/` (ver OUT_DIR — um
 * cabeçalho anterior dizia `public/fonts/`, que nunca foi o destino real).
 *
 * Por que existe: o buzzdir declara `"Aptos Display"` e não embarca nada
 * (`globals.css:55-56`, sem um único `@font-face` no repositório). Quem não tem
 * Office cai em Helvetica e o desenho tipográfico inteiro muda. É o defeito (a)
 * que apontamos, e o único jeito honesto de corrigir é servir o arquivo.
 *
 * O que este script faz:
 *   1. pede o CSS do Google Fonts com um User-Agent moderno — sem isso a API
 *      devolve `ttf`, não `woff2`
 *   2. FILTRA os blocos `@font-face` pelos comentários de subset da resposta
 *      (`/* latin *​/` etc.) — a API css2 IGNORA um parâmetro `subset=` na URL,
 *      e uma versão anterior confiava nele: baixava e versionava também
 *      cyrillic, cyrillic-ext e vietnamese (auditoria 2026-08-06)
 *   3. baixa só os `woff2` dos blocos mantidos, reescreve o `src` para caminho
 *      local e grava `app/fonts/fonts.css`
 *
 * As fontes ficam **versionadas** no repositório. Rodar isto é passo de
 * manutenção, não de build: o CI não deve depender de rede para produzir o site,
 * e uma família que suma do Google Fonts não pode quebrar o deploy.
 *
 * Uso:
 *   node scripts/fetch-fonts.mjs
 */
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

/**
 * Os arquivos vão para `app/fonts/`, não `public/`, e o `url()` é RELATIVO.
 *
 * Dois motivos, os dois descobertos quebrando:
 *
 * 1. `@import url("/fonts/fonts.css")` faz o Turbopack tentar resolver o caminho
 *    como módulo e o build morre em "module not found". Arquivo em `public/` é
 *    servido, não empacotado.
 * 2. Com `basePath` (o site vive em `/<repo>/` no GitHub Pages), um `url()`
 *    absoluto apontaria para a raiz do domínio e a fonte daria 404. O bundler
 *    reescreve `url()` relativo com o basePath correto e ainda coloca hash no
 *    nome — cache eterno de graça.
 */
const OUT_DIR = "app/fonts";

/**
 * Um User-Agent de Chrome recente. A API do Google Fonts faz negociação de
 * formato pelo UA: com UA antigo ou ausente ela serve `ttf`, que é 2 a 4 vezes
 * maior. Não é gambiarra — é o contrato documentado da API.
 */
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

/**
 * Famílias a hospedar. `axis` usa a sintaxe de fonte variável da API v2.
 * Subset `latin-ext` cobre português — o projeto é brasileiro e "scutellata"
 * convive com "ª", "ç" e acentos no conteúdo.
 */
const FAMILIES = [
  { name: "Archivo", axis: "wght@100..900", subsets: ["latin", "latin-ext"] },
  { name: "Spectral", axis: "wght@400;600", italic: true, subsets: ["latin", "latin-ext"] },
  { name: "Azeret Mono", axis: "wght@400;500", subsets: ["latin", "latin-ext"] },
];

function cssUrl(family) {
  const name = family.name.replace(/ /g, "+");
  // `ital,wght@0,...;1,...` é a forma da v2 quando há itálico.
  const spec = family.italic
    ? `${name}:ital,${family.axis.replace("wght@", "wght@0,").replace(/;(?=\d)/g, ";0,")};1,400`
    : `${name}:${family.axis}`;
  // Sem `subset=`: a API css2 ignora o parâmetro. A seleção de subset é feita
  // do lado de cá, filtrando os blocos da resposta (keepSubsets).
  return `https://fonts.googleapis.com/css2?family=${spec}&display=swap`;
}

/**
 * Mantém só os blocos `@font-face` dos subsets pedidos.
 *
 * A resposta da css2 anota cada bloco com um comentário `/* latin *​/` na linha
 * anterior — é o único contrato disponível para saber de que subset o arquivo
 * é. Bloco sem anotação é mantido (falha aberta: fonte demais é peso; fonte de
 * menos é layout quebrado).
 */
function keepSubsets(css, wanted) {
  const blocks = css.split(/(?=\/\* [a-z-]+ \*\/)/);
  return blocks
    .filter((block) => {
      const marker = block.match(/^\/\* ([a-z-]+) \*\//);
      if (!marker) return true;
      return wanted.includes(marker[1]);
    })
    .join("");
}

async function fetchText(url) {
  const response = await fetch(url, { headers: { "User-Agent": UA } });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText} em ${url}`);
  return response.text();
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const chunks = [
    "/* Fontes auto-hospedadas. Gerado por scripts/fetch-fonts.mjs — não editar à mão.",
    "   Todas sob SIL Open Font License 1.1; ver THIRD_PARTY_NOTICES.md. */",
    "",
  ];
  let downloaded = 0;

  for (const family of FAMILIES) {
    const url = cssUrl(family);
    let css;
    try {
      css = await fetchText(url);
    } catch (error) {
      console.error(`falhou ${family.name}: ${error.message}`);
      process.exitCode = 1;
      continue;
    }
    css = keepSubsets(css, family.subsets);

    const matches = [...css.matchAll(/url\((https:\/\/fonts\.gstatic\.com\/[^)]+\.woff2)\)/g)];
    if (matches.length === 0) {
      console.error(`${family.name}: nenhum woff2 no CSS — a API mudou de contrato?`);
      process.exitCode = 1;
      continue;
    }

    const localByRemote = new Map();
    let index = 0;
    for (const [, remote] of matches) {
      if (localByRemote.has(remote)) continue;
      const slug = family.name.toLowerCase().replace(/ /g, "-");
      const fileName = `${slug}-${index}.woff2`;
      index += 1;
      const response = await fetch(remote, { headers: { "User-Agent": UA } });
      if (!response.ok) {
        console.error(`falhou ${remote}: ${response.status}`);
        process.exitCode = 1;
        continue;
      }
      const bytes = Buffer.from(await response.arrayBuffer());
      await writeFile(join(OUT_DIR, fileName), bytes);
      localByRemote.set(remote, `./${fileName}`);
      downloaded += 1;
      console.log(`${fileName}  ${(bytes.length / 1024).toFixed(1)} KB`);
    }

    let localCss = css;
    for (const [remote, local] of localByRemote) {
      localCss = localCss.split(remote).join(local);
    }
    chunks.push(`/* ${family.name} */`, localCss.trim(), "");
  }

  await writeFile(join(OUT_DIR, "fonts.css"), chunks.join("\n"), "utf8");
  console.log(`\n${downloaded} arquivo(s) → ${OUT_DIR}/fonts.css`);
}

await main();
