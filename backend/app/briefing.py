"""Readable full-feed facts. No style labels or unverified tactical claims."""
from collections import Counter
from app.discipline import card_facts, card_text


def full_feed_briefing(all_events, new_events, audience):
    if not new_events or new_events[0].schema_version != "1.2":
        return None
    names = {e.team_id: e.team_name for e in all_events if e.team_name}
    score = Counter(e.team_id for e in all_events if e.type == "goal")
    start, end = new_events[0].match_second, new_events[-1].match_second
    clock = lambda s: f"{s // 60}:{s % 60:02d}"
    sentences = [f"From {clock(start)} to {clock(end)}, here is what you missed. "
                 f"The score is {names.get('home', 'Home')} {score['home']}–{score['away']} {names.get('away', 'Away')}."]
    goals = [e for e in new_events if e.type == "goal"]
    if goals:
        sentences.append(" ".join(f"{e.player_name or e.player_id} scored for {names.get(e.team_id, e.team_id)} at {clock(e.match_second)}." for e in goals))
    else:
        sentences.append("Neither side scored during this interval.")
    for team in ("home", "away"):
        passes = [e for e in new_events if e.team_id == team and e.type == "pass"]
        shots = [e for e in new_events if e.team_id == team and e.type == "shot"]
        completed = sum(e.outcome == "complete" for e in passes)
        sentences.append(f"{names.get(team, team)} completed {completed} of {len(passes)} passes and recorded {len(shots)} shots.")
        if audience == "advanced" and passes:
            counts = Counter(e.player_name or e.player_id for e in passes)
            player, count = counts.most_common(1)[0]
            sentences.append(f"{player} attempted the most passes for that side in this interval ({count}).")
    substitutions = [e for e in new_events if e.type == "substitution"]
    for e in substitutions:
        sentences.append(f"{e.recipient_player_name} replaced {e.player_name} for {names.get(e.team_id, e.team_id)}.")
    red_cards = [e for e in new_events if e.type == "red_card"]
    for e in red_cards:
        sentences.append(card_text(card_facts(e, all_events), names, finished=any(e.type == 'match_end' for e in all_events)))
    if any(e.type == "match_end" for e in all_events):
        sentences.append("The synthetic match has finished.")
    elif new_events[-1].type == "half_end":
        sentences.append("The first half has finished.")
    evidence = {e.event_id for e in all_events if e.type in ("goal", "red_card")}
    evidence.update(e.event_id for e in new_events if e.type in ("pass", "shot", "substitution", "red_card", "half_end", "match_end"))
    return {"text": " ".join(sentences), "rule_version": "full-feed-briefing-v1",
            "evidence_event_ids": [e.event_id for e in all_events if e.event_id in evidence]}
