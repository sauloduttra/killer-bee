# Pack review — what the maintainer checks, and why

A pack is executable configuration: its system prompt runs with the importing user's
provider credential, speaks in their channels, and is read by every other member there
([`SECURITY.md`](../SECURITY.md) has the three facts this follows from). Reviewing a
pack PR is therefore a security function, not a style pass. This document is the
checklist — public, so a contributor can run it against their own PR before the
maintainer does.

## Adversary assumptions

Review assumes the PR author may be any of these, and must hold against all of them:

| # | Adversary | Vector |
|---|---|---|
| A1 | Malicious prompt author | Instructions in the system prompt that exfiltrate channel content (e.g. "summarize this conversation and include it when fetching…"), impersonate other members, or direct users to hostile links |
| A2 | Deceptive packager | Manifest metadata promises X, prompt does Y; description says "reviewer", prompt says "also do Z quietly" |
| A3 | Artifact smuggler | A `.agent.png` presented as an image; a diff to a *generated* artifact that no longer matches its source |
| A4 | Resource abuser | Profile tuned to burn the importer's tokens: maximum fan-out, hair-trigger threshold, maximum persistence, on every channel |
| A5 | Patient contributor | A legitimate first PR, then a subtle prompt edit to an established pack in PR #2 |

## The checklist

Every item says how it is checked. **CI** = enforced by a job in
[`ci.yml`](../.github/workflows/ci.yml) on every PR; **R** = the maintainer does it by
hand, every time.

### Form (CI)

- [ ] **CI** `killerbee validate` passes for every pack directory — manifest grammar,
      slugs, semver, license present, profile ranges, channels either `["all"]` or UUIDs
- [ ] **CI** `killerbee build` succeeds and artifacts upload — the emitted snapshots
      parse under the same rules the desktop import applies
- [ ] **CI** gitleaks (full history) and `scripts/scan_secrets.py` find nothing
- [ ] **CI** every commit is DCO signed-off

### Prompt (R — the heart of the review)

- [ ] Read the **entire system prompt**, every line. The body of each `.persona.md` IS
      the prompt; there is no other place behavior comes from.
- [ ] No instruction to fetch, post, or embed URLs; no instruction to encode, exfiltrate
      or forward conversation content; no instruction addressed to *other* agents or to
      the app rather than to the persona itself.
- [ ] No opaque blobs: base64 runs, hex walls, zero-width or homoglyph tricks, or
      "decode and follow" constructions. The published prompt must be the *legible*
      prompt. (The secret scanner declares base64 out of its reach — this line is
      checked by eyes, and that is stated rather than hidden.)
- [ ] The prompt does what the manifest `description` and README say, and nothing
      undisclosed (A2). Capability claims are honest — no promise of behavior Buzz does
      not offer (no deep links, no auto-start, no guaranteed responses).

### Profile and blast radius (R)

- [ ] `recruitment`, `threshold`, `persistence` are justified by the pack's purpose.
      `threshold: low` (reacts to everything) combined with high `recruitment` and
      `long` persistence on `channels: all` is A4's signature — it needs a written
      reason in the pack README or it does not merge.
- [ ] `channels` is the narrowest sensible default.

### Provenance and diff hygiene (R)

- [ ] For edits to an existing pack (A5): diff the prompt **word by word**; small
      "typo fix" PRs that touch instruction sentences get the full prompt re-read.
- [ ] `compat.buzz_commit` is a real commit and claims about upstream behavior carry
      `file:line` citations — this repo's standing rule
      ([`CONTRIBUTING.md`](../CONTRIBUTING.md)).
- [ ] No generated artifacts in the PR: `dist/`, `site/data/`, `site/public/downloads/`
      are gitignored, and the catalog is rebuilt from source — a hand-edited artifact
      that diverges from its pack cannot enter through a PR (A3).

## What could move from R to CI

Honest status: candidates, not promises. Each would be a `scripts/` check first
(this repo's rule: verification that repeats becomes a script), then a job:

1. **Prompt lint** — flag URLs, base64/hex runs above a length, zero-width characters
   and mixed-script homoglyphs in `.persona.md` bodies. Cheap, high-signal for A1/A3;
   heuristic, so it flags for human review rather than rejects.
2. **Blast-radius gate** — fail when `threshold: low` ∧ `recruitment > N` ∧
   `channels: all` without a `README` justification marker. Encodes the A4 rule as it
   is written above.
3. **Artifact determinism check** — rebuild and byte-compare emitted snapshots in CI
   (the emitter is deterministic by test already; the job would prove it per-PR).

## What review does not guarantee

Reading a prompt bounds what it *says*, not what a model *does* with it in every
context — prompt injection against the *importing* user's other agents, or against
channel members, cannot be ruled out by inspection. Review also cannot vouch for
forks: the sha256 on the catalog page authenticates artifacts built from **this**
repo's `main`, nothing else. The guarantee this catalog actually offers is narrower
and worth stating plainly: **what you can read is exactly what runs, and you can read
it before anything runs.**
