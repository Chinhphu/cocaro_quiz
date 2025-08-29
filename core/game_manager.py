# core/game_manager.py
from typing import List, Optional, Tuple, Dict

# 4 hướng: dọc, ngang, chéo chính, chéo phụ
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]


class GameManager:
    """
    Quản lý lượt chơi, điều kiện thắng, và một số cờ phục vụ EventEngine:
    - turn_dir: +1 (thuận) / -1 (đảo chiều)  -> dùng cho REVERSE_ORDER
    - skip_symbol: bỏ qua lượt kế tiếp của symbol chỉ định -> dùng cho SKIP_NEXT_OPPONENT
    - resolve_answer: an toàn với event đã set owner trước (không ghi đè)
    """

    def __init__(self, board, players: List, win_length: int = 5):
        self.board = board
        self.players = players
        self.current_idx = 0
        self.win_length = win_length
        self.match_log: List[Tuple[int, int, str, bool]] = []  # (row, col, symbol, correct)

        # Event flags / runtime control
        self.turn_dir = 1         # 1: tiến; -1: lùi (REVERSE_ORDER)
        self.skip_symbol: Optional[str] = None  # nếu set -> lượt sau, nếu rơi vào symbol này thì skip một lần

    # ---------- Player / turn helpers ----------

    @property
    def current_player(self):
        return self.players[self.current_idx]

    def next_turn(self, apply_skip: bool = True):
        """Chuyển lượt theo turn_dir. Nếu có skip_symbol thì bỏ qua đúng 1 lần."""
        if not self.players:
            return
        self.current_idx = (self.current_idx + self.turn_dir) % len(self.players)

        if apply_skip and self.skip_symbol:
            # Nếu lượt mới thuộc về người bị skip -> bỏ qua & reset cờ
            if self.current_player.symbol == self.skip_symbol:
                self.current_idx = (self.current_idx + self.turn_dir) % len(self.players)
            self.skip_symbol = None  # chỉ skip đúng 1 lần

    def reverse_order(self):
        """Đảo chiều thứ tự lượt (dành cho REVERSE_ORDER)."""
        self.turn_dir *= -1
        # Không đổi current_idx ngay để mượt: hiệu lực từ lượt kế tiếp

    def skip_next_for(self, symbol: str):
        """Đặt cờ bỏ qua lượt kế tiếp của symbol (SKIP_NEXT_OPPONENT)."""
        self.skip_symbol = symbol

    # ---------- Resolve & win check ----------

    def resolve_answer(
        self,
        cell,
        was_correct: bool,
        capture_symbol: Optional[str] = None,
        advance_turn: bool = True,
    ) -> Optional[str]:
        """
        Gọi khi popup/câu hỏi kết thúc cho một ô vừa được chơi.
        - Nếu was_correct:
            - Nếu capture_symbol được cung cấp -> chiếm ô theo symbol này.
            - Nếu capture_symbol không cung cấp và ô chưa có chủ -> chiếm theo current_player.
            - Nếu ô đã có chủ (do event set trước) -> KHÔNG ghi đè.
        - Kiểm tra thắng dựa trên owner hiện tại của ô (nếu có).
        - Nếu chưa có người thắng và advance_turn=True -> next_turn().

        Trả về: 'symbol' của đội thắng nếu có, ngược lại None.
        """
        # Symbol "đại diện" cho lần trả lời này (để log)
        acting_symbol = capture_symbol or self.current_player.symbol

        # Gán chủ ô nếu cần
        if was_correct:
            if capture_symbol is not None:
                # Event chỉ định ai chiếm
                cell.owner = capture_symbol
            elif cell.owner is None:
                # Trường hợp thông thường
                cell.owner = self.current_player.symbol
            # Nếu cell.owner đã có (set bởi event trước đó) thì không ghi đè.

        # Log lại nước đi
        self.match_log.append((cell.row, cell.col, acting_symbol, was_correct))

        # Kiểm tra thắng chỉ khi có chủ ô
        winner: Optional[str] = None
        if was_correct and cell.owner:
            if self._check_win_from(cell.row, cell.col, cell.owner):
                winner = cell.owner

        # Nếu chưa ai thắng, chuyển lượt (mặc định)
        if winner is None and advance_turn:
            self.next_turn()

        return winner

    def _check_win_from(self, r: int, c: int, symbol: str) -> bool:
        """Kiểm tra đủ chuỗi win_length qua (r,c) theo 4 hướng."""
        n = self.board.size
        cells = self.board.cells
        for dr, dc in DIRECTIONS:
            count = 1
            # lùi
            rr, cc = r - dr, c - dc
            while 0 <= rr < n and 0 <= cc < n and cells[rr][cc].owner == symbol:
                count += 1
                rr -= dr
                cc -= dc
            # tiến
            rr, cc = r + dr, c + dc
            while 0 <= rr < n and 0 <= cc < n and cells[rr][cc].owner == symbol:
                count += 1
                rr += dr
                cc += dc
            if count >= self.win_length:
                return True
        return False

    # ---------- Optional utilities (draw / majority) ----------

    def is_board_full(self) -> bool:
        """Bàn đã kín ô (không còn None) hay chưa."""
        for row in self.board.cells:
            for cell in row:
                if cell.owner is None:
                    return False
        return True

    def owner_counts(self) -> Dict[str, int]:
        """Đếm số ô theo owner."""
        cnt: Dict[str, int] = {}
        for row in self.board.cells:
            for cell in row:
                if cell.owner:
                    cnt[cell.owner] = cnt.get(cell.owner, 0) + 1
        return cnt

    def majority_winner(self) -> Optional[str]:
        """Trả về symbol có số ô nhiều nhất khi bàn đầy; hoà trả None."""
        counts = self.owner_counts()
        if not counts:
            return None
        # Tìm max
        items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        if len(items) == 1:
            return items[0][0]
        # Nếu top 2 bằng nhau -> hoà
        return items[0][0] if items[0][1] > items[1][1] else None
