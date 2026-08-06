import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { REPO_URL } from "@/app/lib/install";
import "./globals.css";

/**
 * `metadataBase` é **https por construção**. O defeito nº 2 que atribuímos ao
 * buzzdir não existia — os metadados dele já eram relativos resolvidos contra uma
 * base https. Mantemos o teste de build que reprova `http://` em metadado assim
 * mesmo: o custo é uma asserção e o modo de falha é silencioso.
 */
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://killerbee-buzz.github.io";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Waggle — Killer Bee agent packs for Buzz",
    template: "%s — Waggle",
  },
  description:
    "Buzz has a persona catalog inside each community. Killer Bee is the catalog between them. Every system prompt readable in full before you install.",
  applicationName: "Waggle",
  alternates: { canonical: "./" },
  openGraph: {
    type: "website",
    url: "./",
    siteName: "Waggle — Killer Bee agent packs for Buzz",
    title: "Waggle — Killer Bee agent packs for Buzz",
    description:
      "Persona and agent-team packs for Buzz, with every system prompt readable in full before you install.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4ede1" },
    { media: "(prefers-color-scheme: dark)", color: "#14100c" },
  ],
  colorScheme: "light dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/*
          CSP via <meta> porque GitHub Pages não deixa definir cabeçalho HTTP.
          Menos poderosa que o header — `frame-ancestors` e `report-uri` são
          ignorados em meta — mas cobre o que importa aqui.

          `script-src` precisa de 'unsafe-inline' pelo payload de hidratação do
          Next, que é inline por construção. É o defeito (c) que apontamos no
          buzzdir e que herdamos pela mesma razão técnica; nonce exigiria um
          servidor, e o site é export estático. Registrado, não escondido.

          `connect-src 'self'` é correto HOJE: o site não fala com relay nenhum.
          Quando a camada L3 entrar (ler kind 30175/30178 ao vivo), isto precisa
          ganhar `wss:` — e é por isso que a CSP do buzzdir não podia ser copiada,
          já que ele nunca abre WebSocket. Ver DECISIONS D-011.
        */}
        <meta
          httpEquiv="Content-Security-Policy"
          content={[
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'none'",
            "form-action 'none'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests",
          ].join("; ")}
        />
        <meta name="referrer" content="strict-origin-when-cross-origin" />
      </head>
      <body>
        <a className="skip" href="#main">
          Skip to content
        </a>

        <header className="masthead">
          <Link href="/" className="wordmark">
            <span className="wordmark-name">Waggle</span>
            <span className="wordmark-sub">Killer Bee packs for Buzz</span>
          </Link>
          <nav aria-label="Main">
            <a href={`${REPO_URL}#readme`}>Docs</a>
            <a href={REPO_URL}>Source</a>
          </nav>
        </header>

        <main id="main">{children}</main>

        <footer className="colophon">
          <p>
            <strong>Not affiliated with Block, Inc., the Buzz project, or buzzdir.</strong>{" "}
            Independent community work. Killer Bee is a satellite: no forks, no patches to
            core.
          </p>
          <p>
            Buzz ships a hosted pack store on its own roadmap. These packs stay valid either
            way — the format is theirs, not ours.
          </p>
          <p className="colophon-meta">
            Apache-2.0 · <a href={`${REPO_URL}/blob/main/docs/BIBLIOGRAFIA.md`}>References</a> ·{" "}
            <a href={`${REPO_URL}/blob/main/docs/PROTOCOL-NOTES.md`}>Protocol notes</a>
          </p>
        </footer>
      </body>
    </html>
  );
}
