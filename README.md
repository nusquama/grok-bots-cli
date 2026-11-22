<p align="center">
  <img src="https://raw.githubusercontent.com/nusquama/grok-bots-cli/main/assets/icon.png" alt="grok-bots-cli icon" width="120">
</p>

<h1 align="center">grok-bots-cli</h1>

<p align="center">
  Read public Grok Bot Marketplace recipes from your terminal or your AI agent.<br>
  No account. No API key. No dependencies.
</p>

<p align="center">
  <a href="https://github.com/nusquama/grok-bots-cli/actions/workflows/ci.yml"><img src="https://github.com/nusquama/grok-bots-cli/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/nusquama/grok-bots-cli/actions/workflows/live-smoke.yml"><img src="https://github.com/nusquama/grok-bots-cli/actions/workflows/live-smoke.yml/badge.svg" alt="Live Marketplace check"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT license">
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

You need Python 3.9 or newer and one of these installers:

- **uv** (recommended): [install uv](https://docs.astral.sh/uv/getting-started/installation/). uv can also download Python for you.
- **pipx**: [install pipx](https://pipx.pypa.io/stable/installation/).

Then pick one:

```bash
uv tool install git+https://github.com/nusquama/grok-bots-cli
```

```bash
pipx install git+https://github.com/nusquama/grok-bots-cli
```

Both create an isolated environment and put `grok-bots-cli` on your `PATH`.
If the command is not found afterwards, run `uv tool update-shell` or `pipx ensurepath`, then open a new terminal.

Check the install:

```bash
grok-bots-cli --version
```

### Update

Run the install command again with `--force`. This always fetches the latest version from GitHub:

```bash
uv tool install --force git+https://github.com/nusquama/grok-bots-cli
```

```bash
pipx install --force git+https://github.com/nusquama/grok-bots-cli
```

To install a specific release instead, add its tag to the URL, for example `...grok-bots-cli@v0.1.1`.
See [Releases](https://github.com/nusquama/grok-bots-cli/releases) for the list.

### Remove

`uv tool uninstall grok-bots-cli` or `pipx uninstall grok-bots-cli`.

## Usage

```bash
# List the bots shown on the Marketplace home page
grok-bots-cli list

# Show a recipe summary (by slug or by listing URL)
grok-bots-cli show dr-eggbot-v2
grok-bots-cli show https://x.ai/bot/marketplace/bots/dr-eggbot-v2

# Save every skill, routine, and memory text as one Markdown document
grok-bots-cli show dr-eggbot-v2 --full > dr-eggbot.md

# Print one raw section as JSON
grok-bots-cli show dr-eggbot-v2 --section skills
```

Sections: `profile`, `memory`, `gettingStarted`, `skills`, `routines`, `plugins`.

## Use it from an AI agent

The repository ships an [Agent Skill](https://agentskills.io) in
[`skills/grok-bots-cli/`](skills/grok-bots-cli/SKILL.md). The skill tells the agent
when and how to call the command. Install the CLI first (see above), then the skill.

**Any agent that reads Agent Skills** (Claude Code, Codex, Cursor, and others).
This command needs [Node.js](https://nodejs.org/) 22.20 or newer:

```bash
npx skills add nusquama/grok-bots-cli
```

**Claude Code plugin:**

```bash
claude plugin marketplace add nusquama/grok-bots-cli
claude plugin install grok-bots-cli@grok-bots-cli
```

Then ask your agent something like *"What does the dr-eggbot Grok Bot do? Show me its skills."*

## How it works

```
grok-bots-cli list
  └─ GET x.ai/bot/marketplace ──────────► bot slugs found in the page

grok-bots-cli show <slug>
  ├─ 1. Ask the public listing service ──► link to the bot's recipe file
  ├─ 2. Download the recipe file ────────► public JSON (the "Import Bot" file)
  └─ 3. Print a summary, a section, or the full Markdown
```

Each command sends one or two HTTPS requests. The tool never logs in and never sends cookies.

## Safety

- **Known hosts only.** Requests go only to `x.ai`, the listing service, and the public recipe storage. Redirects to any other host are refused.
- **Size limit.** Responses larger than 8 MiB are refused.
- **Secret masking.** If a recipe seems to contain a private key, an API token, or a password, the tool replaces it with `[REDACTED]`, prints the rest, and warns you.
- **Clean output.** `--full` stops on control characters, so a recipe cannot hide terminal escape codes.
- **Recipe text is data.** The skill tells agents to treat recipe text as information, never as instructions.

## Please be respectful

- Run one command when you need it. Do not loop over every bot to bulk-download recipes.
- Recipes belong to their authors. Credit them when you reuse their ideas.
- Follow the [SpaceXSI Acceptable Use Policy](https://x.ai/legal/acceptable-use-policy).

## Limitations

- The tool uses the same public services as the Marketplace website. They are not a documented API and can change without notice. A weekly automatic check runs against the live Marketplace; if its badge is red, the tool probably needs an update.
- `list` returns only the bots shown on the Marketplace home page.

## Development

```bash
git clone https://github.com/nusquama/grok-bots-cli
cd grok-bots-cli
uv run python -m unittest discover -s tests -v   # offline tests, no network
uv run grok-bots-cli --version                   # run from the source tree
```

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

[MIT](LICENSE)
