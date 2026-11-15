# Vedora Studio templates

Brand: **Vedora** · Instagram **@the_vedora** · tagline *Discover the Wisdom Within*
Colours: maroon `#761428 → #26060E` (radial), gold `#FBE3A0 → #E8B04B → #C08530`, cream `#F3DDB0`, soft gold `#E2C27E`.
Fonts: **FreeSans** for all Devanagari (FreeSerif breaks conjuncts), Inter for English, GFS Baskerville for the wordmark.

| File | Makes |
|---|---|
| `cards.py` | 1080×1350 feed posts: `shloka_card(...)`, `festival_card(...)` (run it for the two samples) |
| `shloka_reel.py` | 1080×1920 shloka Reel, 12 s, small `@the_vedora` mark, no logo/intro. Content via `VEDORA_CONTENT=content.json` |
| `anim.py` | Welcome Reel animation (lotus bloom → diya lights → wordmark); also supplies shared shapes |
| `music_bed.py` | Calm santoor + drone bed for narrated Reels → `shloka_bed.wav` |
| `music_welcome.py` | Upbeat welcome music (santoor, bansuri, tabla, conch, bells) |
| `emblem.svgfrag` | The lotus-and-diya emblem paths |

Render a Reel: render frame ranges in parallel (`render 0 120 a.mp4`, `120 240 b.mp4`, …), join with the ffmpeg concat demuxer `-c copy`, then add audio with `-c:v copy`, loudness ≈ −14 LUFS.
Publishing: upload media to `media/YYYY-MM/` in this repo, then schedule in Metricool (brand id 8126323) with the raw.githubusercontent.com URL.
Facts: verify every shloka against a standard Gita source and every festival date against Drik Panchang (India) before posting.
