# Killer Bee — persona and agent-team packs for Buzz

In 1956 Warwick Estevam Kerr brought African queens back to Brazil — **fifty from South
Africa and one from Tanzania, by his own account.**<sup>[1]</sup> They were kept at the
experimental apiary in Rio Claro, São Paulo, behind queen excluders that let only workers
through, so that only the gentler lineages would be selected. In **October 1957** someone
removed the excluders. **Twenty-six colonies escaped.** They crossed with the European
bees, took São Paulo, then Brazil, and today they are across all three Americas.

> **A note on that number, because it is the whole point of this project.** The 26 that
> escaped is consistent across every source we checked. The number Kerr *brought* is not:
> published accounts give 36, 47, 49, 51, 56, and 63. The 51 above is Kerr's own telling,
> in an academic interview nearly fifty years after the fact.<sup>[1]</sup> We use it, we
> attribute it, and we say it is disputed — rather than picking the number that makes the
> better story. Full trail in [`docs/BIBLIOGRAFIA.md`](docs/BIBLIOGRAFIA.md).
>
> Two related corrections, since we made both mistakes ourselves first: the escape was
> **1957**, a year after the importation, and calling Rio Claro "Unesp" in 1956 is an
> anachronism — the institution was then the Faculdade de Filosofia, Ciências e Letras de
> Rio Claro.

The researchers who study *Apis mellifera scutellata* prefer the word **defensive**, not
aggressive. And there is a detail that cuts against the myth: during swarming — the
moment the cloud looks most alarming, from the noise and the numbers — the bees have
**little tendency to sting**.

That is the thesis of this project, not a footnote. The swarm **looks** out of control
and is not. A system of agents that alarms you by its numbers while answering to defined
thresholds, with a signed trail and a human in the loop, is exactly what the Buzz
ecosystem says it wants.

---

## What this is

> **Buzz has a persona catalog inside each community. Killer Bee is the catalog between
> them.**

Buzz already solves *intra*-community discovery: a persona published as event kind 30175
with the `["shared","true"]` tag is readable community-wide and feeds the desktop's
"Discover agents" (`crates/buzz-core/src/kind.rs:187`). What does not exist is the step
after: a persona published in your hive is invisible to someone in another one, and
there is no public address to browse before joining anywhere.

Killer Bee fills that gap in three independent layers:

1. **L1 — the repo is the source of truth.** `packs/<name>/` with personas and teams in
   a readable, diffable manifest. This is the governance layer: what gets reviewed in a
   PR, forked, argued about. Needs no Buzz runtime to exist.
2. **L2 — emit what the desktop actually imports.** Agent and team snapshots, in the
   native format the app accepts today. This is the layer that makes a persona **run**.
3. **L3 — publish as signed events.** Personas as kind 30175 `shared`, teams as kind
   30178, on a relay of your own. This is the layer that makes the catalog **public and
   verifiable** instead of a list on a website. Today's honest state: upstream defines
   only the envelope — the 30178 *content* schema is explicitly left to the publishing
   client, so we published ours:
   [`schema/kind-30178-content.schema.json`](schema/kind-30178-content.schema.json)
   defines the member projection (the emitted snapshot minus what NIP-AP orders
   sanitized), and `killerbee event` emits the **unsigned** event ready for a signer.
   Signing and publishing require a key, and keys stay in human hands.

### A note on how this project corrects itself

