import pygame
import random
from .engine import *
from .config import *
from .entity import *
from .projectiles import Bullet, load_resources
from math import sin, cos, pi, radians, degrees

SPRITES = {}

def load_materials():
    
    global SPRITES, BULLET_SPRITE
    BULLET_SPRITE = load_resources()
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

        # self.tri_vignette = pygame.image.load("graphics/tri_vignette.png").convert_alpha()
        self.pl_vignette = pygame.image.load("graphics/player_vignette.png").convert_alpha()
        self.bullet_sprite = BULLET_SPRITE["player_bullet"]

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
        # self.flashlight = True
        self.in_disgiuse = False
        self.dying = False
        self.in_control = True

        self.max_bullets = None
        self.bullets = None

        self.shoot_cooldown_timer = CustomTimer()
        self.dying_timer = CustomTimer()
        self.death_wait_timer = CustomTimer()
        self.SHOOT_COOLDOWN = 1000

    def update_image(self):

        # if self.moving: state = "swim"
        if self.is_dead: state = "dead"
        elif self.in_disgiuse: state = "cover_t_swim"
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
                if event.button == 3 and not self.shoot_cooldown_timer.running and self.in_control\
                    and self.bullets > 0:
                    self.spawn_bullet()
                    self.shoot_cooldown_timer.start(self.SHOOT_COOLDOWN)
                    
            if event.type == pygame.MOUSEBUTTONUP:
                pass
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE  and self.in_control:
                    self.master.game.pause_game()
                if event.key == pygame.K_v:
                    self.master.debug.vignette = not self.master.debug.vignette
                if event.key == pygame.K_SPACE and self.in_control:
                    self.check_level_finish()
                    self.check_on_disguise()
                # if event.key == pygame.K_x:
                #     self.flashlight = not self.flashlight
                if event.key == pygame.K_h:
                    self.get_hurt()

        self.shoot_cooldown_timer.check()
        if self.dying_timer.check():
            self.is_dead = True
            self.dying = False
            self.death_wait_timer.start(2_000)
        if self.death_wait_timer.check():
            self.master.app.death_screen()

    def get_hurt(self, _damage=1):

        if self.is_dead or self.dying: return
        # instant kill
        self.dying = True
        self.in_control = False
        self.moving = False
        self.dying_timer.start(3_000)

    def spawn_bullet(self):

        self.bullets -= 1
        direc = pygame.Vector2()
        direc.from_polar((1, -round(self.direction.angle_to((1, 0))/15)*15))
        Bullet(self.master, [self.master.level.player_bullets_grp],
                        self.hitbox.center, direc, (6, 6))
        
    def check_on_disguise(self):

        for enemy in self.master.level.enemy_grp.sprites():
            if not self.rect.colliderect(enemy.rect): continue
            if not enemy.dead: continue
            if enemy.get_picked_up():
                self.in_disgiuse = True
        # self.in_disgiuse = not self.in_disgiuse
                
    def check_level_finish(self):
        if self.in_disgiuse and self.rect.colliderect((self.master.level.start_pos[0]-32,
                                                       self.master.level.start_pos[1]-32, 64, 64)):
            self.master.game.next_level()
            return True
        
    def draw_ui(self):

        bullet_counter_surf = self.master.font_1.render(str(self.bullets), False, (255, 255, 255))
        text_surf_rect = bullet_counter_surf.get_rect(topright=(W-5, 5))
        self.screen.blit(bullet_counter_surf, text_surf_rect)
        self.screen.blit(self.bullet_sprite, (W-self.bullet_sprite.get_width()-bullet_counter_surf.get_width()-10, 5))

    def draw(self):

        self.screen.blit(self.image, self.rect.topleft + self.master.offset)

        if self.dying:
            vignette = self.master.level.vignette
            vignette.blit(self.pl_vignette, self.rect.center+self.master.offset-\
                        (self.pl_vignette.get_width()/2, self.pl_vignette.get_height()/2)+(W/2, H/2),
                        special_flags=pygame.BLEND_RGBA_MIN)
        # if self.master.debug.vignette:
        #     if self.flashlight:
        #         radius = self.tri_vignette.get_width()/2
        #         tri_vignette = pygame.transform.rotate(self.tri_vignette, (self.direction.angle_to((1, 0))))
        #         rect = tri_vignette.get_rect(center = self.rect.center+self.master.offset)
        #         vignette.blit(tri_vignette, rect.topleft + self.direction*radius + (W/2, H/2),
        #                       special_flags=pygame.BLEND_RGBA_MIN)


        # if self.master.debug.on:
        #     pygame.draw.rect(self.screen, "blue", (self.hitbox.x+self.master.offset.x, self.hitbox.y+self.master.offset.y, self.hitbox.width, self.hitbox.height), 1)

    def update(self):

        self.process_events()
        if self.in_control:
            self.get_input()
        self.apply_force()
        self.move()
        self.update_image()

        self.master.debug("pos: ", (round(self.hitbox.centerx, 2), round(self.hitbox.bottom, 2)))
        self.master.debug("angle: ", round(self.direction.angle_to((0, -1))))
        self.master.debug("control: ", self.in_control)

