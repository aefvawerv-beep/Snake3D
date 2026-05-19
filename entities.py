import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple
from OpenGL.GL import *

@dataclass
class Position3D:
    x: int
    y: int
    z: int

class Direction:
    NORTH = (0, 0, -1)
    SOUTH = (0, 0, 1)
    WEST  = (-1, 0, 0)
    EAST  = (1, 0, 0)
    UP    = (0, 1, 0)
    DOWN  = (0, -1, 0)

class Entity(ABC):
    def __init__(self, position: Position3D, color: Tuple[float, float, float]) -> None:
        self.position = position
        self.color = color

    @abstractmethod
    def draw(self, cell_size: float) -> None:
        pass

class CubeRendererHelper:
    @staticmethod
    def draw_cube(pos: Position3D, cell_size: float, color: Tuple[float, float, float]):
        x = pos.x * cell_size
        y = pos.y * cell_size
        z = pos.z * cell_size
        s = cell_size

        glColor3f(*color)
        glBegin(GL_QUADS)
        # FRONT
        glVertex3f(x, y, z + s)
        glVertex3f(x + s, y, z + s)
        glVertex3f(x + s, y + s, z + s)
        glVertex3f(x, y + s, z + s)
        # BACK
        glVertex3f(x, y, z)
        glVertex3f(x + s, y, z)
        glVertex3f(x + s, y + s, z)
        glVertex3f(x, y + s, z)
        # LEFT
        glVertex3f(x, y, z)
        glVertex3f(x, y, z + s)
        glVertex3f(x, y + s, z + s)
        glVertex3f(x, y + s, z)
        # RIGHT
        glVertex3f(x + s, y, z)
        glVertex3f(x + s, y, z + s)
        glVertex3f(x + s, y + s, z + s)
        glVertex3f(x + s, y + s, z)
        # TOP
        glVertex3f(x, y + s, z)
        glVertex3f(x + s, y + s, z)
        glVertex3f(x + s, y + s, z + s)
        glVertex3f(x, y + s, z + s)
        # BOTTOM
        glVertex3f(x, y, z)
        glVertex3f(x + s, y, z)
        glVertex3f(x + s, y, z + s)
        glVertex3f(x, y, z + s)
        glEnd()

class SnakeSegment(Entity):
    def __init__(self, position: Position3D, is_head: bool = False) -> None:
        super().__init__(position, (0.1, 0.7, 0.1))
        self.is_head = is_head

    def draw(self, cell_size: float) -> None:
        color = (0.1, 0.9, 0.1) if self.is_head else (0.1, 0.6, 0.1)
        CubeRendererHelper.draw_cube(self.position, cell_size, color)

class Food(Entity):
    def __init__(self, position: Position3D) -> None:
        super().__init__(position, (0.9, 0.1, 0.1))

    def randomize_position(self, grid_size: int):
        self.position = Position3D(
            random.randint(0, grid_size - 1),
            random.randint(0, grid_size - 1),
            random.randint(0, grid_size - 1)
        )

    def draw(self, cell_size: float) -> None:
        CubeRendererHelper.draw_cube(self.position, cell_size, self.color)

class Snake:
    def __init__(self) -> None:
        self.segments = [
            SnakeSegment(Position3D(10, 5, 10), is_head=True),
            SnakeSegment(Position3D(10, 5, 11), is_head=False),
            SnakeSegment(Position3D(10, 5, 12), is_head=False)
        ]
        self.current_direction = Direction.NORTH
        self.next_direction = Direction.NORTH

    def update(self, game_scene) -> None:
        inv_curr = (-self.current_direction[0], -self.current_direction[1], -self.current_direction[2])
        if self.next_direction != inv_curr:
            self.current_direction = self.next_direction

        head = self.segments[0]
        dx, dy, dz = self.current_direction
        new_head_pos = Position3D(
            head.position.x + dx,
            head.position.y + dy,
            head.position.z + dz
        )

        if (new_head_pos.x == game_scene.test_food.position.x and 
            new_head_pos.y == game_scene.test_food.position.y and 
            new_head_pos.z == game_scene.test_food.position.z):
            
            new_head = SnakeSegment(new_head_pos, is_head=True)
            head.is_head = False
            self.segments.insert(0, new_head)
            game_scene.test_food.randomize_position(game_scene.grid_size)
        else:
            for i in range(len(self.segments) - 1, 0, -1):
                self.segments[i].position = Position3D(
                    self.segments[i-1].position.x,
                    self.segments[i-1].position.y,
                    self.segments[i-1].position.z
                )
            head.position = new_head_pos

    def draw(self, cell_size: float) -> None:
        for segment in self.segments:
            segment.draw(cell_size)

class RenderDispatcher:
    def dispatch(self, entity, cell_size: float):
        if entity and hasattr(entity, "draw"):
            entity.draw(cell_size)