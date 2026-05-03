from __future__ import annotations

import re
from typing import Iterable, List, Tuple


def _any(patterns: Iterable[str], text: str) -> List[str]:
    found: List[str] = []
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            found.append(p)
    return found


def detect_cross_platform(text: str) -> Tuple[bool, List[str]]:
    patterns = [
        r"\bwhatsapp\b",
        r"\btelegram\b",
        r"\bsnap(chat)?\b",
        r"\bdiscord\b",
        r"\binsta(gram)?\b",
        r"\bcall me\b",
        r"\bmove (to|on)\b",
        r"\btext me\b",
        r"\bDM me\b",
        r"\bshare (your )?number\b",
        r"\bphone number\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_grooming_rules(text: str) -> Tuple[bool, List[str]]:
    patterns = [
        r"\bkeep (this|it) (a )?secret\b",
        r"\bdon't tell (your )?(mom|dad|parents|anyone)\b",
        r"\bno one will understand\b",
        r"\bi (really )?trust you\b",
        r"\byou can trust me\b",
        r"\byou're mature for your age\b",
        r"\bwe are special\b",
        r"\bsend (a )?(pic|photo)\b",
        r"\bshow me\b",
        r"\bmeet (me|up)\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_fake_profile_rules(text: str) -> Tuple[bool, List[str]]:
    patterns = [
        r"\bmy camera is broken\b",
        r"\bi can't video call\b",
        r"\bnew account\b",
        r"\bi lost my old account\b",
        r"\bi'm using my friend's phone\b",
        r"\bmy age is\b",
        r"\btrust me\b",
        r"\bi am not lying\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_bullying_keywords(text: str) -> Tuple[bool, List[str]]:
    # Keep this lightweight and editable; model-based toxicity can be plugged in later.
    patterns = [
        r"\bidiot\b",
        r"\bstupid\b",
        r"\bloser\b",
        r"\bkill yourself\b",
        r"\bi hate you\b",
        r"\bgo die\b",
        r"\bno one likes you\b",
        r"\bugly\b",
        r"\bfat\b",
        r"\bworthless\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits

