import os
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# =========================
# Demo data
# =========================
KINGSTON_DATA: Dict[str, Any] = {
    "zones": {
        "blue_zone":   {"day": "Thursday",  "week1": ["blue_bin"], "week2": ["grey_bin"]},
        "red_zone":    {"day": "Friday",    "week1": ["blue_bin"], "week2": ["grey_bin"]},
        "orange_zone": {"day": "Monday",    "week1": ["blue_bin"], "week2": ["grey_bin"]},
        "purple_zone": {"day": "Wednesday", "week1": ["blue_bin"], "week2": ["grey_bin"]},
        "green_zone":  {"day": "Tuesday",   "week1": ["blue_bin"], "week2": ["grey_bin"]},
    },

    # Reference date for week parity (Week 1). Adjust to align with Kingston’s real calendar.
    "referenceDate": "2026-01-22",

    # Street keywords -> zone (lowercase keys)
    "streets": {
        "princess": "blue_zone",
        "gardiners": "blue_zone",
        "chelsea": "orange_zone",
        "montgomery": "orange_zone",
        "evergreen": "red_zone",
        "first": "red_zone",
        "boxwood": "purple_zone",
        "napier": "purple_zone",
        "ordnance": "green_zone",
        "queen": "green_zone"
    },

    "bin_info": {
        "garbage": "Regular household waste in garbage bags.",
        "green_bin": "Food scraps, coffee grounds, tea bags, meat/bones, soiled paper (organics).",
        "blue_bin": "Containers (glass bottles/jars, metal cans/foil).",
        "grey_bin": "Paper/cardboard and flexible plastic film/bags (demo).",
    }
}

WEEKDAY_TO_INT = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}

# =========================
# Special item rules (small “waste wizard” MVP)
# =========================
SPECIAL_ITEMS = [
    {
        "keywords": ["battery", "batteries", "aa", "aaa", "9v", "lithium", "lithium-ion", "rechargeable"],
        "answer": (
            "<b>Batteries:</b> Do <b>not</b> put in garbage or recycling.<br>"
            "Bring to the Household Hazardous Waste (HHW) depot at <b>196 Lappan’s Lane</b> "
            "(open <b>April–November</b>, <b>Thurs 8–5</b> and <b>Sat 8–4</b>)."
        )
    },
    {
        "keywords": ["paint", "solvent", "propane", "fuel", "gasoline", "antifreeze", "pesticide",
                     "household cleaner", "aerosol", "mercury", "fire extinguisher", "chemical"],
        "answer": (
            "<b>Household hazardous waste:</b> Do <b>not</b> put in garbage/recycling.<br>"
            "Bring to the HHW depot at <b>196 Lappan’s Lane</b> (Apr–Nov Thu/Sat)."
        )
    },
    {
        "keywords": ["needle", "needles", "sharps", "syringe", "injector"],
        "answer": (
            "<b>Needles/sharps:</b> Do <b>not</b> put in garbage or recycling.<br>"
            "Use an approved sharps container and return through a participating pharmacy program. "
            "If you find a needle in public, don’t touch it—contact public health guidance."
        )
    },
    {
        "keywords": ["medication", "medicine", "pills", "prescription", "drug"],
        "answer": (
            "<b>Medications:</b> Do <b>not</b> flush and do <b>not</b> put in garbage/recycling.<br>"
            "Return unused/expired meds to a participating pharmacy (medication return program)."
        )
    },
    {
        "keywords": ["tv", "television", "laptop", "computer", "phone", "cellphone", "tablet",
                     "electronics", "printer", "monitor", "keyboard", "mouse"],
        "answer": (
            "<b>Electronics (e-waste):</b> Do <b>not</b> put in garbage or recycling.<br>"
            "Use an approved e-waste drop-off location."
        )
    },
    {
        "keywords": ["textile", "textiles", "clothes", "clothing", "shirt", "pants", "shoes", "fabric"],
        "answer": (
            "<b>Textiles/clothing:</b> Best handled via donation or textile collection bins.<br>"
            "If heavily soiled/wet/moldy, it may need to go to garbage."
        )
    },
    {
        "keywords": ["pizza box", "pizza boxes"],
        "answer": (
            "<b>Pizza boxes:</b><br>"
            "• If <b>greasy/food-soiled</b>: put in the <b>green bin (organics)</b>.<br>"
            "• If <b>clean cardboard</b>: put in the <b>grey bin</b> (paper/cardboard)."
        )
    },
]

