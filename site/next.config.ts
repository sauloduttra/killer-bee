import type { NextConfig } from "next";

// `basePath` para GitHub Pages sob um subcaminho de repositório. Vazio quando o
// site é servido na raiz de um domínio próprio.
const basePath =
  process.env.PAGES_BASE_PATH ??
  (process.env.GITHUB_REPOSITORY ? `/${process.env.GITHUB_REPOSITORY.split("/")[1]}` : "");

const nextConfig: NextConfig = {
  // Export estático puro: o catálogo é o repositório, e o site é um artefato de
  // build. Sem servidor, sem banco, sem chave de API — coerente com a tese de
  // soberania do ecossistema, não por preguiça.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  basePath,
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
  // Falhar o build em erro de tipo é o ponto de ter tipos.
  // (`eslint` saiu do next.config no Next 16 — o lint roda como passo próprio no CI.)
  typescript: { ignoreBuildErrors: false },
};

export default nextConfig;
