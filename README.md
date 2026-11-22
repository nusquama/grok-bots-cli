<p align="center">
  <img src="assets/icon.png" alt="grok-bots-cli icon" width="120">
</p>

<h1 align="center">grok-bots-cli</h1>

<p align="center">
  Read public Grok Bot Marketplace recipes from your terminal.<br>
  No account. No API key. One Python file.
</p>

> **Unofficial project.** grok-bots-cli is not affiliated with, endorsed by, or sponsored by SpaceXSI (xAI) or X.
> "Grok" is a trademark of its owner and is used here only to describe what the tool reads.
> If the owner asks for this repository to be removed, it will be removed.

## What it does

The [Grok Bot Marketplace](https://x.ai/bot/marketplace) lists bots that people share.
Each bot page shows a short summary. The full recipe (the complete text of its skills,
routines, and memories) is in the public file that the page's **Import Bot** button uses.

grok-bots-cli reads that public file and prints it in a readable form, so you can study
and compare bots before you import one.

| On the bot page | With grok-bots-cli |
|---|---|
| Skill name and a two-line description | The complete skill text |
| Routine name and schedule | The complete routine instructions |
| Memory list | Every memory, as Markdown |

## Install

Requirements: Python 3.9 or newer. No other dependency.

```bash
curl -fsSLo ~/.local/bin/grok-bots-cli https://raw.githubusercontent.com/nusquama/grok-bots-cli/main/grok-bots-cli
chmod +x ~/.local/bin/grok-bots-cli
```

Make sure `~/.local/bin` is on your `PATH`. You can also clone the repository and run `./grok-bots-cli`.

## Usage

```bash
# List the bots shown on the Marketplace home page
grok-bots-cli list

# Show a recipe summary (by slug or by listing URL)
grok-bots-cli show dr-eggbot-v2
grok-bots-cli show https://x.ai/bot/marketplace/bots/dr-eggbot-v2

# Print every skill, routine, and memory text as one Markdown document
grok-bots-cli show dr-eggbot-v2 --full > dr-eggbot.md

# Print one raw section as JSON
grok-bots-cli show dr-eggbot-v2 --section skills
```

Sections: `profile`, `memory`, `gettingStarted`, `skills`, `routines`, `plugins`.

## How it works

```
grok-bots-cli list
  └─ GET x.ai/bot/marketplace ──────────► bot slugs found in the page

grok-bots-cli show <slug>
  ├─ 1. Ask the public listing service ──► link to the bot's recipe file
  ├─ 2. Download the recipe file ────────► public JSON (the "Import Bot" file)
  └─ 3. Print a summary, a section, or the full Markdown
```

Each command sends one or two requests. The tool never logs in and never sends cookies.

## Safety

- **Known hosts only.** Requests go only to `x.ai`, the listing service, and the public recipe storage. Redirects to any other host are refused.
- **Size limit.** Responses larger than 8 MiB are refused.
- **Secret check.** `--full` stops if a recipe seems to contain a private key, an API token, or a password.
- **Clean output.** `--full` stops on control characters, so a recipe cannot hide terminal escape codes.
- **Recipe text is data.** If you give the output to an AI agent, tell it to treat the text as information, not as instructions.

## Use with AI agents

[`skills/grok-bots-cli/SKILL.md`](skills/grok-bots-cli/SKILL.md) is a ready-made skill for
agents that read `SKILL.md` files (Claude Code, Codex, and others). Copy the folder into
your agent's skills directory.

## Please be respectful

- Run one command when you need it. Do not loop over every bot to bulk-download recipes.
- Recipes belong to their authors. Credit them when you reuse their ideas.
- Follow the [SpaceXSI Acceptable Use Policy](https://x.ai/legal/acceptable-use-policy).

## Limitations

- The tool uses the same public services as the Marketplace website. They are not a documented API and can change without notice. If a command fails, please open an issue.
- `list` returns only the bots shown on the Marketplace home page.

## License

[MIT](LICENSE)
