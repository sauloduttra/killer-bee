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

/**
 * Passos reais do import, contados na UI do Buzz Desktop 0.5.5 **em execução**
 * (não lidos no fonte): sidebar → Agents → card `+` → "Import" → seletor do SO →
 * dialog de preview → "Import".
 *
 * O card não se chama "New agent": é um card `+` que abre um menu de três
 * entradas — "Create agent", "Discover agents", "Import". Em teams o menu tem
 * duas: "Create team" e "Import".
 */
export const IMPORT_STEPS = [
  "Download the file below.",
  "In Buzz Desktop, open the Agents section in the sidebar.",
  'Click the "+" card, then "Import".',
  "Pick the file, review the preview, and confirm.",
] as const;

/** Quatro cliques no app mais a seleção no diálogo do sistema operacional. */
export const IMPORT_CLICK_COUNT = "4 clicks plus the OS file picker";

/**
 * Não há atalho. A versão anterior desta constante prometia que arrastar o
 * arquivo sobre a seção Agents pulava dois cliques — **é falso**, e o site
 * chegou a publicar isso.
 *
 * Duas fontes independentes concordam: `desktop/src-tauri/tauri.conf.json:27`
 * traz `"dragDropEnabled": false`, e a enumeração completa de `onDrop=` em
 * `desktop/src` devolve dez handlers — avatar, backup, chave Nostr e composer de
 * mensagem — nenhum na seção Agents nem em `AgentSnapshotImportDialog.tsx`.
 * A enumeração devolveu resultados, então a ausência é confirmada, não coleta
 * falha (D-014).
 */
export const IMPORT_SHORTCUT =
  "There is no drag-and-drop shortcut: the Agents section has no drop target.";

/**
 * O que ainda falta depois de importar. `import.rs:610` grava `agent_command`
 * vazio, `:623` `env_vars` vazio e `:624` `start_on_app_launch: false` — e os
 * três foram **conferidos no app rodando**: o painel de perfil do agente
 * importado mostra `Status: STOPPED`, `Start on launch: No` e a aba Channels
 * vazia, com "Add this agent to a channel".
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

/**
 * href de download com o basePath do deploy.
 *
 * O Next só prefixa `basePath` em `next/link` e nos assets que ele mesmo emite;
 * `<a href="/downloads/...">` cru sai como está. No GitHub Pages de projeto
 * (servido sob `/<repo>/`) isso fazia TODOS os botões de download — o único
 * botão do site — retornarem 404. Localmente o basePath é vazio e tudo
 * funciona, que é o que tornava a falha invisível até o deploy.
 * Auditoria 2026-08-06, achado CONFIRMED; teste de integridade de links em
 * rendered-html.test.mjs impede a volta.
 */
export function downloadHref(packName: string, fileName: string): string {
  return `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/downloads/${packName}/${fileName}`;
}

/** Comando copiável para quem prefere gerar o arquivo a partir da fonte. */
export function buildCommand(packName: string): string {
  return `uv run python -m killerbee build packs/${packName}`;
}

/**
 * Remote real, criado em 2026-08-06 com autorização do Saulo — a suposição de
 * D-020 virou fato. O valor anterior ("killerbee-buzz/killerbee-buzz") era um
 * placeholder órfão que não apontava para conta de ninguém do projeto.
 */
const REPO = "https://github.com/sauloduttra/killer-bee";

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
