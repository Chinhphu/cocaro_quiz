# core/event_mapping.py

# ID → TYPE (5 loại: bonus|warning|danger|challenge|special)
EVENT_TYPE_MAP = {
    # Giữ lại
    "DOUBLE_CORRECT": "bonus",
    "EXTRA_TURN_OR_LOSE": "warning",
    "OPPONENT_QUESTION": "challenge",
    "LOSE_TURN": "danger",
    "OPPONENT_CAPTURE": "danger",
    "REMOVE_ONLY": "danger",
    "SKIP_NEXT_OPPONENT": "danger",
    "DOUBLE_MOVE": "bonus",
    "BLOCK_CELL": "warning",
    "CHANGE_OWNER": "special",
    "FREE_CAPTURE": "bonus",
    "HINT_UNLOCK": "bonus",
    "SWITCH_QUESTION": "challenge",
    "NUKE_AREA": "danger",
    "PROTECT_CELL": "bonus",
}

# TYPE → IDs (để bóc 1 event_id hợp lệ cho một ô thuộc loại đó)
TYPE_TO_IDS = {
    "bonus": [
        "DOUBLE_CORRECT", "DOUBLE_MOVE",
        "FREE_CAPTURE", "HINT_UNLOCK", "PROTECT_CELL"
    ],
    "warning": [
        "EXTRA_TURN_OR_LOSE", "BLOCK_CELL"
    ],
    "danger": [
        "LOSE_TURN", "OPPONENT_CAPTURE", "REMOVE_ONLY",
        "SKIP_NEXT_OPPONENT", "NUKE_AREA"
    ],
    "challenge": [
        "OPPONENT_QUESTION", "SWITCH_QUESTION",
    ],
    "special": [
        "CHANGE_OWNER",
    ],
}