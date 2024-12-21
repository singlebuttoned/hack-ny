# test_visualization.py
import sys
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from OpenGL.GL import *
from PyQt5.QtWidgets import QApplication
import numpy as np


def main():
    # Создаём приложение Qt
    app = QApplication(sys.argv)

    # Создаём окно визуализации
    view = gl.GLViewWidget()
    view.opts["distance"] = 400  # Расстояние камеры
    view.show()
    view.setWindowTitle("3D Visualization Test")

    # Добавляем сетку (опционально)
    grid = gl.GLGridItem()
    grid.scale(10, 10, 10)
    grid.setDepthValue(10)  # Размещаем сетку за объектами
    view.addItem(grid)

    # Создаём 3D маркеры (точки)
    # Пример: Куб из точек
    cube_coords = [
        [1, 1, 1],
        [-1, 1, 1],
        [-1, -1, 1],
        [1, -1, 1],
        [1, 1, -1],
        [-1, 1, -1],
        [-1, -1, -1],
        [1, -1, -1],
    ]
    cube_coords = np.array(cube_coords) * 50  # Масштабирование куба

    # Линии для отображения ребер куба
    lines = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
        [4, 5],
        [5, 6],
        [6, 7],
        [7, 4],
        [0, 4],
        [1, 5],
        [2, 6],
        [3, 7],
    ]
    for line in lines:
        pts = cube_coords[line]
        plt = gl.GLLinePlotItem(pos=pts, color=(1, 1, 1, 1), width=2, antialias=True)
        view.addItem(plt)

    # Добавляем несколько маркеров в виде точек
    pos = np.random.normal(size=(100, 3)) * 100  # Случайные точки
    colors = np.ones((100, 4))
    colors[:, :3] = np.random.rand(100, 3)  # Случайные цвета
    markers = gl.GLScatterPlotItem(pos=pos, color=colors, size=5, pxMode=False)
    view.addItem(markers)

    # Запускаем приложение
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
