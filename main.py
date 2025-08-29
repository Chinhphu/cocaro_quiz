# main.py
import pygame, os, random
from core.question_manager import QuestionManager
from core.board import Board
from utils.config import DATA_PATH, CELL_SIZE, MARGIN, PANEL_WIDTH, WIN_LENGTH
from utils.colors import BACKGROUND_LIGHT, TEAM_COLORS, TEXT_PRIMARY, SURFACE
from utils.helpers import get_font, color
from ui.popup_question import QuestionPopup
from ui.popup_confirmation import ConfirmationPopup
from core.player import Player
from core.game_manager import GameManager
from ui.sidebar_panel import SidebarPanel
from ui.popup_event_intro import EventIntroPopup
from core.event_data import EVENT_INFO
from core.event_mapping import EVENT_TYPE_MAP, TYPE_TO_IDS
from core.event_engine import (
    plan as plan_event,
    apply_immediate,
    resolver_team_symbol,
    resolve_answer,
    reroll_allowed,
    consume_reroll,
)

def load_event_icon(event_id: str):
    path = os.path.join("assets", "images", "events", f"{event_id}.png")
    if os.path.exists(path):
        try: return pygame.image.load(path).convert_alpha()
        except Exception as e: print(f"[WARN] Failed to load icon {event_id}.png: {e}")
    else: print(f"[WARN] Icon not found: {path}")
    return None

pygame.init()
question_manager = QuestionManager(DATA_PATH)
BOARD_SIZE = question_manager.get_board_size()

# --- NEW: Thêm Gutter vào kích thước cửa sổ ---
GUTTER_SIZE = 30
WINDOW_WIDTH  = BOARD_SIZE * (CELL_SIZE + MARGIN) + MARGIN + PANEL_WIDTH + GUTTER_SIZE
WINDOW_HEIGHT = BOARD_SIZE * (CELL_SIZE + MARGIN) + MARGIN + GUTTER_SIZE

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("CỜ GIÁO - Quiz Cờ Ca Rô")
clock = pygame.time.Clock()
board = Board(BOARD_SIZE, question_manager.get_event_cell_count())
players = [
    Player("Đội A", "A", TEAM_COLORS["A"]),
    Player("Đội B", "B", TEAM_COLORS["B"]),
    Player("Đội C", "C", TEAM_COLORS["C"]), # <-- Thêm dòng này
]
gm = GameManager(board, players, win_length=WIN_LENGTH)
gm.board = board
sidebar = SidebarPanel(
    BOARD_SIZE * (CELL_SIZE + MARGIN) + MARGIN + GUTTER_SIZE + 20, 10, PANEL_WIDTH - 40,
)

GAME_STATE = "PLAYING"
popup_intro, popup_question, popup_confirm = None, None, None
selected_cell, target_cells_cache = None, []
BASE_SECONDS = 15
current_evt_ctx = None

# --- NEW: Biến cho tooltip và font ---
hovered_cell_label = None
tooltip_font = get_font("caption", "bold")

def get_targetable_cells(target_type):
    targets = []
    if target_type == "enemy_cell":
        current_symbol = gm.current_player.symbol
        for row in board.cells:
            for cell in row:
                if cell.owner and cell.owner != current_symbol and not getattr(cell, "protected", False):
                    targets.append(cell)
    return targets

def open_question_for_ctx():
    global popup_question, selected_cell
    if not current_evt_ctx: return
    team_symbol = resolver_team_symbol(current_evt_ctx, gm)
    seconds = BASE_SECONDS + getattr(current_evt_ctx, "time_bonus", 0)
    q = question_manager.get_question()
    if q:
        popup_question = QuestionPopup(
            q, team_label=team_symbol, seconds=seconds, event_context=current_evt_ctx, cell_label=get_cell_label(selected_cell)
        )

def reset_turn_state():
    global current_evt_ctx, selected_cell, target_cell_cache, GAME_STATE
    current_evt_ctx, selected_cell, target_cell_cache = None, None, None
    board.highlight_cells = []
    GAME_STATE = "PLAYING"

