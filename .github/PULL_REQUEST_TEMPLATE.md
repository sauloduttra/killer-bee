<!-- Thanks for contributing. The short version of everything below:
     main stays green, claims carry receipts, and prompts are read
     before they run. -->

## What this PR does

<!-- One or two sentences. -->

## What you verified, and how

<!-- This repo's standing rule: "Read kind.rs:196, confirmed 30175" beats
     "should work". Commands you ran, files you read, apps you opened. -->

## Checklist

- [ ] Every commit is signed off (`git commit -s`) — CI enforces DCO
- [ ] `uv run pytest` · `uv run ruff check .` · `uv run ruff format --check .` pass locally
- [ ] Claims about upstream behavior carry `file:line` against a pinned commit

### If this PR adds or edits a pack

- [ ] `uv run python -m killerbee validate packs/<name>` and `build` pass
- [ ] I read [`docs/PACK-REVIEW.md`](../blob/main/docs/PACK-REVIEW.md) and ran its
      checklist against my own pack — including the blast-radius line
      (threshold/recruitment/persistence justified for the purpose)
- [ ] The prompt is fully legible: no opaque blobs, no URLs to fetch, nothing
      the published page would hide from the person about to run it
- [ ] `killerbee.yaml` has a `license`, and nothing Killer Bee-specific leaked
      into `.persona.md` frontmatter (fatal upstream)
