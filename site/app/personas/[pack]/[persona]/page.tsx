import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { allPersonaRoutes, getPersona, splitModel } from "@/app/lib/catalog";
import {
  AFTER_IMPORT,
  IMPORT_CLICK_COUNT,
  agentFileName,
  downloadHref,
} from "@/app/lib/install";
import { VerbatimPrompt } from "@/app/lib/verbatim";
import { OG_ALT } from "@/app/lib/site";
import { Checksums } from "@/app/components/Checksums";
import { ProfileMeter } from "@/app/components/ProfileMeter";
import { CopyButton } from "@/app/components/CopyButton";

export function generateStaticParams() {
  return allPersonaRoutes();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ pack: string; persona: string }>;
}): Promise<Metadata> {
  const { pack, persona } = await params;
  const found = getPersona(pack, persona);
  if (!found) return {};
  return {
    title: `${found.persona.displayName} — ${found.pack.name}`,
    description: found.persona.description,
    alternates: { canonical: "./" },
    // Repete type, siteName e images porque o openGraph da página SUBSTITUI o
    // do layout — sem isto as páginas internas os perdiam (auditoria 2026-08-06).
    openGraph: {
      type: "website",
      siteName: "Waggle — Killer Bee agent packs for Buzz",
      title: `${found.persona.displayName} — Waggle`,
      description: found.persona.description,
      url: "./",
      images: [{ url: "/og.png", width: 1200, height: 630, alt: OG_ALT }],
    },
  };
}

export default async function PersonaPage({
  params,
}: {
  params: Promise<{ pack: string; persona: string }>;
}) {
  const { pack: packName, persona: personaName } = await params;
  const found = getPersona(packName, personaName);
  if (!found) notFound();
  const { pack, persona } = found;
  const { provider, modelId } = splitModel(persona.model);

  const words = persona.systemPrompt.trim().split(/\s+/).length;
  const lineCount = persona.systemPrompt.replace(/\s+$/, "").split("\n").length;
  // Bytes, não caracteres: é a unidade que o limite de 256 KB do corpo de evento
  // usa, e a que importa quando o pack for publicado como kind 30178.
  const byteLength = new TextEncoder().encode(persona.systemPrompt).length;
  const teams = pack.teams.filter((team) => team.members.includes(persona.name));

  return (
    <article className="page persona-page">
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link href="/">Catalog</Link>
        <span aria-hidden="true">/</span>
        <Link href={`/packs/${pack.name}/`}>{pack.name}</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{persona.displayName}</span>
      </nav>

      <header className="page-head">
        <h1>{persona.displayName}</h1>
        <p className="lede">{persona.description}</p>
        <p className="persona-row-model">
          {provider ? (
            <>
              <span className="chip">{provider}</span> <code>{modelId}</code>
            </>
          ) : (
            <span className="chip chip-quiet">no model set</span>
          )}
          {persona.runtime && <span className="chip chip-quiet">{persona.runtime}</span>}
          <span className="chip chip-quiet">{words} words</span>
        </p>
      </header>

      <section aria-labelledby="profile-heading">
        <h2 id="profile-heading" className="section-heading">
          Profile
        </h2>
        <ProfileMeter profile={persona.profile} />
      </section>

      <section className="prompt-section" aria-labelledby="prompt-heading">
        <div className="prompt-head">
          <h2 id="prompt-heading" className="section-heading">
            System prompt, verbatim
          </h2>
          <CopyButton value={persona.systemPrompt} label="Copy prompt" />
        </div>
        <p className="prompt-note">
          Not a rendering of the prompt — <strong>the prompt</strong>. Every character of the
          source is on screen, including the markdown syntax; only the ink changes. Line
          breaks are the author&apos;s. Each line has its own address, so{" "}
          <code>#L12</code> points at line 12.
        </p>
        <div className="tally">
          <span className="tally-value">{byteLength.toLocaleString("en-US")}</span>
          <span className="tally-unit">bytes, verbatim</span>
          <p className="tally-note">
            {lineCount} lines · {words} words. This is what travels inside the snapshot file,
            byte for byte.
          </p>
        </div>
        <VerbatimPrompt source={persona.systemPrompt} />
      </section>

      {teams.length > 0 && (
        <section aria-labelledby="teams-heading">
          <h2 id="teams-heading" className="section-heading">
            Works with
          </h2>
          {teams.map((team) => (
            <p key={team.id}>
              In <strong>{team.name}</strong>, alongside{" "}
              {team.members
                .filter((member) => member !== persona.name)
                .map((member, i, arr) => (
                  <span key={member}>
                    <Link href={`/personas/${pack.name}/${member}/`}>{member}</Link>
                    {i < arr.length - 2 ? ", " : i === arr.length - 2 ? " and " : ""}
                  </span>
                ))}
              .
            </p>
          ))}
        </section>
      )}

      <section className="install" aria-labelledby="get-heading">
        <h2 id="get-heading" className="section-heading">
          Get it
        </h2>
        <div className="downloads">
          <a
            className="button"
            href={downloadHref(pack.name, agentFileName(persona.name, "json"))}
            download
          >
            {agentFileName(persona.name, "json")}
          </a>
          <a
            className="button button-quiet"
            href={downloadHref(pack.name, agentFileName(persona.name, "png"))}
            download
          >
            {agentFileName(persona.name, "png")}
          </a>
        </div>
        <Checksums files={persona.files} />
        <p className="install-count">
          Import in Buzz Desktop: <strong>{IMPORT_CLICK_COUNT}</strong>.
        </p>
        <div className="callout">
          <h3>Then it still needs</h3>
          <ul>
            {AFTER_IMPORT.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>
    </article>
  );
}
