#!/usr/bin/env python3
"""New-machine detector. Prints an orientation + what is missing, then exits 0.

Runs from the SessionStart hook. On the machine that built this project it
prints NOTHING (it must be silent when everything is present, or it becomes
noise that gets ignored). On a fresh clone it is the first thing Claude and
the user see.

Exits 0 always - a setup notice must never block a session.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = {
    "KIE_API_KEY":        "kie.ai - avatar video engine (the only per-reel cost)",
    "ELEVENLABS_API_KEY": "ElevenLabs - the monk's voice",
    "BLOTATO_API_KEY":    "Blotato - posting + DM automations (the only IG path)",
    "APIFY_TOKEN":        "Apify - reads public competitor + own numbers",
}

ORIENTATION = """
================= THIS PROJECT: what it is, in five lines =================

  1. It runs ONE AI influencer end to end: "Master Kaion", an elderly monk who
     does not exist. Vertical reels on Instagram + YouTube in English, and a
     Portuguese twin ("Mestre Kaion"). The face is generated; every post
     carries an AI disclosure.

  2. It sells a thing. A $14.95 ebook (The Quiet Between Thoughts) on Gumroad.
     The funnel is: reel -> viewer comments a keyword -> automatic DM with a
     free practice + a discount link. That DM is the whole business.

  3. A reel is made like this: pick a proven topic from the competitor corpus
     -> write the script -> ElevenLabs voices it -> kie.ai animates a still
     photo of the monk to the audio -> captions + music are assembled locally.
     Roughly $2-6 and ~20 minutes of machine time per reel.

  4. NOTHING is ever published without you approving that exact reel. Building
     and reviewing are free and need no permission. Posting does.

  5. WANT A DIFFERENT INFLUENCER (not a monk)? Do not edit this one. Run the
     skill:  /recreate-influencer
     It takes a target account to learn from, builds a new character, and
     stands up its own pipeline. This project is what that skill produces.

  Read next: CLAUDE.md (the rules, all paid for in real mistakes) and
  output/PRODUCTION_LEDGER.md (what already exists - never rebuild a topic).
===========================================================================
"""


def env_keys(path):
    keys = {}
    if not os.path.exists(path):
        return keys
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        keys[k.strip()] = v.strip().strip('"').strip("'")
    return keys


def main():
    envp = os.path.join(ROOT, "..", ".env") if False else os.path.join(ROOT, ".env")
    keys = env_keys(envp)
    missing = [k for k in REQUIRED if not keys.get(k)]

    if os.path.exists(envp) and not missing:
        return 0                      # configured machine: stay silent

    print(ORIENTATION)
    if not os.path.exists(envp):
        print("  NO .env ON THIS MACHINE - this looks like a fresh copy.\n")
        print("  Run this, then paste your keys into the file that opens:\n")
        print("      cp .env.example .env && open -t .env\n")
    else:
        print("  .env exists but these keys are empty:\n")
    for k in missing:
        print("      %-20s %s" % (k, REQUIRED[k]))
    print("""
  Keys are yours and cost money - this project never ships with any. .env is
  gitignored, so it does not travel with the folder. Get them here:
      kie.ai  ·  elevenlabs.io  ·  blotato.com  ·  console.apify.com

  Tell Claude "keys are in .env" when done and it will verify them.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
