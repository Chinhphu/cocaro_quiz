# core/question_manager.py

import json
import random
import math
import os
from typing import List, Dict, Any, Optional


class QuestionManager:
    """
    Quản lý ngân hàng câu hỏi và cách cấp phát cho game.

    - JSON kỳ vọng: list[ { "question": str, "options": [str,str,str,str], "answer": "A|B|C|D" | str } ]
    - Chia thành 2 pool:
        * used_questions   : dùng để lấp đầy bảng (ưu tiên rút trước)
        * spare_questions  : dự phòng (đổi câu, lặp click, cạn pool chính...)
    - Hiệu năng: dùng chỉ mục (O(1)) thay vì pop(0) (O(n)).
    """

    def __init__(
        self,
        json_path: str,
        event_ratio: float = 0.2,
        spare_ratio: float = 0.3,
        seed: Optional[int] = None,
        min_required: int = 9,
    ):
        self._rng = random.Random(seed)

        # raw & pools
        self._all: List[Dict[str, Any]] = []
        self.used_questions: List[Dict[str, Any]] = []
        self.spare_questions: List[Dict[str, Any]] = []

        # index pointers (O(1) phát câu)
        self._used_i = 0
        self._spare_i = 0

        # board/event stats
        self.board_size = 0
        self.total_cells = 0
        self.num_event_cells = 0

        # load & prepare
        self._load_questions(json_path, min_required)
        self._split_questions(event_ratio, spare_ratio)
        self._calculate_board_size()

    # ------------------ Load & prepare ------------------

    def _load_questions(self, json_path: str, min_required: int):
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Không tìm thấy file: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("File JSON phải là một list các câu hỏi.")
        if len(data) < min_required:
            raise ValueError(f"Phải có ít nhất {min_required} câu hỏi để chơi.")

        # Chuẩn hoá: gán qid nếu thiếu, normalize answer
        self._all = []
        for i, q in enumerate(data):
            if not isinstance(q, dict):
                continue
            qid = q.get("id", f"q{i+1}")
            question = (q.get("question") or "").strip()
            options = q.get("options") or []
            answer = q.get("answer")

            # validate cơ bản
            if not question or not isinstance(options, list) or len(options) < 2:
                continue

            # nếu có 4 đáp án, chuẩn hoá answer dạng "A/B/C/D" -> index
            norm_answer = answer
            if isinstance(answer, str) and len(answer) == 1 and answer.upper() in "ABCD":
                norm_answer = "ABCD".index(answer.upper())

            self._all.append({
                "id": qid,
                "question": question,
                "options": options,
                "answer": norm_answer,
            })

        if len(self._all) < min_required:
            raise ValueError(f"Ngân hàng sau khi chuẩn hoá còn {len(self._all)} câu (< {min_required}).")

    def _split_questions(self, event_ratio: float, spare_ratio: float):
        total = len(self._all)
        spare_count = int(total * spare_ratio)
        used_count = max(0, total - spare_count)

        shuffled = self._all[:]  # copy
        self._rng.shuffle(shuffled)

        self.used_questions = shuffled[:used_count]
        self.spare_questions = shuffled[used_count:]

        # số ô sự kiện tính theo used_count nhưng không vượt used_count
        self.num_event_cells = min(used_count, max(0, int(used_count * event_ratio)))

        # reset pointers
        self._used_i = 0
        self._spare_i = 0

    def _calculate_board_size(self):
        self.total_cells = len(self.used_questions)
        # kích thước cạnh đủ chứa total_cells
        self.board_size = math.ceil(math.sqrt(max(1, self.total_cells)))

    # ------------------ Public API (giữ nguyên chữ ký cũ) ------------------

    def get_board_size(self) -> int:
        return self.board_size

    def get_total_cells(self) -> int:
        return self.total_cells

    def get_event_cell_count(self) -> int:
        return self.num_event_cells

    def get_question(self) -> Optional[Dict[str, Any]]:
        """
        Rút một câu cho ô thường hoặc ô sự kiện cần hỏi.
        Ưu tiên pool 'used_questions', khi hết sẽ sang 'spare_questions'.
        """
        if self._used_i < len(self.used_questions):
            q = self.used_questions[self._used_i]
            self._used_i += 1
            return q
        if self._spare_i < len(self.spare_questions):
            q = self.spare_questions[self._spare_i]
            self._spare_i += 1
            return q
        return None

    def get_spare_question(self) -> Optional[Dict[str, Any]]:
        """Rút trực tiếp từ pool dự phòng (ví dụ cho đổi câu)."""
        if self._spare_i < len(self.spare_questions):
            q = self.spare_questions[self._spare_i]
            self._spare_i += 1
            return q
        return None

    # ------------------ Helpers/diagnostics ------------------

    def remaining_used(self) -> int:
        return max(0, len(self.used_questions) - self._used_i)

    def remaining_spare(self) -> int:
        return max(0, len(self.spare_questions) - self._spare_i)

    def is_exhausted(self) -> bool:
        """Hết sạch cả used + spare."""
        return self.remaining_used() == 0 and self.remaining_spare() == 0
