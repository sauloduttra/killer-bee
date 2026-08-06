import type { MetadataRoute } from "next";
import { allPersonaRoutes, packs } from "@/app/lib/catalog";
import { SITE_URL } from "@/app/lib/site";

// Gerado em build a partir do catálogo — as rotas são as mesmas do
// generateStaticParams, então o sitemap nunca lista página que não exista.
export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: `${SITE_URL}/` },
    ...packs.map((pack) => ({ url: `${SITE_URL}/packs/${pack.name}/` })),
    ...allPersonaRoutes().map(({ pack, persona }) => ({
      url: `${SITE_URL}/personas/${pack}/${persona}/`,
    })),
  ];
}
