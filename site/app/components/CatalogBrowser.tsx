"use client";

import Link from "next/link";
import { useDeferredValue, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { normalize, type Pack } from "@/app/lib/catalog";

/**
 * Assina mudanças de URL feitas fora do React (botão voltar do navegador).
 * `replaceState` não dispara `popstate`, então a escrita própria não realimenta
 * o store — o que é desejado: quem digitou já tem o estado local.
 */
function subscribeToUrl(onChange: () => void) {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

const readSearch = () => window.location.search;
/** No servidor não há URL. Snapshot vazio mantém a hidratação consistente. */
const readSearchOnServer = () => "";

/**
 * Busca e filtro do catálogo, client-side.
 *
 * Três decisões que valem explicar:
 *
 * 1. **`useDeferredValue`** no termo de busca: a digitação atualiza o input na
 *    hora e a lista recalcula em prioridade baixa. Com poucos packs é
 *    imperceptível; com muitos, é a diferença entre digitar liso e digitar travado.
 * 2. **Estado na URL por `history.replaceState`**, não `push`: filtrar não é
 *    navegar, e encher o histórico faz o botão Voltar do navegador parar de
 *    voltar. O link continua compartilhável.
 * 3. **A lista completa é renderizada no servidor** por `CatalogList` (ver
 *    `page.tsx`). Este componente só a filtra. Com JS desligado o catálogo inteiro
 *    continua lá — o que se perde é o filtro, não o conteúdo.
 */
export function CatalogBrowser({ packs, tags }: { packs: Pack[]; tags: string[] }) {
  // A URL é o estado inicial; o estado local só passa a mandar depois que a
  // pessoa mexe. `null` = "ainda não tocado, use a URL". Isso evita semear estado
  // dentro de um efeito, que provoca render em cascata, e mantém o link
  // compartilhável funcionando na primeira pintura.
  const urlSearch = useSyncExternalStore(subscribeToUrl, readSearch, readSearchOnServer);
  const urlParams = useMemo(() => new URLSearchParams(urlSearch), [urlSearch]);

  const [typedQuery, setTypedQuery] = useState<string | null>(null);
  const [pickedTag, setPickedTag] = useState<string | null | undefined>(undefined);

  const query = typedQuery ?? urlParams.get("q") ?? "";
  const activeTag = pickedTag === undefined ? urlParams.get("tag") : pickedTag;

  const setQuery = setTypedQuery;
  const setActiveTag = setPickedTag;
  const deferredQuery = useDeferredValue(query);

  // Escrever na URL é sincronizar com sistema externo — o uso para o qual efeito
  // existe. `replaceState` e não `push`: filtrar não é navegar, e encher o
  // histórico faz o botão Voltar parar de voltar.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (query) params.set("q", query);
    else params.delete("q");
    if (activeTag) params.set("tag", activeTag);
    else params.delete("tag");
    const search = params.toString();
    window.history.replaceState(null, "", search ? `?${search}` : window.location.pathname);
  }, [query, activeTag]);

  // Índice pré-normalizado: normalizar dentro do filtro refaria o trabalho a cada
  // tecla, para cada persona.
  const index = useMemo(
    () =>
      packs.map((pack) => ({
        pack,
        haystack: normalize(
          [
            pack.name,
            pack.description,
            pack.author,
            ...pack.tags,
            ...pack.personas.flatMap((p) => [p.displayName, p.name, p.description]),
            ...pack.teams.map((t) => t.name),
          ].join(" "),
        ),
      })),
    [packs],
  );

  const visible = useMemo(() => {
    const needle = normalize(deferredQuery.trim());
    return index
      .filter(({ pack }) => !activeTag || pack.tags.includes(activeTag))
      .filter(({ haystack }) => !needle || haystack.includes(needle))
      .map(({ pack }) => pack);
  }, [index, deferredQuery, activeTag]);

  const personaCount = visible.reduce((sum, pack) => sum + pack.personas.length, 0);

  return (
    <>
      <div className="tools">
        <label className="search">
          <span className="visually-hidden">Search packs and personas</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search packs, personas, roles"
            autoComplete="off"
            spellCheck={false}
          />
        </label>

        {tags.length > 0 && (
          <div className="filters" role="group" aria-label="Filter by tag">
            {/* aria-pressed é o estado REAL do toggle — data-on é só tinta.
                Sem ele, leitor de tela anuncia um botão comum e o usuário não
                sabe qual filtro está ativo (WCAG 4.1.2). Em forced-colors o
                fundo some, então o CSS também desenha o estado por
                [aria-pressed] em vez de só cor. */}
            <button
              type="button"
              data-on={activeTag === null || undefined}
              aria-pressed={activeTag === null}
              onClick={() => setActiveTag(null)}
            >
              All
            </button>
            {tags.map((tag) => (
              <button
                key={tag}
                type="button"
                data-on={activeTag === tag || undefined}
                aria-pressed={activeTag === tag}
                onClick={() => setActiveTag(activeTag === tag ? null : tag)}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      <p className="results" aria-live="polite">
        {visible.length === packs.length
          ? `${packs.length} pack${packs.length === 1 ? "" : "s"}, ${personaCount} persona${personaCount === 1 ? "" : "s"}`
          : `${visible.length} of ${packs.length} packs · ${personaCount} persona${personaCount === 1 ? "" : "s"}`}
      </p>

      {visible.length === 0 ? (
        <div className="empty">
          <p>Nothing matches that.</p>
          <p>
            Try a shorter term, or{" "}
            <button
              type="button"
              className="linklike"
              onClick={() => {
                setQuery("");
                setActiveTag(null);
              }}
            >
              clear the filters
            </button>
            .
          </p>
        </div>
      ) : (
        <ul className="comb">
          {visible.map((pack) => (
            <PackCell key={pack.name} pack={pack} />
          ))}
        </ul>
      )}
    </>
  );
}

function PackCell({ pack }: { pack: Pack }) {
  const providers = [
    ...new Set(
      pack.personas
        .map((persona) => persona.model?.split(":")[0])
        .filter((provider): provider is string => Boolean(provider)),
    ),
  ];

  return (
    <li className="cell" id={pack.name}>
      <article className="cell-inner">
        <h3 className="cell-title">
          {/* Padrão hitbox: o link cobre a célula inteira, o conteúdo interno não
              captura ponteiro. Evita <a> dentro de <a>, que é HTML inválido. */}
          <Link href={`/packs/${pack.name}/`} className="cell-hit">
            {pack.name}
          </Link>
        </h3>
        <p className="cell-desc">{pack.description}</p>
        <dl className="cell-meta">
          <div>
            <dt>personas</dt>
            <dd>{pack.personas.length}</dd>
          </div>
          <div>
            <dt>teams</dt>
            <dd>{pack.teams.length}</dd>
          </div>
          <div>
            <dt>providers</dt>
            <dd>{providers.length || "—"}</dd>
          </div>
        </dl>
        <ul className="tags">
          {pack.tags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>
      </article>
    </li>
  );
}
