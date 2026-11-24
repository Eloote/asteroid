"""Моделирует движение, столкновения и состояние партии без Tk."""

import math
import random
from dataclasses import dataclass

import settings as cfg


def torus_distance(ax, ay, bx, by):
    """Вернуть кратчайшее расстояние между двумя точками на торе."""
    # На каждой оси выбираем ближайшую периодическую копию точки.
    dx = (ax - bx + cfg.WIDTH / 2) % cfg.WIDTH - cfg.WIDTH / 2
    dy = (ay - by + cfg.HEIGHT / 2) % cfg.HEIGHT - cfg.HEIGHT / 2
    return math.hypot(dx, dy)


@dataclass
class Body:
    """Хранить положение, ориентацию и скорости движущегося тела."""

    x: float
    y: float
    angle: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    spin: float = 0.0
    radius: float = 0.0

    def move(self, dt):
        """Продвинуть тело на dt секунд с переносом через границы."""
        self.x = (self.x + self.vx * dt) % cfg.WIDTH
        self.y = (self.y + self.vy * dt) % cfg.HEIGHT
        self.angle = (self.angle + self.spin * dt) % math.tau

    def touches(self, other):
        """Проверить пересечение окружностей двух тел на торе."""
        distance = torus_distance(self.x, self.y, other.x, other.y)
        return distance <= self.radius + other.radius


@dataclass
class Ship(Body):
    """Хранить состояние двигателя и применять команды пилота."""

    thrusting: bool = False

    def steer(self, keys, dt):
        """Повернуть корабль и изменить скорость за dt секунд."""
        turn = int("Right" in keys) - int("Left" in keys)
        self.spin = turn * cfg.TURN_SPEED
        self.angle = (self.angle + self.spin * dt) % math.tau
        self.thrusting = "Up" in keys

        speed = math.hypot(self.vx, self.vy)
        if self.thrusting:
            self.vx += math.cos(self.angle) * cfg.THRUST * dt
            self.vy += math.sin(self.angle) * cfg.THRUST * dt
            speed = math.hypot(self.vx, self.vy)
            target = min(cfg.MAX_SHIP_SPEED, speed)
        else:
            target = max(0.0, speed - cfg.DRAG * dt)

        # Масштабирование вектора меняет его длину и сохраняет курс.
        if speed:
            self.vx *= target / speed
            self.vy *= target / speed

        self.x = (self.x + self.vx * dt) % cfg.WIDTH
        self.y = (self.y + self.vy * dt) % cfg.HEIGHT

    def launch(self):
        """Создать ракету у носа с заданной скоростью вдоль курса."""
        dx = math.cos(self.angle)
        dy = math.sin(self.angle)
        return Rocket(
            x=(self.x + cfg.SHIP_NOSE * dx) % cfg.WIDTH,
            y=(self.y + cfg.SHIP_NOSE * dy) % cfg.HEIGHT,
            angle=self.angle,
            vx=cfg.ROCKET_SPEED * dx,
            vy=cfg.ROCKET_SPEED * dy,
            radius=cfg.ROCKET_RADIUS,
        )


@dataclass
class Rocket(Body):
    """Хранить оставшееся время полёта ракеты."""

    remaining: float = cfg.ROCKET_LIFE


@dataclass
class Asteroid(Body):
    """Хранить состояние входа на поле и вариант поверхности."""

    variant: int = 0
    entering: bool = False

    def move(self, dt):
        """Ввести астероид с края, затем двигать его по тору."""
        if not self.entering:
            super().move(dt)
            return

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle = (self.angle + self.spin * dt) % math.tau
        margin = self.radius * cfg.ENTRY_MARGIN
        if (margin <= self.x <= cfg.WIDTH - margin
                and margin <= self.y <= cfg.HEIGHT - margin):
            self.entering = False

    def touches(self, other):
        """Проверить столкновение без переноса до завершения входа."""
        if not self.entering:
            return super().touches(other)

        distance = math.hypot(self.x - other.x, self.y - other.y)
        return distance <= self.radius + other.radius


@dataclass
class Explosion:
    """Хранить положение и текущий кадр взрыва."""

    x: float
    y: float
    age: float = 0.0

    @property
    def frame(self):
        """Вернуть индекс кадра, соответствующего возрасту взрыва."""
        return int(self.age / cfg.EXPLOSION_FRAME_TIME)


