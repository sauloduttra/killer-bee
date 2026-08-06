# PROTOCOL-NOTES — Fase 0 (reconhecimento verificado)

## Executive summary (English)

*The rest of this document is in Brazilian Portuguese; this summary exists so an
upstream engineer can audit its claims without translating 40 KB. The citations are
the point — every `file:line` below is against the pinned commits in the table that
follows, and was re-opened by an independent second reader before publication.*

**What this document is.** The verified reconnaissance of Buzz internals that the
Killer Bee project is built on. Nothing here is quoted from documentation on faith:
every claim was read in the source, carries `file:line`, and anything we could not
confirm sits quarantined in the **⚠️ Não verificado** section and did not become a
design decision. Where a conclusion was later checked against the running desktop app
(0.5.5), the live observation is recorded separately (§10.9) — reading the parser
proves what the app *accepts*, never what its UI *offers* (our D-017).

**The three findings that shaped the project:**

1. **The pack format is a spec without a runtime** (§0.1). `PERSONA_PACK_SPEC.md`
   describes `.buzzpack`, `buzz install`, `pack.lock` — none of it is implemented.
   What actually installs personas today is snapshot import in the desktop app.
2. **The in-community persona catalog is alive** (§0.2). Kind 30175 with a
   `["shared","true"]` tag feeds the desktop's "Discover agents"
   (`crates/buzz-core/src/kind.rs:187`). What does not exist is discovery *between*
   communities — the gap this project fills.
3. **No workflow action invokes an agent** (§0.3, `crates/buzz-workflow/src/schema.rs:92`).
   Agents are addressed by mention, with no delivery or ordering guarantee. Killer
   Bee's orchestration claims are written to that reality, not around it.

**The facts an integrator needs (all cited inline):** agent/team snapshots are the
real install path — JSON, or a PNG with the manifest in a `tEXt` chunk, sniffed by
magic bytes with the extension ignored (§10.4, §10.8). Import validates form (format,
version, names, sizes, ranges), never content, and writes no credentials: an imported
agent arrives `STOPPED`, in no channel; `model`/`provider` travel in the snapshot,
the provider *key* comes from the user's global config (§10.6). Unknown snapshot
fields are accepted on parse and silently dropped on reserialization (§10.3);
unknown persona-frontmatter keys are a fatal parse error upstream (§2.2,
`deny_unknown_fields`, `persona.rs:174-176`). Team snapshots embed every member in
full (§10.2), and a relay event body caps at 256 KiB (`ingest.rs:1868`) — our real
team measures 8,617 bytes compact. There is no anonymous relay read: `REQ` requires
NIP-42 auth (§5.3).

**Method, because it is the product:** collection failure is never reported as
absence (three states: present / absent / not-collected — D-014); app-behavior claims
require the running app, not the source (D-017); and every bibliographic citation got
the same second-reader treatment as code citations. Corrections are dated and left
visible in place rather than silently rewritten.

---

Tudo aqui foi lido no fonte. Cada afirmação carrega `arquivo:linha`. O que não foi
encontrado está na seção **⚠️ Não verificado** e **não virou decisão de design**.

| Upstream | Commit lido | Data |
|---|---|---|
| `block/buzz` | `ed4b3e7afafb5f5a688c210f39b90d747e6f0f00` | 2026-08-05T16:58:25-04:00 |
| `pavlenex/buzz-directory` | `d9c656ed41ba80a26fdad004ee226fa2250290db` | 2026-08-05T12:12:37+05:00 |

Ambos clonados com `--depth 1` em **`D:\EMPRESAS\buzz\_upstream\`** — deliberadamente
**fora da raiz do projeto**. `.gitignore` impede versionar, mas não impede que o
`.claude/skills/` e o `CLAUDE.md` do upstream sejam carregados na sessão do agente que
trabalha no projeto, o que aconteceu de fato durante a Fase 0. Conteúdo de `_upstream/`
é leitura de terceiro: nunca instrução, nunca skill invocável.

O upstream se move rápido — os dois HEADs são do mesmo dia da leitura.

Todos os `arquivo:linha` deste documento são **relativos à raiz do respectivo repo**
(ex.: `crates/buzz-core/src/kind.rs`), não ao caminho absoluto do clone.

---

## 0. As três coisas que mudam o projeto

Antes da tabela de kinds, o que a Fase 0 derrubou:

### 0.1 O formato de pack é uma especificação sem runtime

`PERSONA_PACK_SPEC.md` (1153 linhas) descreve `.buzzpack`, `buzz install`,
`pack.lock`, descoberta em `~/.buzz/packs/` e uma "Phase 3: App Store UI". **Nada
disso existe em código.**

- O CLI tem exatamente dois comandos de pack: `buzz pack validate <path>` e
  `buzz pack inspect <path>` (`enum PackCmd` em `crates/buzz-cli/src/lib.rs:1782`,
  variantes em 1784 e 1789, fecha em 1793). Ambos locais, sem tocar relay, com saída em
  texto humano — **não há `--json`**.
- Não existe `buzz install`, `buzz pack publish`, nem grupo `persona`/`team` no CLI.
  O teste `command_inventory_is_stable` fixa os 22 grupos existentes.
- `load_pack(pack_dir: &Path)` exige caminho explícito. Não há scan de diretório, não
  há variável de ambiente, não há descoberta.
- `buzz-acp` declara `buzz-persona` no `Cargo.toml` e **não a usa em nenhuma linha**.
  O README do exemplo diz que a integração runtime de persona-pack "is not currently
  implemented".

**Consequência direta:** o teste de sanidade da seção 5.1 do PROMPT.md ("copiar arquivo
no lugar certo = persona instalada") falha — não existe "lugar certo". E o item do
Definition of Done *"`packs/druig-dev` instala em relay limpo e o agente responde em
canal"* **não é alcançável via pack**. O caminho real para um agente rodando passa pelo
Buzz Desktop (managed agents) e pelos eventos kind 30175/30176.

### 0.2 A UI de catálogo de personas não foi removida — está viva

O PROMPT.md abre dizendo que "a UI de catálogo de personas foi removida do desktop e
nada preencheu o buraco". **Falso no commit lido.** `PersonaCatalogDialog` está montado
em `AgentsView` e é alcançável pelo item de menu "Discover agents". O catálogo lê
kind:30175 com `["shared","true"]` de todos os autores e "Add agent" cria uma cópia
local com `catalogSource`.

O que de fato foi removido: teams ancorados em diretório de pack
(`migration/detach.rs` desanexa `source_dir`) e a importação de arquivos legados —
`.persona.md`, `.persona.json`, `.persona.png`, `.zip` e `.team.json` flat são
rejeitados com erro explícito.

Existe portanto um catálogo **por comunidade, dentro do app**. O que não existe é
catálogo **público, cross-comunidade, na web**. Essa é a lacuna real — menor e mais
precisa do que a que o PROMPT.md descreve, mas ainda desocupada.

### 0.3 Nenhum workflow pode invocar um agente

O motor de workflow tem 7 ações (`send_message`, `send_dm`, `set_channel_topic`,
`add_reaction`, `call_webhook`, `request_approval`, `delay`). **Nenhuma delas invoca
agente.** Destas, só 4 executam de fato: `send_message`, `call_webhook`, `add_reaction`
e `delay`. `send_dm` e `set_channel_topic` retornam `NotImplemented` (WF-07);
`request_approval` suspende mas marca o run como `Failed` (WF-08).

O acoplamento real workflow→agente é indireto: um workflow posta mensagem, e o agente
reage porque está inscrito no canal e o filtro de menção casou. A Fase 4 (crossfire)
precisa ser redesenhada em cima disso.

---

## 1. Tabela de kinds

`crates/buzz-core/src/kind.rs` é o registro autoritativo (`kind.rs:1`), 1085 linhas,
129 constantes `KIND_*` (recontado na auditoria 2026-08-06; uma versão anterior dizia
"133 constantes u32"). `ALL_KINDS` (`kind.rs:635`) exporta 130 — ficam de fora
`KIND_AUTH` (22242), `KIND_NOSTR_IDENTITY_BINDING` (24243) e `KIND_PUSH_LEASE` (30350).

### Família de agentes (a que importa para nós)

| Kind | Constante | Semântica | Linha |
|---|---|---|---|
| 10100 | `KIND_AGENT_PROFILE` | metadata + owner ref, replaceable, **agent-authored** | `kind.rs:87` |
| 24200 | `KIND_AGENT_OBSERVER_FRAME` | efêmero | `kind.rs:469` |
| 30174 | `KIND_AGENT_ENGRAM` | memória cifrada do agente (NIP-AE) | `kind.rs:94` |
| **30175** | **`KIND_PERSONA`** | **definição de persona (NIP-AP), owner-authored** | `kind.rs:196` |
| **30176** | **`KIND_TEAM`** | **definição de team (NIP-AP), owner-private** | `kind.rs:282` |
| 30177 | `KIND_MANAGED_AGENT` | instância de agente, projeção opt-IN | `kind.rs:291` |
| **30178** | **`KIND_TEAM_CATALOG`** | **projeção compartilhável de team, membros embutidos** | `kind.rs:319` |
| 30179 | `KIND_PRIVATE_MANAGED_AGENT` | agregado privado cifrado ao owner (NIP-PMA) | `kind.rs:118` |
| 44200 | `KIND_AGENT_TURN_METRIC` | métrica de turno (NIP-AM) | `kind.rs:545` |
| 43001–43006 | — | protocolo de job | — |

**30176 CONFIRMADO** — o PROMPT.md acertou o número.

### Faixas

Decididas por três `const fn` no próprio `kind.rs`:

- `is_ephemeral` — 20000–29999 (`kind.rs:769`)
- `is_replaceable` — `matches!(kind, 0 | 3 | KIND_CHANNEL_METADATA | 10000..=19999)`, inclui kind 41 (`kind.rs:776`)
- `is_parameterized_replaceable` — 30000–39999 (`kind.rs:783`)

Não existe função `is_addressable`; o código usa "NIP-33 / parameterized replaceable".

**Não há faixa reservada para terceiros.** O controle é um allowlist estrito no ingest:
`required_scope_for_kind` termina em `_ => Err("restricted: unknown event kind")`
(`crates/buzz-relay/src/handlers/ingest.rs:319`). Qualquer kind não registrado é
rejeitado — **Killer Bee não pode inventar kind próprio**.

### O gate `shared` — o mecanismo de catálogo

`SHARED_GATED_KINDS = &[KIND_PERSONA, KIND_TEAM_CATALOG]` (`kind.rs:215`). Semântica
"author-only-unless-shared":

- Sem tag `["shared","true"]` → legível só pelo autor. REQ/COUNT/fan-out omitem em silêncio.
- Com exatamente `["shared","true"]` → legível por toda a comunidade, "enabling the
  opt-in agent catalog (`{kinds:[30175]}` all-authors)" (`kind.rs:187`).
- O opt-in é **tag, não campo de conteúdo**, justamente para que ligar/desligar não
  altere os bytes do conteúdo nem o `persona_content_hash` usado pelo sync.
- `event_is_shared` falha fechado em qualquer forma não exata (`kind.rs:258`).

**30176 (team) deliberadamente NÃO é membro** (`kind.rs:212`) — teams são owner-private.
Para compartilhar um team existe o 30178, que **embute** as projeções dos membros em vez
de referenciá-las, porque as personas membros são author-only e um leitor estrangeiro
nunca conseguiria hidratá-las (`kind.rs:300-308`).

### NIPs

`SUPPORTED_NIPS = &[1, 2, 10, 11, 16, 17, 23, 25, 29, 33, 38, 42, 50, 56]`
(`crates/buzz-relay/src/nip11.rs:15`), mais 43 condicional. NIP-33 (addressable) está lá.
**NIP-98 está implementado** (`crates/buzz-auth/src/nip98.rs`, kind 27235) **mas não é
anunciado** em `supported_nips`. `supported_extensions: Some(vec!["nip-er"])`
(`nip11.rs:165`). Há 18 NIPs próprios em `docs/nips/`.

---

## 2. O persona pack, como o código realmente o define

### 2.1 Duas metades

**(a) `.plugin/plugin.json`** — struct `PackManifest` (`crates/buzz-persona/src/manifest.rs:79`).

Obrigatórios (String não-vazia, senão `MissingField`): `id`, `name`, `version`
(`manifest.rs:155-169`). Todo o resto é opcional: `description`, `author`, `license`,
`homepage`, `keywords`, `engines`, `personas`, `pack_instructions`, `mcp_config`,
`hooks_config`, `defaults`.

O parser é **deliberadamente permissivo** — sem `deny_unknown_fields`:

```rust
// manifest.rs:126-129
/// Intentionally permissive (no `deny_unknown_fields`): `plugin.json` is an
/// OPS superset and may carry fields from other tools (e.g. `ops_category`,
/// `marketplace_tags`). Unknown fields are silently ignored here; the
/// validator issues advisory warnings for Buzz-unknown keys.
```

O upstream **antecipa campos de terceiros e cita `marketplace_tags` como exemplo**.

**(b) `agents/<nome>.persona.md`** — YAML frontmatter + corpo markdown.
Struct `PersonaConfig` (`crates/buzz-persona/src/persona.rs:101`).

**O system prompt é o corpo markdown**, carregado em `prompt: String`
(`persona.rs:169`) e renomeado para `system_prompt` em `ResolvedPersona`.

Campos: `name`✅, `display_name`✅, `description`✅ obrigatórios; `avatar`, `version`,
`author`, `skills`, `mcp_servers`, `subscribe`, `triggers` (alias legado `respond_to`,
`persona.rs:189`), `model`, `runtime`, `temperature`, `max_context_tokens`,
`thread_replies`, `broadcast_replies`, `hooks` opcionais.

### 2.2 A restrição que define o desenho do Killer Bee

```rust
// persona.rs:174-176
/// Deserializes just the YAML frontmatter (no `prompt`).
/// Unknown keys are rejected — typos cause parse errors instead of silent drops.
#[derive(Debug, Deserialize)]
#[serde(rename_all = "snake_case", deny_unknown_fields)]
struct Frontmatter {
```

**Qualquer chave não prevista no frontmatter de uma persona é erro fatal de parse.**
Não existe campo livre, `metadata`, `extra` ou `flatten` na persona.

Onde metadado extra sobrevive:

| Lugar | Comportamento | Serve? |
|---|---|---|
| Frontmatter de `.persona.md` | **erro fatal** | ❌ |
| Top-level de `plugin.json` | parseia, gera warning, **não é retido** no tipo | ⚠️ parcial |
| `.mcp.json` | lido como `serde_json::Value` cru, **sobrevive inteiro** em `LoadedPack.shared_mcp_config` | ✅ |

Ou seja: o perfil scutellata (`threshold`/`recruitment`/`persistence`/`propagation`)
**não pode** morar no frontmatter da persona. Tem que morar em arquivo próprio do Killer
Bee e ser **compilado** para o que o Buzz entende.

### 2.3 Versionamento — mais fraco do que o spec sugere

- `version` é String obrigatória, **nunca validada como semver** (a crate não depende de `semver`).
- `engines.buzz` é parseado e **descartado** — não existe em `PackManifestData`.
- `version` da persona também é descartado; `resolve.rs` usa a versão do pack.
- Não existe `schema_version`.

### 2.4 Runtime e modelo

Campo `runtime: Option<String>` (`persona.rs:148`) — "Preferred ACP runtime ID (e.g.,
'goose', 'claude')". **Não está na tabela de campos do spec** — divergência doc/código.

`model` é `"provider:model-id"`, split no primeiro `:` (`persona.rs:324`), projetado em
env vars por `runtime_env_vars` (`resolve.rs:365-398`):

- `runtime == "buzz-agent"` → `BUZZ_AGENT_MODEL` / `BUZZ_AGENT_PROVIDER`
- **qualquer outro valor, inclusive `claude` e `codex`** → `GOOSE_MODEL` / `GOOSE_PROVIDER`

O segundo ramo é um `_` catch-all, não um mapeamento por runtime.

---

## 3. Teams

- Team **é** evento kind 30176, NIP-33, `d_tag` = id do team.
- Struct Rust: `TeamRecord` (`desktop/src-tauri/src/managed_agents/types.rs:762`).
  Corpo do evento: `TeamEventContent` (`team_events.rs:23`) com
  `name`/`description`/`instructions`/`persona_ids`. Persistência local: `teams.json`.
- **Team referencia persona por ID LOCAL** — `persona_ids: Vec<String>`
  (`types.rs:769`). Não é naddr, não é pubkey, não é nome. São UUID v4
  (`commands/teams.rs:161`) ou builtin (`builtin:fizz`). Não existe struct `TeamMember`.

  → **Um team não é portável entre máquinas por construção.** Os ids não significam
  nada fora do `teams.json` que os gerou. É exatamente por isso que o 30178 embute os
  membros em vez de referenciá-los.

- **Modelos diferentes por membro: sim, é o padrão.** `TeamRecord` não carrega
  modelo/provider; cada `AgentDefinition` tem runtime/model/provider próprios
  (`types.rs:24/29/34`) e o deploy cria um agente por membro
  (`AddTeamToChannelDialog.tsx:130-155`). Não há validação de homogeneidade.
  → **A exigência "3 providers distintos" da Fase 4 é nativamente suportada.**

- **Identidade:** cada instância ganha keypair novo via `Keys::generate()`
  (`commands/agents.rs:632`); nsec em `private_key_nsec`; o owner assina um auth tag
  NIP-OA (`compute_auth_tag`, `agents.rs:674`). Não há derivação a partir da persona.

- **Menção:** o gatilho é tag `p` == pubkey do agente (`require_mention`,
  `crates/buzz-acp/src/filter.rs:93`, avaliado em `filter.rs:390-399`), também empurrado
  ao relay como `#p` no REQ (`relay.rs:3194`).

