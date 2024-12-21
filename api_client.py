# api_client.py
import requests
import logging
from typing import Optional, List
from game_state import GameState, Snake, Enemy, Food, Point3D
from dataclasses import dataclass


class APIClient:
    def __init__(self, token: str, server_url: str):
        self.token = token
        self.server_url = server_url
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }

    def get_game_state(self) -> Optional[GameState]:
        endpoint = "/play/snake3d/player/move"
        url = f"{self.server_url}{endpoint}"
        payload = {"snakes": []}  # Пустой запрос для получения текущего состояния
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            game_state = self.parse_game_state(data)
            logging.debug(f"Получено состояние игры: {game_state}")
            return game_state
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при получении состояния игры: {e}")
            return None

    def send_move(self, snake_id: str, direction: List[int]):
        endpoint = "/play/snake3d/player/move"
        url = f"{self.server_url}{endpoint}"
        payload = {"snakes": [{"id": snake_id, "direction": direction}]}
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logging.info(
                f"Команда отправлена: Змея ID {snake_id}, Направление {direction}"
            )
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при отправке команды: {e}")

    def parse_game_state(self, data: dict) -> GameState:
        snakes = [
            Snake(
                id=s["id"],
                direction=s["direction"],
                old_direction=s.get("oldDirection", [0, 0, 0]),
                geometry=[Point3D(*segment) for segment in s["geometry"]],
                death_count=s.get("deathCount", 0),
                status=s.get("status", "alive"),
                revive_remain_ms=s.get("reviveRemainMs", 0),
            )
            for s in data.get("snakes", [])
        ]

        enemies = [
            Enemy(
                geometry=[Point3D(*segment) for segment in e["geometry"]],
                status=e.get("status", "alive"),
                kills=e.get("kills", 0),
            )
            for e in data.get("enemies", [])
        ]

        food = [
            Food(c=Point3D(*f["c"]), points=f["points"]) for f in data.get("food", [])
        ]

        fences = [Point3D(*f) for f in data.get("fences", [])]

        game_state = GameState(
            map_size=data.get("mapSize", [100, 100, 100]),
            name=data.get("name", "NoName"),
            points=data.get("points", 0),
            fences=fences,
            snakes=snakes,
            enemies=enemies,
            food=food,
            turn=data.get("turn", 0),
            tick_remain_ms=data.get("tickRemainMs", 1000),
            revive_timeout_sec=data.get("reviveTimeoutSec", 5),
            errors=data.get("errors", []),
        )

        return game_state
