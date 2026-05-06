from __future__ import annotations



import re

from typing import List



from app.agents.rules import detect_ai_image_lure, detect_grooming_rules, detect_sexual_image_coercion

from app.agents.types import AgentOutput





def _secrecy_manipulation_language(text: str) -> bool:

    """True when secrecy / isolation phrasing is present (do not rely on regex pattern substrings)."""

    t = (text or "").lower()

    if re.search(r"don'?t\s+tell", t) and re.search(r"\b(secret|raaz|private)\b", t):

        return True

    if re.search(r"don'?t\s+tell", t) and re.search(r"\b(just\s+)?between\s+us\b", t):

        return True

    # Hinglish / Romanized Hindi: parental concealment + secrecy wording

    if re.search(r"\b(mat\s+batana|mat\s+batao|mat\s+bata)\b", t) and re.search(

        r"\b(mummy|papa|maa|baap|parents)\b", t

    ) and re.search(r"\b(secret|raaz|private|sirf\s+hum)\b", t):

        return True

    return False





def _grooming_patterns_indicate_image_pressure(patterns: List[str]) -> bool:

    """Matched grooming regexes that imply nudes / pics / disrobing — not used for meet-ups alone."""

    blob = "\n".join(patterns).lower()

    keys = (

        "nudes",

        "naked",

        "pics",

        "pix",

        "selfie",

        "boobs",

        "nipples",

        "undress",

        "strip",

        "shower",

        "send|snap|dm",

        "send (a )",

        "show|trade",

        "dick",

        "pussy",

        "blemme",

        "shirt",

        "clothes",

    )

    return any(k in blob for k in keys)


def _coercion_patterns_strong(patterns: List[str]) -> bool:
    blob = "\n".join(patterns).lower()
    return any(k in blob for k in ("undress", "strip", "remove", "take", "clothes", "shirt", "body"))





async def run(chat_text: str, **_) -> AgentOutput:

    t = chat_text or ""

    co_hit, co_p = detect_sexual_image_coercion(t)

    hit, patterns = detect_grooming_rules(t)
    img_hit, img_p = detect_ai_image_lure(t)



    if not hit and not co_hit and not img_hit:

        return AgentOutput.low("No strong grooming patterns detected.", confidence=0.55)



    flags: List[str] = ["grooming_pattern"]

    if co_hit:

        flags.append("sexual_image_coercion")



    all_patterns = list(dict.fromkeys(list(patterns) + list(co_p) + list(img_p)))



    secrecy = _secrecy_manipulation_language(t) or (hit and any("secret" in p or "don't tell" in p for p in patterns))

    if secrecy:
        if img_hit and not co_hit:
            return AgentOutput(
                "medium",
                0.72,
                "Detected secrecy paired with image solicitation (grooming-adjacent boundary testing).",
                flags + ["nonsexual_image_solicitation"],
                {"matches": all_patterns},
            )
        return AgentOutput(
            "critical",
            0.82,
            "Detected secrecy/manipulation language commonly used in grooming.",
            flags,
            {"matches": all_patterns},
        )



    if co_hit or (hit and _grooming_patterns_indicate_image_pressure(patterns)):
        if co_hit and _coercion_patterns_strong(co_p):
            return AgentOutput(
                "critical",
                0.9,
                "Detected coercive undressing/body request (high-risk grooming/CSEA-adjacent).",
                flags,
                {"matches": all_patterns},
            )

        return AgentOutput(

            "high",

            0.86,

            "Detected pressure for intimate images or sexual boundary-crossing (grooming/CSEA-adjacent).",

            flags,

            {"matches": all_patterns},

        )



    if hit and any("meet" in p for p in patterns):

        return AgentOutput("high", 0.78, "Detected attempted escalation to offline meeting.", flags, {"matches": all_patterns})

    return AgentOutput("high", 0.72, "Detected trust-building / boundary-testing patterns.", flags, {"matches": all_patterns})