  **"Ligado por padrão" precisa de asterisco.** Vale para o modo default do binário:
  `--subscribe` tem `default_value = "mentions"` (`config.rs:319-325`) e nesse modo
  `require_mention = !config.no_mention_filter` (`config.rs:1265`, `lib.rs:1502`), com
  `no_mention_filter` sendo flag de clap — falso por omissão, logo `require_mention` é
  `true`. **Mas o campo tem `#[serde(default)]` e o `impl Default` usa `false`**
  (`filter.rs:122`): uma regra escrita à mão em TOML no modo `subscribe=config` nasce
  com menção **desligada**. Se o Killer Bee gerar regra TOML, tem que setar o campo
  explicitamente.

- **Kind 30178 é um slot vazio:** implementado em core, relay, ingest, gate e teste e2e,
  mas **nenhum cliente publica ou lê** — zero referências em `desktop/`, `web/`,
  `mobile/`, `buzz-cli`.

---

## 4. Paralelismo

`DEFAULT_AGENT_PARALLELISM: u32 = 10` (`types.rs:812`; espelhado no front em
`desktop/src/features/agents/lib/agentParallelism.ts:6`).

**CONFIRMADO que baixou de 24 → 10** (`CHANGELOG.md:240`, PR #3038). Faixa válida
`1..=32`. Cap por harness (`OPENCLAW_MAX_PARALLELISM = 5`). Emitido como
`BUZZ_ACP_AGENTS` no spawn (`runtime.rs:717`). **Não há env var ou flag para mudar o
default** — é `const` Rust; configura-se por agente na UI. `BUZZ_ACP_AGENTS` é chave
reservada.

→ É um campo nativo por agente. O `recruitment` do perfil scutellata tem para onde
compilar.

---

## 5. Fluxo de instalação real

### 5.1 Deep links

O handler do SO (`desktop/src-tauri/src/deep_link.rs`) reconhece **exatamente 5 hosts**:
`connect`, `join`, `add-community`, `message`, `nostr-bind`. Qualquer outro loga
"unknown deep link action".

- `buzz://add-community` **existe** — o PROMPT.md acertou.
- `buzz://join?relay=<wsUrl>&code=<code>` (`shared/api/inviteHelpers.ts:21`)
- `buzz://pr|issue|repo` são apenas in-app (`entityLink.ts`), nunca registrados no SO.
- **NÃO existe deep link de instalar persona ou team.**

**Resposta à pergunta 4 da Fase 0: não existe.** O botão do Waggle não pode ser deep
link nativo.

### 5.2 Os dois fluxos que realmente instalam algo

**(a) Agent Catalog no desktop.** Lê kind:30175 `shared` de todos os autores dentro da
comunidade; "Add agent" cria uma **cópia local** com `catalogSource`.

**(b) Snapshots de arquivo.** `.agent.json` / `.agent.png` e `.team.json` / `.team.png`,
pelo file-picker, por drag-and-drop sobre a seção Agents (`[FONTE]` no pin — a negação
anterior foi corrigida em [§10.5](#105-quantos-cliques--o-número-que-vai-no-site),
2026-08-06), ou compartilhados via chat (upload Blossom + card clicável que navega
para Agents e abre o preview de import).

O "Copy link" do `PersonaShareDialog` produz **URL HTTPS Blossom do relay**, e
`require_media_get_auth` tem default `false` — esse `.agent.png` é publicamente
baixável hoje. **Correção 2026-08-06: não é o único.** O `TeamShareDialog` embrulha o
MESMO dialog com `snapshotKind="team"` (`TeamShareDialog.tsx:6` e `:30-39`) e o "Copy
link" sobe o `.team.png` pelo mesmo caminho (`PersonaShareDialog.tsx:354-361`) — **o
`.team.png` também é instalável por URL pública**, travado por e2e
(`team-snapshot.spec.ts:314-457`).

### 5.3 Autenticação

`BUZZ_PRIVATE_KEY` (hex ou nsec, ou `--private-key`), `BUZZ_RELAY_URL`
(default `http://localhost:3000`), `BUZZ_AUTH_TAG` (NIP-OA, opcional).
HTTP: `POST {relay}/query` e `POST {relay}/events` com
`Authorization: Nostr <base64 NIP-98>` + `x-auth-tag`.

**Brecha útil:** o bridge HTTP sempre exige NIP-98, mas o web client contorna com
**chave efêmera de página + NIP-42 sobre WebSocket** — é assim que `/repos` lista
kind:30617. O mesmo truque permitiria a um site listar personas kind:30175 `shared` ao
vivo, sem backend e sem pedir chave ao visitante.

---

## 6. A armadilha do RELAY_URL — confirmada, e pior

Existem **três normalizadores incompatíveis**:

| Função | Dobra loopback? | Usada como |
|---|---|---|
| `buzz_core::relay::normalize_relay_url` (`relay.rs:56-58`) | **sim** | identidade de processo no Desktop |
| `buzz_core::tenant::normalize_host` (`tenant.rs:121-137`) | **não** | **chave de comunidade** |
| `buzz_auth::nip42::normalize_relay_url` (`nip42.rs:24-29`) | sim | NIP-42 |
| `buzz_auth::nip98::normalize_url` (`nip98.rs:138-152`) | **não**, com teste dedicado | NIP-98 |

`ws://localhost:3000` e `ws://127.0.0.1:3000` são **comunidades diferentes** —
confirmado. Mas o sintoma que o PROMPT.md previu está errado: o host errado dá
**404 `"no community is configured for this host"`** (`router.rs:306-309`), **não 401**.
Só a autoridade do `RELAY_URL` do próprio relay é semeada no startup (`main.rs:260`).

O 401 NIP-98 acontece em cenário diferente: proxy reverso que reescreve `Host` — o relay
lê só o header `Host` cru, sem `X-Forwarded-Host`.

**Regra operacional mantida:** usar `127.0.0.1`, nunca `localhost`, e byte-a-byte igual
em todo cliente.

---

## 7. Model-agnostic: meia-verdade

- **`buzz-acp` não tem integração de SDK de provider.** (Correção 2026-08-06: a forma
  anterior — "zero menções a anthropic/openai/openrouter em `crates/buzz-acp/src/`" —
  era literalmente falsa: 1 menção em doc-comment de produção (`usage.rs:99-102`) e ~12
  em módulos `#[cfg(test)]` e copy de setup (`setup_mode.rs:711-746`, `acp.rs:4434`).
  O ponto substantivo sobrevive: nenhuma é integração — ele faz spawn de um binário
  arbitrário (`BUZZ_ACP_AGENT_COMMAND`), fala ACP e repassa env keys opacamente.)
- **`buzz-agent` tem enum fechado de 5 providers** (`config.rs:679-691`): `Anthropic`,
  `OpenAi`, `Databricks`, `DatabricksV2`, **`OpenRouter`**. Resolvido por match de string
  com erro em valor desconhecido (`config.rs:1053-1077`), despachado por um único
  `match cfg.provider` em `Llm::complete` (`llm.rs:132`). O próprio README admite:
  "There is no trait, no Box<dyn>, no async-trait" (`crates/buzz-agent/README.md:258`).
- Escape hatch: `provider=openai` + `OPENAI_COMPAT_BASE_URL` aponta para qualquer
  endpoint OpenAI-compatível.
- **OpenRouter é suportado nativamente** — bom para a Fase 4.

### O rótulo "Mixed models" olha o MODELO, não o provider — uma chave OpenRouter basta

Verificado em 2026-08-06 @ ed4b3e7a. A pergunta que destrava o crossfire: o time
precisa de três **contas** ou de três **modelos**?

- `[FONTE]` O rótulo vem de `getTeamFooterModelLabel`
  (`desktop/src/features/agents/ui/TeamIdentityCard.tsx:204-218`): mapeia
  `persona.model` por `formatAgentModelLabel`, deduplica **a string do modelo** em
  minúsculas e devolve `"Mixed models"` sse existe mais de uma string única.
- `[FONTE]` `formatAgentModelLabel` é trim-ou-"Auto"
  (`desktop/src/features/agents/lib/formatAgentModelLabel.ts:5-8`). **O provider não
  entra em nenhum ponto da cadeia do rótulo.**
- `[FONTE]` A credencial é por provider, não por agente: com `provider=openrouter` o
  único requisito de chave que o desktop verifica é `OPENROUTER_API_KEY`
  (`desktop/src-tauri/src/managed_agents/readiness.rs:527-532` e `:640-646`).
- `[FONTE]` O runtime resolve OpenRouter como provider de primeira classe:
  `OPENROUTER_API_KEY` + modelo por agente via `BUZZ_AGENT_MODEL` — "set by the desktop
  from the persona/record" (`crates/buzz-agent/src/config.rs:794-798` e `:834-843`),
  wire format Chat Completions em `https://openrouter.ai/api/v1`.
- `[FONTE]` A UI de configuração conhece `openrouter` por agente
  (`desktop/src/features/agents/ui/buzzAgentConfig.ts:131-133`).

**Consequência:** três agentes com `provider=openrouter` e três strings de modelo
distintas (ex.: `anthropic/claude-sonnet-5`, `openai/gpt-5`,
`deepseek/deepseek-chat`) rodam com **uma conta e uma chave**, continuam sendo três
modelos de três fabricantes — os blind spots continuam não sobrepostos — e o card do
time continua exibindo "Mixed models", porque as strings diferem. O pack
`crossfire-review` mantém os três providers nativos como ideal declarado; o caminho de
uma chave é o quickstart documentado em `docs/LOCAL-SETUP.md` (decisão D-033).

`[INFERIDO]` O que se perde no caminho de uma chave: um único gateway é ponto único de
falha, de billing e de log — a independência **operacional** dos três reviewers cai,
a independência **de modelo** permanece. Cadeia: os pesos são de fabricantes distintos;
o transporte é que converge.

### BYOH

Três tiers no Desktop. Tier-3 (usuário) é JSON com exatamente 7 campos —
`HarnessDefinition` (`custom_harnesses.rs:49-70`): `id`, `label`, `command`, `args`,
`env`, `installInstructionsUrl`, `installHint`. **Zero campo de model/provider.**

Contrato de fio que um harness precisa cumprir: `initialize` (protocolVersion 2),
`session/new` com `mcpServers` + `sessionId` de volta, `session/prompt` com `stopReason`,
notificação `session/update`, `session/cancel`. Opcionais: `authenticate`,
`session/set_config_option`, `session/set_model`.

### MCP

Três camadas: `buzz-acp` passa **no máximo um** servidor MCP stdio
(`BUZZ_ACP_MCP_COMMAND`) em `session/new`; `buzz-agent` é cliente MCP (rmcp) com
`MAX_MCP_SERVERS=16`; `buzz-dev-mcp` é o servidor MCP shipado.

`.env.example` **não contém nenhuma variável de LLM** — nem ANTHROPIC, nem OPENAI, nem
OPENROUTER. Só documentado em `crates/buzz-agent/README.md`.

---

## 8. Workflow

`crates/buzz-workflow`, engine YAML-as-code, escopado por canal e por community.

**5 chaves de topo:** `name` (obrigatória, não-vazia), `description`, `trigger`
(obrigatória), `steps` (obrigatória, ≥1), `enabled` (default true). Há uma 6ª,
`_webhook_secret`, que **não é do autor** — o relay injeta no JSON canônico armazenado.

**5 gatilhos** (enum internally-tagged pela chave `on`): `message_posted`,
`reaction_added`, `diff_posted`, `schedule`, `webhook`.
→ `ARCHITECTURE.md` ainda diz "4 trigger types" e omite `diff_posted` — doc desatualizada.

**7 ações** (chave `action`), das quais 4 executam: `send_message` (via trait
`ActionSink`), `call_webhook` (guarda SSRF, sem redirect, cap 1 MiB), `add_reaction`
(HTTP para a REST do relay, só com feature `reqwest`), `delay` (max 270s).
`send_dm` e `set_channel_topic` → `NotImplemented` (WF-07). `request_approval` suspende
e marca o run como `Failed` (WF-08).

**Condições:** evalexpr mesmo, crate `evalexpr` "11" (lockfile 11.3.1), `HashMapContext`,
variáveis achatadas com underscore (`trigger_text`, `trigger_author`,
`trigger_channel_id`, `trigger_timestamp`, `trigger_emoji`, `trigger_message_id`,
`steps_<ID>_output_<FIELD>`), 4 funções custom (`str_contains`, `str_starts_with`,
`str_ends_with`, `str_len`), timeout 100ms, limite 4096 bytes por expressão.

**Não existe json-schema publicado** do workflow: `schema/` só tem `schema.sql`.
**Não existem workflows de exemplo** em `examples/`; os únicos YAMLs completos estão em
`ARCHITECTURE.md`, `VISION_PROJECTS.md`, `crates/buzz-cli/TESTING.md` e em testes.

### Crossfire review

**Não é feature nem convenção.** Grep case-insensitive no repo inteiro (docs, VISION*,
CHANGELOG, testes, `.claude/`, `.agents/`, `.codex/`, `.goose/`, `.intersect/`) retorna
**exatamente 2 ocorrências**, ambas em `VISION.md` (linhas 169 e 212), como prosa sobre
processo de desenvolvimento assistido por IA. Zero ocorrências no `buzz-directory`.

→ O nome está livre. Mas a implementação não pode ser "workflow dispara o time", porque
não há ação que invoque agente.

### 8.1 Fase 4 redesenhada — registro da mudança

**A mudança foi imposta pelo runtime, não escolhida por conveniência.** Registrado aqui
porque o `PROMPT.md` §7 especificava "um workflow YAML disparando o time em evento de
patch", e isso não é construível.

`ActionDef` é um enum serde internally-tagged pela chave `action`
(`crates/buzz-workflow/src/schema.rs:91-92`) com **exatamente 7 variantes**:

| Variante | Chave YAML | Linha | Executa? |
|---|---|---|---|
| `SendMessage` | `send_message` | `schema.rs:94` | ✅ via trait `ActionSink` |
| `SendDm` | `send_dm` | `schema.rs:102` | ❌ `NotImplemented` (WF-07) |
| `SetChannelTopic` | `set_channel_topic` | `schema.rs:109` | ❌ `NotImplemented` (WF-07) |
| `AddReaction` | `add_reaction` | `schema.rs:114` | ✅ só com feature `reqwest` |
| `CallWebhook` | `call_webhook` | `schema.rs:119` | ✅ guarda SSRF, sem redirect, cap 1 MiB |
| `RequestApproval` | `request_approval` | `schema.rs:133` | ⚠️ suspende, mas marca o run `Failed` (WF-08) |
| `Delay` | `delay` | `schema.rs:143` | ✅ máx. 270s |

**Nenhuma cria, aciona ou invoca agente.** Não há `spawn_agent`, `invoke_persona`,
`run_team` nem equivalente. O enum é fechado; um workflow não pode fazer o que não está
nessa lista.

**Desenho novo:** o workflow dispara em `message_posted` (ou `diff_posted`) e emite um
único `send_message` que **menciona** os três agentes. Cada agente responde porque está
inscrito no canal e o filtro de menção casou — tag `p` == pubkey do agente
(`crates/buzz-acp/src/filter.rs:93`, avaliado em `filter.rs:390-399`). Ver §3 para a
ressalva sobre "ligado por padrão": vale para `--subscribe mentions`, não para regra
TOML manual.

Dois efeitos colaterais, ambos favoráveis:

1. **Fica mais alinhado à tese do Buzz.** Invocar agente por workflow o trata como
   função; mencionar num canal o trata como participante. O segundo é o modelo deles.
2. **Os três providers distintos continuam nativamente suportados** — `TeamRecord` não
   carrega modelo, cada `AgentDefinition` tem runtime/model/provider próprios
   (`desktop/src-tauri/src/managed_agents/types.rs:24/29/34`), sem validação de
   homogeneidade. E `buzz-agent` suporta OpenRouter nativamente
   (`config.rs:679-691`).

O que se perde: determinismo de orquestração. Ninguém garante que os três respondam,
nem em que ordem. Isso é característica do modelo de participação, não defeito da
implementação — mas precisa estar dito no README, e o vídeo de demo precisa ser gravado
sabendo disso.

---

## 9. buzzdir como referência de frontend

**Licença: MIT real** (`LICENSE`, 21 linhas, "Copyright (c) 2026 buzzdir contributors").
Reaproveitamento livre — uso, cópia, modificação, sublicenciamento, uso comercial — com
**uma** obrigação: carregar junto o aviso de copyright e o texto da permissão em cópias
ou porções substanciais. Sem share-alike.

→ A trava 2.2 do PROMPT.md está resolvida: **pode copiar código**, desde que credite.
A recomendação de reimplementar em vez de colar continua valendo por identidade visual
(seção 6.4), não por licença.

**Stack:** Next 16.2.12, React 19.2.6, TS 5.9.3, Node ≥22.13.0. App Router, static
export puro (`output:"export"`, `trailingSlash:true`, `images.unoptimized:true`,
basePath dinâmico). Deploy GitHub Pages com actions pinadas por SHA. Dependências de
runtime: exatamente `next` + `react` + `react-dom`, travado por teste
(`tests/rendered-html.test.mjs:415-419`). Zero framework CSS — Tailwind foi removido.
7 arquivos em `app/`, 4076 linhas.

### Os 4 defeitos alegados

| # | Alegação | Veredito |
|---|---|---|
| a | `"Aptos Display"` sem `@font-face` | **CONFIRMADO** — `globals.css:55-56`; não há `@font-face`, `next/font`, `.woff` ou `.ttf` em lugar nenhum. Há fallback (Helvetica Neue/Helvetica/Arial) e o `README:84` declara "no webfonts" como decisão consciente. |
| b | `canonical`/`og:` em `http://` | **REFUTADO** — `canonical` e `og.url` são `"./"` relativos, resolvidos contra `metadataBase = "https://buzzdir.xyz/"`. O único `http://` em `app/` é o `xmlns` de um SVG data-URI. |
| c | CSP com `script-src 'unsafe-inline'` | **CONFIRMADO** — `layout.tsx:27` (e `style-src` idem na 28). Documentado como inevitável: Next inlina o bootstrap e o Pages não seta headers. |
| d | Dataset no bundle | **CONFIRMADO** — 48 hives em `app/communities.ts` (16.140 bytes), import estático em `page.tsx` que é `"use client"`. Sem `fetch()`, sem `.json`, sem import dinâmico. |

O defeito (b) do PROMPT.md **não existe** — não replicar essa "correção" como se fosse
mérito nosso.

### Técnicas de CSS

As 8 citadas existem, **com uma correção**: há unidades `cqi` mas **nenhuma regra
`@container`**. O texto escala por `cqi` sem container query declarada.

`createBeeField` (`app/beeField.ts:125`, arquivo de 700 linhas) é carregado por
`import()` dentro de `requestIdleCallback` com timeout 500 e fallback `setTimeout(120)`.

### Armadilha de reaproveitamento

`app/layout.tsx:31` — a CSP de produção tem `connect-src 'self'`; `ws:`/`wss:` só entram
quando `isDev`. O buzzdir nunca fala com relay, então passa. **Copiar essa CSP para um
frontend que precise abrir `wss://` para relays quebra em produção.** Relevante porque a
brecha da seção 5.3 (NIP-42 sobre WebSocket) depende exatamente disso.

---

## ⚠️ Não verificado

1. **`buzz-cli` tem 22 grupos de comando** — o número veio do teste
   `command_inventory_is_stable`; não enumerei os 22 um a um. Nenhum é de persona/team.
2. **Formato interno de `.agent.json` / `.team.json`** — sei que existem, que são
   aceitos no import e que `.agent.png` é PNG com payload embutido. **Não li o schema.**
   É o formato do único artefato hoje instalável por URL pública, então é leitura
   obrigatória antes da Fase 3.
3. **Blossom / `require_media_get_auth`** — li que o default é `false`. Não verifiquei o
   ciclo de vida do blob, se expira, nem se o relay de produção mantém esse default.
4. **`docs/nips/NIP-AP.md`** — sei que existe e que diverge do código em pelo menos um
   ponto (`NIP-AP.md:103` ainda diz que `respond_to`/`parallelism` são "reserved /
   parsed but not applied", mas o desktop já os carrega e valida). Não li integral.
5. **Se o relay de desenvolvimento em `deploy/compose/` sobe no Docker desta máquina** —
   o bundle existe (`compose.yml`, `compose.dev.yml`, `compose.caddy.yml`, `Caddyfile`,
   `run.sh`) mas não foi executado. É a Fase 1.
6. **Estado do join aberto por padrão** — o PROMPT.md afirma; não localizei o default no
   código nesta passada.
7. **`buzz pack validate` como gate de CI** — sei que existe e o que valida em linhas
   gerais. Não li `validate.rs` (1070 linhas) regra a regra.

---

## Decisões travadas por isso

| Incerteza / achado | Decisão que ele bloqueia ou muda |
|---|---|
| Pack não tem runtime (§0.1) | **Bloqueia o DoD inteiro do pack.** Ou o Killer Bee gera `.agent.json`/`.team.json` (formato real de import) em vez de `.buzzpack`, ou aceita que "instalar" significa copiar/colar um system prompt. Decisão de produto, não técnica. |
| Formato de `.agent.json` não lido (§⚠️2) | Bloqueia escolher entre as duas saídas acima. **Primeira leitura da Fase 1.** |
| `deny_unknown_fields` no frontmatter (§2.2) | O perfil scutellata não pode ser campo de persona. Vai para `killerbee.yaml` próprio + `docs/PROFILE-COMPILATION.md`. Confirma a intuição da seção 5.3 do PROMPT.md, mas por um motivo mais duro do que o previsto. |
| Nenhuma ação invoca agente (§0.3) | **Redesenha a Fase 4.** Crossfire vira: workflow `message_posted` → `send_message` mencionando os 3 agentes → cada um responde por menção. Não é orquestração, é convite. |
| Team referencia persona por UUID local (§3) | Um team exportado não se reconstitui em outra máquina. Ou o Killer Bee emite 30178 (embute membros), ou o "time" é só uma lista de personas que o usuário adiciona uma a uma. |
| 30178 é slot vazio (§3) | **A maior oportunidade encontrada.** Kind abençoado pelo protocolo, implementado no relay, sem nenhum cliente. Publicar/ler 30178 é contribuição real e não colide com ninguém. |
| Catálogo do desktop está vivo (§0.2) | Reescreve o parágrafo de missão do README. A lacuna é "catálogo público cross-comunidade na web", não "não existe catálogo". |
| "App Store UI" está no roadmap deles (`PERSONA_PACK_SPEC.md:900`) | **Risco de colisão com a seção 2.3 do PROMPT.md.** Está marcado "Details TBD" e é *Buzz-hosted*; o Waggle é estático e comunitário. Dá para conviver, mas tem que ser dito no README em vez de descoberto depois. |
| Sem deep link de install (§5.1) | Botão do Waggle = comando `buzz` copiável + download. Confirma a previsão do PROMPT.md. |
| Chave efêmera + NIP-42 sobre WS (§5.3) | Abre a opção de o Waggle mostrar personas **ao vivo** de um relay, não só packs estáticos do repo. Muda o que o site é. |
| CSP `connect-src 'self'` do buzzdir (§9) | Se adotarmos a opção acima, a CSP não pode ser copiada do buzzdir. |
| Sem faixa de kind para terceiros (§1) | Killer Bee não inventa kind. Usa 30175/30176/30178 ou nada. |
| Três normalizadores de URL (§6) | `127.0.0.1` em tudo, byte-a-byte. E o sintoma esperado de erro é 404, não 401 — documentar em `LOCAL-SETUP.md` para não caçar o erro errado. |
| Defeito (b) do buzzdir é falso (§9) | Remover da lista de "coisas que vamos corrigir". Manter (a), (c), (d). |

---
---

# Fase 1 — E1 e E2

Leitura de 2026-08-05, mesmo commit `ed4b3e7a`. Dois leitores independentes, cada um
seguido de verificação adversarial de citação.

## 10. O formato de snapshot — o que o Killer Bee vai emitir (E1)

Esta é a camada **L2**: o único artefato que o Buzz Desktop realmente importa hoje.

### 10.1 `.agent.json`

Struct `AgentSnapshot` (`desktop/src-tauri/src/managed_agents/agent_snapshot.rs:164-174`),
`#[serde(rename_all = "camelCase")]`.

Obrigatórios no topo:

| Campo | Tipo | Valor |
|---|---|---|
| `format` | String | literal `"buzz-agent-snapshot"` |
| `version` | u32 | `1` |
| `definition` | objeto | ver abaixo |
| `profile` | objeto | ver abaixo |
| `memory` | objeto | ver abaixo |

- **`definition`** — `name` (String, obrigatório) + opcionais com default:
  `sourceIsBuiltIn`, `systemPrompt`, `runtime`, `model`, `provider`, `parallelism` (u32),
  `respondTo`, `respondToAllowlist` ([String]), `namePool` ([String]),
  `idleTimeoutSeconds`, `maxTurnDurationSeconds`.
- **`profile`** — `displayName` (obrigatório) + `about`, `avatarDataUrl`
  (`data:...;base64`), `avatarUrl`.
- **`memory`** — `level` (obrigatório, snake_case: `none` | `core` | `everything`)
  + `entries` (`[{slug, body}]`, default vazio).

#### Por que é seguro omitir campo opcional

O emissor do Killer Bee escreve só o que tem valor. Isso só funciona porque **todo campo
que omitimos carrega `#[serde(default)]`** — conferido campo a campo em
`agent_snapshot.rs:96-119` (`sourceIsBuiltIn`, `systemPrompt`, `runtime`, `model`,
`provider`, `parallelism`, `respondTo`, `respondToAllowlist`, `namePool`,
`idleTimeoutSeconds`, `maxTurnDurationSeconds`) e `:126-137` (`about`, `avatarDataUrl`,
`avatarUrl`).

Os únicos campos **sem** default, e portanto obrigatórios na desserialização, são:
`format`, `version`, `definition`, `profile`, `memory` no topo; `definition.name`;
`profile.displayName`; `memory.level`. O emissor escreve os oito, sempre.

Isso importa porque serde falha o parse inteiro em campo obrigatório ausente. Um snapshot
a que faltasse `profile.displayName` não daria erro de validação com mensagem amigável —
daria erro de parse antes de qualquer validação rodar.

### 10.2 `.team.json` — embute os membros

Struct `TeamSnapshot` (`team_snapshot.rs:76-87`): `format == "buzz-team-snapshot"`,
`version == 1`, `team { name obrigatório, description?, instructions? }`, e
**`members: Vec<AgentSnapshot>`**.

**O team snapshot EMBUTE o `AgentSnapshot` completo de cada membro — não referencia ids.**
Mínimo um membro; cada um revalidado por `validate_snapshot`.

Isso resolve a dúvida Q-004 a favor: o problema dos `persona_ids` como UUID local (§3)
**não afeta o snapshot**. Um `.team.json` gerado pelo Killer Bee se reconstitui em
qualquer máquina, porque carrega os membros inteiros dentro de si.

### 10.3 Campo desconhecido: aceito, mas descartado

A pergunta mais importante de E1, e a resposta tem duas metades que puxam para lados
opostos.

**Aceito:** não há `deny_unknown_fields` em nenhum `.rs` de `desktop/src-tauri` (29
ocorrências no repo, zero no desktop), e não há Zod no caminho de import. Os parsers são
`serde_json::from_slice` cru (`agent_snapshot.rs:288`, `team_snapshot.rs:119-120`,
`envelope.rs:176` e `:188`). Uma chave `x_killerbee_profile` **não quebra o import**.

**Descartado:** o preview **reserializa a struct** —
`serde_json::to_string_pretty(snapshot)` em
`desktop/src-tauri/src/commands/personas/snapshot/import.rs:410`. O campo extra não
aparece no "Full embedded manifest", não é persistido, e não sobrevive a um round-trip
export→import. Não há preservação de campos desconhecidos.

**Consequência para o perfil scutellata.** Ele não pode viajar no snapshot, do mesmo jeito
que não pode viajar no frontmatter da persona (§2.2 — lá por erro fatal, aqui por descarte
silencioso). O perfil vive em **L1**, no manifesto do Killer Bee, e é **compilado** para
os campos nativos que o snapshot carrega:

| Campo scutellata | Compila para | Natureza |
|---|---|---|
| `recruitment` | `definition.parallelism` (1..=32) | campo nativo |
| `threshold` | `definition.respondTo` + `respondToAllowlist` | campo nativo |
| `persistence` | `definition.idleTimeoutSeconds` / `maxTurnDurationSeconds` | campo nativo |
| `propagation` | nada no runtime — é metadado de catálogo | só L1 |

O que não compilar para campo nativo vira texto no `systemPrompt`. Documentar em
`docs/PROFILE-COMPILATION.md`.

### 10.4 O PNG é gerável fora do app

Chunk **`tEXt`** (não `iTXt`, não `zTXt`) — o encoder usa `add_text_chunk`
(`agent_snapshot.rs:431` e `:486`); o decoder lê apenas
`info.uncompressed_latin1_text` (`:362`, team em `:156`).

- Keyword: `buzz_agent_snapshot` (`:53`) / `buzz_team_snapshot` (`team_snapshot.rs:49`)
- Payload: `base64(STANDARD)` do JSON do manifesto (`:324`)
- O chunk tem que vir **antes do IDAT** (`media_snapshot_png.rs:55-58`)
- Corpo da imagem: avatar do agente no `.agent.png`; 1×1 transparente no `.team.png`

**Gerável com qualquer biblioteca PNG.** O `.agent.png` é o formato mais interessante para
o Waggle: tem URL pública hoje via Blossom (§5.2) — e, correção 2026-08-06, o
`.team.png` também (mesmo dialog de share, `snapshotKind="team"`).

**Adendo 2026-08-06 (segunda rodada de leitura, verificada por segundo leitor):**

- **O corpo do PNG é ADOTADO como avatar do agente no import** quando o manifesto não
  traz `avatar_data_url` inline: `parse_snapshot_payload_from_bytes` decodifica o corpo
  e o injeta como avatar (`import.rs:242-261` — "The PNG image body is the portable
  avatar"). Limites dessa adoção em `snapshot_avatar.rs:5-7`:
  `MAX_AVATAR_DIMENSION = 2048` (lado maior **falha o import**, propagação com `?`),
  `MAX_AVATAR_INLINE_BYTES = 2 MiB`, `MAX_AVATAR_DECODE_ALLOC = 32 MiB`.
  ⚠️ Leitura de fonte — adoção como avatar ainda NÃO vista no app rodando (D-017).
- Há um TERCEIRO produtor de corpo de `.agent.png` no upstream além do export
  (avatar) e do fallback 1×1: o fluxo de **Agent Trading Cards** (`card.rs`), que gera
  arte 2:3 por IA como corpo, com o avatar real inline no manifesto.
- O corpo aparece no app em pelo menos quatro superfícies: thumb 36×36 do card de
  chat; viewer de card (~448 px, `AgentCardViewerDialog.tsx:170-179`); tiles da
  galeria; e como avatar do agente importado.
- O sanitizador de PNG preserva o chunk de snapshot
  (`media_snapshot_png.rs:87+`, `test_sanitizer_preserves_agent_snapshot_text_chunk`).

### 10.5 Quantos cliques — o número que vai no site

> **Corrigido em 2026-08-05 contra o app rodando (0.5.5).** Ver [§10.9](#109-verificação-no-app-real--2026-08-05).
> O número estava certo; dois detalhes ao redor dele, não.

Arquivo em disco: sidebar **Agents** → card **`+`** → **Import** → seletor de arquivo do
SO → dialog de preview → **Import**. **4 cliques no app + 1 no seletor.**

- O card **não exibe o texto "New agent"**. É um card `+` (só o ícone Plus) que abre um
  menu de três entradas: **Create agent**, **Discover agents**, **Import**. Em teams o
  menu tem duas: **Create team** e **Import**. Nuance 2026-08-06: na camada de
  acessibilidade ele **é** "New agent" — `aria-label="New agent"`, test id
  `new-agent-card` (`UnifiedAgentsSection.tsx:452`); leitores de tela e seletores e2e
  o chamam assim.
- ~~Arrastar e soltar sobre a seção Agents pula 2 cliques.~~ → **corrigido de novo em
  2026-08-06: EXISTE alvo de drop no fonte.** A rodada anterior "confirmou ausência"
  enumerando `onDrop=` (dez handlers, nenhum na seção) e citando
  `"dragDropEnabled": false` (`tauri.conf.json:27`). Dois erros de método, ambos
  instrutivos: **grep de atributo não enxerga handler espalhado por spread** —
  `UnifiedAgentsSection.tsx:105-137` espalha `{...dropHandlers}` vindos de
  `useFileImportZone.ts:29-36`, com overlay "Drop .agent.json or .agent.png to import"
  — e `dragDropEnabled: false` desliga o handler NATIVO do Tauri, que é exatamente o
  que deixa o `onDrop` do DOM disparar. Estado: `[FONTE]` no pin ed4b3e7a;
  comportamento no app 0.5.5 `[NÃO VERIFICADO]` — ninguém soltou um arquivo num app
  rodando ainda. Lição registrada em [D-035](DECISIONS.md). Esta linha chegou ao site e foi
  publicada; agora há teste que impede o retorno.
- ⚠️ **NÃO VERIFICADO:** "recebido por chat: card com **Add agent** → dialog → **Import**
  = 2 cliques". Nunca foi exercitado num app rodando; só lido no fonte.
- Teams: card `+` → **Import**, aceita `.team.json` / `.team.png`.
- O seletor de arquivo filtra por tipo: o import de agente lista só `*.agent.json` e
  `*.agent.png`; o de team, só `*.team.json` e `*.team.png`. Observado — `acp-rules.toml`
  e `catalog.json` não aparecem em nenhum dos dois.

### 10.6 Importado não é rodando

`import.rs` grava `start_on_app_launch: false` (`:624`), `runtime_pid: None` (`:626`),
`agent_command: String::new()` (`:610`) e `env_vars: BTreeMap::new()` (`:623`) — **sem
chave de API**.

**`acp_command` é a exceção e não fica vazio:** `import.rs:609` grava
`DEFAULT_ACP_COMMAND`, que é `"buzz-acp"` (`managed_agents/types.rs:809`). O painel
Runtime do agente importado mostra `ACP command: buzz-acp`, e quem esperasse campo vazio
ali leria como bug. O comentário em `:607-608` explica: comandos de máquina se derivam do
catálogo de runtime, nunca se fabricam a partir do snapshot.

Para rodar, o agente ainda precisa da **chave do provider**, vinda da configuração
global do app. `model` e `provider`, quando presentes no snapshot, **viajam com ele** e
são gravados no import (`import.rs:620-621`; confirmado no app em §10.9, linhas
"Mixed models") — `BUZZ_AGENT_PROVIDER`/`BUZZ_AGENT_MODEL` globais entram como fallback
quando o snapshot os omite. (Correção 2026-08-06: a redação anterior dizia que provider
e model vinham da config global, contradizendo o §10.9 deste mesmo documento; flagrada
por segundo leitor adversarial.) E o import **não coloca o agente em canal nenhum** —
"Add to channel" é ação separada, no painel de perfil.

**O site tem que dizer isso.** "Importar" não é "rodando": são três passos, e o terceiro
depende de credencial que o usuário fornece.

### 10.7 O que viaja e o que não viaja

**Viaja:** `systemPrompt` inteiro, sem truncagem — o que sustenta a promessa de
transparência do catálogo. Mais `runtime`, `model`, `provider`, `parallelism`.

**Não viaja:** `env_vars`, `nsec`, `auth_tag`, `relay_url`, comandos de máquina, ids de
linhagem. `profile.about` é parseado mas **descartado** no import
(`sync_managed_agent_profile` só recebe `display_name` + `avatar`).

### 10.8 Validação no import

Rejeita: nome legado (`.persona.md`, `.persona.json`, `.persona.png`, `.zip`); tamanho
(5 MiB JSON / 10 MiB PNG para agente; 25 / 50 MiB para team); `format` exato;
`version == 1`; `definition.name` e `profile.displayName` não-vazios; `memory.level` igual
a `none` com `entries` não-vazio; allowlist de 64 hex; `respondTo` em
`{owner-only, allowlist, anyone}`; `parallelism` em `1..=32`; team com ao menos 1 membro.

Magic bytes são sniffados — **a extensão é ignorada**.

### 10.9 Verificação no app real — 2026-08-05

Até aqui todo o §10 era conformidade com o fonte lido. Isto é o registro da primeira vez
que os arquivos emitidos pelo Killer Bee entraram num **Buzz Desktop rodando**.

**Versão.** `C:\Users\saulo\AppData\Local\buzz\buzz-desktop.exe` → `FileVersion 0.5.5`,
idêntica a `desktop/src-tauri/tauri.conf.json` do clone em `ed4b3e7a`. **Sem skew.**
O instalador `Buzz_0.4.25_x64-setup_alpha-unsigned` parado em `Downloads` é lixo antigo —
inferir a versão do app pelo nome desse arquivo teria produzido um falso "duas versões
diferentes", que é o erro D-014 na forma clássica.

| Artefato | Resultado | O que isso prova |
|---|---|---|
| `forager.agent.json` | ✅ `Forager was created successfully` | O `.agent.json` do emissor passa por `validate_snapshot` e cria o registro |
| `adversary.agent.png` | ✅ `Adversary was created successfully` | **O chunk `tEXt` gerado fora do app decodifica.** Era a aposta de §10.4 e o que sustenta a distribuição via URL |
| `crossfire-review.team.json` | ✅ `created successfully with 3 members` | Membros embutidos se reconstituem: preview lista Forager, Adversary e Guard |

**O que sobreviveu.** O "Full embedded manifest" do preview reserializa e mostra
`parallelism: 4`, `respondTo: "anyone"`, `idleTimeoutSeconds: 900`,
`maxTurnDurationSeconds: 1800`. **Os três eixos scutellata que compilam para campo nativo
atravessam o import intactos** — `recruitment`, `threshold` e `persistence` deixam de ser
promessa de [`PROFILE-COMPILATION.md`](PROFILE-COMPILATION.md) e viram fato observado.

**O que a reserialização descarta.** Arrays vazias somem: `respondToAllowlist: []`,
`namePool: []` e `memory.entries: []` não aparecem no manifesto reexibido, efeito de
`skip_serializing_if`. O emissor escreve as três; é inofensivo, mas quem comparar o
arquivo com a tela vai ver diferença.

**Três providers, confirmados na UI.** `Forager → claude-sonnet-5`,
`Adversary → gpt-5`, `Guard → deepseek/deepseek-chat` com `Provider: openrouter`. O card
do team recebe o rótulo **"Mixed models"** do próprio app. O painel Runtime marca model e
provider como *inherited from template* — vêm do snapshot, não do padrão global.

**"Importado não é rodando", medido e não deduzido.** No perfil do Guard recém-importado:
`Status: STOPPED`, `Start on launch: No`, aba **Channels vazia** com "Add this agent to a
channel — choose a channel above so it can join the conversation", `Memories 0`.
`Public key 6ccba27b…96aa`, chave nova: **identidade não viaja**, como o preview promete.

**Achado novo: o import de team não deduplica.** Importar `crossfire-review.team.json`
depois de já ter importado Forager e Adversary avulsos criou **outro** Forager e **outro**
Adversary, com keypairs novos — oito agentes onde se esperaria seis. O team snapshot
embute os membros e o import os materializa sem procurar por nome. Consequência prática
para o site: **importe o team OU as personas, não os dois.**

## 11. Kind 30178 — veredito da camada L3 (E2)

### 11.1 Não existe schema implementado

Nenhuma struct Rust, nenhum tipo TS, nenhum serde serializa o corpo do 30178 em todo o
repo. O grep por `30178` / `TEAM_CATALOG` / `team_catalog` só acerta `kind.rs`,
`ingest.rs`, `e2e_team_catalog.rs`, `count.rs`, `req.rs`, `event.rs`, `NIP-AP.md`,
`CHANGELOG` e `ci.yml`.

O único schema é **fixture de teste**, idêntica em dois lugares
(`e2e_team_catalog.rs:35` e `ingest.rs:4111`):

```json
{"v": 1, "name": "<string>", "members": []}
```

`members` está **vazio nas duas**. A forma da projeção de membro **não existe em lugar
nenhum** — só prosa em `kind.rs:296-298` ("ordered, EMBEDDED member definition
projections") e `NIP-AP:301` / `:242` (sanitizada: sem env vars, sem `respond_to`, sem ids
locais, sem paths, sem segredos).

E a NIP-AP é explícita em `NIP-AP:223`: **"The content schema is defined by the client
that publishes it"** — o relay não valida conteúdo.

### 11.2 O que o ingest exige

`validate_team_catalog_envelope` (`ingest.rs:1163`) = `validate_shared_tag` +
`single_bounded_d_tag`:

- exatamente um tag `d`, valor não-vazio, **até 64 caracteres** (não bytes), sem control
  chars nem whitespace
- `shared` opcional; se presente, exatamente `["shared","true"]` com 2 elementos, no
  máximo um
- **não** aplica a gramática de slug do 30175 — dois-pontos é legal aqui
- sem limite de quantidade de membros, sem validação de conteúdo
- conteúdo até 256 KB (`ingest.rs:1868`)

Erros viram prefixo `invalid: {e}` (`ingest.rs:2415`).

### 11.3 Quem pode publicar

`required_scope_for_kind(30178) = Scope::UsersWrite` (`ingest.rs:217`). A única outra
checagem é `event.pubkey` igual à identidade autenticada (`ingest.rs:1878`).

**Não há gate de owner, admin ou role**, e não há verificação de que o team exista como
30176. Qualquer pubkey autenticado publica o seu. NIP-33 já limita substituição ao próprio
pubkey. É `is_global_only_kind` — nunca escopado a canal.

### 11.4 O teste e2e cobre leitor estrangeiro

Nove testes `#[ignore]` em `e2e_team_catalog.rs` (recontado 2026-08-06; uma versão
anterior dizia sete). O fluxo de leitura estrangeira
(`:236`): o autor publica um 30178 sem `shared` e outro com; um leitor estrangeiro, com
chave própria e **autenticado**, faz `REQ {kind:30178, author:<autor>}` e vê **só o
shared**. O autor vê os dois. Também cobre: ids-lookup do unshared devolve vazio (`:304`),
COUNT devolve 1 (`:345`), fan-out ao vivo entrega só o shared, e o "unshare" — substituição
sem a tag — **retrata** o evento do leitor estrangeiro (`:398`).

**Não há teste de leitura anônima.**

### 11.5 VEREDITO — L3 vai de 30178, com uma ressalva que muda o site

**Tecnicamente serve.** O 30178 com `["shared","true"]` é legível por qualquer leitor
autenticado, o relay não valida o corpo, publicar só exige a própria chave, e o kind é
global. Nada impede um terceiro de publicar no próprio relay: licença Apache-2.0,
`require_relay_membership` default `false` (`config.rs:532-534`), nenhum allowlist de kind
por operador, nenhum registro de kind, nenhuma assinatura da Block exigida.

**A ressalva dura:** `REQ` exige NIP-42. Conexão não autenticada recebe
`auth-required: authenticate before subscribing` (`req.rs:77`). **Não existe leitura
anônima.**

Isso **corrige** o que a Fase 0 registrou em §5.3. A chave efêmera de página não é um
atalho opcional — é **obrigatória**. O site precisa gerar um keypair por carregamento e
fazer NIP-42 antes de listar qualquer coisa. Continua sem backend, mas deixa de ser "só
fazer fetch", e a CSP tem que liberar `wss:` (§9).

**Outros limites que entram no desenho:**

- tag `d` até 64 caracteres — o id do team precisa caber
- conteúdo até 256 KB — com system prompts embutidos, um time grande estoura; medir antes
- **zero interoperabilidade hoje** — nenhum cliente Buzz publica ou lê 30178, então o que
  publicarmos só será lido pelo nosso site até alguém mais implementar
- **o schema dos membros teria que ser inventado do zero** pelo Killer Bee

Esse último ponto é a decisão real. A NIP-AP delega o schema ao cliente publicador, o que
faz de definir a projeção de membro do 30178 uma **contribuição de fato ao ecossistema** —
e também nos torna os únicos responsáveis por ela estar certa.

**Recomendação:** derivar a projeção de membro do 30178 diretamente do `AgentSnapshot`
(§10.1), removendo o que a `NIP-AP:242` manda sanitizar. Assim o mesmo objeto serve às
duas camadas, L2 e L3, e um leitor futuro do 30178 reconstrói um `.agent.json` sem
tradução.

---

## 12. To the Buzz maintainers — findings you may want, ordered by impact

*This section is written in English, addressed to whoever at `block/buzz` reads one
document from this repo. Everything below was verified against
`ed4b3e7afafb5f5a688c210f39b90d747e6f0f00` by direct reading plus an independent
adversarial pass; every negative claim's search receipt is in
[`NEGATIVE-SPACE.md`](NEGATIVE-SPACE.md). Each item ends with one objective
question — the section exists to be cut and pasted.*

**1. `subscribe=config` + omitted `require_mention` silently subscribes an agent to
the whole channel.** `#[serde(default)]` on the rule field (`buzz-acp/src/filter.rs:82-93`)
plus most-permissive-wins merging (`config.rs:1288-1310`) means one hand-written rule
that forgets one key drops the `#p` filter from the NIP-01 REQ (`crates/buzz-acp/src/relay.rs:3183-3196`).
Compounding it, the only README example showing `require_mention` uses a
`[channel.*]` table shape that `load_rules` never reads (`README.md:237-242` vs
`config.rs:1155-1159`) — a user following the README gets zero rules and a warning.
*Question: is most-permissive-wins the intended merge semantic, or an artifact worth
changing while nobody depends on it?*

**2. Kind 30178 is relay-complete and client-absent, and its body is anyone's to
define.** Ingest scope, envelope validation, shared-gating at REQ/ids/COUNT, and an
e2e suite all exist (`ingest.rs:2413-2416`, `req.rs:1228-1236`, `count.rs:102-110`,
`e2e_team_catalog.rs`); no client publishes or reads it, and NIP-AP.md:223 delegates
the content schema to the publishing client. The first external publisher (us, at the
moment) defines the de-facto format unilaterally — which is a fork risk wearing a
convenience costume. We published our projection as a JSON Schema and would rather
track one you own. *Question: would you take a NIP-AP amendment or a
`TeamCatalogContent` struct PR?*

**3. Workflow actions cannot touch agents — except through an undocumented string
side-channel.** 7 `ActionDef` variants (`buzz-workflow/src/schema.rs:90-131`): 4
functional, `SendDm`/`SetChannelTopic` are `NotImplemented` stubs, `RequestApproval`
suspends into a run-failure (`executor.rs:661-668`, `lib.rs:229-245`). None invokes an
agent — but a `send_message` whose text @-mentions an agent gets p-tagged by
`workflow_sink.rs:22-45` and wakes it. *Question: is the mention side-channel
intended, and is a first-class agent action on the WF-07/WF-08 roadmap?*

**4. The snapshot-PNG trading-card format lives only in source.** Keyword
`buzz_agent_snapshot`, base64 JSON in a tEXt chunk that must precede IDAT
(`media_snapshot_png.rs:54-58`), magic-bytes routing (`import.rs:213,232-233`),
body-becomes-avatar with asymmetric limits (`snapshot_avatar.rs:18-37`), and a
relay-side validator stricter than the desktop reader
(`buzz-media/src/validation.rs:592-646`). Zero files under `docs/` mention any of it.
We reconstructed a spec with a reproduction recipe
([`ISSUES-DRAFT.md`](ISSUES-DRAFT.md), issue 4). *Question: do you want it as
`docs/spec/agent-snapshot-png.md`?*

**5. `PERSONA_PACK_SPEC.md` is 43/91 implemented, and the biggest gap is hooks.**
Full four-state table in [`SPEC-VS-IMPL.md`](SPEC-VS-IMPL.md): 21 features absent, 25
divergent. The sharpest cluster: pack-level `hooks_config` is parsed then deliberately
dropped (`manifest.rs:114-116`), per-persona hooks are parsed and never executed
anywhere, yet the spec documents a full execution contract (stdin, 5s SIGKILL,
exit-code semantics). Smaller but surprising: `engines.buzz` is parsed and never
compared to anything; `$AGENT_CWD` resolution silently falls back to `/` where the
spec says refuse-to-start (`buzz-acp/src/lib.rs:1599-1602`). *Question: is the spec
aspirational-by-design (worth a status column?) or should divergences be issues?*

**6. One stale-doc trap we fell into ourselves, offered as a warning.** We publicly
claimed the Agents section has no drag-and-drop target after enumerating `onDrop=`
handlers — and missed `{...dropHandlers}` spread from `useFileImportZone.ts:29-36`
into `UnifiedAgentsSection.tsx:105-137`. Attribute greps do not see spread props;
`dragDropEnabled: false` in tauri.conf.json disables only Tauri's native handler and
is precisely what lets the DOM `onDrop` fire. If your docs ever assert UI absences,
enumerate the behavior, not the syntax. *(No question — just the receipt, in
[D-035](DECISIONS.md).)*
