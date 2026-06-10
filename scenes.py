import os
import json
import glob
import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

from entities import Snake, Food, Obstacle, SnakeSegment, Position3D, Direction, RenderDispatcher

from progress_manager import get_max_unlocked_level, save_progress, reset_progress


def load_all_levels():
    levels = []
    required_keys = ["id", "name", "grid_size", "foods_to_win", "snake_start", "food_start", "obstacles"]
    
    files = glob.glob("levels/*.json")
    if not files:
        print("[WARNING] Folder 'levels' jest pusty lub nie istnieje! Gra nie znajdzie żadnych poziomów.")

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                missing_keys = [key for key in required_keys if key not in data]
                if missing_keys:
                    print(f"[CORRUPTED FILE] Pominięto {file} -> Brakuje wymaganych pól: {missing_keys}")
                    continue  
                
                levels.append(data)
                
        except json.JSONDecodeError:
            print(f"[CORRUPTED JSON] Pominięto {file} -> Uszkodzona składnia znaków (sprawdź nawiasy/przecinki).")
        except Exception as e:
            print(f"Błąd ładowania {file}: {e}")
            
    levels.sort(key=lambda x: x.get("id", 0))
    return levels

def get_next_level(current_id):
    levels = load_all_levels()
    for lvl in levels:
        if lvl.get("id", 0) == current_id + 1:
            return lvl
    return None


# =========================
# BASE SCENE
# =========================
class Scene:
    def handle_event(self, event): ...
    def update(self): ...
    def render(self): ...


