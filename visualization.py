# visualization.py
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from game_state import GameState, Snake


class Visualization:
    def __init__(self, game_state: GameState, my_snake: Snake):
        self.game_state = game_state
        self.my_snake = my_snake

    def plot(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        # Настройки осей
        max_x, max_y, max_z = self.game_state.map_size
        ax.set_xlim(0, max_x)
        ax.set_ylim(0, max_y)
        ax.set_zlim(0, max_z)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title("Состояние игры 3D Snake")

        # Отрисовка заборов (fences)
        for fence in self.game_state.fences:
            ax.scatter(
                fence.x, fence.y, fence.z, c="black", marker="s", s=20, label="Fence"
            )

        # Отрисовка мандаринов (food)
        for food in self.game_state.food:
            ax.scatter(
                food.c.x, food.c.y, food.c.z, c="yellow", marker="o", s=50, label="Food"
            )

        # Отрисовка змей соперников (enemies)
        for enemy in self.game_state.enemies:
            if enemy.status == "alive":
                for segment in enemy.geometry:
                    ax.scatter(
                        segment.x,
                        segment.y,
                        segment.z,
                        c="red",
                        marker="^",
                        s=30,
                        label="Enemy",
                    )

        # Отрисовка вашей змеи (my_snake)
        for idx, segment in enumerate(self.my_snake.geometry):
            color = "orange"
            marker = "o"
            size = 100 if idx == 0 else 50  # Голова крупнее
            ax.scatter(
                segment.x,
                segment.y,
                segment.z,
                c=color,
                marker=marker,
                s=size,
                label="My Snake",
            )

        # Чтобы избежать дублирования меток в легенде
        handles, labels = ax.get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        ax.legend(unique.values(), unique.keys())

        plt.show()
