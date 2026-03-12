# Context Preservation: Docs, Rules, and Skills

**Date**: 2026-03-12
**Status**: completed

## Goal

Create a comprehensive set of documentation, Cursor rules, and skills that encode deep understanding of the danger-finger codebase — its physical design rationale, parametric modeling patterns, class hierarchy, coordinate systems, and common pitfalls — so that future AI sessions start with high contextual fluency.

## Steps

1. Deep-read entire codebase: all Python modules, web files, scripts, tests, existing docs, existing rules
2. Read all past agent transcripts (29 conversations) to extract hard-won lessons
3. Create `docs/ARCHITECTURE.md` — system pipeline, class hierarchy, build flow, server, frontend
4. Create `docs/PARTS_ANATOMY.md` — physical design of every part, mechanical connections, materials, TODO inventory
5. Create `docs/CSG_PATTERNS.md` — SolidPython2 idioms, custom primitives, modeling patterns
6. Create `.cursor/rules/parametric-consistency.mdc` — cascade checking, fewer-params principle
7. Create `.cursor/rules/csg-modeling-guide.mdc` — primitive reference, key rules
8. Create `.cursor/rules/part-physical-context.mdc` — read physical context before modifying geometry
9. Create `.cursor/rules/coordinate-systems.mdc` — three coordinate spaces, common confusions
10. Create `.cursor/rules/prop-system.mdc` — how Prop descriptors work, adding params, frontend flow
11. Create `~/.cursor/skills/parametric-cad-workflow/SKILL.md` — step-by-step for parametric tasks
12. Update `docs/PRODUCT.md`, `docs/PARAMETERS.md`, `keep-docs-updated.mdc` with cross-references
13. Archive this plan

## Key decisions

- **Physical anatomy doc prioritized**: Past sessions repeatedly broke fit/clearance because agents didn't understand the mechanical purpose of geometry features. PARTS_ANATOMY.md is the most important new artifact.
- **Coordinate systems documented separately**: Three distinct coordinate spaces (SCAD, print, viewer) caused repeated confusion in past sessions. A dedicated rule prevents mixing them.
- **"Fewer parameters" principle codified**: Past "parametric overhaul" sessions tended to promote magic numbers to new Prop parameters without true derivation. The parametric-consistency rule explicitly discourages this.
- **Skill for parametric workflow**: Combines knowledge from multiple past sessions into a single step-by-step guide that any future agent can follow.

## Files affected

- `docs/ARCHITECTURE.md` — NEW: full system architecture
- `docs/PARTS_ANATOMY.md` — NEW: physical design of every part
- `docs/CSG_PATTERNS.md` — NEW: SolidPython2 modeling patterns
- `.cursor/rules/parametric-consistency.mdc` — NEW
- `.cursor/rules/csg-modeling-guide.mdc` — NEW
- `.cursor/rules/part-physical-context.mdc` — NEW
- `.cursor/rules/coordinate-systems.mdc` — NEW
- `.cursor/rules/prop-system.mdc` — NEW
- `~/.cursor/skills/parametric-cad-workflow/SKILL.md` — NEW
- `docs/PRODUCT.md` — updated with cross-references
- `docs/PARAMETERS.md` — updated with cross-references
- `.cursor/rules/keep-docs-updated.mdc` — updated with new doc list

## Outcome

11 new artifacts created. The documentation now covers:
- System architecture from browser to STL file
- Physical anatomy of every part with mechanical rationale
- CSG modeling patterns and custom primitives
- Parameter system internals
- Three coordinate systems and how they relate
- Step-by-step workflow for parametric modifications
- Hard-won lessons from 29 past agent sessions encoded as rules

Future agents editing geometry code will automatically see relevant rules (via glob triggers) and can follow the parametric-cad-workflow skill for any modeling task.
