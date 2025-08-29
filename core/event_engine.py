# core/event_engine.py
import random

class EventContext:
    def __init__(
        self, event_id, event_type, ask_team="current", num_questions=1,
        time_bonus=0, allow_reroll=False, notes="",
    ):
        self.event_id, self.event_type = event_id, event_type
        self.ask_team, self.remaining = ask_team, num_questions
        self.time_bonus, self.allow_reroll = time_bonus, allow_reroll
        self.used_reroll, self.notes = False, notes
        self.apply_hint = False
        self.requires_target_selection = False
        self.target_type = None
        self.selected_target_cells = [] # Luôn là một danh sách
        self.num_targets_to_select = 1
        self.immediate = {
            "free_capture": False, "skip_turn": False, "block_cell": False,
            "opponent_free_capture": False, "swap_team_now": False,
            "team_swap_symbols": False, "reverse_order": False,
            "skip_next_opponent": False, "shuffle_events": False, "protect_cell": False,
            "nuke_3x3": False,
        }
        self.on_correct = { "capture": True, "extra_turn": False }
        self.on_incorrect = { "keep_empty": True, "lose_turn": False }
        self._steal_return = False

    def __repr__(self):
        return f"<EventContext {self.event_id}>"

def _random_enemy_cells(board, gm, limit=1):
    cur_sym = gm.current_player.symbol
    enemy_cells = [c for r in board.cells for c in r if c.owner and c.owner != cur_sym and not getattr(c, "protected", False)]
    random.shuffle(enemy_cells)
    return enemy_cells[:max(0, limit)]

