import type { MetadataRoute } from "next";
import { SITE_URL } from "@/app/lib/site";

// Gerado em build (export estático) — o metadata declarava
// `robots: { index: true }` e não existia robots.txt nenhum; crawler que só
// olha o arquivo não via permissão nem sitemap (auditoria 2026-08-06).
export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
