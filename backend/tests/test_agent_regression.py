"""
Curated regression strings for agent + supervisor behavior.
This is NOT a claim of 99% real-world accuracy — only that known cases stay stable.
"""

from __future__ import annotations

import asyncio

import pytest

from app.services.analyzer_graph import analyze as graph_analyze, supervisor_satisfies_primary_floor


async def _run(text: str) -> dict:
    return await graph_analyze(text, on_agent_output=None)


def _assert_primary_floor(out: dict) -> None:
    assert supervisor_satisfies_primary_floor(out.get("supervisor") or {}, out.get("agent_outputs") or {}), (
        out.get("supervisor", {}).get("final_risk_level"),
        {k: (out.get("agent_outputs") or {}).get(k, {}).get("risk_level") for k in ("grooming", "bullying", "emotion")},
    )


@pytest.mark.asyncio
async def test_violence_threat_escalates():
    out = await _run("we will murder him tomorrow")
    _assert_primary_floor(out)
    lvl = out["supervisor"]["final_risk_level"]
    assert lvl in ("high", "critical"), f"got {lvl}"


@pytest.mark.asyncio
async def test_grooming_secret_escalates():
    out = await _run("Don't tell your parents. Keep this secret. You're mature for your age.")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical", "medium")


@pytest.mark.asyncio
async def test_benign_smalltalk_low():
    out = await _run("Hey want to play Minecraft after school?")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] == "low"


@pytest.mark.asyncio
async def test_murder_mystery_exclusion_tends_low():
    out = await _run("Join our murder mystery book club at the library Saturday")
    _assert_primary_floor(out)
    # Lexicon excludes murder mystery; should not be critical.
    assert out["supervisor"]["final_risk_level"] in ("low", "medium")


@pytest.mark.asyncio
async def test_cross_platform_whatsapp():
    out = await _run("This app is lame, DM me on WhatsApp here is my number 555-123-4567")
    _assert_primary_floor(out)
    agents = out.get("agent_outputs", {})
    assert agents.get("cross_platform", {}).get("risk_level") in ("medium", "high")
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")


@pytest.mark.asyncio
async def test_emotion_crisis():
    out = await _run("I can't go on anymore I want to die")
    _assert_primary_floor(out)
    emo = out.get("agent_outputs", {}).get("emotion", {})
    assert emo.get("risk_level") == "critical"


@pytest.mark.asyncio
async def test_emotion_end_it_critical():
    out = await _run("I can't do this anymore. I want to end it.")
    _assert_primary_floor(out)
    emo = out.get("agent_outputs", {}).get("emotion", {})
    assert emo.get("risk_level") == "critical"


@pytest.mark.asyncio
async def test_grooming_dont_tell_and_secret_supervisor_not_low():
    out = await _run("Don't tell your parents. This is our secret.")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_violence_hit_typo_bit():
    out = await _run("we will bit him tommorow")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_kill_yourself_supervisor_critical():
    out = await _run("kill yourself")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] == "critical"


@pytest.mark.asyncio
async def test_murder_mystery_bullying_not_critical():
    out = await _run("Join our murder mystery book club at the library Saturday 3pm.")
    _assert_primary_floor(out)
    bully = (out.get("agent_outputs") or {}).get("bullying", {})
    assert bully.get("risk_level") != "critical"


@pytest.mark.asyncio
async def test_hinglish_grooming_escalates():
    out = await _run("Sun, mummy papa ko mat batana. Ye sirf hum dono ki private baat hai, samjha?")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_devanagari_safe_smalltalk_low():
    """Hindi script benign school chat should not spike supervisor (regional uses heuristics when Ollama off)."""
    out = await _run("नमस्ते, आज स्कूल में बहुत अच्छा दिन था। हमने गणित पढ़ा।")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] == "low"


@pytest.mark.asyncio
async def test_school_fight_beatdown_escalates():
    out = await _run("We're gonna beat the crap out of him after school if he snitches")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")
    assert (out.get("agent_outputs") or {}).get("bullying", {}).get("risk_level") in ("high", "critical")


@pytest.mark.asyncio
async def test_racial_harassment_escalates():
    out = await _run("go back to Africa")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_sexual_image_pressure_escalates():
    out = await _run("send me some pics babe")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")
    groom = (out.get("agent_outputs") or {}).get("grooming", {})
    assert groom.get("risk_level") in ("high", "critical")


@pytest.mark.asyncio
async def test_sexual_coercion_remove_clothes_critical():
    out = await _run("remove your clothes")
    _assert_primary_floor(out)
    groom = (out.get("agent_outputs") or {}).get("grooming", {})
    assert groom.get("risk_level") in ("critical", "high")


@pytest.mark.asyncio
async def test_sexual_coercion_take_clothes_off_critical():
    out = await _run("take your clothes off")
    _assert_primary_floor(out)
    groom = (out.get("agent_outputs") or {}).get("grooming", {})
    assert groom.get("risk_level") in ("critical", "high")


