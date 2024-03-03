import pygame
import random
from .engine import *
from .config import *
from .entity import *
from math import sin, cos, pi, radians, degrees

SPRITES = {}

def load_materials():
    
    global SPRITES

    SPRITES["player"] = import_sprite_sheets("graphics/player")


class Player(pygame.sprite.Sprite):

    def __init__(self, master, grps):

        super().__init__(grps)
        self.master = master
        self.master.player = self
        self.screen = pygame.display.get_surface()

        self.animations = SPRITES["player"]
        self.image = self.animations["swim"][0]
        self.rect = self.image.get_rect()

        self.tri_vignette = pygame.image.load("graphics/tri_vignette.png").convert_alpha()
        self.pl_vignette = pygame.image.load("graphics/player_vignette.png").convert_alpha()

        self.anim_index = 0
        self.anim_speed = 0.15

        self.hitbox = pygame.FRect(0, 0, 16, 16)
        # self.hitbox.center = pos
        # self.rect.center = pos
        self.velocity = pygame.Vector2()
        self.max_speed = 1.3
        self.disgiuse_speed = 0.8
        self.acceleration = 0.15
        self.deceleration = 0.3
        self.direction = pygame.Vector2(0, 1)

        self.moving = False
        self.is_dead = False
        self.flashlight = True
        self.in_disgiuse = False

        self.shoot_cooldown_timer = CustomTimer()
        self.SHOOT_COOLDOWN = 1000

    def update_image(self):

        # if self.moving: state = "swim"
        if self.in_disgiuse: state = "cover_t_swim"
        else: state = "swim"

        try:
            self.image = self.animations[state][int(self.anim_index)]
        except IndexError:
            self.image = self.animations[state][0]
            self.anim_index = 0

        if self.moving: self.anim_speed = 0.15
        # else: self.anim_speed = 0.08
        else: self.anim_speed = 0

        self.anim_index += self.anim_speed *self.master.dt

        mirror = self.direction.dot((-1, 0)) > 0
        self.image = pygame.transform.flip(self.image, False, mirror)
        # self.image = pygame.transform.rotozoom(self.image, round(self.direction.angle_to((1, 0))/15)*15, 1)
        self.image = pygame.transform.rotate(self.image, round(self.direction.angle_to((1, 0))/15)*15)
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
            speed = self.disgiuse_speed if self.in_disgiuse else self.max_speed
            self.velocity.move_towards_ip( self.direction*speed, self.acceleration *self.master.dt)
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
                if event.button == 3 and not self.shoot_cooldown_timer.running:
                    self.spawn_bullet()
                    self.shoot_cooldown_timer.start(self.SHOOT_COOLDOWN)
                    
            if event.type == pygame.MOUSEBUTTONUP:
                pass
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.master.game.pause_game()
                if event.key == pygame.K_v:
                    self.master.debug.vignette = not self.master.debug.vignette
                if event.key == pygame.K_SPACE:
                    self.check_on_disguise()
                if event.key == pygame.K_x:
                    self.flashlight = not self.flashlight

        self.shoot_cooldown_timer.check()

    def spawn_bullet(self):

        direc = pygame.Vector2()
        direc.from_polar((1, -round(self.direction.angle_to((1, 0))/15)*15))
        Bullet(self.master, [self.master.level.player_bullets_grp],
                        self.hitbox.center, direc)
        
    def check_on_disguise(self):

        for enemy in self.master.level.enemy_grp.sprites():
            if not self.rect.colliderect(enemy.rect): continue
            if not enemy.dead: continue
            if enemy.get_picked_up():
                self.in_disgiuse = True
        # self.in_disgiuse = not self.in_disgiuse

    def draw(self):

        self.screen.blit(self.image, self.rect.topleft + self.master.offset)

        if self.master.debug.vignette:
            vignette = self.master.level.vignette
            vignette.blit(self.pl_vignette, self.rect.center+self.master.offset-\
                          (self.pl_vignette.get_width()/2, self.pl_vignette.get_height()/2)+(W/2, H/2),
                          special_flags=pygame.BLEND_RGBA_MIN)
            if self.flashlight:
                radius = self.tri_vignette.get_width()/2
                tri_vignette = pygame.transform.rotate(self.tri_vignette, (self.direction.angle_to((1, 0))))
                # bg_tri_vignette = pygame.Surface(tri_vignette.get_size(), pygame.SRCALPHA)
                # bg_tri_vignette.fill((0, 0, 0, 255))
                # bg_tri_vignette.blit(tri_vignette, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                rect = tri_vignette.get_rect(center = self.rect.center+self.master.offset)
                vignette.blit(tri_vignette, rect.topleft + self.direction*radius + (W/2, H/2),
                              special_flags=pygame.BLEND_RGBA_MIN)


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

