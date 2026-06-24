"""veilleur — a daily tech-watch curator that feeds an Obsidian Zettelkasten.

The pipeline: matcha aggregates RSS/HN feeds into a markdown digest; veilleur
parses it, triages items against an interests profile with one batched LLM call,
enriches the shortlist (summary + connections to existing permanent notes), and
writes a dated note into the vault inbox. See ``main.py`` for the orchestration.
"""

__version__ = "0.1.0"
