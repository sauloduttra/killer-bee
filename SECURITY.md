# Security

## Reporting a vulnerability

Two private channels, pick either:

- **GitHub private vulnerability reporting** — [Report a vulnerability](https://github.com/sauloduttra/killer-bee/security/advisories/new)
  (enabled on this repo; the report is visible only to the maintainer until a fix ships).
- **Email** — sauloduttra@gmail.com, subject starting with `[killer-bee security]`.

Please do not open a public issue for anything you believe is exploitable. You should
hear back within 7 days; this is a one-maintainer project and that number is honest
rather than impressive.

If the issue is in **Buzz itself** (the desktop app, the relay, the protocol), report it
to the upstream project — [github.com/block/buzz](https://github.com/block/buzz) — not
here. This repo emits files that Buzz consumes; it does not control what Buzz does with
them.

## Threat model — what a pack actually is

A Killer Bee pack is **executable configuration**. The threat model follows from three
facts, each verified against the upstream source and recorded with `file:line` citations
in [`docs/PROTOCOL-NOTES.md`](docs/PROTOCOL-NOTES.md):

1. **A pack's system prompt runs with *your* provider credential.** Importing an agent
   copies no key into your machine — the artifact carries no credential fields at all,
   and the import writes empty env vars and no API key (PROTOCOL-NOTES §10.6,
   `import.rs:610-626`). To run, the agent uses the provider key *you* configured in the
   app. A malicious prompt therefore spends your tokens, speaks with your agent's voice
   in your channels, and sees whatever the channel shows it.

2. **A `.agent.png` looks like an image and installs an agent.** The snapshot travels in
   a PNG `tEXt` chunk (PROTOCOL-NOTES §10.4); the app identifies files by magic bytes
   and **ignores the extension** (§10.8). Treat any `.agent.png`/`.team.png` from a
   stranger as a program, not a picture — because that is what the importer treats it as.
   And the importer validates **form, never content**: format, version, names, sizes,
   ranges (§10.8) — not one line of the system prompt is inspected by the app. Whatever
   reading happens before an agent runs is reading a human chose to do.

3. **Imported is not running.** The agent arrives `STOPPED`, in no channel, with
   `Start on launch: No` (§10.6, §10.9). The dangerous moment is not the import — it is
   the moment you add it to a channel with credentials configured. That gap is your
   review window. Use it:

   ```bash
   uv run python -m killerbee inspect the-file.agent.png --prompt
   ```

   `inspect` shows everything inside the artifact — including the full system prompt —
   **before** anything is imported. Every artifact page on the catalog site also
   publishes the sha256 of each file; verify the file you downloaded is the file that
   was reviewed.

## What is enforced, what is reviewed, what is not guaranteed

- **CI enforces**: every versioned pack validates against the emitter's contract;
  secrets are scanned twice (gitleaks over full history + an independent stdlib
  scanner); every commit carries a DCO sign-off. See
  [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- **A maintainer reviews** every pack PR line by line before merge — the checklist,
  the adversary assumptions, and what review deliberately does *not* promise are
  written down in [`docs/PACK-REVIEW.md`](docs/PACK-REVIEW.md).
- **Nothing guarantees a prompt is safe.** Review reads what a prompt *says*; no review
  process can bound what a model *does* with it in every context. The catalog's real
  security property is transparency: the full prompt is published, hashed, and
  inspectable offline before you run it. Keep the human in the loop — that is the
  design, not a disclaimer.

## Scope

In scope: the `killerbee` CLI and emitter, the packs versioned in this repo, the
catalog site (Waggle), and this repo's CI. Out of scope: Buzz, buzz-relay, buzzdir,
and the providers your agents run on.
