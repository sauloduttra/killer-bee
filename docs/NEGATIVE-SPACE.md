# Espaço negativo — toda afirmação de ausência, com o método junto

**Commit:** `ed4b3e7afafb` · **Gerado por** `scripts/evidence_to_docs.py` a partir
de [`evidence/neg_rows.json`](evidence/neg_rows.json) — edite lá, não aqui.

Afirmação negativa é a mais frágil e a mais valiosa. Sem o método de busca
junto, é ausência de evidência vendida como evidência de ausência. Cada
entrada carrega: o que foi buscado, quantos falsos positivos foram
descartados, e **o que a tornaria falsa**.

Placar da re-verificação adversarial (2026-08-06): 60 confirmadas · 5 parciais · **3 refutadas** — as refutadas estavam publicadas e foram corrigidas ([D-035](DECISIONS.md)). O detector funcionando é a notícia boa.

---

## [n-33] ❌ REFUTADA — nosso doc estava errado

**Afirmação:** There is no drag-and-drop target for snapshot import: the Agents section has no drop target, dragDropEnabled is false, and no onDrop handler exists in UnifiedAgentsSection.tsx or AgentSnapshotImportDialog.tsx.

**Evidência:** `desktop/src/features/agents/ui/UnifiedAgentsSection.tsx:105-111` · `desktop/src/features/agents/ui/UnifiedAgentsSection.tsx:126-131` · `desktop/src/features/agents/ui/UnifiedAgentsSection.tsx:132-137` · `desktop/src/shared/hooks/useFileImportZone.ts:29-36` · `desktop/src/shared/hooks/useFileImportZone.ts:8-11`

**Método de busca:**

- `Grep 'onDrop' desktop/src (16 hits)`
- `Grep -iE 'onDrop|dragover|drop' UnifiedAgentsSection.tsx and AgentSnapshotImportDialog.tsx`
- `Grep 'dragDropEnabled' desktop/`

**Falsos positivos:** AgentSnapshotImportDialog.tsx still has no drop handler (dialog is preview/confirm only); the drop target lives on the section, which then routes to onImportSnapshotFile.

**O que a tornaria falsa:** n/a — claim refuted; the falsifying code exists at this commit.

**Nota:** The upstream added a shared useFileImportZone hook: the Agents section root spreads dropHandlers and renders a 'Drop .agent.json or .agent.png to import' overlay; AgentsView.tsx also carries a .team.json/.team.png input. tauri.conf.json:27 still sets dragDropEnabled:false, but that disables Tauri's native drag handler, which is exactly what lets these DOM onDrop events fire in the webview. Our docs (PROTOCOL-NOTES 363-364, 760-767; HANDOFF 316-318) are stale on this point.


---

## [n-34] ❌ REFUTADA — nosso doc estava errado

**Afirmação:** The Blossom-hosted .agent.png (via PersonaShareDialog 'Copy link') is the ONLY installable artifact that already has a public URL today — no other installable artifact is publicly URL-addressable.

**Evidência:** `desktop/src/features/agents/ui/TeamShareDialog.tsx:6` · `desktop/src/features/agents/ui/TeamShareDialog.tsx:30-39` · `desktop/src/features/agents/ui/PersonaShareDialog.tsx:354-361` · `desktop/src-tauri/src/commands/team_snapshot.rs:391` · `desktop/tests/e2e/team-snapshot.spec.ts:351`

**Método de busca:**

- `Grep 'PersonaShareDialog|agent\.png|Copy link' (whole repo)`
- `Read TeamShareDialog.tsx (all), PersonaShareDialog.tsx:140-400`
- `Grep 'copy|link' desktop/tests/e2e/team-snapshot.spec.ts`
- `Grep 'function uploadMediaBytes' desktop/src — invokes upload_media_bytes returning BlobDescriptor (Blossom)`

**Falsos positivos:** n/a — this is a refutation.

**O que a tornaria falsa:** n/a.

**Nota:** The claim is no longer true as stated: TeamShareDialog wraps the SAME SnapshotShareDialog (exported from PersonaShareDialog.tsx) with snapshotKind="team", and its Copy link path uploads the .team.png via uploadMediaBytes and copies the public Blossom URL (PersonaShareDialog.tsx:338-373). The .team.png is installable via confirm_team_snapshot_import (desktop/src-tauri/src/lib.rs:823, commands/team_snapshot.rs:500) and its link flow is pinned by e2e tests (team-snapshot.spec.ts:314-457). So the .agent.png is not the ONLY URL-addressable installable artifact — the team snapshot .team.png is a second one via the identical mechanism. If the original doc intended 'the snapshot-PNG family shared f…


---

## [n-38] ❌ REFUTADA — nosso doc estava errado

**Afirmação:** crates/buzz-acp/src/ contains zero mentions of anthropic, openai, or openrouter — buzz-acp is genuinely provider-agnostic (it spawns an arbitrary binary and speaks ACP).

**Evidência:** `crates/buzz-acp/src/usage.rs:99-102` · `crates/buzz-acp/src/setup_mode.rs:711-712` · `crates/buzz-acp/src/setup_mode.rs:744-746` · `crates/buzz-acp/src/acp.rs:4434`

**Método de busca:**

- `Grep 'anthropic|openai|openrouter' -i in crates/buzz-acp/src — 13 hits`
- `Verified context of each hit (production doc comment vs #[cfg(test)])`

**Falsos positivos:** openrouter alone genuinely has 0 hits in buzz-acp/src.

**O que a tornaria falsa:** n/a — the thing claimed absent was found.

**Nota:** The literal 'zero mentions' claim is false at this commit: 1 production doc-comment mention of Anthropic (usage.rs:102) plus ~12 mentions of ANTHROPIC_API_KEY/OPENAI_API_KEY/'openai' inside #[cfg(test)] modules (setup_mode.rs tests around 661-978, acp.rs:4434). The SUBSTANTIVE point survives: none of these are provider SDK integrations — buzz-acp still spawns an arbitrary agent binary and passes env keys through opaquely; the strings are setup-nudge/usage-accounting copy and test fixtures. Only 'openrouter' is truly at zero.


---

## [n-11] ⚠️ parcial — precisa de nuance

**Afirmação:** There is no is_addressable function in the Buzz code; the code uses 'NIP-33 / parameterized replaceable' terminology instead.

**Evidência:** `crates/buzz-sdk/src/builders.rs:2179-2180` · `crates/buzz-core/src/kind.rs:64` · `crates/buzz-core/src/kind.rs:451`

**Método de busca:**

- `Grep 'fn is_addressable' repo-wide — 0 hits`
- `Grep 'is_addressable|isAddressable' repo-wide — 2 hits (both builders.rs:2179-2180)`
- `Grep 'parameterized replaceable|NIP-33' -i in crates/ — 20+ hits`

**Falsos positivos:** The 2 is_addressable hits are a local `let` binding inside build_delete_addressable, not a function definition.

**O que a tornaria falsa:** A future `fn is_addressable` (or method) being extracted, e.g. from build_delete_addressable, or exposed by buzz-core kind helpers.

**Nota:** No FUNCTION named is_addressable exists — that half is correct, and the NIP-33/parameterized-replaceable terminology claim is confirmed. But the identifier `is_addressable` DOES exist as a local variable in buzz-sdk/src/builders.rs:2179, so a blanket 'is_addressable does not appear in the code' reading would be wrong.


---

## [n-16] ⚠️ parcial — precisa de nuance

**Afirmação:** Any unknown key in persona (.persona.md) YAML frontmatter is a fatal parse error (deny_unknown_fields); there is no free-form field, no `metadata`, no `extra`, no `flatten` in the persona frontmatter.

**Evidência:** `crates/buzz-persona/src/persona.rs:174-175` · `crates/buzz-persona/src/persona.rs:172-173` · `crates/buzz-persona/src/persona.rs:68-69`

**Método de busca:**

- `Grep 'deny_unknown_fields|flatten|metadata|extra' crates/buzz-persona/src/persona.rs`
- `Read persona.rs:40-198 (RespondTo, McpServerConfig, Hooks, Frontmatter structs)`

**Falsos positivos:** 'metadata' hit at persona.rs:264 is std::fs::metadata (file size check), not a frontmatter field.

**O que a tornaria falsa:** A #[serde(flatten)] catch-all map or a metadata/extra field added to Frontmatter; or deny_unknown_fields removed.

**Nota:** Confirmed at the top level: Frontmatter (persona.rs:176-198) has deny_unknown_fields, no flatten/metadata/extra field, and Hooks (persona.rs:83) is also strict. Nuance: nested structs RespondTo (persona.rs:51-52) and McpServerConfig (persona.rs:68-69) do NOT carry deny_unknown_fields, so an unknown key nested inside `triggers:` or an `mcp_servers:` entry is silently ignored, not fatal. 'Any unknown key' is therefore slightly overbroad; top-level keys are fatal.


---

## [n-41] ⚠️ parcial — precisa de nuance

**Afirmação:** .env.example contains no LLM variables at all — no ANTHROPIC, no OPENAI, no OPENROUTER; they are documented only in crates/buzz-agent/README.md.

**Evidência:** `.env.example:166-168` · `crates/buzz-agent/README.md:139-149` · `crates/buzz-acp/README.md:1`

**Método de busca:**

- `Read .env.example (254 lines) and deploy/compose/.env.example (53 lines) in full`
- `Grep 'ANTHROPIC|OPENAI|OPENROUTER' in .env.example — 0 hits`
- `Grep 'ANTHROPIC_API_KEY|OPENROUTER_API_KEY|OPENAI_COMPAT_API_KEY' repo-wide — 73 files`

**Falsos positivos:** Core absence holds: neither .env.example contains any ANTHROPIC/OPENAI/OPENROUTER variable.

**O que a tornaria falsa:** An ANTHROPIC_/OPENAI_/OPENROUTER_ line added to either .env.example.

**Nota:** Two clauses need tightening: (1) 'no LLM variables at all' overreaches — .env.example line 168 documents BUZZ_ACP_MODEL ('Desired LLM model ID'), an LLM-model variable, though not a provider credential; (2) 'documented only in crates/buzz-agent/README.md' is false — the provider keys appear in 73 files including crates/buzz-acp/README.md, desktop readiness/env-var code, and benchmark configs. crates/buzz-agent/README.md is merely the canonical reference table. The headline negative (no provider API-key vars in .env.example) is confirmed.


---

## [n-50] ⚠️ parcial — precisa de nuance

**Afirmação:** The desktop Agents card is not called 'New agent' — it is a '+' card opening a three-entry menu (Create agent / Discover agents / Import); for teams, two entries (Create team / Import).

