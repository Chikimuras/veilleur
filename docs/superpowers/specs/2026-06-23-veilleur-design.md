# veilleur — Design

**Date:** 2026-06-23
**Status:** Approved
**Auteur:** Alexandre (+ Claude)

## Objectif

Assistant de veille techno autonome. Tourne seul chaque matin, agrège des
sources techniques, filtre/score/résume le bruit avec un LLM, et livre un
digest condensé sous forme de **note Zettelkasten** qui suggère des connexions
vers les notes permanentes existantes. But final : nourrir la montée en
expertise, pas juste consommer des news.

- **Cœur "B"** : curateur autonome (cron → fetch → score → résumé → digest).
- **Touche "C"** : le digest alimente le Zettelkasten (liens `[[...]]` vers les
  notes permanentes existantes).

## Décisions de design

| Sujet | Décision |
|---|---|
| Forme | Curateur autonome (B) avec sortie Zettelkasten (C) |
| Sources | RSS + APIs spécifiques (HN, Lobsters, Reddit) pour le signal popularité |
| Socle | `matcha` (piqoni/matcha) comme boîte noire amont, **non patché** |
| Rapport à matcha | Couche par-dessus, découplée — maj de matcha = bump de version |
| Langage de la couche | Python |
| Connexions vault | LLM avec index compact du vault en contexte (pas d'embeddings) |
| Sortie | Une note par jour dans `00_Inbox/` (`YYYY-MM-DD-veille.md`) |
| Scoring | Profil explicite `interests.md` + signal popularité |
| Cadence | Quotidien, 7h (cron/launchd) |

## Architecture

Pipeline en 2 étages découplés :

```
┌─────────────┐     markdown brut      ┌──────────────────────────────┐     note finale
│   matcha    │ ─────────────────────► │   veilleur (Python)          │ ──────────────► 00_Inbox/
│ (binaire Go │  (fetch + dedup +      │  parse → triage → enrich →   │  YYYY-MM-DD-
│  épinglé)   │   signal popularité)   │  render                      │  veille.md
└─────────────┘                        └──────────────────────────────┘
```

- **matcha** = partie pénible : fetch multi-sources, dédup ("déjà vu" via sa
  base sqlite), tag popularité. **Résumé LLM, reading time, images, instapaper
  désactivés** : on veut les items bruts.
- **Signal popularité (contrainte réelle, vérifiée dans le code matcha)** :
  matcha n'écrit **pas** le nombre de points/commentaires dans le markdown. Sur
  les items Hacker News uniquement, il préfixe un icône : `💬` (<100
  commentaires) ou `🔥` (≥100). Notre signal popularité est donc un **booléen
  `hot`** (🔥 présent), pas un nombre. Les items non-HN n'ont aucun signal.
- **veilleur** (Python) = toute la curation.
- **Couplage = un seul point** : le format markdown de matcha, isolé dans
  `digest_parser.py` + testé sur fixtures. Une maj matcha qui change le format
  casse un test ciblé, pas tout.
- **Maj matcha = triviale** : version dans la config, upgrade = `go install
  …@vX` (ou release binaire) + bump. Aucun patch, aucun merge.

## Data flow

1. **matcha** tourne → digest brut dans un dossier de travail.
2. **Parse** → `list[Item {titre, url, source, hot: bool}]`.
3. **Index vault** → scan `30_Permanent_Notes/`, extraction
   `{titre, 💡 concept, tags}` → index compact (mis en cache, reconstruit si le
   vault a changé).
4. **Étage 1 — Triage** (1 appel LLM batché, pas cher) : score chaque item 0–10
   contre `interests.md` (pertinence + valeur d'apprentissage) pondéré par la
   popularité. On garde au-dessus d'un seuil (plafond configurable, ex. max
   10/jour). → réduit le bruit avant de dépenser.
5. **Étage 2 — Enrich** (items retenus seulement) : fetch texte de l'article
   (readability), puis LLM →
   `{résumé FR, pourquoi ça vaut le coup, connexions [[...]] + justification}`.
6. **Render** → note du jour dans `00_Inbox/` au format Zettelkasten.

Triage cheap-d'abord / enrich coûteux-ensuite = réduction du bruit + maîtrise
du coût LLM.

## Composants (modules Python)

| Module | Responsabilité | Dépend de |
|---|---|---|
| `config.py` | charge config (chemins, modèle, seuils, version matcha) | — |
| `matcha_runner.py` | lance le binaire matcha, localise sa sortie | config |
| `digest_parser.py` | markdown matcha → `list[Item]` | — (couplage isolé) |
| `vault_index.py` | scan notes permanentes → index + cache | config |
| `content_fetch.py` | URL → texte propre (readability) | — |
| `triage.py` | Étage 1 : scoring LLM batché | config, LLM |
| `enrich.py` | Étage 2 : fetch + résumé + connexions | content_fetch, vault_index, LLM |
| `render.py` | items enrichis → markdown final | — |
| `main.py` | orchestration + CLI (`--force`) | tous |

LLM = SDK Anthropic (Claude). Modèle par défaut **Sonnet 4.6** pour le triage,
configurable ; enrich peut monter en gamme.

## Configuration (maintenue par l'utilisateur)

- **`interests.md`** — profil aspirationnel : domaines, objectif d'expertise,
  ce qui gonfle (hype produit, levées…). Cerveau du scoring.
- **`feeds`** (config.yaml de matcha) — sources, import OPML supporté.
- **`veilleur.toml`** — seuils, plafond d'items/jour, modèle, chemins (vault,
  inbox, binaire matcha + version épinglée).

