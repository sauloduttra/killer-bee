# Contributing to Killer Bee

## Sign your commits — DCO

Every commit needs a Developer Certificate of Origin sign-off:

```bash
git commit -s -m "add scout persona to druig-dev pack"
```

`-s` appends `Signed-off-by: Your Name <your@email>`. That line means you certify the
[DCO 1.1](https://developercertificate.org/): you wrote the contribution, or you have the
right to submit it under this project's license.

**Why DCO and not a CLA.** A CLA asks you to sign a contract with a legal entity. The DCO
asks you to assert a fact in your commit message. It is lighter for you, and it preserves
the project's ability to relicense later without renegotiating with every contributor —
which stops being possible the moment an unsigned external contribution lands.

CI rejects unsigned commits. If you forget: `git commit --amend -s` for the last one, or
`git rebase --signoff main` for a branch.

## What this project is strict about

### Never invent a fact about the upstream

Killer Bee interoperates with `block/buzz`. Every claim about their formats, event kinds,
field names, CLI flags, or behavior must come from reading the source, and must be cited
as `file:line` against a pinned commit.

- "The field is probably called `system_prompt`" does not exist here. Either you read it,
  or you don't know.
- Unverified goes in `docs/PROTOCOL-NOTES.md` under **⚠️ Não verificado**, and does not
  become code.
- **The real code always wins** over any document in this repo, including this one.
  Found a divergence? Report it explicitly — do not silently adapt around it.

The upstream moves fast. When you cite, pin the commit.

### The math layer is pure

A calculation function takes numbers and returns numbers. It does not read files, print,
hit the network, read globals, hold state, or plot. I/O, CLI, cache, and charts live in
another layer that calls the pure one.

This is what decides whether code becomes an MCP tool and an eval fixture, or stays a
pretty notebook. A pure function is wrappable as a tool in minutes and testable without
infrastructure. An impure one is neither.

### Honest signatures

Type hints on every public function. **Units in the name, not in a comment** —
`rate_annual_pct` and `tenor_years`, not `r` and `t`. Invalid input raises with a message
saying which value and why. **Never return `NaN` silently** — a `NaN` that crosses three
layers and shows up in a final result is the most expensive bug in numeric code.

### Determinism

Every source of randomness takes an explicit seed parameter. No pure function reads the
clock. A test that depends on luck does not get merged.

### Biological metaphor comes with its receipts

This project is named after a bee and has a `scutellata` profile. That is a credibility
risk, and it is managed, not indulged.

Nature-named metaheuristics have a deserved bad reputation in computer science: there is a
whole literature of "new wolf / whale / bat algorithm" that is a known algorithm
repackaged with worse analysis. A skeptical engineer recognizes the pattern and discards
it in ten seconds, without reading. We do not want to be discarded in ten seconds.

**Whenever a biological metaphor appears in a public document, in code, or in the UI, all
five of these appear with it:**

1. **The established name of the mechanism**, before or alongside the biological one —
   "stigmergy", "response threshold model", "bandit", "EWMA"
2. **A primary citation**, verified — see below
3. **The equation written out**, not described
4. **One sentence saying what it is a special case of** — reinforcement with decay is an
   exponential moving average, and that is already implemented in `vol-lab`
5. **Zero claim of algorithmic novelty.** The contribution is the application to Buzz's
   substrate, not the mathematics

**The test that matters most: remove the biological metaphor entirely. Does the thing
still stand up?** If yes, the biology is legitimate intuition and may stay. If no, it is
folklore and it goes.

Biology explains **why** something works. It is never the argument **that** it works.

### Bibliographic citations get the same scrutiny as code citations

Verified against the publisher's page or a resolved DOI **before** entering a public
document, and checked by a second reader — the same discipline applied to `file:line`
citations of the upstream.

Author, title, venue, volume, pages, and **year** must all be confirmed. Year is where
citations go wrong most often: submission year, conference year, and journal year are
three different things.

If a reference does not confirm, it goes to `⚠️ NÃO VERIFICADO` in
[`docs/BIBLIOGRAFIA.md`](docs/BIBLIOGRAFIA.md) and stays out of the README. **A wrong
reference is worse than an absent one** — it is the exact failure mode we are trying to
avoid by citing in the first place.

### Verification that repeats becomes a script

If a check happens twice, it becomes a file in `scripts/` and then a CI job. Do not verify
by hand and report in prose: if you can write the function that decides, write it.

## Setup

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format .
```

Python only, `uv` only. No bare `pip install`, no poetry, no conda, no hand-written
`requirements.txt`. `pyproject.toml` is the source of truth and `uv.lock` is versioned.

## Adding a pack

```
packs/<name>/
  killerbee.yaml           # manifest: metadata, scutellata profiles, teams
  personas/*.persona.md    # native Buzz format: YAML frontmatter + markdown body
  README.md
  CHANGELOG.md
```

Then:

```bash
uv run python -m killerbee validate packs/<name>
uv run python -m killerbee build packs/<name>
```

Both run in CI; an invalid pack fails the build.

**Keep `.persona.md` files free of Killer Bee keys.** Their frontmatter is parsed with
`deny_unknown_fields` upstream (`crates/buzz-persona/src/persona.rs:174-176`) — one extra
key is a fatal parse error there. Everything of ours goes in `killerbee.yaml`.

## Never commit

- A private key, in any form. `BUZZ_PRIVATE_KEY` is a complete identity, not config.
- Vendor data, licensed transcripts, or personal data — not even a sample, not even as a
  test fixture. Generate synthetic fixtures with a fixed seed.
- Anything from `_upstream/`. It is reading material, and it lives outside this repo on
  purpose: a clone inside the project injects the upstream's own agent configuration into
  your session.

`gitleaks` runs in CI. `scripts/scan_secrets.py` runs the same check locally:

```bash
uv run --no-project scripts/scan_secrets.py .
```

## Commits and PRs

Small commits, imperative messages, one subject each. `main` stays green.

In the PR body, say what you verified and how. "Read `kind.rs:196`, confirmed 30175" beats
"should work".
