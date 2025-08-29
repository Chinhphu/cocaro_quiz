# ui/sidebar_panel.py
import pygame
from utils.colors import (
    TEXT_PRIMARY, TEXT_MUTED, BACKGROUND_MEDIUM, TEAM_COLORS,
    SURFACE, TEXT_SECONDARY
)
from utils.helpers import get_font, color, wrap_lines

def _lighten_color(rgb_tuple, amount=80):
    r = min(255, rgb_tuple[0] + amount)
    g = min(255, rgb_tuple[1] + amount)
    b = min(255, rgb_tuple[2] + amount)
    mix_ratio = 0.3
    r = int(r * (1 - mix_ratio) + 245 * mix_ratio)
    g = int(g * (1 - mix_ratio) + 245 * mix_ratio)
    b = int(b * (1 - mix_ratio) + 245 * mix_ratio)
    return (r, g, b)

def _pill(surface, rect, bg, radius=12, border=None):
    pygame.draw.rect(surface, color(bg), rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, color(border), rect, width=2, border_radius=radius)

class SidebarPanel:
    def __init__(self, x, y, width):
        self.rect = pygame.Rect(x, y, width, 9999)
        self.h1 = get_font("heading2", "bold")
        self.body = get_font("body", "medium")
        self.small = get_font("caption", "semibold")
        self.label = get_font("label", "semibold")
        self.line_gap = 8
        self.sec_gap = 16
        self.pad_x = 8
        self.HIGHLIGHT_COLOR = SURFACE
        
        # --- NEW: Thêm bộ nhớ cho Lịch sử trận đấu ---
        self.logs = []
        self.max_logs = 15 # Giới hạn hiển thị 15 dòng log gần nhất
        self.log_font = get_font("caption", "medium")

    # --- NEW: Thêm phương thức để main.py "gửi" log tới ---
    def add_log(self, message: str):
        """Thêm một tin nhắn mới vào đầu danh sách log."""
        self.logs.insert(0, message)
        # Nếu log quá dài, cắt bỏ những dòng cũ nhất
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[:self.max_logs]

    def draw(self, screen, gm, win_length: int):
        x, y = self.rect.x, self.rect.y
        w = self.rect.width

        # --- Phần Thông tin & Thứ tự lượt đi (giữ nguyên) ---
        title = self.h1.render("Thông tin", True, color(TEXT_PRIMARY))
        screen.blit(title, (x, y))
        y += title.get_height() + self.sec_gap

        cur = gm.current_player
        dir_arrow = "→" if getattr(gm, "turn_dir", 1) > 0 else "←"
        turn_txt = f"Lượt: {cur.name} ({cur.symbol}) {dir_arrow}"
        screen.blit(self.body.render(turn_txt, True, color(TEXT_PRIMARY)), (x, y))
        y += 28
        
        skip_sym = getattr(gm, "skip_symbol", None)
        if skip_sym:
            skip_note = f"Sắp bỏ qua lượt của: {skip_sym}"
            screen.blit(self.small.render(skip_note, True, color(TEXT_MUTED)), (x, y))
            y += 20

        win_txt = f"Thắng: {win_length} liên tiếp"
        screen.blit(self.body.render(win_txt, True, color(TEXT_PRIMARY)), (x, y))
        y += 32

        screen.blit(self.label.render("Thứ tự lượt:", True, color(TEXT_PRIMARY)), (x, y))
        y += 24

        counts = self._get_owner_counts(gm)
        ordered_players = self._get_ordered_players(gm)
        chip_h = 28
        number_gutter = 30
        
        for i, p in enumerate(ordered_players):
            is_current = (i == 0)
            turn_number_str = f"{i + 1}."
            font_weight = "bold" if is_current else "medium"
            number_font = get_font("body", font_weight)
            number_surf = number_font.render(turn_number_str, True, color(TEXT_PRIMARY))
            screen.blit(number_surf, (x, y + (chip_h - number_surf.get_height()) // 2))

            chip_x, chip_w = x + number_gutter, w - number_gutter
            chip = pygame.Rect(chip_x, y, chip_w, chip_h)
            team_color = color(TEAM_COLORS.get(p.symbol, "#AAAAAA"))
            bg_color = _lighten_color(team_color) if is_current else BACKGROUND_MEDIUM
            border_color = team_color if is_current else None
            _pill(screen, chip, bg_color, radius=10, border=border_color)

            name_font = get_font("body", "bold" if is_current else "medium")
            dot_r, dot_x = 7, chip.x + 10 + 7
            dot_y = chip.y + chip_h // 2
            pygame.draw.circle(screen, team_color, (dot_x, dot_y), dot_r)

            name_txt = f"{p.name} [{p.symbol}]"
            name_surf = name_font.render(name_txt, True, color(TEXT_PRIMARY))
            screen.blit(name_surf, (dot_x + dot_r + 8, chip.y + (chip_h - name_surf.get_height()) // 2))

            score = counts.get(p.symbol, 0)
            score_surf = self.small.render(f"{score}", True, color(TEXT_MUTED))
            screen.blit(score_surf, (chip.right - score_surf.get_width() - 10, chip.y + (chip_h - score_surf.get_height()) // 2))
            y += chip_h + self.line_gap

        y += self.sec_gap

        # --- NEW: Vẽ khu vực Lịch sử trận đấu ---
        screen.blit(self.label.render("Lịch sử:", True, color(TEXT_PRIMARY)), (x, y))
        y += 24

        for log_msg in self.logs:
            # Tự động wrap text nếu log quá dài
            lines = wrap_lines(self.log_font, log_msg, w)
            for line in lines:
                log_surf = self.log_font.render(line, True, color(TEXT_SECONDARY))
                screen.blit(log_surf, (x, y))
                y += log_surf.get_height() + 2
            
            y += 4 # Thêm khoảng cách nhỏ giữa các log
            if y > screen.get_height() - 20: # Ngăn vẽ tràn ra ngoài
                break

    @staticmethod
    def _get_owner_counts(gm):
        counts = {}
        for row in gm.board.cells:
            for cell in row:
                if cell.owner:
                    counts[cell.owner] = counts.get(cell.owner, 0) + 1
        return counts

    @staticmethod
    def _get_ordered_players(gm):
        ordered_players = []
        num_players = len(gm.players)
        if num_players > 0:
            idx, turn_dir = gm.current_idx, getattr(gm, "turn_dir", 1)
            for _ in range(num_players):
                ordered_players.append(gm.players[idx])
                idx = (idx + turn_dir) % num_players
        return ordered_players