#!/usr/bin/env python3
"""Gate 0 — QC the ElevenLabs narration BEFORE any video spend.

    python3 scripts/gate0_tts.py 26

Why this runs before kie sees anything: ElevenLabs itself garbles a word now and
then, and a garbled word survives into a ~740-credit render that then has to be
thrown away. PT2 spoke "transforma a Sabira-casa" and cost four video rolls
before anyone noticed. Whole-file similarity did NOT catch it — that render
scored 0.9933 with the garble still in it, because one bad word inside 1,200
characters barely moves an aggregate.

So the gate is SENTENCE-LEVEL: every sentence of our script must align on its
own, and one bad sentence fails the file no matter how good the rest is.

Three measurement rules, each bought with real money (CLAUDE.md):

  1. Strip digits AND number-words from both sides. Whisper writes "40", our
     script writes "forty". A naive comparison failed 30/30 clean chapters and
     burned 60,460 ElevenLabs characters re-rolling them.
  2. Score similarity as the SUM of matching blocks, never the single longest
     match, so one differing word mid-sentence cannot fail a good line.
  3. When the gate fails everything, suspect the gate. Transcribe one file by
     hand and read it before trusting a mass failure.

A sentence that fails twice should be REWORDED rather than re-rendered — some
phrases trip a given voice reproducibly (PT2 failed the same clause in rounds
4, 5 and 6).
"""

import difflib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "output", "assets")
FLOOR = 0.85

NUMBER_WORDS = r"""zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|
twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|
thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|first|second|
third|fourth|fifth|sixth|seventh|eighth|ninth|tenth"""


# Compounds Whisper writes as ONE word where our scripts write TWO (or the
# reverse). Purely orthographic — the audio is identical either way, so a
# mismatch here is a measurement artifact, not a TTS defect. Same class of bug
# as the digits/number-words rule below it, which cost 60,460 ElevenLabs
# characters before anyone transcribed a file by hand and read it.
# Found 2026-08-15: reel 34's "Holding on to it" was heard as "Holding onto it"
# and scored 0.846 against a 0.85 floor, on audio that was perfect.
COMPOUNDS = [("onto", "on to"), ("into", "in to"), ("anymore", "any more"),
             ("everyday", "every day"), ("cannot", "can not"),
             ("someday", "some day"), ("awhile", "a while"),
             ("alright", "all right"), ("away", "a way")]
# ⚠️ "away"/"a way" is the one entry here that is NOT purely cosmetic. Whisper
# heard reel 39's "I will send you a way to find yours" as "send you AWAY to
# find yours" — and so would a listener. Normalising it keeps the gate honest,
# but when this pair fires, LISTEN to the line before shipping it: the fix is
# usually to reword the script, not to accept the match. Reel 39 was reworded.


def norm(s):
    s = s.lower()
    s = re.sub(r"\d+", " ", s)                                  # rule 1: digits
    s = re.sub(r"\b(" + NUMBER_WORDS.replace("\n", "") + r")\b", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    s = " ".join(s.split())
    for one, two in COMPOUNDS:          # collapse BOTH sides to the one-word form
        s = re.sub(r"\b" + two + r"\b", one, s)
    return s


def sim(a, b):
    """Sum of matching blocks / length — rule 2, not the longest single match."""
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    m = difflib.SequenceMatcher(None, a, b)
    return sum(bl.size for bl in m.get_matching_blocks()) / max(len(a), len(b))


def coverage(sentence, heard):
    """How much of OUR sentence appears anywhere in the transcript.

    Divide by the SENTENCE length, never by the haystack. The first version of
    this gate scored each sentence against a window 1.4x its own length and
    divided by the longer side, so a perfect match could only ever reach
    1/1.4 = 0.714 — and 13 of 14 clean sentences "failed" at 0.71-0.74 while
    the audio was verbatim. That is the CLAUDE.md lesson arriving on schedule:
    a gate that fails everything is a broken gate. Confirmed by transcribing
    the file and reading it, which is the required response to a mass failure.

    Two further traps, both hit while writing this:

      * difflib's AUTOJUNK silently discards any element appearing in more than
        1% of a sequence longer than 200 — on character sequences against a
        full transcript that is every common letter, so scores collapsed to
        ~0.0 for sentences that were plainly present. Compare WORDS, not
        characters, and the heuristic stops mattering.
      * Exact cleaned-substring is checked FIRST, because CLAUDE.md records a
        garble at a sentence TAIL that a fuzzy ratio waved through twice.
    """
    a, b = norm(sentence), norm(heard)
    if not a or not b:
        return 0.0
    if a in b:                       # the common case, and the strictest test
        return 1.0
    wa, wb = a.split(), b.split()
    n = len(wa)
    best = 0.0
    for i in range(max(1, len(wb) - n + 1)):
        m = difflib.SequenceMatcher(None, wa, wb[i:i + n], autojunk=False)
        best = max(best, sum(bl.size for bl in m.get_matching_blocks()) / n)
    return best


def sentences(text):
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")):
        s = s.strip()
        if len(norm(s).split()) >= 3:     # a 1-2 word fragment cannot be scored
            out.append(s)
    return out


def main():
    rid = sys.argv[1]
    mp3 = os.path.join(ART, f"voice_{rid}.mp3")
    if not os.path.exists(mp3):
        sys.exit(f"missing {mp3} — run eleven.py say {rid} first")

    reels = json.load(open(os.path.join(ROOT, "scripts", "reels.json")))
    reel = next(r for r in reels if str(r["id"]) == str(rid))
    script = " ".join(" ".join(b["lines"]) for b in reel["beats"])

    wav = f"/tmp/gate0_{rid}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-ac", "1",
                    "-ar", "16000", "-y", wav], check=True)
    import mlx_whisper
    heard = mlx_whisper.transcribe(
        wav, path_or_hf_repo="mlx-community/whisper-small.en-mlx")["text"]
    os.remove(wav)

    whole = sim(script, heard)
    print(f"reel {rid}: whole-file {whole:.4f}  "
          f"(informational only — a garble hides at this level)\n")

    heard_n = norm(heard)
    failed = []
    for s in sentences(script):
        best = coverage(s, heard_n)
        flag = "ok  " if best >= FLOOR else "FAIL"
        if best < FLOOR:
            failed.append((best, s))
        print(f"  {flag} {best:.3f}  {s[:78]}")

    print()
    if failed:
        print(f"GATE 0 FAILED — {len(failed)} sentence(s) below {FLOOR}. "
              f"Do not spend on video.")
        for b, s in failed:
            print(f"   {b:.3f}  {s}")
        print("\nIf a sentence fails twice, REWORD it — do not re-render again.")
        sys.exit(1)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", mp3],
                         capture_output=True, text=True).stdout.strip()
    d = float(dur)
    print(f"GATE 0 PASSED — every sentence >= {FLOOR}")
    print(f"  duration {d:.1f}s -> kling standard {d * 0.0383:.2f} USD "
          f"({d * 0.0383 / 0.005:.0f} cr)")


if __name__ == "__main__":
    main()