Secrets (clé API Anthropic) via variable d'environnement.

## Gestion d'erreurs (fail-safe, jamais de note pourrie)

- **matcha échoue** → abort, log clair, **aucune note écrite**.
- **Fetch d'un article échoue** → skip cet item, continue (isolation par item),
  mention dans la note.
- **Appel LLM** → retry avec backoff. Triage entier KO → abort. Enrich d'un item
  KO → item inclus avec infos brutes + flag "résumé indisponible" (pas de perte
  silencieuse).
- **Vault vide/absent** → section connexions vide, pas de crash.
- **Idempotence** : note du jour déjà présente → skip (sécurité cron), `--force`
  pour réécrire.

## Tests (TDD)

- **Unitaires** : `digest_parser` sur fixtures matcha (filet anti-régression sur
  les maj matcha) ; `vault_index` sur notes d'exemple ; `render` en golden file ;
  `triage`/`enrich` avec LLM mocké.
- **Intégration** : bout-en-bout avec mini-feed fixture + LLM mocké → vérifie la
  structure de la note produite.

## Déploiement

- Repo git : `~/veilleur`.
- Cron/launchd quotidien à **7h** : `matcha && veilleur`.
- Plateforme : macOS (launchd, cohérent avec le setup SketchyBar existant).

## Format de la note de sortie

Aligné sur les conventions du vault (`AGENTS.md` + templates) :

- **Nom** : `YYYY-MM-DD-veille.md` dans `00_Inbox/` (distinct de la daily note
  `YYYY-MM-DD.md`).
- **Frontmatter** : `type: veille` (nouveau type capture — les 4 existants ne
  collent pas), `status: ⏳` (capture non traitée, en attente de promotion),
  `date` ISO, `tags` en array. Le `type != "daily"` fait que la note apparaît
  automatiquement dans le dataview "Notes Créées Aujourd'hui" de la daily note.
- **H1 emoji-préfixé** (façon `📅` de la daily) : `📡 Veille — YYYY-MM-DD`.
- **Heading `## 🔗 Connexions` repris à l'identique** du `Tpl_Permanent_Note`
  → promouvoir un item en note permanente = copier-coller.

```markdown
---
type: veille
status: ⏳
date: 2026-06-23
tags:
  - veille
---

# 📡 Veille — 2026-06-23

> 7 articles retenus sur 42 analysés.

## [Titre de l'article](url)
**Source :** Hacker News · 🔥 · **Score :** 8/10
**Tags :** rust, distributed-systems

Résumé en français, 2-3 phrases.

**Pourquoi pour toi :** lien avec l'objectif d'expertise du profil.

### 🔗 Connexions
- [[Note permanente existante]] — pourquoi ça résonne.

---

## [Autre article](url)
…
```

Quand aucune connexion n'est trouvée (vault jeune), la section `🔗 Connexions`
liste un `[[ ]]` vide (comme le template) plutôt que d'être absente — invite à
wirer manuellement.

## Hors scope (YAGNI pour le MVP)

- Canal mail (réservé pour plus tard si lecture mobile souhaitée).
- Embeddings sémantiques (bascule possible si le vault explose en volume —
  seule l'étape "trouver les candidats" changerait).
- Scraping de pages sans flux RSS.
- Création/écriture automatique de notes permanentes (l'utilisateur promeut
  manuellement depuis l'Inbox).
