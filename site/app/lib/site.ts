/**
 * A URL pública canônica do site, num lugar só.
 *
 * `layout.tsx` (metadataBase), `sitemap.ts` e `robots.ts` precisam do MESMO
 * valor — três cópias divergiriam em silêncio. No CI vem de
 * `NEXT_PUBLIC_SITE_URL` (pages.yml passa `steps.pages.outputs.base_url`, que
 * é origin + basePath — usar `origin` cru foi o bug do canonical, auditoria
 * 2026-08-06). O default segue a suposição de D-020 (repo
 * sauloduttra/killer-bee → GitHub Pages de projeto).
 */
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://sauloduttra.github.io/killer-bee"
).replace(/\/$/, "");

/** Alt da og:image — compartilhado entre o layout e as páginas internas, que
 * precisam repetir `images` porque openGraph de página substitui o do layout. */
export const OG_ALT =
  "Waggle — Killer Bee packs for Buzz. Buzz has a persona catalog inside each " +
  "community; Killer Bee is the catalog between them. By Saulo Duttra.";
