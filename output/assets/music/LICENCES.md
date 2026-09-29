# Music licences — check this before adding ANY track

## Approved for use

| file | source | licence | attribution | commercial |
|---|---|---|---|---|
| `chopin_prelude_28_6.mp3` | Musopen | **CC0 1.0 Universal** | not required | permitted |
| `chopin_nocturne_27_1.mp3` | Musopen | **CC0 1.0 Universal** | not required | permitted |
| `chopin_nocturne_9_1.mp3` | Musopen | **CC0 1.0 Universal** | not required | permitted |

Provenance: the nocturne files carry an ID3 comment pointing at
`https://archive.org/details/musopen-chopin`, whose licence line reads **"CC0
1.0 Universal"** (verified 2026-08-13). Commercial use permitted, attribution
not required. Chopin died in 1849 so the *composition* is public domain
everywhere; CC0 covers the *recording*, which is the part that would otherwise
still be in copyright.

⚠️ `chopin_prelude_28_6.mp3` — the track we actually use — carries **no ID3 tags
at all**. Its Musopen origin is INFERRED from the sibling files downloaded in
the same batch. Very probably correct, but it is an inference, not a receipt.
If a platform ever raises a claim, re-download it from the Musopen collection
above so the provenance is documented rather than assumed.

## Rejected

`_do_not_use/` holds Kevin MacLeod tracks (CC BY — requires visible
attribution). See `_do_not_use/WHY_NOT.md`.

## The rule for adding a track

1. Confirm the licence of the **RECORDING**, not just the composition. A public
   domain composition performed in 2019 has a copyrighted recording.
2. CC0 or public domain only. **CC BY is not usable here** — our captions are
   hashtags only, so there is nowhere to place a credit.
3. Save the source URL into the file's ID3 comment on download, and add a row
   to the table above.
4. Commercial releases are legal ONLY through the platform's own in-app music
   picker (TikTok / Instagram), never baked in with ffmpeg. This is why the PT
   masters ship dry: "Moment Of Reflection" is a commercial release.
