# decision_maker.py
import logging
from typing import List, Optional
from game_state import GameState, Snake, Food, Point3D, Strategy
from enum import Enum


class DecisionMaker:
    def __init__(self, strategy: Strategy = Strategy.BASIC):
        self.strategy = strategy
        logging.info(f"Стратегия принятия решений: {self.strategy.name}")

    def decide_move(self, game_state: GameState, my_snake: Snake) -> List[int]:
        if self.strategy == Strategy.BASIC:
            return self.basic_strategy(game_state, my_snake)
        elif self.strategy == Strategy.ADVANCED:
            return self.advanced_strategy(game_state, my_snake)
        else:
            logging.warning("Неизвестная стратегия. Используем BASIC.")
            return self.basic_strategy(game_state, my_snake)

    def basic_strategy(self, game_state: GameState, my_snake: Snake) -> List[int]:
        logging.info("Используется BASIC стратегия.")
        head = my_snake.geometry[0]
        logging.info(f"Позиция головы змеи: ({head.x}, {head.y}, {head.z})")

        # Найдем ближайший мандарин по Манхэттену
        target = self.find_closest_food(head, game_state.food)
        if not target:
            logging.info(
                "Мандарины не найдены, продолжаем двигаться текущим направлением"
            )
            return (
                my_snake.direction
            )  # Если мандаринов нет, продолжаем движение текущим направлением

        logging.info(
            f"Цель: мандарин на позиции ({target.c.x}, {target.c.y}, {target.c.z})"
        )
        direction = self.get_direction_vector(head, target.c)
        logging.info(f"Решённое направление: {direction}")
        return direction

    def advanced_strategy(self, game_state: GameState, my_snake: Snake) -> List[int]:
        logging.info("Используется ADVANCED стратегия.")
        head = my_snake.geometry[0]
        logging.info(f"Позиция головы змеи: ({head.x}, {head.y}, {head.z})")

        # Возможные направления движения
        possible_directions = [
            [1, 0, 0],  # +x
            [-1, 0, 0],  # -x
            [0, 1, 0],  # +y
            [0, -1, 0],  # -y
            [0, 0, 1],  # +z
            [0, 0, -1],  # -z
        ]

        # Получить позиции препятствий и врагов
        obstacle_positions = {tuple([f.x, f.y, f.z]) for f in game_state.fences}
        enemy_positions = {
            tuple([segment.x, segment.y, segment.z])
            for enemy in game_state.enemies
            if enemy.status == "alive"
            for segment in enemy.geometry
        }

        # Получить ближайшего врага для оценки безопасности
        closest_enemy_distance = self.get_closest_distance(head, enemy_positions)

        # Получить ближайший мандарин для оценки полезности направления
        closest_food_distance = self.get_closest_distance_advanced(
            head, game_state.food
        )

        direction_scores = {}

        for direction in possible_directions:
            new_head = Point3D(
                head.x + direction[0],
                head.y + direction[1],
                head.z + direction[2],
            )

            # Проверка коллизии
            if (new_head.x, new_head.y, new_head.z) in obstacle_positions:
                logging.info(
                    f"Направление {direction} приводит к столкновению с препятствием."
                )
                continue
            if (new_head.x, new_head.y, new_head.z) in enemy_positions:
                logging.info(
                    f"Направление {direction} приводит к столкновению с врагом."
                )
                continue

            # Оценка безопасности
            distance_to_closest_enemy = self.get_distance(
                new_head, enemy_positions
            )  # Более высокая безопасность при большей дистанции

            # Оценка полезности
            distance_to_closest_food = self.get_distance_advanced(
                new_head, game_state.food
            )  # Чем ближе, тем выше полезность

            # Вычисление баллов (можно настроить веса)
            # Например, вес безопасности = 1, полезности = 1.5
            score = (distance_to_closest_enemy * 1.0) + (
                1.5 / (distance_to_closest_food + 1)
            )
            direction_scores[tuple(direction)] = score
            logging.info(
                f"Направление {direction}: Безопасность={distance_to_closest_enemy}, Полезность={distance_to_closest_food}, Баллы={score}"
            )

        if not direction_scores:
            logging.warning(
                "Нет безопасных направлений. Продолжаем двигаться текущим направлением."
            )
            return my_snake.direction

        # Выбираем направление с максимальными баллами
        best_direction = max(direction_scores, key=direction_scores.get)
        logging.info(f"Выбранное направление (ADVANCED): {best_direction}")
        return list(best_direction)

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

    def get_closest_distance(self, head: Point3D, positions: set) -> Optional[int]:
        min_distance = float("inf")
        for pos in positions:
            distance = (
                abs(pos[0] - head.x) + abs(pos[1] - head.y) + abs(pos[2] - head.z)
            )
            if distance < min_distance:
                min_distance = distance
        return min_distance if min_distance != float("inf") else None

    def get_closest_distance_advanced(
        self, head: Point3D, food_list: List[Food]
    ) -> Optional[int]:
        min_distance = float("inf")
        for food in food_list:
            distance = (
                abs(food.c.x - head.x) + abs(food.c.y - head.y) + abs(food.c.z - head.z)
            )
            if distance < min_distance:
                min_distance = distance
        return min_distance if min_distance != float("inf") else None

    def get_distance(self, point: Point3D, positions: set) -> float:
        """Возвращает минимальное расстояние от точки до набора позиций."""
        min_distance = float("inf")
        for pos in positions:
            distance = (
                (pos[0] - point.x) ** 2
                + (pos[1] - point.y) ** 2
                + (pos[2] - point.z) ** 2
            ) ** 0.5  # Евклидово расстояние
            if distance < min_distance:
                min_distance = distance
        return min_distance if min_distance != float("inf") else float("inf")

    def get_distance_advanced(self, point: Point3D, food_list: List[Food]) -> float:
        """Возвращает минимальное Евклидово расстояние от точки до набора мандаринов."""
        min_distance = float("inf")
        for food in food_list:
            distance = (
                (food.c.x - point.x) ** 2
                + (food.c.y - point.y) ** 2
                + (food.c.z - point.z) ** 2
            ) ** 0.5
            if distance < min_distance:
                min_distance = distance
        return min_distance if min_distance != float("inf") else float("inf")

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