# =========================
# Helpers
# =========================
def get_week_number(d: date) -> int:
    """Return 1 or 2 based on parity from referenceDate."""
    ref = date.fromisoformat(KINGSTON_DATA["referenceDate"])
    diff_days = (d - ref).days
    diff_weeks = diff_days // 7
    return 1 if (diff_weeks % 2 == 0) else 2

def next_date_for_weekday(target_weekday: int, from_date: date) -> date:
    """Next occurrence (always in the future)."""
    days_ahead = (target_weekday - from_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)

def format_date(d: date) -> str:
    return d.strftime("%A, %B %d").replace(" 0", " ")

def find_street_key(message: str) -> Optional[str]:
    m = message.lower()
    for street_key in KINGSTON_DATA["streets"].keys():
        if street_key.lower() in m:
            return street_key
    return None

def is_pickup_question(message: str) -> bool:
    m = message.lower()
    return any(k in m for k in [
        "pickup", "pick up", "collection", "garbage day", "recycling day",
        "when is", "next garbage", "next recycling", "next pickup", "what day"
    ])

def infer_stream(message: str) -> str:
    m = message.lower()
    if any(k in m for k in ["recycl", "blue bin", "grey bin", "gray bin"]):
        return "recycling"
    if any(k in m for k in ["green bin", "organics", "compost"]):
        return "green_bin"
    return "garbage"

def match_special_item(message: str) -> Optional[str]:
    m = message.lower()
    for rule in SPECIAL_ITEMS:
        if any(k in m for k in rule["keywords"]):
            return rule["answer"]
    return None

def is_sorting_question(message: str) -> bool:
    """
    IMPORTANT: We treat messages containing special-item keywords as sorting questions,
    even if the phrasing is “Where do batteries go?”
    """
    m = message.lower()

    # If message contains any special-item keyword, it's a sorting question
    for rule in SPECIAL_ITEMS:
        if any(k in m for k in rule["keywords"]):
            return True

    # General disposal phrasing
    return any(k in m for k in [
        "what goes", "can i recycle", "can i put", "where do i put", "where do", "where should",
        "which bin", "how do i dispose", "dispose", "disposal", "throw out", "trash",
        "recycle", "recycling", "garbage", "compost", "organics",
        "blue bin", "grey bin", "gray bin", "green bin"
    ])

def build_pickup_reply(street_key: str, stream: str) -> str:
    zone_name = KINGSTON_DATA["streets"][street_key]
    zone = KINGSTON_DATA["zones"][zone_name]

    today = date.today()
    target_day = WEEKDAY_TO_INT[zone["day"].lower()]
    next_pickup = next_date_for_weekday(target_day, today)

    week_num = get_week_number(next_pickup)

    collecting: List[str] = ["garbage", "green_bin"]
    if week_num == 1:
        collecting += zone["week1"]
    else:
        collecting += zone["week2"]

    collecting_pretty = ", ".join([c.replace("_", " ") for c in collecting])

    if stream == "recycling":
        focus_line = "Recycling alternates weekly (blue/grey) — see items collected below."
    elif stream == "green_bin":
        focus_line = "Green bin is collected weekly (demo)."
    else:
        focus_line = "Garbage is collected weekly (demo)."

    return (
        f"<b>{street_key.title()}</b> (zone: <b>{zone_name.replace('_',' ')}</b>)<br>"
        f"Next collection: <b>{format_date(next_pickup)}</b><br>"
        f"{focus_line}<br>"
        f"Items collected that day: <b>{collecting_pretty}</b><br>"
        f"<span style='color:#666;font-size:13px'>Demo uses a pilot dataset; full rollout connects to City collection zones + schedules.</span>"
    )

