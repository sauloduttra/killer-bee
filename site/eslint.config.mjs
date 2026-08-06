/**
 * Flat config direto.
 *
 * `eslint-config-next` 16 já exporta flat config; passar por `FlatCompat` faz o
 * validador legado tentar serializar o objeto de plugins e estourar em
 * "Converting circular structure to JSON". A ponte de compatibilidade só serve
 * para config que ainda é eslintrc — esta não é.
 */
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const config = [
  ...(Array.isArray(nextCoreWebVitals) ? nextCoreWebVitals : [nextCoreWebVitals]),
  ...(Array.isArray(nextTypescript) ? nextTypescript : [nextTypescript]),
  {
    // Saída de build e dados gerados a partir de packs/ não são fonte.
    ignores: ["out/**", ".next/**", "public/downloads/**", "data/**"],
  },
];

export default config;
