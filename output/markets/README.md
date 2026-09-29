# Market architecture (decided 2026-08-08)

One folder per monk. EN (Kaion) keeps the legacy layout in output/assets +
output/reels; ES and PT live here.

| market | character | face | voice (.env) | copies | ledger prefix |
|---|---|---|---|---|---|
| EN | Master Kaion | kaion_rest.png | George JBFqnCBsd6RMkjVDRZzb | monkcheen + yangmunus | (none) |
| ES | Maestro Kaion | TO GENERATE (new face) | EL_VOICE_ES | monjechen | ES |
| PT | Mestre Kaion | PT/anchors/pt_mestre_mat.png | EL_VOICE_PT | monge.yang | PT |

Rules, same for every market: different FACE per market (network-fingerprint
isolation) · pose/wardrobe bank per character, one anchor per reel, never
consecutive repeats, match the source's camera distance · kie.REALISM appended
to every image and video prompt · dedicated dm_registry entries + Blotato
automations per account · ledger ids prefixed (ES1, PT1...), duplicate sources
forbidden per-market, allowed across markets.