**Evidência:** `desktop/src/features/agents/ui/UnifiedAgentsSection.tsx:452` · `desktop/src/features/agents/ui/UnifiedAgentsSection.tsx:458-470` · `desktop/src/features/agents/ui/TeamsSection.tsx:209-214` · `desktop/src/features/agents/ui/CreateIdentityCard.tsx:31-35`

**Método de busca:**

- `Grep '"New agent"' in desktop/src — 4 hits inspected`
- `Grep 'Discover agents|Create agent|Create team' in desktop/src`
- `Read CreateIdentityCard.tsx in full — label prop optional and NOT passed by either call site`

**Falsos positivos:** AddCustomHarnessDialog.tsx / addCustomHarness.ts 'New agent' mentions are comments.

**O que a tornaria falsa:** The call sites passing a visible `label` prop, or the aria-label being renamed.

**Nota:** Visually correct and menu contents exactly match (3 entries for agents, 2 for teams; the card renders only a Plus icon, no visible text). But 'not called New agent' is false at the accessibility layer: the card's aria-label IS 'New agent' (test id 'new-agent-card'; teams: 'New team'), and personaLibraryCopy.ts:6 sets createNew: "New agent". Screen readers and e2e selectors do call it 'New agent'.


---

## [n-57] ⚠️ parcial — precisa de nuance

**Afirmação:** Snapshot import sniffs magic bytes and ignores the file extension entirely.

**Evidência:** `desktop/src-tauri/src/commands/personas/snapshot/import.rs:213` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:217-219` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:233` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:36-39` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:388-389`

**Método de busca:**

- `Read parse_snapshot_payload_from_bytes (import.rs:213-281) and preview_agent_snapshot_import (371-397)`
- `grep 'reject_legacy_persona_filename|file_name' across snapshot code including team_snapshot.rs`

**Falsos positivos:** team snapshot preview takes `_file_name` (unused, team_snapshot.rs:460); confirm_agent_snapshot_import receives no file_name at all — those paths truly ignore the name.

**O que a tornaria falsa:** Removal of reject_legacy_persona_filename from the preview path would make 'entirely' fully accurate; conversely, format branching on extension would refute the sniffing half.

**Nota:** Format detection is genuinely magic-bytes-only (PNG signature, else JSON; the code comment says so verbatim). BUT the agent-import preview first rejects files by name suffix (.persona.md/.persona.json/.persona.png/.zip) before decoding — a valid snapshot named foo.persona.json is refused because of its extension. 'Extension ignored entirely' is therefore overstated for the preview path; sniffing claim itself holds.


---

## [n-01] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The .buzzpack pack format described in PERSONA_PACK_SPEC.md (.buzzpack archives, `buzz install`, pack.lock, ~/.buzz/packs/ discovery, 'Phase 3: App Store UI') is not implemented anywhere in the Buzz code — it exists only in the spec.

**Evidência:** `crates/buzz-persona/PERSONA_PACK_SPEC.md:849` · `crates/buzz-cli/src/lib.rs:1932-1933` · `crates/buzz-cli/src/lib.rs:2272`

**Método de busca:**

- `Grep -i 'buzzpack' (whole repo)`
- `Grep -i 'pack\.lock' (whole repo)`
- `Grep -i '\.buzz/packs|buzz.?install|BUZZ_PACK|packs_dir|pack_discovery' (whole repo)`
- `Grep -i 'App Store' (whole repo)`
- `Grep -i 'install' crates/buzz-cli/src`
- `Grep -i 'zip|archive|unpack|extract' crates/buzz-persona/src`

**Falsos positivos:** buzzpack: 8 hits, all in PERSONA_PACK_SPEC.md. pack.lock: 5 hits, all spec. 'buzz install': deploy/charts YAML comments (Helm install of the relay) and desktop agent_discovery.rs / windows_install.rs 'buzz-install-<slug>.ps1' temp script names for installing external agents (codex/claude/goose) — none are pack installs. 'App Store': spec:900 plus SECURITY.md 'desktop app stores nsec'. buzz-cli 'i…

**O que a tornaria falsa:** A future buzz-cli subcommand named 'install' (or 'pack install'), any code reading '~/.buzz/packs', a .buzzpack/zip reader in buzz-persona, or code writing/reading a pack.lock file.

**Nota:** buzz pack has exactly two subcommands (validate, inspect), both taking an explicit local directory path.


---

## [n-02] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The CLI's two pack commands (`buzz pack validate`, `buzz pack inspect`) have no --json output flag — output is human text only.

**Evidência:** `crates/buzz-cli/src/lib.rs:1782-1793` · `crates/buzz-cli/src/commands/pack.rs:66-68` · `crates/buzz-cli/src/lib.rs:1929-1933`

**Método de busca:**

- `Grep 'json' -i in crates/buzz-cli/src (all hits reviewed)`
- `Grep 'Pack|pack' in crates/buzz-cli/src/lib.rs`
- `Read PackCmd enum (lib.rs:1780-1793) and commands/pack.rs in full`

**Falsos positivos:** A `json: bool` flag exists but belongs to `buzz mem ls` (lib.rs:1708-1710), not pack. A global `--format json|compact` exists (lib.rs:93-95) but the pack dispatch (lib.rs:1930-1933) passes only `path` to cmd_validate/cmd_inspect — cli.format is never read on the pack path.

**O que a tornaria falsa:** Adding a `json: bool` field to PackCmd::Validate/Inspect, or wiring cli.format into commands::pack::cmd_validate/cmd_inspect.

**Nota:** Nuance worth keeping in docs: the CLI does have a top-level --format flag defaulting to json for relay read commands; it simply does not apply to pack output.


---

## [n-03] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** There is no `buzz install`, no `buzz pack publish`, and no persona/team command group in the buzz CLI; none of the 22 command groups is persona/team-related.

**Evidência:** `crates/buzz-cli/src/lib.rs:176-243` · `crates/buzz-cli/src/lib.rs:1782-1793` · `crates/buzz-cli/src/lib.rs:237` · `crates/buzz-cli/src/commands/pack.rs:1-3`

**Método de busca:**

- `Grep '"install"|"publish"|"persona"|"team"' crates/buzz-cli/src (content)`
- `Grep -i 'install' crates/buzz-cli/src`
- `Read lib.rs:176-243 (full Cmd enum), lib.rs:1782-1793 (full PackCmd enum), main.rs`

**Falsos positivos:** 4 'install' hits are rustls CryptoProvider install_default (lib.rs:29-39). 'publish' hits (lib.rs:964, 2222) are SocialCmd::PublishNote — NIP-01 text note, not pack publish. Both discarded.

**O que a tornaria falsa:** A future commit adding a Cmd::Install/Cmd::Persona/Cmd::Team variant to the enum at lib.rs:176, or a Publish arm to PackCmd at lib.rs:1782.

**Nota:** Cmd enum has exactly 22 variants (Agents..Moderation); none named persona/team; PackCmd has only Validate and Inspect. Nuance: the Pack group IS persona-pack tooling (local validate/inspect only), so 'none is persona/team-related' holds only in the sense of persona/team lifecycle management — worth tightening the wording in our doc.


---

## [n-04] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** load_pack(pack_dir) requires an explicit path — there is no directory scan, no environment variable, and no pack discovery mechanism; there is no 'right place' where copying a pack file installs a persona.

**Evidência:** `crates/buzz-persona/src/pack.rs:125` · `crates/buzz-persona/src/resolve.rs:186` · `crates/buzz-cli/src/commands/pack.rs:15-18`

**Método de busca:**

- `Grep 'env::var|std::env|read_dir|walkdir' crates/buzz-persona/src`
- `Grep 'BUZZ_.*PACK|PACK.*DIR|persona_pack_dir|--pack' crates/`
- `Grep 'buzz-persona' **/Cargo.toml (consumers: buzz-cli, buzz-acp, desktop)`
- `Grep 'pub async fn|tauri::command' desktop/src-tauri/src/commands/teams.rs`
- `Grep 'import|pack|team' desktop/src-tauri/src/lib.rs (registered command list)`
- `Grep 'read_dir|scan|watch|load_teams_from' desktop/src-tauri/src/managed_agents/teams.rs`

**Falsos positivos:** read_dir hits in buzz-persona (pack.rs:272, validate.rs:379) scan the skills/ subdirectory INSIDE an already-given pack dir, not a pack-discovery location. BUZZ_GIT_PACK_* env vars (relay config.rs:768-786) are the git pack cache, unrelated. Desktop teams load from a JSON store (teams_store_path) plus built-ins; TeamRecord.source_dir comes from legacy migration, and no Tauri command imports a pac…

**O que a tornaria falsa:** An env var like BUZZ_PACKS_DIR, a loop scanning a packs directory to call load_pack, or a desktop/CLI command that discovers packs from a fixed filesystem location.


---

## [n-05] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** buzz-acp declares the buzz-persona dependency in its Cargo.toml but does not use it on any line; the example README states persona-pack runtime integration 'is not currently implemented'.

**Evidência:** `crates/buzz-acp/Cargo.toml:22` · `examples/meadow-core/README.md:25`

**Método de busca:**

- `Grep 'buzz_persona|buzz-persona' in crates/buzz-acp (whole crate) — 1 hit: Cargo.toml:22`
- `Grep 'persona' -i in crates/buzz-acp/src — ~80 hits inspected`

**Falsos positivos:** All src hits are local identifiers (persona_env_vars, persona CODEX_CONFIG merge comments, [System] persona prompt framing) — none reference the buzz_persona crate path or re-export it.

**O que a tornaria falsa:** Any `use buzz_persona` / `buzz_persona::` occurrence in crates/buzz-acp/src, or removal of the dead Cargo.toml dependency.

**Nota:** The dependency is declared and entirely unused in code at this commit.


---

## [n-06] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Persona discovery between communities does not exist — no public, cross-community, web catalog; the live desktop catalog is per-community, inside the app.

**Evidência:** `docs/nips/NIP-AP.md:279` · `docs/nips/NIP-AP.md:295` · `crates/buzz-persona/PERSONA_PACK_SPEC.md:1132-1134`

**Método de busca:**

- `Grep -i 'catalog' repo-wide (60+ files) and specifically in web/ (0 hits)`
- `Grep -i 'marketplace|persona registry|pack registry' crates/ (2 hits)`
- `Grep -i 'cross-community|between communities' repo-wide (30 hits inspected)`

**Falsos positivos:** Catalog hits are theme catalogs (mobile), harness catalogs (desktop settings), and the per-community NIP-AP shared-persona catalog. 'marketplace' appears only under PERSONA_PACK_SPEC.md 'Future Work' and a manifest comment about foreign OPS fields. All 'cross-community' hits are isolation-fence code (S1 tenancy), not discovery.

