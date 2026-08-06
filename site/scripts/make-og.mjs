// Gera site/app/opengraph-image.png (1200×630) uma única vez, para ser
// versionado. Usa o sharp já presente em site/node_modules — o build do site
// NÃO depende disto; é ferramenta de geração, como fetch-fonts.
import sharp from "sharp";
import { writeFileSync } from "node:fs";

const W = 1200;
const H = 630;

// Favo idêntico ao do fundo do site (D-019): pointy-top, √3R=40, tile 40×69.282.
let hexes = "";
for (let ty = -1; ty * 69.282 < H + 70; ty++) {
  for (let tx = -1; tx * 40 < W + 40; tx++) {
    const ox = tx * 40;
    const oy = ty * 69.282;
    hexes += `<path transform="translate(${ox} ${oy})" fill="none" stroke="#43605f" stroke-opacity=".10" d="M0 11.547L20 0l20 11.547M0 11.547v23.094l20 11.547 20-11.547M20 46.188v23.094"/>`;
  }
}

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
  <rect width="${W}" height="${H}" fill="#e3e8df"/>
  ${hexes}
  <rect x="0" y="0" width="${W}" height="10" fill="#87581d"/>
  <text x="84" y="150" font-family="Arial, sans-serif" font-weight="700" font-size="44" fill="#221d16">Waggle</text>
  <text x="84" y="196" font-family="Consolas, monospace" font-size="26" fill="#43605f">KILLER BEE PACKS FOR BUZZ</text>
  <text x="84" y="330" font-family="Georgia, serif" font-size="58" fill="#221d16">Buzz has a persona catalog</text>
  <text x="84" y="400" font-family="Georgia, serif" font-size="58" fill="#221d16">inside each community.</text>
  <text x="84" y="470" font-family="Georgia, serif" font-size="58" fill="#87581d">Killer Bee is the catalog between them.</text>
  <text x="84" y="560" font-family="Consolas, monospace" font-size="24" fill="#5d564b">Every system prompt readable in full before you install · by Saulo Duttra</text>
</svg>`;

const png = await sharp(Buffer.from(svg)).png().toBuffer();
writeFileSync("D:/EMPRESAS/buzz/killer-bee/site/app/opengraph-image.png", png);
console.log("og image:", png.length, "bytes");
