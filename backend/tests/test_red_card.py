import pytest
from fastapi.testclient import TestClient
from app import matchday, security, main, story_writer, recap_quality
from app.models import MatchEvent, CatchUpRequest

HEADERS = {"X-MatchOS-Client": "replay"}


def test_red_card_variant_profiles_and_active_ten_men():
    for profile in matchday.PROFILES:
        cfg = matchday.versioned_profile(profile, 3)
        assert cfg.get("red_card") is not None
        rc = cfg["red_card"]
        assert rc["team"] in ("home", "away")
        assert isinstance(rc["second"], int)
        player_slot = rc.get("player") or rc.get("player_slot")
        assert isinstance(player_slot, int)

        feed = matchday.library_fixture(profile, f"test-rc-{profile['role']}", variant=3)
        card_events = [e for e in feed if e["type"] == "red_card"]
        assert len(card_events) == 1
        card = card_events[0]
        assert card["match_second"] == rc["second"]
        assert card["team_id"] == rc["team"]
        assert card["player_id"] == f"{rc['team']}-{player_slot}"

        # Ensure the carded player never appears in any subsequent action
        card_seq = card["sequence"]
        for event in feed:
            if event["sequence"] > card_seq:
                assert event.get("player_id") != card["player_id"]
                assert event.get("recipient_player_id") != card["player_id"]


def test_red_card_pulse_and_watch_reason():
    # Featured variant 3 has Manchester City (away) red card at 3300
    profile = next(p for p in matchday.PROFILES if p["role"] == "featured")
    feed = [MatchEvent(**raw) for raw in matchday.library_fixture(profile, "m-feat-rc", variant=3)]

    # Before the card at 3270
    p_before = matchday.pulse(feed, 3270)
    assert p_before["red_cards"] == {"home": 0, "away": 0}
    assert p_before["components"]["recent_red_card"] == 0

    # At the card second 3300
    p_at = matchday.pulse(feed, 3300)
    assert p_at["red_cards"] == {"home": 0, "away": 1}
    assert p_at["components"]["recent_red_card"] == 35
    assert p_at["eligible"] is True
    assert p_at["why_now"] is not None
    assert p_at["why_now"]["trigger"] == "red_card"
    assert "down to 10 men" in p_at["why_now"]["headline"]
    assert "sent off" in p_at["why_now"]["headline"]
    assert "red card" in p_at["why_now"]["text"]
    assert p_at["why_now"]["card_event_id"] is not None
    assert p_at["why_now"]["card_event_id"] in p_at["why_now"]["evidence_event_ids"]

    # 150 seconds after card (within 180s)
    p_recent = matchday.pulse(feed, 3450)
    assert p_recent["components"]["recent_red_card"] == 35
    assert p_recent["why_now"]["trigger"] == "red_card"

    # 210 seconds after card (past 180s window)
    p_later = matchday.pulse(feed, 3510)
    assert p_later["components"]["recent_red_card"] == 0
    assert p_later["red_cards"] == {"home": 0, "away": 1}


def test_red_card_triggers_immediate_notification_in_matchday():
    with TestClient(main.app, headers=HEADERS) as c:
        c.post("/api/session", json={}).raise_for_status()
        # Using a matchday_id containing 'red-card' selects variant 3 for all fixtures
        view = c.post("/api/matchdays/start", json={"matchday_id": "day-red-card-test"}).json()
        assert view["matchday_id"] == "day-red-card-test"
        # Verify all matches selected variant 4 (1-based variant_id = 4, index 3)
        assert all(m["variant_id"] == 4 for m in view["matches"])

        # Comeback match has Crystal Palace red card at second 2100 (tick 70)
        # Advance tick to 69 (second 2070)
        for tick in range(1, 70):
            view = c.post("/api/matchdays/day-red-card-test/tick", json={"tick": tick}).json()
        assert view["clock_second"] == 2070

        # Now tick to 70 (second 2100)
        view = c.post("/api/matchdays/day-red-card-test/tick", json={"tick": 70}).json()
        assert view["clock_second"] == 2100
        assert view["recommendation"] is not None
        assert view["recommendation"]["role"] == "comeback"
        assert view["notification"] is not None
        assert "down to 10 men" in view["notification"]["title"]
        assert "Crystal Palace" in view["notification"]["title"]
        assert view["notification"]["match_id"].endswith("-comeback")

        # Notification is active and retained across ticks during the 180s discovery window
        # Tick 70 (2100s) -> expires_at_second is 2280 (Tick 76)
        assert view["notification"]["expires_at_second"] == 2280

        # Tick 71 (2130s, +30s): notification persists across ticks during the window
        view71 = c.post("/api/matchdays/day-red-card-test/tick", json={"tick": 71}).json()
        assert view71["notification"] is not None
        assert view71["notification"]["id"] == view["notification"]["id"]
        assert view71["notification"]["match_id"].endswith("-comeback")

        # Tick 75 (2250s, +150s): notification still active
        for tick in range(72, 76):
            view_active = c.post("/api/matchdays/day-red-card-test/tick", json={"tick": tick}).json()
        assert view_active["notification"] is not None

        # Tick 76 (2280s, exactly 180s after card): discovery window expires, notification cleared
        view_expired = c.post("/api/matchdays/day-red-card-test/tick", json={"tick": 76}).json()
        assert view_expired["clock_second"] == 2280
        assert view_expired["notification"] is None


