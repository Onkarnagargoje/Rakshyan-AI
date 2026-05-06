from __future__ import annotations



from app.agents.rules import (

    detect_bullying_keywords,

    detect_directed_bitch_insult,

    detect_hate_harassment,

    detect_hostile_profanity,

    detect_violence_threats,

)

from app.agents.types import AgentOutput





async def run(chat_text: str, **_) -> AgentOutput:

    v_hit, v_patterns = detect_violence_threats(chat_text)

    if v_hit:

        return AgentOutput(

            "critical",

            0.88,

            "Detected credible violence or harm-to-others language (threats, weapons, murder/kill phrasing).",

            ["violence_threat", "harm_to_others"],

            {"matches": v_patterns},

        )



    hate_hit, hate_patterns, hate_tier = detect_hate_harassment(chat_text)

    if hate_hit:

        level = "critical" if hate_tier == "critical" else "high"

        conf = 0.89 if hate_tier == "critical" else 0.85

        return AgentOutput(

            level,

            conf,

            "Detected racial, identity-based, or dehumanizing harassment language.",

            ["hate_harassment", "bullying_language"],

            {"matches": hate_patterns, "hate_tier": hate_tier},

        )



    prof_hit, prof_patterns = detect_hostile_profanity(chat_text)

    if prof_hit:

        return AgentOutput(

            "medium",

            0.72,

            "Detected strong hostile or dismissive profanity (toxicity / verbal aggression).",

            ["hostile_profanity", "bullying_language"],

            {"matches": prof_patterns},

        )



    # Product: directed "bitch" / gendered slurs → medium in non-gaming chat; competitive-gaming

    # trash talk (gg/rekt/ranked/etc.) suppresses bitch-only escalation to avoid noisy parent alerts.

    bitch_hit, bitch_patterns = detect_directed_bitch_insult(chat_text)

    if bitch_hit:

        return AgentOutput(

            "medium",

            0.68,

            "Detected directed gendered insult / slur (non-gaming context).",

            ["gendered_slur", "bullying_language"],

            {"matches": bitch_patterns},

        )



    hit, patterns = detect_bullying_keywords(chat_text)

    if not hit:

        return AgentOutput.low("No strong bullying or violence-threat signals detected.", confidence=0.6)



    flags = ["bullying_language"]

    if any("kill yourself" in p for p in patterns):

        return AgentOutput("critical", 0.85, "Detected self-harm encouragement / severe bullying language.", flags, {"matches": patterns})

    return AgentOutput("high", 0.78, "Detected abusive / insulting language patterns.", flags, {"matches": patterns})

