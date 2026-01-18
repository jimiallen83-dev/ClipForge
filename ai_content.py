import os
import random
import textwrap
from typing import List

try:
    import openai

    _have_openai = True
except Exception:
    _have_openai = False

from PIL import Image, ImageDraw, ImageFont
import subprocess


def _call_openai(prompt: str, max_tokens: int = 64):
    if not _have_openai or not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OpenAI not available")
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    resp = openai.Completion.create(
        engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens, n=1
    )
    return resp.choices[0].text.strip()


def generate_titles_from_text(text: str, n: int = 5) -> List[str]:
    """Generate title suggestions from clip text. Uses OpenAI when available, otherwise templates."""
    text = (text or "").strip()
    suggestions = []
    if not text:
        # generic titles
        base = [
            "Unbelievable Moment",
            "You Won't Believe This",
            "Must Watch Clip",
            "Top Moment",
        ]
        return random.sample(base, min(n, len(base)))

    if _have_openai and os.environ.get("OPENAI_API_KEY"):
        try:
            prompt = (
                "Generate %d short clickable YouTube title options (3-8 words) "
                "from this clip text:\n\n%s\n\nTitles:\n1." % (n, text)
            )
            out = _call_openai(prompt, max_tokens=80)
            # try to split on newlines or numbers
            out_clean = out.replace("\r", "")
            lines = [line.strip() for line in out_clean.split("\n") if line.strip()]
            for line in lines:
                # remove leading numbering
                title = line.split(".", 1)[-1].strip()
                if title:
                    suggestions.append(title)
            if len(suggestions) >= n:
                return suggestions[:n]
        except Exception:
            pass

    # Fallback heuristic templates
    snip = textwrap.shorten(text, width=60, placeholder="...")
    templates = [
        f"{snip} — You Won't Believe It",
        f"What Happened Next: {snip}",
        f"{snip} (Must Watch)",
        f"Top Moment: {snip}",
        f"Unexpected: {snip}",
    ]
    # dedupe and return n items
    seen = set()
    for t in templates:
        if t not in seen:
            suggestions.append(t)
            seen.add(t)
        if len(suggestions) >= n:
            break
    return suggestions


def generate_script_from_text(
    text: str, tone: str = "energetic", target_seconds: int = 20
) -> str:
    """Generate a short script suitable for 20s voiceover.

    Uses OpenAI if available; otherwise uses heuristic expansions.
    """
    text = (text or "").strip()
    if _have_openai and os.environ.get("OPENAI_API_KEY"):
        try:
            prompt = (
                f"Write a {target_seconds}-second {tone} voiceover script (concise) "
                f"for this clip:\n\n{text}\n\nScript:"
            )
            return _call_openai(prompt, max_tokens=150)
        except Exception:
            pass

    # Fallback: craft a short script by splitting sentences
    sent = text.split(".")
    core = sent[0].strip() if sent else text
    script = f"Here's the moment: {core}. Don't blink — this is wild!"
    return script


def generate_thumbnail(
    source_video_path: str, time_seconds: float, overlay_text: str, out_path: str
):
    """Extract a frame at `time_seconds` and overlay `overlay_text` using PIL."""
    # extract frame via ffmpeg
    tmp_img = out_path + ".frame.jpg"
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(time_seconds),
        "-i",
        source_video_path,
        "-frames:v",
        "1",
        tmp_img,
    ]
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        # ffmpeg not installed on this host; continue and create placeholder image below
        pass
    # open and overlay
    try:
        im = Image.open(tmp_img).convert("RGBA")
    except Exception:
        # create placeholder
        im = Image.new("RGBA", (1280, 720), (30, 30, 30))

    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except Exception:
        font = ImageFont.load_default()

    text = overlay_text or ""
    # wrap text
    lines = textwrap.wrap(text, width=24)
    w, h = im.size
    y = h - (len(lines) * 50) - 40
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except Exception:
            tw, th = font.getsize(line)
        x = (w - tw) / 2
        # outline
        draw.text((x - 2, y - 2), line, font=font, fill=(0, 0, 0))
        draw.text((x + 2, y - 2), line, font=font, fill=(0, 0, 0))
        draw.text((x - 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += th + 8

    # JPEG doesn't support alpha; convert to RGB
    try:
        if im.mode in ("RGBA", "LA"):
            im = im.convert("RGB")
    except Exception:
        im = im.convert("RGB")
    im.save(out_path)
    # cleanup tmp
    try:
        os.remove(tmp_img)
    except Exception:
        pass
    return out_path


def generate_tts_from_script(script: str, out_path: str, lang: str = "en") -> str:
    """Generate TTS audio using gTTS if available, fallback to returning None."""
    try:
        from gtts import gTTS

        tts = gTTS(text=script, lang=lang)
        tts.save(out_path)
        return out_path
    except Exception:
        # not available or failed
        return None
