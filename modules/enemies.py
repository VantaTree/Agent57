import pygame
from .config import *
from .engine import *
from .entity import *
from random import randint, choice
from math import sin
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

ENEMY_SPRITES = {}

def load_enemy_sprites():

    global ENEMY_SPRITES

    for folder in ("guard", "fish1", "target_fish"):
        ENEMY_SPRITES[folder] = import_sprite_sheets(F"graphics/enemies/{folder}")


IDLE = 0
PATH = 1
FOLLOW = 2
ATTACK = 3
ANGRY = 4
DEAD = 5

class Enemy(pygame.sprite.Sprite):

    def __init__(self, master, grps, level, sprite_type, pos, hitbox, attack_rect, max_health, max_speed, acc, dcc):

        super().__init__(grps)
        self.master = master
        self.screen = pygame.display.get_surface()
        self.level = level

        self.sprite_type = sprite_type
        self.animations = ENEMY_SPRITES[sprite_type]
        self.image = self.animations["swim"][0]
        self.rect = self.image.get_rect(center=pos)

        self.anim_index = 0
        self.anim_speed = 0.15

        self.attack_rect_dimen = attack_rect
        self.attack_rect = pygame.FRect(*attack_rect)

        self.pos = pos
        self.hitbox = pygame.FRect(*hitbox)
        self.hitbox.center = self.rect.center
        self.velocity = pygame.Vector2()
        self.target_direc = pygame.Vector2()
        self.max_speed = max_speed
        self.acceleration = acc
        self.deceleration = dcc
        self.direction = pygame.Vector2(choice((1, -1)), 0)


        self.state = PATH
        self.moving = False
        self.max_health = max_health
        self.health = self.max_health
        self.invinsible = False
        self.hurting = False
        self.dead = False

        self.path_cells = []
        self.path_cell_index = 0

        self.invinsibility_timer = CustomTimer()
        self.hurt_for = CustomTimer()

    def update_image(self):

        if self.state == DEAD: state = "dead"
        else: state = "swim"
        # elif self.state == ATTACK: state = "attack"

        try:
            image = self.animations[state][int(self.anim_index)]
        except IndexError:
            image = self.animations[state][0]
            self.anim_index = 0
            if self.state == ATTACK:
                self.state = FOLLOW
            # elif self.state == DEAD:
            #     self.die()
            #     return

        if self.moving: self.anim_speed = 0.15
        elif self.state == DEAD: self.anim_speed = 0.01
        # else: self.anim_speed = 0.08
        else: self.anim_speed = 0

        self.anim_index += self.anim_speed *self.master.dt

        mirror = self.direction.dot((-1, 0)) > 0
        image = pygame.transform.flip(image, False, mirror)
        self.image = pygame.transform.rotate(image, round(self.direction.angle_to((1, 0))/15)*15)
        self.rect = self.image.get_rect(center = self.hitbox.center)

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
                if enemy is self or enemy.dead: continue
                if self.rect.colliderect(enemy.rect):
                    try:
                        space_vec = pygame.Vector2(self.rect.centerx-enemy.rect.centerx, self.rect.centery-enemy.rect.centery)
                        self.velocity += space_vec.normalize() * 0.008
                    except ValueError: pass

    def control(self):

        self.moving = bool(self.target_direc) and not self.hurting
        if self.moving:
            self.direction.update(self.target_direc)

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

    def follow_path(self):

        if self.state != PATH: return
        try:
            t_cell_x, t_cell_y = self.path_cells[self.path_cell_index]
        except IndexError:
            self.path_cell_index = 0
            
            # generate_new_path
            points_list = self.level.guard_walk_positions if self.sprite_type == "guard" else self.level.walk_positions
            point = choice(points_list)
            start = self.level.pathfinding_grid.node(self.rect.x//(TILESIZE*2), self.rect.y//(TILESIZE*2))
            end = self.level.pathfinding_grid.node(int(point.x//(TILESIZE*2)), int(point.y//(TILESIZE*2)))
            finder = AStarFinder(diagonal_movement=DiagonalMovement.only_when_no_obstacle)
            self.path_cells, _runs = finder.find_path(start, end, self.level.pathfinding_grid)
            self.level.pathfinding_grid.cleanup()

            t_cell_x, t_cell_y = self.path_cells[self.path_cell_index]

        # t_pos_x, t_pos_y = t_cell_x*TILESIZE+TILESIZE//2 , t_cell_y*TILESIZE+TILESIZE//2
        t_pos_x, t_pos_y = t_cell_x*TILESIZE*2+TILESIZE , t_cell_y*TILESIZE*2+TILESIZE
        self.target_direc.update(t_pos_x - self.rect.centerx,
                t_pos_y - self.rect.centery)
        try:
            self.target_direc.normalize_ip()
        except ValueError: pass
        if pygame.Rect(t_pos_x-1, t_pos_y-1, 2, 2).collidepoint(self.rect.center):
            self.path_cell_index += 1

    def process_events(self):

        pass

    def check_player_collision(self):

        pass
        # if self.hitbox.colliderect(self.master.player.hitbox):
        #     self.master.player.get_hurt(1)
    
    def get_picked_up(self):

        if self.state != DEAD or self.sprite_type != "target_fish": return False
        self.kill()
        return True

    def get_hurt(self, damage):

        if self.invinsible or self.state == DEAD: return False
        if self.state in (IDLE, PATH):
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
            self.state = DEAD
            self.dead = True
            self.anim_index = 0
        return True
    
    def die(self):

        pass

    def draw(self):

        self.screen.blit(self.image, self.rect.topleft + self.master.offset)
        # pygame.draw.rect(self.screen, "blue", (self.hitbox.x+self.master.offset.x, self.hitbox.y+self.master.offset.y, self.hitbox.width, self.hitbox.height), 1)
        # pygame.draw.rect(self.screen, "red", (self.attack_rect.x+self.master.offset.x, self.attack_rect.y+self.master.offset.y, self.attack_rect.width, self.attack_rect.height), 1)

    def update(self):

        if self.state != DEAD:
            self.process_events()
            self.follow_path()
        self.check_timers()
        if self.state != DEAD:
            self.control()
            self.apply_force()
            self.move()
            self.check_player_collision()
        self.update_image()


class Guard(Enemy):

    def __init__(self, master, grps, level, sprite_type, pos):

        super().__init__(master, grps, level, sprite_type, pos,
                         (0, 0, 14, 14), (0, 0, 32, 32), 2, 0.8, 0.1, 0.1)
        
        self.ambience_dist = 16*TILESIZE # makes creature noises within this distance
        self.calm_dist = 28*TILESIZE # clams the creature after this distance
        self.follow_dist = 6*TILESIZE # follows within this distance
        self.attack_dist = 1.5*TILESIZE # initiates an attack in this distance
        
    def process_events(self):

        if self.state == DEAD: return
        dist = dist_sq(self.master.player.rect.center, self.rect.center)
        if dist < self.attack_dist**2 and self.state == ANGRY:
            self.state = FOLLOW
        elif dist < self.follow_dist**2:
            if self.state == PATH:
                self.state = FOLLOW
        elif self.state != ANGRY:
            self.state = PATH
            self.target_direc.update()

        if dist > self.calm_dist**2 and self.state == ANGRY:
            self.state = PATH

        if self.state in (FOLLOW, ANGRY):
            self.target_direc.update(self.master.player.rect.centerx - self.rect.centerx,
                self.master.player.rect.centery - self.rect.centery)
            try:
                self.target_direc.normalize_ip()
            except ValueError: pass

            self.direction.update(self.master.player.rect.centerx - self.rect.centerx,
                self.master.player.rect.centery - self.rect.centery)
            try:
                self.direction.normalize_ip()
            except ValueError: pass
        

class Fish(Enemy):

    def __init__(self, master, grps, level, sprite_type, pos):

        super().__init__(master, grps, level, sprite_type, pos,
                         (0, 0, 14, 14), (0, 0, 16, 16), 1, 0.5, 0.1, 0.1)