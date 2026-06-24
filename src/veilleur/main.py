import argparse
from datetime import date
from pathlib import Path

from . import (
    config,
    content_fetch,
    digest_parser,
    enrich,
    llm,
    matcha_runner,
    render,
    triage,
    vault_index,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="veilleur")
    parser.add_argument("--config", default="~/.config/veilleur/veilleur.toml")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)

    cfg = config.load_config(Path(args.config).expanduser())
    today = args.date or date.today().isoformat()

    note_path = cfg.inbox_dir / f"{today}-veille.md"
    if note_path.exists() and not args.force:
        print(f"Note déjà présente: {note_path} (utilise --force pour réécrire)")
        return 0

    digest_path = matcha_runner.run_matcha(cfg, today=today)
    items = digest_parser.parse_digest(digest_path.read_text(encoding="utf-8"))
    n_analyzed = len(items)
    if not items:
        print("Aucun item dans le digest matcha.")
        return 0

    client = llm.make_client(cfg.anthropic_api_key)
    interests = cfg.interests_path.read_text(encoding="utf-8")
    notes = vault_index.build_index_cached(
        cfg.permanent_notes_dir, cfg.work_dir / "vault_index.json")
    index_str = vault_index.format_index(notes)

    kept = triage.triage(items, interests, client, cfg.model,
                         cfg.triage_threshold, cfg.max_items)
    for item in kept:
        enrich.enrich_item(item, index_str, client, cfg.model,
                           content_fetch.fetch_text)

    note = render.render_note(kept, today, n_analyzed)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(note, encoding="utf-8")
    print(f"Écrit: {note_path} ({len(kept)} items retenus sur {n_analyzed})")
    return 0
