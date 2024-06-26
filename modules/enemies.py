import pygame
from .config import *
from .engine import *
from .entity import *
from .projectiles import Bullet
from random import randint, choice
from math import sin, sqrt, radians
import json
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

ENEMY_SPRITES = {}

def load_enemy_sprites():

    global ENEMY_SPRITES, WARNING_SYMBOL, ALERT_SYMBOL

    for folder in ("guard", "target_fish", "fish1", "fish2", "fish3"):
        ENEMY_SPRITES[folder] = import_sprite_sheets(F"graphics/enemies/{folder}")
    
    ALERT_SYMBOL = pygame.image.load("graphics/UI/alert_symbol.png").convert_alpha()
    WARNING_SYMBOL = pygame.image.load("graphics/UI/warning_symbol.png").convert_alpha()

FISH_DIALOGUES:dict[str, list[str]] = json.load(open("data/dialogues.json"))

IDLE = 0
PATH = 1
FOLLOW = 2
AGRO = 2
ATTACK = 3
ANGRY = 4
DEAD = 5
SUMMONED = 6

class Enemy(pygame.sprite.Sprite):

    def __init__(self, master, grps, level, sprite_type, pos, hitbox, max_health, max_speed, acc, dcc):

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
        self.is_guard = False
        self.suspicion_meter = 0

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
                self.state = AGRO
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
                if enemy is self: continue
                if self.rect.colliderect(enemy.rect):
                    try:
                        space_vec = pygame.Vector2(self.rect.centerx-enemy.rect.centerx, self.rect.centery-enemy.rect.centery)
                        self.velocity += space_vec.normalize() * 0.008
                    except ValueError: pass

    def control(self):

        self.moving = bool(self.target_direc) and not self.hurting
        if self.moving:
            # self.direction.update(self.target_direc)
            self.direction.move_towards_ip(self.target_direc, self.acceleration*self.master.dt)

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
        # do_collision(self, 2, self.master)

    def follow_path(self, generate_new_on_end=True):

        if self.state not in (PATH, AGRO): return
        try:
            t_cell_x, t_cell_y = self.path_cells[self.path_cell_index]
        except IndexError:
            self.path_cell_index = 0
            
            # generate_new_path
            if generate_new_on_end:
                self.generate_new_path()
                t_cell_x, t_cell_y = self.path_cells[self.path_cell_index]
            else: return True

        # t_pos_x, t_pos_y = t_cell_x*TILESIZE+TILESIZE//2 , t_cell_y*TILESIZE+TILESIZE//2
        t_pos_x, t_pos_y = t_cell_x*TILESIZE*2+TILESIZE , t_cell_y*TILESIZE*2+TILESIZE
        self.target_direc.update(t_pos_x - self.rect.centerx,
                t_pos_y - self.rect.centery)
        try:
            self.target_direc.normalize_ip()
        except ValueError: pass
        if pygame.Rect(t_pos_x-1, t_pos_y-1, 2, 2).collidepoint(self.rect.center):
            self.path_cell_index += 1

    def generate_new_path(self, to_pos=None):
        
        orig_x, orig_y = self.rect.centerx//(TILESIZE*2), self.rect.centery//(TILESIZE*2)
        to_x, to_y = orig_x, orig_y
        if to_pos is None:
            points_list = self.level.guard_walk_positions if self.sprite_type == "guard" else self.level.walk_positions
            while (to_x, to_y) == (orig_x, orig_y):
                point = choice(points_list)
                to_x, to_y = point.x//(TILESIZE*2), point.y//(TILESIZE*2)
        else:
            to_x, to_y = to_pos[0]//(TILESIZE*2), to_pos[1]//(TILESIZE*2)
            if (to_x, to_y) == (orig_x, orig_y):
                raise ValueError(F"Object already at cell {to_x, to_y}, pathfinding is not necessary")

        start = self.level.pathfinding_grid.node(orig_x, orig_y)
        end = self.level.pathfinding_grid.node(int(to_x), int(to_y))
        finder = AStarFinder(diagonal_movement=DiagonalMovement.only_when_no_obstacle)
        self.path_cells, _runs = finder.find_path(start, end, self.level.pathfinding_grid)
        self.level.pathfinding_grid.cleanup()

    def process_events(self):

        pass

    def check_player_collision(self):

        pass
        # if self.hitbox.colliderect(self.master.player.hitbox):
        #     self.master.player.get_hurt(1)
    
    def can_get_picked_up(self, get_picked=True):

        if self.state != DEAD or self.sprite_type != "target_fish": return False
        if get_picked:
            self.kill()
        return True

    def get_hurt(self, damage):

        if self.invinsible or self.state == DEAD: return False
        if self.state in (IDLE, PATH):
            self.state = AGRO
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

    def in_line_of_sight(self, target_dist, direc=None) -> bool:

        ray_pos_x = self.hitbox.centerx / TILESIZE
        ray_pos_y = self.hitbox.centery / TILESIZE
        if direc is None:
            direc = pygame.Vector2(self.master.player.hitbox.centerx - self.hitbox.centerx,
                self.master.player.hitbox.centery - self.hitbox.centery)
            try:
                direc.normalize_ip()
            except ValueError: pass
        direc.x += .000000000000001
        direc.y += .000000000000001

        map_x = int(ray_pos_x)
        map_y = int(ray_pos_y)
        delta_dist_x = abs(1 / direc.x)
        delta_dist_y = abs(1 / direc.y)
        # delta_dist_x = sqrt(1 + (direc.y / direc.x) ** 2)
        # delta_dist_y = sqrt(1 + (direc.x / direc.y) ** 2)
        ray_len_x = 0
        ray_len_y = 0
        step_x = 0
        step_y = 0

        if direc.x < 0:
            step_x = -1
            ray_len_x = (ray_pos_x - map_x) * delta_dist_x
        else:
            step_x = 1
            ray_len_x = (map_x+1 - ray_pos_x) * delta_dist_x

        if direc.y < 0:
            step_y = -1
            ray_len_y = (ray_pos_y - map_y) * delta_dist_y
        else:
            step_y = 1
            ray_len_y = (map_y+1 - ray_pos_y) * delta_dist_y

        tile_found = False
        max_dist = W+H
        dist = 0.0
        while (not tile_found and dist < max_dist):
            if ray_len_x < ray_len_y:
                map_x += step_x
                dist = ray_len_x
                ray_len_x += delta_dist_x
            else:
                map_y += step_y
                dist = ray_len_y
                ray_len_y += delta_dist_y

            # if self.level.size[0] > map_check.x >= 0 and self.level.size[1] > map_check.y >= 0:
            if self.level.collision[map_y][map_x]:
                tile_found = True

        if tile_found:
            intersection = (ray_pos_x, ray_pos_y) + direc * dist
            pygame.draw.line(self.master.debug.surface, (255, 215, 0), self.hitbox.center+self.master.offset,
                             intersection*TILESIZE+self.master.offset)

        return not tile_found or (dist*TILESIZE)**2 > target_dist

    def draw(self):

        self.screen.blit(self.image, self.rect.topleft + self.master.offset)

        if not self.dead:
            if self.state == AGRO or 99 > self.suspicion_meter >= 68:
                self.screen.blit(ALERT_SYMBOL, self.hitbox.midtop+self.master.offset+[-ALERT_SYMBOL.get_width()/2, 6*sin(pygame.time.get_ticks()/300)-self.hitbox.h])
            elif self.state == ATTACK or self.suspicion_meter >= 99:
                self.screen.blit(WARNING_SYMBOL, self.hitbox.midtop+self.master.offset+[-WARNING_SYMBOL.get_width()/2, 6*sin(pygame.time.get_ticks()/300)-self.hitbox.h])

        if self.master.debug.on:
            pygame.draw.rect(self.master.debug.surface, (24, 116, 205, 100), (self.hitbox.x+self.master.offset.x, self.hitbox.y+self.master.offset.y, self.hitbox.width, self.hitbox.height), 1)

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
                         (0, 0, 16, 16), 2, 0.8, 0.1, 0.1)
        
        self.ambience_dist = 12*TILESIZE # makes creature noises within this distance
        self.calm_dist = 10*TILESIZE # clams the creature after this distance
        self.agro_dist = 6*TILESIZE # follows within this distance
        self.attack_dist = 5*TILESIZE # initiates an attack in this distance

        self.fov = 0.7
        self.chasing = False
        self.is_guard = True

        self.attack_cooldown_timer = CustomTimer()
        self.chase_path_timer = CustomTimer(auto_clear=True)
        self.summoned_timer = CustomTimer()
        self.chase_path_timer.start(1_000, 0)

    def check_timers(self):

        super().check_timers()
        self.attack_cooldown_timer.check()
        self.summoned_timer.check()
        if self.chase_path_timer.check() and self.state in (AGRO, ATTACK, SUMMONED):
            try:
                self.generate_new_path(self.master.player.hitbox.center)
                self.chasing = True
            except ValueError:
                self.chasing = False

    def follow_path(self):

        if self.state in (AGRO, ATTACK):
            generate_new_on_end = False
        else: generate_new_on_end = True
        return super().follow_path(generate_new_on_end)
        
    def process_events(self):

        if self.state == DEAD: return

        self.master.debug("State:",["IDLE", "PATH", "AGRO", "ATTACK", "ANGRY"][self.state])
        angle = self.direction.angle_to([1, 0])
        pygame.draw.arc(self.master.debug.surface, (108, 10, 50, 50),
            [self.master.offset.x-self.agro_dist+self.rect.centerx, self.master.offset.y-self.agro_dist+self.rect.centery, self.agro_dist*2, self.agro_dist*2],
            radians(angle-(1-self.fov)*90), radians(angle+(1-self.fov)*90),  self.agro_dist)

        dist = dist_sq(self.master.player.rect.center, self.rect.center)
        to_player = pygame.Vector2(self.master.player.hitbox.centerx - self.hitbox.centerx,
            self.master.player.hitbox.centery - self.hitbox.centery)
        try:
            to_player.normalize_ip()
        except ValueError: pass
        # in_los = self.in_line_of_sight(dist, to_player)
        # in_fov = self.direction.dot(to_player) <= self.fov

        if self.state == ATTACK and dist > self.attack_dist**2:
            self.state = AGRO
        elif (self.state == AGRO and dist <= self.attack_dist**2 and not self.attack_cooldown_timer.running
          and self.direction.dot(to_player) > 0.9 # in fov
          and self.in_line_of_sight(dist, self.direction)): # in line of sight
            self.shoot_bullet()
            self.state = ATTACK
            self.attack_cooldown_timer.start(2_000)
            self.anim_index = 0
        elif ( self.state != AGRO and self.state != ATTACK and (not self.master.player.in_disguise or self.master.player.attacking) and
                self.rect.colliderect([-self.master.offset.x, -self.master.offset.y, W, H]) and # on screen
                self.direction.dot(to_player) >= self.fov and # in field of view
                dist <= self.agro_dist**2 and # in range
                self.in_line_of_sight(dist, to_player)): # in line of sight
            if self.state == PATH:
                self.state = AGRO
                self.chase_path_timer.start_time = pygame.time.get_ticks() - self.chase_path_timer.duration-10

        if dist > self.calm_dist**2 and self.state != PATH and not self.summoned_timer.running:
            self.chasing = False
            self.state = PATH
            self.generate_new_path()

        if self.state in (AGRO, ATTACK) and not self.chasing:
            self.target_direc.update(self.master.player.rect.centerx - self.rect.centerx,
                self.master.player.rect.centery - self.rect.centery)
            try:
                self.target_direc.normalize_ip()
            except ValueError: pass

    def shoot_bullet(self):

        direc = pygame.Vector2()
        direc.from_polar((1, -round(self.direction.angle_to((1, 0))/15)*15))
        Bullet(self.master, [self.master.level.player_bullets_grp], 
               self.hitbox.center, direc, (7, 7), False, 2)
        
        

