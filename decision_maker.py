# decision_maker.py
import logging
from typing import List, Optional
from game_state import GameState, Snake, Food, Point3D


class DecisionMaker:
    def __init__(self):
        pass

    def decide_move(self, game_state: GameState, my_snake: Snake) -> List[int]:
        logging.debug("Начало процесса принятия решения")
        head = my_snake.geometry[0]
        logging.debug(f"Позиция головы змеи: ({head.x}, {head.y}, {head.z})")

        # Найдём ближайший мандарин по Манхэттену
        target = self.find_closest_food(head, game_state.food)
        if not target:
            logging.debug(
                "Мандарины не найдены, продолжаем двигаться текущим направлением"
            )
            return (
                my_snake.direction
            )  # Если мандаринов нет, продолжаем движение текущим направлением

        logging.debug(
            f"Цель: мандарин на позиции ({target.c.x}, {target.c.y}, {target.c.z})"
        )
        direction = self.get_direction_vector(head, target.c)
        logging.debug(f"Решённое направление: {direction}")
        return direction

    def find_closest_food(self, head: Point3D, food_list: List[Food]) -> Optional[Food]:
        min_distance = float("inf")
        closest_food = None
        for food in food_list:
            distance = (
                abs(food.c.x - head.x) + abs(food.c.y - head.y) + abs(food.c.z - head.z)
            )
            logging.debug(
                f"Мандарин на ({food.c.x}, {food.c.y}, {food.c.z}) Расстояние: {distance}"
            )
            if distance < min_distance:
                min_distance = distance
                closest_food = food
        return closest_food

    def get_direction_vector(self, head: Point3D, target: Point3D) -> List[int]:
        direction = [0, 0, 0]
        if head.x < target.x:
            direction[0] = 1
        elif head.x > target.x:
            direction[0] = -1
        elif head.y < target.y:
            direction[1] = 1
        elif head.y > target.y:
            direction[1] = -1
        elif head.z < target.z:
            direction[2] = 1
        elif head.z > target.z:
            direction[2] = -1
        return direction