def build_sorting_reply(message: str) -> str:
    # 1) Special items first
    special = match_special_item(message)
    if special:
        return special

    m = message.lower()

    # 2) If user asks about a bin explicitly
    if "blue" in m:
        return f"<b>Blue bin:</b> {KINGSTON_DATA['bin_info']['blue_bin']}"
    if "grey" in m or "gray" in m:
        return f"<b>Grey bin:</b> {KINGSTON_DATA['bin_info']['grey_bin']}"
    if any(k in m for k in ["green bin", "organics", "compost"]):
        return f"<b>Green bin (organics):</b> {KINGSTON_DATA['bin_info']['green_bin']}"

    # 3) Tiny set of common items (expand later)
    if any(k in m for k in ["bottle", "can", "jar"]):
        return "<b>Usually blue bin:</b> Rinse if needed, then put containers in the <b>blue bin</b>."
    if any(k in m for k in ["cardboard", "paper"]):
        return "<b>Usually grey bin:</b> Paper and cardboard go in the <b>grey bin</b>."
    if any(k in m for k in ["food", "leftover", "banana", "apple", "coffee grounds"]):
        return "<b>Usually green bin:</b> Food scraps go in the <b>green bin</b>."

    return (
        "Tell me the item and I’ll suggest where it goes (e.g., “battery”, “pizza box”, “old phone”).<br>"
        "I can also answer <b>pickup schedule</b> questions if you include your street."
    )

# =========================
# Optional Claude (rewrite + translate)
# =========================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def claude_refine(user_message: str, base_answer_html: str, lang: str = "en") -> str:
    if not ANTHROPIC_API_KEY:
        return base_answer_html

    lang = (lang or "en").lower().strip()
    lang_name = {
        "en": "English",
        "fr": "French",
        "es": "Spanish",
        "zh": "Simplified Chinese",
    }.get(lang, "English")

    # If English, no need to "translate"—just polish
    if lang_name == "English":
        prompt = (
            "Rewrite the following answer to be friendly, concise, and clear.\n"
            "Do not change facts/dates. Preserve <b> and <br> formatting.\n\n"
            f"{base_answer_html}\n"
        )
        system_msg = "You are a helpful civic services assistant."
    else:
        # Strong translation instruction
        prompt = (
            f"Translate the following answer into {lang_name}.\n"
            f"CRITICAL: Output must be 100% in {lang_name}. Do not include English.\n"
            "Do not change facts/dates. Preserve <b> and <br> formatting.\n\n"
            f"{base_answer_html}\n"
        )
        system_msg = f"You must respond ONLY in {lang_name}."

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 450,
                "system": system_msg,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        data = r.json()
        if "content" in data and data["content"]:
            return data["content"][0].get("text", base_answer_html)
        return base_answer_html
    except Exception:
        return base_answer_html


# =========================
# Routes
# =========================
@app.post("/chat")
def chat():
    body = request.get_json(force=True)
    message = (body.get("message", "") or "").strip()
    lang = (body.get("lang", "en") or "en").strip().lower()

    print("DEBUG /chat message:", message)
    print("DEBUG /chat lang:", lang)

    if not message:
        return jsonify({"ok": False, "error": "Please type a message."}), 400

    # 0) Special items always work, even if phrasing doesn't match sorting triggers
    special = match_special_item(message)
    if special:
        refined = claude_refine(message, special, lang)
        return jsonify({"ok": True, "reply": refined})

    # 1) Pickup schedule questions: deterministic
    if is_pickup_question(message):
        street_key = find_street_key(message)
        if not street_key:
            known = ", ".join(list(KINGSTON_DATA["streets"].keys())[:12])
            base = (
                "I can help — which street are you on?<br>"
                f"<span style='color:#666;font-size:13px'>Demo streets I recognize: {known} ...</span>"
            )
            return jsonify({"ok": True, "reply": claude_refine(message, base, lang)})

        stream = infer_stream(message)
        base = build_pickup_reply(street_key, stream)
        refined = claude_refine(message, base, lang)
        return jsonify({"ok": True, "reply": refined})

    # 2) Sorting / “where does this go?” questions
    if is_sorting_question(message):
        base = build_sorting_reply(message)
        refined = claude_refine(message, base, lang)
        return jsonify({"ok": True, "reply": refined})

    # 3) Default fallback
    known = ", ".join(list(KINGSTON_DATA["streets"].keys())[:12])
    base = (
        "I can answer:<br>"
        "• <b>Pickup schedule</b> questions (e.g., “When is garbage pickup on Princess?”)<br>"
        "• <b>Item disposal</b> questions (e.g., “battery”, “pizza box”, “old phone”)<br>"
        f"<span style='color:#666;font-size:13px'>Demo streets I recognize: {known} ...</span>"
    )
    return jsonify({"ok": True, "reply": claude_refine(message, base, lang)})

@app.get("/health")
def health():
    return jsonify({"ok": True, "anthropic_enabled": bool(ANTHROPIC_API_KEY)})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
