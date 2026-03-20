"""Pong AI engine — two imperfect AI paddles on a 15x5 grid.

Ball bounces off walls and paddles. AI tracks ball with delay and occasional
random offset for visual interest. Score shown on light bar.
"""

from __future__ import annotations

import random
from typing import override

from nut65_pipboy.keyboard import COLS, VALID_POSITIONS
from nut65_pipboy.types import HueSat

from .base import COLOR_OFF, FrameGrid, GameEngine, empty_frame

# Pong uses rows 0-4 (row 4 gaps are fine for paddles/ball, unlike snake's grid)
PLAY_ROWS = 5
PLAY_COLS = COLS

PADDLE_HEIGHT = 2
MAX_SCORE = 7


class PongGame(GameEngine):
    def __init__(self) -> None:
        super().__init__()
        self._left_y = 1
        self._right_y = 1
        self._ball_r = 2.0
        self._ball_c = 7.0
        self._vel_r = 0.0
        self._vel_c = 1.0
        self._left_score = 0
        self._right_score = 0
        self._game_over = False
        self._pause_timer = 0
        self.reset()

    @override
    def reset(self) -> None:
        self._left_y = 1
        self._right_y = 1
        self._game_over = False
        self._left_score = 0
        self._right_score = 0
        self._serve()

    def _serve(self) -> None:
        self._ball_r = 2.0
        self._ball_c = 7.0
        self._vel_r = random.choice([-0.5, 0.0, 0.5])
        self._vel_c = random.choice([-1.0, 1.0])
        self._pause_timer = 12  # 1 second pause before serve

    @property
    @override
    def score(self) -> int:
        return self._left_score * 10 + self._right_score

    @property
    @override
    def game_over(self) -> bool:
        return self._game_over

    @override
    def tick(self) -> None:
        if self._pause_timer > 0:
            self._pause_timer -= 1
            return

        if self._game_over:
            self._pause_timer += 1
            if self._pause_timer >= 36:  # 3s pause then restart
                self.reset()
            return

        # Move AI paddles (imperfect tracking)
        self._move_paddle_ai()

        # Move ball
        self._ball_r += self._vel_r
        self._ball_c += self._vel_c

        # Bounce off top/bottom walls
        if self._ball_r < 0:
            self._ball_r = -self._ball_r
            self._vel_r = abs(self._vel_r)
        elif self._ball_r >= PLAY_ROWS:
            self._ball_r = 2 * PLAY_ROWS - 2 - self._ball_r
            self._vel_r = -abs(self._vel_r)

        ball_row = int(round(self._ball_r))
        ball_col = int(round(self._ball_c))

        # Check left paddle collision (col 0)
        if ball_col <= 1 and self._vel_c < 0:
            if self._left_y <= ball_row < self._left_y + PADDLE_HEIGHT:
                self._vel_c = abs(self._vel_c)
                # Add spin based on hit position
                hit_offset = ball_row - self._left_y - 1
                self._vel_r = hit_offset * 0.5
                self._ball_c = 1.5
            elif ball_col <= 0:
                # Left missed — right scores
                self._right_score += 1
                self._check_game_over()
                self._serve()
                return

        # Check right paddle collision (col 14)
        if ball_col >= PLAY_COLS - 2 and self._vel_c > 0:
            if self._right_y <= ball_row < self._right_y + PADDLE_HEIGHT:
                self._vel_c = -abs(self._vel_c)
                hit_offset = ball_row - self._right_y - 1
                self._vel_r = hit_offset * 0.5
                self._ball_c = PLAY_COLS - 2.5
            elif ball_col >= PLAY_COLS - 1:
                # Right missed — left scores
                self._left_score += 1
                self._check_game_over()
                self._serve()
                return

    def _move_paddle_ai(self) -> None:
        ball_row = int(round(self._ball_r))

        # Left paddle: tracks ball with slight delay + random jitter
        target_left = ball_row - PADDLE_HEIGHT // 2
        if self._vel_c < 0:  # ball coming toward left
            target_left += random.randint(-1, 1)
        if self._left_y < target_left:
            self._left_y = min(self._left_y + 1, PLAY_ROWS - PADDLE_HEIGHT)
        elif self._left_y > target_left:
            self._left_y = max(self._left_y - 1, 0)

        # Right paddle: slightly worse tracking
        target_right = ball_row - PADDLE_HEIGHT // 2
        if self._vel_c > 0:  # ball coming toward right
            target_right += random.randint(-1, 1)
        if random.random() < 0.15:  # 15% chance of no movement (sluggish)
            return
        if self._right_y < target_right:
            self._right_y = min(self._right_y + 1, PLAY_ROWS - PADDLE_HEIGHT)
        elif self._right_y > target_right:
            self._right_y = max(self._right_y - 1, 0)

    def _check_game_over(self) -> None:
        if self._left_score >= MAX_SCORE or self._right_score >= MAX_SCORE:
            self._game_over = True
            self._pause_timer = 0

    @override
    def render(self) -> FrameGrid:
        frame = empty_frame()

        # Clear play area
        for r in range(PLAY_ROWS):
            for c in range(PLAY_COLS):
                if (r, c) in VALID_POSITIONS:
                    frame[r][c] = COLOR_OFF

        color_paddle = HueSat(self.hue, 255)
        color_ball = HueSat((self.hue + 128) % 256, 255)
        color_net = HueSat(self.hue, 40)

        # Center net (col 7, dim)
        for r in range(PLAY_ROWS):
            if (r, 7) in VALID_POSITIONS:
                frame[r][7] = color_net

        # Left paddle (col 0)
        for dr in range(PADDLE_HEIGHT):
            pr = self._left_y + dr
            if 0 <= pr < PLAY_ROWS and (pr, 0) in VALID_POSITIONS:
                frame[pr][0] = color_paddle

        # Right paddle (col 14)
        for dr in range(PADDLE_HEIGHT):
            pr = self._right_y + dr
            if 0 <= pr < PLAY_ROWS and (pr, 14) in VALID_POSITIONS:
                frame[pr][14] = color_paddle

        # Ball
        br = max(0, min(PLAY_ROWS - 1, int(round(self._ball_r))))
        bc = max(0, min(PLAY_COLS - 1, int(round(self._ball_c))))
        if (br, bc) in VALID_POSITIONS:
            frame[br][bc] = color_ball

        # Light bar (row 5): score display
        color_left = HueSat(self.hue, 200)
        color_right = HueSat((self.hue + 128) % 256, 200)
        for c in range(COLS):
            if (5, c) not in VALID_POSITIONS:
                continue
            if c < 7:
                frame[5][c] = color_left if c < self._left_score else COLOR_OFF
            elif c == 7:
                frame[5][c] = COLOR_OFF
            else:
                frame[5][c] = color_right if (14 - c) < self._right_score else COLOR_OFF

        return frame
