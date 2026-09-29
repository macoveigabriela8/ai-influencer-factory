#!/usr/bin/env python3
"""Generate the full audiobook from manuscript.json via ElevenLabs.

    python3 scripts/build_audiobook.py

One chunk per day (plus front matter), eleven_multilingual_v2, George,
request stitching (previous_request_ids, max 3) for prosody continuity,
<break> tags for pacing. Outputs per-day mp3s, 4 week files, one full mp3.
"""

import json
import os
import subprocess
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "output", "book")
AUD = os.path.join(BOOK, "audio")
VOICE = "JBFqnCBsd6RMkjVDRZzb"
MODEL = "eleven_multilingual_v2"

WEEKNAMES = ["Week one. The morning.", "Week two. The body.",
             "Week three. The noise.", "Week four. The stillness."]
NUMS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen", "twenty", "twenty-one",
        "twenty-two", "twenty-three", "twenty-four", "twenty-five",
        "twenty-six", "twenty-seven", "twenty-eight", "twenty-nine", "thirty"]


def key():
    for l in open(os.path.join(ROOT, ".env")):
        if l.startswith("ELEVENLABS_API_KEY"):
            return l.split("=", 1)[1].strip()


def tts(text, prev_ids, out):
    body = json.dumps({
        "text": text, "model_id": MODEL,
        "previous_request_ids": prev_ids[-3:],
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.75,
                           "speed": 0.92}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}"
        "?output_format=mp3_44100_192",
        body, {"xi-api-key": key(), "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=600)
    rid = r.headers.get("request-id") or r.headers.get("x-request-id") or ""
    open(out, "wb").write(r.read())
    return rid


def day_text(i, d):
    parts = [f"Day {NUMS[i]}. {d['title']}. <break time=\"1.4s\" />",
             " <break time=\"1.0s\" /> ".join(d["paras"]),
             "<break time=\"1.6s\" /> Today's practice. <break time=\"0.8s\" />",
             " <break time=\"0.7s\" /> ".join(d["steps"]),
             "<break time=\"1.6s\" /> One line to write tonight: "
             f"<break time=\"0.6s\" /> {d['journal']}"]
    return " ".join(parts)


def main():
    os.makedirs(AUD, exist_ok=True)
    m = json.load(open(os.path.join(BOOK, "manuscript.json")))
    prev = []
    files = []

    front = ('The Quiet Between Thoughts. <break time="1.0s" /> '
             'Thirty days of small practices for a mind that will not stop '
             'talking. <break time="1.0s" /> Read by Master Kaion. '
             '<break time="2.2s" />'
             'Before you begin. <break time="1.3s" />'
             'You did not find this book because your life is broken. You '
             'found it because your mind is loud... and you suspect it does '
             'not have to be. <break time="1.2s" />'
             'I spent forty years learning one thing in silence: peace is not '
             'found by changing where you live. It is found by changing how '
             'you meet your own mind. That sentence is easy to read, and slow '
             'to learn. The thirty days ahead are how I teach it. '
             '<break time="1.2s" />'
             'Each day asks for ten minutes, sometimes less. One short '
             'teaching. One small practice. One line to write. Do not listen '
             'ahead. A day heard in one minute does nothing; a day lived '
             'changes the next one. <break time="1.2s" />'
             'If you miss a day, you have not failed. Begin again where you '
             'stopped. The path does not resent slow walkers.')
    p = os.path.join(AUD, "00_intro.mp3")
    if not os.path.exists(p):
        prev.append(tts(front, prev, p))
    files.append(p)
    print("intro ok", flush=True)

    lastweek = -1
    for i, d in enumerate(m["days"]):
        p = os.path.join(AUD, f"{i+1:02d}_day.mp3")
        if not os.path.exists(p):
            t = day_text(i, d)
            if d["week"] != lastweek:
                t = f'<break time="0.5s" /> {WEEKNAMES[d["week"]]} <break time="2.0s" /> ' + t
            prev.append(tts(t, prev, p))
        lastweek = d["week"]
        files.append(p)
        print(f"day {i+1} ok", flush=True)

    outro = ('<break time="1.0s" /> This is the end of the thirty days, and '
             'the beginning of yours. <break time="1.0s" /> Go gently, my '
             'friend. The path does not resent slow walkers. It only asks '
             'that you keep walking. <break time="1.5s" /> The Quiet Between '
             'Thoughts, by Master Kaion.')
    p = os.path.join(AUD, "99_outro.mp3")
    if not os.path.exists(p):
        prev.append(tts(outro, prev, p))
    files.append(p)
    print("outro ok", flush=True)

    # gap file: 1.8s of silence between days
    gap = os.path.join(AUD, "_gap.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=mono", "-t", "1.8", "-c:a",
                    "libmp3lame", "-b:a", "192k", gap], check=True)

    def concat(fs, out):
        lst = os.path.join(AUD, "_list.txt")
        with open(lst, "w") as f:
            for x in fs:
                f.write(f"file '{x}'\nfile '{gap}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                        "-safe", "0", "-i", lst, "-c:a", "libmp3lame", "-b:a",
                        "192k", out], check=True)

    weeks = [(0, 0, 7), (1, 7, 14), (2, 14, 21), (3, 21, 30)]
    daysf = files[1:-1]
    for w, a, b in weeks:
        concat(daysf[a:b], os.path.join(BOOK, f"TQBT_week{w+1}.mp3"))
    concat(files, os.path.join(BOOK, "TQBT_full_audiobook.mp3"))
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0",
                        os.path.join(BOOK, "TQBT_full_audiobook.mp3")],
                       capture_output=True, text=True).stdout.strip()
    print(f"FULL AUDIOBOOK: {float(d)/60:.1f} minutes")


if __name__ == "__main__":
    main()
