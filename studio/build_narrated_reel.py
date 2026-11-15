"""Assemble a narrated Vedora shloka Reel.

python3 build_narrated_reel.py content.json out.mp4 [hook.wav] sanskrit1.wav sanskrit2.wav hindi.wav [english.wav]
(hook.wav is expected exactly when content.json has a \"hook\")

content.json holds the on-screen text (ref, sanskrit[2], hindi[2], english[2], takeaway). Narration clips are
trimmed, laid out with pauses, the on-screen text is timed to them, the calm music bed is ducked under the voice,
and the result is loudness-matched for Instagram (about -14 LUFS).
"""
import json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
FPS = 30

def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)

def duration(path):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)).stdout)

def lufs(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1])

def main(content_path, out, *clips):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="vedora_"))
    content = json.load(open(content_path, encoding="utf-8"))
    # 1. trim each clip's silence and convert to 48 kHz mono
    trimmed = []
    for i, c in enumerate(clips):
        t = tmp / f"clip{i}.wav"
        run("ffmpeg", "-y", "-v", "error", "-i", c, "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,"
            "afade=t=in:d=0.02,aresample=48000", "-ac", "1", str(t))
        trimmed.append((t, duration(t)))
    # 2. timeline: [hook], sanskrit 1, sanskrit 2, hindi, [english] with pauses between
    k = 1 if content.get("hook") else 0           # index of the first Sanskrit clip
    gaps = ([1.0] if k else []) + [0.5, 0.9, 0.7]
    starts, t = [], 0.8 if not k else 0.4
    for i, (_, d) in enumerate(trimmed):
        starts.append(t); t += d + (gaps[i] if i < len(gaps) else 0)
    end = starts[-1] + trimmed[-1][1]
    st = lambda i: starts[i]
    dur = lambda i: trimmed[i][1]
    times = {}
    if k:
        hook_end = st(0) + dur(0)
        times.update(hook_in=0.15, hook_sub=st(0) + dur(0) * 0.68, hook_out=hook_end + 0.25, ref=hook_end + 0.6)
    else:
        times.update(hook_in=0, hook_sub=0, hook_out=0, ref=0.2)
    times.update(s1=st(k) - 0.15, s2=st(k + 1) - 0.15, divider=st(k + 2) - 0.6, h1=st(k + 2) - 0.1,
                 h2=st(k + 2) + dur(k + 2) * 0.5)
    if len(trimmed) > k + 3:             # English is narrated too
        times.update(e1=st(k + 3) - 0.1, e2=st(k + 3) + dur(k + 3) * 0.5, take=end + 0.3); total = round(end + 3.0, 2)
    else:                                # English shown as text only: give it reading time after the voice ends
        times.update(e1=end + 0.2, e2=end + 0.5, take=end + 1.8); total = round(end + 4.6, 2)
    content.update(times=times, duration=total)
    cj = tmp / "content.json"; json.dump(content, open(cj, "w", encoding="utf-8"), ensure_ascii=False)
    # 3. narration track
    voice = tmp / "voice.wav"
    inputs, filt = [], []
    for i, (p, _) in enumerate(trimmed):
        inputs += ["-i", str(p)]
        ms = int(starts[i] * 1000)
        filt.append(f"[{i}]adelay={ms}|{ms}[v{i}]")
    filt.append("".join(f"[v{i}]" for i in range(len(trimmed))) + f"amix=inputs={len(trimmed)}:normalize=0,apad=whole_dur={total}[v]")
    run("ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[v]", "-ac", "1", str(voice))
    # 4. music bed of the same length
    music = tmp / "bed.wav"
    run(sys.executable, str(HERE / "music_bed.py"), cwd=tmp, env={**os.environ, "VEDORA_DURATION": str(total), "VEDORA_MUSIC_OUT": str(music)})
    # 5. video frames (2 chunks in parallel)
    n = int(round(total * FPS)); half = n // 2
    env = {**os.environ, "VEDORA_CONTENT": str(cj)}
    procs = [subprocess.Popen([sys.executable, str(HERE / "shloka_reel.py"), "render", str(a), str(b), str(tmp / f"part{k}.mp4")], env=env)
             for k, (a, b) in enumerate([(0, half), (half, n)])]
    assert all(p.wait() == 0 for p in procs)
    (tmp / "parts.txt").write_text("file 'part0.mp4'\nfile 'part1.mp4'\n")
    video = tmp / "video.mp4"
    run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "parts.txt"), "-c", "copy", str(video))
    # 6. mix: voice at -16 LUFS, music ducked under it, whole thing to about -14 LUFS
    vg = -16 - lufs(voice); mg = -27 - lufs(music)
    mix = tmp / "mix.wav"
    run("ffmpeg", "-y", "-v", "error", "-i", str(voice), "-i", str(music), "-filter_complex",
        f"[0]volume={vg:.2f}dB,aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[vo][sc];"
        f"[1]volume={mg:.2f}dB[mu];[mu][sc]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=500[duck];"
        f"[vo][duck]amix=inputs=2:normalize=0:duration=first[m]", "-map", "[m]", str(mix))
    fg = -14 - lufs(mix)
    tmp_out = pathlib.Path(out).with_suffix(".tmp.mp4")
    run("ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", f"volume={fg:.2f}dB,alimiter=limit=0.95", "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(tmp_out))
    tmp_out.rename(out)
    print(json.dumps({"out": out, "duration": total, "times": {k: round(v, 2) for k, v in times.items()}}, ensure_ascii=False))

if __name__ == "__main__":
    main(*sys.argv[1:])
