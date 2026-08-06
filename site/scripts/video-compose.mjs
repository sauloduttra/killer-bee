// Compõe os frames finais do vídeo de 90s: recorte fino, legendas em placa
// REGISTRO e o cartão final com os créditos. Consome media/raw e media/frames,
// escreve media/final. Roteiro: docs/AUDIT-2026-08-06.md (beat a beat).
// Rodar de site/: `node scripts/video-compose.mjs` (caminhos relativos a site/).
import sharp from "sharp";
import { mkdirSync } from "node:fs";

const FRAMES = "../media/frames/";
const RAW = "../media/raw/";
const FINAL = "../media/final/";
mkdirSync(FINAL, { recursive: true });

const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** Placa de legenda: faixa inferior no substrato escuro do REGISTRO, filete
 * na tinta de queima. Baked no frame — sem drawtext/fontes do ffmpeg. */
function captionSvg(text) {
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="110">
    <rect width="1920" height="110" fill="#141712" fill-opacity="0.94"/>
    <rect width="1920" height="3" fill="#c08a33"/>
    <text x="84" y="68" font-family="Consolas, monospace" font-size="30" fill="#dcddd4">${esc(text)}</text>
  </svg>`);
}

async function withCaption(src, out, text) {
  await sharp(FRAMES + src)
    .composite([{ input: captionSvg(text), gravity: "south" }])
    .png()
    .toFile(FINAL + out);
}

// Recorte mais justo do card "Mixed models".
await sharp(RAW + "app-runtime.png")
  .extract({ left: 500, top: 980, width: 1920, height: 1080 })
  .png()
  .toFile(FINAL + "m07-mixed-src.png");

// ── Cartão final ────────────────────────────────────────────────────────────
let hexes = "";
for (let ty = -1; ty * 69.282 < 1080 + 70; ty++) {
  for (let tx = -1; tx * 40 < 1920 + 40; tx++) {
    hexes += `<path transform="translate(${tx * 40} ${ty * 69.282})" fill="none" stroke="#7fa3a0" stroke-opacity=".06" d="M0 11.547L20 0l20 11.547M0 11.547v23.094l20 11.547 20-11.547M20 46.188v23.094"/>`;
  }
}
const endcard = `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
  <rect width="1920" height="1080" fill="#1a1e19"/>
  ${hexes}
  <rect x="0" y="0" width="1920" height="8" fill="#c08a33"/>
  <text x="140" y="270" font-family="Arial, sans-serif" font-weight="700" font-size="88" fill="#dcddd4">Killer Bee</text>
  <text x="140" y="340" font-family="Georgia, serif" font-size="42" fill="#c08a33">The catalog between communities.</text>
  <text x="140" y="470" font-family="Consolas, monospace" font-size="34" fill="#dcddd4">github.com/sauloduttra/killer-bee</text>
  <text x="140" y="525" font-family="Consolas, monospace" font-size="34" fill="#dcddd4">sauloduttra.github.io/killer-bee</text>
  <text x="140" y="640" font-family="Consolas, monospace" font-size="26" fill="#9a9a90">Apache-2.0 · not affiliated with Block, Inc. or the Buzz project</text>
  <text x="140" y="690" font-family="Consolas, monospace" font-size="26" fill="#9a9a90">every claim carries file:line · every download carries sha256</text>
  <text x="140" y="840" font-family="Arial, sans-serif" font-weight="700" font-size="40" fill="#dcddd4">built by Saulo Duttra</text>
  <text x="140" y="895" font-family="Consolas, monospace" font-size="28" fill="#7fa3a0">github.com/sauloduttra · x.com/sauloduttra · nostr: primal.net/p/nprofile1qqsxwact…</text>
</svg>`;
await sharp(Buffer.from(endcard)).png().toFile(FINAL + "m11-endcard.png");

// ── Sequência com legendas ─────────────────────────────────────────────────
await sharp(FRAMES + "hero.png").png().toFile(FINAL + "m01-hero.png");
await withCaption("verbatim.png", "m02-verbatim.png",
  "the system prompt, verbatim — every character on screen, even the markdown");
await withCaption("l12.png", "m03-l12.png",
  "#L12 — every line of the prompt has an address");
await withCaption("team-downloads.png", "m04-downloads.png",
  "one team, three agents, three providers — sha256 beside every download");
await withCaption("install.png", "m05-install.png",
  "no one-click install exists. four clicks plus the file picker — we counted");
await withCaption("import3.png", "m06-import.png",
  "one file rebuilds the whole team — fresh keypairs, identity never travels");
await sharp(FINAL + "m07-mixed-src.png")
  .composite([{ input: captionSvg("the app itself labels it: Mixed models"), gravity: "south" }])
  .png()
  .toFile(FINAL + "m07-mixed.png");
await withCaption("stopped.png", "m08-stopped.png",
  "imported is not running — STOPPED until you add your own credentials");
await withCaption("channels.png", "m09-channels.png",
  "and in no channel until you put it there. we say so up front");
await withCaption("manifesto.png", "m10-manifesto.png",
  "no buzz install · no deep links · no guaranteed replies — all documented");

console.log("frames finais em media/final/");
