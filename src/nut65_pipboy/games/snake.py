"""Snake AI engine — Greedy + tail-escape BFS on a 15x5 grid.

The snake chases food via BFS shortest path, but only commits if it can
still reach its own tail afterward (safety check). Falls back to stalling
toward the tail if no safe path exists.
"""

from __future__ import annotations

import random
from collections import deque
from typing import override

from nut65_pipboy.keyboard import COLS, VALID_POSITIONS
from nut65_pipboy.types import HueSat

from .base import COLOR_OFF, FrameGrid, GameEngine, empty_frame

# Play area: rows 0-3 only (row 4 has spacebar gaps, row 5 = light bar)
PLAY_ROWS = 4
PLAY_COLS = COLS  # 15

# Valid cells for the snake (exclude row 4+ and missing matrix positions)
PLAY_CELLS: frozenset[tuple[int, int]] = frozenset(
    (r, c) for r, c in VALID_POSITIONS if r < PLAY_ROWS
)

COLOR_FOOD = HueSat(hue=0, sat=255)       # red (always)
COLOR_FLASH = HueSat(hue=0, sat=255)

DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # right, left, down, up


def _neighbors(pos: tuple[int, int]) -> list[tuple[int, int]]:
    r, c = pos
    return [(r + dr, c + dc) for dr, dc in DIRECTIONS if (r + dr, c + dc) in PLAY_CELLS]


def _bfs(start: tuple[int, int], goal: tuple[int, int], blocked: set[tuple[int, int]]) -> list[tuple[int, int]] | None:
    """BFS shortest path from start to goal, avoiding blocked cells."""
    if start == goal:
        return [start]
    queue: deque[tuple[tuple[int, int], list[tuple[int, int]]]] = deque([(start, [start])])
    visited = {start}
    while queue:
        pos, path = queue.popleft()
        for nb in _neighbors(pos):
            if nb in visited or nb in blocked:
                continue
            new_path = path + [nb]
            if nb == goal:
                return new_path
            visited.add(nb)
            queue.append((nb, new_path))
    return None


def _longest_path_toward(start: tuple[int, int], goal: tuple[int, int], blocked: set[tuple[int, int]]) -> tuple[int, int] | None:
    """Pick the neighbor of start that is farthest from goal (stalling)."""
    best_move = None
    best_dist = -1
    for nb in _neighbors(start):
        if nb in blocked:
            continue
        dist = abs(nb[0] - goal[0]) + abs(nb[1] - goal[1])
        # Prefer moves that keep more space available
        if dist > best_dist:
            best_dist = dist
            best_move = nb
    return best_move


class SnakeGame(GameEngine):
    def __init__(self) -> None:
        super().__init__()
        self._snake: deque[tuple[int, int]] = deque()
        self._food: tuple[int, int] = (0, 0)
        self._game_over = False
        self._death_timer = 0
        self.reset()

    @override
    def reset(self) -> None:
        mid_r, mid_c = PLAY_ROWS // 2, PLAY_COLS // 2
        self._snake = deque([(mid_r, mid_c), (mid_r, mid_c - 1), (mid_r, mid_c - 2)])
        self._game_over = False
        self._death_timer = 0
        self._spawn_food()

    def _spawn_food(self) -> None:
        snake_set = set(self._snake)
        free = [c for c in PLAY_CELLS if c not in snake_set]
        if free:
            self._food = random.choice(free)
        else:
            self._game_over = True

    @property
    @override
    def score(self) -> int:
        return len(self._snake)

    @property
    @override
    def game_over(self) -> bool:
        return self._game_over

    @override
    def tick(self) -> None:
        if self._game_over:
            self._death_timer += 1
            if self._death_timer >= 12:  # ~1s at 12fps
                self.reset()
            return

        head = self._snake[0]
        snake_body = set(self._snake)
        # The tail will move, so it's not blocked for pathfinding
        tail = self._snake[-1]
        blocked = snake_body - {tail}

        next_move = self._find_safe_move(head, blocked, tail)

        if next_move is None:
            # No valid move — game over
            self._game_over = True
            return

        # Move snake
        self._snake.appendleft(next_move)
        if next_move == self._food:
            self._spawn_food()  # grow (don't remove tail)
        else:
            self._snake.pop()

    def _find_safe_move(self, head: tuple[int, int], blocked: set[tuple[int, int]], tail: tuple[int, int]) -> tuple[int, int] | None:
        # Strategy 1: BFS to food, verify tail reachability after eating
        path_to_food = _bfs(head, self._food, blocked)
        if path_to_food and len(path_to_food) > 1:
            candidate = path_to_food[1]
            # Simulate: after moving to candidate, can we still reach the tail?
            sim_blocked = blocked | {candidate}
            # If we'd eat food, snake grows so tail stays
            if candidate == self._food:
                sim_tail = tail
            else:
                sim_tail = self._snake[-2] if len(self._snake) > 1 else tail
            if _bfs(candidate, sim_tail, sim_blocked - {sim_tail}) is not None:
                return candidate

        # Strategy 2: Follow longest path toward tail (stall for space)
        stall = _longest_path_toward(head, tail, blocked)
        if stall is not None:
            return stall

        # Strategy 3: Any valid neighbor
        for nb in _neighbors(head):
            if nb not in blocked:
                return nb

        return None

    @override
    def render(self) -> FrameGrid:
        frame = empty_frame()

        # Clear play area
        for r, c in PLAY_CELLS:
            frame[r][c] = COLOR_OFF

        if self._game_over:
            # Brief red flash then fade to off
            color = COLOR_FLASH if self._death_timer < 4 else COLOR_OFF
            for r, c in PLAY_CELLS:
                frame[r][c] = color
        else:
            # Food
            frame[self._food[0]][self._food[1]] = COLOR_FOOD

            # Snake body — uses self.hue from color palette
            color_body = HueSat(self.hue, 255)
            color_head = HueSat((self.hue + 20) % 256, 255)
            for i, (r, c) in enumerate(self._snake):
                frame[r][c] = color_head if i == 0 else color_body

        # Light bar (row 5): snake length progress
        bar_fill = min(15, int(len(self._snake) / len(PLAY_CELLS) * 15))
        color_bar = HueSat(self.hue, 255)
        for c in range(COLS):
            if (5, c) in VALID_POSITIONS:
                frame[5][c] = color_bar if c < bar_fill else COLOR_OFF

        return frame