class Game:
    """Вести счёт, создавать объекты и разрешать столкновения."""

    def __init__(self, rng=None):
        """Показать начальную заставку с пустым игровым полем."""
        self.rng = rng if rng is not None else random.Random()
        self.active = False
        self.finished = False
        self.score = 0
        self.lives = cfg.START_LIVES
        self.ship = None
        self.asteroids = []
        self.rockets = []
        self.explosions = []
        self.spawn_in = cfg.FIRST_SPAWN_DELAY

    def start(self):
        """Сбросить счёт и поместить неподвижный корабль в центр поля."""
        self.active = True
        self.finished = False
        self.score = 0
        self.lives = cfg.START_LIVES
        self.ship = self._new_ship()
        self.asteroids.clear()
        self.rockets.clear()
        self.explosions.clear()
        self.spawn_in = cfg.FIRST_SPAWN_DELAY

    def shoot(self):
        """Выпустить ракету во время активной партии."""
        if self.active:
            self.rockets.append(self.ship.launch())

    def step(self, keys, dt):
        """Обновить модель за один шаг, заданный в секундах."""
        for explosion in self.explosions:
            explosion.age += dt
        self.explosions[:] = [
            item for item in self.explosions
            if item.frame < cfg.EXPLOSION_FRAMES
        ]
        if not self.active:
            return

        self.ship.steer(keys, dt)
        self.spawn_in -= dt
        if self.spawn_in <= 0:
            self.asteroids.append(self._new_asteroid())
            self.spawn_in += cfg.SPAWN_INTERVAL

        for asteroid in self.asteroids:
            asteroid.move(dt)
        for rocket in self.rockets:
            rocket.move(min(dt, rocket.remaining))
            rocket.remaining -= dt
        self._check_hits()
        self.rockets[:] = [
            rocket for rocket in self.rockets if rocket.remaining > 0
        ]

    @staticmethod
    def _new_ship():
        """Создать неподвижный корабль в центре носом вверх."""
        return Ship(
            cfg.WIDTH / 2,
            cfg.HEIGHT / 2,
            angle=-math.pi / 2,
            radius=cfg.SHIP_RADIUS,
        )

    def _new_asteroid(self):
        """Создать астероид за случайной стороной с курсом внутрь."""
        radius = self.rng.uniform(*cfg.ASTEROID_RADIUS)
        margin = radius * cfg.ENTRY_MARGIN
        vertical_edge = self.rng.choice((True, False))
        inward = self.rng.choice((-1, 1))
        direction = math.radians(self.rng.uniform(*cfg.ENTRY_ANGLE))
        speed = self.rng.uniform(*cfg.ASTEROID_SPEED)
        normal_speed = inward * math.cos(direction) * speed
        tangent_speed = math.sin(direction) * speed
        # Оставляем место для бокового смещения до полного входа.
        inset = 2 * margin
        if vertical_edge:
            x = -margin if inward > 0 else cfg.WIDTH + margin
            y = self.rng.uniform(inset, cfg.HEIGHT - inset)
            vx, vy = normal_speed, tangent_speed
        else:
            x = self.rng.uniform(inset, cfg.WIDTH - inset)
            y = -margin if inward > 0 else cfg.HEIGHT + margin
            vx, vy = tangent_speed, normal_speed
        spin = self.rng.uniform(*cfg.ASTEROID_SPIN)
        return Asteroid(
            x=x,
            y=y,
            angle=self.rng.uniform(0, math.tau),
            vx=vx,
            vy=vy,
            spin=spin * self.rng.choice((-1, 1)),
            radius=radius,
            variant=self.rng.randrange(cfg.ASTEROID_VARIANTS),
            entering=True,
        )

    def _break_asteroid(self, asteroid):
        """Удалить астероид и начать взрыв в его центре."""
        self.asteroids.remove(asteroid)
        self.explosions.append(Explosion(asteroid.x, asteroid.y))

    def _check_hits(self):
        """Обработать попадания ракет, затем столкновение корабля."""
        for rocket in self.rockets[:]:
            for asteroid in self.asteroids:
                if asteroid.touches(rocket):
                    self._break_asteroid(asteroid)
                    self.rockets.remove(rocket)
                    self.score += cfg.POINTS_PER_HIT
                    break

        for asteroid in self.asteroids:
            if asteroid.touches(self.ship):
                self._break_asteroid(asteroid)
                # При нуле запасных жизней следующее попадание последнее.
                if self.lives == 0:
                    self.active = False
                    self.finished = True
                    self.ship = None
                    self.asteroids.clear()
                    self.rockets.clear()
                else:
                    self.lives -= 1
                    self.ship = self._new_ship()
                break
