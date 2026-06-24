"""Orchestrator and CLI entry point.

Wires the pipeline together: load config → (idempotency check) → obtain matcha's
digest → parse → triage → enrich the shortlist → render → write the daily note.

CLI:
    veilleur                 # generate today's note (skips if it already exists)
    veilleur --force         # regenerate / overwrite today's note
    veilleur --date <ISO>    # re-render from an already-present matcha digest
"""

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
    """Run the full veilleur pipeline once.

    Args:
        argv: Optional argument list (defaults to ``sys.argv`` via argparse).

    Returns:
        Process exit code: 0 on success or a benign skip, 1 if ``--date`` was
        given but no matcha digest exists for that day.
    """
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

    # matcha only ever produces TODAY's digest. If a digest file for `today`
    # already exists in work_dir, reuse it (re-render, --force, or an explicit
    # --date for a day already fetched); otherwise run matcha to produce it.
    digest_path = (
        cfg.work_dir / f"{cfg.matcha_file_prefix}{today}{cfg.matcha_file_suffix}.md"
    )
    if not digest_path.exists():
        if args.date:
            print(
                f"Aucun digest matcha pour {today} ({digest_path}). "
                "matcha ne produit que le digest du jour ; --date sert à "
                "re-générer la note d'un digest déjà présent."
            )
            return 1
        digest_path = matcha_runner.run_matcha(cfg, today=today)

    items = digest_parser.parse_digest(digest_path.read_text(encoding="utf-8"))
    n_analyzed = len(items)  # total before triage, for the note's summary line
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
    print(f"Écrit: {note_path} ({len(kept)} articles retenus sur {n_analyzed})")
    return 0
