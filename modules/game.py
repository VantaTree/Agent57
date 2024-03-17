import pygame
from .engine import *
from .config import *
from .level import Level, load_resources
from .player import Player, load_materials

class Game:

    def __init__(self, master):

        self.master = master
        self.master.game = self
        self.screen = pygame.display.get_surface()

        load_materials()
        load_resources()

        self.master.offset = pygame.Vector2(0, 0)

        self.player = Player(master, [])
        self.camera = Camera(master)
        self.camera.set_target(self.player, lambda p: p.rect.center + p.direction*TILESIZE)
        self.camera.snap_offset()

        self.levels = ["test_level", "level_1", "level_0"]
        self.curr_level = 0
        self.level = Level(master, self.player, self.levels[self.curr_level])

    def next_level(self):
        self.curr_level += 1
        if self.curr_level >= len(self.levels):
            self.master.app.finish_game()
            return
        self.master.app.next_level(self.curr_level)
        self.restart_level()

    def restart_level(self):

        self.level = Level(self.master, self.player, self.levels[self.curr_level])
        self.player.velocity.update()
        self.player.dying = False
        self.player.is_dead = False
        self.player.moving = False
        self.player.in_control = True
        self.player.in_disgiuse = False
        self.player.bullets = self.player.max_bullets

    def run(self):

        self.level.vignette = self.level.orig_vignette.copy()
        self.player.update()
        self.camera.update()
        self.level.update()

        self.level.draw_bg()
        # self.camera.draw()
        self.level.draw()
        self.player.draw()
        self.level.draw_fg()        


class Camera:

    def __init__(self, master, target = None, key = None):

        self.master = master
        master.camera = self

        self.camera_rigidness = 0.05

        self.target = target
        self.key = key

    def key(self): pass

    def set_target(self, target, key):

        self.target = target
        self.key = key

    def get_target_pos(self):

        return self.key(self.target)

    def snap_offset(self):

        self.master.offset = (self.get_target_pos() - pygame.Vector2(W/2, H/2)) * -1

    def update_offset(self):

        if self.target == self.master.player:
            self.camera_rigidness = 0.18 if self.master.player.moving else 0.05
        else: self.camera_rigidness = 0.05
        
        self.master.offset -= (self.master.offset + (self.get_target_pos() - pygame.Vector2(W/2, H/2)))\
            * self.camera_rigidness * self.master.dt

    def clamp_offset(self):

        size = self.master.level.size

        if size[0]*TILESIZE <= W: self.master.offset.x = 0
        elif self.master.offset.x > 0: self.master.offset.x = 0
        elif self.master.offset.x < -size[0]*TILESIZE + W:
            self.master.offset.x = -size[0]*TILESIZE + W
        
        if size[1]*TILESIZE <= H:
            self.master.offset.y = 0
        elif self.master.offset.y > 0: self.master.offset.y = 0
        elif self.master.offset.y < -size[1]*TILESIZE + H:
            self.master.offset.y = -size[1]*TILESIZE + H

    def draw(self):

        pass

    def update(self):

        self.update_offset()
        self.clamp_offset()
