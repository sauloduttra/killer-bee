# Rascunhos das 4 issues para `block/buzz`

> **Submeter é 🔴 — quem posta é o usuário.** Corpo em inglês, pronto para colar.
> Toda citação verificada contra `ed4b3e7afafb5f5a688c210f39b90d747e6f0f00`
> (2026-08-05) por leitura direta + verificação adversarial independente
> (método em [`NEGATIVE-SPACE.md`](NEGATIVE-SPACE.md)). Antes de postar, rode
> `uv run python scripts/verify_citations.py docs/ISSUES-DRAFT.md` para conferir
> deriva contra o main do dia.

---

## Issue 1 — kind 30178 (team catalog): the body schema is implemented-adjacent everywhere except where it's defined

**Title:** `kind 30178: content schema is explicitly delegated to publishing clients, but no client exists — worth standardizing?`

```markdown
Verified at ed4b3e7afafb5f5a688c210f39b90d747e6f0f00.

Kind 30178 (team catalog) is fully wired on the relay side:

- constant + NIP-33 assert: `crates/buzz-core/src/kind.rs:319`, `:859`; member of
  `SHARED_GATED_KINDS` (`kind.rs:215`)
- ingest scope + envelope validation (`["shared","true"]` + single bounded `d` tag):
  `crates/buzz-relay/src/handlers/ingest.rs:208-219`, `:1154-1168`, `:2413-2416`
- read-path gating at every chokepoint (REQ, ids, COUNT — including the COUNT
  fast-path bypass to avoid existence leaks): `handlers/req.rs:1228-1236`,
  `handlers/count.rs:102-110`, `buzz-db/src/event.rs:525-533`
- e2e suite in CI: `crates/buzz-test-client/tests/e2e_team_catalog.rs`,
  `.github/workflows/ci.yml:763-765`
- generic 256 KB content cap applies: `handlers/ingest.rs:1868-1875`

But the event **content** is explicitly left undefined: NIP-AP.md:223 says
"The content schema is defined by the client that publishes it", and NIP-AP.md:256
confirms content is stored unvalidated. Meanwhile no in-repo client publishes or
reads 30178 at all — grep for `30178` hits 8 files, none under `desktop/`
(the desktop's kinds.ts stops at 30177); the only producer is the e2e suite.

So today, the first client to publish 30178 gets to define the de-facto body format
unilaterally — and if a later official definition differs, every event published in
the meantime is wrong retroactively. We're building an external publisher and hit
exactly this: we defined a member projection (snapshot minus
{respondTo, respondToAllowlist}) and published it as a JSON Schema
(https://github.com/sauloduttra/killer-bee/blob/main/schema/kind-30178-content.schema.json),
measured against the 256 KB cap (largest 12-member team uses ~15%).

**Question:** would you take a PR adding a content schema definition to
docs/nips/NIP-AP.md (or a serde struct alongside the persona 30175
`PersonaEventContent` precedent at
`desktop/src-tauri/src/managed_agents/persona_events.rs:24`)? If yes, is
"sanitized team fields + ordered embedded member projections" the shape you had in
mind, or is there a reason it was deliberately left open?
```

---

## Issue 2 — workflow actions: 7 variants, 4 functional, none can invoke an agent

**Title:** `workflows: no ActionDef variant can involve an agent — intended boundary or roadmap gap?`

```markdown
Verified at ed4b3e7afafb5f5a688c210f39b90d747e6f0f00.

`ActionDef` (`crates/buzz-workflow/src/schema.rs:90-131`) has 7 variants. In the
executor (`executor.rs:519-690`):

- **functional (4):** `SendMessage` (via ActionSink), `AddReaction` and
  `CallWebhook` (behind the `reqwest` feature — enabled by buzz-relay, so
  functional in the shipped binary; SSRF check at `executor.rs:798-800`), `Delay`
- **stubs (2):** `SendDm` and `SetChannelTopic` return
  `WorkflowError::NotImplemented` (`executor.rs:580-589`, TODO WF-07)
- **dead end (1):** `RequestApproval` returns `Suspended` with a token, but the
  only consumer marks the run Failed — "approval gates are not yet implemented
  (WF-08)" (`executor.rs:661-668`, `crates/buzz-workflow/src/lib.rs:229-245`)

None of the 7 involves an agent. Search receipt: `ActionDef::` appears only in
schema.rs and executor.rs; grepping buzz-workflow for agent/acp/persona/llm yields
only the word "impersonated" in a spoofing test (`crates/buzz-workflow/src/lib.rs:1608-1618`); buzz-workflow's
Cargo.toml pulls no agent crate.

The one indirect path we found: a `send_message` action whose text @-mentions an
agent gets p-tagged by the relay's ActionSink (`workflow_sink.rs:22-45`), and ACP
agents wake on p-tag mentions — so "workflow pokes agent via mention text" works
as a side effect, undocumented and string-typed.

**Question:** is "workflows never invoke agents" a deliberate security/complexity
boundary (in which case: worth documenting, and is the mention side-channel
intended?), or is a `prompt_agent`-style variant on the roadmap alongside WF-07/WF-08?
```

---

## Issue 3 — buzz-acp `subscribe=config`: omitted `require_mention` silently widens the subscription, and the README documents a rule format the parser ignores

**Title:** `buzz-acp config mode: require_mention defaults to false + most-permissive-wins merge = hand-written rules subscribe to everything; README example uses a shape load_rules never reads`

