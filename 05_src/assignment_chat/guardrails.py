import re

BLOCKED_TOPICS = {
    "pets": {
        "patterns": [
            r"\b(cat|cats|kitten|kittens|feline|meow)\b",
            r"\b(dog|dogs|puppy|puppies|canine|woof|poodle|labrador)\b",
        ],
        "reply": "I'm a travel assistant, so I'm not able to help with questions about cats or dogs. Can I help you plan a trip instead?",
    },
    "horoscope": {
        "patterns": [
            r"\b(horoscope|horoscopes|zodiac|astrology|astrological)\b",
            r"\b(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)\b",
            r"\b(star sign|birth sign|sun sign|moon sign|rising sign)\b",
        ],
        "reply": "Horoscopes and zodiac signs are outside my expertise! I'm here to help with travel planning — where are you thinking of going?",
    },
    "taylor_swift": {
        "patterns": [
            r"\btaylor swift\b",
            r"\btaylor alison swift\b",
            r"\bswifties?\b",
            r"\bthe eras tour\b",
        ],
        "reply": "That topic is outside what I can help with. I'm your travel planning companion — ask me about destinations, costs, or weather!",
    },
}

INJECTION_PATTERNS = [
    r"ignore (all |previous |your )?(instructions?|prompt|rules?|guidelines?)",
    r"(reveal|show|print|display|tell me|what (is|are)) (your )?(system prompt|instructions?|prompt|rules?|guidelines?|secret)",
    r"(forget|disregard|override) (everything|all|your|previous)",
    r"you are now|pretend (you are|to be)|act as (if )?you (are|have no)",
    r"(new|updated|different) (instructions?|rules?|prompt|persona|role)",
    r"what were you told",
    r"(bypass|break|escape|jailbreak) (your )?(rules?|restrictions?|filter|guardrails?)",
    r"do anything now|dan mode|developer mode",
    r"act as (a |an )?",                      # catches "act as a pirate"
    r"pretend (to be|you are) (a |an )?",     # catches "pretend to be a X"
    r"(be|become|play) (a |an )?\w+ (for me|now|instead)",  # catches "be a pirate for me"
    r"respond (only |from now on )?(as|like) (a |an )?",    # catches "respond as a pirate"
    r"(talk|speak|write|reply) (to me )?(like|as) (a |an )?", # catches "talk like a pirate"
]
 
INJECTION_REPLY = (
    "I can't help with that. I'm here to assist with travel planning — "
    "feel free to ask me about destinations, trip costs, weather, or currency conversion!"
)


def check_guardrails(message: str) -> str | None:
    """
    Check a user message against all guardrails.
    Returns a refusal string if the message is blocked, or None if it's fine.
    """
    lowered = message.lower()
 
    # 1. Check for prompt injection attempts
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return INJECTION_REPLY
 
    # 2. Check for blocked topics
    for topic, config in BLOCKED_TOPICS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, lowered):
                return config["reply"]
 
    return None  # message is clean
 
 
def check_response(response: str) -> str:
    """
    Scan the agent's response for accidental system prompt leakage.
    If detected, replace with a safe fallback.
    """
    leakage_patterns = [
        r"you are a friendly and knowledgeable travel assistant",
        r"today's date is \d{4}-\d{2}-\d{2}",
        r"system prompt",
        r"my instructions (are|say|tell me)",
    ]
    lowered = response.lower()
    for pattern in leakage_patterns:
        if re.search(pattern, lowered):
            return "I'm here to help with your travel plans! What destination are you interested in?"
 
    return response