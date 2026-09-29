#!/usr/bin/env python3
"""
Build a Google Flow Agent Mode prompt for a reel.

    python3 scripts/flow_prompt.py A          # -> output/REEL_A_FLOW_PROMPT.md
    python3 scripts/flow_prompt.py A B C

Agent Mode takes the whole script and splits it into 10s segments itself, so
there is no manual chunking here -- only the dialogue plus the invariant blocks
below. Those blocks are the reason this is a generator rather than three hand-
written files: every fix found by testing one reel has to reach all of them.

Two deliberate departures from the AI Avatar Starter Kit master prompt this is
modelled on, both driven by measurement rather than taste:

  * Its Camera Direction asks for two static shots and one cut per segment.
    Scene-cut analysis of his three best reels found ZERO cuts across 151-161s.
    At two per segment a reel would carry ~30. The unbroken take is the format.
  * Delivery is pinned to a measured 161.6 wpm (Whisper, his 1.4M-view reel)
    rather than an adjective. "Slow and calm" with no number is what produced a
    voice preview far slower than his.

The Set block exists because the Character binding pins the PERSON, not the
room. Run 1 with only the kit's one-line consistency clause drifted from
bookshelves to Buddha statues between two consecutive segments, changed the
table, put a tripod in frame, and had him lift the sutra off the table.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WPM = 161.6      # measured, his BIG01
SEG = 10.0       # Flow's hard cap per generation
CREDITS = 15     # per generation, from the user's account

DELIVERY = (
    "calm and warm, but BRISK and conversational -- the pace of an ordinary "
    "unhurried conversation, not the pace of a sermon, meditation, guided "
    "relaxation or prayer. Roughly three words every second, about 160 words per "
    "minute. Each 10-second segment must contain about 27 words of speech; if the "
    "words assigned to a segment do not fill it, that segment is being spoken too "
    "slowly. Do not stretch vowels, do not trail off at the ends of sentences, and "
    "do not leave silence at the start or end of a segment. Half-second pauses "
    "between sentences only, never a pause inside a sentence. He is telling you "
    "something useful, not performing wisdom."
)

SET = """## The Set — this exact room in every segment, without variation
The entire video takes place in one unchanging location. Do not reinterpret, redecorate or re-stage it between segments.

- Room: the interior of a Tibetan temple hall. Directly behind him, at a distance, a plain deep-red painted wooden pillar to his left and a dim wall of old cloth-bound scripture shelves to his right. The background is soft and out of focus at all times.
- The space between him and the camera is completely empty. The floor in front of the table is bare, plain and unfurnished, and nothing at all stands on it.
- The only objects anywhere in the frame are the table, the sutra lying on it, and him.
- Table: one low, plain, light honey-coloured wooden table with a flat unadorned front edge. No carving, no ornament, no cloth.
- On the table: a single open long-leaf sutra lying flat, and nothing else. The sutra stays lying flat on the table for the entire video. He never picks it up, never lifts it, never holds it, and never touches it.
- Lighting: warm, soft, unchanging light from the left. Identical brightness, colour and direction in every segment.

## Continuity of the performer
- His hands stay resting clasped together on the table, and return to that clasped resting position between gestures. His hands never leave the table area and never hold anything.
- His expression stays composed, warm and gentle throughout — a soft attentive half-smile at most. He never grins, never laughs, never breaks into a broad smile.
- His posture, distance from the camera, and position within the frame are identical in every segment.

## Camera Direction
One single locked-off camera for the entire video. Medium close-up, front-facing, subject centred, chest and hands visible in a vertical 9:16 frame. No cuts, no change of angle, no change of shot size at any point. No pans, tilts, handheld movement, tracking shots, dolly movement or zooms. Every segment uses the identical framing so the finished video reads as one continuous unbroken take."""


def dialogue(reel):
    return "\n\n".join(" ".join(b["lines"]) for b in reel["beats"])


def trim(text, secs):
    """Cut the dialogue to roughly `secs`, always ending on a sentence."""
    import re
    budget = secs / 60 * WPM
    out, n = [], 0
    for s in re.findall(r"[^.!?]+[.!?]", text):
        s = s.strip()
        # Stop before overshooting, but never return an empty script.
        if out and n + len(s.split()) > budget:
            break
        out.append(s)
        n += len(s.split())
    return " ".join(out)


def build(rid, secs=None):
    reels = json.load(open(os.path.join(ROOT, "scripts", "reels.json")))
    reel = next((r for r in reels if r["id"] == rid.upper()), None)
    if not reel:
        sys.exit(f"no reel {rid} in reels.json")

    # Reel B was extended past what reels.json holds, so prefer the script file
    # when one exists -- otherwise the generator would silently ship the short cut.
    md = os.path.join(ROOT, "output", f"REEL_{rid.upper()}_SCRIPT.md")
    if os.path.exists(md) and "## Continuous text" in open(md).read():
        body = open(md).read().split("## Continuous text")[1]
        paras = [p.strip() for p in body.split("\n\n")
                 if p.strip() and not p.startswith("#") and "paste this into Flow" not in p]
        text = "\n\n".join(paras)
    else:
        text = dialogue(reel)

    if secs:
        text = trim(text, secs)

    n = len(text.split())
    est = n / WPM * 60          # keep `secs` intact: it names the test cut below
    segs = int(-(-est // SEG))

    doc = f"""# Reel {reel['id']} — "{reel.get('title', '')}"  ·  Google Flow Agent Mode

**{n} words · ~{est:.0f}s · ~{segs} segments · ~{segs * CREDITS} credits**

Paste the block below into Google Flow with **Agent Mode** selected and the
character bound. The agent splits the dialogue into 10s segments itself.

`No background music` is load-bearing: each segment is a separate inference, so
a music bed would restart in a different phase every 10 seconds. Score the
assembled cut in post instead.

---

@[CHARACTER] Speaks the following dialogue exactly as written. Do not omit, paraphrase, reorder, or add any words.

: {text}

## Instructions
- Dialogue Delivery Style: {DELIVERY}
- Split the dialogue into consecutive 10-second video segments while preserving every word in the exact order.
- Do not shorten, paraphrase, skip, or modify any part of the dialogue.
- Generate all segments as one seamless continuous performance.
- Use natural lip sync, realistic facial expressions, eye contact, blinking, subtle breathing, and expressive but restrained hand gestures.
- Ensure every segment connects seamlessly with the next.
- No background music.

## Visual Consistency
Maintain absolute consistency with the reference image. Keep the subject's appearance, clothing, hairstyle, and facial features identical across every segment.

{SET}
"""
    suffix = f"_TEST{int(est)}s" if secs else ""
    out = os.path.join(ROOT, "output", f"REEL_{reel['id']}{suffix}_FLOW_PROMPT.md")
    open(out, "w").write(doc)
    print(f"  {reel['id']}  {n:3d}w  ~{est:3.0f}s  {segs:2d} seg  {segs * CREDITS:3d} cr"
          f"  -> {os.path.relpath(out, ROOT)}")
    return segs * CREDITS


if __name__ == "__main__":
    args = sys.argv[1:]
    secs = None
    if "--test" in args:
        i = args.index("--test")
        secs = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    ids = args or ["A", "B", "C"]
    print(f"  {sum(build(i, secs) for i in ids)} credits total")