def plan(event_id: str, event_type: str, gm, cell):
    et = (event_type or "bonus").lower()
    eid = event_id.upper().strip() if event_id else "DOUBLE_CORRECT"
    ctx = EventContext(eid, et)

    # Dựa trên danh sách sự kiện đã được tinh gọn
    if eid == "CHANGE_OWNER":
        ctx.requires_target_selection, ctx.target_type, ctx.num_targets_to_select = True, "enemy_cell", 1
        ctx.on_correct["capture"], ctx.notes = False, "Chọn 1 ô của đối thủ để cướp."
    elif eid == "REMOVE_ONLY":
        ctx.requires_target_selection, ctx.target_type, ctx.num_targets_to_select = True, "enemy_cell", 1
        ctx.notes = "Chọn 1 ô của đối thủ để xóa."
    elif eid == "NUKE_AREA":
        ctx.immediate["nuke_3x3"], ctx.notes = True, "Xóa tất cả các ô trong vùng 3x3 xung quanh."
    elif eid == "DOUBLE_CORRECT":
        ctx.remaining, ctx.notes = 2, "Đúng 2 câu liên tiếp để chiếm ô."
    elif eid == "DOUBLE_MOVE":
        ctx.on_correct["extra_turn"], ctx.notes = True, "Đúng -> chiếm ô + thêm 1 lượt."
    elif eid == "EXTRA_TURN_OR_LOSE":
        ctx.on_correct["extra_turn"], ctx.on_incorrect["lose_turn"] = True, True
        ctx.notes = "Đúng được thêm lượt; sai thì mất lượt."
    elif eid == "FREE_CAPTURE":
        ctx.immediate["free_capture"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Chiếm ô ngay (current)."
    elif eid == "LOSE_TURN":
        ctx.immediate["skip_turn"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Mất lượt ngay."
    elif eid == "OPPONENT_CAPTURE":
        ctx.immediate["opponent_free_capture"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Đối thủ chiếm ô ngay."
    elif eid == "BLOCK_CELL":
        ctx.immediate["block_cell"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Ô bị khóa, không chiếm được."
    elif eid == "HINT_UNLOCK":
        ctx.apply_hint = True
        ctx.notes = "Gợi ý: Loại bỏ 2 đáp án sai."
    elif eid == "SWITCH_QUESTION":
        ctx.allow_reroll = True
        ctx.notes = "Được đổi câu hỏi 1 lần."
    elif eid == "OPPONENT_QUESTION":
        ctx.ask_team = "opponent"
        ctx.notes = "Đối thủ trả lời; đúng thì đối thủ chiếm, sai thì giữ trống."
    elif eid == "STEAL_QUESTION":
        ctx.ask_team = "opponent"
        ctx.notes = "Đối thủ trả lời trước; nếu sai, bạn được trả lời lại (1 câu)."
    elif eid == "TEAM_SWAP":
        ctx.immediate["team_swap_symbols"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Hoán đổi ký hiệu 2 đội."
    elif eid == "NUKE_AREA":
        ctx.immediate["nuke_3x3"] = True # Bật cờ nuke 3x3
        ctx.on_correct["capture"] = False # Không cần câu hỏi, không chiếm ô
        ctx.notes = "Xóa tất cả các ô trong vùng 3x3 xung quanh."
    elif eid == "PROTECT_CELL":
        ctx.immediate["protect_cell"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Bảo vệ ô (ô hiện tại không thể bị chiếm)."
    elif eid == "SHUFFLE_EVENTS":
        ctx.immediate["shuffle_events"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Xáo trộn loại sự kiện trên các ô chưa bị chiếm."
    elif eid == "SWAP_TURN":
        ctx.immediate["swap_team_now"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Đổi lượt cho đội kế tiếp ngay; sau đó vẫn hỏi."
    elif eid == "REVERSE_ORDER":
        ctx.immediate["reverse_order"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Đảo thứ tự lượt (áp dụng từ lượt kế)."
    elif eid == "SKIP_NEXT_OPPONENT":
        ctx.immediate["skip_next_opponent"] = True
        ctx.on_correct["capture"] = False
        ctx.notes = "Bỏ qua lượt đối thủ kế tiếp."
    elif eid == "CHAOS_MODE":
        choices = [ "DOUBLE_CORRECT", "DOUBLE_MOVE", "FREE_CAPTURE", "EXTRA_TURN_OR_LOSE", "NUKE_AREA" ]
        chosen = random.choice(choices)
        return plan(chosen, event_type, gm, cell)
    else:
        ctx.notes = "Fallback: hỏi 1 câu như thường."
        ctx.remaining = 1
    return ctx

def apply_immediate(ctx: EventContext, gm, cell, board):
    out = { "turn_ended": False, "open_question": True, "winner": None }

    # --- SỬA LỖI: LOGIC THỰC THI CHO REMOVE_ONLY ---
    if ctx.event_id == "REMOVE_ONLY":
        # Sửa lại để lặp qua danh sách selected_target_cells (số nhiều)
        for target_cell in ctx.selected_target_cells:
            if target_cell:
                target_cell.owner = None # Xóa chủ ô
        gm.next_turn()
        out["turn_ended"], out["open_question"] = True, False
        return out

    if ctx.immediate.get("nuke_3x3"):
        center_r, center_c = cell.row, cell.col
        nuked_count = 0
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                r, c = center_r + dr, center_c + dc
                if 0 <= r < board.size and 0 <= c < board.size:
                    target_cell = board.cells[r][c]
                    if not getattr(target_cell, "protected", False):
                        if target_cell.owner is not None: nuked_count += 1
                        target_cell.owner = None
        ctx.notes = f"Vụ nổ tại {chr(ord('A') + center_c)}{center_r + 1} đã xóa {nuked_count} ô!"
        gm.next_turn()
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("free_capture"):
        if not getattr(cell, "protected", False) and not getattr(cell, "blocked", False):
            cell.owner = gm.current_player.symbol
            out["winner"] = gm.resolve_answer(cell, was_correct=True, capture_symbol=gm.current_player.symbol, advance_turn=True)
        else: gm.next_turn()
        out["turn_ended"], out["open_question"] = True, False
        return out

    if ctx.immediate.get("opponent_free_capture"):
        next_sym = gm.players[(gm.current_idx + 1) % len(gm.players)].symbol
        if not getattr(cell, "protected", False) and not getattr(cell, "blocked", False):
            cell.owner = next_sym
            out["winner"] = gm.resolve_answer(cell, was_correct=True, capture_symbol=next_sym, advance_turn=True)
        else: gm.next_turn()
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("skip_turn"):
        gm.next_turn()
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("block_cell"):
        cell.blocked, cell.event_type = True, None
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("swap_team_now"):
        gm.next_turn()
        return out # Vẫn mở câu hỏi

    if ctx.immediate.get("team_swap_symbols"):
        if len(gm.players) >= 2:
            a, b = gm.players[0], gm.players[1]
            a.symbol, b.symbol = b.symbol, a.symbol
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("reverse_order"):
        gm.reverse_order()
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("skip_next_opponent"):
        next_sym = gm.players[(gm.current_idx + 1) % len(gm.players)].symbol
        gm.skip_next_for(next_sym)
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("shuffle_events"):
        event_cells = [c for r in board.cells for c in r if c.owner is None and c.event_type]
        types = [c.event_type for c in event_cells]
        random.shuffle(types)
        for c, t in zip(event_cells, types): c.event_type = t
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    if ctx.immediate.get("protect_cell"):
        cell.protected = True
        out["turn_ended"], out["open_question"] = True, False
        return out
        
    return out

def resolver_team_symbol(ctx: EventContext, gm):
    if ctx.ask_team == "current": return gm.current_player.symbol
    return gm.players[(gm.current_idx + 1) % len(gm.players)].symbol

def reroll_allowed(ctx: EventContext):
    return ctx.allow_reroll and not ctx.used_reroll

def consume_reroll(ctx: EventContext):
    ctx.used_reroll = True

def resolve_answer(ctx: EventContext, gm, cell, was_correct: bool):
    out = {"ask_more": False, "captured": False, "extra_turn": False, "resolution_complete": False}
    
    # --- MODIFIED: Hoàn thiện logic cho CHANGE_OWNER ---
    if ctx.event_id == "CHANGE_OWNER" and was_correct:
        if ctx.selected_target_cells:
            target_cell = ctx.selected_target_cells[0]
            if target_cell:
                target_cell.owner = gm.current_player.symbol
                # Báo cho main.py biết rằng hành động cướp ô đã xảy ra
                out["captured"] = True 
        
        out["resolution_complete"] = True
        return out
    
    if not was_correct:
        return out
        
    ctx.remaining -= 1
    if ctx.remaining > 0:
        out["ask_more"] = True
    elif ctx.on_correct.get("capture", True):
        if not getattr(cell, "protected", False) and not getattr(cell, "blocked", False):
            cell.owner = gm.current_player.symbol
            out["captured"] = True
            
    if ctx.on_correct.get("extra_turn"):
        out["extra_turn"] = True

    return out