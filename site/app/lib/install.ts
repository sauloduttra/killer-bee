/**
 * O que o botão "instalar" pode honestamente oferecer.
 *
 * Verificado no fonte do Buzz @ `ed4b3e7a`, e o resultado é desconfortável:
 *
 * - **Não existe deep link de instalação.** O handler do SO reconhece exatamente
 *   cinco hosts — `connect`, `join`, `add-community`, `message`, `nostr-bind`
 *   (`desktop/src-tauri/src/deep_link.rs`). Persona e team não estão entre eles.
 * - **Não existe `buzz install`.** O CLI tem só `buzz pack validate` e
 *   `buzz pack inspect`, ambos locais (`crates/buzz-cli/src/lib.rs:1782`).
 *   `.buzzpack` e `pack.lock` existem apenas na especificação.
 * - O que o desktop importa de fato são **snapshots**: `.agent.json` / `.agent.png`
 *   e `.team.json` / `.team.png`.
 *
 * Então o caminho real é: baixar o arquivo e importar no app. Sem glamour, e é o
 * único que funciona. O site diz o número de cliques em vez de escondê-lo — um
 * botão que promete mais do que entrega queima mais confiança que um botão
 * honesto e feio.
 */

/** Passos reais do import, contados na UI do Buzz Desktop. */
export const IMPORT_STEPS = [
  "Download the file below.",
  "In Buzz Desktop, open the Agents section in the sidebar.",
  'Click "New agent" (or "New team"), then "Import".',
  "Pick the file, review the preview, and confirm.",
] as const;

/** Quatro cliques no app mais a seleção no diálogo do sistema operacional. */
export const IMPORT_CLICK_COUNT = "4 clicks plus the OS file picker";

/** Arrastar e soltar sobre a seção Agents pula dois cliques. */
export const IMPORT_SHORTCUT =
  "Dragging the file onto the Agents section skips two of those clicks.";

/**
 * O que ainda falta depois de importar — `import.rs` grava
 * `start_on_app_launch: false`, `agent_command` vazio e `env_vars` vazio.
 */
export const AFTER_IMPORT = [
  "The agent exists but is not running yet.",
  "It needs provider credentials from the app's global settings.",
  'Adding it to a channel is a separate action in the agent\'s profile panel.',
] as const;

export function agentFileName(personaName: string, extension: "json" | "png"): string {
  return `${personaName}.agent.${extension}`;
}

export function teamFileName(teamId: string, extension: "json" | "png"): string {
  return `${teamId}.team.${extension}`;
}

/** Comando copiável para quem prefere gerar o arquivo a partir da fonte. */
export function buildCommand(packName: string): string {
  return `uv run python -m killerbee build packs/${packName}`;
}

const REPO = "https://github.com/killerbee-buzz/killerbee-buzz";

/** Issue pré-preenchida para submissão de pack. */
export function submitPackUrl(): string {
  const body = [
    "## Pack",
    "",
    "Repository or archive:",
    "",
    "## Checklist",
    "",
    "- [ ] `killerbee validate` passes",
    "- [ ] Every persona has a license and an author",
    "- [ ] No credentials, vendor data, or third-party content in the pack",
    "- [ ] System prompts are the ones actually used, not a summary",
  ].join("\n");
  return `${REPO}/issues/new?title=${encodeURIComponent("Add pack: ")}&body=${encodeURIComponent(body)}`;
}

export const REPO_URL = REPO;
