# game_state.py
from dataclasses import dataclass
from enum import Enum
from typing import List


@dataclass
class Point3D:
    x: int
    y: int
    z: int


@dataclass
class Snake:
    id: str
    direction: List[int]
    old_direction: List[int]
    geometry: List[Point3D]
    death_count: int
    status: str
    revive_remain_ms: int



@dataclass
class Enemy:
    geometry: List[Point3D]
    status: str
    kills: int


@dataclass
class Food:
    c: Point3D
    points: int


@dataclass
class GameState:
    map_size: List[int]
    name: str
    points: int
    fences: List[Point3D]
    snakes: List[Snake]
    enemies: List[Enemy]
    food: List[Food]
    turn: int
    tick_remain_ms: int
    revive_timeout_sec: int
    errors: List[str]


class Strategy(Enum):
    BASIC = 1
    ADVANCED = 2