# =========================
# MAIN MENU
# =========================
class MainMenuScene(Scene):
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 16, bold=True)
        
        # Przywrócone poprawne przyciski menu głównego
        self.play_button = pygame.Rect((self.game.width - 300) // 2, 180, 300, 50)
        self.settings_button = pygame.Rect((self.game.width - 300) // 2, 250, 300, 50)
        self.exit_button = pygame.Rect((self.game.width - 300) // 2, 320, 300, 50)
        self.reset_button = pygame.Rect((self.game.width - 200) // 2, 450, 200, 35)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_button.collidepoint(event.pos):
                self.game.change_scene(LevelSelectorScene(self.game))
                return
            if self.settings_button.collidepoint(event.pos):
                self.game.change_scene(SettingsScene(self.game))
                return
            if self.exit_button.collidepoint(event.pos):
                pygame.quit()
                import sys; sys.exit()
                return
            if self.reset_button.collidepoint(event.pos):
                reset_progress()
                # Odświeżamy scenę menu głównego, aby zaktualizować stan
                self.game.change_scene(MainMenuScene(self.game))
                return

    def update(self): pass

    def render(self):
        glClearColor(0.93, 0.93, 0.93, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        # Tworzenie interfejsu na jednej czystej powierzchni
        surface = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        surface.fill((238, 238, 238))

        # Tytuł
        t_text = self.title_font.render("3D SNAKE GAME", True, (0, 90, 90))
        surface.blit(t_text, ((self.game.width - t_text.get_width()) // 2, 60))

        # Przyciski główne
        pygame.draw.rect(surface, (0, 128, 128), self.play_button, border_radius=4)
        play_text = self.font.render("PLAY", True, (255, 255, 255))
        surface.blit(play_text, (self.play_button.x + (self.play_button.width - play_text.get_width()) // 2, self.play_button.y + 11))

        pygame.draw.rect(surface, (0, 128, 128), self.settings_button, border_radius=4)
        settings_text = self.font.render("SETTINGS", True, (255, 255, 255))
        surface.blit(settings_text, (self.settings_button.x + (self.settings_button.width - settings_text.get_width()) // 2, self.settings_button.y + 11))

        pygame.draw.rect(surface, (120, 120, 120), self.exit_button, border_radius=4)
        exit_text = self.font.render("EXIT", True, (255, 255, 255))
        surface.blit(exit_text, (self.exit_button.x + (self.exit_button.width - exit_text.get_width()) // 2, self.exit_button.y + 11))

        # Przycisk Reset
        pygame.draw.rect(surface, (215, 90, 90), self.reset_button, border_radius=4)
        r_text = self.small_font.render("RESET PROGRESS", True, (255, 255, 255))
        surface.blit(r_text, (self.reset_button.x + (self.reset_button.width - r_text.get_width()) // 2, self.reset_button.y + 8))

        # Konwersja i mapowanie na teksturę OpenGL
        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_TEXTURE_2D); tex_id = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tex_id)
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
        
        glDeleteTextures([tex_id]); glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_MODELVIEW); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glPopAttrib()


# =========================
# LEVEL SELECTOR SCENE
# =========================
class LevelSelectorScene(Scene):
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)
        
        self.levels_data = load_all_levels()
        self.level_rects = {}
        
        self.max_unlocked = get_max_unlocked_level()
        
        button_w = 260
        button_h = 45
        gap_x = 40  
        gap_y = 15  
        start_y = 120
        
        total_grid_width = (button_w * 2) + gap_x
        start_x = (self.game.width - total_grid_width) // 2
        
        for i, lvl in enumerate(self.levels_data):
            col = i % 2      
            row = i // 2      
            x = start_x + col * (button_w + gap_x)
            y = start_y + row * (button_h + gap_y)
            
            self.level_rects[lvl["id"]] = pygame.Rect(x, y, button_w, button_h)
            
        self.back_button = pygame.Rect((self.game.width - 300) // 2, 440, 300, 45)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                self.game.change_scene(MainMenuScene(self.game))
                return
            
            for lvl in self.levels_data:
                lvl_id = lvl["id"]
                if self.level_rects[lvl_id].collidepoint(event.pos):
                    if lvl_id <= self.max_unlocked:
                        self.game.change_scene(GameScene(self.game, lvl))
                    else:
                        print(f"[INFO] Poziom {lvl_id} jest zablokowany! Ukończ poprzednie etapy.")
                    return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_scene(MainMenuScene(self.game))

    def update(self): pass

    def render(self):
        glClearColor(0.93, 0.93, 0.93, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        surface = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        surface.fill((238, 238, 238))

        title_text = self.title_font.render("SELECT LEVEL", True, (0, 90, 90))
        surface.blit(title_text, ((self.game.width - title_text.get_width()) // 2, 45))

        for lvl in self.levels_data:
            lvl_id = lvl["id"]
            rect = self.level_rects[lvl_id]
            
            if lvl_id <= self.max_unlocked:
                color = (0, 128, 128)        
                text_color = (255, 255, 255)
                display_name = lvl["name"]
            else:
                color = (180, 180, 180)      
                text_color = (120, 120, 120)
                display_name = f"{lvl['name']} [LOCKED]"
                
            pygame.draw.rect(surface, color, rect, border_radius=4)
            
            lvl_text = self.font.render(display_name, True, text_color)
            text_x = rect.x + (rect.width - lvl_text.get_width()) // 2
            text_y = rect.y + (rect.height - lvl_text.get_height()) // 2
            surface.blit(lvl_text, (text_x, text_y))

        pygame.draw.rect(surface, (255, 127, 80), self.back_button, border_radius=4)
        back_text = self.font.render("BACK", True, (255, 255, 255))
        back_x = self.back_button.x + (self.back_button.width - back_text.get_width()) // 2
        back_y = self.back_button.y + (self.back_button.height - back_text.get_height()) // 2
        surface.blit(back_text, (back_x, back_y))

        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_TEXTURE_2D); tex_id = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.game.width, self.game.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS); glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0); glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0); glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0); glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0); glEnd()
        
        # DODANO: Poprawne czyszczenie stosu macierzy OpenGL dla uniknięcia freeze
        glDeleteTextures([tex_id]); glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_MODELVIEW); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glPopAttrib()


# =========================
# GAME OVER SCENE
# =========================
class GameOverScene(Scene):
    def __init__(self, game, level_data):
        self.game = game
        self.level_data = level_data
        self.title_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        
        self.retry_button = pygame.Rect((self.game.width - 200) // 2, 250, 200, 55)
        self.menu_button = pygame.Rect((self.game.width - 200) // 2, 330, 200, 55)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.retry_button.collidepoint(event.pos):
                self.game.change_scene(GameScene(self.game, self.level_data))
            elif self.menu_button.collidepoint(event.pos):
                self.game.change_scene(MainMenuScene(self.game))

    def update(self): pass

    def render(self):
        glClearColor(0.93, 0.93, 0.93, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        surface = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        surface.fill((238, 238, 238))

        title_text = self.title_font.render("GAME OVER!", True, (180, 40, 40))
        surface.blit(title_text, ((self.game.width - title_text.get_width()) // 2, 120))

        pygame.draw.rect(surface, (0, 128, 128), self.retry_button, border_radius=4)
        pygame.draw.rect(surface, (255, 127, 80), self.menu_button, border_radius=4)

        retry_text = self.font.render("RETRY", True, (255, 255, 255))
        menu_text = self.font.render("MENU", True, (255, 255, 255))

        surface.blit(retry_text, (self.retry_button.x + (self.retry_button.width - retry_text.get_width()) // 2, self.retry_button.y + 14))
        surface.blit(menu_text, (self.menu_button.x + (self.menu_button.width - menu_text.get_width()) // 2, self.menu_button.y + 14))

        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_TEXTURE_2D); tex_id = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.game.width, self.game.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS); glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0); glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0); glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0); glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0); glEnd()
        glDeleteTextures([tex_id]); glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_MODELVIEW); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glPopAttrib()


# =========================
# LEVEL WIN SCENE
# =========================
class LevelWinScene(Scene):
    def __init__(self, game, level_data):
        self.game = game
        self.level_data = level_data
        self.title_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        
        self.next_lvl_data = get_next_level(self.level_data["id"])
        
        self.next_button = pygame.Rect((self.game.width - 200) // 2, 250, 200, 55) if self.next_lvl_data else None
        self.menu_button = pygame.Rect((self.game.width - 200) // 2, 330, 200, 55)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.next_button and self.next_button.collidepoint(event.pos):
                self.game.change_scene(GameScene(self.game, self.next_lvl_data))
            elif self.menu_button.collidepoint(event.pos):
                self.game.change_scene(MainMenuScene(self.game))

    def update(self): pass

    def render(self):
        glClearColor(0.93, 0.93, 0.93, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        surface = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        surface.fill((238, 238, 238))

        title_text = self.title_font.render("LEVEL CLEARED!", True, (40, 140, 40))
        surface.blit(title_text, ((self.game.width - title_text.get_width()) // 2, 120))

        if self.next_button:
            pygame.draw.rect(surface, (0, 128, 128), self.next_button, border_radius=4)
            next_text = self.font.render("NEXT LEVEL", True, (255, 255, 255))
            surface.blit(next_text, (self.next_button.x + (self.next_button.width - next_text.get_width()) // 2, self.next_button.y + 14))

        pygame.draw.rect(surface, (255, 127, 80), self.menu_button, border_radius=4)
        menu_text = self.font.render("MENU", True, (255, 255, 255))
        surface.blit(menu_text, (self.menu_button.x + (self.menu_button.width - menu_text.get_width()) // 2, self.menu_button.y + 14))

        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_TEXTURE_2D); tex_id = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.game.width, self.game.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS); glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0); glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0); glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0); glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0); glEnd()
        glDeleteTextures([tex_id]); glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_MODELVIEW); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glPopAttrib()


# =========================
# SETTINGS SCENE
# =========================
class SettingsScene(Scene):
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)
        
        self.actions = [
            ("MOVE_NORTH", "Move Forward"),
            ("MOVE_SOUTH", "Move Backward"),
            ("MOVE_WEST", "Move Left"),
            ("MOVE_EAST", "Move Right"),
            ("MOVE_UP", "Move Up"),
            ("MOVE_DOWN", "Move Down")
        ]
        
        self.button_rects = {}
        start_y = 120
        for action_key, _ in self.actions:
            self.button_rects[action_key] = pygame.Rect(450, start_y, 200, 35)
            start_y += 45
            
        self.sens_rect = pygame.Rect(450, start_y + 10, 200, 35)
        self.back_button = pygame.Rect(200, 490, 400, 45)
        self.active_action = None
        self.temp_sens_str = ""

    def handle_event(self, event):
        if self.active_action == "MOUSE_SENSITIVITY":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    try:
                        val = float(self.temp_sens_str)
                        val = max(0.01, min(5.0, val))
                        self.game.config["MOUSE_SENSITIVITY"] = round(val, 3)
                    except ValueError:
                        pass
                    
                    self.game.save_config()
                    self.active_action = None
                elif event.key == pygame.K_BACKSPACE:
                    self.temp_sens_str = self.temp_sens_str[:-1]
                else:
                    char = event.unicode
                    if char.isdigit() or (char == '.' and '.' not in self.temp_sens_str):
                        if len(self.temp_sens_str) < 5:
                            self.temp_sens_str += char
            return

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
            
            for action_key, rect in self.button_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_action = action_key
                    return
            
            if self.sens_rect.collidepoint(event.pos):
                self.active_action = "MOUSE_SENSITIVITY"
                self.temp_sens_str = str(self.game.config.get("MOUSE_SENSITIVITY", 0.3))
                return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_scene(MainMenuScene(self.game))

    def update(self): pass

    def render(self):
        glClearColor(0.9, 0.9, 0.9, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        surface = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        surface.fill((238, 238, 238))

        title_text = self.title_font.render("SETTINGS", True, (0, 90, 90))
        surface.blit(title_text, ((self.game.width - title_text.get_width()) // 2, 35))

        for action_key, label in self.actions:
            rect = self.button_rects[action_key]
            if self.active_action == action_key:
                pygame.draw.rect(surface, (0, 160, 160), rect, border_radius=4)
                key_text_str = "Press any key..."
            else:
                pygame.draw.rect(surface, (0, 128, 128), rect, border_radius=4)
                current_key_code = self.game.config.get(action_key, 0)
                key_text_str = pygame.key.name(current_key_code).upper()

            lbl_surf = self.font.render(label, True, (40, 40, 40))
            surface.blit(lbl_surf, (150, rect.y + 6))
            key_surf = self.font.render(key_text_str, True, (255, 255, 255))
            surface.blit(key_surf, (rect.x + (rect.width - key_surf.get_width()) // 2, rect.y + 6))

        if self.active_action == "MOUSE_SENSITIVITY":
            pygame.draw.rect(surface, (0, 160, 160), self.sens_rect, border_radius=4)
            sens_text_str = self.temp_sens_str + "_"
        else:
            pygame.draw.rect(surface, (0, 128, 128), self.sens_rect, border_radius=4)
            sens_text_str = str(self.game.config.get('MOUSE_SENSITIVITY', 0.3))

        lbl_sens = self.font.render("Mouse sensitivity:", True, (40, 40, 40))
        surface.blit(lbl_sens, (150, self.sens_rect.y + 6))
        sens_surf = self.font.render(sens_text_str, True, (255, 255, 255))
        surface.blit(sens_surf, (self.sens_rect.x + (self.sens_rect.width - sens_surf.get_width()) // 2, self.sens_rect.y + 6))

        pygame.draw.rect(surface, (255, 127, 80), self.back_button, border_radius=4)
        back_text = self.font.render("BACK", True, (255, 255, 255))
        surface.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + 11))

        text_data = pygame.image.tostring(surface, "RGBA", True)
        glEnable(GL_TEXTURE_2D); tex_id = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.game.width, self.game.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS); glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0); glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0); glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0); glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0); glEnd()
        glDeleteTextures([tex_id]); glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_MODELVIEW); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glPopAttrib()


# =========================
# GAME LEVEL (3D OPENGL)
# =========================
class GameScene(Scene):
    def __init__(self, game, level_data):
        self.game = game
        self.level_data = level_data
        
        self.grid_size = level_data.get("grid_size", 10)
        self.foods_to_win = level_data.get("foods_to_win", 1)
        self.foods_eaten = 0
        
        self.world_size = 8.0
        self.cell_size = self.world_size / self.grid_size

        self.yaw = 45.0
        self.pitch = 30.0

        self.snake = Snake()
        
        snake_data = level_data.get("snake_start", [])
        if snake_data:
            self.snake.segments = [
                SnakeSegment(Position3D(p["x"], p["y"], p["z"]), is_head=(i == 0)) 
                for i, p in enumerate(snake_data)
            ]
        else:
            self.snake.segments = [SnakeSegment(Position3D(1, 1, 1), is_head=True)]
        
        food_data = level_data.get("food_start", {"x": 2, "y": 2, "z": 2})
        self.food = Food(Position3D(food_data["x"], food_data["y"], food_data["z"]))
        
        self.obstacles = [
            Obstacle(Position3D(p["x"], p["y"], p["z"])) 
            for p in level_data.get("obstacles", [])
        ]
        
        self.dispatcher = RenderDispatcher()
        self.move_interval = 300
        self.last_move_time = pygame.time.get_ticks()
        
    def game_over(self):
        self.game.change_scene(GameOverScene(self.game, self.level_data))

    def on_food_eaten(self):
        self.foods_eaten += 1
        if self.foods_eaten >= self.foods_to_win:
            current_level_id = self.level_data["id"]
            current_max = get_max_unlocked_level()

            if current_level_id == current_max:
                save_progress(current_max + 1)
                print(f"[PROGRESS] Odblokowano poziom {current_level_id + 1}!")
            self.game.change_scene(LevelWinScene(self.game, self.level_data))
        else:
            self.food.randomize_position(self)

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
            sensitivity = self.game.config.get("MOUSE_SENSITIVITY", 0.3)
            self.yaw += dx * sensitivity
            self.pitch += dy * sensitivity
            
            #self.pitch = max(-91, min(91, self.pitch))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_scene(LevelSelectorScene(self.game))
            
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
        self.dispatcher.dispatch(self.food, self.cell_size)
        for obs in self.obstacles:
            self.dispatcher.dispatch(obs, self.cell_size)

        self.draw_grid()