def test_red_card_notification_detected_when_not_highest_ranked(monkeypatch):
    # Verify that a red card anywhere is dispatched even if another match is the recommendation leader
    with TestClient(main.app, headers=HEADERS) as c:
        c.post("/api/session", json={}).raise_for_status()
        view = c.post("/api/matchdays/start", json={"matchday_id": "day-red-card-rank-test"}).json()

        # Monkeypatch rank() so that the featured match is ALWAYS the recommendation leader
        featured_mid = next(m["match_id"] for m in view["matches"] if m["role"] == "featured")
        original_rank = matchday.rank

        def forced_featured_leader(entries):
            ranked = original_rank(entries)
            # Put featured match first regardless of ratings
            return sorted(entries, key=lambda e: (0 if e["match_id"] == featured_mid else 1))

        monkeypatch.setattr(matchday, "rank", forced_featured_leader)

        # Advance to tick 70 (second 2100) where Comeback gets a red card
        for tick in range(1, 71):
            view = c.post("/api/matchdays/day-red-card-rank-test/tick", json={"tick": tick}).json()

        # Even though featured match is the forced leader, the red card notification is for Comeback!
        assert view["recommendation"]["match_id"] == featured_mid
        assert view["notification"] is not None
        assert view["notification"]["match_id"].endswith("-comeback")
        assert "Crystal Palace" in view["notification"]["title"]
        assert "down to 10 men" in view["notification"]["title"]


@pytest.mark.parametrize("profile", matchday.PROFILES, ids=lambda p: p["role"])
@pytest.mark.parametrize("variant", range(4))
def test_catch_me_up_across_all_12_match_versions(profile, variant):
    role = profile["role"]
    events = [MatchEvent(**e) for e in matchday.library_fixture(profile, f"cmu-{role}", variant)]
    variant_cfg = matchday.versioned_profile(profile, variant)
    has_card = variant_cfg.get("red_card") is not None
    card_cfg = variant_cfg.get("red_card") if has_card else None

    for now in (1200, 2700, 3600, 4530, 5580):
        observed = [e for e in events if e.match_second <= now]
        res = main.build_catch_up(observed, CatchUpRequest())
        fan = res["fan_briefing"]
        assert fan is not None
        recap_en = fan["spoken_recap"]["en"]
        recap_es = fan["spoken_recap"]["es"]
        assert len(recap_en) > 0 and len(recap_es) > 0

        # Check evidence event IDs are strictly bounded to observed events
        assert set(fan["evidence_event_ids"]) <= {e.event_id for e in observed}

        card_happened = has_card and now >= card_cfg["second"]
        if card_happened:
            card_event = next(e for e in observed if e.type == "red_card")
            player_name = card_event.player_name or card_event.player_id
            team_name = card_event.team_name or card_event.team_id
            clock_str = f"{card_cfg['second'] // 60}:{card_cfg['second'] % 60:02d}"

            # English recap verification
            assert player_name in recap_en
            assert team_name in recap_en
            assert ("10 men" in recap_en or "ten men" in recap_en)
            assert ("sent off" in recap_en or "red card" in recap_en)
            assert clock_str in recap_en

            # Spanish recap verification
            assert player_name in recap_es
            assert team_name in recap_es
            assert ("10 hombres" in recap_es or "10 jugadores" in recap_es)
            assert ("expulsión" in recap_es or "tarjeta roja" in recap_es)
            assert clock_str in recap_es

            # Evidence event ID included in fan briefing evidence
            assert card_event.event_id in fan["evidence_event_ids"]

            # Score story section text also reports the sending off
            score_section = next(s for s in fan["sections"] if s["title"] == "The score story")
            assert (player_name in score_section["text"] or team_name in score_section["text"])
            assert card_event.event_id in score_section["evidence_event_ids"]
        else:
            # Before the card occurs or on non-red-card versions, no sending off is described
            assert "red card" not in recap_en.lower()
            assert "tarjeta roja" not in recap_es.lower()


def test_full_feed_briefing_explains_sending_off_accurately():
    from app.briefing import full_feed_briefing
    for profile in matchday.PROFILES:
        feed = [MatchEvent(**e) for e in matchday.library_fixture(profile, f"ff-{profile['role']}", 3)]
        card_event = next(e for e in feed if e.type == "red_card")
        # Snapshot including the sending off
        obs = [e for e in feed if e.match_second <= card_event.match_second]
        new_events = [e for e in obs if e.match_second >= card_event.match_second]
        briefing = full_feed_briefing(obs, new_events, "advanced")
        assert briefing is not None
        assert "sent off with a red card" in briefing["text"]
        assert card_event.player_name in briefing["text"]
        assert card_event.event_id in briefing["evidence_event_ids"]



