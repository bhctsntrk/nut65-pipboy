"""5x5 bitmap pixel font for LED matrix text rendering.

Each character is a list of 5 integers (one per row, 5 rows tall).
Bits represent columns (5 cols wide), LSB = leftmost pixel.
Characters are rendered with 1-column gap between them.

Hand-tuned for readability on a keyboard LED matrix.
"""

# fmt: off
FONT: dict[str, list[int]] = {
    " ": [0, 0, 0, 0, 0],
    "A": [14, 17, 31, 17, 17],
    "B": [15, 17, 15, 17, 15],
    "C": [14, 17, 1, 17, 14],
    "D": [15, 17, 17, 17, 15],
    "E": [31, 1, 15, 1, 31],
    "F": [31, 1, 15, 1, 1],
    "G": [14, 1, 25, 17, 14],
    "H": [17, 17, 31, 17, 17],
    "I": [14, 4, 4, 4, 14],
    "J": [16, 16, 16, 17, 14],
    "K": [17, 9, 7, 9, 17],
    "L": [1, 1, 1, 1, 31],
    "M": [17, 27, 21, 17, 17],
    "N": [17, 19, 21, 25, 17],
    "O": [14, 17, 17, 17, 14],
    "P": [15, 17, 15, 1, 1],
    "Q": [14, 17, 17, 25, 30],
    "R": [15, 17, 15, 9, 17],
    "S": [30, 1, 14, 16, 15],
    "T": [31, 4, 4, 4, 4],
    "U": [17, 17, 17, 17, 14],
    "V": [17, 17, 17, 10, 4],
    "W": [17, 17, 21, 27, 17],
    "X": [17, 10, 4, 10, 17],
    "Y": [17, 10, 4, 4, 4],
    "Z": [31, 8, 4, 2, 31],
    "0": [14, 17, 17, 17, 14],
    "1": [4, 6, 4, 4, 14],
    "2": [14, 16, 14, 1, 31],
    "3": [14, 16, 12, 16, 14],
    "4": [17, 17, 31, 16, 16],
    "5": [31, 1, 15, 16, 15],
    "6": [14, 1, 15, 17, 14],
    "7": [31, 16, 8, 4, 4],
    "8": [14, 17, 14, 17, 14],
    "9": [14, 17, 30, 16, 14],
    "!": [4, 4, 4, 0, 4],
    "?": [14, 16, 12, 0, 4],
    ".": [0, 0, 0, 0, 4],
    ",": [0, 0, 0, 4, 2],
    ":": [0, 4, 0, 4, 0],
    "-": [0, 0, 14, 0, 0],
    "%": [19, 8, 4, 2, 25],
    "/": [16, 8, 4, 2, 1],
}
# fmt: on

CHAR_WIDTH = 5
CHAR_GAP = 1
CHAR_HEIGHT = 5


def text_to_columns(text: str) -> list[list[bool]]:
    """Convert text to a list of columns (each column is 5 booleans, top to bottom)."""
    columns: list[list[bool]] = []
    for i, ch in enumerate(text.upper()):
        glyph = FONT.get(ch, FONT[" "])
        for col_idx in range(CHAR_WIDTH):
            column = []
            for row_idx in range(CHAR_HEIGHT):
                pixel = bool(glyph[row_idx] & (1 << col_idx))
                column.append(pixel)
            columns.append(column)
        if i < len(text) - 1:
            columns.append([False] * CHAR_HEIGHT)
    return columns
