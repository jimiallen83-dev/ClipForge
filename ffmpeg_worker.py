"""Worker utilities for parallel FFmpeg processing with caching."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from ffmpeg_renderer import render_short


def _ensure_output_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def render_short_cached(task):
    """task: dict with keys: source, start, end, srt_path, output_path

    Will skip rendering if `output_path` exists and is newer than source file.
    """
    src = task.get("source")
    out = task.get("output_path")
    _ensure_output_dir(out)
    try:
        if os.path.exists(out):
            if src and os.path.exists(src):
                if os.path.getmtime(out) >= os.path.getmtime(src):
                    return {"output": out, "skipped": True}
        # call renderer
        render_short(src, task.get("start"), task.get("end"), task.get("srt_path"), out)
        return {"output": out, "skipped": False}
    except Exception as e:
        return {"error": str(e)}


def render_batch_parallel(tasks, max_workers=4):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(render_short_cached, t): t for t in tasks}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
    return results
