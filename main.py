"""Запускает настольную игру «Астероиды» командой python main.py."""

import time
import tkinter as tk

import settings as cfg
from model import Game
from view import View


class App:
    """Связать события окна, физический цикл и отрисовку игры."""

    def __init__(self, root):
        """Подготовить окно, модель и обработчики клавиатуры и мыши."""
        self.root = root
        self.root.title("Астероиды")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            root, width=cfg.WIDTH, height=cfg.HEIGHT,
            highlightthickness=0, borderwidth=0, takefocus=True,
        )
        self.canvas.pack()
        self.game = Game()
        self.view = View(self.canvas)
        self.keys = set()
        self.accumulator = 0.0
        self.start_time = self.last_frame = time.perf_counter()
        self.canvas.bind("<Button-1>", self._click)
        self.root.bind("<KeyPress>", self._press)
        self.root.bind("<KeyRelease>", self._release)
        self.canvas.bind("<FocusOut>", self._clear_keys)
        self.canvas.focus_set()

    def _click(self, event):
        """Начать партию при левом щелчке внутри заставки."""
        left, top, right, bottom = cfg.PANEL
        in_panel = left <= event.x <= right and top <= event.y <= bottom
        if not self.game.active and in_panel:
            self.keys.clear()
            self.game.start()
            self.canvas.focus_set()

    def _press(self, event):
        """Запомнить клавишу и выстрелить при нажатии пробела."""
        key = event.keysym
        if self.game.active and key in cfg.CONTROL_KEYS:
            if key == "space" and key not in self.keys:
                self.game.shoot()
            self.keys.add(key)

    def _release(self, event):
        """Убрать отпущенную клавишу из набора команд."""
        self.keys.discard(event.keysym)

    def _clear_keys(self, _event):
        """Сбросить команды при потере фокуса игрового поля."""
        self.keys.clear()

    def _tick(self):
        """Обновить физику фиксированными шагами и отрисовать кадр."""
        now = time.perf_counter()
        self.accumulator += min(now - self.last_frame, cfg.MAX_FRAME_TIME)
        self.last_frame = now
        while self.accumulator >= cfg.STEP:
            self.game.step(self.keys, cfg.STEP)
            self.accumulator -= cfg.STEP
        self.view.render(self.game, now - self.start_time)
        self.root.after(cfg.FRAME_MS, self._tick)

    def run(self):
        """Запустить цикл отрисовки и обработку событий Tk."""
        self._tick()
        self.root.mainloop()


def main():
    """Создать приложение и открыть окно игры."""
    App(tk.Tk()).run()


if __name__ == "__main__":
    main()
