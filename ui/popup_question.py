# ui/popup_question.py
import pygame
from utils.colors import (
    SURFACE, BACKGROUND_MEDIUM, TEXT_PRIMARY, TEXT_MUTED,
    TEXT_HOVER, EVENT_COLORS
)
from utils.helpers import get_font, wrap_lines, text_block_height, color

SCROLL_SPEED = 40

# NEW: Định nghĩa màu cho feedback đáp án
CORRECT_BG = (212, 237, 218)       # Xanh lá cây nhạt
CORRECT_BORDER = (37, 133, 56)     # Xanh lá cây đậm
INCORRECT_BG = (248, 215, 218)     # Đỏ nhạt
INCORRECT_BORDER = (195, 53, 69)   # Đỏ đậm
SELECTION_BG = (217, 236, 255)     # Xanh dương nhạt

def _pill(surface, rect, bg, radius=16, border=None):
    pygame.draw.rect(surface, color(bg), rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, color(border), rect, width=2, border_radius=radius)

class QuestionPopup:
    def __init__(self, question_obj, team_label="A", seconds=15, cell_label=None, event_context=None):
        import random # Đảm bảo đã import random
        self.q = question_obj
        self.team = team_label
        self.cell_label = cell_label or ""
        self.seconds = seconds

        # --- Hệ thống trạng thái ---
        self.state = "ANSWERING"
        self.selected_idx = None
        self.result = None
        self._correct_answer_idx = self._get_correct_answer_index()
        self.time_left_on_reveal = -1
        self._start_ms = pygame.time.get_ticks()

        # --- Logic cho HINT_UNLOCK ---
        self.disabled_options = []
        if event_context and getattr(event_context, "apply_hint", False):
            options_count = len(self.q.get("options", []))
            incorrect_indices = [i for i in range(options_count) if i != self._correct_answer_idx]
            random.shuffle(incorrect_indices)
            num_to_disable = 2 if options_count > 3 else 1
            self.disabled_options = incorrect_indices[:num_to_disable]

        # Fonts
        self.f_title = get_font("heading2", "semibold")
        self.f_body = get_font("body", "medium")
        self.f_label = get_font("label", "semibold")
        self.f_timer = get_font("heading1", "bold")

        # Scroll
        self.scroll_y = 0
        self.max_scroll = 0

        # Cache rects
        self._last_popup_rect = None
        self._viewport = None
        self._option_content_rects = []
        self._last_done_rect = None

    # --- MODIFIED: Phương thức helper mới ---
    def _get_correct_answer_index(self):
        """Xác định index (0-3) của câu trả lời đúng từ dữ liệu."""
        ans = self.q.get("answer")
        options = self.q.get("options", [])
        if isinstance(ans, str) and len(ans) == 1 and ans.upper() in "ABCD":
            return "ABCD".index(ans.upper())
        # Fallback cho câu trả lời dạng text
        for i, option_text in enumerate(options):
            if str(option_text).strip().lower() == str(ans).strip().lower():
                return i
        return -1

    def time_left(self):
        elapsed = (pygame.time.get_ticks() - self._start_ms) / 1000.0
        return max(0, int(self.seconds - elapsed))

    # --- MODIFIED: is_finished giờ rất đơn giản ---
    def is_finished(self):
        return self.state == "FINISHED"

    def was_correct(self):
        return self.result is True

    def _answer_is_correct(self, picked_idx):
        return picked_idx == self._correct_answer_idx

    # --- MODIFIED: handle_event theo trạng thái ---
    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL and self._viewport and self.max_scroll > 0:
            mx, my = pygame.mouse.get_pos()
            if self._viewport.collidepoint(mx, my):
                self.scroll_y = max(0, min(self.scroll_y - event.y * SCROLL_SPEED, self.max_scroll))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.state == "ANSWERING":
                # Cho phép chọn/đổi đáp án
                if self._viewport:
                    for i, content_rect in enumerate(self._option_content_rects):
                        # <<< LOGIC GỢI Ý ĐƯỢC THÊM VÀO ĐÂY
                        # Nếu đáp án này đã bị vô hiệu hóa bởi HINT, bỏ qua không xử lý click
                        if i in getattr(self, "disabled_options", []):
                            continue

                        visible_rect = content_rect.move(0, -self.scroll_y)
                        if self._viewport.colliderect(visible_rect) and visible_rect.collidepoint(mx, my):
                            self.selected_idx = i
                            return

                # Bấm nút "Đáp án"
                if self._last_done_rect and self._last_done_rect.collidepoint(mx, my):
                    if self.selected_idx is not None:
                        self.result = self._answer_is_correct(self.selected_idx)
                        self.time_left_on_reveal = self.time_left()
                        self.state = "REVEALING"

            elif self.state == "REVEALING":
                # Bấm nút "Xong"
                if self._last_done_rect and self._last_done_rect.collidepoint(mx, my):
                    self.state = "FINISHED"

    def draw(self, screen):
        sw, sh = screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        screen.blit(overlay, (0, 0))

        pw = min(760, int(sw * 0.78))
        ph = int(sh * 0.82)
        px, py = (sw - pw) // 2, (sh - ph) // 2
        popup_rect = pygame.Rect(px, py, pw, ph)
        self._last_popup_rect = popup_rect
        pygame.draw.rect(screen, color(SURFACE), popup_rect, border_radius=24)

        padding = 28
        content_x = px + padding
        content_w = pw - padding * 2
        label_y = py + padding + 48
        screen.blit(self.f_label.render(f"Đội {self.team} • Câu hỏi", True, color(TEXT_MUTED)), (content_x, label_y))

        viewport_top = label_y + 32
        viewport_height = ph - (viewport_top - py) - 88
        viewport = pygame.Rect(content_x, viewport_top, content_w, viewport_height)
        self._viewport = viewport

        q_lines = wrap_lines(self.f_title, self.q.get("question", ""), content_w)
        options = self.q.get("options", [])
        opt_line_sets = [wrap_lines(self.f_body, opt, content_w - 56) for opt in options]
        opt_heights = [text_block_height(self.f_body, lines, 4) + 18 for lines in opt_line_sets]
        q_h = text_block_height(self.f_title, q_lines, 6)
        content_total_h = q_h + 16 + sum(opt_heights) + 12 * (len(options) - 1)
        self.max_scroll = max(0, content_total_h - viewport_height)

        clip_prev = screen.get_clip()
        screen.set_clip(viewport)

        y_draw = viewport.y - self.scroll_y
        for ln in q_lines:
            surf = self.f_title.render(ln, True, color(TEXT_PRIMARY))
            screen.blit(surf, (viewport.x, y_draw))
            y_draw += surf.get_height() + 6
        y_draw += 10
        y_content = y_draw + self.scroll_y

        self._option_content_rects = []
        for i, lines in enumerate(opt_line_sets):
            btn_h = opt_heights[i]
            content_rect = pygame.Rect(viewport.x, y_content, content_w, btn_h)
            visible_rect = content_rect.move(0, -self.scroll_y)
            self._option_content_rects.append(content_rect)

            # --- MODIFIED: Logic vẽ màu nền đáp án ---
            bg, border = BACKGROUND_MEDIUM, None
            is_selected = (self.selected_idx == i)
            is_correct_answer = (i == self._correct_answer_idx)

            if self.state == "ANSWERING":
                if is_selected:
                    bg = SELECTION_BG
            elif self.state == "REVEALING":
                if is_correct_answer:
                    bg, border = CORRECT_BG, CORRECT_BORDER
                elif is_selected and not self.result: # Chọn sai
                    bg, border = INCORRECT_BG, INCORRECT_BORDER

            _pill(screen, visible_rect, bg, radius=14, border=border)
            
            lab = self.f_body.render(f"{chr(65+i)}.", True, color(TEXT_PRIMARY))
            screen.blit(lab, (visible_rect.x + 14, visible_rect.y + 10))
            
            tx, ty = visible_rect.x + 14 + lab.get_width() + 8, visible_rect.y + 10
            for ln in lines:
                surf = self.f_body.render(ln, True, color(TEXT_PRIMARY))
                screen.blit(surf, (tx, ty))
                ty += surf.get_height() + 4
            
            y_content += btn_h + 12

        screen.set_clip(clip_prev)

        footer_y = py + ph - 72
        circle_center = (content_x + 36, footer_y + 36)
        
        # --- MODIFIED: Xử lý timer và trạng thái ---
        t_left = self.time_left_on_reveal if self.state == "REVEALING" else self.time_left()
        if t_left <= 0 and self.state == "ANSWERING":
            self.result = self._answer_is_correct(self.selected_idx) if self.selected_idx is not None else False
            self.time_left_on_reveal = 0
            self.state = "REVEALING"
        
        t_col = EVENT_COLORS["danger"] if t_left <= 5 else TEXT_HOVER
        t_surf = self.f_timer.render(str(t_left), True, color(t_col))
        pygame.draw.circle(screen, color(SURFACE), circle_center, 34)
        screen.blit(t_surf, t_surf.get_rect(center=circle_center))
        
        # --- MODIFIED: Xử lý nút bấm ---
        btn_w, btn_h = 140, 44
        done_rect = pygame.Rect(px + pw - padding - btn_w, footer_y + 14, btn_w, btn_h)
        self._last_done_rect = done_rect

        btn_text_str = "Xong" if self.state == "REVEALING" else "Đáp án"
        enabled = (self.selected_idx is not None) if self.state == "ANSWERING" else True
        
        bg = BACKGROUND_MEDIUM if enabled else "#E9EEF4"
        fg = TEXT_PRIMARY if enabled else TEXT_MUTED
        _pill(screen, done_rect, bg, radius=20)
        label = get_font("label", "semibold").render(btn_text_str, True, color(fg))
        screen.blit(label, label.get_rect(center=done_rect.center))

        return popup_rect