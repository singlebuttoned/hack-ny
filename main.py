# main.py
import time
import logging
from api_client import APIClient
from game_state import GameState, Snake, Strategy
from decision_maker import DecisionMaker
from visualization import Visualization
from logger_config import setup_logger
import threading


def bot_logic(api_client, decision_maker, visualization, snake_id):
    my_snake = None

    # Получаем начальное состояние игры
    initial_game_state = api_client.get_game_state()
    if not initial_game_state or not initial_game_state.snakes:
        logging.error("Не удалось получить информацию о вашей змее.")
        return

    my_snake = initial_game_state.snakes[0]  # Если несколько, необходимо выбрать нужную
    logging.info(f"Управляется змеёй с ID: {my_snake.id}")

    # Отправляем начальное визуализационное обновление
    visualization.request_update(initial_game_state, my_snake)

    while True:
        game_state = api_client.get_game_state()
        if not game_state:
            logging.error("Нет состояния игры, пробуем снова через 1 секунду.")
            time.sleep(1)
            continue

        # Проверка статуса вашей змеи
        my_snake = next((s for s in game_state.snakes if s.id == my_snake.id), my_snake)
        if my_snake.status == "dead":
            logging.warning(
                f"Змея мертва, ожидаем возрождения {game_state.revive_timeout_sec} с"
            )
            time.sleep(game_state.revive_timeout_sec)
            continue

        # Принятие решения о движении
        direction = decision_maker.decide_move(game_state, my_snake, visualization)
        logging.info(f"Принято направление: {direction}")

        # Отправка команды о движении
        api_client.send_move(my_snake.id, direction)

        # Обновление визуализации
        visualization.request_update(game_state, my_snake)

        # Логика ожидания конца тика
        tick_time = game_state.tick_remain_ms / 1000.0  # Перевод в секунды
        logging.debug(f"Ожидание конца тика: {tick_time} секунд")
        time.sleep(tick_time)


def main():
    # Настройка логирования
    setup_logger()
    logging.info("Запуск бота для 3D Snake")

    # Конфигурация
    TOKEN = "f05b5728-8e94-4f55-a903-e2ca923d285d"  # Замените на ваш токен
    SERVER_URL = "https://games-test.datsteam.dev"  # Используйте основной сервер для финальных раундов

    api_client = APIClient(token=TOKEN, server_url=SERVER_URL)
    decision_maker = DecisionMaker(strategy=Strategy.ADVANCED, max_search_depth=40)
    visualization = Visualization()

    # Запускаем приложение визуализации в главном потоке
    # А бот в отдельном потоке
    bot_thread = threading.Thread(
        target=bot_logic,
        args=(api_client, decision_maker, visualization, None),
        daemon=True,
    )
    bot_thread.start()

    # Запускаем GUI
    visualization.start()


if __name__ == "__main__":
    main()
