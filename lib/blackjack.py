import random
import cv2
import numpy as np
import random as rnd
import math
from typing import Literal
from lib.init import blackjack_assets_folder_path, blackjack_videos_folder_path
from lib.opencv_custom_writer import OpencvCustomWriter

table = cv2.imread(blackjack_assets_folder_path / "background.jpg", cv2.IMREAD_UNCHANGED)
table = cv2.resize(table, (int(table.shape[0] / 5), int(table.shape[1] / 5)))

table_w, table_h = table.shape[1], table.shape[0]
table_c = table_w // 2, table_h // 2

cards: dict[str, np.ndarray] = {}
for suit in ["C", "D", "H", "S"]:
    for idx in range(1, 14):
        card_id = f"{suit}{idx}"
        card_ = cv2.imread(blackjack_assets_folder_path / f"cards/{card_id}.png", cv2.IMREAD_UNCHANGED)
        cards[card_id] = cv2.resize(card_, (card_.shape[1] * 3, card_.shape[0] * 3))

card_back = cv2.imread(blackjack_assets_folder_path / "cards/1.png", cv2.IMREAD_UNCHANGED)
card_back = cv2.resize(card_back, (card_back.shape[1] * 3, card_back.shape[0] * 3))
card_size = card_back.shape[1], card_back.shape[0]


def cv2_paste_with_alpha(background, foreground, pos):
    x, y = pos
    fg_h, fg_w = foreground.shape[:2]
    roi = background[y:y + fg_h, x:x + fg_w]

    if foreground.shape[2] == 4:
        alpha = foreground[:, :, 3] / 255.0
        for c in range(3):
            roi[:, :, c] = (1 - alpha) * roi[:, :, c] + alpha * foreground[:, :, c]
    else:
        roi[:] = foreground

    background[y:y + fg_h, x:x + fg_w] = roi


def draw_card(frame: np.ndarray, target_pos: tuple[int, int], card: str | None = None, progress: float = 1.0):
    if card is None:
        card_front = card_back
    else:
        card_front = cards[card]

    flip_prog = max(0.0, min(1.0, progress))
    scale = abs(1 - 2 * flip_prog)  # 1 → 0 → 1
    if scale < 0.05:
        scale = 0.05

    cur_w = int(card_size[0] * scale)
    cur_card = card_back if flip_prog < 0.5 else card_front

    resized = cv2.resize(cur_card, (cur_w, card_size[1]), interpolation=cv2.INTER_NEAREST)

    x = target_pos[0] + (card_size[0] - cur_w) // 2
    y = target_pos[1]
    cv2_paste_with_alpha(frame, resized, (x, y))


def get_pos(number: int):
    border_pad = 10
    start_height = 400
    card_pad_h = math.floor(((table_h - start_height) - border_pad - card_size[1]) / 11)
    card_pad_w = math.floor((table_w - border_pad * 2 - card_size[0]) / 11)
    return border_pad + number * card_pad_w, start_height + number * card_pad_h


def get_anim_pos(start: tuple[int, int], end: tuple[int, int], progress: float) -> tuple[int, int]:
    progress = max(0.0, min(1.0, progress))
    rel = end[0] - start[0], end[1] - start[1]
    return math.floor(start[0] + rel[0] * progress), math.floor(start[1] + rel[1] * progress)


def calculate_score(hand: list[str]) -> int:
    score = 0
    ace_count = 0
    for card in hand:
        val = min(10, int(card[1:]))
        if val == 1:
            ace_count += 1
        else:
            score += val

    for i in range(ace_count):
        if score + 11 <= 21:
            score += 11
        else:
            score += 1

    return score