def test_red_card_included_in_ai_evidence_packet():
    for profile in matchday.PROFILES:
        feed = [MatchEvent(**e) for e in matchday.library_fixture(profile, f"pkt-{profile['role']}", 3)]
        card_event = next(e for e in feed if e.type == "red_card")
        obs = [e for e in feed if e.match_second <= card_event.match_second]
        fan = main.build_catch_up(obs, CatchUpRequest())["fan_briefing"]
        packet = story_writer.evidence_packet(fan, obs)

        card_fact_id = f"red_card:{card_event.event_id}"
        assert card_fact_id in packet["required_fact_ids"]

        card_fact = next((f for f in packet["facts"] if f["fact_id"] == card_fact_id), None)
        assert card_fact is not None
        assert card_fact["data"]["kind"] == "red_card"
        assert card_fact["data"]["player_name"] == card_event.player_name
        assert card_fact["data"]["clock"] == f"{card_event.match_second // 60}:{card_event.match_second % 60:02d}"
        assert card_fact["evidence_event_ids"] == [card_event.event_id]


@pytest.mark.parametrize("profile", matchday.PROFILES, ids=lambda p: p["role"])
def test_ai_recap_validation_accepts_valid_red_card_and_rejects_omission(profile):
    feed = [MatchEvent(**e) for e in matchday.library_fixture(profile, f"ai-eval-{profile['role']}", 3) if e["match_second"] <= 5580]
    res = main.build_catch_up(feed, CatchUpRequest())
    fan = res["fan_briefing"]
    packet = story_writer.evidence_packet(fan, feed)
    card_event = next(e for e in feed if e.type == "red_card")
    card_id = f"red_card:{card_event.event_id}"
    assert card_id in packet["required_fact_ids"]

    valid_en = fan["spoken_recap"]["en"]
    valid_es = fan["spoken_recap"]["es"]

    # 1. Valid draft containing the red card passes validation cleanly
    valid_draft = {
        "en": valid_en,
        "es": valid_es,
        "fact_ids": packet["required_fact_ids"],
    }
    assert story_writer.compose_draft(valid_draft, packet) is valid_draft

    # 2. Draft omitting the red card from English prose is rejected
    omitted_en_sentences = [s for s in valid_en.split('. ') if card_event.player_name not in s]
    omitted_en = '. '.join(omitted_en_sentences)
    omitted_en_draft = {
        "en": omitted_en,
        "es": valid_es,
        "fact_ids": packet["required_fact_ids"],
    }
    with pytest.raises(recap_quality.RecapQualityError) as exc_en:
        story_writer.validate_draft(omitted_en_draft, packet)
    assert exc_en.value.details["language"] == "en"
    assert any(issue["code"] == "missing_selected_red_card" for issue in exc_en.value.details.get("issues", []))

    # 3. Draft omitting the red card from Spanish prose is rejected
    omitted_es_sentences = [s for s in valid_es.split('. ') if card_event.player_name not in s]
    omitted_es = '. '.join(omitted_es_sentences)
    omitted_es_draft = {
        "en": valid_en,
        "es": omitted_es,
        "fact_ids": packet["required_fact_ids"],
    }
    with pytest.raises(recap_quality.RecapQualityError) as exc_es:
        story_writer.validate_draft(omitted_es_draft, packet)
    assert exc_es.value.details["language"] == "es"
    assert any(issue["code"] == "missing_selected_red_card" for issue in exc_es.value.details.get("issues", []))

    # 4. Draft omitting the red card fact ID is rejected
    omitted_id_draft = {
        "en": valid_en,
        "es": valid_es,
        "fact_ids": [fid for fid in packet["required_fact_ids"] if fid != card_id],
    }
    with pytest.raises(ValueError, match="Unknown or omitted facts"):
        story_writer.validate_draft(omitted_id_draft, packet)


def test_direct_validate_selected_claims_rejects_omitted_red_card():
    profile = next(p for p in matchday.PROFILES if p["role"] == "featured")
    feed = [MatchEvent(**e) for e in matchday.library_fixture(profile, "claim-test", 3) if e["match_second"] <= 5580]
    res = main.build_catch_up(feed, CatchUpRequest())
    fan = res["fan_briefing"]
    packet = story_writer.evidence_packet(fan, feed)
    card_event = next(e for e in feed if e.type == "red_card")

    valid_en = fan["spoken_recap"]["en"]
    omitted_en = '. '.join(s for s in valid_en.split('. ') if card_event.player_name not in s)

    # Valid claims pass
    recap_quality.validate_selected_claims(valid_en, packet)

    # Omitted claim raises RecapQualityError with code missing_selected_red_card
    with pytest.raises(recap_quality.RecapQualityError, match="missing_selected_red_card"):
        recap_quality.validate_selected_claims(omitted_en, packet)
