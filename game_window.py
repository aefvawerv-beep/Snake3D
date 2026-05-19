import json
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *

# Bezpieczny import całej zawartości
from scenes import *


class GameWindow:

    def __init__(self):
        pygame.init()

        self.width = 800
        self.height = 600

        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            DOUBLEBUF | OPENGL | RESIZABLE
        )

        pygame.display.set_caption("Snake 3D")
        self.clock = pygame.time.Clock()

        self.config_path = "config.json"
        self.config = self.load_config()

        self.running = True
        self.current_scene = MainMenuScene(self)

        glViewport(0, 0, self.width, self.height)

    def load_config(self):
        default_config = {
            "MOVE_NORTH": pygame.K_w,
            "MOVE_SOUTH": pygame.K_s,
            "MOVE_WEST": pygame.K_a,
            "MOVE_EAST": pygame.K_d,
            "MOVE_UP": pygame.K_q,
            "MOVE_DOWN": pygame.K_e,
            "MOUSE_SENSITIVITY": 0.30  # Nowa domyślna wartość czułości
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for key in default_config:
                        if key not in loaded:
                            loaded[key] = default_config[key]
                    return loaded
            except Exception:
                return default_config
        else:
            self.save_config(default_config)
            return default_config

    def save_config(self, config_to_save=None):
        if config_to_save is None:
            config_to_save = self.config
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=4)
        except Exception as e:
            print(f"Błąd zapisu pliku: {e}")

    def change_scene(self, scene):
        self.current_scene = scene
        if hasattr(scene, "on_enter"):
            scene.on_enter()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height),
                        DOUBLEBUF | OPENGL | RESIZABLE
                    )
                    glViewport(0, 0, self.width, self.height)

                self.current_scene.handle_event(event)

            self.current_scene.update()
            self.current_scene.render()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()