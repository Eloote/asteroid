"""Рисует оригинальную графику, интерфейс и кадры взрыва в Tk."""

import base64
import math
import random
import struct
import tkinter as tk
import zlib
from pathlib import Path

import settings as cfg


ASSETS = Path(__file__).resolve().with_name("assets")

# Контуры деталей корабля в локальной системе координат.
SHIP_HULL = (
    (cfg.SHIP_NOSE, 0), (12, -5), (-2, -7), (-14, -15),
    (-19, -12), (-15, -5), (-17, 0), (-15, 5), (-19, 12),
    (-14, 15), (-2, 7), (12, 5),
)
SHIP_WING_UP = ((1, -6), (-13, -13), (-16, -11), (-10, -4))
SHIP_WING_DOWN = ((1, 6), (-13, 13), (-16, 11), (-10, 4))
SHIP_SPINE = ((20, 0), (7, -4), (-10, -4), (-15, 0), (-10, 4), (7, 4))
SHIP_COCKPIT = ((13, 0), (7, -2), (1, -2), (-3, 0), (1, 2), (7, 2))
SHIP_FLAME = ((-13, -5), (-23, -6), (-34, 0), (-23, 6), (-13, 5))
FLAME_CORE = ((-15, -3), (-22, -3), (-29, 0), (-22, 3), (-15, 3))


def polygon_points(x, y, angle, points):
    """Повернуть локальные вершины и вернуть координаты для Canvas."""
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return [
        coord
        for px, py in points
        for coord in (
            x + px * cosine - py * sine,
            y + px * sine + py * cosine,
        )
    ]


def wrapped_centers(x, y, radius):
    """Выдать центр и видимые копии спрайта у сторон и в углах поля."""
    offsets_x = [0]
    offsets_y = [0]
    if x < radius:
        offsets_x.append(cfg.WIDTH)
    if x > cfg.WIDTH - radius:
        offsets_x.append(-cfg.WIDTH)
    if y < radius:
        offsets_y.append(cfg.HEIGHT)
    if y > cfg.HEIGHT - radius:
        offsets_y.append(-cfg.HEIGHT)
    for dx in offsets_x:
        for dy in offsets_y:
            yield x + dx, y + dy


def png_image(master, width, height, pixels):
    """Преобразовать RGBA-буфер в изображение Tk с альфа-каналом."""
    def chunk(kind, payload):
        """Упаковать секцию PNG с длиной и контрольной суммой."""
        crc = zlib.crc32(kind + payload)
        return (
            struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", crc)
        )

    stride = width * 4
    scanlines = b"".join(
        b"\x00" + pixels[start:start + stride]
        for start in range(0, len(pixels), stride)
    )
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b"")
    )
    return tk.PhotoImage(master=master, data=base64.b64encode(data))


def atlas_tile(master, sheet, column, row, size):
    """Вырезать квадратный кадр из столбца и строки атласа."""
    tile = tk.PhotoImage(master=master, width=size, height=size)
    x = column * size
    y = row * size
    tile.tk.call(
        str(tile), "copy", str(sheet), "-from", x, y, x + size, y + size,
    )
    return tile


def panel_image(master):
    """Создать полупрозрачное стекло заставки с фиолетовым градиентом."""
    pixels = bytearray()
    for y in range(cfg.PANEL_HEIGHT):
        level = y / (cfg.PANEL_HEIGHT - 1)
        color = bytes((28 + int(20 * level), 19, 91, 123 + int(level * 32)))
        pixels.extend(color * cfg.PANEL_WIDTH)
    return png_image(master, cfg.PANEL_WIDTH, cfg.PANEL_HEIGHT, pixels)


