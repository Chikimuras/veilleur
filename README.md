# veilleur

Curateur de veille techno quotidien. `matcha` agrège les flux, `veilleur`
filtre/résume/relie avec un LLM et écrit une note Zettelkasten dans Obsidian.

## Install

```bash
# 1. matcha (binaire épinglé — upgrade = bump matcha_version puis ré-exécute)
go install github.com/piqoni/matcha@v0.9.0

# 2. veilleur
uv tool install --from . veilleur   # expose `veilleur` dans ~/.local/bin

# 3. config
mkdir -p ~/.config/veilleur ~/.local/state/veilleur
cp examples/veilleur.toml ~/.config/veilleur/
cp examples/matcha.yaml   ~/.config/veilleur/
cp examples/interests.md  ~/.config/veilleur/

# 4. clé API dans le Keychain (jamais en clair dans un fichier)
security add-generic-password -a "$USER" -s anthropic-api-key -w 'sk-ant-...'
# terminal: dans ~/.zshrc
#   export ANTHROPIC_API_KEY="$(security find-generic-password -s anthropic-api-key -w 2>/dev/null)"
```

## Run

```bash
veilleur                 # produit la note du jour dans 00_Inbox/
veilleur --force         # réécrit si déjà présente
veilleur --date 2026-06-23
```

## Schedule (7h tous les matins)

```bash
cp examples/veilleur-cron ~/.local/bin/ && chmod +x ~/.local/bin/veilleur-cron
cp examples/com.alexandre.veilleur.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.alexandre.veilleur.plist
```

## Upgrade matcha

```bash
go install github.com/piqoni/matcha@vX.Y.Z   # nouvelle version
# bump matcha_version dans veilleur.toml — aucun patch, aucun merge
```

If a matcha upgrade changes its markdown format, exactly one test fails:
`tests/test_digest_parser.py`. Fix the parser there.
