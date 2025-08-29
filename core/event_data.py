# core/event_data.py
# Mô tả ngắn để hiển thị trên popup intro

EVENT_INFO = {
    "DOUBLE_CORRECT": {
        "title": "Trả lời ĐÚNG 2 câu liên tiếp để chiếm ô.",
        "desc": "Sai bất kỳ câu nào, ô vẫn trống."
    },
    "EXTRA_TURN_OR_LOSE": {
        "title": "Đúng +1 lượt, Sai mất lượt.",
        "desc": "Trả lời đúng: được đi thêm 1 lượt. Trả lời sai: mất lượt hiện tại."
    },
    "OPPONENT_QUESTION": {
        "title": "Đối thủ trả lời thay bạn.",
        "desc": "Nếu đối thủ trả lời đúng, họ chiếm ô. Nếu sai, ô vẫn trống."
    },
    
    "LOSE_TURN": {
        "title": "Mất lượt ngay.",
        "desc": "Bỏ qua lượt hiện tại. Không có câu hỏi."
    },
    "OPPONENT_CAPTURE": {
        "title": "Đối thủ chiếm ô ngay.",
        "desc": "Ô này thuộc về đội đối thủ lập tức. Không có câu hỏi."
    },
    "REMOVE_ONLY": {
        "title": "Xóa 1 ô của đối thủ.",
        "desc": "Chọn ngẫu nhiên và xóa 1 ô thuộc về đối thủ. Ô hiện tại vẫn trống."
    },
    
    
    "SKIP_NEXT_OPPONENT": {
        "title": "Bỏ qua lượt đối thủ tiếp theo.",
        "desc": "Khi lượt của đối thủ tới sẽ bị bỏ qua. (Bản nhẹ: chưa áp dụng.)"
    },
    "DOUBLE_MOVE": {
        "title": "Đúng thì đi 2 lượt.",
        "desc": "Nếu trả lời đúng: chiếm ô và được đi thêm 1 lượt nữa."
    },
    "BLOCK_CELL": {
        "title": "Khóa ô.",
        "desc": "Ô bị khóa, không thể chiếm trong lượt này."
    },
    "CHANGE_OWNER": {
        "title": "Đổi quyền 1 ô của đối thủ.",
        "desc": "Chuyển quyền sở hữu 1 ô đối thủ sang đội bạn."
    },
    "FREE_CAPTURE": {
        "title": "Chiếm ô miễn phí.",
        "desc": "Không cần trả lời. Ô thuộc về đội bạn ngay."
    },
    
    "HINT_UNLOCK": {
        "title": "Mở gợi ý.",
        "desc": "Bạn được +5 giây để suy nghĩ (thay cho hint)."
    },
    "SWITCH_QUESTION": {
        "title": "Đổi câu hỏi 1 lần.",
        "desc": "Trong popup câu hỏi, bạn có thể đổi sang câu khác 1 lần."
    },
    
    
    "NUKE_AREA": {
        "title": "Xóa diện rộng.",
        "desc": "Xóa vùng 3 × 3 ô xung quanh."
    },
    "PROTECT_CELL": {
        "title": "Bảo vệ ô.",
        "desc": "Ô được bảo vệ trong một thời gian. (Bản nhẹ: chưa áp dụng.)"
    },
    
}
