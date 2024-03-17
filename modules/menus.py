import pygame
from .config import *


class Button():
    def __init__(self, master, pos, action, button_list, color_text=(255, 255, 255), color_shadow=(105, 75, 105)):

        self.master = master
        self.pos = pos
        self.action = action
        self.screen = pygame.display.get_surface()
        self.color_text = color_text
        self.mouse_hover = False
        self.hover_sound_played = False


        self.image = self.master.font.render(action.upper(), False, self.color_text)
        self.rect = self.image.get_rect(center=pos)
        # self.detection_rect = self.rect.inflate(10,10)
        self.detection_rect = self.rect.inflate(0,0)

        self.underline = pygame.Surface((self.image.get_width(), 1))
        self.underline.fill(self.color_text)
        self.underline_rect = self.underline.get_rect(midtop=(self.rect.midbottom))

        self.shadow = self.master.font.render(action.upper(), False, color_shadow)
        self.shadow.set_alpha(200)
        

        button_list.append(self)

    def interact(self, mouse_pos, click=False):

        if click and self.mouse_hover:
            if self.action not in ("start", "resume"):
                pass
                # self.master.sounds["UI_Select"].play()

            return self.action
        self.mouse_hover = self.detection_rect.collidepoint(mouse_pos)
        if self.mouse_hover:
            if not self.hover_sound_played:
                self.hover_sound_played = True
                # self.master.sounds["UI_Hover"].play()
        else:self.hover_sound_played = False

    def draw(self):
        
        if not self.mouse_hover:
            self.screen.blit(self.shadow, (self.rect.left-2, self.rect.top+2))
        else:
            self.screen.blit(self.underline, self.underline_rect)

        self.screen.blit(self.image, self.rect)


class Slider:

    def __init__(self, master, pos, action, button_list, length, min_value=0, max_value=100, default_value=0, step_value=1, color_text=(255, 255, 255), color_shadow=(105, 75, 105)):

        self.master = master
        self.screen = pygame.display.get_surface()
        self.pos = pos
        self.action = action
        self.length = length
        self.min_value = min_value
        self.max_value = max_value
        self.step_value = step_value
        self._value = default_value
        self.value = self._value

        self.color_text = color_text
        self.color_shadow = color_shadow

        self.title = self.master.font.render(action.upper(), False, color_text)
        self.rect_title = self.title.get_rect(bottomleft=(pos[0]-length/2+2, pos[1]-2))
        self.detection_rect = pygame.Rect(self.pos[0]-self.length/2, self.pos[1], self.length, 4)

        self.underline = pygame.Surface((self.title.get_width(), 1))
        self.underline.fill(color_text)
        self.underline_rect = self.underline.get_rect(midtop=(self.rect_title.midbottom))

        self.shadow = self.master.font.render(action.upper(), False, color_shadow)
        self.shadow.set_alpha(200)
        
        button_list.append(self)

        self.activated = False

    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, new_value):
        new_value = min(self.max_value, max(self.min_value, new_value))
        self._value = (new_value-self.min_value) // self.step_value * self.step_value + self.min_value

    def interact(self, mouse_pos, click=False):

        if self.activated:
            val = (mouse_pos[0] - self.detection_rect.left) / self.length * (self.max_value-self.min_value) + self.min_value
            self.value = round(val)

        if click and self.detection_rect.collidepoint(mouse_pos):
            self.activated = True
            # self.master.sounds["UI_Hover"].play()
        if not pygame.mouse.get_pressed()[0]:
            self.activated = False


    def draw(self):
        
        if not self.activated:
            self.screen.blit(self.shadow, (self.rect_title.left-2, self.rect_title.top+2))
        else:
            self.screen.blit(self.underline, self.underline_rect)
        self.screen.blit(self.title, self.rect_title)

        value_surf = self.master.font_1.render(str(int(self._value)), True, self.color_text)
        self.screen.blit(value_surf, (self.detection_rect.right-value_surf.get_width(), self.detection_rect.top-value_surf.get_height()))

        self.screen.fill(self.color_shadow, self.detection_rect)
        if self._value == self.min_value:
            bar_filled = 0
        else:
            bar_filled = self.length * ((self._value-self.min_value)/(self.max_value-self.min_value))
        self.screen.fill(self.color_text, (self.detection_rect.x, self.detection_rect.y, bar_filled, self.detection_rect.height))


