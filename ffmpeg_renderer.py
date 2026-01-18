import subprocess
import os
import shutil
from typing import List

# Detect ffmpeg availability once
HAVE_FFMPEG = shutil.which("ffmpeg") is not None


def render_short(input_path, start, end, srt_path, output_path):
    # Use safe quoting for subtitle path and apply common short settings
    vf = "crop=ih*9/16:ih,scale=1080:1920"
    # subtitles filter needs proper escaping if path contains spaces
    subtitles_filter = "subtitles='" + srt_path + "':force_style='Fontsize=46'"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ss",
        str(start),
        "-to",
        str(end),
        "-vf",
        f"{vf},{subtitles_filter}",
        "-af",
        "loudnorm",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        output_path,
    ]
    if not HAVE_FFMPEG:
        # ffmpeg not available on host; skip actual render
        return
    try:
        subprocess.run(cmd, check=False)
    except Exception:
        return


def render_short_cached(input_path, start, end, srt_path, output_path):
    """Higher-level wrapper that skips rendering if output exists and is fresher than source."""
    if os.path.exists(output_path):
        try:
            if os.path.exists(input_path) and os.path.getmtime(
                output_path
            ) >= os.path.getmtime(input_path):
                return {"output": output_path, "skipped": True}
        except Exception:
            pass
    render_short(input_path, start, end, srt_path, output_path)
    return {"output": output_path, "skipped": False}


def render_clips_parallel(tasks: List[dict], workers: int = 4):
    """
    Render a list of clip tasks in parallel.

    Each task should contain keys: input_path, start, end, srt_path, output_path.
    """
    try:
        from ffmpeg_worker import render_batch_parallel

        formatted = []
        for t in tasks:
            formatted.append(
                {
                    "source": t.get("input_path"),
                    "start": t.get("start"),
                    "end": t.get("end"),
                    "srt_path": t.get("srt_path"),
                    "output_path": t.get("output_path"),
                }
            )
        return render_batch_parallel(formatted, max_workers=workers)
    except Exception:
        # fallback to sequential
        res = []
        for t in tasks:
            res.append(
                render_short_cached(
                    t.get("input_path"),
                    t.get("start"),
                    t.get("end"),
                    t.get("srt_path"),
                    t.get("output_path"),
                )
            )
        return res


def render_longform(clips_list_file, music_file, output_path):
    # Concatenate clips
    # Build concatenated output using concat demuxer
    temp_out = "temp_long.mp4"
    concat_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        clips_list_file,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        temp_out,
    ]
    if not HAVE_FFMPEG:
        # cannot run ffmpeg: produce placeholder by touching output
        try:
            open(temp_out, "wb").close()
        except Exception:
            pass
    else:
        subprocess.run(concat_cmd, check=False)

    # Attach music, ducking under speech if possible
    if music_file and os.path.exists(music_file):
        music_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            temp_out,
            "-i",
            music_file,
            "-filter_complex",
            (
                "[1:a]volume=0.12[a1];"
                "[0:a][a1]sidechaincompress=threshold=0.02:ratio=10:attack=20:release=250"
            ),
            "-c:v",
            "copy",
            output_path,
        ]
        if HAVE_FFMPEG:
            subprocess.run(music_cmd, check=False)
        else:
            try:
                os.replace(temp_out, output_path)
            except Exception:
                pass
    else:
        # no music provided — move temp to output
        try:
            os.replace(temp_out, output_path)
        except Exception:
            # fallback to copying via ffmpeg
            if HAVE_FFMPEG:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", temp_out, "-c", "copy", output_path],
                    check=False,
                )
            else:
                try:
                    open(output_path, "wb").close()
                except Exception:
                    pass


def assemble_from_segments(
    segments, music_file=None, output_path="longform_output.mp4"
):
    """segments: list of dicts with keys: source_path, start, end, title(optional)

    This will extract each segment to a temp file, create a concat list, and run render_longform.
    It will also create an ffmetadata file with chapters if titles provided.
    """
    import tempfile
    import os

    tmpdir = tempfile.mkdtemp(prefix="clipforge_")
    list_file = os.path.join(tmpdir, "clips.txt")
    temp_files = []
    for i, s in enumerate(segments):
        src = s.get("source_path")
        start = s.get("start")
        end = s.get("end")
        out = os.path.join(tmpdir, f"seg_{i}.mp4")
        # extract segment
        if HAVE_FFMPEG:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                src,
                "-ss",
                str(start),
                "-to",
                str(end),
                "-c",
                "copy",
                out,
            ]
            subprocess.run(cmd, check=False)
        else:
            # create empty placeholder segment file
            try:
                open(out, "wb").close()
            except Exception:
                pass
        temp_files.append(out)

    # write concat list
    with open(list_file, "w", encoding="utf-8") as f:
        for t in temp_files:
            f.write(f"file '{t}'\n")

    # create ffmetadata for chapters if titles
    metadata_path = os.path.join(tmpdir, "meta.txt")
    has_titles = any(s.get("title") for s in segments)
    if has_titles:
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\n")
            time_acc = 0.0
            for s in segments:
                start = s.get("start", 0.0)
                dur = s.get("end", start) - start
                title = s.get("title", "")
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={int(time_acc * 1000)}\n")
                f.write(f"END={int((time_acc + dur) * 1000)}\n")
                f.write(f"title={title}\n")
                time_acc += dur

    # render longform
    render_longform(list_file, music_file, output_path)

    # attach metadata chapters if present
    if has_titles:
        tmp_out = output_path + ".withmeta.mp4"
        if HAVE_FFMPEG:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    output_path,
                    "-i",
                    metadata_path,
                    "-map_metadata",
                    "1",
                    "-c",
                    "copy",
                    tmp_out,
                ],
                check=False,
            )
        try:
            os.replace(tmp_out, output_path)
        except Exception:
            pass

    return output_path