def explosion_frames(master):
    """Собрать атлас из квадратных тайлов и вырезать кадры взрыва."""
    size = cfg.EXPLOSION_TILE
    width = size * cfg.EXPLOSION_FRAMES
    atlas = bytearray(width * size * 4)
    center = size / 2
    rng = random.Random(cfg.ART_SEED)
    sparks = [
        (rng.uniform(0, math.tau), rng.uniform(0.52, 1.0))
        for _ in range(18)
    ]
    for frame in range(cfg.EXPLOSION_FRAMES):
        progress = frame / (cfg.EXPLOSION_FRAMES - 1)
        ring = 6 + progress * (center - 10)
        glow = (1 - progress) ** 0.58
        origin = frame * size
        for y in range(size):
            for x in range(size):
                dx, dy = x - center, y - center
                angle = math.atan2(dy, dx)
                noise = math.sin(7 * angle + progress) * 0.11
                noise += math.sin(13 * angle - 4 * progress) * 0.06
                distance = math.hypot(dx, dy) / (1 + noise)
                core_size = ring * 0.70 + 2
                core = max(0.0, 1 - distance / core_size)
                edge = max(0.0, 1 - abs(distance - core_size) / 7)
                shock = max(0.0, 1 - abs(distance - ring) / 3)
                fire = max(core**0.55 * glow, edge * glow * 0.74)
                blue = shock * glow * 0.63
                if fire >= blue:
                    green = int(123 + 132 * core**0.46)
                    blue_channel = int(36 + 219 * core**1.25)
                    color = (255, green, blue_channel)
                    alpha = int(250 * fire)
                else:
                    color = (86, 114, 255)
                    alpha = int(241 * blue)
                index = (y * width + origin + x) * 4
                atlas[index:index + 4] = bytes((*color, alpha))
        for angle, speed in sparks:
            distance = (ring + 5) * speed
            x = round(center + math.cos(angle) * distance)
            y = round(center + math.sin(angle) * distance)
            for dy in (0, 1):
                for dx in (0, 1, 2):
                    index = ((y + dy) * width + origin + x + dx) * 4
                    atlas[index:index + 4] = bytes((
                        255, 224, 137, int(245 * glow),
                    ))

    sheet = png_image(master, width, size, atlas)
    return [
        atlas_tile(master, sheet, frame, 0, size)
        for frame in range(cfg.EXPLOSION_FRAMES)
    ]


