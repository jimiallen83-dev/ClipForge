def group_by_theme(clips):
    groups = {}
    for c in clips:
        meta = c.get("metadata") or {}
        theme = meta.get("theme") if isinstance(meta, dict) else None
        if not theme:
            theme = c.get("emotion") or "misc"
        groups.setdefault(theme, []).append(c)
    return groups


def arrange_for_longform(clips, target_minutes=15):
    """Arrange clips into a 10-15 minute timeline.

    Strategy:
    - Pick a strong "cold open" clip (highest score)
    - Create sections by interleaving themes for pacing
    - Fill until target duration reached
    """
    clips_sorted = sorted(clips, key=lambda c: c.get("score", 0), reverse=True)
    if not clips_sorted:
        return []

    timeline = []
    total = 0
    # cold open
    cold_open = clips_sorted[0]
    timeline.append(cold_open)
    total += cold_open.get("duration", 0)

    # group remaining
    remaining = clips_sorted[1:]
    groups = group_by_theme(remaining)
    # create a round-robin across groups to keep pacing varied
    group_lists = [list(v) for v in groups.values()]
    idxs = [0] * len(group_lists)
    gi = 0
    while total < target_minutes * 60 and any(
        idxs[i] < len(group_lists[i]) for i in range(len(group_lists))
    ):
        i = gi % len(group_lists)
        if idxs[i] < len(group_lists[i]):
            clip = group_lists[i][idxs[i]]
            timeline.append(clip)
            total += clip.get("duration", 0)
            idxs[i] += 1
        gi += 1

    # if still short, append remaining highest scoring clips
    if total < target_minutes * 60:
        for c in remaining:
            if c in timeline:
                continue
            timeline.append(c)
            total += c.get("duration", 0)
            if total >= target_minutes * 60:
                break

    return timeline


def build_longform(clips, target_minutes=15):
    """Compatibility wrapper: old callers import `build_longform`.

    Delegates to `arrange_for_longform`.
    """
    return arrange_for_longform(clips, target_minutes=target_minutes)