This README's first draft claimed Buzz had no persona catalog at all, and that its
desktop UI had been removed. Reading the source proved both wrong. The claim was
corrected, the correction is recorded with citations in
[`PROMPT.md`](PROMPT.md#premissas-corrigidas-na-fase-0), and the original text was struck
through rather than deleted.

In a project whose product is verifiability, showing the correction is an asset, not an
embarrassment. Every factual claim in [`docs/PROTOCOL-NOTES.md`](docs/PROTOCOL-NOTES.md)
carries a `file:line` against a pinned upstream commit, and was checked by a second
reader that reopened the file.

## Quick start

```bash
uv sync
uv run python -m killerbee validate packs/crossfire-review
uv run python -m killerbee build packs/crossfire-review
```

`build` writes to `dist/<pack>/`:

| File | What it is |
|---|---|
| `<persona>.agent.json` / `.agent.png` | agent snapshot the desktop imports |
| `<team>.team.json` / `.team.png` | team snapshot, **members embedded in full** |
| `acp-rules.toml` | buzz-acp subscription rules, mention flag always explicit |
| `catalog.json` | index for the site, including every system prompt in full |

## Installing a pack — the honest click count

There is no one-click install in Buzz today. No `buzz install` command, no
`buzz://` deep link for personas. We would rather say so than ship a button that
promises more than it delivers.

1. Download the `.agent.json` (or `.agent.png`).
2. Buzz Desktop → **Agents** → the **`+`** card → **Import** → pick the file → confirm in
   the preview. **Four clicks plus the OS file picker.** There is no drag-and-drop
   shortcut — the Agents section has no drop target.
3. **Imported is not running.** The agent still needs provider credentials from the
   app's global config, and "Add to channel" is a separate action.

Import a **team** or the individual **personas**, not both: the team snapshot embeds each
member in full, and importing it after the personas creates duplicates.

Counted and confirmed in a running Buzz Desktop 0.5.5 on 2026-08-05 — including the
correction to step 2, which said something the app does not do.

## Orchestration is by mention, not by guarantee

The `crossfire-review` preset works like this: a workflow posts **one message mentioning
the three agents**, and each responds because the mention filter matched.

Nothing guarantees all three respond, nor in what order. That is not a limitation we
worked around — it is how Buzz models agents, as members rather than cron jobs. The
workflow engine has seven actions and **none of them invokes an agent**
(`crates/buzz-workflow/src/schema.rs:92`). A mention treats an agent as a participant; an
invocation would treat it as a function. We think the first is more honest, and it is
certainly more theirs.

## The scutellata profile — a response threshold model

The mechanism has an established name, and it is not "bee". These fields are a discrete
instance of the **response threshold model** of division of labour in social insects. In
its fixed-threshold form, an individual takes on a task with probability

```
P(act) = sⁿ / (sⁿ + θⁿ)
```

where `s` is stimulus intensity, `θ` the individual's threshold, and `n` the steepness
exponent — how sharply response switches on around `θ` (the literature typically fits
`n ≈ 2`). Technically this is a **Hill function** in `s` (equivalently, logistic in
`log s` — an earlier revision called it a "logistic gate", which is only right in log
space). Nothing more exotic than that, and **no algorithmic novelty is claimed here.**
The model is from the 1990s. What is ours is the mapping onto the fields Buzz's runtime
actually reads:

| Trait | Field | Compiles to |
|---|---|---|
| lower response threshold | `threshold` | `respondTo` + the ACP mention flag |
| recruits the swarm, not ten guards | `recruitment` | `parallelism` (native, 1–32) |
| pursues much further | `persistence` | idle and turn timeouts |
| swarms more often per season | `propagation` | nothing at runtime — catalog metadata |

To be precise about what runs: **the equation above is not computed anywhere in this
codebase.** There is no `s`, no measured stimulus, no `P` — today's implementation is the
degenerate case where the author picks one of three discrete `θ` levels and the gate is
compiled away into static fields (a lookup table in `killerbee/profile.py`, locked by a
property test: distinct profiles compile to distinct definitions, except `propagation`,
the one axis declared inert). Saying "static version" alone would be softer than the
truth. The adaptive variant — where `θ` moves with experience — now exists as **pure,
tested mathematics** in [`killerbee/threshold.py`](killerbee/threshold.py), and it is
**not wired to anything**: no agent's threshold moves, the manifest format is unchanged,
and `build` never calls it. Wiring it needs a running agent, which needs credentials.

Analysing it changed what we would have built. The fixed point has a closed form,
`θ* = s·(ξ/φ)^(1/n)` with execution rate `φ/(ξ+φ)`, and it is a **repeller**: the drift
grows with θ, so acting makes acting cheaper. An isolated agent under constant stimulus
does not settle at `θ*` — it runs away from it and saturates. So the backlog's own
phrasing ("convergence to specialization") was wrong: what you get is **polarization**,
agents that answer everything or nothing.

Adding the colony's coupling — a shared stimulus that drops when someone works — buys
**regulation**, and only that: demand is met in every seed, but four *identical* agents
split the load evenly rather than differentiating. Specialization appears when the
starting thresholds differ: the one below the separatrix does ~55% of the work and the
rest sit at ~1%. Which makes the `threshold` a pack author picks today not a sensitivity
knob but **the choice of who becomes the specialist** once the dynamics are ever wired
up. Derivation, the adversarial refutation that corrected three of its
corollaries, and the dimensional error of ours that the property tests caught are all in
[`docs/THRESHOLD-DYNAMICS.md`](docs/THRESHOLD-DYNAMICS.md). The timeout pairs behind `persistence` (300/600, 900/1800, 3600/7200
seconds) are our choice — the invariant they keep (turn cap = 2× idle window, adjacent
levels ×3–4 apart so the *ordering* is the contract), the human anchors behind them,
and what measurement would invalidate them are declared in
[`docs/PROFILE-COMPILATION.md`](docs/PROFILE-COMPILATION.md).

Buzz rejects unknown keys in persona frontmatter outright, and silently discards them in
snapshots. So the profile lives in our manifest and **compiles** to native fields. The full
contract, including what does not compile, is in
[`docs/PROFILE-COMPILATION.md`](docs/PROFILE-COMPILATION.md).

**Remove the bee and it still stands:** three per-agent trigger axes, compiling to native
fields, with declared ranges. The biology stays because it explains *why* three axes and
not five — never as the argument that it works. That rule is written down in
[`CONTRIBUTING.md`](CONTRIBUTING.md#biological-metaphor-comes-with-its-receipts) and
applies to every metaphor this project ever uses.

### What would falsify this

The profile's claim is narrow: the three live axes produce **behavior an importer can
observe**. That is testable without trusting us, because each axis compiles to a field
with a measurable consequence. Import two personas identical except for one axis into
the same channel, drive them with the same message stream, and measure:

| Axis | Measure | The claim fails if… |
|---|---|---|
| `threshold` | response rate to **unmentioned** messages | `low` (mention flag off) and `medium` (on) respond at indistinguishable rates |
| `recruitment` | concurrent responses in flight | `parallelism: 1` and `parallelism: 8` produce the same concurrency distribution |
| `persistence` | session lifetime after last activity | adjacent levels (5 → 15 → 60 min idle) yield lifetimes that do not separate |

If any row's distributions are indistinguishable, that axis is decoration and this
section says so — the way `propagation` already does (compiles to nothing at runtime,
stated in the table above). Running this protocol needs live agents with credentials,
which is exactly the E-series work in [`docs/DOD.md`](docs/DOD.md); until it runs,
what you are reading is a promise of a measurement, not a measurement. The falsifiable
statement is published **before** the result, on purpose.

## Not affiliated

Killer Bee is not affiliated with, endorsed by, or operated by Block, Inc., the Buzz
project, or buzzdir. It is independent community work.

It is a **satellite**: zero forks, zero patches to core. It consumes the native formats
because interoperating requires it.

The Buzz roadmap includes a hosted "App Store UI" for packs
(`crates/buzz-persona/PERSONA_PACK_SPEC.md:900`, marked *Details TBD*). We are saying so
out loud rather than being found out later: Killer Bee is a **community, static,
cross-community, independent** catalog. If Block ships a hosted store, these packs remain
valid — the format is theirs, not ours.

`buzzdir.xyz` is a technical reference for this project's frontend. It is also
independent community work, maintained by pavlenex, MIT-licensed. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Security

A pack is executable configuration: its prompt runs with *your* provider credential,
and a `.agent.png` is a program that looks like a picture. The threat model, the
private reporting channels, and what review does and does not guarantee are in
[`SECURITY.md`](SECURITY.md); what the maintainer checks on every pack PR is public in
[`docs/PACK-REVIEW.md`](docs/PACK-REVIEW.md). The one-command version:

```bash
uv run python -m killerbee inspect the-file.agent.png --prompt
```

reads everything inside an artifact — anyone's, not just ours — **before** it is
imported.

## Author

Built by **Saulo Duttra** —
[GitHub](https://github.com/sauloduttra) ·
[X](https://x.com/sauloduttra) ·
[Nostr](https://primal.net/p/nprofile1qqsxwact6elv3edmvdnx88p87ug6hklxrqxzvax360j382gq8s869jsz37dga)

## License

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). Contributions require a
DCO sign-off — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
