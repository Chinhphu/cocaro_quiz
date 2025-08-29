# ui/popup_confirmation.py
import pygame
from utils.colors import SURFACE, TEXT_PRIMARY, BACKGROUND_MEDIUM, EVENT_COLORS
from utils.helpers import get_font, color, wrap_lines

class ConfirmationPopup:
    def __init__(self, message: str, confirm_text="Xác nhận", cancel_text="Hủy"):
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        
        self.result = None  # None: đang chờ, "confirm": đồng ý, "cancel": hủy
        
        # Fonts
        self.font_body = get_font("body", "semibold")
        self.font_btn = get_font("label", "bold")
        
        # Cache rects
        self.card_rect = None
        self.confirm_rect = None
        self.cancel_rect = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.confirm_rect and self.confirm_rect.collidepoint(event.pos):
                self.result = "confirm"
            elif self.cancel_rect and self.cancel_rect.collidepoint(event.pos):
                self.result = "cancel"
                
    def draw(self, screen):
        sw, sh = screen.get_size()
        
        # Overlay mờ
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        
        # Card
        card_w = 400
        card_h = 200
        self.card_rect = pygame.Rect(0, 0, card_w, card_h)
        self.card_rect.center = (sw // 2, sh // 2)
        pygame.draw.rect(screen, color(SURFACE), self.card_rect, border_radius=16)
        
        # Message text
        lines = wrap_lines(self.font_body, self.message, card_w - 40)
        y_draw = self.card_rect.y + 40
        for line in lines:
            line_surf = self.font_body.render(line, True, color(TEXT_PRIMARY))
            line_rect = line_surf.get_rect(centerx=self.card_rect.centerx, y=y_draw)
            screen.blit(line_surf, line_rect)
            y_draw += line_surf.get_height() + 5
            
        # Buttons
        btn_h = 44
        btn_w = 140
        padding = 15
        
        # Cancel button (trái)
        self.cancel_rect = pygame.Rect(
            self.card_rect.x + padding,
            self.card_rect.bottom - btn_h - padding,
            btn_w, btn_h
        )
        pygame.draw.rect(screen, color(BACKGROUND_MEDIUM), self.cancel_rect, border_radius=12)
        cancel_surf = self.font_btn.render(self.cancel_text, True, color(TEXT_PRIMARY))
        screen.blit(cancel_surf, cancel_surf.get_rect(center=self.cancel_rect.center))
        
        # Confirm button (phải, màu đỏ)
        self.confirm_rect = pygame.Rect(
            self.card_rect.right - btn_w - padding,
            self.card_rect.bottom - btn_h - padding,
            btn_w, btn_h
        )
        pygame.draw.rect(screen, color(EVENT_COLORS["danger"]), self.confirm_rect, border_radius=12)
        confirm_surf = self.font_btn.render(self.confirm_text, True, color(SURFACE))
        screen.blit(confirm_surf, confirm_surf.get_rect(center=self.confirm_rect.center))