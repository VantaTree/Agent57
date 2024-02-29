import pygame
import random
from .engine import *
from .config import *
from .entity import *
from math import sin, cos, pi, radians, degrees

SPRITES = {}

def load_materials():
    
    global SPRITES

    SPRITES["test"] = import_sprite_sheets("graphics/test")


class Player(pygame.sprite.Sprite):

    def __init__(self, master, grps):

        super().__init__(grps)
        self.master = master
        self.master.player = self
        self.screen = pygame.display.get_surface()

        pos = [32, 32]

        # self.animation = SPRITES["test"]["player"]
        self.animation = [pygame.image.load("graphics/test_player.png").convert_alpha()]
        self.image = self.animation[0]
        self.rect = self.image.get_rect()

        self.anim_index = 0
        self.anim_speed = 0.15

        self.hitbox = pygame.FRect(0, 0, 16, 16)
        self.hitbox.center = pos
        self.rect.center = pos
        self.velocity = pygame.Vector2()
        self.max_speed = 1.1
        self.acceleration = 0.15
        self.deceleration = 0.3
        self.direction = pygame.Vector2(0, 1)

        self.moving = False
        self.is_dead = False
        self.flashlight = True

    def update_image(self):

        try:
            self.image = self.animation[int(self.anim_index)]
        except IndexError:
            self.image = self.animation[0]
            self.anim_index = 0

        if self.moving: self.anim_speed = 0.15
        else: self.anim_speed = 0.08

        self.anim_index += self.anim_speed *self.master.dt
        # self.image = pygame.transform.rotozoom(self.image, self.direction.angle_to((0, -1))//15*15, 1)
        self.image = pygame.transform.rotate(self.image, round(self.direction.angle_to((0, -1))/15)*15)
        self.rect = self.image.get_rect(center = self.hitbox.center)


    def get_input(self):

        direction =  pygame.mouse.get_pos() - self.master.offset - self.hitbox.center
        try:
            self.direction = direction.normalize()
        except ValueError:
            self.direction = direction
        
        self.moving = pygame.mouse.get_pressed()[0]

    def apply_force(self):


        if self.moving:
            self.velocity.move_towards_ip( self.direction*self.max_speed, self.acceleration *self.master.dt)
        else:
            self.velocity.move_towards_ip( (0, 0), self.deceleration *self.master.dt)

    def move(self):

        self.hitbox.centerx += self.velocity.x * self.master.dt
        do_collision(self, 0, self.master)
        self.hitbox.centery += self.velocity.y * self.master.dt
        do_collision(self, 1, self.master)
        do_collision(self, 2, self.master)

    def process_events(self):

        for event in pygame.event.get((pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN)):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    self.flashlight = not self.flashlight
            if event.type == pygame.MOUSEBUTTONUP:
                pass
                    # self.master.game.pause_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v:
                    self.master.debug.pl_vignette = not self.master.debug.pl_vignette

    def draw(self):

        self.screen.blit(self.image, self.rect.topleft + self.master.offset)
        # if self.master.debug.on:
        #     pygame.draw.rect(self.screen, "blue", (self.hitbox.x+self.master.offset.x, self.hitbox.y+self.master.offset.y, self.hitbox.width, self.hitbox.height), 1)

    def update(self):

        self.process_events()
        self.get_input()
        self.apply_force()
        self.move()
        self.update_image()

        self.master.debug("pos: ", (round(self.hitbox.centerx, 2), round(self.hitbox.bottom, 2)))
        self.master.debug("angle: ", round(self.direction.angle_to((0, -1))))

