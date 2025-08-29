# core/board.py
import os
import pygame
import random
from utils.config import CELL_SIZE, MARGIN
from utils.colors import BACKGROUND_MEDIUM, TEAM_COLORS, EVENT_COLORS, TEXT_MUTED
from utils.helpers import get_font, color
# --- NEW: Import danh sách sự kiện ---
from core.event_mapping import EVENT_TYPE_MAP

# --- NEW: Thêm công tắc để bật/tắt chế độ debug ---
# Đặt là True để trải đều tất cả sự kiện ra bàn cờ
# Đặt là False để quay lại chế độ sinh ngẫu nhiên như bình thường
DEBUG_ASSIGN_ALL_EVENTS = True

GUTTER_SIZE = 30

class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.owner = None
        self.event_type = None
        self.question_used = False
        self.event_id = None # Sẽ được gán trực tiếp ở chế độ debug
        self.protected = False
        self.blocked = False

    def is_empty(self):
        return self.owner is None

class Board:
    PIECE_DIR = os.path.join("assets", "images", "pieces")

    def __init__(self, size, event_count):
        self.size = size
        self.cells = [[Cell(r, c) for c in range(size)] for r in range(size)]
        self._step = CELL_SIZE + MARGIN
        self.piece_icons = self._load_piece_icons()
        self.highlight_cells = []
        self.label_font = get_font("caption", "semibold")

        # --- MODIFIED: Dùng công tắc debug ---
        if DEBUG_ASSIGN_ALL_EVENTS:
            self.assign_all_events_for_debugging()
        else:
            self.assign_event_cells(event_count)

    # --- NEW: Hàm mới để gán tất cả sự kiện cho việc test ---
    def assign_all_events_for_debugging(self):
        """Trải đều tất cả các event đã định nghĩa lên bàn cờ."""
        all_event_ids = list(EVENT_TYPE_MAP.keys())
        random.shuffle(all_event_ids) # Xáo trộn để mỗi lần chạy có một layout khác nhau

        all_cells = [cell for row in self.cells for cell in row]
        
        print("--- DEBUG MODE: Assigning all events to board ---")
        # Gán lần lượt từng event_id cho một ô
        for i, event_id in enumerate(all_event_ids):
            if i < len(all_cells): # Đảm bảo không gán nhiều hơn số ô có trên bàn cờ
                cell = all_cells[i]
                cell.event_id = event_id
                cell.event_type = EVENT_TYPE_MAP[event_id] # Lấy type tương ứng
                print(f"  Assigned {event_id} to cell ({cell.row}, {cell.col})")
        print("-------------------------------------------------")


    def assign_event_cells(self, count):
        """Hàm sinh sự kiện ngẫu nhiên gốc."""
        all_cells = [cell for row in self.cells for cell in row]
        random.shuffle(all_cells)
        selected = all_cells[:max(0, min(count, len(all_cells)))]
        possible_types = list(EVENT_COLORS.keys())
        for cell in selected:
            cell.event_type = random.choice(possible_types)
    
    def _load_piece_icons(self):
        # ... (Hàm này giữ nguyên, không thay đổi) ...
        icons = {}
        target = CELL_SIZE - 12
        for sym in ["A", "B", "C", "D", "E", "F"]:
            path = os.path.join(self.PIECE_DIR, f"{sym}.png")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    ih, iw = target, int(img.get_width() * (target / max(1, img.get_height())))
                    icons[sym] = pygame.transform.smoothscale(img, (iw, ih))
                except Exception as e:
                    print(f"[WARN] Cannot load piece icon {path}: {e}")
        return icons

    def draw(self, screen):
        # ... (Hàm này giữ nguyên, không thay đổi) ...
        for c in range(self.size):
            label_text = chr(ord('A') + c)
            label_surf = self.label_font.render(label_text, True, color(TEXT_MUTED))
            x_pos = MARGIN + GUTTER_SIZE + c * self._step + (CELL_SIZE // 2)
            screen.blit(label_surf, label_surf.get_rect(center=(x_pos, MARGIN + GUTTER_SIZE // 2)))
        for r in range(self.size):
            label_text = str(r + 1)
            label_surf = self.label_font.render(label_text, True, color(TEXT_MUTED))
            y_pos = MARGIN + GUTTER_SIZE + r * self._step + (CELL_SIZE // 2)
            screen.blit(label_surf, label_surf.get_rect(center=(MARGIN + GUTTER_SIZE // 2, y_pos)))
        for r in range(self.size):
            base_y = MARGIN + GUTTER_SIZE + r * self._step
            for c in range(self.size):
                base_x = MARGIN + GUTTER_SIZE + c * self._step
                cell = self.cells[r][c]
                rect = pygame.Rect(base_x, base_y, CELL_SIZE, CELL_SIZE)
                if cell.owner:
                    icon = self.piece_icons.get(cell.owner)
                    if icon:
                        pygame.draw.rect(screen, color(BACKGROUND_MEDIUM), rect, border_radius=10)
                        ir = icon.get_rect(center=rect.center)
                        screen.blit(icon, ir)
                    else:
                        fill = TEAM_COLORS.get(cell.owner, (170, 170, 170))
                        pygame.draw.rect(screen, color(fill), rect, border_radius=6)
                else:
                    fill = EVENT_COLORS.get(cell.event_type, BACKGROUND_MEDIUM) if cell.event_type else BACKGROUND_MEDIUM
                    pygame.draw.rect(screen, color(fill), rect, border_radius=6)
                if cell in self.highlight_cells:
                    pygame.draw.rect(screen, (255, 215, 0), rect, 3, border_radius=8)

    def get_cell_at(self, mouse_pos):
        # ... (Hàm này giữ nguyên, không thay đổi) ...
        mx, my = mouse_pos
        start_x, start_y = MARGIN + GUTTER_SIZE, MARGIN + GUTTER_SIZE
        if mx < start_x or my < start_y: return None
        step = self._step
        c, r = (mx - start_x) // step, (my - start_y) // step
        if r < 0 or c < 0 or r >= self.size or c >= self.size: return None
        x, y = start_x + c * step, start_y + r * step
        if not (x <= mx <= x + CELL_SIZE and y <= my <= y + CELL_SIZE): return None
        return self.cells[r][c]