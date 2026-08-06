/**
 * Leitura do catálogo em tempo de build.
 *
 * O JSON é gerado por `uv run python -m killerbee catalog`, que valida cada pack
 * antes de emitir — se um pack estiver quebrado, o catálogo não é escrito e o
 * build do site falha por falta de dado, não por render torto.
 *
 * Import estático de propósito: o catálogo é conteúdo, não dado remoto. O site é
 * export estático puro, então isto vira HTML no build e o visitante não paga
 * requisição nenhuma. Quando o catálogo passar de ~200 packs isso vira peso morto
 * no bundle — está registrado como B-06 no backlog, com o índice comprimido como
 * saída. Hoje são 8 KB; otimizar agora seria resolver um problema que não temos.
 */
import catalogJson from "@/data/catalog.json";

export type Threshold = "low" | "medium" | "high";
export type Persistence = "short" | "medium" | "long";
export type Propagation = "low" | "medium" | "high";

export interface ScutellataProfile {
  threshold: Threshold;
  /** Paralelismo nativo do Buzz: 1..=32. */
  recruitment: number;
  persistence: Persistence;
  propagation: Propagation;
}

export interface Persona {
  name: string;
  displayName: string;
  description: string;
  /** O prompt inteiro, sem truncagem. Transparência é o produto. */
  systemPrompt: string;
  model: string | null;
  runtime: string | null;
  profile: ScutellataProfile;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  instructions: string;
  members: string[];
}

export interface Pack {
  name: string;
  version: string;
  description: string;
  author: string;
  license: string;
  tags: string[];
  buzzCommit: string;
  personas: Persona[];
  teams: Team[];
}

interface Catalog {
  generatedFrom: string;
  packs: Pack[];
}

const catalog = catalogJson as Catalog;

export const packs: Pack[] = catalog.packs;

export function getPack(name: string): Pack | undefined {
  return packs.find((pack) => pack.name === name);
}

export function getPersona(packName: string, personaName: string) {
  const pack = getPack(packName);
  if (!pack) return undefined;
  const persona = pack.personas.find((p) => p.name === personaName);
  if (!persona) return undefined;
  return { pack, persona };
}

/** Todos os pares (pack, persona) — alimenta `generateStaticParams`. */
export function allPersonaRoutes(): { pack: string; persona: string }[] {
  return packs.flatMap((pack) =>
    pack.personas.map((persona) => ({ pack: pack.name, persona: persona.name })),
  );
}

/** União ordenada de todas as tags, para os filtros do catálogo. */
export function allTags(): string[] {
  return [...new Set(packs.flatMap((pack) => pack.tags))].sort();
}

/**
 * Divide `"provider:model-id"` no primeiro `:`, como o upstream faz em
 * `crates/buzz-persona/src/persona.rs:324`. Um `model` sem `:` é model-id sem
 * provider — o mesmo comportamento do emissor.
 */
export function splitModel(model: string | null): {
  provider: string | null;
  modelId: string | null;
} {
  if (!model) return { provider: null, modelId: null };
  const index = model.indexOf(":");
  if (index === -1) return { provider: null, modelId: model };
  return {
    provider: model.slice(0, index) || null,
    modelId: model.slice(index + 1) || null,
  };
}

/**
 * Normalização para busca tolerante a acento e caixa.
 *
 * `NFD` separa a letra do diacrítico, e a faixa `̀-ͯ` remove os
 * diacríticos combinantes — assim "análise" casa com "analise". Sem isto, um
 * catálogo em português falha silenciosamente para quem digita sem acento, que é
 * a maioria.
 */
export function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}
