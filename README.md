# AI Influencer Factory

This project builds and runs an **AI influencer**: a person who does not exist,
who speaks to camera in short vertical videos, posts them to Instagram and
YouTube, and sells a digital product through the comments.

It currently runs one: **Master Kaion**, an elderly monk who shares calm,
practical wisdom. He has ~1,000 Instagram followers, a best video of ~98,000
views, and sells a $14.95 ebook.

## What kind of influencer can it make?

One kind, done well: **a single character, seated, talking to camera** — the
"wise voice" format. Think:

- a monk sharing life advice *(what it makes today)*
- a grandmother with old remedies
- a doctor with health habits
- a coach, a teacher, a retired craftsman

Anything where one face gives you 30–90 seconds of advice. It does **not** make
dancing, vlogs, product demos, or anything with real footage. The character is
a generated photo brought to life with a generated voice.

## How it works, in plain language

1. **Learn from someone real.** You point it at an influencer who already
   works. It reads their most successful videos and learns what topics and
   phrasings get views.
2. **Make a character.** It designs a face and a voice. You approve them
   before anything costs money.
3. **Make videos.** For each video: pick a proven topic → write the script →
   the voice reads it → the face is animated to the voice → captions and
   music go on. About **$2–6 and 20 minutes per video.**
4. **You post.** Nothing goes public until you have seen that exact video and
   said yes. It then schedules the post and sets up the reply system.
5. **Sell in the comments.** Each video asks viewers to comment one word.
   Anyone who does gets an automatic private message with a free tip and a
   discount link to the product. That message is the whole business.

## Getting started

You need four accounts, all of which have free tiers to start:

| service | what it does | cost |
|---|---|---|
| kie.ai | animates the face | the only real per-video cost, ~$2–6 |
| ElevenLabs | the voice | small monthly plan |
| Blotato | posts to Instagram/YouTube and sends the DMs | monthly plan |
| Apify | reads public numbers from other accounts | free tier is enough |

Then, in this folder:

1. Make a copy of `.env.example` and name it `.env`.
2. Open it and paste each key next to its name.
3. Open Claude Code in this folder. It will check the keys and tell you
   what is missing.

**To continue Master Kaion**, say what you want: "make the next video",
"how is the account doing", "fix the DMs".

**To make a completely new influencer**, say: `/recreate-influencer`
and tell it which real account to learn from.

## Two rules that protect you

- **Nothing is ever posted without your yes** on that specific video.
- **Every post is labelled as AI** — the platforms require it, and the label is
  switched on in the Instagram app when you post.

## Where things are

- `CLAUDE.md` — the full rulebook. Every rule in it was learned from a real,
  paid-for mistake. Long, but it is why the project works.
- `output/PRODUCTION_LEDGER.md` — every video ever made, so no topic is
  made twice.
- `scripts/` — the machinery. You never need to open these.
