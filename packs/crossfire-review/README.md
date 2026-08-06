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
2. Buzz Desktop → **Agents** → the **`+`** card under *Agent teams* → **Import** → pick
   the file → confirm. (4 clicks + the OS file picker. There is no drag-and-drop
   shortcut.)
3. Imported ≠ running: each agent still needs provider credentials in the
   app's global config, and "Add to channel" is a separate action per agent.

Import the team **or** the three personas, never both — the team snapshot embeds each
member in full, and the import does not deduplicate by name.

Verified in Buzz Desktop 0.5.5 on 2026-08-05: the team imports with 3 members and the app
labels the card **"Mixed models"**, because the three run on Anthropic, OpenAI and
OpenRouter.

## Orchestration is by mention, not by guarantee

You start a round by posting **one message mentioning the three agents** —
yourself, or from a Buzz workflow **you** wire up. **The pack does not ship a
workflow**; nothing you download posts that message for you. Each agent
responds because the mention matched. Nothing guarantees that all three
respond, nor in what order — that is how agents work in Buzz (members, not
cron jobs), and we would rather tell you now than have you discover it
mid-demo.

## The low threshold is opt-in, and here is exactly where it lives

Two of the three personas declare threshold **low** — "react to every patch,
not only mentions". Honest scope of that claim:

- **Desktop import path (the install above): mention-only.** The desktop
  launches its agents in mention mode and the snapshot format has no trigger
  field — nothing in a `.team.json` can change that. An imported Adversary
  reacts to @mentions, like every other imported agent.
- **The low threshold materializes only via `acp-rules.toml`**, which is in
  the box but is NOT importable in the app. It applies if you run the agent
  process yourself:

  ```
  buzz-acp --subscribe config --config acp-rules.toml
  ```

  In that mode Adversary and Guard match **every message** in their channels
  (`require_mention = false`), so put the team in a dedicated review channel,
  not in `#general`. (This path has not been exercised end-to-end by us yet —
  running it needs provider credentials; tracked openly in the repo.)

The generated `acp-rules.toml` sets `require_mention` **explicitly on every
rule** — the upstream default for the field is `false`
(`crates/buzz-acp/src/filter.rs:122`), so a rule that omits it is born
matching **everything** in the channel, mentions or not. Loud excess, not
silence — either way, not what the author meant, which is why the file never
relies on the default.
