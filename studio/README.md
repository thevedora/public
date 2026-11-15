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
| `vedora_tts.py` | Free narration in the owner's cloned voice (ai4bharat/IndicF5, MIT). Needs `HF_TOKEN` env var and the voice sample from the PRIVATE repo. `0.78|text` = slower Sanskrit recitation. Hindi/Sanskrit only — English comes out broken, keep it on-screen |
| `build_narrated_reel.py` | Trims narration clips, times the on-screen text to them, ducks `music_bed.py` under the voice, outputs the Reel at about −14 LUFS |
| `story_reel.py` + `build_story_reel.py` | Narrated story Reel: hook with echo, subtitles timed to narration, cold→warm mood at the Gita verse, checklist, takeaway, end card. Script format: see `scripts/toxic_boss_6-5.json`. `VEDORA_TEMPO=1.1 VEDORA_GAP_SCALE=0.75` tightens long Reels |
| `emblem.svgfrag` | The lotus-and-diya emblem paths |

Render a Reel: render frame ranges in parallel (`render 0 120 a.mp4`, `120 240 b.mp4`, …), join with the ffmpeg concat demuxer `-c copy`, then add audio with `-c:v copy`, loudness ≈ −14 LUFS.
Publishing: upload media to `media/YYYY-MM/` in this repo, then schedule in Metricool (brand id 8126323) with the raw.githubusercontent.com URL.
Facts: verify every shloka against a standard Gita source and every festival date against Drik Panchang (India) before posting.

Narration setup (CPU): `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`, then `pip install git+https://github.com/ai4bharat/IndicF5.git`, then `pip install "numpy>=2.1"` (IndicF5 pins an old numpy that breaks pyarrow). About 3 minutes of CPU per narrated line on 2 cores.
