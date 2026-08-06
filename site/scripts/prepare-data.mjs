/**
 * Gera os dados do site a partir de `packs/`.
 *
 * Duas saídas, ambas produzidas pelo CLI Python, que valida cada pack antes de
 * emitir:
 *
 *   site/data/catalog.json          — lido no build, vira HTML estático
 *   site/public/downloads/<pack>/*  — os snapshots que o visitante baixa
 *
 * O `--out` aponta direto para `public/downloads` porque essa é exatamente a URL
 * que as páginas linkam. Sem etapa de cópia, sem dois lugares para ficarem
 * dessincronizados.
 *
 * Se um pack estiver inválido, o CLI sai diferente de zero e o build do site
 * morre aqui — antes de gerar página, não depois.
 */
import { execFileSync, execSync } from "node:child_process";
import { readdirSync, existsSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const siteDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoDir = resolve(siteDir, "..");
const packsDir = join(repoDir, "packs");

function run(args) {
  execFileSync("uv", ["run", "python", "-m", "killerbee", ...args], {
    cwd: repoDir,
    stdio: "inherit",
  });
}

// `uv` ausente é o modo de falha mais provável para quem clona só o site.
try {
  execSync("uv --version", { stdio: "ignore" });
} catch {
  console.error(
    "\nuv não encontrado. O catálogo é gerado pelo CLI Python do Killer Bee.\n" +
      "Instale uv (https://docs.astral.sh/uv/) e rode de novo.\n",
  );
  process.exit(1);
}

if (!existsSync(packsDir)) {
  console.error(`\npacks/ não encontrado em ${packsDir}\n`);
  process.exit(1);
}

// Com NEXT_PUBLIC_SITE_URL (setada nos builds de deploy; ausente em dev), o
// catálogo carrega o bloco imeta pronto por artefato — cada host publica
// imeta apontando para os PRÓPRIOS downloads; o sha256 é o mesmo em todos.
const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL ?? "").replace(/\/+$/, "");
const catalogArgs = ["catalog", "--packs", "packs", "--out", "site/data/catalog.json"];
if (siteUrl) {
  catalogArgs.push("--imeta-base-url", siteUrl);
}
run(catalogArgs);

const packNames = readdirSync(packsDir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && existsSync(join(packsDir, entry.name, "killerbee.yaml")))
  .map((entry) => entry.name)
  .sort();

if (packNames.length === 0) {
  console.error("\nnenhum pack em packs/ — o site não teria conteúdo\n");
  process.exit(1);
}

// Limpar antes de regenerar: o build escreve por pack e nunca apaga — sem isto,
// persona removida do catálogo continuaria PUBLICADA como download órfão para
// sempre (aconteceu no corte 51→48, D-036: hjm-lab & cia. sobreviveram aqui).
rmSync(join(siteDir, "public", "downloads"), { recursive: true, force: true });

for (const name of packNames) {
  run(["build", `packs/${name}`, "--out", "site/public/downloads"]);
}

console.log(`\ndados prontos: ${packNames.length} pack(s)\n`);
