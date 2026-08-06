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
   verifiable** instead of a list on a website.

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
2. Buzz Desktop → **Agents** → **New team** / **New agent** → **Import** → pick the file.
   **Four clicks plus the OS file picker.** Drag-and-drop onto the Agents section saves
   two.
3. **Imported is not running.** The agent still needs provider credentials from the
   app's global config, and "Add to channel" is a separate action.

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

where `s` is stimulus intensity and `θ` the individual's threshold. It is a logistic gate
with a per-agent bias — nothing more exotic than that, and **no algorithmic novelty is
claimed here.** The model is from the 1990s. What is ours is the mapping onto the fields
Buzz's runtime actually reads:

| Trait | Field | Compiles to |
|---|---|---|
| lower response threshold | `threshold` | `respondTo` + the ACP mention flag |
| recruits the swarm, not ten guards | `recruitment` | `parallelism` (native, 1–32) |
| pursues much further | `persistence` | idle and turn timeouts |
| swarms more often per season | `propagation` | nothing at runtime — catalog metadata |

Today's implementation is the **static** version: three discrete values chosen by the pack
author, no continuous stimulus, no learning. The adaptive variant — where `θ` moves with
experience, which is what actually makes division of labour self-organize — is
[B-02 in the backlog](docs/BACKLOG.md#b-02--limiar-adaptativo-no-perfil-scutellata) and is
**not built**.

Buzz rejects unknown keys in persona frontmatter outright, and silently discards them in
snapshots. So the profile lives in our manifest and **compiles** to native fields. The full
contract, including what does not compile, is in
[`docs/PROFILE-COMPILATION.md`](docs/PROFILE-COMPILATION.md).

**Remove the bee and it still stands:** three per-agent trigger axes, compiling to native
fields, with declared ranges. The biology stays because it explains *why* three axes and
not five — never as the argument that it works. That rule is written down in
[`CONTRIBUTING.md`](CONTRIBUTING.md#biological-metaphor-comes-with-its-receipts) and
applies to every metaphor this project ever uses.

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

## License

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). Contributions require a
DCO sign-off — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
