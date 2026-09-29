#!/usr/bin/env python3
"""Cut a 15s story teaser from a master, IG-story-conformed.

    python3 scripts/make_story.py output/reels/reel_23_x_music.mp4 23 [start]

Encoding is pinned to Instagram's native story pipeline: 48kHz AAC-LC 128k
stereo, H.264 high, yuv420p, 30fps. The Aug-7 story published via Blotato
played silent for the user despite the source file carrying clean 44.1kHz
audio (byte-identical upload verified, -22dB mean). 44.1kHz is within spec but
is the one deviation from IG's native 48kHz; conforming removes the only
server-side resample step we cannot observe. (The other suspect is the app's
sticky story-mute toggle, which is viewer-side and not fixable here.)
"""

import os
import subprocess
import sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "output", "reels", "stories")


def main():
    src, rid = sys.argv[1], sys.argv[2]
    start = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, f"story_{rid}_15s.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-i", src,
        "-t", "15", "-r", "30",
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
        "-movflags", "+faststart", dst], check=True)
    print(dst)


if __name__ == "__main__":
    main()
