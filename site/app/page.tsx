import Link from "next/link";
import { allTags, packs } from "@/app/lib/catalog";
import { submitPackUrl } from "@/app/lib/install";
import { CatalogBrowser } from "@/app/components/CatalogBrowser";
import { WaggleField } from "@/app/components/WaggleField";

export default function Home() {
  const tags = allTags();
  const personaCount = packs.reduce((sum, pack) => sum + pack.personas.length, 0);
  const encoder = new TextEncoder();
  const promptBytes = packs.reduce(
    (sum, pack) =>
      sum + pack.personas.reduce((n, p) => n + encoder.encode(p.systemPrompt).length, 0),
    0,
  );

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <h1>
            Buzz has a persona catalog inside each community.
            <br />
            <em>Killer Bee is the catalog between them.</em>
          </h1>
          <p className="lede">
            Persona and agent-team packs you can read before you run. Every system prompt is
            here in full — not a summary, not a screenshot. If you would not paste it into
            your own agent, do not install it.
          </p>
          {/* O maior elemento da página é uma grandeza medida, não o nome do
              produto. É o total de bytes de prompt que este catálogo expõe para
              leitura — o único número que descreve honestamente o que o site é. */}
          <div className="tally">
            <span className="tally-value">{promptBytes.toLocaleString("en-US")}</span>
            <span className="tally-unit">bytes of system prompt, readable</span>
            <p className="tally-note">
              Across {packs.length} pack{packs.length === 1 ? "" : "s"} and {personaCount}{" "}
              persona{personaCount === 1 ? "" : "s"}. No accounts, no tracking, no download
              counts, no stars — there is nothing here to inflate.
            </p>
          </div>
        </div>
        <WaggleField />
      </section>

      <section className="directory" aria-labelledby="catalog-heading">
        <h2 id="catalog-heading" className="section-heading">
          Catalog
        </h2>
        {/* A lista renderizada pelo servidor vive dentro do browser client-side:
            o markup vai completo no HTML estático e o filtro é progressivo. */}
        <CatalogBrowser packs={packs} tags={tags} />
      </section>

      <section className="manifesto" aria-labelledby="honest-heading">
        <p className="section-index">01</p>
        <h2 id="honest-heading">What installing actually looks like</h2>
        <p className="manifesto-lede">
          There is no one-click install in Buzz today, and this site will not pretend
          otherwise.
        </p>
        <div className="manifesto-grid">
          <div>
            <h3>No deep link exists</h3>
            <p>
              The desktop app registers five URL actions — connect, join, add-community,
              message, nostr-bind. Persona and team are not among them. We checked the
              handler, not the docs.
            </p>
          </div>
          <div>
            <h3>No <code>buzz install</code> either</h3>
            <p>
              The CLI has <code>pack validate</code> and <code>pack inspect</code>, both local.
              The <code>.buzzpack</code> archive and its registry live in the spec, not in the
              code.
            </p>
          </div>
          <div>
            <h3>So: download, then import</h3>
            <p>
              Four clicks plus the file picker. We counted. Every pack page shows the steps and
              what is still missing afterwards — importing an agent is not the same as running
              one.
            </p>
          </div>
          <div>
            <h3>Teams answer by mention</h3>
            <p>
              You post one message mentioning the agents — yourself, or from a workflow you
              wire up; the pack does not ship one. Each replies because the mention matched.
              Nothing guarantees all of them answer, or in what order. That is how Buzz models
              agents — as members, not cron jobs.
            </p>
          </div>
        </div>
      </section>

      <section className="list-hive" aria-labelledby="submit-heading">
        <div>
          <h2 id="submit-heading">Have a pack?</h2>
          <p>
            The catalog is the repository. The button below opens an issue with the checklist;
            a pull request lands the pack; a fork is the governance. Packs are validated in
            CI — an invalid one fails the build.
          </p>
        </div>
        <div className="cta-comb">
          <a className="button" href={submitPackUrl()}>
            Submit a pack
          </a>
          <Link className="button button-quiet" href="/packs/crossfire-review/">
            See an example
          </Link>
        </div>
      </section>
    </>
  );
}