class Blackjack:
    def __init__(self):
        self.deck: set[str] = set(cards.keys())
        self.dealer_hand: list[str] = []
        self.player_hand: list[str] = []
        self.fps = 50

    def get_random_card(self) -> str:
        card = rnd.choice(tuple(self.deck))
        self.deck.remove(card)
        return card

    def write_frames(self, frames: list[np.ndarray]) -> str:
        blackjack_videos_folder_path.mkdir(exist_ok=True)
        filename = blackjack_videos_folder_path / f"{random.randint(0, 1 << 31)}.mp4"
        with OpencvCustomWriter(self.fps, table_w, table_h, filename) as writer:
            for frame in frames:
                writer.write(frame)
        return filename

    def start(self) -> str:
        self.dealer_hand.append('S2')
        self.dealer_hand.append('H2')
        self.player_hand.append(self.get_random_card())
        self.player_hand.append(self.get_random_card())
        return self.write_frames(self.render_initial())

    def hit(self) -> tuple[str, bool]:
        new_card = self.get_random_card()
        filename = self.write_frames(self.render_hit(new_card))
        self.player_hand.append(new_card)
        score = calculate_score(self.player_hand)
        return filename, score > 21

    def stand(self) -> tuple[str, Literal["win", "draw", "lose"]]:
        player_score = calculate_score(self.player_hand)
        dealer_score = calculate_score(self.dealer_hand)

        while dealer_score < 17:
            self.dealer_hand.append(self.get_random_card())
            dealer_score = calculate_score(self.dealer_hand)

        filename = self.write_frames(self.render_stand())

        if dealer_score > 21 or dealer_score < player_score:
            return filename, "win"
        elif dealer_score == player_score:
            return filename, "draw"
        else:
            return filename, "lose"

    def render_stand(self) -> list[np.ndarray]:
        card_pad = card_size[0]
        start_pos = math.floor((table_w - card_pad * len(self.dealer_hand)) / 2)

        if start_pos < 0:
            card_pad = math.floor((table_w - card_size[0]) / (len(self.dealer_hand) - 1))
            start_pos = 0

        frames = []
        for frame_i in range(len(self.dealer_hand) * 31):
            frame = table.copy()
            self.render_hands(frame, dealer=False)
            for j, card in enumerate(self.dealer_hand):
                if j > 1 and j * 31 > frame_i:
                    continue

                i = frame_i % 31
                target_pos = start_pos + card_pad * j, 100
                if (j + 1) * 31 <= frame_i:
                    progress = 1
                elif j == 0:
                    target_pos = get_anim_pos((table_c[0] - card_size[0], 100), target_pos, i / 30)
                    progress = 1
                elif j == 1:
                    if j * 31 > frame_i:
                        target_pos = get_anim_pos((table_c[0], 100), target_pos, i / 30)
                        progress = 0
                    else:
                        progress = i / 30
                else:
                    target_pos = get_anim_pos((table_w - card_size[0], 100), target_pos, i / 30)
                    progress = i / 30

                draw_card(frame, target_pos, card, progress=progress)

            # cv2.imshow("frame", frame)
            # cv2.waitKey(10)
            frames.append(frame)
        return frames

    def render_hit(self, new_card: str) -> list[np.ndarray]:
        frames = []
        for i in range(31):
            frame = table.copy()
            self.render_hands(frame)
            draw_card(frame, get_pos(len(self.player_hand)), new_card, progress=i / 30)

            frames.append(frame)
        return frames

    def render_initial(self) -> list[np.ndarray]:
        frames = []
        for i in range(56):
            frame = table.copy()
            self.render_hands(frame, i)

            frames.append(frame)
        return frames

    def render_hands(self, frame: np.ndarray, i: int | None = None, dealer=True):
        opening = i is not None

        if dealer:
            progress = (i - 5) / 20 if opening else 1
            draw_card(frame, (table_c[0] - card_size[0], 100), self.dealer_hand[0], progress)
            draw_card(frame, (table_c[0], 100))

        for j, card in enumerate(self.player_hand):
            draw_card(frame, get_pos(j), card, (i - 5 * (j + 4)) / 30 if opening else 1)


def main():
    blackjack = Blackjack()
    print(blackjack.start())

    while True:
        val = input("hit or stand:")
        if val == "hit":
            filename, lose = blackjack.hit()
            print(filename)
            if lose:
                print("You defeated!")
                break
        elif val == "stand":
            print(blackjack.stand())
        else:
            break


if __name__ == '__main__':
    main()