**O que a tornaria falsa:** A web/ route, admin-web page, or separate service listing personas across relays/communities, or a NIP-AP section defining cross-relay persona discovery.

**Nota:** Sharing scope tops out at community-wide fan-out on one relay; web/ has zero catalog code. The only mention of a marketplace is explicitly future work.


---

## [n-07] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** No workflow action invokes an agent: the ActionDef enum is closed with exactly 7 variants, and there is no spawn_agent, invoke_persona, run_team, or any equivalent action.

**Evidência:** `crates/buzz-workflow/src/schema.rs:90-92` · `crates/buzz-workflow/src/schema.rs:92-147`

**Método de busca:**

- `Grep 'enum ActionDef' (whole repo) — single definition at schema.rs:92`
- `Read schema.rs:92-147 — variants: SendMessage, SendDm, SetChannelTopic, AddReaction, CallWebhook, RequestApproval, Delay (7 exactly)`
- `Grep 'spawn_agent|invoke_persona|run_team|invoke_agent|run_agent|SpawnAgent|InvokePersona|RunTeam' (whole repo)`
- `Grep -i 'agent' crates/buzz-workflow/src — 0 hits`

**Falsos positivos:** All spawn_agent/run_agent hits are desktop process management (spawn_agent_child in managed_agents/runtime.rs, run_agent_models_command) — agent-subprocess lifecycle, not workflow actions. The workflow crate itself never mentions 'agent'.

**O que a tornaria falsa:** A new ActionDef variant (e.g. InvokeAgent/RunPersona) in schema.rs, or executor.rs dispatching any step to an agent runtime.


---

## [n-08] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The workflow actions send_dm and set_channel_topic are not implemented — both return NotImplemented.

**Evidência:** `crates/buzz-workflow/src/executor.rs:580-583` · `crates/buzz-workflow/src/executor.rs:586-589` · `desktop/src/features/workflows/ui/WorkflowStepCard.tsx:20-21`

**Método de busca:**

- `Grep 'send_dm|set_channel_topic|SendDm|SetChannelTopic' repo-wide — all 40+ hits reviewed`

**Falsos positivos:** desktop `set_channel_topic` Tauri command and CLI cmd_set_channel_topic are the interactive channel-topic feature, not the workflow executor action; schema.rs defines the action shape only.

**O que a tornaria falsa:** Replacing the two executor.rs match arms with real send/publish implementations.

**Nota:** ARCHITECTURE.md:827 documents the same stub status (WF-07).


---

## [n-09] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Agent addressing by mention carries no delivery or ordering guarantee — nothing guarantees that mentioned agents respond, nor in what order.

**Evidência:** `crates/buzz-acp/src/relay.rs:3167` · `crates/buzz-acp/src/relay.rs:3193-3196` · `crates/buzz-acp/src/relay.rs:3198-3199` · `docs/nips/NIP-AO.md:206-208`

**Método de busca:**

- `Grep 'mention' crates/buzz-acp/src (relay.rs, queue.rs read in context)`
- `Grep -i 'delivery guarantee|guaranteed|ordering|ack|barrier|best-effort' crates/buzz-acp/src and docs/nips`

**Falsos positivos:** All 'guarantee'/'ordering' hits in buzz-acp are per-agent internals (turn deadlines, pool cleanup, reaction add/remove ordering, prompt section ordering) — none coordinates delivery or response order across mentioned agents.

**O que a tornaria falsa:** A mention-ack/receipt event kind, a relay-side pending-mention queue with redelivery, or a dispatcher serializing responses of multiple mentioned agents.

**Nota:** A mention is just a `#p` filter on each agent's own WebSocket REQ subscription; delivery is subscription fan-out with reconnect-skew catch-up, and each mentioned agent responds (or not) independently.


---

## [n-10] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** KIND_AUTH (22242), KIND_NOSTR_IDENTITY_BINDING (24243) and KIND_PUSH_LEASE (30350) are left out of the ALL_KINDS export in crates/buzz-core/src/kind.rs.

**Evidência:** `crates/buzz-core/src/kind.rs:77-109` · `crates/buzz-core/src/kind.rs:635-766`

**Método de busca:**

- `Grep 'ALL_KINDS|KIND_AUTH|KIND_NOSTR_IDENTITY_BINDING|KIND_PUSH_LEASE|SHARED_GATED_KINDS' crates/buzz-core/src/kind.rs`
- `awk 'NR>=635 && NR<=766' kind.rs | grep -E 'KIND_AUTH|KIND_NOSTR_IDENTITY_BINDING|KIND_PUSH_LEASE' — exit 1 (0 hits)`
- `awk 'NR>=635 && NR<=766' kind.rs | grep -c 'KIND_|RELAY_ADMIN_' — 130 entries`

**Falsos positivos:** KIND_PUSH_LEASE at kind.rs:131 is inside AUTHOR_ONLY_KINDS (lines 129-133), not ALL_KINDS. KIND_HTTP_AUTH at line 701 of the list is a different constant (27235), not KIND_AUTH.

**O que a tornaria falsa:** Adding any of the three constants to the ALL_KINDS slice (lines 635-766), which currently holds exactly 130 entries.


---

## [n-12] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** No kind range reserved for third parties: relay ingest uses a strict allowlist (required_scope_for_kind falls through to 'restricted: unknown event kind'); any unregistered kind is rejected.

**Evidência:** `crates/buzz-relay/src/handlers/ingest.rs:210` · `crates/buzz-relay/src/handlers/ingest.rs:319` · `crates/buzz-relay/src/handlers/ingest.rs:1884-1887`

**Método de busca:**

- `Grep 'required_scope_for_kind|unknown event kind' crates/`
- `Read full match ingest.rs:211-321 checking for range arms`
- `Grep -i 'extra_kinds|allowed_kinds|custom_kind|kind_allowlist|additional_kinds' crates/`

**Falsos positivos:** One hit: buzz-acp config test 'test_mentions_mode_custom_kinds' — agent-side subscription kinds, not relay ingest. Match guards (is_moderation_command_kind, relay-admin kinds) are fixed code lists, not ranges or config.

**O que a tornaria falsa:** A wildcard/range arm (e.g. 30000..=39999) in required_scope_for_kind, or a config/env-driven extension of the accepted-kind set.