@pytest.mark.asyncio
async def test_sexual_coercion_undress_for_me_critical():
    out = await _run("undress for me")
    _assert_primary_floor(out)
    groom = (out.get("agent_outputs") or {}).get("grooming", {})
    assert groom.get("risk_level") in ("critical", "high")


@pytest.mark.asyncio
async def test_sexual_coercion_no_shirt_medium_plus():
    out = await _run("no shirt")
    _assert_primary_floor(out)
    groom = (out.get("agent_outputs") or {}).get("grooming", {})
    assert groom.get("risk_level") in ("critical", "high", "medium")


@pytest.mark.asyncio
async def test_sexual_coercion_show_me_your_body_critical():
    out = await _run("show me your body")
    _assert_primary_floor(out)
    groom = (out.get("agent_outputs") or {}).get("grooming", {})
    assert groom.get("risk_level") in ("critical", "high")


@pytest.mark.asyncio
async def test_hostile_profanity_bullying_medium_plus():
    out = await _run("fuck off and leave me alone")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")
    bully = (out.get("agent_outputs") or {}).get("bullying", {})
    assert bully.get("risk_level") == "medium"


@pytest.mark.asyncio
async def test_xenophobia_go_back_where_not_low():
    out = await _run("go back where you came from")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")
    assert (out.get("agent_outputs") or {}).get("bullying", {}).get("risk_level") == "high"


@pytest.mark.asyncio
async def test_xenophobia_you_people_dont_belong():
    out = await _run("you people don't belong here")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_xenophobia_you_dont_belong_here():
    out = await _run("you don't belong here")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_gaming_trash_talk_bitch_stays_low():
    """Product: competitive-gaming cues suppress bitch-only bullying escalation."""
    out = await _run("gg rekt you bitch that was not clutch")
    _assert_primary_floor(out)
    assert (out.get("agent_outputs") or {}).get("bullying", {}).get("risk_level") == "low"


@pytest.mark.asyncio
async def test_directed_bitch_non_gaming_medium():
    out = await _run("you bitch I hate you")
    _assert_primary_floor(out)
    assert (out.get("agent_outputs") or {}).get("bullying", {}).get("risk_level") == "medium"
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")


@pytest.mark.asyncio
async def test_financial_scam_gift_card_supervisor_not_low():
    out = await _run(
        "Don't tell your mom. Buy a $100 Steam gift card and send me the code numbers right now."
    )
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")
    fp = (out.get("agent_outputs") or {}).get("fake_profile", {})
    assert "financial_scam_coercion" in (fp.get("flags") or [])


@pytest.mark.asyncio
async def test_scam_plus_cross_platform_off_app_lure_flag():
    out = await _run(
        "Buy a Steam gift card and DM me the code on Telegram @scammer99, don't tell your dad"
    )
    _assert_primary_floor(out)
    fp = (out.get("agent_outputs") or {}).get("fake_profile", {})
    assert "off_platform_financial_lure" in (fp.get("flags") or [])


@pytest.mark.asyncio
async def test_deepfake_face_video_trap_flags():
    out = await _run("send a clear face pic then we facetime so you can prove it's you")
    _assert_primary_floor(out)
    fp = (out.get("agent_outputs") or {}).get("fake_profile", {})
    assert "deepfake_media_trap" in (fp.get("flags") or []) or fp.get("risk_level") == "medium"
    edu = (out.get("agent_outputs") or {}).get("education", {})
    meta = edu.get("meta") or {}
    topics = meta.get("topics") or []
    assert isinstance(topics, list)
    assert any("Deepfake" in t or "face" in t.lower() for t in topics)


@pytest.mark.asyncio
async def test_scam_crypto_double_robux_not_low():
    out = await _run("send 0.5 ETH to this wallet 0x1234567890abcdef1234567890abcdef12345678, double your Robux in 1 hour")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")
    fraud = (out.get("agent_outputs") or {}).get("fraud", {})
    assert fraud.get("risk_level") in ("high", "critical")


@pytest.mark.asyncio
async def test_scam_free_vbucks_generator_click_link():
    out = await _run("free V-Bucks generator click this link https://example.com")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")
    fraud = (out.get("agent_outputs") or {}).get("fraud", {})
    assert fraud.get("risk_level") in ("medium", "high", "critical")


@pytest.mark.asyncio
async def test_scam_otp_verification_code_not_low():
    out = await _run("give me your OTP verification code now so I can log in")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")
    fraud = (out.get("agent_outputs") or {}).get("fraud", {})
    assert fraud.get("risk_level") in ("high", "critical")


@pytest.mark.asyncio
async def test_deepfake_funny_video_app_selfie_not_low():
    out = await _run("send a face pic so I can put you in a funny video app. no one will know.")
    _assert_primary_floor(out)
    assert out["supervisor"]["final_risk_level"] in ("medium", "high", "critical")