class View:
    """Создать слои поля и отрисовывать текущее состояние партии."""

    def __init__(self, canvas):
        """Подготовить фон, спрайты и элементы счёта."""
        self.canvas = canvas
        self.sky = tk.PhotoImage(master=canvas, file=ASSETS / "nebula.png")
        self.rock_sheet = tk.PhotoImage(
            master=canvas, file=ASSETS / "asteroids.png",
        )
        self.rock_frames = {}
        self.panel = panel_image(canvas)
        self.frames = explosion_frames(canvas)
        self.drift = self._make_background()
        self.hud = self._make_hud()

    def render(self, game, elapsed):
        """Обновить фон, игровые объекты, заставку и счётчики."""
        self.canvas.delete("scene")
        for x, y, radius, items in self.drift:
            left = (x - elapsed * cfg.BACKGROUND_SPEED) % cfg.WIDTH
            for item, offset in zip(items, (-cfg.WIDTH, 0, cfg.WIDTH)):
                self.canvas.coords(item, left + offset, y)
                visible = -radius <= left + offset <= cfg.WIDTH + radius
                self.canvas.itemconfigure(
                    item, state="normal" if visible else "hidden"
                )

        if game.active:
            for asteroid in game.asteroids:
                self._draw_asteroid(asteroid)
            for rocket in game.rockets:
                self._draw_rocket(rocket)
            self._draw_ship(game.ship)
        if not game.active:
            self._draw_panel(game.finished)
        for explosion in game.explosions:
            image = self.frames[explosion.frame]
            for x, y in wrapped_centers(
                explosion.x, explosion.y, cfg.EXPLOSION_TILE / 2
            ):
                self.canvas.create_image(x, y, image=image, tags="scene")

        score, lives = self.hud
        labels = (f"Очки: {game.score}", f"Жизни: {game.lives}")
        for items, text in zip((score, lives), labels):
            for item in items:
                self.canvas.itemconfigure(item, text=text)
        self.canvas.tag_raise("hud")

    def _make_background(self):
        """Нарисовать неподвижное звёздное поле и создать слой обломков."""
        canvas = self.canvas
        canvas.create_image(0, 0, image=self.sky, anchor="nw")
        rng = random.Random(cfg.ART_SEED)
        row = len(cfg.ROCK_RADII) * cfg.ASTEROID_VARIANTS
        drift = []
        for index in range(cfg.BACKGROUND_COUNT):
            column = rng.choices(range(len(cfg.BACKGROUND_RADII)),
                                 weights=(8, 6, 5, 3, 1))[0]
            radius = cfg.BACKGROUND_RADII[column] + 2
            image = self._rock_tile(column, row)
            x = (index + rng.random()) * cfg.WIDTH / cfg.BACKGROUND_COUNT
            y = rng.randrange(cfg.HEIGHT)
            items = tuple(
                canvas.create_image(0, y, image=image) for _ in range(3)
            )
            drift.append((x, y, radius, items))
        return drift

    def _make_hud(self):
        """Создать зелёные счётчики с тёмной тенью у верхнего края."""
        canvas = self.canvas
        return tuple(
            tuple(
                canvas.create_text(
                    x + offset, 19 + offset, fill=color, tags="hud",
                    font=("Arial", -27),
                )
                for offset, color in ((2, "#071407"), (0, "#37ff38"))
            )
            for x in (cfg.WIDTH - 135, 126)
        )

    def _draw_panel(self, finished):
        """Нарисовать центральную заставку для начала или повтора."""
        canvas = self.canvas
        left, top, right, bottom = cfg.PANEL
        x = (left + right) / 2
        canvas.create_image(
            left, top, image=self.panel, anchor="nw", tags="scene",
        )
        canvas.create_rectangle(
            left + 1, top + 1, right - 1, bottom - 1,
            outline="#465c9f", width=3, tags="scene",
        )
        title = "АСТЕРОИДЫ"
        title_y = top + 124
        title_options = {
            "text": title, "font": ("Arial Black", -48, "bold italic"),
            "tags": "scene",
        }
        for color, radius in (("#292457", 7), ("#6b76bd", 5),
                              ("#b4c5ef", 2)):
            for index in range(8):
                angle = index * math.tau / 8
                canvas.create_text(
                    x + radius * math.cos(angle),
                    title_y + radius * math.sin(angle), fill=color,
                    **title_options,
                )
        canvas.create_text(
            x, title_y, fill="#272940", **title_options,
        )
        canvas.create_text(
            x, title_y - 2, fill="#edf3ff", **title_options,
        )
        prompt = "Играть снова" if finished else "Нажмите, чтобы начать"
        for offset, color in ((2, "#120f36"), (0, "#f4f7ff")):
            canvas.create_text(
                x + offset, top + 191 + offset,
                text=prompt, fill=color, font=("Arial", -18, "bold"),
                tags="scene",
            )
        if finished:
            canvas.create_text(
                x, top + 233, text="Партия окончена", fill="#c8d3f2",
                font=("Arial", -15), tags="scene",
            )

    def _rock_tile(self, column, row):
        """Вернуть кадр астероида, вырезая его при первом обращении."""
        key = column, row
        if key not in self.rock_frames:
            self.rock_frames[key] = atlas_tile(
                self.canvas, self.rock_sheet, column, row, cfg.ROCK_TILE,
            )
        return self.rock_frames[key]

    def _draw_ship(self, ship):
        """Показать металлический корабль в режиме полёта или тяги."""
        layers = [
            (SHIP_HULL, "#596479", "#252437"),
            (SHIP_WING_UP, "#ccd7df", "#a6b3c9"),
            (SHIP_WING_DOWN, "#8d9db0", "#586984"),
            (SHIP_SPINE, "#b5c1d3", "#7a889d"),
            (SHIP_COCKPIT, "#2258a7", "#57b5ff"),
        ]
        if ship.thrusting:
            layers[:0] = [
                (SHIP_FLAME, "#9b3fea", ""),
                (FLAME_CORE, "#ffd3ff", "#fb7e94"),
            ]
        for x, y in wrapped_centers(ship.x, ship.y, cfg.SHIP_DRAW_RADIUS):
            for shape, color, outline in layers:
                points = polygon_points(x, y, ship.angle, shape)
                self.canvas.create_polygon(
                    *points, fill=color, outline=outline, tags="scene",
                )
            for side in (-1, 1):
                accent = polygon_points(
                    x, y, ship.angle, ((-12, 11 * side), (-5, 7 * side)),
                )
                self.canvas.create_line(
                    *accent, fill="#db715b", width=2, tags="scene",
                )

    def _draw_asteroid(self, asteroid):
        """Выбрать кадр по радиусу и ориентации и показать копии у края."""
        radius_index, radius = min(
            enumerate(cfg.ROCK_RADII),
            key=lambda item: abs(item[1] - asteroid.radius),
        )
        row = radius_index * cfg.ASTEROID_VARIANTS + asteroid.variant
        frame = round(asteroid.angle * cfg.ROCK_ANGLES / math.tau)
        image = self._rock_tile(frame % cfg.ROCK_ANGLES, row)
        if asteroid.entering:
            centers = ((asteroid.x, asteroid.y),)
        else:
            centers = wrapped_centers(asteroid.x, asteroid.y, radius * 1.10)
        for x, y in centers:
            self.canvas.create_image(x, y, image=image, tags="scene")

    def _draw_rocket(self, rocket):
        """Нарисовать ракету и короткий светящийся след вдоль курса."""
        for x, y in wrapped_centers(rocket.x, rocket.y, 14):
            points = polygon_points(
                x, y, rocket.angle, ((-9, 0), (3, 0)),
            )
            self.canvas.create_line(
                *points, fill="#ff962e", width=3, tags="scene",
            )
            self.canvas.create_oval(
                x - 2, y - 2, x + 2, y + 2, fill="#fff4a2",
                width=0, tags="scene",
            )
