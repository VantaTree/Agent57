import pygame
from .config import *
from .engine import *
from random import randint, choice
from math import sin
from .entity import *

ENEMY_SPRITES = {}

def load_enemy_sprites():

    global ENEMY_SPRITES

    pass
        # ENEMY_SPRITES[folder] = import_sprite_sheets(F"graphics/enemies/{folder}")


IDLE = 0
AGRO = 1
FOLLOW = 2
ATTACK = 3
ANGRY = 4
DYING = 5

class Enemy(pygame.sprite.Sprite):

    def __init__(self, master, grps, level, sprite_type, pos, hitbox, attack_rect, max_health, max_speed, acc, dcc, **kwargs):

        super().__init__(grps)
        self.master = master
        self.screen = pygame.display.get_surface()
        self.level = level

        self.sprite_type = sprite_type
        # self.animations = ENEMY_SPRITES[sprite_type]
        # self.image = self.animations["idle"][0]
        self.animations = [pygame.image.load("graphics/test_enemy.png").convert_alpha()]
        self.image = self.animations[0]
        self.rect = self.image.get_rect(topleft=pos)

        self.anim_index = 0
        self.anim_speed = 0.15

        self.attack_rect_dimen = attack_rect
        self.attack_rect = pygame.FRect(*attack_rect)

        self.pos = pos
        self.hitbox = pygame.FRect(*hitbox)
        self.hitbox.midbottom = self.rect.midbottom
        self.velocity = pygame.Vector2()
        self.target_direc = pygame.Vector2()
        self.max_speed = max_speed
        self.acceleration = acc
        self.deceleration = dcc
        self.facing_direc = pygame.Vector2(choice((1, -1)), 0)

        self.state = IDLE
        self.moving = False
        self.max_health = max_health
        self.health = self.max_health
        self.invinsible = False
        self.hurting = False

        self.ambience_dist = kwargs.get("ambience_dist") # makes creature noises within this distance
        self.calm_dist = kwargs.get("calm_dist") # clams the creature after this distance
        self.follow_dist = kwargs.get("follow_dist") # follows within this distance
        self.attack_dist = kwargs.get("attack_dist") # initiates an attack in this distance

        self.invinsibility_timer = CustomTimer()
        self.hurt_for = CustomTimer()

    def update_image(self):

        if self.state == DYING: state = "dead"
        elif self.moving: state = "run"
        elif self.state == ATTACK: state = "attack"
        else: state = "idle"

        try:
            # image = self.animations[state][int(self.anim_index)]
            self.image = self.animations[int(self.anim_index)]
        except IndexError:
            # image = self.animations[state][0]
            self.image = self.animations[0]
            self.anim_index = 0
            if self.state == ATTACK:
                self.state = FOLLOW
            elif self.state == DYING:
                self.die()
                return

        if self.moving: self.anim_speed = 0.15
        elif self.state == ATTACK: self.anim_speed = 0.18
        else: self.anim_speed = 0.08

        self.anim_index += self.anim_speed *self.master.dt

        self.image = pygame.transform.rotate(self.image, round(self.facing_direc.angle_to((0, -1))/15)*15)
        self.rect = self.image.get_rect(midbottom = self.hitbox.midbottom)

        if self.invinsible:
            if self.hurting:
                self.image.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
                self.image.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MIN)
            self.image.set_alpha(int((sin(pygame.time.get_ticks()/30)+1)/2 *255))

    def apply_force(self):

        if self.moving:
            self.velocity.move_towards_ip( self.target_direc*self.max_speed, self.acceleration *self.master.dt)
        else:
            self.velocity.move_towards_ip( (0, 0), self.deceleration *self.master.dt)

        if self.moving:
            for enemy in self.level.enemy_grp.sprites():
                if enemy is self: continue
                if self.rect.colliderect(enemy.rect):
                    try:
                        space_vec = pygame.Vector2(self.rect.centerx-enemy.rect.centerx, self.rect.centery-enemy.rect.centery)
                        self.velocity += space_vec.normalize() * 0.008
                    except ValueError: pass

    def control(self):

        self.moving = bool(self.target_direc) and not self.hurting
        if self.moving:
            self.facing_direc.update(self.target_direc)

    def check_timers(self):

        if self.invinsibility_timer.check():
            self.invinsible = False
        if self.hurt_for.check():
            self.hurting = False

    def move(self):

        self.hitbox.centerx += self.velocity.x * self.master.dt
        do_collision(self, 0, self.master)
        self.hitbox.centery += self.velocity.y * self.master.dt
        do_collision(self, 1, self.master)
        do_collision(self, 2, self.master)

    def process_events(self):

        if self.state == DYING: return

        dist = dist_sq(self.master.player.rect.center, self.rect.center)
        if dist < self.follow_dist**2:
            if self.state == IDLE:
                self.state = AGRO
        elif self.state != ANGRY:
            self.state = IDLE
            self.target_direc.update()
        if dist > self.calm_dist**2 and self.state == ANGRY:
            self.state = IDLE
        if self.state in (FOLLOW, ANGRY):
            self.target_direc.update(self.master.player.rect.centerx - self.rect.centerx,
                self.master.player.rect.centery - self.rect.centery)
            try:
                self.target_direc.normalize_ip()
            except ValueError: pass

        if self.state in (AGRO, FOLLOW, ANGRY):
            self.facing_direc.update(self.master.player.rect.centerx - self.rect.centerx,
                self.master.player.rect.centery - self.rect.centery)
            try:
                self.facing_direc.normalize_ip()
            except ValueError: pass
            if dist < self.attack_dist**2:
                self.state = ATTACK
                self.anim_index = 0
                self.target_direc.update()

    def check_player_collision(self):

        pass
        # if self.hitbox.colliderect(self.master.player.hitbox):
        #     self.master.player.get_hurt(1)

    def get_hurt(self, damage):

        if self.invinsible or self.state == DYING: return False
        if self.state in (IDLE, AGRO):
            self.state = ANGRY
        elif self.state != ANGRY: self.state = FOLLOW
        self.health -= damage
        self.velocity.update()
        self.moving = False
        self.hurting = True
        self.invinsible = True
        self.hurt_for.start(200)
        self.invinsibility_timer.start(1_000)

        if self.health <= 0:
            self.state = DYING
            self.anim_index = 0
        return True

    def draw(self):

        self.screen.blit(self.image, self.rect.topleft + self.master.offset)
        # pygame.draw.rect(self.screen, "blue", (self.hitbox.x+self.master.offset.x, self.hitbox.y+self.master.offset.y, self.hitbox.width, self.hitbox.height), 1)
        # pygame.draw.rect(self.screen, "red", (self.attack_rect.x+self.master.offset.x, self.attack_rect.y+self.master.offset.y, self.attack_rect.width, self.attack_rect.height), 1)

    def update(self):

        self.process_events()
        self.check_timers()
        self.control()
        self.apply_force()
        self.move()
        self.check_player_collision()
        self.update_image()