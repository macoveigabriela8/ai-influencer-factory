#!/usr/bin/env python3
"""PT audiobook for O Silêncio Entre Pensamentos via ElevenLabs.

    python3 scripts/build_audiobook_pt.py            # generate + QC + assemble
    python3 scripts/build_audiobook_pt.py qc         # re-run QC only

Recipe (verified against ElevenLabs docs 2026-08-08): eleven_multilingual_v2
(v3 audio tags rejected: v3 drops <break> support and v2 is the proven
pipeline), voice EL_VOICE_PT (same voice as the PT reels), one chunk per day
(~200-300 words, far under any limit), previous_request_ids stitching (max 3)
for prosody continuity, <break> tags <=3s for pacing, stability 0.55 /
similarity 0.75 / speed 0.92.

Gate 0 (standing rule): every chunk is whisper-transcribed and EVERY script
sentence must appear at >=0.85 similarity individually; failures are re-rolled
with a FRESH render. Assembly: ffmpeg concat with 1.8s gaps.
"""
import difflib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "output", "book")
AUD = os.path.join(BOOK, "audio_pt")
MODEL = "eleven_multilingual_v2"
GAP = 1.8

NUMS = ["um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito",
        "nove", "dez", "onze", "doze", "treze", "catorze", "quinze",
        "dezesseis", "dezessete", "dezoito", "dezenove", "vinte",
        "vinte e um", "vinte e dois", "vinte e três", "vinte e quatro",
        "vinte e cinco", "vinte e seis", "vinte e sete", "vinte e oito",
        "vinte e nove", "trinta"]


