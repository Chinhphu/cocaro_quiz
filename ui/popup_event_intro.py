# ui/popup_event_intro.py
import pygame
from utils.helpers import get_font
from utils.colors import TEXT_SECONDARY, EVENT_COLORS
from utils.helpers import wrap_lines, text_block_height  # dùng helpers thay vì hàm wrap nội bộ

ELLIPSIS = "…"

class EventIntroPopup:
    """
    Popup giới thiệu sự kiện:
    - Overlay mờ
    - Card bo góc giữa màn hình
    - Icon + TIÊU ĐỀ (wrap, tối đa 3 dòng, canh giữa)
    - Mô tả có khung cuộn (không tràn)
    - Nút "Sẵn sàng" cố định
    - Màu accent theo event_type
    """
    def __init__(self, event_id: str, title: str, desc: str, icon_surface: pygame.Surface, event_type: str):
        self.event_id = event_id or "EVENT"
        self.title = (title or "").strip() or "Sự kiện"
        self.desc = (desc or "").strip()
        self.icon = icon_surface
        self.event_type = (event_type or "bonus").lower()
        self.accent = EVENT_COLORS.get(self.event_type, (0, 191, 165))

        self.finished = False
        self.hover_btn = False

        # Fonts đồng bộ với hệ thống
        self.title_font = get_font("heading2", "bold")   # ~32pt
        self.desc_font  = get_font("body", "medium")     # ~22pt
        self.btn_font   = get_font("body", "bold")

        # Layout state
        self.card_rect = None
        self.btn_rect = None

        # Scroll state cho mô tả
        self.scroll_y = 0
        self.max_scroll = 0

    # ---------------- Interaction ----------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.btn_rect:
            self.hover_btn = self.btn_rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_rect and self.btn_rect.collidepoint(event.pos):
                self.finished = True

        if event.type == pygame.MOUSEWHEEL and self.max_scroll > 0:
            self.scroll_y -= event.y * 30
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.finished = True
            elif event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)
            elif event.key == pygame.K_PAGEUP:
                self.scroll_y = max(0, self.scroll_y - 200)
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 200)

    def is_finished(self):
        return self.finished

    # ---------------- Drawing ----------------
    def draw(self, screen):
        sw, sh = screen.get_size()

        # Overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Card
        card_w = min(840, int(sw * 0.84))
        card_h = min(520, int(sh * 0.76))
        self.card_rect = pygame.Rect(0, 0, card_w, card_h)
        self.card_rect.center = (sw // 2, sh // 2)
        pygame.draw.rect(screen, (255, 255, 255), self.card_rect, border_radius=16)

        pad = 28
        inner_left  = self.card_rect.x + pad
        inner_right = self.card_rect.right - pad
        inner_w     = inner_right - inner_left
        cur_y       = self.card_rect.y + pad

        # Icon (center)
        if self.icon:
            max_ih = 100
            ih = max_ih
            iw = int(self.icon.get_width() * (ih / max(1, self.icon.get_height())))
            icon_surf = pygame.transform.smoothscale(self.icon, (iw, ih))
            icon_rect = icon_surf.get_rect()
            icon_rect.centerx = self.card_rect.centerx
            icon_rect.y = cur_y
            screen.blit(icon_surf, icon_rect)
            cur_y = icon_rect.bottom + 16
        else:
            cur_y += 8

        # ----- TITLE: wrap + center + giới hạn 3 dòng -----
        maxw_title = int(inner_w * 0.92)
        title_lines = wrap_lines(self.title_font, self.title, maxw_title)
        if len(title_lines) > 3:
            title_lines = title_lines[:3]
            while self.title_font.size(title_lines[-1] + ELLIPSIS)[0] > maxw_title and len(title_lines[-1]) > 1:
                title_lines[-1] = title_lines[-1][:-1]
            title_lines[-1] = title_lines[-1] + ELLIPSIS

        for ln in title_lines:
            surf = self.title_font.render(ln, True, self.accent)
            rect = surf.get_rect()
            rect.centerx = self.card_rect.centerx
            rect.y = cur_y
            screen.blit(surf, rect)
            cur_y = rect.bottom + 8

        cur_y += 6  # chút khoảng cách trước phần mô tả

        # Nút (đặt trước để giữ vùng desc không đè lên)
        btn_w, btn_h = 180, 52
        self.btn_rect = pygame.Rect(
            self.card_rect.right - pad - btn_w,
            self.card_rect.bottom - pad - btn_h,
            btn_w, btn_h
        )

        # Khu vực mô tả (scrollable)
        content_bottom  = self.btn_rect.top - 16
        content_height  = max(60, content_bottom - cur_y)
        content_rect    = pygame.Rect(inner_left, cur_y, inner_w, content_height)

        # Render desc vào surface riêng (dùng wrap_lines + text_block_height)
        content_surf = pygame.Surface((inner_w, max(content_height, 10)), pygame.SRCALPHA)
        desc_lines = wrap_lines(self.desc_font, self.desc, int(inner_w * 0.92))
        total_h = text_block_height(self.desc_font, desc_lines, line_spacing=6)

        # clamp scroll
        self.max_scroll = max(0, total_h - content_height)
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

        # Vẽ từng dòng (canh giữa) vào content_surf
        y = 0
        center_x = content_surf.get_width() // 2
        for ln in desc_lines:
            if ln == "":
                y += self.desc_font.get_height()
                continue
            s = self.desc_font.render(ln, True, TEXT_SECONDARY)
            r = s.get_rect()
            r.centerx = center_x
            r.y = y
            content_surf.blit(s, r)
            y += s.get_height() + 6

        # Blit với cắt theo scroll
        screen.blit(content_surf, (content_rect.x, content_rect.y),
                    area=pygame.Rect(0, self.scroll_y, content_rect.w, content_rect.h))

        # Scrollbar (nếu cần)
        if self.max_scroll > 0:
            bar_w = 6
            rail = pygame.Rect(content_rect.right - bar_w, content_rect.y, bar_w, content_rect.h)
            pygame.draw.rect(screen, (230, 230, 230), rail, border_radius=3)
            visible_ratio = content_rect.h / (total_h + 1e-6)
            thumb_h = max(24, int(rail.h * visible_ratio))
            thumb_y = rail.y + int((self.scroll_y / max(1, self.max_scroll)) * (rail.h - thumb_h))
            pygame.draw.rect(screen, (200, 200, 200), (rail.x, thumb_y, bar_w, thumb_h), border_radius=3)

        # Nút "Sẵn sàng"
        btn_color = self._mix(self.accent, (255, 255, 255), 0.15) if self.hover_btn else self.accent
        pygame.draw.rect(screen, btn_color, self.btn_rect, border_radius=12)
        btn_text = self.btn_font.render("Sẵn sàng", True, (255, 255, 255))
        screen.blit(btn_text, btn_text.get_rect(center=self.btn_rect.center))

    # ---------------- Helpers ----------------
    @staticmethod
    def _mix(c1, c2, t=0.5):
        return (
            int(c1[0]*(1-t)+c2[0]*t),
            int(c1[1]*(1-t)+c2[1]*t),
            int(c1[2]*(1-t)+c2[2]*t),
        )