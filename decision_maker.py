# decision_maker.py
import logging
import heapq
import random
from typing import List, Optional, Tuple, Dict
from game_state import GameState, Snake, Food, Point3D, Strategy
from visualization import Visualization


class DecisionMaker:
    def __init__(
        self,
        strategy: Strategy,
        max_search_depth: int,
        target_change_interval: int = 5,
    ):
        """
        :param strategy: Выбранная стратегия (BASIC или ADVANCED)
        :param max_search_depth: Максимальное количество клеток для поиска путей (радиус N)
        :param target_change_interval: Минимальное количество шагов между сменой цели
        """
        self.strategy = strategy
        self.max_search_depth = max_search_depth
        self.target_change_interval = target_change_interval
        self.current_target: Optional[Food] = None
        self.steps_since_target_change: int = (
            self.target_change_interval
        )  # Инициализируем, чтобы можно было выбрать цель сразу
        logging.info(f"Стратегия принятия решений: {self.strategy.name}")
        logging.info(f"Максимальная глубина поиска: {self.max_search_depth}")
        logging.info(f"Интервал смены цели: {self.target_change_interval} шагов")

    def decide_move(
        self, game_state: GameState, my_snake: Snake, visualization: Visualization
    ) -> List[int]:
        """
        Определяет направление движения змеи на основе выбранной стратегии.
        :param game_state: Текущее состояние игры
        :param my_snake: Информация о вашей змее
        :param visualization: Объект визуализации для отображения целей
        :return: Направление движения в виде списка [dx, dy, dz]
        """
        # Увеличиваем счетчик шагов с момента последней смены цели
        self.steps_since_target_change += 1

        # Выбор стратегии
        if self.strategy == Strategy.BASIC:
            return self.basic_strategy(game_state, my_snake, visualization)
        elif self.strategy == Strategy.ADVANCED:
            return self.advanced_strategy(game_state, my_snake, visualization)
        elif self.strategy == Strategy.KILLER:  # Добавляем обработку KILLER
            return self.killer_strategy(game_state, my_snake, visualization)
        else:
            logging.warning("Неизвестная стратегия. Используем BASIC.")
            return self.basic_strategy(game_state, my_snake, visualization)

    def basic_strategy(
        self, game_state: GameState, my_snake: Snake, visualization: Visualization
    ) -> List[int]:
        logging.info("Используется BASIC стратегия.")
        head = my_snake.geometry[0]
        logging.info(f"Позиция головы змеи: ({head.x}, {head.y}, {head.z})")

        # Найдем ближайший мандарин по Манхэттену
        target = self.find_closest_food(head, game_state.food)
        visualization.target = target  # Передаём цель в визуализацию
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
        desired_direction = self.get_direction_vector(head, target.c)
        logging.info(f"Желаемое направление: {desired_direction}")

        # Определяем набор безопасных направлений
        safe_directions = self.get_safe_directions(game_state, my_snake)

        # Если желаемое направление безопасно, выбираем его
        if desired_direction in safe_directions:
            logging.info("Желаемое направление безопасно.")
            return desired_direction

        logging.info(
            "Желаемое направление небезопасно. Ищем альтернативное безопасное направление."
        )

        # Ищем альтернативное направление, которое приближает к цели
        alternative_directions = self.get_alternative_directions(
            head, target.c, safe_directions
        )
        if alternative_directions:
            logging.info(
                f"Выбрано альтернативное направление: {alternative_directions[0]}"
            )
            return alternative_directions[0]

        # Если нет предпочтительных альтернатив, выбираем любое безопасное направление
        if safe_directions:
            logging.info(
                f"Нет предпочтительных альтернатив. Выбираем безопасное направление: {safe_directions[0]}"
            )
            return safe_directions[0]

        logging.warning("Нет безопасных направлений, продолжаем текущим направлением.")
        return my_snake.direction  # Если нет безопасных направлений, сохраняем текущее

    def killer_strategy(
        self, game_state: GameState, my_snake: Snake, visualization: Visualization
    ) -> List[int]:
        logging.info("Используется KILLER стратегия.")
        head = my_snake.geometry[0]
        map_size = game_state.map_size

        # Собираем препятствия в радиусе N
        obstacles = self.get_obstacles_within_radius(
            game_state, my_snake, head, self.max_search_depth
        )
        logging.debug(
            f"Общее количество препятствий в радиусе {self.max_search_depth}: {len(obstacles)}"
        )

        # Находим все головы врагов в радиусе N
        enemy_heads = self.get_enemy_heads_within_radius(
            game_state, head, self.max_search_depth
        )
        logging.info(
            f"Количество голов врагов в радиусе {self.max_search_depth}: {len(enemy_heads)}"
        )

        obstacles = set(
            filter(lambda x: (True if x not in enemy_heads else False), obstacles)
        )

        if not enemy_heads:
            logging.info("Нет голов врагов в радиусе. Выбираем безопасное направление.")
            safe_directions = self.get_safe_directions(game_state, my_snake)
            if safe_directions:
                chosen_direction = random.choice(safe_directions)
                logging.info(f"Выбрано безопасное направление: {chosen_direction}")
                return chosen_direction
            else:
                return self.random_move()

        # Выбираем ближайшую голову врага
        closest_enemy_head, path = self.find_closest_enemy_head(
            head, enemy_heads, obstacles, map_size
        )

        if closest_enemy_head and path:
            self.current_target = closest_enemy_head
            visualization.target = closest_enemy_head
            self.steps_since_target_change = 0
            logging.info(
                f"Выбрана цель (голова врага) на позиции: ({closest_enemy_head.x}, {closest_enemy_head.y}, {closest_enemy_head.z})"
            )
            return self.get_direction_from_path(head, path)
        else:
            logging.info(
                "Нет доступных путей к головам врагов. Выбираем безопасное направление."
            )
            safe_directions = self.get_safe_directions(game_state, my_snake)
            if safe_directions:
                chosen_direction = random.choice(safe_directions)
                logging.info(f"Выбрано безопасное направление: {chosen_direction}")
                return chosen_direction
            else:
                return self.random_move()

    def advanced_strategy(
        self, game_state: GameState, my_snake: Snake, visualization: Visualization
    ) -> List[int]:
        logging.info("Используется ADVANCED стратегия.")
        head = my_snake.geometry[0]
        map_size = game_state.map_size

        # Определяем препятствия в пределах радиуса N
        obstacles = self.get_obstacles_within_radius(
            game_state, my_snake, head, self.max_search_depth
        )
        logging.debug(
            f"Общее количество препятствий в радиусе {self.max_search_depth}: {len(obstacles)}"
        )

        # Собираем доступные цели (мандарины) в радиусе N
        available_food = self.find_food_within_radius(
            head, game_state.food, self.max_search_depth
        )
        logging.info(
            f"Количество доступных мандаринов в радиусе {self.max_search_depth}: {len(available_food)}"
        )

        # Условия для смены цели:
        # 1. Нет текущей цели
        # 2. Прошло достаточно шагов с последней смены цели
        # 3. Текущая цель недоступна (не в радиусе или путь заблокирован)
        need_new_target = False
        if self.current_target:
            distance = self.manhattan_distance(head, self.current_target.c)
            if distance > self.max_search_depth:
                logging.info(
                    "Текущая цель вышла за пределы радиуса. Требуется смена цели."
                )
                need_new_target = True
            else:
                # Проверяем, доступен ли путь до текущей цели
                path = self.a_star(
                    start=(head.x, head.y, head.z),
                    goal=(
                        self.current_target.c.x,
                        self.current_target.c.y,
                        self.current_target.c.z,
                    ),
                    obstacles=obstacles,
                    map_size=map_size,
                    max_depth=self.max_search_depth,
                )
                if not path:
                    logging.info(
                        "Нет доступного пути до текущей цели. Требуется смена цели."
                    )
                    need_new_target = True
        else:
            need_new_target = True

        if (
            need_new_target
            and self.steps_since_target_change >= self.target_change_interval
        ):
            logging.info("Выбираем новую цель.")
            # Выбираем ближайшую доступную цель, до которой можно добраться
            new_target, new_path = self.select_new_target(
                head, available_food, obstacles, map_size
            )
            if new_target and new_path:
                self.current_target = new_target
                self.steps_since_target_change = 0
                visualization.target = new_target
                logging.info(
                    f"Новая цель установлена: ({new_target.c.x}, {new_target.c.y}, {new_target.c.z})"
                )
                # Двигаемся по пути к новой цели
                return self.get_direction_from_path(head, new_path)
            else:
                logging.info(
                    "Не удалось найти доступную цель. Будем двигаться безопасно."
                )
                self.current_target = None
        elif self.current_target:
            logging.info(
                f"Продолжаем двигаться к текущей цели: ({self.current_target.c.x}, {self.current_target.c.y}, {self.current_target.c.z})"
            )
            # Проверяем, доступен ли путь до текущей цели
            path = self.a_star(
                start=(head.x, head.y, head.z),
                goal=(
                    self.current_target.c.x,
                    self.current_target.c.y,
                    self.current_target.c.z,
                ),
                obstacles=obstacles,
                map_size=map_size,
                max_depth=self.max_search_depth,
            )
            if path:
                # Двигаемся по пути к текущей цели
                visualization.route = path
                return self.get_direction_from_path(head, path)
            else:
                logging.info(
                    "Путь до текущей цели больше не доступен. Требуется смена цели."
                )
                self.current_target = None

        # Если цели нет или путь до неё не доступен, выбираем безопасное направление
        logging.info("Выбираем безопасное направление.")
        safe_directions = self.get_safe_directions(game_state, my_snake)
        if safe_directions:
            chosen_direction = random.choice(safe_directions)
            logging.info(f"Выбрано безопасное направление: {chosen_direction}")
            return chosen_direction

        logging.warning("Нет безопасных направлений, продолжаем текущим направлением.")
        return my_snake.direction  # Если нет безопасных направлений, сохраняем текущее

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

    def find_food_within_radius(
        self, head: Point3D, food_list: List[Food], radius: int
    ) -> List[Food]:
        """
        Находит все мандарины (цели) в пределах радиуса от головы змеи.
        :param head: Позиция головы змеи
        :param food_list: Список всех мандаринов на карте
        :param radius: Радиус поиска
        :return: Список мандаринов в пределах радиуса
        """
        available_food = []
        for food in food_list:
            distance = self.manhattan_distance(head, food.c)
            if distance <= radius:
                available_food.append(food)
                logging.debug(
                    f"Мандарин на ({food.c.x}, {food.c.y}, {food.c.z}) в радиусе: {distance}"
                )
        return available_food

    def get_enemy_heads_within_radius(
        self, game_state: GameState, head: Point3D, radius: int
    ) -> List[Point3D]:
        """
        Находит головы всех врагов в пределах заданного радиуса.
        :param game_state: Текущее состояние игры
        :param head: Позиция головы змеи
        :param radius: Радиус поиска
        :return: Список позиций голов врагов
        """
        enemy_heads = []
        for enemy in game_state.enemies:
            if not enemy.geometry:
                continue  # Если у врага нет координат, пропускаем
            enemy_head = enemy.geometry[
                0
            ]  # Предполагаем, что первая точка - это голова
            distance = self.manhattan_distance(head, enemy_head)
            if distance <= radius:
                enemy_heads.append(enemy_head)
                logging.debug(
                    f"Голова врага на ({enemy_head.x}, {enemy_head.y}, {enemy_head.z}) в радиусе: {distance}"
                )
        return enemy_heads

    def find_closest_enemy_head(
        self,
        head: Point3D,
        enemy_heads: List[Point3D],
        obstacles: set,
        map_size: List[int],
    ) -> Tuple[Optional[Point3D], Optional[List[Tuple[int, int, int]]]]:
        """
        Находит ближайшую голову врагов, до которой есть доступный путь.
        :param head: Позиция головы змеи
        :param enemy_heads: Список позиций голов врагов
        :param obstacles: Множество препятствий
        :param map_size: Размер карты
        :return: Кортеж из позиции головы и пути до нее или (None, None) если не найдено
        """
        sorted_heads = sorted(
            enemy_heads,
            key=lambda enemy_head: self.manhattan_distance(head, enemy_head),
        )
        for enemy_head in sorted_heads:
            path = self.a_star(
                start=(head.x, head.y, head.z),
                goal=(enemy_head.x, enemy_head.y, enemy_head.z),
                obstacles=obstacles,
                map_size=map_size,
                max_depth=self.max_search_depth,
            )
            if path:
                logging.info(
                    f"Найден путь к голове врага на ({enemy_head.x}, {enemy_head.y}, {enemy_head.z}) длиной {len(path)}"
                )
                return enemy_head, path
            else:
                logging.debug(
                    f"Нет доступного пути к голове врага на ({enemy_head.x}, {enemy_head.y}, {enemy_head.z})"
                )
        return None, None

    def select_new_target(
        self,
        head: Point3D,
        available_food: List[Food],
        obstacles: set,
        map_size: List[int],
    ) -> Tuple[Optional[Food], Optional[List[Tuple[int, int, int]]]]:
        """
        Выбирает новую цель из доступных мандаринов и возвращает путь к ней.
        :param head: Позиция головы змеи
        :param available_food: Список доступных мандаринов в радиусе
        :param obstacles: Множество препятствий
        :param map_size: Размер карты
        :return: Кортеж из выбранной цели и пути до неё
        """
        # Сортируем мандарины по расстоянию
        sorted_food = sorted(
            available_food, key=lambda food: self.manhattan_distance(head, food.c)
        )
        for food in sorted_food:
            path = self.a_star(
                start=(head.x, head.y, head.z),
                goal=(food.c.x, food.c.y, food.c.z),
                obstacles=obstacles,
                map_size=map_size,
                max_depth=self.max_search_depth,
            )
            if path:
                logging.info(
                    f"Найден путь к мандарину на ({food.c.x}, {food.c.y}, {food.c.z}) длиной {len(path)}"
                )
                return food, path
            else:
                logging.debug(
                    f"Не удалось найти путь к мандарину на ({food.c.x}, {food.c.y}, {food.c.z})"
                )
        return None, None

    def get_direction_from_path(
        self, head: Point3D, path: List[Tuple[int, int, int]]
    ) -> List[int]:
        """
        Определяет направление движения по первому шагу пути.
        :param head: Позиция головы змеи
        :param path: Путь, найденный алгоритмом A*
        :return: Направление движения в виде списка [dx, dy, dz]
        """
        if len(path) < 2:
            logging.warning("Путь слишком короткий, продолжаем текущим направлением.")
            return [
                0,
                0,
                0,
            ]  # Нет шага вперед, можно выбрать безопасное направление или останавливаться

        next_step = path[1]
        direction = [
            next_step[0] - head.x,
            next_step[1] - head.y,
            next_step[2] - head.z,
        ]

        # Нормализуем направление
        direction = [int(d / max(abs(d), 1)) for d in direction]
        logging.info(f"Направление по пути: {direction}")
        return direction

    def get_obstacles_within_radius(
        self, game_state: GameState, my_snake: Snake, head: Point3D, radius: int
    ) -> set:
        """
        Собирает все препятствия (стены, враги, змеи) в пределах радиуса от головы.
        :param game_state: Текущее состояние игры
        :param my_snake: Ваша змейка
        :param head: Позиция головы змеи
        :param radius: Радиус поиска
        :return: Множество координат препятствий
        """
        obstacles = set()

        # Стены
        for fence in game_state.fences:
            distance = self.manhattan_distance(head, fence)
            if distance <= radius:
                obstacles.add((fence.x, fence.y, fence.z))
                logging.debug(
                    f"Препятствие (стена) на ({fence.x}, {fence.y}, {fence.z}) в радиусе: {distance}"
                )

        # Враги
        for enemy in game_state.enemies:
            for point in enemy.geometry:
                distance = self.manhattan_distance(head, point)
                if distance <= radius:
                    obstacles.add((point.x, point.y, point.z))
                    logging.debug(
                        f"Препятствие (враг) на ({point.x}, {point.y}, {point.z}) в радиусе: {distance}"
                    )

        # Собственные змейки
        for snake in game_state.snakes:
            for point in snake.geometry:
                distance = self.manhattan_distance(head, point)
                if distance <= radius:
                    obstacles.add((point.x, point.y, point.z))
                    logging.debug(
                        f"Препятствие (змейка) на ({point.x}, {point.y}, {point.z}) в радиусе: {distance}"
                    )

        return obstacles

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

    def get_safe_directions(
        self, game_state: GameState, my_snake: Snake
    ) -> List[List[int]]:
        """
        Возвращает список безопасных направлений, в которые змея может двигаться.
        :param game_state: Текущее состояние игры
        :param my_snake: Ваша змейка
        :return: Список безопасных направлений [dx, dy, dz]
        """
        safe_directions = []
        head = my_snake.geometry[0]
        map_size = game_state.map_size

        # Собираем множество препятствий: стены, враги, все змеи (включая собственную)
        obstacles = set()
        for fence in game_state.fences:
            obstacles.add((fence.x, fence.y, fence.z))
        for enemy in game_state.enemies:
            for point in enemy.geometry:
                obstacles.add((point.x, point.y, point.z))
        for snake in game_state.snakes:
            for point in snake.geometry:
                obstacles.add((point.x, point.y, point.z))

        logging.debug(f"Общее количество препятствий: {len(obstacles)}")

        # Определяем возможные направления движения
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

            # Проверяем, находится ли новая позиция внутри карты
            if not (
                0 <= new_x < map_size[0]
                and 0 <= new_y < map_size[1]
                and 0 <= new_z < map_size[2]
            ):
                logging.debug(f"Направление {direction} выходит за пределы карты.")
                continue

            # Проверяем, не является ли новая позиция препятствием
            if (new_x, new_y, new_z) in obstacles:
                logging.debug(
                    f"Направление {direction} ведет к препятствию на ({new_x}, {new_y}, {new_z})."
                )
                continue

            # Направление безопасно
            safe_directions.append(direction)

        logging.debug(f"Безопасные направления: {safe_directions}")
        return safe_directions

    def a_star(
        self,
        start: Tuple[int, int, int],
        goal: Tuple[int, int, int],
        obstacles: set,
        map_size: List[int],
        max_depth: int,
    ) -> Optional[List[Tuple[int, int, int]]]:
        """
        Реализует алгоритм A* для поиска пути от start до goal с учетом препятствий и ограничения глубины.
        :param start: Координаты начала пути
        :param goal: Координаты цели
        :param obstacles: Множество препятствий
        :param map_size: Размер карты
        :param max_depth: Максимальная глубина поиска
        :return: Список координат пути или None, если путь не найден
        """
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
                path = self.reconstruct_path(came_from, current)
                logging.debug(f"Путь найден: {path}")
                return path

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

    def reconstruct_path(
        self,
        came_from: Dict[Tuple[int, int, int], Optional[Tuple[int, int, int]]],
        current: Tuple[int, int, int],
    ) -> List[Tuple[int, int, int]]:
        """
        Восстанавливает путь от цели до начала на основе словаря came_from.
        :param came_from: Словарь, указывающий предыдущий узел для каждого узла в пути
        :param current: Конечный узел (цель)
        :return: Список координат пути от начала до цели
        """
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
        """
        Возвращает соседние узлы для заданного узла.
        :param node: Текущий узел
        :param map_size: Размер карты
        :return: Список соседних узлов
        """
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

    def heuristic(self, a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
        """
        Эвристическая функция (Манхэттенское расстояние) для A*.
        :param a: Координаты точки a
        :param b: Координаты точки b
        :return: Манхэттенское расстояние между a и b
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])

    def manhattan_distance(self, a: Point3D, b: Point3D) -> int:
        """
        Вычисляет Манхэттенское расстояние между двумя точками.
        :param a: Первая точка
        :param b: Вторая точка
        :return: Манхэттенское расстояние
        """
        return abs(a.x - b.x) + abs(a.y - b.y) + abs(a.z - b.z)

    def get_direction_vector(self, head: Point3D, target: Point3D) -> List[int]:
        """
        Определяет вектор направления от головы змеи к цели.
        :param head: Позиция головы змеи
        :param target: Позиция цели
        :return: Вектор направления [dx, dy, dz]
        """
        direction = [0, 0, 0]
        if head.x < target.x:
            direction[0] = 1
        elif head.x > target.x:
            direction[0] = -1
        if head.y < target.y:
            direction[1] = 1
        elif head.y > target.y:
            direction[1] = -1
        if head.z < target.z:
            direction[2] = 1
        elif head.z > target.z:
            direction[2] = -1
        return direction

    def get_alternative_directions(
        self, head: Point3D, target: Point3D, safe_directions: List[List[int]]
    ) -> List[List[int]]:
        """
        Сортирует безопасные направления по приоритету приближения к цели.
        :param head: Позиция головы змеи
        :param target: Позиция цели
        :param safe_directions: Список безопасных направлений
        :return: Список безопасных направлений, отсортированных по приоритету
        """

        def direction_priority(direction):
            new_x = head.x + direction[0]
            new_y = head.y + direction[1]
            new_z = head.z + direction[2]
            # Вычисляем манхэттенское расстояние до цели после движения в этом направлении
            return self.manhattan_distance(Point3D(new_x, new_y, new_z), target)

        # Сортируем безопасные направления по возрастанию расстояния до цели
        sorted_directions = sorted(safe_directions, key=direction_priority)
        return sorted_directions

    def random_move(self) -> List[int]:
        """
        Выбирает случайное направление из возможных.
        :return: Направление движения в виде списка [dx, dy, dz]
        """
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