```markdown
Verified at ed4b3e7afafb5f5a688c210f39b90d747e6f0f00.

Two compounding surprises for anyone writing `[[rules]]` by hand:

1. **Omitted `require_mention` = false, and false wins.**
   `SubscriptionRule.require_mention` is `#[serde(default)]` → false when the key
   is absent (`crates/buzz-acp/src/filter.rs:82-93`). In config mode the merged
   per-channel filter starts at `require_mention=true` and ANY matching rule with
   false flips it (`crates/buzz-acp/src/config.rs:1288-1310`, most-permissive-wins). With it false, the
   NIP-01 REQ omits the `#p` tag entirely (`crates/buzz-acp/src/relay.rs:3183-3196`), so the agent
   receives — and its rules get to dispatch on — every matching event in the
   channel, not just mentions. One forgotten key in one rule widens the whole
   channel subscription. (Contrast: `subscribe=mentions` forces
   `require_mention=true` unless `--no-mention-filter`, `config.rs:1257-1274`.)

2. **The only README example with `require_mention` is in a format the parser
   doesn't read.** README shows a `[channel.CHANNEL_UUID]` table
   (`crates/buzz-acp/README.md:237-242`), but `load_rules` deserializes
   `TomlConfig { rules: Vec<SubscriptionRule> }` — i.e. `[[rules]]` tables — with
   no deny_unknown_fields (`crates/buzz-acp/src/config.rs:1155-1159`). A user following the README gets
   zero rules and only a "config file contains zero rules" warning
   (`crates/buzz-acp/src/config.rs:1176-1181`). `--subscribe config` and the `[[rules]]` schema are
   documented nowhere (search receipt: `require_mention` appears in 6 files, all
   inside crates/buzz-acp; the only .md hit is the README example above).

Suggested fixes (happy to PR any subset): document `subscribe=config` +
`[[rules]]` in the README with the default called out; fix or remove the
`[channel.*]` example; consider `deny_unknown_fields` on `TomlConfig` so the
documented-but-ignored shape fails loudly.

**Question:** is most-permissive-wins the intended merge semantic for multi-rule
channels, or an artifact worth changing while nobody depends on it?
```

---

## Issue 4 — snapshot-in-PNG format: reconstructive spec + reproduction recipe (currently source-only)

**Title:** `agent/team snapshot PNG format is undocumented outside the source — here's a reconstructed spec; want it as docs/spec/?`

```markdown
Verified at ed4b3e7afafb5f5a688c210f39b90d747e6f0f00.

The trading-card PNG format is a nice piece of design that can only be learned by
reading Rust. Reconstructed spec, every step cited:

- **Carrier:** one PNG tEXt chunk, keyword `buzz_agent_snapshot` (agents) or
  `buzz_team_snapshot` (teams); chunk text = base64 (STANDARD) of the manifest
  JSON (`desktop/src-tauri/src/managed_agents/agent_snapshot.rs:59-63`, `:320-324`;
  `desktop/src-tauri/src/managed_agents/team_snapshot.rs:49-52`).
- **Placement is load-bearing:** the chunk must precede IDAT — the import reader
  only surfaces text chunks seen before IDAT
  (`desktop/src-tauri/src/commands/media_snapshot_png.rs:54-58`).
- **Detection is magic-bytes-first:** first 4 bytes `89 50 4E 47` route to the PNG
  branch, anything else to JSON; the extension is not consulted at this stage
  (`desktop/src-tauri/src/commands/personas/snapshot/import.rs:213`, `:232-233`).
  (Nuance: the import PREVIEW does reject some names by suffix —
  `.persona.md/.persona.json/.persona.png/.zip` — before sniffing, `import.rs:36-39`.)
- **Envelope dispatch:** decoded JSON's `format` field selects Plain
  (`"buzz-agent-snapshot"`, version 1) vs Locked (NIP-44 envelope, own size cap,
  fails closed without local keys) (`agent_snapshot_envelope.rs:174-196`).
- **Body-as-avatar:** if `profile.avatarDataUrl` is absent, the PNG pixels become
  the agent's avatar (`import.rs:242-261`), with asymmetric limits: >2048 px is a
  hard import error, >2 MiB re-encoded is a soft skip
  (`snapshot_avatar.rs:18-23`, `:35-37`). Total file cap 10 MiB (`import.rs:234-239`).
- **Relay-side is stricter than the desktop:** media validation permits exactly ONE
  tEXt chunk and only with an allowlisted snapshot keyword; any other
  tEXt/zTXt/iTXt/eXIf/iCCP (even pHYs, explicitly excluded as an identity channel)
  is rejected (`crates/buzz-media/src/validation.rs:592-646`). The upload
  sanitizer extracts and re-injects the snapshot chunk across re-encode
  (`media_snapshot_png.rs:22-80`).

Search receipt for "undocumented": grep `buzz_agent_snapshot|buzz-agent-snapshot`
under docs/ → zero files; the 7 repo-wide hits are all source (+1 UI doc-comment,
`AgentCardMintDialog.tsx:101-104`); the only prose trace is one CHANGELOG line (:293).

**Question:** would you take a PR adding this as `docs/spec/agent-snapshot-png.md`?
We're generating these PNGs from an external emitter and would rather track a spec
you own than re-derive it from source each release.
```

---

## Como isto foi verificado

Cada issue foi montada por um leitor dedicado com recibo de busca (padrões, caminhos,
falsos positivos descartados, e o que falsificaria cada negativa), e as afirmações
negativas passaram por segundo cético independente. Registro completo:
[`NEGATIVE-SPACE.md`](NEGATIVE-SPACE.md) e [`SPEC-VS-IMPL.md`](SPEC-VS-IMPL.md).
