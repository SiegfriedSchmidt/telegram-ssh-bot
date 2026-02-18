from io import BytesIO
from lib.init import fonts_folder_path
from PIL import Image, ImageDraw, ImageFont
import pyte

CELL_WIDTH = 10
CELL_HEIGHT = 18
FONT_SIZE = 16


def resolve_color(value):
    # Named colors from pyte
    NAMED = {
        "black": 0,
        "red": 1,
        "green": 2,
        "brown": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
    }

    if value in NAMED:
        return xterm_to_rgb(NAMED[value])

    if value.isdigit():
        return xterm_to_rgb(int(value))

    return 200, 200, 200


def xterm_to_rgb(n):
    # Standard ANSI colors
    if 0 <= n <= 15:
        ansi = [
            (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
            (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
            (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
            (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)
        ]
        return ansi[n]

    # 6×6×6 color cube
    if 16 <= n <= 231:
        n -= 16
        r = (n // 36) % 6
        g = (n // 6) % 6
        b = n % 6
        return (
            55 + r * 40 if r else 0,
            55 + g * 40 if g else 0,
            55 + b * 40 if b else 0
        )

    # Grayscale ramp
    if 232 <= n <= 255:
        gray = 8 + (n - 232) * 10
        return gray, gray, gray

    return 255, 255, 255


class EmulatedTerminal:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.screen = pyte.Screen(self.width, self.height)
        self.stream = pyte.ByteStream(self.screen)

    def feed(self, chunk: bytes):
        self.stream.feed(chunk)

    def render(self) -> BytesIO:
        width = self.screen.columns * CELL_WIDTH
        height = self.screen.lines * CELL_HEIGHT

        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Use a monospaced font
        font = ImageFont.truetype(fonts_folder_path / "JetBrainsMonoNL-Bold.ttf", FONT_SIZE)

        for y in range(self.screen.lines):
            for x in range(self.screen.columns):
                char = self.screen.buffer[y].get(x)

                if not char:
                    continue

                # --- Foreground ---
                if char.fg != "default":
                    fg_color = resolve_color(char.fg)
                else:
                    fg_color = (200, 200, 200)

                # --- Background ---
                if char.bg != "default":
                    bg_color = resolve_color(char.bg)
                else:
                    bg_color = (0, 0, 0)

                px = x * CELL_WIDTH
                py = y * CELL_HEIGHT

                # Draw background rectangle
                draw.rectangle(
                    [px, py, px + CELL_WIDTH, py + CELL_HEIGHT],
                    fill=bg_color
                )

                # Draw character
                draw.text(
                    (px, py),
                    char.data,
                    font=font,
                    fill=fg_color
                )

        # Draw cursor (if visible)
        if not self.screen.cursor.hidden:
            cx = self.screen.cursor.x
            cy = self.screen.cursor.y

            if 0 <= cx < self.screen.columns and 0 <= cy < self.screen.lines:
                px = cx * CELL_WIDTH
                py = cy * CELL_HEIGHT

                # Simple block cursor
                draw.rectangle(
                    [px, py, px + CELL_WIDTH, py + CELL_HEIGHT],
                    outline=(255, 255, 255),
                    width=1
                )

        bio = BytesIO()
        image.save(bio, 'PNG')
        bio.seek(0)
        return bio

    def text(self) -> str:
        return '\n'.join(self.screen.display)
