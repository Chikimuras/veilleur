# veilleur

> A daily tech-watch curator that turns RSS/Hacker News noise into a focused, LLM-summarised note in your [Obsidian](https://obsidian.md/) Zettelkasten — and links each item to the notes you already have.

`veilleur` runs once a day. It lets [matcha](https://github.com/piqoni/matcha)
aggregate your feeds, then scores every item against *your* interests with a
single LLM call, summarises the best few, and writes a dated note into your
vault — suggesting connections to your existing permanent notes so reading
turns into knowledge, not just scrolling.

```
┌─────────────┐   markdown digest    ┌────────────────────────────────┐   daily note
│   matcha    │ ───────────────────► │  veilleur                      │ ───────────────►  vault/Inbox/
│ (Go binary, │  fetch + dedup +     │  parse → triage → enrich →     │   YYYY-MM-DD-
│  pinned)    │  popularity signal   │  render                        │   veille.md
└─────────────┘                      └────────────────────────────────┘
```

## Why

Tech-watch becomes expertise only when you reformulate and connect what you
read. `veilleur` is built around that: it filters aggressively for *your*
learning goals, and every digest item is offered with candidate links into your
Zettelkasten, ready to promote into a permanent note.

## Features

- **Two-stage LLM pipeline** — a cheap batched *triage* scores and shortlists,
  then an *enrich* pass summarises only the survivors (cost stays bounded).
- **Profile-driven scoring** — you describe what you want to go deep on (and
  what to filter out) in a plain-markdown `interests.md`.
- **Zettelkasten connections** — the LLM links each item to your existing
  permanent notes by their one-sentence concept, never inventing notes.
- **matcha as an unmodified, pinned dependency** — upgrades are a version bump;
  the only coupling point is one well-tested parser.
- **Fail-safe** — a feed/LLM hiccup never produces a broken note; per-item
  failures are isolated and flagged.
- **Idempotent** — safe to run repeatedly; re-run with `--force`.

## Requirements

- Python ≥ 3.12
- [`uv`](https://github.com/astral-sh/uv)
- [`matcha`](https://github.com/piqoni/matcha) (Go binary)
- An [Anthropic API key](https://console.anthropic.com/)
- An Obsidian vault (or any folder of markdown notes)

## Install

```bash
# 1. matcha (pinned — upgrades are just a version bump later)
go install github.com/piqoni/matcha@v0.9.0   # ensure $(go env GOPATH)/bin is on PATH

# 2. veilleur
git clone https://github.com/Chikimuras/veilleur.git
cd veilleur
uv sync

# 3. config
mkdir -p ~/.config/veilleur ~/.local/state/veilleur
cp examples/veilleur.toml ~/.config/veilleur/
cp examples/matcha.yaml   ~/.config/veilleur/
cp examples/interests.md  ~/.config/veilleur/
# then edit all three (vault path, feeds, your interests)

# 4. API key — keep it out of files
export ANTHROPIC_API_KEY=sk-ant-...
```

## Configuration

| File | What it controls |
|------|------------------|
| `veilleur.toml` | Vault paths, model, `triage_threshold`, `max_items`, matcha binary/config paths. |
| `matcha.yaml` | The RSS/HN feeds matcha pulls. Keep matcha's own summariser **off** — summarising is veilleur's job. `markdown_dir_path` must equal veilleur's `work_dir`. |
| `interests.md` | Your profile: domains to score high, things to filter out. The brain of the triage. |

The Anthropic API key is read from `ANTHROPIC_API_KEY` and is never stored in a
config file.

## Usage

```bash
uv run veilleur                     # generate today's note (skips if it exists)
uv run veilleur --force             # regenerate / overwrite today's note
uv run veilleur --date 2026-06-25   # re-render from an already-present digest
```

## Scheduling (daily at 07:00)

`examples/` contains a macOS launchd job and a wrapper that pulls the API key
from the Keychain (so no secret is ever written to a file):

```bash
# store the key once
security add-generic-password -a "$USER" -s anthropic-api-key -w 'sk-ant-...'

cp examples/veilleur-cron ~/.local/bin/ && chmod +x ~/.local/bin/veilleur-cron
cp examples/com.example.veilleur.plist ~/Library/LaunchAgents/
# edit the plist + wrapper paths for your machine, then:
launchctl load ~/Library/LaunchAgents/com.example.veilleur.plist
```

On Linux, use cron instead and export `ANTHROPIC_API_KEY` in the job's
environment.

> **launchd PATH gotcha:** launchd's `PATH` does not include `~/go/bin` or
> `~/.local/bin`. Use absolute paths — set `matcha_bin` to the absolute matcha
> path in `veilleur.toml`, and call `uv` by absolute path in the wrapper.

## Upgrading matcha

```bash
go install github.com/piqoni/matcha@vX.Y.Z   # new version
# bump matcha_version in veilleur.toml — no patching, no merge
```

If a matcha upgrade changes its markdown format, exactly one test fails —
`tests/test_digest_parser.py`. Fix the parser there; nothing else couples to
matcha's output.

## Output

```markdown
---
type: veille
status: ⏳
date: 2026-06-24
tags:
  - veille
---

# 📡 Veille — 2026-06-24

> 10 articles retenus sur 91 analysés.

## [How we found a bug in the hyper HTTP library](https://blog.cloudflare.com/hyper-bug/)
**Source :** The Cloudflare Blog · **Score :** 8/10
**Tags :** securite, rust, http

Les ingénieurs de Cloudflare ont traqué un bug de race condition dans hyper…

**Pourquoi pour toi :** Méthodologie de debug systématique sur un système réel en Rust.

### 🔗 Connexions
- [[Un bug se diagnostique en comparant le modèle mental attendu à l'état réel observé]] — l'enquête suit exactement ce schéma.
```

> The produced note is in French by default (the prompts are French). Edit the
> prompts in `triage.py` / `enrich.py` for another language.

## Development

```bash
uv sync
uv run pytest        # full suite
```

Architecture — one focused module per pipeline stage:

| Module | Responsibility |
|--------|----------------|
| `config` | Load and resolve the TOML config; read the API key from env. |
| `matcha_runner` | Invoke the pinned matcha binary; locate its output (fail-safe). |
| `digest_parser` | Parse matcha's markdown → `Item`s (the sole matcha coupling point). |
| `vault_index` | Extract `{title, concept, tags}` from permanent notes (+ cache). |
| `content_fetch` | Best-effort article text extraction (httpx + trafilatura). |
| `llm` | Anthropic JSON call with retry/backoff. |
| `triage` | Stage 1: batched scoring → shortlist. |
| `enrich` | Stage 2: summary + "why" + Zettelkasten connections. |
| `render` | Render the daily note (vault conventions). |
| `main` | Orchestration + CLI. |

The design spec and implementation plan live in `docs/`.

## License

[MIT](LICENSE)
