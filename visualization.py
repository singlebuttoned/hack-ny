# visualization.py
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from game_state import GameState, Snake
import logging
from threading import Lock
from PyQt5.QtCore import QObject, pyqtSignal


class Visualization(QObject):
    update_signal = pyqtSignal(object, object)


    def __init__(self):
        super().__init__()
        self.game_state = None
        self.my_snake = None
        self.lock = Lock()
        self.target = None

        # Создаём сигнал для обновления данных
        self.update_signal.connect(self.update_visualization)

        # Инициализируем приложение Qt
        self.app = pg.mkQApp("3D Snake Visualization")
        self.window = gl.GLViewWidget()
        self.window.opts["distance"] = 500  # Расстояние камеры
        self.window.show()
        self.window.setWindowTitle("3D Snake Game Visualization")

        # Добавляем сетку (опционально)
        grid = gl.GLGridItem()
        grid.scale(10, 10, 10)
        grid.setDepthValue(10)  # Размещаем сетку за всеми объектами
        self.window.addItem(grid)

        # Создаём объекты для отрисовки
        self.fences = gl.GLScatterPlotItem()
        self.food = gl.GLScatterPlotItem()
        self.enemies = gl.GLScatterPlotItem()
        self.snake = gl.GLScatterPlotItem()

        # **Инициализируем объект для отображения цели**
        self.target_marker = gl.GLScatterPlotItem()

        # Добавляем объекты на сцену
        self.window.addItem(self.fences)
        self.window.addItem(self.food)
        self.window.addItem(self.enemies)
        self.window.addItem(self.snake)
        self.window.addItem(self.target_marker)  # Добавляем после инициализации

    def start(self):
        # Запускаем приложение Qt
        pg.exec()

    def request_update(self, game_state: GameState, my_snake: Snake):
        # Посылаем сигнал для обновления данных в главном потоке
        self.update_signal.emit(game_state, my_snake)

    def update_visualization(self, game_state: GameState, my_snake: Snake):
        with self.lock:
            self.game_state = game_state
            self.my_snake = my_snake
            # self

            # Обновляем заборы
            fences = game_state.fences
            if fences:
                fence_positions = np.array(
                    [[f.x, f.y, f.z] for f in fences], dtype=np.float32
                )
                self.fences.setData(pos=fence_positions, color=(0.5, 0, 0.5, 1), size=5)
            else:
                self.fences.setData(
                    pos=np.empty((0, 3)), color=np.empty((0, 4)), size=np.empty((0,))
                )

            # Обновляем мандарины
            foods = game_state.food
            if foods:
                food_positions = np.array(
                    [[food.c.x, food.c.y, food.c.z] for food in foods], dtype=np.float32
                )
                self.food.setData(pos=food_positions, color=(1, 1, 0, 1), size=10)
            else:
                self.food.setData(
                    pos=np.empty((0, 3)), color=np.empty((0, 4)), size=np.empty((0,))
                )

            # Обновляем врагов
            enemies = game_state.enemies
            enemy_segments = [
                segment
                for enemy in enemies
                if enemy.status == "alive"
                for segment in enemy.geometry
            ]
            if enemy_segments:
                enemy_positions = np.array(
                    [[segment.x, segment.y, segment.z] for segment in enemy_segments],
                    dtype=np.float32,
                )
                self.enemies.setData(pos=enemy_positions, color=(1, 0, 0, 1), size=8)
            else:
                self.enemies.setData(
                    pos=np.empty((0, 3)), color=np.empty((0, 4)), size=np.empty((0,))
                )

            # Обновляем вашу змейку
            snake_segments = my_snake.geometry
            if snake_segments:
                snake_positions = np.array(
                    [[segment.x, segment.y, segment.z] for segment in snake_segments],
                    dtype=np.float32,
                )
                self.snake.setData(pos=snake_positions, color=(0, 1, 0, 1), size=10)
            else:
                self.snake.setData(
                    pos=np.empty((0, 3)), color=np.empty((0, 4)), size=np.empty((0,))
                )

            target = self.target
            if target:
                target_position = np.array([[target.c.x, target.c.y, target.c.z]], dtype=np.float32)
                self.target_marker.setData(pos=target_position, color=(0, 0, 1, 1), size=22)
            else:
                self.target_marker.setData(
                    pos=np.empty((0, 3)), color=np.empty((0, 4)), size=np.empty((0,))
                )