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
        r"\bsignal\b",
        r"\bsnap(chat)?\b",
        r"\bdiscord\b",
        r"\binsta(gram)?\b",
        r"\bfacebook\s*messenger\b",
        r"\bmessenger\b",
        r"\bimessage\b",
        r"\bline\b",
        r"\bwechat\b",
        r"\bviber\b",
        r"\bgoogle\s*chat\b",
        r"\badd\s+me\s+on\b",
        r"\bcall me\b",
        r"\bmove (to|on)\b",
        r"\btext me\b",
        r"\bDM me\b",
        r"\bslide\s+into\s+(my\s+)?dms?\b",
        r"\bshare (your )?number\b",
        r"\bphone number\b",
        r"\b(my|here'?s)\s+\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
        r"\bdownload\s+(this|my)\s+app\b",
        r"\bjoin\s+my\s+(private\s+)?(server|group|channel)\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_grooming_rules(text: str) -> Tuple[bool, List[str]]:
    patterns = [
        r"\bkeep (this|it) (a )?secret\b",
        r"\bdon'?t tell (your )?(mom|dad|parents|anyone|teacher)\b",
        # Romanized Hindi / Hinglish — secrecy toward parents (Ollama still recommended for nuance)
        r"\b(mummy|papa|maa|baap|mummy\s+papa|parents)\s+ko\s+mat\s+(batana|batao|bata|bolna|bol)\b",
        r"\bmat\s+(batana|batao|bata)\b.{0,80}\b(mummy|papa|maa|baap|parents)\b",
        r"\b(chup|chup\s+reh|kisi\s+ko\s+mat\s+batana)\b.{0,100}\b(secret|raaz|private)\b",
        r"\b(sirf|sirf)\s+(hum|hum\s+dono|humari)\b.{0,60}\b(secret|raaz|private\s+baat)\b",
        r"\b(between|just)\s+us\b",
        r"\bno one will understand\b",
        r"\bi (really )?trust you\b",
        r"\byou can trust me\b",
        r"\byou'?re mature for your age\b",
        r"\bwe are special\b",
        r"\bolder (guy|man|friend)\b.*\b(you|u)\b",
        r"\b(young|little)\s+(girl|boy|kid)\b.*\b(secret|pic|photo|nude|meet|alone)\b",
        r"\bsend (a )?(pic|photo|selfie|nude|naked)\b",
        r"\b(send|snap|dm)\s+(me\s+)?(some\s+)?(pics?|pix|photos?|selfies?|nudes?)\b",
        r"\b(send|trade|swap)\s+(me\s+)?(nudes?|naked\s+(pics?|photos?)|body\s+pics?)\b",
        r"\blemme\s+see\s+(you\s+)?(naked|topless|without\s+(your\s+)?(shirt|top|clothes))\b",
        r"\b(take|record)\s+(a\s+)?(nude|naked|shower)\s+(pic|photo|video|selfie)\b",
        r"\b(show|trade)\s+(me\s+)?(your|ur)\b",
        r"\bmeet (me|up)\b",
        r"\b(alone|private)\s+(at|in)\s+(my|the)\s+(house|place|room)\b",
        r"\b(gift|money|allowance)\s+if\s+you\b",
        r"\bpretend\s+(you'?re|to be)\s+older\b",
        r"\bdelete\s+(the\s+)?(chat|messages|history)\b",
        r"\b(turn off|disable)\s+(notifications|screen\s*time)\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_fake_profile_rules(text: str) -> Tuple[bool, List[str]]:
    patterns = [
        r"\bmy camera is broken\b",
        r"\bi can't video call\b",
        r"\b(can'?t|won'?t)\s+(vc|video\s*chat|facetime)\b",
        r"\bnew account\b",
        r"\bi lost my old account\b",
        r"\b(hacked|banned)\s+account\b",
        r"\bi'm using my friend's phone\b",
        r"\bmy age is\b",
        r"\b(i'?m|i am)\s+\d{2}\s*(yo|years\s*old)\b",
        r"\btrust me\b",
        r"\bi am not lying\b",
        r"\bverified\s+badge\s+(is\s+)?(broken|glitched)\b",
        r"\bthis is my (alt|backup)\s+account\b",
        r"\bmodeling\s+opportunity\b",
        r"\b(sponsor|brand)\s+deal\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_violence_threats(text: str) -> Tuple[bool, List[str]]:
    """Third-party or general violence / harm intent (school safety, fights, weapons)."""
    patterns = [
        r"\bmurder\b",
        r"\b(homicide|manslaughter)\b",
        r"\bkill(ing)?\s+(him|her|them|you|u|someone|everybody|everyone)\b",
        r"\b(will|gonna|going to|'ll)\s+(kill|murder|stab|shoot)\b",
        r"\b(will|gonna|going to|'ll)\s+(hit|bit)\s+(him|her|them|you|u)\b",  # "bit" common typo for "hit"
        r"\bbeat\s+(the\s+)?(crap|hell|shit|daylights)\s+out\s+of\s+(him|her|them|you|u)\b",
        r"\b(jump|jumping|jumped)\s+(on\s+)?(him|her|them|you|u)\b.*\b(after\s+)?(school|class|recess|lunch)\b",
        r"\b(after\s+)?(school|class|recess)\b.{0,40}\b(jump|beat|fight)\s+(him|her|them|you|u)\b",
        r"\b(gang\s+up\s+on|jump)\s+(him|her|them|you|u)\b",
        r"\b(we'?re|i'?m)\s+gonna\s+(beat|wreck|destroy)\s+(you|him|her|them)\b",
        r"\b(stab|shoot|strangle|drown)\s+(him|her|them|you|u)\b",
        r"\bbeat\s+(him|her|them|you|u)\s+(to death|up)\b",
        r"\bbring\s+(a )?(gun|knife|weapon)\b",
        r"\b(school\s+)?shooting\b",
        r"\bbomb\s+(the )?(school|place)\b",
        r"\bthreat(en|s)?\s+to\s+(kill|hurt|harm)\b",
        r"\bplan(ned|ning)?\s+to\s+(kill|murder|attack)\b",
        r"\bget\s+rid\s+of\s+(him|her|them)\b",
    ]
    t = (text or "").lower()
    # Standalone "murder" hits "murder mystery" / book-club phrasing — exclude that context.
    if re.search(
        r"murder\s+mystery|mystery\s+(book|novel|game|night|party|weekend|club)|"
        r"book\s+club.*\bmurder\b|\bmurder\b.*book\s+club|\bcozy\s+murder\b|\bmurder\s+party\b",
        t,
    ):
        patterns = [p for p in patterns if p != r"\bmurder\b"]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_hostile_profanity(text: str) -> Tuple[bool, List[str]]:
    """Strong dismissive profanity — product policy: at least medium bullying signal."""
    patterns = [
        r"\bf+u+c+k+\s+off\b",
        r"\bf\s*u\s*c\s*k\s+off\b",
        r"\bfuck\s+off\b",
        r"\bfuck\s+you\b",
        r"\bf+u+c+k+\s+you\b",
        r"\b(gtfo|stfu)\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def _gaming_trash_talk_context(text: str) -> bool:
    """
    Heuristic for competitive-game banter. Used to suppress bitch-only bullying escalation
    (product: gaming trash talk + 'bitch' stays low; school-directed slurs stay medium).
    """
    t = (text or "").lower()
    cues = (
        " gg",
        "gg ",
        "ggez",
        "rekt",
        "noob",
        " tryhard",
        "tryhard",
        "clutch",
        "ranked",
        "valorant",
        "fortnite",
        "roblox",
        "minecraft",
        "league",
        "overwatch",
        " warzone",
        "apex",
        "sweaty lobby",
        "respawn",
        " match mvp",
        "round mvp",
        " ping ms",
        "lag spike",
    )
    hits = sum(1 for c in cues if c in t)
    return hits >= 2 or any(x in t for x in ("valorant", "fortnite", "ranked match", "ranked game"))


def detect_directed_bitch_insult(text: str) -> Tuple[bool, List[str]]:
    """
    Directed gendered “bitch” / insult patterns → **medium** bullying when not gaming banter.

    Product policy: **gaming trash talk + “bitch”** (gg/rekt/ranked/noob/clutch cues) stays **low**
    to reduce noisy alerts on competitive voice/chat. School-directed slurs stay **medium**.
    """
    if not re.search(r"\bbitch(es)?\b", text or "", flags=re.IGNORECASE):
        return False, []
    if _gaming_trash_talk_context(text):
        return False, []
    patterns = [
        r"\b(you|u|ya)\s+bitch\b",
        r"\bbitch\b.{0,16}\b(you|u)\b",
        r"\b(stupid|dumb|ugly|fucking|fuckin)\s+bitch\b",
        r"\bbitch\s+ass\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_hate_harassment(text: str) -> Tuple[bool, List[str], str]:
    """
    Racial / identity-based hate and dehumanization.

    Tiering (product): explicit deportation to a place / slurs / Nazi → **critical**.
    Xenophobic “othering” without naming a country (“go back where you came from”,
    “you don’t belong here”, “get out of our country”) → **high** so they are not all-low.
    """
    critical_patterns = [
        r"\bgo\s+back\s+to\s+(africa|mexico|the\s+ghetto)\b",
        r"\b(heil\s+hitler|sieg\s+heil|1488)\b",
        r"\b(k[i1]ll\s+all\s+the\s+)(jews|muslims|blacks|whites|gays|immigrants)\b",
        r"\b(n[i1]g{2,}[ae](s|z|ah|er)?|f[a4]gg[o0]t(s)?|ch[i1]nk|sp[i1]c|k[i1]ke|gook|towelhead)\b",
        r"\b(porch\s+monkey|coon)\b",
        r"\b(you\s+)?(dirty\s+)?(jew|muslim)\s+(rat|dog|pig)\b",
    ]
    high_patterns = [
        r"\bgo\s+back\s+where\s+you\s+came\s+from\b",
        r"\bgo\s+back\s+to\s+where\s+you\s+came\s+from\b",
        r"\bgo\s+back\s+to\s+your\s+country\b",
        r"\bgo\s+back\s+where\s+you\s+belong\b",
        r"\byou\s+people\s+don'?t\s+belong\b",
        r"\b(your\s+kind|people\s+like\s+you)\s+don'?t\s+belong\s+(here|in\s+this\s+(country|school|town))\b",
        r"\byou\s+don'?t\s+belong\s+here\b",
        r"\byou\s+don'?t\s+belong\s+in\s+this\s+(school|country|town|city)\b",
        r"\bget\s+out\s+of\s+our\s+(country|school|town|city)\b",
        r"\b(not\s+welcome\s+here|you\s+are\s+not\s+welcome\s+here)\b",
        r"\b(hate\s+all\s+the\s+)(jews|muslims|immigrants|gays|trans(\s+people)?|black\s+people|white\s+people)\b",
        r"\b(you\s+people\s+are\s+all\s+)(criminals|animals|rapists|terrorists)\b",
        r"\b(r[e3]t[a@]rd(s|ed)?|spaz(z)?)\b",  # ableist slurs — common in school harassment
        r"\b(dyke|tr[a4]nn(y|ies))\b",  # anti-LGBTQ slurs
    ]
    c = _any(critical_patterns, text)
    if c:
        return True, c, "critical"
    h = _any(high_patterns, text)
    if h:
        return True, h, "high"
    return False, [], ""


def detect_sexual_image_coercion(text: str) -> Tuple[bool, List[str]]:
    """Image / nude pressure without relying on full grooming trust-building context."""
    patterns = [
        r"\b(send|snap|dm)\s+(me\s+)?(some\s+)?(nudes?|naked\s+(pics?|photos?)|body\s+pics?)\b",
        r"\b(send|show)\s+(me\s+)?(your\s+)?(boobs?|dick|pussy|nipples?)\b",
        r"\b(show|send)\s+(me\s+)?(your\s+)?(body|naked\s+body)\b",
        r"\bshow\s+(me\s+)?(your\s+)?body\b",
        r"\b(take|remove)\s+(your\s+)?(shirt|top|bra|pants|clothes|clothing)\s+off\b",
        r"\b(take|remove)\s+off\s+(your\s+)?(shirt|top|bra|pants|clothes|clothing)\b",
        r"\bremove\s+(your\s+)?(clothes|clothing)\b",
        r"\btake\s+off\s+(your\s+)?(clothes|clothing)\b",
        r"\btake\s+(your\s+)?(shirt|top|bra|pants)\s+off\b",
        r"\b(undress|strip)\s+(for\s+me|on\s+camera|on\s+video)\b",
        r"\b(undress|strip)\b.{0,20}\b(for\s+me|now|please)\b",
        r"\b(undress|strip)\b",
        r"\b(no\s+)?(shirt|top)\b",
        r"\b(no\s+)?clothes\b",
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


def detect_financial_scam_coercion(text: str) -> Tuple[bool, List[str]]:
    """Gift-card / wire / crypto pressure and parent-secret + money combos (child-targeted scams)."""
    patterns = [
        r"\b(send|buy|get|need)\s+(me\s+)?(\$\s?)?\d*\.?\d*\s*(dollars?)?.*\b(gift\s*card|steam\s*card|itunes|google\s*play|robux|vbucks|xbox\s*card)\b",
        r"\b(gift\s*card|steam\s*card|itunes\s*card).{0,55}\b(code|pin|numbers?|scratch\s+off)\b",
        r"\b(western\s+union|wire\s+transfer|moneygram)\b.{0,40}\b(send|pay|transfer)\b",
        r"\b(send|transfer)\s+(bitcoin|btc|crypto|usdt|ethereum)\b",
        r"\b(your|my|mom'?s|dad'?s|parents?)\s+(credit|debit)\s+card\b.{0,45}\b(number|pin|cvv|cvc|security\s*code)\b",
        r"\b(don'?t\s+tell).{0,50}\b(parent|mom|dad).{0,70}\b(money|pay|gift\s*card|card\s*number)\b",
        r"\b(irs|police|fbi|government)\b.{0,40}\b(pay|fine|gift\s*card|bitcoin|settle)\b",
        r"\b(pay\s+me|send\s+money)\s+or\s+i\s*('ll|will)\b",
        r"\b(victim|compensation)\s+fee\b.{0,30}\b(pay|send|wire)\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_scam_fraud(text: str) -> Tuple[bool, List[str], str]:
    """
    Scam / fraud targeting kids (robux/vbucks, nitro, trades, OTP, wallet scams).
    Returns (hit, patterns, tier) where tier is 'high' or 'medium'.
    """
    high_patterns = [
        r"\b0x[a-f0-9]{40}\b",  # Ethereum address
        r"\b(send|transfer)\s+\d+(\.\d+)?\s*(eth|btc|bitcoin|crypto|usdt)\b",
        r"\b(verification|verify|otp|one[-\s]?time\s+pass(code|word)|2fa|auth(enticator)?)\b.{0,40}\b(code|pin)\b",
        r"\b(send|give|share)\s+(me\s+)?(your\s+)?(otp|verification\s+code|2fa\s+code|auth\s+code)\b",
        r"\b(double|2x)\s+(your\s+)?(robux|v-?bucks|money|coins?)\b",
        r"\b(send|deposit)\b.{0,40}\b(and\s+)?(i('ll| will)\s+)?(double|2x)\b",
        r"\b(cashapp|cash\s*app)\b.{0,30}\b(send|pay)\b",
    ]
    medium_patterns = [
        r"\bfree\s+(robux|v-?bucks|nitro)\b",
        r"\b(robux|v-?bucks)\s+generator\b",
        r"\bdiscord\s+nitro\b.{0,40}\bfree\b",
        r"\bsteam\b.{0,40}\b(trade|trade\s+offer|skins?)\b.{0,60}\b(link|click)\b",
        r"\b(account\s+recovery|password\s+reset|reset\s+your\s+password)\b.{0,80}\b(link|click)\b",
        r"\b(login|sign\s+in)\b.{0,50}\b(link|click)\b",
        r"\bclick\b.{0,25}\b(link|url)\b",
        r"https?://",
    ]
    t = (text or "").lower()
    h = _any(high_patterns, t)
    if h:
        return True, h, "high"
    m = _any(medium_patterns, t)
    if m:
        return True, m, "medium"
    return False, [], ""


def detect_ai_image_lure(text: str) -> Tuple[bool, List[str]]:
    """
    Non-sexual image solicitation + AI edit/deepfake intent.
    This is not itself 'grooming' unless paired with secrecy/isolation patterns.
    """
    patterns = [
        r"\b(send|share|dm)\s+(me\s+)?(a\s+)?(selfie|face\s+pic|face\s+photo|photo|pic|picture)\b",
        r"\b(send|share)\s+(me\s+)?(your\s+)?(selfie|photo|pic|picture)\b",
        r"\b(i('ll| will)\s+)?(edit|put|add)\s+you\s+(into|in)\s+(a\s+)?(video|clip)\b",
        r"\b(put|add)\s+your\s+face\s+(into|in|on)\b.{0,30}\b(video|app|filter)\b",
        r"\b(ai\s+)?(face\s*swap|deepfake|faceswap)\b",
        r"\b(train|training)\s+(my\s+)?(model|ai)\b.{0,40}\b(on|with)\b.{0,20}\b(your\s+)?(photos?|pics?|selfies?)\b",
        r"\b(for\s+my\s+)?(school\s+project|project)\b.{0,60}\b(send|share)\b.{0,20}\b(selfie|photo|pic)\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits


def detect_deepfake_media_trap(text: str) -> Tuple[bool, List[str]]:
    """Deepfake / face-for-video coercion often used for sextortion or catfish escalation."""
    patterns = [
        r"\bdeep\s*fake\b",
        r"\bdeepfake\b",
        r"\bface\s*swap\b",
        r"\bfaceswap\b",
        r"\b(nudify|undress)\s*(ai|app|bot|site|tool)\b",
        r"\b(put|stick|shop|morph)\s+your\s+face\s+(on|into|in)\b",
        r"\b(send|take|snap)\s+(a\s+)?(clear\s+)?face\s+(pic|photo|selfie)\b.{0,80}\b(video|facetime|zoom|verify|prove\s+it'?s\s+you)\b",
        r"\b(clear\s+)?face\s+(pic|photo|selfie)\b.{0,80}\b(facetime|video\s*chat|zoom|prove\s+it'?s\s+you|verify\s+it'?s\s+you)\b",
        r"\b(video\s*chat|facetime|zoom\s+call|google\s+meet)\b.{0,60}\b(point\s+(the\s+)?camera|show\s+your\s+face|full\s+face|turn\s+on\s+camera)\b",
        r"\b(i('ll| will)\s+)?(edit|put|add)\s+you\s+(into|in)\s+(a\s+)?(video|clip)\b",
    ]
    hits = _any(patterns, text)
    return (len(hits) > 0), hits

