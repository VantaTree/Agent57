import pygame
from .config import *
from .engine import *
from random import choice, uniform, randint
from math import sqrt

class ParticleManager:

    def __init__(self, master):

        self.master = master
        master.particle_manager = self

        self.above_grp = CustomGroup()
        self.below_grp = CustomGroup()

    def add(self, type):

        pass

    def update(self):

        pass

class Particle(pygame.sprite.Sprite):

    def __init__(self, master, grps, pos, color="red", size=(1, 1), velocity=(0, 0), force=(0, 0), friction=0, duration=500, fade=True, anchor=None, anchor_pull=0, grow_by=0):

        super().__init__(grps)
        self.master = master
        self.screen = pygame.display.get_surface()

        self.original_image = pygame.Surface(size)
        self.original_image.fill(color)
        self.image = self.original_image
        self.pos = pygame.Vector2(pos)

        self.velocity = pygame.Vector2(velocity)
        self.force = pygame.Vector2(force)
        self.friction = friction
        self.duration = duration
        self.anchor = anchor
        self.anchor_pull = anchor_pull
        self.fade = fade
        self.grow_by = grow_by
        self.growth_scale = 1
        self.alpha = 255
        self.start_time = pygame.time.get_ticks()
        
        self.alive_timer = CustomTimer()

        self.alive_timer.start(duration)

    def draw(self):

        if self.growth_scale != 1:
            self.image = pygame.transform.scale_by(self.original_image, self.growth_scale)
        self.image.set_alpha(self.alpha)
        self.screen.blit(self.image, self.pos-(self.image.get_width()/2, self.image.get_height()/2)+self.master.offset)

    def update(self):

        self.velocity += self.force *self.master.dt
        if self.friction != 0:
            self.velocity.move_towards_ip((0, 0), self.friction *self.master.dt)
        if self.anchor:
            anchor_force = pygame.Vector2(self.anchor[0] - self.rect.centerx, self.anchor[1] - self.rect.centery)
            anchor_force.scale_to_length(self.anchor_pull)
            self.velocity += anchor_force*self.master.dt

        self.pos += self.velocity *self.master.dt

        self.growth_scale += self.grow_by/60 *self.master.dt

        if self.fade:
            self.alpha = 255- (pygame.time.get_ticks()-self.start_time) / self.duration * 255

        if self.alive_timer.check():
            self.kill()
            return