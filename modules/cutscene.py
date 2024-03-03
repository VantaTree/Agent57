import pygame
from .engine import *
from .config import *

CUTSCENE_TEXT = {
    "intro":[
        "Ever since the Fish left us and went up into space, We never had fish meat since, the people crave it dearly",
        "I hope this robot fish will bring some back. Then we will have a Monopoly MuhahAHAHaHa.",
    ],
    "end won":[
        "This is what we strive for.\nWe can finally get some Fish Meat.",
    ],
    "end lost":[
        "Bad Boy,\nNow we have no food",
    ],
    "transition":[], # supposed to be empty
    "you_died":[
        "You Died!"
    ],
}


class FiFo:
    """fade-in fade-out cutscene"""

    def __init__(self, master, type, change_state_to, continue_text=True, text_color=0xFFFFFFFF) -> None:

        self.master = master
        self.screen = pygame.display.get_surface()

        self.black_bg = pygame.Surface(self.screen.get_size())
        self.black_bg.set_alpha(0)

        self.text_color = text_color
        self.change_state_to = change_state_to

        self.type = type
        self.texts = CUTSCENE_TEXT[type]
        self.page_index = 0
        self.alpha = 0
        self.halt = False
        self.skip = False

        self.increment = 1
        self.alpha_speed = 8

        self.letter_index = 0
        self.full_text_shown = False

        self.continue_text = continue_text

        if self.type != "transition":
            if self.continue_text:
                self.bottom_text = self.master.font_1.render("Click to Continue", False, (255, 255, 255))
                self.bottom_text_rect = self.bottom_text.get_rect(topleft=(5, 5))

            self.letter_increment_timer = CustomTimer(True)
            self.letter_increment_timer.start(40, 0)

    def check_events(self):

        for event in pygame.event.get((pygame.MOUSEBUTTONUP, pygame.KEYDOWN)):
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.halt:
                    # self.master.sounds["UI_Hover"].play()
                    if not self.full_text_shown:
                        self.full_text_shown = True
                    else:
                        self.increment = -1
                        self.halt = False
                        self.full_text_shown = False
                        self.letter_index = 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.skip = True
                    return
                
    def draw(self):
        
        self.screen.fill((180, 0, 0))
        self.screen.blit(self.black_bg, (0, 0))
        if self.increment == 0 and self.type != "transition":
            if self.continue_text:
                self.screen.blit(self.bottom_text, self.bottom_text_rect)

            if self.full_text_shown:
                text = self.texts[self.page_index]
            else:
                text = self.texts[self.page_index][:self.letter_index]
            text_surf = self.master.font.render(text, False, self.text_color, wraplength=int(W/3*2))
            rect = text_surf.get_rect(center=(W/2, H/2))
            self.screen.blit(text_surf, rect)

    def update(self):

        if self.type != "transition" and self.letter_increment_timer.check() and self.halt and not self.full_text_shown:
            self.letter_index += 1
            # self.master.sounds["SFX_Text"].play()
            if self.letter_index == len(self.texts[self.page_index]):
                self.full_text_shown = True

        else:
            self.black_bg.set_alpha(int(self.alpha))
            self.alpha += self.alpha_speed*self.increment *self.master.dt
            if self.alpha >= 256:
                self.increment = 0
                self.alpha = 255
                if self.type == "transition":
                    self.increment = -1
                else:
                    self.halt = True
            elif self.alpha < 0:
                if self.type == "transition":
                    return True
                self.alpha = 0
                self.increment = 1
                self.page_index += 1
                if self.page_index == len(self.texts):
                    return True

    def run(self):

        self.check_events()
        if self.skip:
            self.master.app.state = self.change_state_to
            return True
        result = self.update()
        self.draw()
        if result:
            self.master.app.state = self.change_state_to
            # self.master.sounds["SFX_Spawn"].play()
        return result
    