# visualization.py
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from game_state import GameState, Snake
import logging
import numpy as np
from threading import Lock


class Visualization:
    def __init__(self, initial_game_state: GameState, my_snake: Snake):
        self.game_state = initial_game_state
        self.my_snake = my_snake

        # Замок для безопасного обновления данных из разных потоков
        self.lock = Lock()

        # Создаем окно
        self.app = pg.mkQApp("3D Snake Visualization")
        self.window = gl.GLViewWidget()
        self.window.opts["distance"] = 500
        self.window.show()
        self.window.setWindowTitle("3D Snake Game Visualization")

        # Добавляем сетку (опционально)
        grid = gl.GLGridItem()
        grid.scale(10, 10, 10)
        grid.setDepthValue(10)  # Размещаем сетку за всеми объектами
        self.window.addItem(grid)

        # Создаем объекты для отрисовки
        self.fences = gl.GLScatterPlotItem()
        self.food = gl.GLScatterPlotItem()
        self.enemies = gl.GLScatterPlotItem()
        self.snake = gl.GLScatterPlotItem()

        self.window.addItem(self.fences)
        self.window.addItem(self.food)
        self.window.addItem(self.enemies)
        self.window.addItem(self.snake)

        # Настраиваем начальные данные
        self.update_visualization(initial_game_state, my_snake)

    def update_visualization(self, game_state: GameState, my_snake: Snake):
        with self.lock:
            self.game_state = game_state
            self.my_snake = my_snake

            # Обновляем заборы
            fences = game_state.fences
            if fences:
                fence_positions = np.array([[f.x, f.y, f.z] for f in fences])
                self.fences.setData(pos=fence_positions, color=(0, 0, 0, 1), size=5)
            else:
                self.fences.setData(pos=[], color=[], size=[])

            # Обновляем мандарины
            foods = game_state.food
            if foods:
                food_positions = np.array(
                    [[food.c.x, food.c.y, food.c.z] for food in foods]
                )
                self.food.setData(pos=food_positions, color=(1, 1, 0, 1), size=10)
            else:
                self.food.setData(pos=[], color=[], size=[])

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
                    [[segment.x, segment.y, segment.z] for segment in enemy_segments]
                )
                self.enemies.setData(pos=enemy_positions, color=(1, 0, 0, 1), size=8)
            else:
                self.enemies.setData(pos=[], color=[], size=[])

            # Обновляем вашу змейку
            snake_segments = my_snake.geometry
            if snake_segments:
                snake_positions = np.array(
                    [[segment.x, segment.y, segment.z] for segment in snake_segments]
                )
                self.snake.setData(pos=snake_positions, color=(1, 0.5, 0, 1), size=10)
            else:
                self.snake.setData(pos=[], color=[], size=[])

    def start(self):
        # Запускаем приложение в отдельном потоке
        import threading

        thread = threading.Thread(target=self.app.exec_)
        thread.daemon = True
        thread.start()