def get_cell_label(cell):
    if not cell: return ""
    return f"{chr(ord('A') + cell.col)}{cell.row + 1}"

running = True
while running:
    events = pygame.event.get()
    mouse_pos = pygame.mouse.get_pos()
    for event in events:
        if event.type == pygame.QUIT: running = False

    # --- NEW: Xử lý hover để hiển thị tooltip ---
    # Chỉ hiện tooltip khi không có popup nào đang che
    if popup_intro is None and popup_question is None and popup_confirm is None:
        hovered_cell = board.get_cell_at(mouse_pos)
        if hovered_cell:
            hovered_cell_label = get_cell_label(hovered_cell)
        else:
            hovered_cell_label = None
    else:
        hovered_cell_label = None

    # --- Xử lý trạng thái game (giữ nguyên) ---
    if GAME_STATE == "PLAYING":
        if popup_intro is None and popup_question is None and current_evt_ctx is None:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    cell = board.get_cell_at(mouse_pos)
                    if not cell or cell.owner is not None: continue
                    selected_cell = cell
                    if cell.event_type:
                        base_type, event_id = str(cell.event_type).lower(), getattr(cell, "event_id", None)
                        if not event_id:
                            candidates = TYPE_TO_IDS.get(base_type, [])
                            event_id = random.choice(candidates) if candidates else random.choice(list(EVENT_TYPE_MAP.keys()))
                            setattr(cell, "event_id", event_id)
                        info, icon = EVENT_INFO.get(event_id, {}), load_event_icon(event_id)
                        sidebar.add_log(f"Sự kiện tại {get_cell_label(cell)}: {info.get('title', event_id)}")
                        popup_intro = EventIntroPopup(
                            event_id=event_id, title=info.get("title", "Sự kiện"), desc=info.get("desc", ""), 
                            icon_surface=icon, event_type=EVENT_TYPE_MAP.get(event_id, base_type),
                        )
                    else:
                        q = question_manager.get_question()
                        if q: popup_question = QuestionPopup(q, team_label=gm.current_player.symbol, seconds=BASE_SECONDS, cell_label=get_cell_label(cell))
        if popup_intro:
            for event in events: popup_intro.handle_event(event)
        if popup_question:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_R and current_evt_ctx and reroll_allowed(current_evt_ctx):
                    consume_reroll(current_evt_ctx)
                    sidebar.add_log(f"{gm.current_player.name} đã đổi câu hỏi!")
                    popup_question, q = None, question_manager.get_question()
                    if q: open_question_for_ctx()
                else: popup_question.handle_event(event)
    elif GAME_STATE == "TARGET_SELECTION":
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cell = board.get_cell_at(mouse_pos)
                if cell and cell in board.highlight_cells:
                    target_cell_cache = cell
                    popup_confirm = ConfirmationPopup(message=f"Áp dụng lên ô {get_cell_label(cell)}?")
                    GAME_STATE = "AWAITING_CONFIRMATION"
    elif GAME_STATE == "AWAITING_CONFIRMATION":
        if popup_confirm:
            for event in events: popup_confirm.handle_event(event)
            if popup_confirm.result is not None:
                if popup_confirm.result == "confirm":
                    current_evt_ctx.selected_target_cells = target_cells_cache
                    
                    if current_evt_ctx.event_id in ["REMOVE_ONLY", "NUKE_AREA"]:
                        log_msg = f"{gm.current_player.name} xóa {len(target_cells_cache)} ô."
                        sidebar.add_log(log_msg)
                        apply_immediate(current_evt_ctx, gm, selected_cell, board)
                        reset_turn_state()
                    else:
                        open_question_for_ctx()
                        # --- SỬA LỖI: Chuyển game về trạng thái PLAYING ---
                        GAME_STATE = "PLAYING"
                
                elif popup_confirm.result == "cancel":
                    target_cells_cache = []
                    GAME_STATE = "TARGET_SELECTION"
                
                popup_confirm = None

    if popup_intro and popup_intro.is_finished():
        eid, base_type = getattr(selected_cell, "event_id", None), str(selected_cell.event_type).lower() if selected_cell.event_type else "bonus"
        current_evt_ctx = plan_event(eid, EVENT_TYPE_MAP.get(eid, base_type), gm, selected_cell)
        if current_evt_ctx.requires_target_selection and current_evt_ctx.event_id == "REMOVE_ONLY":
            GAME_STATE, board.highlight_cells = "TARGET_SELECTION", get_targetable_cells(current_evt_ctx.target_type)
        else:
            imm = apply_immediate(current_evt_ctx, gm, selected_cell, board)
            if imm["open_question"]:
                if current_evt_ctx.requires_target_selection:
                    GAME_STATE, board.highlight_cells = "TARGET_SELECTION", get_targetable_cells(current_evt_ctx.target_type)
                else: open_question_for_ctx()
            else:
                if current_evt_ctx.event_id == "LOSE_TURN": sidebar.add_log(f"{gm.current_player.name} bị mất lượt!")
                reset_turn_state()
        popup_intro = None

   # --- MODIFIED: Hoàn thiện logic xử lý kết quả popup ---
    if popup_question and popup_question.is_finished():
        was_ok = popup_question.was_correct()
        player_name = gm.current_player.name
        if current_evt_ctx:
            out = resolve_answer(current_evt_ctx, gm, selected_cell, was_ok)
            
            if out.get("ask_more"):
                sidebar.add_log(f"{player_name} trả lời đúng câu 1/2.")
                open_question_for_ctx()

            else:
                # Nếu event đã tự xử lý xong (như CHANGE_OWNER)
                if out.get("resolution_complete"):
                    if out.get("captured"):
                         sidebar.add_log(f"{player_name} cướp thành công ô {get_cell_label(current_evt_ctx.selected_target_cells[0])}!")
                    # Tiếp tục xử lý lượt cho ô sự kiện gốc (để giữ tính năng 2 câu hỏi)
                    winner = gm.resolve_answer(selected_cell, was_ok, advance_turn=True)
                    if winner:
                        sidebar.add_log(f"CHIẾN THẮNG! {winner} đã thắng!")

                else:
                    # Logic cũ cho các event thông thường
                    cell_lbl = get_cell_label(selected_cell)
                    action_str = "đã chiếm" if out.get("captured", was_ok) else "trả lời sai"
                    sidebar.add_log(f"{player_name} {action_str} ô {cell_lbl}.")
                    winner = gm.resolve_answer(selected_cell, was_ok)
                    if out.get("extra_turn"):
                        sidebar.add_log(f"{player_name} được thêm một lượt!")
                    if winner:
                        sidebar.add_log(f"CHIẾN THẮNG! {winner} đã thắng!")

                reset_turn_state()
                popup_question = None
        else: # Ô thường
            cell_lbl = get_cell_label(selected_cell)
            action_str = "đã chiếm" if was_ok else "trả lời sai"
            sidebar.add_log(f"{player_name} {action_str} ô {cell_lbl}.")
            winner = gm.resolve_answer(selected_cell, was_ok)
            if winner:
                sidebar.add_log(f"CHIẾN THẮNG! {winner} đã thắng!")
            reset_turn_state()
            popup_question = None

    screen.fill(color(BACKGROUND_LIGHT))
    board.draw(screen)
    sidebar.draw(screen, gm, gm.win_length)
    if popup_question: popup_question.draw(screen)
    if popup_intro: popup_intro.draw(screen)
    if popup_confirm: popup_confirm.draw(screen)

    # --- NEW: Vẽ tooltip nếu có ---
    if hovered_cell_label:
        text_surf = tooltip_font.render(hovered_cell_label, True, color(SURFACE))
        tooltip_rect = text_surf.get_rect(center=(mouse_pos[0], mouse_pos[1] - 25))
        
        # Thêm background cho tooltip
        bg_rect = tooltip_rect.inflate(12, 6)
        pygame.draw.rect(screen, color(TEXT_PRIMARY), bg_rect, border_radius=5)
        
        screen.blit(text_surf, tooltip_rect)

    pygame.display.flip()
    clock.tick(60)
pygame.quit()