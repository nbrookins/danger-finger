# Context Optimization Rules

**Date**: 2026-03-12
**Status**: completed

## Goal

Create a small set of targeted cursor rules that front-load critical project knowledge into agent context, preventing the repeated re-derivations and mistakes observed across past sessions. Builds on top of the completed "Context Preservation" plan which created foundational docs and requestable rules — this plan adds the discoverability and bug-prevention layer.

## Steps

1. Audit all 40 existing rules (16 project, 24 global) for gaps
2. Analyze 5 most recent agent transcripts for recurring mistakes and re-derivations
3. Create always-applied `project-routing-map.mdc` — task-domain routing to correct docs
4. Create always-applied `endpoint-state-map.mdc` — auth requirements, state locations, multi-instance implications
5. Create requestable `geometry-validation.mdc` — topology checks, `_fn` visibility, post-CSG-rewrite checklist
6. Create requestable `python-to-scad-translation.mdc` — transform order, formula, OpenSCAD constraints
7. Update `docs/PRODUCT.md` rules index with all 4 new rules
8. Update `docs/ARCHITECTURE.md` endpoint table with auth column

## Key decisions

- Two always-applied rules (~40 lines total, ~200 tokens) — marginal cost per session is negligible
- Routing map points to existing docs rather than duplicating content — keeps rules short and docs as source of truth
- Geometry validation and Python-to-SCAD rules are requestable (glob-triggered) since they only matter for geometry/SCAD tasks
- Endpoint table in ARCHITECTURE.md now includes Auth column for at-a-glance reference

## Files affected

- `.cursor/rules/project-routing-map.mdc` — NEW: always-applied task-domain routing map
- `.cursor/rules/endpoint-state-map.mdc` — NEW: always-applied endpoint auth and state reference
- `.cursor/rules/geometry-validation.mdc` — NEW: requestable post-CSG-change checklist
- `.cursor/rules/python-to-scad-translation.mdc` — NEW: requestable Python-to-OpenSCAD pitfalls
- `docs/PRODUCT.md` — added 4 new rules to Cursor rules index table
- `docs/ARCHITECTURE.md` — added Auth column to Tornado handlers endpoint table

## Outcome

6 files created/updated. The two always-applied rules add ~40 lines to every agent context window, providing a routing map to prevent "read everything" patterns and an endpoint cheat sheet to prevent re-reading `server.py`. Two requestable rules capture hard-won transcript lessons about geometry validation and Python-to-OpenSCAD translation. Based on transcript analysis, these would have prevented 2 of 3 major bugs and saved 3-5 file reads per session in recent transcripts.
