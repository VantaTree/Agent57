import pygame
from .config import *
from .engine import *
from math import ceil

def load_dialogue_sprites():

    global diag_endT, diag_end, diag_middleT, diag_middle, diag_plain

    diag_plain = pygame.image.load("graphics/UI/speech_bubble.png").convert_alpha()
    diag_middleT = pygame.image.load("graphics/UI/speech_bubble_mid.png").convert_alpha()
    diag_endT = diag_plain.subsurface(0, 0, TILESIZE, TILESIZE)
    diag_middle = diag_plain.subsurface(TILESIZE, 0, TILESIZE, TILESIZE)
    diag_end = diag_plain.subsurface(2*TILESIZE, 0, TILESIZE, TILESIZE)
    diag_end = pygame.transform.flip(diag_end, True, False)


class DialogueManager(CustomGroup):

    def __init__(self, master):

        super().__init__()
        self.master = master
        master.dialogue_manager = self

    def create_dialogue(self, anchor, duration, text):

        return Dialogue(self.master, [self], anchor, duration, text)


class Dialogue(pygame.sprite.Sprite):

    def __init__(self, master, grps, anchor, duration, text):

        super().__init__(grps)
        self.master = master
        self.screen = pygame.display.get_surface()

        self.timer = CustomTimer()
        self.timer.start(duration)
        self.anchor = anchor
        self.text = text

    def update(self):

        if self.timer.check():
            self.kill()

    def draw(self):

        text = self.master.font_1.render(self.text, False, (25, 25, 25))

        diag_units = max(3, ceil(text.get_width()/TILESIZE))
        diag = pygame.Surface((diag_units*TILESIZE, TILESIZE), pygame.SRCALPHA)

        diag_rect = diag.get_rect(midbottom = self.anchor.rect.midtop+self.master.offset)
        hit_x, hit_y = 0, 0
        if diag_rect.left < 0:
            diag_rect.left = 0
            hit_x = -1
        elif diag_rect.right > W:
            diag_rect.right = W
            hit_x = 1
        if diag_rect.top < 0:
            diag_rect.top = 0
            hit_y = -1
        elif diag_rect.bottom > H:
            diag_rect.bottom = H
            hit_y = 1

        d1 = diag_endT if hit_x < 0 else diag_end
        d2 = diag_endT if hit_x > 0 else diag_end
        # dm = pygame.transform.flip(diag_middleT, False, True) if hit_y < 0 else diag_middleT
        diag.blit(pygame.transform.flip(d1, False, False), (0, 0))
        diag.blit(pygame.transform.flip(d2, True, False), (TILESIZE*(diag_units-1), 0))
        for i in range(1, diag_units-1):
            dm = diag_middleT if i == diag_units//2 and hit_x == 0 else diag_middle
            diag.blit(dm, (TILESIZE*i, 0))

        self.screen.blit(diag, diag_rect)
        self.screen.blit(text, (diag_rect.centerx-text.get_width()/2, diag_rect.centery-text.get_height()/2))

