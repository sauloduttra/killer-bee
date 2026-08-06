import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getPack, packs, splitModel } from "@/app/lib/catalog";
import {
  AFTER_IMPORT,
  IMPORT_CLICK_COUNT,
  IMPORT_SHORTCUT,
  IMPORT_STEPS,
  agentFileName,
  buildCommand,
  teamFileName,
} from "@/app/lib/install";
import { CopyButton } from "@/app/components/CopyButton";
import { ProfileMeter } from "@/app/components/ProfileMeter";

export function generateStaticParams() {
  return packs.map((pack) => ({ pack: pack.name }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ pack: string }>;
}): Promise<Metadata> {
  const { pack: packName } = await params;
  const pack = getPack(packName);
  if (!pack) return {};
  return {
    title: pack.name,
    description: pack.description,
    alternates: { canonical: `./` },
    openGraph: { title: `${pack.name} — Waggle`, description: pack.description, url: "./" },
  };
}

export default async function PackPage({ params }: { params: Promise<{ pack: string }> }) {
  const { pack: packName } = await params;
  const pack = getPack(packName);
  if (!pack) notFound();

  const providers = [
    ...new Set(
      pack.personas
        .map((persona) => splitModel(persona.model).provider)
        .filter((provider): provider is string => Boolean(provider)),
    ),
  ];

  return (
    <article className="page">
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link href="/">Catalog</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{pack.name}</span>
      </nav>

      <header className="page-head">
        <h1>{pack.name}</h1>
        <p className="lede">{pack.description}</p>
        <dl className="factsheet">
          <div>
            <dt>version</dt>
            <dd>{pack.version}</dd>
          </div>
          <div>
            <dt>author</dt>
            <dd>{pack.author || "—"}</dd>
          </div>
          <div>
            <dt>license</dt>
            <dd>{pack.license || "—"}</dd>
          </div>
          <div>
            <dt>providers</dt>
            <dd>{providers.length ? providers.join(", ") : "unset"}</dd>
          </div>
          {pack.buzzCommit && (
            <div>
              <dt>verified against</dt>
              <dd>
                <code title={pack.buzzCommit}>buzz @ {pack.buzzCommit.slice(0, 8)}</code>
              </dd>
            </div>
          )}
        </dl>
      </header>

      {pack.teams.length > 0 && (
        <section aria-labelledby="teams-heading">
          <h2 id="teams-heading" className="section-heading">
            Teams
          </h2>
          {pack.teams.map((team) => (
            <div className="team" key={team.id}>
              <h3>{team.name}</h3>
              <p>{team.description}</p>
              {team.instructions && (
                <details className="disclosure">
                  <summary>Team instructions, in full</summary>
                  <div className="prose">
                    <p>{team.instructions}</p>
                  </div>
                </details>
              )}
              <p className="team-members">
                {team.members.map((member, i) => (
                  <span key={member}>
                    {i > 0 && <span aria-hidden="true"> · </span>}
                    <Link href={`/personas/${pack.name}/${member}/`}>{member}</Link>
                  </span>
                ))}
              </p>
              <div className="downloads">
                <a
                  className="button"
                  href={`/downloads/${pack.name}/${teamFileName(team.id, "json")}`}
                  download
                >
                  {teamFileName(team.id, "json")}
                </a>
                <a
                  className="button button-quiet"
                  href={`/downloads/${pack.name}/${teamFileName(team.id, "png")}`}
                  download
                >
                  {teamFileName(team.id, "png")}
                </a>
              </div>
            </div>
          ))}
        </section>
      )}

      <section aria-labelledby="personas-heading">
        <h2 id="personas-heading" className="section-heading">
          Personas
        </h2>
        <ul className="persona-list">
          {pack.personas.map((persona) => {
            const { provider, modelId } = splitModel(persona.model);
            return (
              <li key={persona.name} className="persona-row">
                <div className="persona-row-head">
                  <h3>
                    <Link href={`/personas/${pack.name}/${persona.name}/`}>
                      {persona.displayName}
                    </Link>
                  </h3>
                  <p className="persona-row-desc">{persona.description}</p>
                  <p className="persona-row-model">
                    {provider ? (
                      <>
                        <span className="chip">{provider}</span> <code>{modelId}</code>
                      </>
                    ) : (
                      <span className="chip chip-quiet">no model set</span>
                    )}
                    {persona.runtime && <span className="chip chip-quiet">{persona.runtime}</span>}
                  </p>
                </div>
                <ProfileMeter profile={persona.profile} />
                <div className="downloads">
                  <a
                    className="button"
                    href={`/downloads/${pack.name}/${agentFileName(persona.name, "json")}`}
                    download
                  >
                    {agentFileName(persona.name, "json")}
                  </a>
                  <a
                    className="button button-quiet"
                    href={`/downloads/${pack.name}/${agentFileName(persona.name, "png")}`}
                    download
                  >
                    {agentFileName(persona.name, "png")}
                  </a>
                  <Link className="button button-quiet" href={`/personas/${pack.name}/${persona.name}/`}>
                    Read the prompt
                  </Link>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="install" aria-labelledby="install-heading">
        <h2 id="install-heading" className="section-heading">
          Installing
        </h2>
        <p className="install-count">
          <strong>{IMPORT_CLICK_COUNT}.</strong> {IMPORT_SHORTCUT}
        </p>
        <ol className="steps">
          {IMPORT_STEPS.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>

        <div className="callout">
          <h3>Imported is not running</h3>
          <ul>
            {AFTER_IMPORT.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <h3 className="subhead">Or build it from source</h3>
        <p>
          The files above are generated from this repository. Nothing is fetched at runtime
          and nothing phones home.
        </p>
        <div className="command">
          <code>{buildCommand(pack.name)}</code>
          <CopyButton value={buildCommand(pack.name)} />
        </div>
      </section>
    </article>
  );
}
