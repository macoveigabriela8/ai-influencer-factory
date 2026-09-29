#!/usr/bin/env python3
"""Render one kling avatar take, crash-safe.

    python3 scripts/render_avatar.py <reel_id> <anchor_name>
    python3 scripts/render_avatar.py --resume <reel_id>      # fetch a live task

Why this exists: on 2026-08-10 a render was submitted from a foreground shell
that timed out at 10 minutes. The job kept running and finished, but the task id
only ever existed in the lost stdout, and kie exposes NO task-history endpoint —
so ~440 credits became unrecoverable.

Every task id is written to data/kie_tasks.json the moment it is created, BEFORE
any polling. If this process dies, `--resume` picks the job back up from disk and
fetches the finished video for free.

Engine is kling/ai-avatar-standard: $0.0383/s measured, 49% under pro, single
takes to 37.6s+ proven, 720x1264 native and upscales fine.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kie  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
ANC = os.path.join(ART, "anchors")
TASKS = os.path.join(ROOT, "data", "kie_tasks.json")
MODEL = "kling/ai-avatar-standard"

# HAND MOTION: TESTED AND REVERTED, 2026-08-11. Do not re-open without funding.
#
# The user found reel 25 too static ("hands way too still, the candle flame does
# not move"), so this block was rewritten to ask for occasional slow gestures.
# Reel 24 rendered on that prompt and FAILED deep-QA: from 4.0s to 16.0s the
# raised hand is a fused mitten — no separable fingers, no thumb, no wrist,
# sprouting straight out of the robe — dead centre of the hook at the largest
# on-screen hand size in the reel. The resting hand was correct throughout, and
# both hands were clean for the other 37s where no gesture was commanded. The
# defect was exactly co-extensive with the one movement asked for.
#
# So: kling renders STILL hands correctly and GESTURED hands badly. That is the
# engine's ceiling, not a wording problem, and no amount of prompt tuning buys
# both. Hands are now positively PLACED (folded, interlaced, low in the lap) —
# placed, not merely "resting where they are", because a vague state invites the
# model to invent one.
#
# The frozen candle flame has the same root and no fix here at all: a
# lip-sync-on-a-still animates the face region and leaves the scene alone, so
# nothing outside the face is simulated. Buying real body motion means a
# different engine — InfiniteTalk ($0.06/s, 10-min single takes) or Wan-2.2-S2V
# (~$0.03/s, face quality untested), both audio-driven so the words stay
# verbatim. Seedance moves the body but re-performs the script, which is why it
# deletes CTA lines (8 documented failures) and costs $0.205/s.
#
# Kept from the working version: feet and seat pinned (the PT6 sway guard), the
# English assertion (the language guard), a positive lower-frame line, the
# closing end-state, and "only his voice" so the model does not bed its own music.
MOTION = (
    # ⚠️ THE MOTION PROMPT MUST DESCRIBE THE ANCHOR THAT IS ACTUALLY BEING SENT.
    # Until 2026-08-15 this block described reel 24's WIDE shot — "cross-legged
    # on the floor", "hands folded in his lap", "the patterned stone floor fills
    # the lower part of the frame" — while the anchors had long since become
    # CHEST-UP portraits behind a table with no legs, lap, hands or floor in
    # frame. So kling received a picture of a torso and instructions about
    # crossed legs, plus THREE separate commands to hold still ("settled and
    # unmoving", "resting there the whole time", "settles into stillness")
    # aimed at body parts it could not see. The operator's note was that the
    # shoulders read stiff. Describing motion for things outside the frame is
    # the likely cause, and it is free to fix.
    #
    # Rules for editing this text:
    #   * describe ONLY what the anchor actually shows;
    #   * name what MOVES before what stays still — a prompt that is mostly
    #     stillness language produces a photograph that happens to talk;
    #   * keep it 20-40 words of motion, all positive phrasing;
    #   * "he speaks in English, in a calm measured voice" stays forever — it is
    #     the language guard that stopped Seedance drifting into Japanese;
    #   * "only his voice and quiet temple ambience" stays — it is the guard
    #     against the engine bedding its own music.
    # GAZE, added 2026-08-15: the operator reported he looks away ~50% of the
    # time. Likely self-inflicted — the previous revision said "his head turns
    # slightly and tilts as he makes each point", which invites the model to
    # swing the whole head, and the eyes follow it off-lens. Separate the two:
    # let the HEAD move a little, pin the EYES to the lens. Eye contact is
    # stated first and repeated at the close, because it is the single thing a
    # talking-head reel cannot afford to lose.
    "He looks straight into the camera lens the entire time, holding the "
    "viewer's gaze without looking away. His chest and shoulders rise and fall "
    "visibly as he breathes, and his upper body shifts a little with the rhythm "
    "of his speech. His head moves only slightly while his eyes stay fixed on "
    "the lens, with subtle micro-expressions and gentle natural blinking. He "
    "speaks in English, in a calm measured voice, unhurried. As he finishes, "
    "his breathing slows and he comes to rest, still looking into the lens. "
    "Only his voice and quiet temple ambience."
)


def identity_gate(anchor):
    """HARD GATE: refuse to spend on an anchor that has drifted from the canon.

    The face drifted across many published reels before anyone noticed, because
    each anchor was generated by editing the previous one and nano-banana
    re-renders the face every time (see CLAUDE.md, "ANCHOR IDENTITY DRIFT").
    The operator caught it by eye; nothing in the pipeline did.

    Documentation was not enough — a manual check inside a batch is a check that
    eventually does not happen, which is exactly how reel 28 shipped burned. So
    this is code, it runs before the money, and it exits non-zero.

    Passes when the anchor is ONE generation from CANON. Anything further must
    be confirmed deliberately with IDENTITY_OK=1 after reading the strip.
    """
    import make_anchor
    prov_path = os.path.join(ANC, anchor + ".json")
    strip = os.path.join(ANC, f"_identity_{anchor}.png")
    if not os.path.exists(prov_path):
        if os.environ.get("IDENTITY_OK") == "1":
            print(f"  identity gate: no provenance for {anchor}, "
                  f"overridden by IDENTITY_OK=1")
            return
        sys.exit(f"identity gate: {anchor} has no provenance record. It predates "
                 f"the drift fix, so its distance from the canonical face "
                 f"({make_anchor.CANON}) is unknown. Regenerate it with "
                 f"make_anchor.py, or set IDENTITY_OK=1 after comparing faces.")
    prov = json.load(open(prov_path))
    hops = prov.get("hops_from_canon", 99)
    print(f"  identity gate: {anchor} is {hops} generation(s) from "
          f"{prov.get('canon')}")
    if hops > 1 and os.environ.get("IDENTITY_OK") != "1":
        sys.exit(f"  REFUSING TO RENDER: {anchor} is {hops} generations from the "
                 f"canonical face, and drift compounds every generation. "
                 f"Regenerate it from the canon (make_anchor.py defaults to it), "
                 f"or read {os.path.relpath(strip, ROOT)} and re-run with "
                 f"IDENTITY_OK=1 if it is genuinely the same man.")


def tasks(write=None):
    d = json.load(open(TASKS)) if os.path.exists(TASKS) else {}
    if write is not None:
        os.makedirs(os.path.dirname(TASKS), exist_ok=True)
        json.dump(write, open(TASKS, "w"), indent=1)
        return write
    return d


def poll(tid, label, secs=20, limit=180):
    for i in range(limit):
        s = kie.api(f"/jobs/recordInfo?taskId={tid}")
        d = s.get("data") or {}
        st = d.get("state") or d.get("status") or "?"
        if st in ("success", "SUCCESS", "completed"):
            print(f"  {label}: done · {float(d.get('creditsConsumed') or 0):.0f} cr")
            return d
        if st in ("fail", "failed", "FAIL", "error"):
            print(json.dumps(d, indent=1)[:600])
            sys.exit(f"{label} FAILED")
        if i % 5 == 0:
            print(f"    …{st} ({i*secs}s)", flush=True)
        time.sleep(secs)
    sys.exit(f"{label} still running — rerun with --resume")


def save(d, rid):
    u = [x for x in kie.urls_from(d) if ".mp4" in x] or kie.urls_from(d)
    if not u:
        sys.exit("no video url in result")
    p = kie.fetch(u[0], os.path.join(ART, f"avatar_{rid}.mp4"))
    print("  saved", p)
    return p


def main():
    if sys.argv[1] == "--resume":
        rid = sys.argv[2]
        st = tasks()
        rec = st.get(rid)
        if not rec:
            sys.exit(f"no recorded task for reel {rid}")
        print(f"resuming reel {rid} task {rec['taskId']}")
        save(poll(rec["taskId"], f"reel {rid}"), rid)
        return

    force = "--force" in sys.argv
    rid, anchor = sys.argv[1], sys.argv[2]
    # Pre-flight the anchor's subtitle band before spending ~440 credits. A flat
    # lower third is what made kling burn gibberish subtitles into reel 24 twice
    # (see output/RCA_BURNED_SUBTITLES.md).
    identity_gate(anchor)          # same man? — runs BEFORE the money
    import anchor_check
    detail, spread = anchor_check.measure(os.path.join(ANC, anchor + ".png"))
    if not force and (detail < anchor_check.MIN_DETAIL
                      or spread < anchor_check.MIN_SPREAD):
        sys.exit(f"{anchor}: subtitle band too empty (detail {detail:.4f}, "
                 f"spread {spread:.1f}) — burned-text risk. Re-compose the "
                 f"anchor, or pass --force if you have judged the frame.")
    print(f"  anchor band ok: detail {detail:.4f} spread {spread:.1f}")
    mp3 = os.path.join(ART, f"voice_{rid}.mp3")
    url = os.path.join(ART, f"voice_{rid}.url")
    if not os.path.exists(url):
        kie.upload(mp3)
    img = open(os.path.join(ANC, anchor + ".url")).read().strip()
    aud = open(url).read().strip()

    r = kie.api("/jobs/createTask", {"model": MODEL, "input": {
        "image_url": img, "audio_url": aud, "prompt": MOTION}})
    if r.get("code") != 200:
        print(json.dumps(r, indent=1)[:600])
        sys.exit("createTask failed")
    tid = r["data"]["taskId"]

    # WRITE THE ID BEFORE POLLING — this line is the whole point of the file.
    st = tasks()
    st[rid] = {"taskId": tid, "anchor": anchor, "model": MODEL,
               "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    tasks(st)
    print(f"reel {rid}: task {tid} (recorded in data/kie_tasks.json)", flush=True)

    save(poll(tid, f"reel {rid}"), rid)


if __name__ == "__main__":
    main()
