# decision_maker.py
import logging
from typing import List, Optional, Tuple, Dict
from game_state import GameState, Snake, Food, Point3D, Strategy

import heapq
import random


class DecisionMaker:
    def __init__(self, strategy: Strategy, max_search_depth: int = 20):
        """
        :param strategy: Выбранная стратегия (BASIC или ADVANCED)
        :param max_search_depth: Максимальное количество клеток для поиска путей
        """
        self.strategy = strategy
        self.max_search_depth = max_search_depth
        logging.info(f"Стратегия принятия решений: {self.strategy.name}")
        logging.info(f"Максимальная глубина поиска: {self.max_search_depth}")

    def decide_move(self, game_state: GameState, my_snake: Snake) -> List[int]:
        # Выбор стратегии
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
        map_size = game_state.map_size

        # Определяем ограничение области поиска
        search_limit = self.max_search_depth

        # Определяем препятствия в пределах N клеток от головы
        obstacles = set()
        # Стены
        for fence in game_state.fences:
            if self.within_limit(head, fence, search_limit):
                obstacles.add((fence.x, fence.y, fence.z))
        # Враги
        for enemy in game_state.enemies:
            for point in enemy.geometry:
                if self.within_limit(head, point, search_limit):
                    obstacles.add((point.x, point.y, point.z))
        # Собственная змейка (исключая хвост, если не растем)
        for snake in game_state.snakes:
            for point in snake.geometry:
                if self.within_limit(head, point, search_limit):
                    obstacles.add((point.x, point.y, point.z))

        logging.debug(
            f"Общее количество препятствий в пределах {search_limit}: {len(obstacles)}"
        )

        # Найдем все доступные мандарины в пределах N клеток
        available_food = [
            food
            for food in game_state.food
            if self.within_limit(head, food.c, search_limit)
        ]

        if not available_food:
            logging.info(
                "Нет доступной еды в пределах ограничения. Двигаемся безопасно."
            )
            return self.safe_move(obstacles, my_snake.direction, map_size, head)

        # Используем A* для поиска пути к ближайшему мандарину
        paths = []
        for food in available_food:
            path = self.a_star(
                start=(head.x, head.y, head.z),
                goal=(food.c.x, food.c.y, food.c.z),
                obstacles=obstacles,
                map_size=map_size,
                max_depth=search_limit,
            )
            if path:
                paths.append((len(path), path, food))

        if not paths:
            logging.info(
                "Нет доступных путей к еде в пределах ограничения. Двигаемся безопасно."
            )
            return self.safe_move(obstacles, my_snake.direction, map_size, head)

        # Выбираем самый короткий путь
        paths.sort(key=lambda x: x[0])
        _, best_path, target_food = paths[0]
        logging.info(
            f"Лучший путь к мандарину на ({target_food.c.x}, {target_food.c.y}, {target_food.c.z}) длиной {len(best_path)}"
        )

        # Определяем направление первого шага
        if len(best_path) < 2:
            logging.warning("Путь слишком короткий, продолжаем текущим направлением.")
            return my_snake.direction  # Нет шага вперед, продолжаем движение

        next_step = best_path[1]
        direction = [
            next_step[0] - head.x,
            next_step[1] - head.y,
            next_step[2] - head.z,
        ]

        # Нормализуем направление
        direction = [int(d / max(abs(d), 1)) for d in direction]

        logging.info(f"Решённое направление: {direction}")
        return direction

    def within_limit(self, head: Point3D, point: Point3D, limit: int) -> bool:
        """Проверяет, находится ли точка в пределах заданного ограничения от головы."""
        distance = abs(point.x - head.x) + abs(point.y - head.y) + abs(point.z - head.z)
        return distance <= limit

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

    def a_star(
        self,
        start: Tuple[int, int, int],
        goal: Tuple[int, int, int],
        obstacles: set,
        map_size: List[int],
        max_depth: int,
    ) -> Optional[List[Tuple[int, int, int]]]:
        logging.debug(
            f"A* поиск пути от {start} до {goal} с ограничением глубины {max_depth}"
        )
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from: Dict[Tuple[int, int, int], Optional[Tuple[int, int, int]]] = {
            start: None
        }
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            current_f, current = heapq.heappop(open_set)
            current_depth = g_score[current]

            if current == goal:
                return self.reconstruct_path(came_from, current)

            if current_depth >= max_depth:
                logging.debug(
                    f"Превышена максимальная глубина для узла {current}. Пропуск."
                )
                continue  # Пропускаем узлы, превышающие максимальную глубину

            neighbors = self.get_neighbors(current, map_size)
            for neighbor in neighbors:
                if neighbor in obstacles:
                    continue
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self.heuristic(neighbor, goal)
                    if tentative_g <= max_depth:
                        f_score[neighbor] = f
                        heapq.heappush(open_set, (f, neighbor))

        logging.debug("Путь не найден.")
        return None  # Путь не найден

    def heuristic(self, a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
        # Манхэттенское расстояние
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])

    def reconstruct_path(
        self,
        came_from: Dict[Tuple[int, int, int], Optional[Tuple[int, int, int]]],
        current: Tuple[int, int, int],
    ) -> List[Tuple[int, int, int]]:
        path = [current]
        while came_from[current]:
            current = came_from[current]
            path.append(current)
        path.reverse()
        logging.debug(f"Найденный путь: {path}")
        return path

    def get_neighbors(
        self, node: Tuple[int, int, int], map_size: List[int]
    ) -> List[Tuple[int, int, int]]:
        x, y, z = node
        neighbors = []
        directions = [
            (1, 0, 0),
            (-1, 0, 0),
            (0, 1, 0),
            (0, -1, 0),
            (0, 0, 1),
            (0, 0, -1),
        ]
        for dx, dy, dz in directions:
            nx, ny, nz = x + dx, y + dy, z + dz
            if (
                0 <= nx < map_size[0]
                and 0 <= ny < map_size[1]
                and 0 <= nz < map_size[2]
            ):
                neighbors.append((nx, ny, nz))
        return neighbors

    def safe_move(
        self,
        obstacles: set,
        current_direction: List[int],
        map_size: List[int],
        head: Point3D,
    ) -> List[int]:
        # Проверяем возможные направления и выбираем первое безопасное
        possible_directions = [
            [1, 0, 0],
            [-1, 0, 0],
            [0, 1, 0],
            [0, -1, 0],
            [0, 0, 1],
            [0, 0, -1],
        ]
        for direction in possible_directions:
            new_x = head.x + direction[0]
            new_y = head.y + direction[1]
            new_z = head.z + direction[2]
            if (
                0 <= new_x < map_size[0]
                and 0 <= new_y < map_size[1]
                and 0 <= new_z < map_size[2]
                and (new_x, new_y, new_z) not in obstacles
            ):
                logging.info(f"Безопасное направление найдено: {direction}")
                return direction
        logging.warning("Нет безопасных направлений, продолжаем текущим направлением.")
        return current_direction  # Если нет безопасных направлений, сохраняем текущее

    def random_move(self) -> List[int]:
        directions = [
            [1, 0, 0],
            [-1, 0, 0],
            [0, 1, 0],
            [0, -1, 0],
            [0, 0, 1],
            [0, 0, -1],
        ]
        direction = random.choice(directions)
        logging.info(f"Случайное направление: {direction}")
        return direction
