"""Хранит параметры окна, управления, физики и анимации."""

# Размеры игрового поля, шаг физики и частота отрисовки.
WIDTH = 800
HEIGHT = 600
STEP = 1 / 120
FRAME_MS = 16
MAX_FRAME_TIME = 0.1

# Размеры центральной заставки и прямоугольник для начала партии.
PANEL_WIDTH = 400
PANEL_HEIGHT = 300
PANEL = (
    (WIDTH - PANEL_WIDTH) // 2,
    (HEIGHT - PANEL_HEIGHT) // 2,
    (WIDTH + PANEL_WIDTH) // 2,
    (HEIGHT + PANEL_HEIGHT) // 2,
)

# Запас жизней, радиус столкновения и длина носовой части корабля.
START_LIVES = 3
SHIP_RADIUS = 14
SHIP_NOSE = 23
SHIP_DRAW_RADIUS = 34

# Угловая скорость в рад/с, ускорение и торможение в пикс./с².
TURN_SPEED = 3.6
THRUST = 370
DRAG = 145
MAX_SHIP_SPEED = 355

# Параметры ракеты, дальность полёта и очки за попадание.
ROCKET_SPEED = 620
ROCKET_RADIUS = 3
ROCKET_LIFE = 0.82 * min(WIDTH, HEIGHT) / ROCKET_SPEED
POINTS_PER_HIT = 1

# Частота появления, размеры и диапазоны скоростей астероидов.
FIRST_SPAWN_DELAY = 0.52
SPAWN_INTERVAL = 0.96
ASTEROID_RADIUS = (19, 42)
ASTEROID_SPEED = (38, 126)
ASTEROID_SPIN = (0.35, 2.2)
ASTEROID_VARIANTS = 3

# Вход с края: отклонение от нормали и запас в радиусах астероида.
ENTRY_ANGLE = (-25, 25)
ENTRY_MARGIN = 1.25

# Скорость фонового слоя и параметры спрайтовой таблицы взрыва.
BACKGROUND_SPEED = 21
BACKGROUND_OPACITY = 132
BACKGROUND_COUNT = 29
BACKGROUND_RADII = (6, 8, 10, 13, 17)
EXPLOSION_FRAMES = 12
EXPLOSION_FRAME_TIME = 0.045
EXPLOSION_TILE = 112

# Размеры и углы спрайтов. Строки атласа сгруппированы по размерам.
ROCK_TILE = 92
ROCK_ANGLES = 24
ROCK_RADII = (20, 24, 29, 34, 39, 43)

# Семя даёт воспроизводимый фон и взрывы независимо от хода партии.
ART_SEED = 9164

# Клавиши, которые отслеживает приложение.
CONTROL_KEYS = frozenset(("Left", "Right", "Up", "space"))
