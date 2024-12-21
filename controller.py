# controller.py
import sys
import threading
from typing import List
from game_state import GameState, Snake, Enemy, Food, Point3D
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from threading import Lock


class Controller(QObject):
    # Сигнал для обновления визуализации
    update_signal = pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        self.game_state = None
        self.my_snake = None
        self.lock = Lock()
        self.current_direction = [0, 0, 0]  # Изначально без движения

        # Создаём приложение Qt
        self.app = QApplication(sys.argv)
        self.window = gl.GLViewWidget()
        self.window.setWindowTitle("3D Snake Controller")
        self.window.setGeometry(100, 100, 800, 600)
        self.window.opts["distance"] = 500  # Расстояние камеры
        self.window.show()

        # Добавляем сетку (опционально)
        grid = gl.GLGridItem()
        grid.scale(10, 10, 10)
        grid.setDepthValue(10)  # Размещаем сетку за всеми объектами
        self.window.addItem(grid)

        # Добавляем координатные оси
        self.axes = gl.GLLinePlotItem()
        self.add_axes([0, 0, 0])  # Начальная позиция
        self.window.addItem(self.axes)

        # Создаём объекты для отрисовки
        self.fences = gl.GLScatterPlotItem()
        self.food = gl.GLScatterPlotItem()
        self.enemies = gl.GLScatterPlotItem()
        self.snake = gl.GLScatterPlotItem()

        # Добавляем объекты на сцену
        self.window.addItem(self.fences)
        self.window.addItem(self.food)
        self.window.addItem(self.enemies)
        self.window.addItem(self.snake)

        # Подключаем сигнал для обновления визуализации
        self.update_signal.connect(self.update_visualization)

        # Устанавливаем обработчик нажатий клавиш
        self.window.keyPressEvent = self.key_press_event

        # Запускаем поток Qt приложения
        self.thread = threading.Thread(target=self.start_app, daemon=True)
        self.thread.start()

    def add_axes(self, position):
        """Добавляет координатные оси, исходящие из заданной позиции."""
        length = 20  # Длина осей

        # Ось X (Красная)
        x_axis = np.array([position, [position[0] + length, position[1], position[2]]])
        # Ось Y (Зелёная)
        y_axis = np.array([position, [position[0], position[1] + length, position[2]]])
        # Ось Z (Синяя)
        z_axis = np.array([position, [position[0], position[1], position[2] + length]])

        # Объединяем все оси в один массив
        axes_data = np.vstack([x_axis, y_axis, z_axis])

        # Цвета для осей: X - красный, Y - зелёный, Z - синий
        colors = np.array(
            [
                [1, 0, 0, 1],  # X
                [1, 0, 0, 1],
                [0, 1, 0, 1],  # Y
                [0, 1, 0, 1],
                [0, 0, 1, 1],  # Z
                [0, 0, 1, 1],
            ]
        )

        self.axes.setData(pos=axes_data, color=colors, width=2, antialias=True)

    def start_app(self):
        """Запускает цикл приложения Qt."""
        self.app.exec_()

    def request_move(self, game_state: GameState, my_snake: Snake) -> List[int]:
        """Обновляет состояние игры и возвращает текущее направление движения."""
        with self.lock:
            self.game_state = game_state
            self.my_snake = my_snake

            # Обновляем визуализацию
            self.update_signal.emit(game_state, my_snake)

            # Возвращаем текущее направление
            return self.current_direction

    def update_visualization(self, game_state: GameState, my_snake: Snake):
        """Обновляет объекты на сцене на основе текущего состояния игры."""
        with self.lock:
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

                # Устанавливаем фокус камеры на голову змеи
                snake_head = snake_positions[0]  # Первая точка — голова змеи
                self.window.opts["center"] = pg.Vector(
                    snake_head[0], snake_head[1], snake_head[2]
                )

                # Обновляем координатные оси, исходя из головы змеи
                self.window.removeItem(self.axes)
                self.add_axes(snake_head)
                self.window.addItem(self.axes)

            else:
                self.snake.setData(
                    pos=np.empty((0, 3)), color=np.empty((0, 4)), size=np.empty((0,))
                )

    def key_press_event(self, event):
        """Обрабатывает нажатия клавиш для управления направлением."""
        key = event.key()
        with self.lock:
            if key == Qt.Key_Left:
                self.current_direction = [-1, 0, 0]
            elif key == Qt.Key_Right:
                self.current_direction = [1, 0, 0]
            elif key == Qt.Key_Up:
                self.current_direction = [0, 1, 0]
            elif key == Qt.Key_Down:
                self.current_direction = [0, -1, 0]
            elif key == Qt.Key_PageUp:
                self.current_direction = [0, 0, 1]
            elif key == Qt.Key_PageDown:
                self.current_direction = [0, 0, -1]

    def move(self, game_state: GameState, my_snake: Snake) -> List[int]:
        """
        Возвращает направление, выбранное пользователем.

        :param game_state: Текущее состояние игры
        :param my_snake: Ваша змейка
        :return: Список из трёх целых чисел, представляющих направление [x, y, z]
        """
        return self.request_move(game_state, my_snake)
