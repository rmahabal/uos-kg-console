# Generator source (`/src`)

This folder is the **Python generator** that bakes the four standalone CU console pages
(`console-ccu.html`, `console-farmers.html`, `console-iccu.html`, `console-mission.html`)
found in the repo root.

> The live **uploader** (`/uploader.html`) does **not** use this Python. It runs `engine.js`
> (repo root), a browser port of the exact same logic. This `/src` folder is the readable,
> commented reference for what `engine.js` does.

## Files
| File | Role |
|------|------|
| `convert.py` | instance KG JSON → Explorer graph format (`var G`) |
| `compute.py` | per-CU computations: KPIs, composition, **agent-readiness rubric**, provenance, Overview cards |
| `cards_bind.py` | binds the Overview bottom cards (confidence bands, reg coverage, top gaps) |
| `build.py` | orchestrator — reads the template + each CU JSON, bakes a standalone page into `pages/` |
| `_template_console.html` | the console UI shell (static HTML: one inline `var G` graph + JS-driven views) |
| `data/*.json` | the four source CU instance graphs |

## Run
```bash
cd src
python3 build.py        # regenerates pages/console-<cu>.html for all four CUs
```
No dependencies beyond the Python standard library.

## `engine.js` ↔ Python mapping
`engine.js` (repo root) = `convert.py` + `compute.py` + `cards_bind.py` + `build.py` combined
into one browser module exposing `window.KGEngine.buildPage(template, json)`. The uploader calls
this. **If you change the readiness rubric in `compute.py`, mirror it in `engine.js`** (and vice
versa) so the static pages and the uploader stay consistent.

## How readiness & gaps are derived (the "intelligence")
All computed from the JSON — nothing hardcoded per CU:

- **Graph** — `convert()` maps the 16 instance node-types + edges into the explorable graph.
- **Agent readiness** (`compute.py`) — each of the 4 business groups has a deployability
  baseline (`READY_BASE` / `BLOCK_BASE`), modulated by that CU's **high-confidence share**,
  **NEEDS_FI gap density**, **domain coverage**, and an **archetype tilt** (`_tilt`, keyed off
  the JSON's `archetype` field). Anchored so a deposits-led community CU reproduces the original
  hand-judged `6 / 23 / 22`.
- **51-agent breakdown** (`build.py:rethread()`) — the agent inventory is the universal Uptiq
  catalog (fixed); each agent's Ready/Partial/Blocked dot is re-ranked per CU so the dots match
  that CU's group counts. Reasons are kept bespoke where status is unchanged, generic where it flips.
- **Top gaps** (`compute.py:cards()`) — node types with the most NEEDS_FI flags.

## Schema assumptions
The generator expects the instance JSON to carry: the 16 node types, the per-node metadata
envelope (`confidence_score`, `state`, `owner`, `source_provenance`, `effective_from`,
`pii_classification`, …), `edges` as `{from, rel, to}`, plus top-level `fi`, `archetype`,
`reg_linkage`, `version`, `built`. Sparse/malformed JSON degrades gracefully rather than erroring.
