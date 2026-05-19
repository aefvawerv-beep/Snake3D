import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

from entities import Snake, Food, Position3D, Direction, RenderDispatcher


# =========================
# BASE SCENE
# =========================
class Scene:
    def handle_event(self, event): ...
    def update(self): ...
    def render(self): ...


# =========================
# MAIN MENU (PANCERNE RENDEROWANIE 2D)
# =========================
class MainMenuScene(Scene):
    def __init__(self, game):
        self.game = game
        self.play_button = pygame.Rect(300, 200, 200, 55)
        self.settings_button = pygame.Rect(300, 280, 200, 55)
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_button.collidepoint(event.pos):
                self.game.change_scene(GameScene(self.game))
            elif self.settings_button.collidepoint(event.pos):
                self.game.change_scene(SettingsScene(self.game))
                
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.change_scene(GameScene(self.game))

    def update(self):
        pass

    def render(self):
        glClearColor(0.93, 0.93, 0.93, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()

        surface = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        surface.fill((238, 238, 238)) # Jasnoszare tło #EEEEEE

        pygame.draw.rect(surface, (0, 128, 128), self.play_button, border_radius=4)
        pygame.draw.rect(surface, (255, 127, 80), self.settings_button, border_radius=4)

        play_text = self.font.render("PLAY", True, (255, 255, 255))
        settings_text = self.font.render("USTAWIENIA", True, (255, 255, 255))

        surface.blit(play_text, (self.play_button.x + (self.play_button.width - play_text.get_width()) // 2, self.play_button.y + 14))
        surface.blit(settings_text, (self.settings_button.x + (self.settings_button.width - settings_text.get_width()) // 2, self.settings_button.y + 14))

        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_TEXTURE_2D)
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.game.width, self.game.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0)
        glEnd()

        glDeleteTextures([tex_id])
        glDisable(GL_TEXTURE_2D)

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glPopAttrib()


# =========================
# OKNO USTAWIEŃ Z MODYFIKACJĄ CZUŁOŚCI
# =========================
class SettingsScene(Scene):
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)
        
        self.actions = [
            ("MOVE_NORTH", "Ruch w przód"),
            ("MOVE_SOUTH", "Ruch w tył"),
            ("MOVE_WEST", "Ruch w lewo"),
            ("MOVE_EAST", "Ruch w prawo"),
            ("MOVE_UP", "Ruch w górę"),
            ("MOVE_DOWN", "Ruch w dół")
        ]
        
        self.button_rects = {}
        start_y = 120
        for action_key, _ in self.actions:
            self.button_rects[action_key] = pygame.Rect(450, start_y, 200, 35)
            start_y += 45
            
        self.sens_rect = pygame.Rect(450, start_y + 10, 200, 35)
        self.back_button = pygame.Rect(200, 490, 400, 45)
        self.active_action = None
        
        # Zmienna przechowująca tekst wpisywany z klawiatury
        self.temp_sens_str = ""

    def handle_event(self, event):
        # 1. Obsługa wpisywania tekstu dla czułości myszy
        if self.active_action == "MOUSE_SENSITIVITY":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    # Próba zamiany wpisanego tekstu na ułamek (float)
                    try:
                        val = float(self.temp_sens_str)
                        # Zabezpieczenie, by czułość nie była ujemna ani za duża
                        val = max(0.01, min(5.0, val))
                        self.game.config["MOUSE_SENSITIVITY"] = round(val, 3)
                    except ValueError:
                        pass # Jeśli wpisano głupoty (np. samą kropkę), ignorujemy
                    
                    self.game.save_config()
                    self.active_action = None
                
                elif event.key == pygame.K_BACKSPACE:
                    self.temp_sens_str = self.temp_sens_str[:-1]
                
                else:
                    # Akceptuj tylko cyfry i maksymalnie jedną kropkę (z limitem do 5 znaków)
                    char = event.unicode
                    if char.isdigit() or (char == '.' and '.' not in self.temp_sens_str):
                        if len(self.temp_sens_str) < 5:
                            self.temp_sens_str += char
            return

        # 2. Standardowa obsługa przypisywania klawiszy (W, S, A, D itd.)
        if self.active_action is not None:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:
                    self.game.config[self.active_action] = event.key
                    self.game.save_config()
                self.active_action = None
            return

        # 3. Obsługa kliknięć myszką w menu
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                self.game.change_scene(MainMenuScene(self.game))
                return
            
            for action_key, rect in self.button_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_action = action_key
                    return
            
            # Kliknięto w pole wpisywania czułości
            if self.sens_rect.collidepoint(event.pos):
                self.active_action = "MOUSE_SENSITIVITY"
                # Wczytanie obecnej wartości do edycji jako tekst
                self.temp_sens_str = str(self.game.config.get("MOUSE_SENSITIVITY", 0.3))
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_scene(MainMenuScene(self.game))

        # Standardowa obsługa przypisywania klawisza
        if self.active_action is not None:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:
                    self.game.config[self.active_action] = event.key
                    self.game.save_config()
                self.active_action = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                self.game.change_scene(MainMenuScene(self.game))
                return
            
            # Czy kliknięto w bindowanie klawisza
            for action_key, rect in self.button_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_action = action_key
                    return
            
            # Czy kliknięto w regulację czułości
            if self.sens_rect.collidepoint(event.pos):
                self.active_action = "MOUSE_SENSITIVITY"
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_scene(MainMenuScene(self.game))

    def update(self):
        pass

    def render(self):
        glClearColor(0.9, 0.9, 0.9, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()

        surface = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        surface.fill((238, 238, 238))

        title_text = self.title_font.render("USTAWIENIA GRY", True, (0, 90, 90))
        surface.blit(title_text, ((self.game.width - title_text.get_width()) // 2, 35))

        # 1. Rysowanie wierszy klawiszy
        for action_key, label in self.actions:
            rect = self.button_rects[action_key]
            if self.active_action == action_key:
                pygame.draw.rect(surface, (0, 160, 160), rect, border_radius=4)
                key_text_str = "Wciśnij klawisz..."
            else:
                pygame.draw.rect(surface, (0, 128, 128), rect, border_radius=4)
                current_key_code = self.game.config.get(action_key, 0)
                key_text_str = pygame.key.name(current_key_code).upper()

            lbl_surf = self.font.render(label, True, (40, 40, 40))
            surface.blit(lbl_surf, (180, rect.y + 6))

            key_surf = self.font.render(key_text_str, True, (255, 255, 255))
            surface.blit(key_surf, (rect.x + (rect.width - key_surf.get_width()) // 2, rect.y + 6))

        # 2. Rysowanie wiersza czułości myszy
        if self.active_action == "MOUSE_SENSITIVITY":
            pygame.draw.rect(surface, (0, 160, 160), self.sens_rect, border_radius=4)
            # Dodajemy znak zachęty "_" symulujący kursor
            sens_text_str = self.temp_sens_str + "_" 
        else:
            pygame.draw.rect(surface, (0, 128, 128), self.sens_rect, border_radius=4)
            sens_text_str = str(self.game.config.get('MOUSE_SENSITIVITY', 0.3))

        lbl_sens = self.font.render("Czułość myszy (wpisz):", True, (40, 40, 40))
        surface.blit(lbl_sens, (180, self.sens_rect.y + 6))

        sens_surf = self.font.render(sens_text_str, True, (255, 255, 255))
        surface.blit(sens_surf, (self.sens_rect.x + (self.sens_rect.width - sens_surf.get_width()) // 2, self.sens_rect.y + 6))

        # 3. Przycisk POWRÓT
        pygame.draw.rect(surface, (255, 127, 80), self.back_button, border_radius=4)
        back_text = self.font.render("POWRÓT", True, (255, 255, 255))
        surface.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + 11))

        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_TEXTURE_2D)
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.game.width, self.game.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0)
        glEnd()

        glDeleteTextures([tex_id])
        glDisable(GL_TEXTURE_2D)

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glPopAttrib()


# =========================
# POZIOM GRY (3D OPENGL)
# =========================
class GameScene(Scene):
    def __init__(self, game, grid_size: int = 20):
        self.game = game
        self.grid_size = grid_size
        self.world_size = 8.0
        self.cell_size = self.world_size / self.grid_size

        self.yaw = 45.0
        self.pitch = 30.0

        self.snake = Snake()
        self.test_food = Food(Position3D(10, 5, 5))
        self.dispatcher = RenderDispatcher()

        self.move_interval = 300
        self.last_move_time = pygame.time.get_ticks()

    def on_enter(self):
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, self.game.width, self.game.height)

    def setup_camera(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, self.game.width / self.game.height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            dx, dy = event.rel
            # Pobieranie aktualnej czułości bezpośrednio ze słownika config okna gry
            sensitivity = self.game.config.get("MOUSE_SENSITIVITY", 0.3)
            self.yaw += dx * sensitivity
            self.pitch += dy * sensitivity
            self.pitch = max(-89, min(89, self.pitch))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_scene(MainMenuScene(self.game))
            
            elif event.key == self.game.config["MOVE_NORTH"]:
                self.snake.next_direction = Direction.NORTH
            elif event.key == self.game.config["MOVE_SOUTH"]:
                self.snake.next_direction = Direction.SOUTH
            elif event.key == self.game.config["MOVE_WEST"]:
                self.snake.next_direction = Direction.WEST
            elif event.key == self.game.config["MOVE_EAST"]:
                self.snake.next_direction = Direction.EAST
            elif event.key == self.game.config["MOVE_UP"]:
                self.snake.next_direction = Direction.UP
            elif event.key == self.game.config["MOVE_DOWN"]:
                self.snake.next_direction = Direction.DOWN

    def draw_grid(self):
        size = self.grid_size
        c = self.cell_size

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glColor4f(0.0, 0.0, 0.0, 0.12)
        glBegin(GL_LINES)
        for x in range(1, size):
            glVertex3f(x * c, 0, 0); glVertex3f(x * c, 0, size * c)
            glVertex3f(x * c, size * c, 0); glVertex3f(x * c, size * c, size * c)
        for y in range(1, size):
            glVertex3f(0, y * c, 0); glVertex3f(0, y * c, size * c)
            glVertex3f(size * c, y * c, size * c); glVertex3f(size * c, y * c, 0)
        for y in range(1, size):
            for x in range(1, size):
                glVertex3f(x * c, y * c, 0); glVertex3f(x * c, y * c, size * c)
        for x in range(1, size):
            glVertex3f(x * c, 0, 0); glVertex3f(x * c, size * c, 0)
            glVertex3f(x * c, 0, size * c); glVertex3f(x * c, size * c, size * c)
        for z in range(1, size):
            glVertex3f(0, 0, z * c); glVertex3f(0, size * c, z * c)
            glVertex3f(size * c, 0, z * c); glVertex3f(size * c, size * c, z * c)
        for z in range(1, size):
            for x in range(1, size):
                glVertex3f(x * c, 0, z * c); glVertex3f(x * c, size * c, z * c)
        for z in range(1, size):
            glVertex3f(0, 0, z * c); glVertex3f(size * c, 0, z * c)
            glVertex3f(0, size * c, z * c); glVertex3f(size * c, size * c, z * c)
        for y in range(1, size):
            glVertex3f(0, y * c, 0); glVertex3f(size * c, y * c, 0)
            glVertex3f(0, y * c, size * c); glVertex3f(size * c, y * c, size * c)
        for x in range(1, size):
            for y in range(1, size):
                glVertex3f(0, y * c, x * c); glVertex3f(size * c, y * c, x * c)
        glEnd()

        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glColor4f(0.3, 0.3, 0.3, 1.0)
        glBegin(GL_LINES)
        max_pos = size * c
        for z in [0, max_pos]:
            glVertex3f(0, 0, z); glVertex3f(max_pos, 0, z)
            glVertex3f(max_pos, 0, z); glVertex3f(max_pos, max_pos, z)
            glVertex3f(max_pos, max_pos, z); glVertex3f(0, max_pos, z)
            glVertex3f(0, max_pos, z); glVertex3f(0, 0, z)
        for x in [0, max_pos]:
            for y in [0, max_pos]:
                glVertex3f(x, y, 0); glVertex3f(x, y, max_pos)
        glEnd()

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time >= self.move_interval:
            self.snake.update(self)
            self.last_move_time = current_time

    def render(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.setup_camera()
        glLoadIdentity()

        glTranslatef(0.0, 0.0, -25.0)
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)

        center = self.world_size / 2
        glTranslatef(-center, -center, -center)

        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)

        self.dispatcher.dispatch(self.snake, self.cell_size)
        self.dispatcher.dispatch(self.test_food, self.cell_size)

        self.draw_grid()