def env(k):
    for l in open(os.path.join(ROOT, ".env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip()


def load():
    p1 = json.load(open(os.path.join(BOOK, "pt_days_0_9.json")))
    p2 = json.load(open(os.path.join(BOOK, "pt_days_10_19.json")))
    p3 = json.load(open(os.path.join(BOOK, "pt_days_20_29.json")))
    return p1["weeks"], p1["days"] + p2["days"] + p3["days"]


def day_text(i, d):
    return " ".join([
        f"Dia {NUMS[i]}. {d['title']}. <break time=\"1.4s\" />",
        ' <break time="1.0s" /> '.join(d["paras"]),
        '<break time="1.6s" /> A prática de hoje. <break time="0.8s" />',
        ' <break time="0.7s" /> '.join(d["practice_steps"]),
        '<break time="1.6s" /> Uma linha para escrever esta noite: '
        f'<break time="0.6s" /> {d["journal"]}'])


def front_text():
    return ("O Silêncio Entre Pensamentos. Um retorno de trinta dias à "
            "quietude. Mestre Kaion. <break time=\"2.0s\" /> Antes de "
            "começar. <break time=\"1.2s\" /> Você não encontrou este livro "
            "porque a sua vida está quebrada. Encontrou porque a sua mente é "
            "barulhenta, e você desconfia de que não precisa ser assim. "
            "<break time=\"1.0s\" /> Passei quarenta anos aprendendo uma "
            "coisa em silêncio: a paz não se encontra mudando o lugar onde "
            "você vive. Encontra-se mudando o modo como você encontra a "
            "própria mente. Os trinta dias deste livro são o modo como eu a "
            "ensino. <break time=\"1.0s\" /> Cada dia pede dez minutos, às "
            "vezes menos. Um ensinamento curto. Uma prática pequena. Uma "
            "linha para escrever. Não leia adiantado. Um dia vivido muda o "
            "dia seguinte. <break time=\"1.0s\" /> Se você perder um dia, "
            "não falhou. Recomece de onde parou. O caminho não guarda rancor "
            "de quem anda devagar.")


def tts(text, prev_ids, out):
    body = json.dumps({
        "text": text, "model_id": MODEL,
        "previous_request_ids": prev_ids[-3:],
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.75,
                           "speed": 0.92}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{env('EL_VOICE_PT')}"
        "?output_format=mp3_44100_192",
        body, {"xi-api-key": env("ELEVENLABS_API_KEY"),
               "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=600)
    rid = r.headers.get("request-id") or r.headers.get("x-request-id") or ""
    open(out, "wb").write(r.read())
    return rid


def strip_tags(t):
    return re.sub(r"<break[^>]*/>", " ", t)


# Whisper renders numbers as DIGITS ("Dia 1", "40 anos") where our script has
# WORDS ("Dia um", "quarenta anos"). Comparing them directly failed every
# chapter that mentions a number and burned 60k characters in re-rolls on
# 2026-08-08. Numbers are dropped from BOTH sides before comparing: the gate
# exists to catch dropped or hallucinated CONTENT, not spelling of numerals.
NUMWORDS = set("""um uma dois duas tres três quatro cinco seis sete oito nove
dez onze doze treze catorze quatorze quinze dezesseis dezessete dezoito
dezenove vinte trinta quarenta cinquenta sessenta e meia""".split())


def clean(t, drop_numbers=True):
    t = re.sub(r"[^a-z0-9áéíóúâêôãõçà ]", " ", t.lower().replace("\n", " "))
    words = [w for w in t.split()
             if not (drop_numbers and (w.isdigit() or w in NUMWORDS))]
    return " ".join(words)


def qc_chunk(mp3, text):
    """Whisper-transcribe (mlx, same engine as assemble_pt.py); every sentence
    must align >=0.85 individually.

    Similarity uses the SUM of matching blocks, not the single longest match:
    one differing word mid-sentence must not fail an otherwise perfect line.
    """
    import mlx_whisper
    r = mlx_whisper.transcribe(
        mp3, path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        language="pt")
    # Whisper loops on trailing silence, emitting degenerate segments like
    # "Cas Cas Cas Cas..." or "tenha tenha tenha...". Those are decoder
    # artifacts, never audio: drop any segment whose words are mostly repeats
    # before measuring, or the insertion check below false-fails good files.
    kept = []
    for s in r["segments"]:
        w = clean(s["text"]).split()
        if len(w) >= 6 and len(set(w)) / len(w) < 0.35:
            continue
        kept.append(s["text"])
    heard = clean(" ".join(kept))
    fails = []
    # truncation guard: PT narration runs ~13-15 chars/sec at speed 0.92, plus
    # the break tags. A take under half its expected length is cut short even
    # if every word it DID say matches.
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", mp3], capture_output=True, text=True).stdout or 0)
    expect = len(strip_tags(text)) / 14.0
    if dur < expect * 0.5:
        fails.append((0.0, f"TRUNCATED: {dur:.0f}s audio vs ~{expect:.0f}s expected"))
    for s in re.split(r"[.!?]", strip_tags(text)):
        s2 = clean(s)
        if len(s2) < 12:
            continue
        m = difflib.SequenceMatcher(None, s2, heard, autojunk=False)
        ratio = sum(b.size for b in m.get_matching_blocks()) / max(1, len(s2))
        if ratio < 0.85:
            fails.append((round(ratio, 2), s.strip()[:70]))

    # INSERTION check. The rules above only prove every scripted line is
    # PRESENT; they cannot see words the model ADDED. Day 14 shipped a
    # hallucinated "Estito" between two correct sentences and passed clean
    # (caught by an independent auditor 2026-08-08). Measure the reverse
    # direction: how much of what was HEARD is explained by the script.
    # Whisper loops on trailing silence ("tenha tenha tenha..."), so collapse
    # consecutive repeated words before measuring or every file false-fails.
    hw, out = heard.split(), []
    for w in hw:
        if not out or out[-1] != w:
            out.append(w)
    heard_dedup = " ".join(out)
    script = clean(strip_tags(text))
    m = difflib.SequenceMatcher(None, heard_dedup, script, autojunk=False)
    cover = sum(b.size for b in m.get_matching_blocks()) / max(1, len(heard_dedup))
    # Threshold calibrated 2026-08-08 on this batch: at 0.92 the check flagged
    # a DIFFERENT random chapter on every run (0.68-0.89) purely from Whisper
    # variance, and all of them proved clean on acoustic inspection. 0.80
    # catches gross damage (a duplicated or hallucinated paragraph) without
    # crying wolf. HONEST LIMIT: it cannot catch a short insertion such as the
    # 6-character "Estito" hallucinated into day 14 — that took the
    # independent auditor's RMS-plus-biased-decode analysis. Small insertions
    # are the listener gate's job, not this one's.
    if cover < 0.80:
        extra = [b for b in m.get_opcodes() if b[0] == "delete"
                 and b[2] - b[1] > 5]
        snippets = [heard_dedup[b[1]:b[2]][:40] for b in extra[:3]]
        fails.append((round(cover, 2), f"INSERTED CONTENT: {snippets}"))
    return fails


def main():
    os.makedirs(AUD, exist_ok=True)
    weeks, days = load()
    # Names carry an explicit playback sequence. The earlier scheme
    # ("01_dia" / "01a_semana") sorted the week opener AFTER its first day,
    # because "_" < "a" in ASCII. Sequence numbers make order unambiguous.
    chunks, seq = [("000_frente", front_text(), "00_frente")], 1
    for i, d in enumerate(days):
        if i == 0 or days[i - 1]["week"] != d["week"]:
            w = weeks[d["week"]]
            chunks.append((f"{seq:03d}_semana",
                           f"{w['n']}. {w['t']}. <break time=\"1.0s\" />",
                           f"{i + 1:02d}a_semana"))
            seq += 1
        chunks.append((f"{seq:03d}_dia", day_text(i, d), f"{i + 1:02d}_dia"))
        seq += 1

    # adopt audio already paid for under the old names (and the verified probe)
    for name, _, legacy in chunks:
        new = os.path.join(AUD, name + ".mp3")
        old = os.path.join(AUD, legacy + ".mp3")
        if not os.path.exists(new) and os.path.exists(old):
            os.rename(old, new)
    probe = os.path.join(AUD, "TEST_01.mp3")
    if os.path.exists(probe) and not os.path.exists(os.path.join(AUD, "002_dia.mp3")):
        os.rename(probe, os.path.join(AUD, "002_dia.mp3"))

    qc_only = len(sys.argv) > 1 and sys.argv[1] == "qc"
    prev = []
    report = {}
    for name, text, _ in chunks:
        mp3 = os.path.join(AUD, name + ".mp3")
        if not qc_only and not os.path.exists(mp3):
            for attempt in range(2):
                rid = tts(text, prev, mp3)
                fails = qc_chunk(mp3, text)
                if not fails:
                    prev.append(rid)
                    break
                print(f"{name} attempt {attempt + 1} FAILED: {fails[:3]}")
                # keep the file: a failed take is already billed, and it is
                # the only evidence for diagnosing WHY it failed
                os.rename(mp3, mp3.replace(".mp3", f".fail{attempt}.mp3"))
            else:
                report[name] = "failed twice - inspect .fail*.mp3"
                continue
            print(f"{name} ok ({len(strip_tags(text))} chars)")
        elif os.path.exists(mp3):
            fails = qc_chunk(mp3, text)
            if fails:
                report[name] = fails[:3]
    if report:
        print("QC REPORT (needs attention):", json.dumps(report, indent=1,
                                                         ensure_ascii=False))
        return 1

    # assembly: concat with GAP seconds of silence between chunks
    files = sorted(f for f in os.listdir(AUD) if f.endswith(".mp3")
                   and not f.startswith("FULL"))
    # The spacer must be the SAME codec/rate/layout as the chapters (mp3,
    # 44100, mono). A .wav spacer is silently DROPPED by the concat demuxer:
    # on 2026-08-08 the first assembly came out 61s short with every chapter
    # running straight into the next. Always verify total duration after.
    sil = os.path.join(AUD, "_gap.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=r=44100:cl=mono:d={GAP}",
                    "-c:a", "libmp3lame", "-b:a", "192k", sil],
                   capture_output=True)
    lst = os.path.join(AUD, "_list.txt")
    with open(lst, "w") as f:
        for i, m in enumerate(files):
            if i:
                f.write(f"file '{sil}'\n")
            f.write(f"file '{os.path.join(AUD, m)}'\n")
    full = os.path.join(AUD, "FULL_O_Silencio_Entre_Pensamentos.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:a", "libmp3lame", "-b:a", "192k", full],
                   capture_output=True)
    def dur(p):
        return float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)

    got = dur(full)
    want = sum(dur(os.path.join(AUD, m)) for m in files) + GAP * (len(files) - 1)
    print(f"FULL assembled: {full} ({got:.0f}s)")
    if abs(got - want) > 2:
        print(f"⚠️  ASSEMBLY DRIFT: expected {want:.0f}s, got {got:.0f}s "
              f"({got - want:+.0f}s) — spacers or chapters were dropped")
        return 1

    # per-week files, same structure as the EN audiobook zip
    weeknos, cur = {}, -1
    for name, _, _ in chunks:
        if name.endswith("_semana"):
            cur += 1
        if cur >= 0:
            weeknos.setdefault(cur, []).append(name + ".mp3")
    for wn, members in weeknos.items():
        wl = os.path.join(AUD, f"_w{wn}.txt")
        with open(wl, "w") as f:
            for i, m in enumerate(members):
                if i:
                    f.write(f"file '{sil}'\n")
                f.write(f"file '{os.path.join(AUD, m)}'\n")
        out = os.path.join(AUD, f"Semana_{wn + 1}.mp3")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
                        wl, "-c:a", "libmp3lame", "-b:a", "192k", out],
                       capture_output=True)
        print(f"  Semana {wn + 1}: {dur(out):.0f}s ({len(members)} faixas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