**Nota:** The allowlist is hardcoded; adding a kind requires a source change (CONTRIBUTING.md:435 'Register the kind's required scope'). Test at ingest.rs:3393 asserts kind 99999 is rejected.


---

## [n-13] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Kind 30176 (team) is deliberately NOT a member of SHARED_GATED_KINDS — teams are owner-private and cannot be opted into the shared catalog gate.

**Evidência:** `crates/buzz-core/src/kind.rs:212-214` · `crates/buzz-core/src/kind.rs:215` · `crates/buzz-core/src/kind.rs:282`

**Método de busca:**

- `Grep 'SHARED_GATED_KINDS' crates/buzz-core/src/kind.rs`
- `Read kind.rs:200-224`

**Falsos positivos:** None — the slice has exactly two members (30175, 30178) and an explicit code comment naming the exclusion as deliberate.

**O que a tornaria falsa:** KIND_TEAM added to SHARED_GATED_KINDS, or a separate owner-private read gate for 30176 (the comment calls that 'a separate change').

**Nota:** Nuance: the comment says 30176 'needs owner-private read semantics instead, which is a separate change' — i.e. that owner-private gate is desired but not yet implemented; today 30176 is simply not shared-gated.


---

## [n-14] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** NIP-98 is implemented (crates/buzz-auth/src/nip98.rs, kind 27235) but is not announced in the relay's supported_nips list.

**Evidência:** `crates/buzz-auth/src/nip98.rs:1` · `crates/buzz-relay/src/nip11.rs:15` · `crates/buzz-relay/src/nip11.rs:153-156`

**Método de busca:**

- `Grep 'supported_nips' repo-wide — all hits reviewed`
- `Grep '27235' in crates/buzz-auth`
- `Grep 'supported_nips|98' in crates/buzz-pair-relay/src — 0 hits`

**Falsos positivos:** The only runtime mutation of supported_nips is the conditional push of NIP 43 (nip11.rs:154-156); desktop pairing.rs hits are client-side NIP-11 parsing tests. 98 appears nowhere in any supported_nips construction.

**O que a tornaria falsa:** Adding 98 to the SUPPORTED_NIPS const at nip11.rs:15 or a conditional supported_nips.push(98) in RelayInfo::build.

**Nota:** NIP-98 verification is real production code in buzz-auth; the relay NIP-11 document simply never advertises it.


---

## [n-15] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The PackManifest parser for plugin.json has no deny_unknown_fields — unknown fields are silently ignored (validator only issues advisory warnings).

**Evidência:** `crates/buzz-persona/src/manifest.rs:126-129` · `crates/buzz-persona/src/manifest.rs:128-129` · `crates/buzz-persona/src/manifest.rs:130-132`

**Método de busca:**

- `Read manifest.rs in full`
- `Grep 'deny_unknown_fields' crates/buzz-persona (7 hits)`

**Falsos positivos:** deny_unknown_fields hits at persona.rs:83,175 apply to .persona.md frontmatter/Hooks (hard errors by design), not plugin.json; spec/test hits describe that same frontmatter behavior.

**O que a tornaria falsa:** Adding #[serde(deny_unknown_fields)] to RawManifest or PackManifest in manifest.rs.

**Nota:** RawManifest (manifest.rs:130-149) carries no deny attribute; the permissiveness is documented as intentional for OPS-superset plugin.json files.


---

## [n-17] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The pack manifest `version` string is never validated as semver — the buzz-persona crate does not depend on the semver crate.

**Evidência:** `crates/buzz-persona/Cargo.toml:9-13` · `crates/buzz-persona/src/manifest.rs:167-168`

**Método de busca:**

- `Read crates/buzz-persona/Cargo.toml in full — 4 deps, no semver`
- `Grep 'semver|Version::parse' -i in crates/ — 3 hits`
- `Grep 'version' -i in crates/buzz-persona/src — validation sites reviewed`

**Falsos positivos:** The 3 semver hits are doc comments only (PERSONA_PACK_SPEC.md:208 and manifest.rs:34,38 describing the Engines.buzz field, which is stored as Option<String> and never parsed). manifest.rs:157-168 checks only presence and non-emptiness of version.

**O que a tornaria falsa:** buzz-persona adding `semver` to Cargo.toml, or manifest.rs parsing `version`/`engines.buzz` with semver::Version/VersionReq.

**Nota:** The spec doc says 'Semver' but no code enforces it.


---

## [n-18] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** engines.buzz is parsed and then discarded — it does not exist in PackManifestData.

**Evidência:** `crates/buzz-persona/src/manifest.rs:39-41` · `crates/buzz-persona/src/manifest.rs:180` · `crates/buzz-persona/src/pack.rs:102-115` · `crates/buzz-persona/src/pack.rs:138-151`

**Método de busca:**

- `Grep 'PackManifestData' repo-wide (4 hits, all in buzz-persona)`
- `Grep 'engines' crates/buzz-persona/src (7 hits)`
- `Read pack.rs:100-151 field-by-field`

**Falsos positivos:** validate.rs:111 lists 'engines' in the known-keys array (so no warning is emitted); validate.rs:582 and manifest.rs:224,238 are tests. No hit enforces or propagates the constraint.

**O que a tornaria falsa:** PackManifestData gaining an engines field, or any code comparing engines.buzz against a runtime version.

**Nota:** PackManifestData has fields id/name/version/description/personas/pack_instructions/mcp_config/defaults only; the PackManifest→PackManifestData conversion at pack.rs:138-151 copies everything except engines (and hooks_config, which is intentionally omitted per comment at pack.rs:111-112).


---

## [n-19] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The persona-level `version` field is also discarded — resolve.rs uses the pack's version instead.

**Evidência:** `crates/buzz-persona/src/resolve.rs:223-228` · `crates/buzz-persona/src/resolve.rs:228` · `crates/buzz-persona/src/pack.rs:77-98` · `crates/buzz-persona/src/persona.rs:116`

**Método de busca:**

- `Grep 'version' crates/buzz-persona/src/resolve.rs`
- `Read pack.rs:77-98 (LoadedPersona has no version field)`

**Falsos positivos:** Version hits in resolve.rs tests are pack manifest versions, not persona versions.

**O que a tornaria falsa:** LoadedPersona gaining a version field wired from frontmatter and resolve.rs preferring it (the code comment at resolve.rs:225-227 sketches exactly that future change).

**Nota:** Frontmatter accepts `version` (persona.rs:116, 181) but it is dropped when building LoadedPersona; resolve.rs assigns the pack manifest version unconditionally.


---

## [n-20] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** There is no schema_version field in the pack/persona format.

**Evidência:** `crates/buzz-persona/src/manifest.rs:79-82`

**Método de busca:**

- `Grep 'schema_version|schemaVersion|format_version|formatVersion' -i in crates/buzz-persona — 0 hits`
- `Grep 'schema_version|schemaVersion' -i in docs/nips — 0 hits`
- `Grep 'schema_version|schemaVersion' repo-wide — ~25 hits reviewed`

**Falsos positivos:** Repo-wide schema_version hits belong to unrelated subsystems: buzz-conformance trace steps (src/lib.rs:292), buzz-voice pocket_april bundles (src/pocket_april.rs:41), harbor benchmark manifests, and desktop tts_settings — none are the persona/pack format.

**O que a tornaria falsa:** A schema_version (or format_version) field added to PackManifest, Persona front matter, or the NIP-AP kind:30175 spec.

**Nota:** The desktop agent-snapshot format has `format` + `version` discriminators, but that is the snapshot envelope, not the pack/persona format.


---

## [n-21] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The persona `runtime` field exists in code (persona.rs:148) but is not in the spec's field table — a doc/code divergence.

**Evidência:** `crates/buzz-persona/src/persona.rs:145-148` · `crates/buzz-persona/src/persona.rs:192` · `crates/buzz-persona/PERSONA_PACK_SPEC.md:204-219`

**Método de busca:**

- `Grep -i 'runtime' PERSONA_PACK_SPEC.md (40+ hits, all prose about agent runtimes)`
- `Grep '^| `' PERSONA_PACK_SPEC.md — full enumeration of every table row`

**Falsos positivos:** Every 'runtime' hit in the spec is prose about the ACP/agent runtime (goose etc.); none is a field-table row. Table rows at 204-219 list name..hooks (16 fields) and at 761-770 list behavioral fields — neither includes `runtime`.

**O que a tornaria falsa:** A `| \`runtime\` |` row added to either spec table.

**Nota:** runtime is accepted by the deny_unknown_fields Frontmatter parser (persona.rs:192) and exposed in PersonaConfig (persona.rs:148) and LoadedPersona (pack.rs:85), yet absent from both spec field tables. Divergence stands at this commit.


---

## [n-22] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** In runtime_env_vars, any runtime other than 'buzz-agent' (including 'claude' and 'codex') hits a `_` catch-all mapping to GOOSE_MODEL/GOOSE_PROVIDER — there is no per-runtime mapping.

**Evidência:** `crates/buzz-persona/src/resolve.rs:372-378` · `crates/buzz-persona/src/resolve.rs:379-384`

**Método de busca:**

- `Grep 'runtime_env_vars' (whole repo) — sole definition at resolve.rs:365`
- `Read resolve.rs:365-398 — match has exactly two arms: Some("buzz-agent") and `_``

**Falsos positivos:** None; there are no Some("claude")/Some("codex") arms anywhere in the function, and temperature/context always emit GOOSE_* (resolve.rs:388-395).

**O que a tornaria falsa:** Additional match arms per runtime (claude/codex/goose) replacing the `_` catch-all in resolve.rs:372-385.


---

## [n-23] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Teams reference member personas only by local ID (UUID v4 or builtin:*) — not naddr, not pubkey, not name; there is no TeamMember struct.

**Evidência:** `desktop/src-tauri/src/managed_agents/types.rs:769` · `desktop/src-tauri/src/commands/personas/create.rs:55` · `desktop/src-tauri/src/managed_agents/teams.rs:38`

**Método de busca:**

- `Grep 'TeamMember' repo-wide — 4 hits total, all inspected`
- `Grep 'struct Team|pub struct.*Team' repo-wide — TeamRecord/CreateTeamRequest/UpdateTeamRequest all use Vec<String>`
- `Grep 'naddr' in desktop/src-tauri/src/managed_agents — 0 hits`

**Falsos positivos:** The 4 TeamMember hits are TS helper names (findTeamMemberTarget, ensureWelcomeTeamMembership) and TeamSnapshotMemberPreview (a UI preview row) — no TeamMember struct or type exists.

**O que a tornaria falsa:** Introduction of a `struct TeamMember`/`type TeamMember`, or persona_ids becoming typed references (naddr coordinates or pubkeys).

**Nota:** TeamRecord.persona_ids is plain Vec<String>; ensure_persona_ids_are_active (personas.rs:265-269) resolves them against local persona records by string ID only.


---

## [n-24] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** A team (kind 30176 / teams.json) is not portable between machines by construction — its local persona ids mean nothing outside the teams.json that generated them.

**Evidência:** `crates/buzz-core/src/kind.rs:302-304` · `crates/buzz-core/src/kind.rs:306-307` · `desktop/src-tauri/src/managed_agents/team_events.rs:47` · `desktop/src-tauri/src/managed_agents/team_events.rs:79-83`

**Método de busca:**

- `Grep 'KIND_TEAM|30176' crates/ and 'teams.json' repo-wide`
- `Read team_events.rs (full wire projection), teams.rs:1-80`

**Falsos positivos:** None material — the 30176 content body is exactly name/description/instructions/persona_ids (TeamEventContent), with persona_ids as raw local id strings (e.g. 'builtin:fizz').

**O que a tornaria falsa:** 30176 content embedding member definition projections (like 30178 does), or persona_ids replaced by globally addressable NIP-33 coordinates.

**Nota:** Nuance: same-owner device sync reconciles teams.json AND personas via 30175/30176, so the owner's own devices converge; but upstream's own rationale for creating 30178 (kind.rs:300-308) is precisely that 30176's references are local ids a foreign reader can never resolve. As a shareable artifact, a 30176 team is non-portable by construction.


---

## [n-25] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** TeamRecord carries no model/provider fields, and there is no validation of model/provider homogeneity across team members (each AgentDefinition has its own runtime/model/provider).

**Evidência:** `desktop/src-tauri/src/managed_agents/types.rs:762-786` · `desktop/src-tauri/src/managed_agents/types.rs:24-34`

**Método de busca:**

- `Grep 'struct TeamRecord' -A 60 (whole repo) — fields: id, name, description, instructions, persona_ids, is_builtin, source_dir, is_symlink, symlink_target, version, created_at, updated_at`
- `Grep -i 'homogen' (whole repo)`
- `Grep 'model|provider' desktop/src-tauri/src/commands/teams.rs — 0 hits`

**Falsos positivos:** The single 'homogeneous' hit is a Python docstring in benchmarks/harbor-buzz-orchestra/src/harbor_buzz_orchestra/manifest.py:58 (benchmark roster class), unrelated to team validation.

**O que a tornaria falsa:** model/provider fields on TeamRecord, or create_team/update_team (commands/teams.rs:144,185) iterating member AgentDefinitions to compare model/provider.


---

## [n-26] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Each agent instance gets a freshly generated keypair (Keys::generate()) — there is no key derivation from the persona.

**Evidência:** `desktop/src-tauri/src/commands/agents.rs:632-633` · `desktop/src-tauri/src/commands/agents.rs:628-630`

**Método de busca:**

- `Grep 'Keys::generate' in desktop/src-tauri/src — agents.rs:632 is the agent-mint site; snapshot import mints likewise`
- `Grep 'nip06|from_mnemonic|derive_key|seed' -i in desktop/src-tauri/src — hits reviewed`
- `Grep 'derive|derivation' -i in desktop/src-tauri/src/managed_agents — hits reviewed`

**Falsos positivos:** 'seed' hits are test fixtures (seed_events, keyring seeding); 'derive' hits are #[derive] attributes and provider-id/env-var derivation comments — nothing derives Nostr keys from persona data.

**O que a tornaria falsa:** A NIP-06 style derivation (mnemonic/HKDF from persona id or pack key) replacing Keys::generate() at agent mint or snapshot import.

**Nota:** The persona is looked up only to check it is active (line 628-630); the keypair minted at line 632 is independent random entropy. Snapshot import (import.rs) also mints fresh identities.


---

## [n-27] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The mention-filter-on-by-default behavior does not apply to hand-written TOML rules: require_mention has #[serde(default)] and Default is false, so a manual TOML rule in subscribe=config mode is born with the mention filter OFF.

**Evidência:** `crates/buzz-acp/src/filter.rs:91-93` · `crates/buzz-acp/src/filter.rs:116-122` · `crates/buzz-acp/src/config.rs:1396-1399`

**Método de busca:**

- `Grep 'require_mention' crates/buzz-acp/src/config.rs and filter.rs`
- `Read SubscriptionRule struct + Default impl (filter.rs:82-129) and the config-mode merge (config.rs:1381-1411)`

**Falsos positivos:** None — serde's default for bool is false, and the explicit Default impl also sets false; the config-mode filter merge is most-permissive-wins, so one omitted require_mention drives the channel filter to no-#p.

**O que a tornaria falsa:** A #[serde(default = "...")] function returning true on SubscriptionRule.require_mention, or the Default impl flipping to true.

**Nota:** Test test_config_mode_require_mention_most_permissive (config.rs:1902-1913) locks the most-permissive-wins merge in.


---

## [n-28] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Kind 30178 (team catalog) is an empty slot: implemented in core, relay, ingest, gate and e2e test, but no client publishes or reads it — zero references in desktop/, web/, mobile/ and buzz-cli; zero interoperability today.

**Evidência:** `crates/buzz-core/src/kind.rs:319` · `crates/buzz-relay/src/handlers/ingest.rs:1154` · `crates/buzz-db/src/event.rs:529` · `crates/buzz-test-client/tests/e2e_team_catalog.rs:1`

**Método de busca:**

- `Grep '30178|TEAM_CATALOG|TeamCatalog|team_catalog|teamCatalog' desktop/ — 0 hits`
- `same pattern web/ — 0 hits`
- `same pattern mobile/ — 0 hits`
- `same pattern crates/buzz-cli — 0 hits`
- `same pattern admin-web/ — 0 hits`
- `Grep 'KIND_TEAM_CATALOG' (whole repo) — only buzz-core/kind.rs and buzz-relay/ingest.rs`

**Falsos positivos:** None inspected in client trees — all 30178 references live in buzz-core, buzz-relay (ingest/req/count), buzz-db, CHANGELOG, docs/nips/NIP-AP.md, and the buzz-test-client e2e suite.

**O que a tornaria falsa:** Any desktop/web/mobile/buzz-cli code constructing, publishing, subscribing to, or parsing kind 30178 events.


---

## [n-29] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** There is no environment variable or CLI flag to change DEFAULT_AGENT_PARALLELISM's default of 10 — it is a Rust const, configurable only per-agent in the UI.

**Evidência:** `desktop/src-tauri/src/managed_agents/types.rs:812-816` · `desktop/src/features/agents/lib/agentParallelism.ts:9`

**Método de busca:**

- `Grep 'PARALLELISM' repo-wide — all ~45 hits reviewed`
- `Grep 'parallelism|PARALLELISM' in crates/buzz-acp/src — 3 hits reviewed`
- `Read types.rs:809-820 — default_agent_parallelism() returns the const with no env read`

**Falsos positivos:** BUZZ_ACP_PARALLELISM appears only in a buzz-backend-kubernetes test-fixture README describing an INVENTED (wrong) var name; OPENCLAW_MAX_PARALLELISM=5 is a per-runtime spawn cap, not the default; buzz-acp's BUZZ_ACP_AGENTS controls harness subprocess count, a different knob.

**O que a tornaria falsa:** default_agent_parallelism() reading an env var (e.g. BUZZ_AGENT_PARALLELISM) or a CLI flag/setting overriding the const.

**Nota:** Per-agent override flows through PersonaAdvancedFields/EditAgentAdvancedFields UI into AgentDefinition.parallelism (clamped 1-32).


---

## [n-30] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The OS deep-link handler recognizes exactly 5 hosts (connect, join, add-community, message, nostr-bind); anything else only logs 'unknown deep link action'; buzz://pr|issue|repo links are in-app only and never registered with the OS.

**Evidência:** `desktop/src-tauri/src/deep_link.rs:312-380` · `desktop/src-tauri/src/deep_link.rs:378-380` · `desktop/src/shared/lib/entityLink.ts:119` · `desktop/src-tauri/tauri.conf.json:46-49`

**Método de busca:**

- `Grep 'unknown deep link action' repo-wide (1 hit)`
- `Read deep_link.rs:294-385 (full host match: connect:313, join:322, add-community:337, message:353, nostr-bind:369)`
- `Grep 'buzz://' entityLink.ts`

**Falsos positivos:** None — the match has exactly 5 named arms plus Some(action) catch-all (log only) and None (log only).

**O que a tornaria falsa:** A new host arm in handle_deep_link_url (e.g. Some("pr")), or entityLink parsing wired into the OS deep-link event path.

**Nota:** Precision nuance: OS registration is scheme-level — the whole `buzz` scheme IS registered (tauri.conf.json:48), so an OS-clicked buzz://pr URL reaches the handler and dies in the unknown-action log branch. 'Never registered with the OS' is accurate for the hosts' handling, not for the scheme.


---

## [n-31] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** There is no deep link for installing a persona or a team — an install button on a website cannot be a native deep link.

**Evidência:** `desktop/src-tauri/src/deep_link.rs:312-377` · `desktop/src-tauri/src/deep_link.rs:378-380`

**Método de busca:**

- `Grep -i 'deep.?link|deepLink|register_uri_scheme|buzz://' (whole repo)`
- `Read desktop/src-tauri/src/deep_link.rs:300-385 — supported actions: connect, join, add-community, message, nostr-bind; anything else logs 'unknown deep link action'`
- `Grep 'persona|team|install|pack' desktop/src-tauri/src/deep_link.rs`

**Falsos positivos:** buzz://repo|pr|issue links in crates/buzz-cli/src/links.rs are git-entity links, and docs/buzz-entity-links.md:15 states 'Still unimplemented: OS-level deep links (slice 2)' for them; the 'persona/team/install' grep matched only a test string 'Acme Team' in an add-community URL (deep_link.rs:446). Mobile parses only message/connect/join links.

**O que a tornaria falsa:** A new deep_link.rs match arm such as install-persona/install-team/import-agent, or an OS-level handler that opens the snapshot import flow from a URL scheme.


---

## [n-32] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Legacy persona/team file import was removed: .persona.md, .persona.json, .persona.png, .zip and flat .team.json files are rejected with an explicit error.

**Evidência:** `desktop/src-tauri/src/commands/personas/snapshot/import.rs:33-34` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:41-44` · `desktop/src-tauri/src/commands/team_snapshot.rs:34-35` · `desktop/src-tauri/src/commands/team_snapshot.rs:66-72`

**Método de busca:**

- `Grep '\.persona\.md|\.persona\.json|\.persona\.png|\.team\.json' in desktop/src-tauri/src — all hits reviewed`

**Falsos positivos:** migration.rs .persona.md hits are the one-time on-disk migration of pre-existing team dirs, not the import surface; media_download.rs .team.json hits are the NEW canonical snapshot format (buzz-team-snapshot v1), distinct from the rejected flat legacy schema.

**O que a tornaria falsa:** Removal of reject_legacy_persona_filename / LEGACY_TEAM_ERROR, or re-acceptance of ZIP magic / flat {version:1,type:team} JSON in decode_team_snapshot_from_bytes.

**Nota:** ZIP is rejected on both paths: by filename suffix for personas (import.rs:34) and by PK magic bytes for teams (team_snapshot.rs:61-63).


---

## [n-35] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** There is no anonymous relay read: REQ requires NIP-42 authentication; an unauthenticated connection receives 'auth-required: authenticate before subscribing'.

**Evidência:** `crates/buzz-relay/src/handlers/req.rs:75-83` · `crates/buzz-relay/src/nip11.rs:97-100` · `crates/buzz-relay/src/nip11.rs:114`

**Método de busca:**

- `Grep 'auth-required' in crates/buzz-relay/src — all hits reviewed`
- `Grep 'authenticate before subscribing' repo-wide`
- `Read handle_req auth match (req.rs:49-84) — only AuthState::Authenticated proceeds, every other state returns`

**Falsos positivos:** None — there is no config toggle or bypass arm in the REQ handler; the only conditional inside Authenticated is scope checking.

**O que a tornaria falsa:** A public-read config flag or an additional match arm in handle_req serving filters to non-Authenticated connections.

**Nota:** The catch-all `_` arm covers unauthenticated, pending, and failed states identically.


---

## [n-36] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Hitting the relay with a host that has no configured community returns 404 'no community is configured for this host' — not 401; only the relay's own RELAY_URL authority is seeded at startup.

**Evidência:** `crates/buzz-relay/src/router.rs:306-310` · `crates/buzz-relay/src/router.rs:308` · `crates/buzz-relay/src/main.rs:248-249` · `crates/buzz-relay/src/main.rs:259-260`

**Método de busca:**

- `Grep 'no community is configured for this host' repo-wide (7 hits)`
- `Read router.rs:285-330 and main.rs:244-290`
- `Grep -i 'seed' crates/buzz-relay/src`

**Falsos positivos:** The other 6 message hits (audio, invites, bridge) are the same generic rejection reused on other HTTP surfaces — consistent with the claim, not against it.

**O que a tornaria falsa:** The rejection changed to StatusCode::UNAUTHORIZED, or startup seeding extended to a configurable multi-host list.

**Nota:** Community binding happens 'row zero' before the WebSocket upgrade and before any auth, so an unmapped host can never produce a 401; startup calls ensure_configured_community only for the authority derived from config.relay_url (BUZZ_RELAY_URL).


---

## [n-37] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The relay reads only the raw Host header — it does not honor X-Forwarded-Host (so a reverse proxy rewriting Host causes NIP-98 401s).

**Evidência:** `crates/buzz-relay/src/api/bridge.rs:625-630` · `crates/buzz-relay/src/api/bridge.rs:195-206` · `crates/buzz-auth/src/nip98.rs:40`

**Método de busca:**

- `Grep 'X-Forwarded|x-forwarded' crates/ — 1 hit (doc comment only)`
- `Grep -i 'forwarded' (whole repo) — inspected all hits`
- `Grep -i 'header::HOST|"host"' crates/buzz-relay/src — tenant binding always from raw HOST header`
- `Read bridge.rs:185-206 (nip98_expected_url), tenant.rs:71-91 (bind_community from raw_host)`

**Falsos positivos:** The only X-Forwarded mention in crates/ is a buzz-auth doc comment telling CALLERS of verify_nip98_event to reconstruct the URL for proxy deployments — no relay code path does so. Other 'forwarded' hits are event-forwarding/mesh terminology (buzz-acp relay.rs, tunnel/reliable.rs), not HTTP headers.

**O que a tornaria falsa:** Relay middleware or handlers reading x-forwarded-host (or Forwarded:) to derive raw_host before bind_community / nip98_expected_url.


---

## [n-39] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** buzz-agent has a closed enum of exactly 5 providers dispatched by match, with no trait abstraction — its README says 'There is no trait, no Box<dyn>, no async-trait'.

**Evidência:** `crates/buzz-agent/README.md:258` · `crates/buzz-agent/src/config.rs:679-691` · `crates/buzz-agent/src/llm.rs:133-140`

**Método de busca:**

- `Grep 'There is no trait, no Box' crates/buzz-agent (README.md:258 exact)`
- `Read config.rs:678-691 (Provider: Anthropic, OpenAi, Databricks, DatabricksV2, OpenRouter = 5)`
- `Grep 'trait |Box<dyn|async_trait' crates/buzz-agent/src`

**Falsos positivos:** auth.rs:43-44 has an async_trait TokenSource — that abstracts token acquisition (OAuth), not provider dispatch; llm.rs:4860/6784/6802 async_trait hits are in test modules; lib.rs Box<dyn Error> is error plumbing. None is a provider abstraction.

**O que a tornaria falsa:** Introduction of a Provider/LlmBackend trait object replacing the enum match in llm.rs.

**Nota:** README says 'one match in Llm::complete'; in code the enum is matched at both body-build and parse sites (llm.rs:133, 253) — same closed-enum architecture, slightly looser than 'a single match'.


---

## [n-40] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Tier-3 custom HarnessDefinition JSON has exactly 7 fields and zero model/provider fields.

**Evidência:** `desktop/src-tauri/src/managed_agents/custom_harnesses.rs:49-70` · `desktop/src-tauri/src/managed_agents/custom_harnesses.rs:44-46`

**Método de busca:**

- `Grep 'struct HarnessDefinition' -B10 -A45 (whole repo) — single definition`
- `Read custom_harnesses.rs:42-70 — fields: id, label, command, args, env, install_instructions_url, install_hint (7 exactly)`

**Falsos positivos:** None — no model/provider/runtime field appears in the struct; env is a free-form BTreeMap but is not a model/provider field.

**O que a tornaria falsa:** model or provider fields added to HarnessDefinition, or an 8th field of any kind.


---

## [n-42] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** ARCHITECTURE.md is outdated: it still says '4 trigger types' and omits the diff_posted workflow trigger (the code has 5).

**Evidência:** `ARCHITECTURE.md:532` · `crates/buzz-workflow/src/schema.rs:38-68` · `crates/buzz-workflow/src/schema.rs:51-52`

**Método de busca:**

- `Grep -i 'trigger|diff_posted' ARCHITECTURE.md`
- `Read schema.rs:33-68 (TriggerDef: MessagePosted, ReactionAdded, DiffPosted, Schedule, Webhook = 5)`

**Falsos positivos:** None — ARCHITECTURE.md:532 is the only trigger-type count in the doc and it lists 4; DiffPosted round-trip tests exist (schema.rs:874-886).

**O que a tornaria falsa:** ARCHITECTURE.md updated to list diff_posted / '5 trigger types'.

**Nota:** Divergence still present at this commit.


---

## [n-43] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The 6th top-level workflow key _webhook_secret is not authored by the user — the relay injects it into the stored canonical JSON.

**Evidência:** `crates/buzz-workflow/src/schema.rs:14-27` · `crates/buzz-relay/src/webhook_secret.rs:3-4` · `crates/buzz-relay/src/handlers/command_executor.rs:732-733` · `crates/buzz-relay/src/webhook_secret.rs:54-56`

**Método de busca:**

- `Grep '_webhook_secret' (whole repo)`
- `Read webhook_secret.rs:1-70, command_executor.rs:700-760, schema.rs:12-31`

**Falsos positivos:** None — WorkflowDef has 5 author keys (name, description, trigger, steps, enabled); _webhook_secret exists only in relay-side inject/extract/strip helpers and is stripped before API responses.

**O que a tornaria falsa:** WorkflowDef gaining a _webhook_secret field, or clients being allowed to supply it through the save path.


---

## [n-44] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** There is no published JSON schema for workflows — the schema/ directory contains only schema.sql.

**Evidência:** `schema/schema.sql:1`

**Método de busca:**

- `ls schema/ — only schema.sql`
- `Glob '**/*.schema.json' repo-wide — 2 hits`
- `Glob '**/workflow*.json' — 0 hits`
- `Grep 'json-schema|jsonschema|JsonSchema|\$schema' -i in crates/buzz-workflow — 0 hits`

**Falsos positivos:** The 2 *.schema.json hits are Helm chart values schemas (deploy/charts/buzz/values.schema.json, deploy/charts/buzz-push-gateway/values.schema.json) — unrelated to workflow definitions.

**O que a tornaria falsa:** A workflow.schema.json landing in schema/ or docs/, or buzz-workflow adopting schemars/JsonSchema derives.

**Nota:** Workflow shape is defined only by the serde types in crates/buzz-workflow/src/schema.rs.


---

## [n-45] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** There are no example workflows in examples/ — the only complete workflow YAMLs are in ARCHITECTURE.md, VISION_PROJECTS.md, crates/buzz-cli/TESTING.md and in tests.

**Evidência:** `examples/README.md:3` · `ARCHITECTURE.md:516-526`

**Método de busca:**

- `find examples/ -type f (11 files: countdown-bot/*, meadow-core/*, README.md)`
- `find examples/ -iname '*.yaml' -o -iname '*.yml' (0 hits)`
- `grep -ril 'trigger:' examples/ (0 hits)`
- `grep -rln 'on: message_posted|trigger:' --include='*.md' repo-wide`

**Falsos positivos:** meadow-core is a persona pack (plugin.json + .persona.md), not workflows; countdown-bot is a Rust bot. The markdown grep returned exactly ARCHITECTURE.md, crates/buzz-cli/TESTING.md, VISION_PROJECTS.md — matching the claim's list.

**O que a tornaria falsa:** A workflow .yaml/.yml file or workflow-bearing doc added under examples/.

**Nota:** Claim's enumeration of where workflow YAML does live is exactly reproduced by the search at this commit.


---

## [n-46] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** 'Crossfire review' is not a Buzz feature or convention: a case-insensitive grep of the whole repo (docs, VISION*, CHANGELOG, tests, .claude/, .agents/, .codex/, .goose/, .intersect/) returns exactly 2 occurrences, both prose in VISION.md (lines 169 and 212), and zero occurrences in buzz-directory.

**Evidência:** `VISION.md:169` · `VISION.md:212`

**Método de busca:**

- `rg -i --hidden -n 'crossfire' . (in _upstream/buzz) — exactly 2 hits, VISION.md:169 and VISION.md:212`
- `rg -i --hidden --no-ignore -l 'crossfire' . (excluding node_modules) — VISION.md only`
- `rg -i --hidden -n 'crossfire' D:/EMPRESAS/buzz/_upstream/buzz-directory — exit 1 (0 hits)`
- `ls -d .claude .agents .codex .goose .intersect — all exist and were covered by --hidden`

**Falsos positivos:** None — both hits are marketing/vision prose, not code, config, skill files, or tests.

**O que a tornaria falsa:** Any code identifier, doc heading, skill, or workflow named crossfire appearing in either repo.


---

## [n-47] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The desktop snapshot import path has no deny_unknown_fields in any .rs file under desktop/src-tauri (29 occurrences repo-wide, zero in desktop) and no Zod validation on the import path — an unknown key such as x_killerbee_profile does not break import.

**Evidência:** `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:164-166` · `desktop/src/shared/features/manifest.ts:2`

**Método de busca:**

- `Grep 'deny_unknown_fields' in desktop/ — 0 hits`
- `Grep 'deny_unknown_fields' repo-wide with count — 30 occurrences in 9 files: 29 in .rs (buzz-dev-mcp 3, buzz-core 7, buzz-relay 3+1, buzz-push-gateway 9, buzz-persona 5+1 test) + 1 in PERSONA_PACK_SPEC.md`
- `Grep 'zod' -i in desktop/ — 6 files, each inspected`
- `Read AgentSnapshot struct derives (agent_snapshot.rs:90-174)`

**Falsos positivos:** Zod hits besides shared/features/manifest.ts (feature-flag manifest, not import) are binary/asset noise: an SVG path string, the EFF wordlist ('zodiac'), and base64 avatar data in personas.rs. Note buzz-persona (pack format) DOES use deny_unknown_fields — but that is the pack path, not the desktop snapshot import path.

**O que a tornaria falsa:** Adding #[serde(deny_unknown_fields)] to AgentSnapshot/TeamSnapshot structs, or a zod schema parsing the snapshot on the TS side of the import dialog.

**Nota:** The doc's '29 repo-wide' matches the .rs occurrence count exactly (30 total including one markdown mention in PERSONA_PACK_SPEC.md). Serde's default behavior silently ignores unknown keys, so an x_killerbee_profile key survives decode without error — it is dropped, not rejected.


---

## [n-48] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Unknown snapshot fields are not preserved: the import preview reserializes the struct (serde_json::to_string_pretty), so an extra field does not appear in the preview manifest, is not persisted, and does not survive an export→import round-trip.

**Evidência:** `desktop/src-tauri/src/commands/personas/snapshot/import.rs:410-411` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:82-83` · `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:164-172`

**Método de busca:**

- `Grep 'to_string_pretty' desktop/src-tauri/src (7 hits; import.rs:410 is the preview)`
- `grep -n 'flatten|deny_unknown_fields|extra' agent_snapshot.rs`
- `Read AgentSnapshot/AgentSnapshotDefinition/Profile/Memory structs`

**Falsos positivos:** The 3 grep hits in agent_snapshot.rs are extract_chunk_payload_png and an 'extra chunk' PNG comment — no #[serde(flatten)] catch-all map, no deny_unknown_fields anywhere in the snapshot types.

**O que a tornaria falsa:** A #[serde(flatten)] extra: Map<String,Value> field on the snapshot structs, or the preview rendering raw file bytes instead of the reserialized struct.

**Nota:** Unknown JSON keys parse without error (permissive serde) and vanish on to_string_pretty; persistence flows through typed AgentDefinition/ManagedAgentRecord, so nothing unknown can round-trip.


---

## [n-49] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** A snapshot missing a required field (e.g. profile.displayName) fails the whole serde parse — it does not produce a friendly validation error, because parse failure happens before any validation runs.

**Evidência:** `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:287-291` · `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:125-126` · `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:403-404`

**Método de busca:**

- `Grep 'display_name|deny_unknown' agent_snapshot.rs`
- `Read agent_snapshot.rs:90-174 (structs; display_name has no #[serde(default)]) and 287-292, 387-407 (decode then validate order)`

**Falsos positivos:** None — validate_snapshot's friendly messages cover only format/version mismatch and EMPTY (post-parse) name/displayName strings; a MISSING field never reaches it.

**O que a tornaria falsa:** display_name (and peers) becoming Option with defaults, plus validate_snapshot reporting missing fields by name.


---

## [n-51] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The import file picker filters by type: acp-rules.toml and catalog.json do not appear in either the agent picker (*.agent.json/*.agent.png) or the team picker (*.team.json/*.team.png).

**Evidência:** `desktop/src/features/agents/ui/UnifiedAgentsSection.tsx:140-146` · `desktop/src/features/agents/ui/AgentsView.tsx:648`

**Método de busca:**

- `grep -rn 'accept=' desktop/src --include='*.tsx' (8 hits, full enumeration)`
- `grep for Tauri dialog pickers with extension filters (0 hits)`
- `grep -il 'toml' desktop/src --include='*.tsx'`

**Falsos positivos:** Other accept= hits are avatar images, .ncryptsec/.key backups — none accepts .toml or bare .json. The 4 'toml' tsx hits are repo file-viewer panels, not pickers.

**O que a tornaria falsa:** An accept list widened to .json/.toml, or a Tauri dialog.open import path with broader filters.

**Nota:** Browser accept filters are advisory (an OS 'All files' override can bypass them), but the pickers as coded exclude both files.


---

## [n-52] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Snapshot import writes no credentials / API key: env_vars is an empty BTreeMap, agent_command is empty, runtime_pid is None, start_on_app_launch is false.

**Evidência:** `desktop/src-tauri/src/commands/personas/snapshot/import.rs:623` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:610` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:624-626` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:595-596`

**Método de busca:**

- `Grep 'env_vars|agent_command|runtime_pid|start_on_app_launch' desktop/src-tauri/src/commands/personas/snapshot/`
- `Read import.rs:570-640 (both the AgentDefinition at :581 and ManagedAgentRecord at :597-640)`

**Falsos positivos:** None — the persona definition record at import.rs:581 also gets env_vars: BTreeMap::new(); runtime_pid: None at :626.

**O que a tornaria falsa:** Import copying snapshot-supplied env vars or commands into either record.


---

## [n-53] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Import does not place the agent in any channel — 'Add to channel' is a separate action in the profile panel.

**Evidência:** `desktop/src-tauri/src/commands/personas/snapshot/import.rs:624-630` · `desktop/src/features/profile/ui/UserProfilePanelSections.tsx:689` · `desktop/src/features/agents/ui/AddAgentToChannelDialog.tsx:234`

**Método de busca:**

- `Grep 'channel' -i in commands/personas/snapshot/import.rs — 0 hits in the entire file`
- `Grep 'Add to channel' in desktop/src — 2 hits, both the separate profile-panel action`
- `Read the full confirm-import record construction (import.rs:560-674)`

**Falsos positivos:** None — the import flow writes personas + managed-agent records, publishes kind:0 and memory, and emits agents-data-changed; no channel membership call exists anywhere in the file.

**O que a tornaria falsa:** The import confirm handler invoking any channel-add/join command (e.g. the logic behind AddAgentToChannelDialog) after minting the record.

**Nota:** Imported record is also STOPPED by construction: runtime_pid None, start_on_app_launch false.


---

## [n-54] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** An imported agent is not running: Status STOPPED, Start on launch No, empty Channels tab, 0 memories, and no provider credential (measured in app 0.5.5).

**Evidência:** `desktop/src-tauri/src/commands/personas/snapshot/import.rs:624` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:623` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:626` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:635` · `desktop/src-tauri/tauri.conf.json:4`

**Método de busca:**

- `grep 'autostart|start_on_launch|is_active|channel' in snapshot/import.rs`
- `Read confirm_agent_snapshot_import phases (import.rs:438-700): validate/mint/publish/memory — no spawn, no channel membership write`

**Falsos positivos:** is_active:true (576, 646) is definition/record liveness flags, not a running process — runtime_pid stays None and nothing starts the agent.

**O que a tornaria falsa:** The import flow gaining an auto-start call, channel auto-join, start_on_app_launch:true, or env_var/credential copying from the snapshot.

**Nota:** Code confirms every structural part: never started, autostart off, env_vars (credentials) cleared, no channel wiring; doc comment (import.rs:452-454) confirms no source identity/env material is consumed. Caveat: '0 memories' is snapshot-dependent — Phase 4 does write memory entries when the snapshot carries them, so that figure reflects the specific tested snapshot. The live-app measurement itself cannot be re-run in this audit; app version at this commit is 0.5.5, matching.


---

## [n-55] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Snapshots do not carry env_vars, nsec, auth_tag, relay_url, machine commands, or lineage ids — agent identity does not travel; import generates a new keypair.

**Evidência:** `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:92-174` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:452-454` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:517` · `desktop/src-tauri/src/commands/personas/snapshot/tests.rs:833-836`

**Método de busca:**

- `Read agent_snapshot.rs:90-174 — manifest fields limited to format, version, definition{name, source_is_builtin, system_prompt, runtime, model, provider, parallelism, respond_to, respond_to_allowlist, name_pool, idle/max…`
- `Grep 'env_vars|nsec|auth_tag|relay_url|lineage' in agent_snapshot.rs manifest structs — none`
- `Grep 'private_key_nsec|Keys::generate' import.rs`

**Falsos positivos:** respond_to_allowlist DOES travel but is flagged/re-validated at import (import.rs:110-113 comment; keep_allowlist gate) — pubkeys, not credentials. The e2e test tests.rs:809 pins 'relay_url, env_vars, auth_tag are not carried'.

**O que a tornaria falsa:** New AgentSnapshot fields carrying keys, env, relay URL, spawn commands, or source ids consumed at import instead of minting Keys::generate().


---

## [n-56] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** profile.about is parsed but discarded on import — sync_managed_agent_profile receives only display_name and avatar.

**Evidência:** `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:127-128` · `desktop/src-tauri/src/relay.rs:440-446` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:679-687`

**Método de busca:**

- `Grep 'about' -i in commands/personas/snapshot/ — 3 hits, all tests setting about: None`
- `Read sync_managed_agent_profile signature (relay.rs:440-452) — no about parameter; build_profile_event takes name+avatar only`

**Falsos positivos:** None — import.rs never reads snapshot.profile.about; the field deserializes into the struct and is dropped.

**O que a tornaria falsa:** sync_managed_agent_profile/build_profile_event gaining an `about` parameter fed from snapshot.profile.about.

**Nota:** about survives only inside the preview's manifest_json blob shown to the user; it never reaches the kind:0 event.


---

## [n-58] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Snapshot import validates form only (format, version, names, sizes, ranges) — it never validates content.

**Evidência:** `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:387-407` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:30` · `desktop/src-tauri/src/managed_agents/types.rs:895` · `desktop/src-tauri/src/managed_agents/types.rs:913`

**Método de busca:**

- `Grep 'MAX_SNAPSHOT_JSON_BYTES|validate|clamp|range' import.rs`
- `Read validate_snapshot (agent_snapshot.rs:387-407), validate_respond_to_allowlist (types.rs:890-906), resolve_mint_behavioral_defaults (types.rs:929-955), confirm flow (import.rs:461-520)`

**Falsos positivos:** materialize_import_avatar re-uploads avatar bytes with MIME detection (detect_and_validate_mime, import.rs:952) — still a format check, not content validation. system_prompt, memory bodies, model/provider strings pass through with no semantic check.

**O que a tornaria falsa:** Import checking model/provider against a runtime catalog, scanning prompt or memory content, or verifying avatar semantics beyond MIME/size.


---

## [n-59] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Reserialization drops empty arrays: respondToAllowlist: [], namePool: [] and memory.entries: [] do not appear in the redisplayed manifest, due to skip_serializing_if.

**Evidência:** `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:112-115` · `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:154-155` · `desktop/src-tauri/src/commands/personas/snapshot/import.rs:410-411`

**Método de busca:**

- `Read AgentSnapshotDefinition/AgentSnapshotMemory field attributes (agent_snapshot.rs:90-174)`
- `Grep 'manifest_json' in commands/personas/snapshot/ — produced by re-serializing the parsed struct, not by echoing the raw file`

**Falsos positivos:** name_pool carries the same skip attribute at agent_snapshot.rs:114-115; rename_all=camelCase yields respondToAllowlist/namePool key names in JSON.

**O que a tornaria falsa:** The preview switching to echoing the raw uploaded bytes, or the skip_serializing_if attributes being removed.

**Nota:** Because manifest_json is to_string_pretty of the decoded struct, any field whose value is an empty Vec is omitted from the 'exactly as decoded' display — a known display-fidelity wrinkle.


---

## [n-60] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Team import does not deduplicate: importing a team snapshot after its member personas were already imported creates duplicate agents with new keypairs — embedded members are materialized without matching by name.

**Evidência:** `desktop/src-tauri/src/commands/team_snapshot.rs:482` · `desktop/src-tauri/src/commands/team_snapshot.rs:497-498` · `desktop/src-tauri/src/commands/team_snapshot.rs:528-531` · `desktop/src-tauri/src/commands/team_snapshot.rs:145-155`

**Método de busca:**

- `grep 'dedup|duplicate|match.*name|existing' team_snapshot.rs`
- `Read confirm_team_snapshot_import (500-680) and build_import_definitions/build_import_team`

**Falsos positivos:** The only 'duplicate' guard (634-643) is a generated-pubkey collision check ('astronomically unlikely'), not persona dedup; load_personas in phase 3 is for appending new definitions, not lookup.

**O que a tornaria falsa:** build_import_definitions gaining a match-by-name/slug against existing personas, or an import-time 'link to existing agent' option.

**Nota:** Every embedded member becomes a brand-new AgentDefinition + ManagedAgentRecord + keypair; the new TeamRecord gets a fresh UUID. Re-import after individual persona import necessarily duplicates.


---

## [n-61] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** No implemented schema exists for the kind 30178 content body: no Rust struct, no TS type, no serde serialization anywhere in the repo; the only schema is a test fixture with empty members, and the member-projection shape exists nowhere (only prose) — a publisher would have to invent it from scratch.

**Evidência:** `crates/buzz-test-client/tests/e2e_team_catalog.rs:34-36` · `crates/buzz-relay/src/handlers/ingest.rs:4111` · `docs/nips/NIP-AP.md:223` · `docs/nips/NIP-AP.md:256`

**Método de busca:**

- `Grep -i 'TeamCatalogContent|CatalogContent|struct.*Catalog|type.*Catalog' (whole repo)`
- `rg '"members"' --type rust --type ts -g '!node_modules'`
- `Grep 'members' docs/nips/NIP-AP.md`

**Falsos positivos:** Struct/type Catalog hits are unrelated: MeshCatalogEntry/MeshModelCatalog (mesh LLM), AcpRuntimeCatalogEntry (harness catalog), CatalogAgentProjection/PersonaCatalogPublication (TS, kind 30175 persona catalog), CatalogSource (provenance), AgentVoiceCatalog. '"members"' hits are NIP-29 channel membership (nostr_convert.rs:540, relay_members.rs) and channel DB tests — none serialize a 30178 body. B…

**O que a tornaria falsa:** A Rust struct / TS type / serde impl (or JSON schema file) defining the 30178 content body incl. member projections, or a client publisher constructing non-empty members.


---

## [n-62] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** 30178 ingest validation does not apply the kind-30175 slug grammar to the d tag — a colon is legal there.

**Evidência:** `crates/buzz-relay/src/handlers/ingest.rs:1159-1162` · `crates/buzz-relay/src/handlers/ingest.rs:1163-1167` · `crates/buzz-relay/src/handlers/ingest.rs:1113-1123` · `crates/buzz-test-client/tests/e2e_team_catalog.rs:117-122`

**Método de busca:**

- `Grep '30178' in crates/ — all hits reviewed`
- `Read validate_team_catalog_envelope (ingest.rs:1154-1168) and single_bounded_d_tag (1093-1123)`

**Falsos positivos:** The [a-z0-9_-] slug grammar (ingest.rs:1140-1150) sits directly above but is invoked by the 30175 persona validator, not by validate_team_catalog_envelope. single_bounded_d_tag checks only cardinality=1, non-empty, ≤64 chars, no control/whitespace — colon passes.

**O que a tornaria falsa:** validate_team_catalog_envelope calling the slug-grammar check, which would break builtin-team:welcome addressing.

**Nota:** An e2e test explicitly locks in colon acceptance (e2e_team_catalog.rs:119).


---

## [n-63] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** 30178 ingest imposes no member-count limit and no content validation — per NIP-AP the content schema is client-defined and the relay does not validate content.

**Evidência:** `crates/buzz-relay/src/handlers/ingest.rs:1163-1168` · `docs/nips/NIP-AP.md:256` · `docs/nips/NIP-AP.md:223`

**Método de busca:**

- `Grep 'KIND_TEAM_CATALOG' ingest.rs (8 hits; validation call at 2413-2416)`
- `Read validate_team_catalog_envelope — only validate_shared_tag + single_bounded_d_tag`
- `Contrast search: PROJECT_MEMBER_CAP = 64 exists for kind:30621 (ingest.rs:1176) — no analogous cap for 30178`

**Falsos positivos:** The neighboring project validator (30621) does cap members at 64 — inspected and confirmed it applies only to KIND_PROJECT, underscoring that 30178 deliberately has no such cap.

**O que a tornaria falsa:** validate_team_catalog_envelope parsing content JSON or adding a member/tag cap for 30178.

**Nota:** Only bound on 30178 content is the generic relay frame limit (config max_frame_bytes) — no member count, no schema check.


---

## [n-64] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Publishing kind 30178 has no owner/admin/role gate and no verification that the team exists as a 30176 — any authenticated pubkey can publish its own (only Scope::UsersWrite plus pubkey-matches-identity are checked).

**Evidência:** `crates/buzz-relay/src/handlers/ingest.rs:215-219` · `crates/buzz-relay/src/handlers/ingest.rs:1878-1881` · `crates/buzz-relay/src/handlers/ingest.rs:1163-1168` · `crates/buzz-relay/src/handlers/ingest.rs:2413-2416`

**Método de busca:**

- `Grep 'validate_team_catalog_envelope' ingest.rs — definition at 1163, sole production call at 2413-2416`
- `Read required_scope_for_kind (ingest.rs:211-243) — 30178 maps to Scope::UsersWrite`
- `Read ingest.rs:1860-1900 — generic checks: timestamp, size, pubkey==auth identity, scope`
- `Grep '30176|KIND_TEAM' near the 30178 validation — no DB lookup of a team head`

**Falsos positivos:** The nearby is_agent_owner DB check (ingest.rs:2384-2400) applies only to KIND_AGENT_TURN_METRIC, not 30178. Envelope validation checks only shared-tag shape and one bounded d tag; content is stored unvalidated (NIP-AP.md:256).

**O que a tornaria falsa:** ingest gaining a role/ownership gate for 30178 or a lookup verifying a kind:30176 head exists at the same (pubkey, d) coordinate.


---

## [n-65] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The 30178 e2e test suite has no anonymous-read test.

**Evidência:** `crates/buzz-test-client/src/lib.rs:90-93` · `crates/buzz-test-client/tests/e2e_team_catalog.rs:91`

**Método de busca:**

- `Grep 'anonymous|unauthenticated|without auth|no auth|anon' -i in tests/e2e_team_catalog.rs — 0 hits`
- `Grep test fns in e2e_team_catalog.rs — 8 tests enumerated (lines 86-398), each name reviewed`
- `Grep 'connect_unauthenticated' in crates/buzz-test-client — used only in e2e_relay.rs:590 and e2e_human_edit_agent_content.rs:85, never in e2e_team_catalog.rs`

**Falsos positivos:** The 'foreign' tests (foreign_sees_only_shared, ids_lookup_unshared, count_excludes_foreign_unshared) use a DIFFERENT authenticated identity, not an anonymous connection — BuzzTestClient::connect always performs NIP-42 auth.

**O que a tornaria falsa:** A test in e2e_team_catalog.rs calling connect_unauthenticated and asserting REQ behavior for kind 30178.

**Nota:** All 8 team-catalog tests authenticate; anonymous-read behavior for 30178 is covered only indirectly by the relay-wide REQ auth gate tests elsewhere.


---

## [n-66] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** Nothing prevents a third party from publishing 30178 on their own relay: no operator-level kind allowlist, no kind registry, no Block signature requirement (require_relay_membership defaults false; Apache-2.0).

**Evidência:** `crates/buzz-relay/src/config.rs:127-128` · `crates/buzz-relay/src/config.rs:532-534` · `LICENSE:1-2` · `crates/buzz-relay/src/handlers/ingest.rs:1878-1881` · `docs/nips/NIP-MP.md:66`

**Método de busca:**

- `Grep 'require_relay_membership' config.rs (default via env BUZZ_REQUIRE_RELAY_MEMBERSHIP, unwrap_or(false))`
- `Grep -i 'extra_kinds|allowed_kinds|kind_allowlist' crates/ (no operator kind config)`
- `Grep -i 'kind registry' repo-wide`
- `head LICENSE`

**Falsos positivos:** 'kind registry' in AGENTS.md/ARCHITECTURE.md refers to buzz-core/src/kind.rs — a compiled-in constants file, not a governance/allowlist mechanism; relay_operator_pubkeys (config.rs:187) is operator-supplied moderation config, not a vendor signature gate.

**O que a tornaria falsa:** An operator-configurable kind allowlist, a signed-kind-registry check, or ingest verifying events against a hardcoded vendor (Block) pubkey.

**Nota:** Ingest's only signature requirements are the event's own author signature and pubkey==authenticated identity; the kind allowlist is source code any Apache-2.0 fork can extend, and NIP-MP itself states external kind registries reserve nothing. A self-hosted relay accepts 30178 out of the box (membership enforcement off by default).


---

## [n-67] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** docs/nips/NIP-AP.md:103 is stale — it still says respond_to/parallelism are 'reserved / parsed but not applied', while the desktop already loads and validates them.

**Evidência:** `docs/nips/NIP-AP.md:103-104` · `docs/nips/NIP-AP.md:105-106` · `desktop/src-tauri/src/managed_agents/persona_events.rs:391-392` · `desktop/src-tauri/src/managed_agents/types.rs:86-90` · `desktop/src-tauri/src/managed_agents/persona_events.rs:200-202`

**Método de busca:**

- `Read docs/nips/NIP-AP.md:80-115 (tables mark respond_to/respond_to_allowlist/parallelism 'Reserved.'; :103-109 'parsed but not yet applied')`
- `Grep 'respond_to|parallelism' desktop/src-tauri/src/managed_agents/persona_events.rs and types.rs`

**Falsos positivos:** None — the doc's three specific assertions are each contradicted: the local store DOES carry them (AgentDefinition, types.rs:86-90), writers DO emit them (persona_event_content, persona_events.rs:379-399), readers load them (persona_events.rs:200-202), and they are validated (RespondTo::parse_wire types.rs:864-877; validate_respond_to_allowlist types.rs:890-906; parallelism 1..=32 types.rs:913) a…

**O que a tornaria falsa:** NIP-AP.md being updated to remove the 'Status: reserved' block (which would make this staleness claim obsolete).

**Nota:** The persona_events.rs comment explicitly dates the activation ('live since the create-path unification (B5)'), so the NIP text at lines 103-109 describes a superseded state.


---

## [n-68] 🗓 documentado como futuro (e de fato ausente)

**Afirmação:** The snapshot PNG carries its payload in a tEXt chunk only — not iTXt, not zTXt; the decoder reads only info.uncompressed_latin1_text.

**Evidência:** `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:361-366` · `desktop/src-tauri/src/managed_agents/agent_snapshot.rs:431-432` · `desktop/src-tauri/src/managed_agents/team_snapshot.rs:156`

**Método de busca:**

- `Grep 'uncompressed_latin1_text|tEXt|iTXt|zTXt' -i in desktop/src-tauri/src — all hits reviewed`
- `Grep 'compressed_latin1_text|utf8_text' — 4 hits, all `.uncompressed_latin1_text` (substring match); zero standalone zTXt (compressed_latin1_text) or iTXt (utf8_text) reads`
- `Grep 'add_ztxt_chunk|add_itxt_chunk' in desktop/src-tauri/src — 0 hits`

**Falsos positivos:** media_animated.rs builds a raw tEXt chunk in a sanitizer test; media_snapshot_png.rs scans raw chunk types for b"tEXt" — both consistent with tEXt-only. The png crate maps tEXt→uncompressed_latin1_text, zTXt→compressed_latin1_text, iTXt→utf8_text; only the first is ever touched.

**O que a tornaria falsa:** The encoder switching to add_ztxt_chunk/add_itxt_chunk, or the decoders also scanning compressed_latin1_text/utf8_text.

**Nota:** Both encode paths (make_png_with_text at 425-440 and inject_text_chunk at 462-493) use add_text_chunk (tEXt); agent and team decoders read only uncompressed_latin1_text. A payload placed in iTXt or zTXt would be invisible to import.

