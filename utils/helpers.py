# utils/helpers.py
import pygame
from utils.config import FONT_MEDIUM, FONT_SEMIBOLD, FONT_BOLD, FONT_SIZES

# ---------------- Font helpers (memoized) ----------------
_font_cache = {}

def get_font(style="body", weight="medium"):
    """
    Lấy pygame.font.Font theo (style, weight), có cache để tránh load nhiều lần.
    """
    key = (style, weight)
    if key in _font_cache:
        return _font_cache[key]
    size = FONT_SIZES.get(style, 22)
    if weight == "bold":
        path = FONT_BOLD
    elif weight == "semibold":
        path = FONT_SEMIBOLD
    else:
        path = FONT_MEDIUM
    _font_cache[key] = pygame.font.Font(path, size)
    return _font_cache[key]

# ---------------- Color helpers (RGB-safe) ----------------
def hex_to_rgb(value: str):
    """
    '#RRGGBB' hoặc 'RRGGBB' -> (R, G, B).
    Nếu input không hợp lệ, cố gắng dùng pygame.Color để parse; thất bại thì trả lại giá trị gốc.
    """
    if not isinstance(value, str):
        return value
    s = value.strip().lstrip("#")
    if len(s) == 6:
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except Exception:
            pass
    # fallback: pygame.Color có thể hiểu nhiều định dạng
    try:
        col = pygame.Color(value)
        return (col.r, col.g, col.b)
    except Exception:
        return value

def color(c):
    """
    Trả về tuple (R, G, B) an toàn cho pygame:
    - tuple/list/pygame.Color -> (r,g,b)
    - hex string '#RRGGBB' hoặc 'RRGGBB' -> (r,g,b)
    - loại khác -> trả lại nguyên giá trị (để không phá vỡ nơi khác)
    """
    if isinstance(c, pygame.Color):
        return (c.r, c.g, c.b)
    if isinstance(c, (list, tuple)):
        # Cho phép (r,g,b,a) -> cắt alpha
        return tuple(c[:3])
    if isinstance(c, str):
        return hex_to_rgb(c)
    return c

# ---------------- Text wrapping ----------------
def fit_substring(word: str, font, max_width: int) -> str:
    """Lấy phần đầu của 'word' vừa với max_width (dùng cho từ siêu dài)."""
    if not word:
        return ""
    lo, hi, best = 1, len(word), 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if font.size(word[:mid])[0] <= max_width:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return word[:best]

def wrap_lines(font, text, max_width):
    """
    Trả về danh sách dòng đã wrap theo max_width.
    - Tôn trọng xuống dòng '\n' (coi như đoạn mới).
    - Bẻ cả 'từ' quá dài nếu vượt max_width.
    """
    lines_out = []
    paragraphs = text.split('\n') if text else []
    for raw in paragraphs:
        raw = raw.strip()
        if not raw:
            lines_out.append("")   # giữ dòng trống giữa các đoạn
            continue

        words, cur, cur_w = raw.split(' '), [], 0
        space_w = font.size(' ')[0]

        for w in words:
            wpx = font.size(w)[0]

            # Nếu từ đơn lẻ đã quá rộng, bẻ nhỏ theo pixel
            if wpx > max_width:
                # đẩy dòng hiện tại nếu đang có chữ
                if cur:
                    lines_out.append(' '.join(cur))
                    cur, cur_w = [], 0
                # bẻ từ thành nhiều mảnh
                rest = w
                while font.size(rest)[0] > max_width and len(rest) > 0:
                    cut = fit_substring(rest, font, max_width)
                    lines_out.append(cut)
                    rest = rest[len(cut):]
                if rest:
                    cur = [rest]
                    cur_w = font.size(rest)[0]
                continue

            # ghép thêm w vào dòng hiện tại nếu còn chỗ
            add = (space_w if cur else 0) + wpx
            if cur_w + add <= max_width:
                cur.append(w)
                cur_w += add
            else:
                # đẩy dòng cũ, bắt đầu dòng mới với w
                lines_out.append(' '.join(cur) if cur else w)
                cur, cur_w = [w], wpx

        if cur:
            lines_out.append(' '.join(cur))

    return lines_out

def text_block_height(font, lines, line_spacing=6):
    """Tính tổng chiều cao khối text đã wrap."""
    if not lines:
        return 0
    h = 0
    for ln in lines:
        h += font.size(ln)[1] + line_spacing
    return h - line_spacing  # bỏ spacing dư cuối
