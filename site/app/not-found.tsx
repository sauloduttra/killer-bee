import Link from "next/link";

/**
 * Tela vazia é convite para agir, não lamento — e não pede desculpa.
 */
export default function NotFound() {
  return (
    <article className="page">
      <header className="page-head">
        <h1>No pack at that address</h1>
        <p className="lede">
          The catalog is generated from the repository at build time, so a missing page means
          the pack is not in the repository — not that something broke.
        </p>
      </header>
      <p>
        <Link className="button" href="/">
          Back to the catalog
        </Link>
      </p>
    </article>
  );
}
