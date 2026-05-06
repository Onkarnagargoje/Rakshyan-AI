"""
Deterministic high-recall safety lexicon used as a supervisor floor.

This does not replace agents; it prevents catastrophic false negatives when
regex agents miss a phrasing. Exclusion patterns reduce obvious false positives.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.agents.types import RiskLevel

_EXCLUDE = [
    r"murder\s+mystery",
    r"\bcozy\s+murder\b",
    r"mystery\s+(book|novel|game|night|party|weekend|club)",
    r"book\s+club.*\bmurder\b|\bmurder\b.*book\s+club",
    r"true\s+crime",
    r"video\s+game",
    r"\b(lol|lmao|jk|just kidding)\b",
    r"\b(homework|assignment|exam|class)\b.*\b(kill|die)\b",  # "this homework is killing me"
]


def _excluded(text: str) -> bool:
    t = text.lower()
    for pat in _EXCLUDE:
        if re.search(pat, t, flags=re.I):
            return True
    return False


# (name, pattern, severity rank 3=critical)
_CRITICAL_PATTERNS: List[Tuple[str, str]] = [
    ("csam_like_request", r"\b(child|kid|minor)\s+(porn|nude|naked|pics?|pix)\b"),
    ("csam_like_request2", r"\b(send|trade|swap)\s+(cp|illegal)\b"),
    ("sexual_extortion", r"\b(sextort|blackmail|pay\s+or\s+i('ll| will)\s+leak)\b"),
    ("suicide_plan", r"\b(kill|end)\s+(myself|my\s+self)\b"),
    ("suicide_plan2", r"\b(suicide|suicidal)\b.*\b(plan|tonight|today|tomorrow)\b"),
    ("self_harm_act", r"\b(cut|burn)\s+(myself|my\s+wrist|my\s+arm)\b"),
    ("weapon_school", r"\b(gun|knife|weapon)\b.*\b(school|class|campus)\b"),
    ("bomb_threat", r"\b(bomb|explosive)\b.*\b(school|building|place)\b"),
]

_HIGH_PATTERNS: List[Tuple[str, str]] = [
    ("violence_third_party", r"\b(murder|assassinate)\b"),
    ("violence_kill", r"\bkill(ing)?\s+(him|her|them|you|u|someone)\b"),
    ("violence_beat_out", r"\bbeat\s+(the\s+)?(crap|hell|shit|daylights)\s+out\s+of\b"),
    ("violence_beat", r"\bbeat\s+(him|her|them|you)\s+(up|to\s+death)\b"),
    ("hate_deport", r"\bgo\s+back\s+to\s+(africa|mexico|the\s+ghetto)\b"),
    ("xenophobia_go_back", r"\bgo\s+back\s+where\s+you\s+came\s+from\b"),
    ("xenophobia_belong", r"\byou\s+people\s+don'?t\s+belong\b"),
    ("xenophobia_dont_belong_here", r"\byou\s+don'?t\s+belong\s+here\b"),
    ("image_coercion", r"\b(send|snap|dm)\s+(me\s+)?(some\s+)?(nudes?|naked\s+(pics?|photos?)|body\s+pics?)\b"),
    ("strangulation", r"\b(strangle|choke)\s+(him|her|them|you)\b"),
    ("rape_threat", r"\brape\b"),
    ("stalking", r"\b(i('m| am)\s+)?(following|watching)\s+you\b"),
    ("dox_threat", r"\b(dox|doxx|leak\s+your\s+address)\b"),
    ("grooming_age_sex", r"\b(how\s+old\s+are\s+you).*\b(nude|naked|sex)\b"),
    ("isolation", r"\b(cut\s+off|stop\s+talking\s+to)\s+(your\s+)?(friends|family|parents)\b"),
]

_MEDIUM_PATTERNS: List[Tuple[str, str]] = [
    ("distress_vague", r"\b(can't\s+take\s+it\s+anymore|want\s+to\s+die|better\s+off\s+dead)\b"),
    ("drugs_deal", r"\b(pills|meth|coke|cocaine|heroin)\b.*\b(buy|sell|deliver)\b"),
    ("meet_stranger", r"\bmeet\s+(me\s+)?(alone|in\s+private|at\s+(my|the)\s+house)\b"),
    ("hostile_f_off", r"\bfuck\s+off\b"),
    ("scam_giftcard_code", r"\b(gift\s*card|steam\s*card).{0,55}\b(code|pin|cvv)\b"),
    ("deepfake_keyword", r"\b(deepfake|deep\s*fake|nudify\s+ai|face\s*swap)\b"),
    (
        "face_pic_video_lure",
        r"\bface\s+(pic|photo|selfie)\b.{0,90}\b(facetime|video\s*chat|zoom|prove\s+it'?s\s+you|verify\s+it'?s\s+you)\b",
    ),
]


def _first_hits(pairs: List[Tuple[str, str]], text: str) -> List[str]:
    out: List[str] = []
    for name, pat in pairs:
        if re.search(pat, text, flags=re.IGNORECASE):
            out.append(name)
    return out


def lexicon_supervisor_floor(chat_text: str) -> Optional[Tuple[RiskLevel, float, str, List[str]]]:
    """
    If any pattern fires and text is not excluded, return minimum floor for supervisor.
    Returns (risk_level, confidence, reason, flag_names).
    """
    if not (chat_text or "").strip():
        return None
    if _excluded(chat_text):
        return None

    c = _first_hits(_CRITICAL_PATTERNS, chat_text)
    if c:
        return (
            "critical",
            0.92,
            "Global safety lexicon matched high-severity indicators (self-harm, sexual exploitation, weapons, or similar).",
            ["lexicon_" + x for x in c[:6]],
        )
    h = _first_hits(_HIGH_PATTERNS, chat_text)
    if h:
        return (
            "high",
            0.86,
            "Global safety lexicon matched serious harm, sexual violence, or strong grooming-adjacent indicators.",
            ["lexicon_" + x for x in h[:6]],
        )
    m = _first_hits(_MEDIUM_PATTERNS, chat_text)
    if m:
        return (
            "medium",
            0.72,
            "Global safety lexicon matched elevated-risk phrasing worth parent review.",
            ["lexicon_" + x for x in m[:6]],
        )
    return None
