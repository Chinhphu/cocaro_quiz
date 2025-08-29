# core/player.py
class Player:
    def __init__(self, name: str, symbol: str, color_rgb: tuple):
        self.name = name        # "Đội A"
        self.symbol = symbol    # "A".."F"
        self.color = color_rgb  # (R,G,B) - hiện chưa dùng, để sau
        self.score = 0

    def reset(self):
        self.score = 0