class MainMenu():

    def __init__(self, master):
        self.master = master
        self.master.main_menu = self
        self.screen = pygame.display.get_surface()
        self.title_surf = self.master.font_big.render(GAME_NAME, False, (235, 10, 5))
        self.title_rect = self.title_surf.get_rect(midtop=(W/2, H*0.1))
        self.title_shadow = self.master.font_big.render(GAME_NAME, False, (255, 20, 25))
        self.title_shadow.set_alpha(100)
        self.buttons:list[Button] = []
        self.create_buttons()
        
    def create_buttons(self):

        col = (185, 198, 194)
        Button(self.master, (W//2, H*0.37), 'start', self.buttons, col)
        Button(self.master, (W//2, H*0.49), 'fullscreen', self.buttons, col)
        Button(self.master, (W//2, H*0.61), 'settings', self.buttons, col)
        Button(self.master, (W//2, H*0.73), 'quit', self.buttons, col)

    def update(self):

        for event in pygame.event.get((pygame.MOUSEBUTTONDOWN)):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                for button in self.buttons:
                    action = button.interact(event.pos, click=True)
                    if action == 'start':
                        # self.master.music.change_track("in_game")
                        # self.master.sounds["UI_Select"].play()
                        self.master.app.state = self.master.app.INTRO_CUTSCENE
                    elif action == 'fullscreen':
                        pygame.display.toggle_fullscreen()
                    elif action == 'settings':
                        self.master.settings_menu.open(bg_color=0)
                    elif action == 'quit':
                        pygame.quit()
                        raise SystemExit
                    if action is not None:
                        return

    def draw(self):

        self.screen.fill(0)

        self.screen.blit(self.title_shadow, (self.title_rect.x-2, self.title_rect.y+2))
        self.screen.blit(self.title_surf, self.title_rect)

        for button in self.buttons:
            button.draw()
            button.interact(pygame.mouse.get_pos())

    def run(self):
        self.update()
        self.draw()


class PauseMenu():

    def __init__(self, master):
        self.master = master
        self.master.pause_menu = self

        self.screen = pygame.display.get_surface()
        self.bg_overlay = pygame.Surface(self.screen.get_size())
        self.bg_overlay.set_alpha(70)

        self.buttons:list[Button] = []
        self.create_buttons()
        
    def create_buttons(self):

        col = (185, 198, 194)
        Button(self.master, (W//2, H*0.26), 'resume', self.buttons, col)
        Button(self.master, (W//2, H*0.38), 'fullscreen', self.buttons, col)
        Button(self.master, (W//2, H*0.5), 'restart level', self.buttons, col)
        Button(self.master, (W//2, H*0.62), 'settings', self.buttons, col)
        Button(self.master, (W//2, H*0.74), 'quit', self.buttons, col)

    def open(self):
        self.master.app.state = self.master.app.PAUSE
        self.bg = pygame.transform.gaussian_blur(self.screen, 5, False)
        # self.master.sounds["UI_Pause"].play()

    def update(self):
        
        for event in pygame.event.get((pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.master.app.state = self.master.app.IN_GAME
                # self.master.sounds["UI_Return"].play()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                for button in self.buttons:
                    action = button.interact(event.pos, click=True)
                    if action == 'resume':
                        self.master.app.state = self.master.app.IN_GAME
                        # self.master.sounds["UI_Return"].play()
                    elif action == 'fullscreen':
                        pygame.display.toggle_fullscreen()
                    elif action == 'restart level':
                        # self.master.app.death_screen()
                        self.master.game.paused = False
                        self.master.player.get_hurt()
                    elif action == 'settings':
                        self.master.settings_menu.open(bg=self.bg, bg_overlay=self.bg_overlay)
                    elif action == 'quit':
                        pygame.quit()
                        raise SystemExit
                    if action is not None:
                        return
    def draw(self):

        self.screen.blit(self.bg, (0, 0))
        self.screen.blit(self.bg_overlay, (0, 0))

        for button in self.buttons:
            button.draw()
            button.interact(pygame.mouse.get_pos())

    def run(self):

        self.draw()
        self.update()


class SettingsMenu:

    def __init__(self, master):
        self.master = master
        self.master.settings_menu = self
        self.screen = pygame.display.get_surface()
        self.title_surf = self.master.font_big.render("Settings", False, (235, 10, 5))
        self.title_rect = self.title_surf.get_rect(midtop=(W/2, H*0.1))
        self.title_shadow = self.master.font_big.render("Settings", False, (255, 20, 25))
        self.title_shadow.set_alpha(100)
        self.buttons:list[Button] = []
        self.create_buttons()
        
    def create_buttons(self):

        col = (185, 198, 194)
        self.fps_slider = Slider(self.master, (W//2, H*0.5), "fps", self.buttons, 75, max_value=256, color_text=col, default_value=FPS)
        Button(self.master, (W//2, H*0.6), 'back', self.buttons, col)

    def open(self, *, bg=None, bg_overlay=None, bg_color=None):

        self.prev_state = self.master.app.state
        self.master.app.state = self.master.app.SETTINGS
        self.bg = bg
        self.bg_overlay = bg_overlay
        self.bg_color = bg_color

    def update(self):

        for event in pygame.event.get((pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN)):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.master.app.state = self.prev_state
                # self.master.sounds["UI_Return"].play()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                for button in self.buttons:
                    action = button.interact(event.pos, click=True)
                    if action == 'back':
                        # self.master.sounds["UI_Select"].play()
                        self.master.fps = self.fps_slider.value
                        self.master.app.state = self.prev_state
                    if action is not None:
                        return

    def draw(self):

        if self.bg is not None:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill(self.bg_color)
        if self.bg_overlay is not None:
            self.screen.blit(self.bg_overlay, (0, 0))

        self.screen.blit(self.title_shadow, (self.title_rect.x-2, self.title_rect.y+2))
        self.screen.blit(self.title_surf, self.title_rect)

        for button in self.buttons:
            button.draw()
            button.interact(pygame.mouse.get_pos())

    def run(self):

        self.update()
        self.draw()
