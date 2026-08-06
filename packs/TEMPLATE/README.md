# Pack template — the 10-minute path

Copy this directory, rename three things, validate, open a PR.

```bash
# 1. Copy (from the repo root)
cp -r packs/TEMPLATE packs/my-pack

# 2. Make it real: the .example suffix is what keeps the template
#    invisible to the CLI, the site and CI
mv packs/my-pack/killerbee.yaml.example packs/my-pack/killerbee.yaml

# 3. Edit: manifest metadata, persona frontmatter, and the prompt —
#    the markdown body of each .persona.md IS the system prompt

# 4. Validate and build. Both run in CI; an invalid pack fails the build.
uv run python -m killerbee validate packs/my-pack
uv run python -m killerbee build packs/my-pack

# 5. Read your own artifact the way a stranger would, before you ship it
uv run python -m killerbee inspect dist/my-pack/scout.agent.png
```

Then delete this README from your copy (or replace it with your pack's own),
add a `CHANGELOG.md`, and open the PR. The review that your PR will get is
written down in [`docs/PACK-REVIEW.md`](../../docs/PACK-REVIEW.md) — reading
it first is the fastest way to pass it.

Rules that save you a round-trip:

- **Everything Killer Bee-specific lives in `killerbee.yaml`.** One extra key
  in a `.persona.md` frontmatter is a fatal parse error upstream.
- **`name` fields are slugs** (`^[a-z0-9][a-z0-9_-]{0,63}$`) and become file
  names — no dots, no uppercase, no Windows reserved names.
- **Editor validation is free:** the manifest's first line points
  yaml-language-server at [`schema/killerbee.schema.json`](../../schema/killerbee.schema.json),
  so VS Code and every LSP-based editor flags mistakes as you type. The
  authority is still `killerbee validate`.
- **Every commit needs a DCO sign-off:** `git commit -s`.
