# Crossfire Review

Three reviewers, three providers, one patch. **Forager** writes, **Adversary**
attacks, **Guard** audits — and the disagreement between them is the product:
what one model would get wrong with confidence, a different model catches.

The name comes from `block/buzz`'s own vision docs (`VISION.md:169`), where
crossfire review exists as an idea. Nothing in the Buzz runtime implements it.
This pack is that idea, made installable.

## What's in the box

| Persona | Role | Suggested model | scutellata profile |
|---|---|---|---|
| Forager | writes the patch, triages attacks | `anthropic:claude-sonnet-5` | threshold medium · recruitment 4 · persistence medium |
| Adversary | correctness, edge cases, regressions | `openai:gpt-5` | threshold **low** · recruitment 8 · persistence **long** |
| Guard | secrets, dependencies, licenses, trust boundaries | `openrouter:deepseek/deepseek-chat` | threshold **low** · recruitment **1** · persistence long |

Model strings are **suggestions** — the `provider:model-id` format is the
upstream's; swap the id for whatever your providers offer. The point that is
not negotiable: **run the three on different providers**, or the crossfire
degenerates into an echo.

## Install (honest click count)

There is no one-click install in Buzz today, and this pack will not pretend
otherwise.

1. Download `crossfire-review.team.json` (or the `.team.png`).
2. Buzz Desktop → **Agents** → **New team** → **Import** → pick the file.
   (4 clicks + the OS file picker; drag-and-drop onto the Agents section skips two.)
3. Imported ≠ running: each agent still needs provider credentials in the
   app's global config, and "Add to channel" is a separate action per agent.

## Orchestration is by mention, not by guarantee

The workflow trigger posts **one message mentioning the three agents**; each
responds because the mention filter matched. Nothing guarantees that all three
respond, nor in what order — that is how agents work in Buzz (members, not cron
jobs), and we would rather tell you now than have you discover it mid-demo.

Adversary and Guard run with a **low threshold** (they react to every patch in
subscribed channels, not only mentions). Put this team in a dedicated review
channel, not in `#general`.

The generated `acp-rules.toml` sets `require_mention` **explicitly on every
rule** — the upstream default for hand-written rules is `false`
(`crates/buzz-acp/src/filter.rs:122`), and a rule born deaf to mentions would
kill this preset silently.
