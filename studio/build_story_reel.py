"""Assemble a narrated Vedora story Reel from a script and its narration clips.

python3 build_story_reel.py script.json out.mp4 clip1.wav clip2.wav ...

script.json: {"ref", "shloka": [2 lines], "end": [lines], "clips": [{"kind": hook|sub|shloka|meaning|check|take,
               "speed"?, "segs": [[devanagari_text_spoken, [subtitle lines]], ...]}, ...]}
One clip per script clip (made with vedora_tts.py from the joined devanagari segs). Subtitles inside a clip are timed in
proportion to the length of each spoken segment (the voice model paces speech by text length).
"""
import json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
FPS = 30

def run(*cmd, **kw): return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)
def duration(p): return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)).stdout)
def lufs(p):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", str(p), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1])

def main(script_path, out, *clips):
    sc = json.load(open(script_path, encoding="utf-8")); C = sc["clips"]
    assert len(clips) == len(C), f"{len(C)} clips in script, {len(clips)} wav files given"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="vedora_story_"))
    tempo = float(os.environ.get("VEDORA_TEMPO", "1.0"))        # speeds up spoken lines (not the shloka), pitch kept
    gap_k = float(os.environ.get("VEDORA_GAP_SCALE", "1.0"))    # scales the pauses between clips
    trimmed = []
    for i, c in enumerate(clips):
        t = tmp / f"clip{i}.wav"
        at = f",atempo={tempo}" if tempo != 1.0 and C[i]["kind"] != "shloka" else ""
        run("ffmpeg", "-y", "-v", "error", "-i", c, "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,afade=t=in:d=0.02,aresample=48000" + at,
            "-ac", "1", str(t))
        trimmed.append((t, duration(t)))
    # timeline: pause after each clip (shorter before the shloka, longer at section changes)
    starts, t = [], 0.45
    for i, (_, d) in enumerate(trimmed):
        starts.append(t)
        nxt = C[i + 1]["kind"] if i + 1 < len(C) else None
        gap = 0.5 if nxt == "shloka" else 1.0 if nxt in ("check", "take") or C[i]["kind"] in ("hook", "meaning") else 0.8
        t += d + gap * gap_k
    ends = [s + d for s, (_, d) in zip(starts, trimmed)]
    E, warm = [], [[0, 0]]
    shloka_i = next((i for i, c in enumerate(C) if c["kind"] == "shloka"), None)
    meaning_last = max((i for i, c in enumerate(C) if c["kind"] == "meaning"), default=shloka_i)
    take_i = next((i for i, c in enumerate(C) if c["kind"] == "take"), len(C) - 1)
    total = round(ends[-1] + 3.2, 2)
    for i, c in enumerate(C):
        segs = c["segs"]; L = [max(1, len(s[0])) for s in segs]; tot = sum(L)
        seg_t = [starts[i] + (ends[i] - starts[i]) * sum(L[:j]) / tot for j in range(len(segs))]
        k = c["kind"]
        if k == "shloka":
            card_out = ends[meaning_last] + 0.7
            E += [dict(style="ref", lines=[sc["ref"]], t_in=starts[i] - 0.25, t_out=card_out),
                  dict(style="shloka", lines=sc["shloka"], t_in=starts[i] - 0.1, t_out=card_out)]
            continue
        for j, (_, sub) in enumerate(segs):
            if not sub: continue
            t_in = seg_t[j] - 0.1 if j == 0 else seg_t[j] + 0.05
            if k in ("check",): t_out = ends[i] + 0.7
            elif k == "take": t_out = total
            elif k == "hook": t_out = ends[i] + 0.55
            elif k == "meaning" and j == len(segs) - 1: t_out = ends[meaning_last] + 0.7
            else: t_out = seg_t[j + 1] if j + 1 < len(segs) else ends[i] + 0.35
            E.append(dict(style="hook" if k == "hook" else k, lines=sub, t_in=t_in, t_out=t_out, slot=j))
    if shloka_i is not None:
        warm += [[starts[shloka_i] - 0.8, 0], [starts[shloka_i] + 0.6, 1], [ends[meaning_last] + 0.4, 1],
                 [ends[meaning_last] + 1.2, 0.72], [starts[take_i] - 0.2, 0.72], [starts[take_i] + 0.8, 1]]
    E.append(dict(style="end", lines=sc.get("end", []), t_in=ends[-1] + 0.5, t_out=total))
    tl = tmp / "timeline.json"
    json.dump(dict(duration=total, warmth=warm, elements=E), open(tl, "w", encoding="utf-8"), ensure_ascii=False)
    # narration track
    voice = tmp / "voice.wav"; inp, filt = [], []
    for i, (p, _) in enumerate(trimmed):
        inp += ["-i", str(p)]; ms = int(starts[i] * 1000); filt.append(f"[{i}]adelay={ms}|{ms}[v{i}]")
    filt.append("".join(f"[v{i}]" for i in range(len(trimmed))) + f"amix=inputs={len(trimmed)}:normalize=0,apad=whole_dur={total}[v]")
    run("ffmpeg", "-y", "-v", "error", *inp, "-filter_complex", ";".join(filt), "-map", "[v]", "-ac", "1", str(voice))
    music = tmp / "bed.wav"
    run(sys.executable, str(HERE / "music_bed.py"), cwd=tmp, env={**os.environ, "VEDORA_DURATION": str(total), "VEDORA_MUSIC_OUT": str(music)})
    # frames in two parallel chunks
    n = int(round(total * FPS)); half = n // 2; env = {**os.environ, "VEDORA_TIMELINE": str(tl)}
    procs = [subprocess.Popen([sys.executable, str(HERE / "story_reel.py"), "render", str(a), str(b), str(tmp / f"p{k}.mp4")], env=env)
             for k, (a, b) in enumerate([(0, half), (half, n)])]
    assert all(p.wait() == 0 for p in procs)
    (tmp / "parts.txt").write_text("file 'p0.mp4'\nfile 'p1.mp4'\n")
    video = tmp / "video.mp4"
    run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "parts.txt"), "-c", "copy", str(video))
    vg, mg = -16 - lufs(voice), -27 - lufs(music); mix = tmp / "mix.wav"
    run("ffmpeg", "-y", "-v", "error", "-i", str(voice), "-i", str(music), "-filter_complex",
        f"[0]volume={vg:.2f}dB,aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[vo][sc];[1]volume={mg:.2f}dB[mu];"
        f"[mu][sc]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=500[duck];[vo][duck]amix=inputs=2:normalize=0:duration=first[m]",
        "-map", "[m]", str(mix))
    fg = -14 - lufs(mix); tmp_out = pathlib.Path(out).with_suffix(".tmp.mp4")
    run("ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", f"volume={fg:.2f}dB,alimiter=limit=0.95", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(tmp_out))
    tmp_out.rename(out)
    print(json.dumps(dict(out=out, duration=total, clip_starts=[round(s, 2) for s in starts]), ensure_ascii=False))

if __name__ == "__main__":
    main(*sys.argv[1:])
