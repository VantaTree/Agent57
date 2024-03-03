import pygame
from .config import *
from .engine import *
from .entity import *

def load_resources():

    global BULLET_SPRITE
    BULLET_SPRITE = pygame.image.load("graphics/bullet.png").convert_alpha()
    return BULLET_SPRITE

class Bullet(pygame.sprite.Sprite):

    def __init__(self, master, grps, pos, direction, speed = 3):

        super().__init__(grps)
        self.master = master
        self.screen = pygame.display.get_surface()

        self.orig_image = BULLET_SPRITE
        self.image = self.orig_image
        # self.bullet_vignette = pygame.image.load("graphics/bullet_vignette.png").convert_alpha()
        # self.bullet_vignette = pygame.image.load("graphics/vignette_bullet.png").convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.FRect(0, 0, 6, 6)
        self.hitbox.center = pos

        self.direction = pygame.Vector2(direction)
        self.speed = speed
        self.angle = self.direction.angle_to([1, 0])

    def update_image(self):

        self.image = pygame.transform.rotate(self.orig_image, self.angle)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def move(self):

        self.hitbox.x += self.direction.x * self.speed * self.master.dt
        self.hitbox.y += self.direction.y * self.speed * self.master.dt

        if is_colliding(self, self.master):
            self.kill()

    def check_hit(self):

        for sprite in self.master.level.enemy_grp.sprites():
            if self.hitbox.colliderect(sprite.rect):
                if sprite.dead: continue
                sprite.get_hurt(1)
                self.kill()
                break

    def update(self):

        self.move()
        self.check_hit()
        self.update_image()

    def draw(self):
        
        self.screen.blit(self.image, self.rect.topleft+self.master.offset)

        # if self.master.debug.vignette:
        #     vignette = self.master.level.vignette
        #     pos = self.rect.center+self.master.offset-(self.bullet_vignette.get_width()/2, self.bullet_vignette.get_height()/2) + (W/2, H/2)
        #     vignette.blit(self.bullet_vignette, pos, special_flags=pygame.BLEND_RGBA_MIN)

