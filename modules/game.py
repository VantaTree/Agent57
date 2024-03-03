import pygame
from .engine import *
from .config import *
from .level import Level
from .menus import PauseMenu
from .player import Player, load_materials

class Game:

    def __init__(self, master):

        self.master = master
        self.master.game = self
        self.screen = pygame.display.get_surface()

        load_materials()

        self.master.offset = pygame.Vector2(0, 0)

        self.which_pilot = 1 # 1234
        self.pause_menu = PauseMenu(master)

        self.player = Player(master, [])
        self.camera = Camera(master)
        self.camera.set_target(self.player, lambda p: p.rect.center + p.direction*TILESIZE)
        self.camera.snap_offset()

        self.level = Level(master, self.player, "test_level")
        # self.level = Level(master, self.player, "level_1")
        # self.level = Level(master, self.player, "level_0")

        self.paused = False

    def pause_game(self):
        if not self.paused:
            self.paused = True
            self.pause_menu.open()

    def run(self):

        if self.paused:
            self.pause_menu.draw()
            self.pause_menu.update()
            return

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