class Fish(Enemy):

    def __init__(self, master, grps, level, sprite_type, pos):

        super().__init__(master, grps, level, sprite_type, pos,
                         (0, 0, 16, 16), 1, 0.5, 0.1, 0.1)
        
        self.player_detection_dist = round(3*TILESIZE)
        self.player_too_close_dist = 1*TILESIZE
        self.call_guard_dist = 14*TILESIZE
        self.fov = 0.6
        self.react_to_player_timer = CustomTimer()

    def check_timers(self):

        super().check_timers()
        self.react_to_player_timer.check()
        
    def process_events(self):

        if self.state == DEAD: return
        
        angle = self.direction.angle_to([1, 0])
        pygame.draw.arc(self.master.debug.surface, (198, 85, 50, 85),
            [self.master.offset.x-self.player_detection_dist+self.rect.centerx, self.master.offset.y-self.player_detection_dist+self.rect.centery, self.player_detection_dist*2, self.player_detection_dist*2],
            radians(angle-(1-self.fov)*90), radians(angle+(1-self.fov)*90),  self.player_detection_dist)
        pygame.draw.circle(self.master.debug.surface, (108, 10, 50, 50),
                           (self.master.offset.x+self.rect.centerx, self.master.offset.y+self.rect.centery),
                           self.player_too_close_dist)

        dist = dist_sq(self.master.player.rect.center, self.rect.center)
        to_player = pygame.Vector2(self.master.player.hitbox.centerx - self.hitbox.centerx,
            self.master.player.hitbox.centery - self.hitbox.centery)
        try:
            to_player.normalize_ip()
        except ValueError: pass
        
        if (dist <= self.player_too_close_dist**2 or
                (dist <= self.player_detection_dist**2 and self.direction.dot(to_player) >= self.fov # in fov
                 and self.in_line_of_sight(dist, to_player))): # in los
            diag = None
            # TODO add random dialogues
            if not self.react_to_player_timer.running:
                if self.master.player.in_disguise or self.suspicion_meter > 68:
                    # Bad react
                    self.react_to_player_timer.start(3_000)
                    self.suspicion_meter += 34
                    diag = self.master.dialogue_manager.create_dialogue(self, 1_800, choice(FISH_DIALOGUES["sus_react"]))
                else:
                    # cool react
                    self.react_to_player_timer.start(4_000)
                    self.master.dialogue_manager.create_dialogue(self, 1_800, choice(FISH_DIALOGUES["cool_react"]))
            elif self.master.player.attacking:
                pass # TODO rect crazy
                self.suspicion_meter = 100
                diag = self.master.dialogue_manager.create_dialogue(self, 1_000, "")

            if self.suspicion_meter >= 100:
                if diag is not None:
                    diag.text = choice(FISH_DIALOGUES["danger_react"])
                for enemy in self.level.enemy_grp.sprites():
                    if enemy is self or enemy.dead or not enemy.is_guard: continue
                    if dist_sq(self.hitbox.center, enemy.hitbox.center) < self.call_guard_dist**2:
                        enemy.state = AGRO
                        enemy.summoned_timer.start(2_000)
                self.suspicion_meter = 99
