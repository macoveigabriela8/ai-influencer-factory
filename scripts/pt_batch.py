#!/usr/bin/env python3
"""Render the PT launch batch from scripts_PT.json, sequentially, budget-capped.

    python3 scripts/pt_batch.py

Per reel: ElevenLabs TTS (EL_VOICE_PT) -> upload -> kling/ai-avatar-standard
single take with a rotated PT anchor -> poll -> download to
output/markets/PT/assets/sdPTn.mp4. Stops when the credit floor is hit.
State in output/markets/PT/source/batch_state.json so it is resumable.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import kie  # noqa: E402

PT = os.path.join(ROOT, "output", "markets", "PT")
SCRIPTS = os.path.join(PT, "source", "scripts_PT.json")
STATE = os.path.join(PT, "source", "batch_state.json")
CREDIT_FLOOR = 6000   # keep ~$30 for the ES monk

# anchor rotation: one look per reel, never the same twice in a row
ANCHORS = ["pt_a2_window_light", "pt_a3_veranda_standing", "pt_a4_low_table",
           "pt_a5_grey_shawl_mist", "pt_a6_dirt_path", "pt_a7_candle_dark",
           "pt_mestre_mat", "pt_a2_window_light", "pt_a4_low_table"]

FRAMING = {
    "pt_a3_veranda_standing": "wide full-body shot",
    "pt_a6_dirt_path": "wide full-body shot",
    "pt_mestre_mat": "wide full-body shot",
}


def env(k):
    for l in open(os.path.join(ROOT, ".env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip()


def tts(text, out):
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.75,
                           "style": 0.15, "use_speaker_boost": True,
                           "speed": 0.88}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{env('EL_VOICE_PT')}"
        "?output_format=mp3_44100_192",
        body, {"xi-api-key": env("ELEVENLABS_API_KEY"),
               "Content-Type": "application/json"})
    open(out, "wb").write(urllib.request.urlopen(req, timeout=600).read())


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", p],
        capture_output=True, text=True).stdout.strip())


def main():
    items = json.load(open(SCRIPTS))
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    for i, it in enumerate(items):
        rid = it["id"]
        if st.get(rid, {}).get("done"):
            print(rid, "already done"); continue
        bal = kie.credits()
        if bal < CREDIT_FLOOR + 800:
            print(f"STOP: balance {bal} near floor {CREDIT_FLOOR}"); break
        mp3 = os.path.join(PT, "assets", f"voice_{rid}.mp3")
        if not os.path.exists(mp3):
            tts(it["script"], mp3)
        d = dur(mp3)
        print(f"{rid}: voice {d:.1f}s")
        aud = kie.upload(mp3)
        anchor = ANCHORS[i % len(ANCHORS)]
        img = open(os.path.join(PT, "anchors", anchor + ".url")).read().strip()
        shot = FRAMING.get(anchor, "medium shot")
        prompt = (f"Static locked-off camera, {shot}, one continuous take, "
            "cinematic film still, documentary style. An elderly monk with "
            "round wire-rimmed glasses and a short white chin beard speaks "
            "directly to the camera throughout, in Brazilian Portuguese, in a "
            "calm measured grandfatherly voice. His hands stay resting still "
            "the entire time. Small natural head movements, natural lip "
            "movement matching the speech, subtle micro-expressions, realistic "
            "skin, natural imperfections, realistic shadows. Only his voice "
            "and quiet ambience.")
        r = kie.api("/jobs/createTask", {"model": "kling/ai-avatar-standard",
            "input": {"image_url": img, "audio_url": aud, "prompt": prompt}})
        tid = r["data"]["taskId"]
        print(f"{rid}: task {tid} anchor {anchor}")
        while True:
            j = (kie.api(f"/jobs/recordInfo?taskId={tid}").get("data") or {})
            s = j.get("state")
            if s in ("success", "fail"):
                break
            time.sleep(30)
        if s == "fail":
            print(f"{rid}: FAILED {j.get('failMsg')}")
            st[rid] = {"done": False, "fail": str(j.get("failMsg"))[:200]}
        else:
            u = [x for x in kie.urls_from(j) if ".mp4" in x][0]
            out = os.path.join(PT, "assets", f"sd{rid}.mp4")
            kie.fetch(u, out)
            st[rid] = {"done": True, "credits": j.get("creditsConsumed"),
                       "anchor": anchor, "dur": d, "file": out}
            print(f"{rid}: done, {j.get('creditsConsumed')} credits")
        json.dump(st, open(STATE, "w"), indent=1)
    print("BATCH COMPLETE · balance:", kie.credits())


if __name__ == "__main__":
    main()
