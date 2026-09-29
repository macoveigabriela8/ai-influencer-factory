# Reading this skill inside the `influencer` project

This is a vendored copy so the skill travels with the folder. The upstream
plugin lives at `~/.claude/plugins/marketplaces/local-desktop-app-uploads/`
and is NOT part of this project.

## The bundled scripts it mentions are already here, and newer

SKILL.md refers to "bundled scripts (`scripts/` in this plugin)" — `kie.py`,
`eleven.py`, `render_reel.py`, `qc_gate.py`, `align_clips.py`,
`assemble_reel.py`, `drone_check.py`. Those were **extracted from this very
project** and have since been superseded here. Use this project's `scripts/`.
They are not duplicated into the skill folder on purpose: two copies of the
same script set drift apart, and this project has already paid for that bug
once (see "twin sets must agree").

## What this skill is FOR, in this project

Not for running Master Kaion — CLAUDE.md is the authority on that. Use it
only to stand up a **different** influencer from scratch: a new character, a
new niche, a new account. It handles target-account teardown, character
design and approval, and a fresh pipeline.

Master Kaion is what this skill produced. Everything CLAUDE.md records since
then — the burned-subtitle gates, the anchor-drift rule, the DM funnel, the
loudness and sample-rate fixes — was learned after, and is NOT in the skill.
If you spin up a new influencer, port those lessons across by hand.
