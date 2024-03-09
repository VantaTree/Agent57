import pygame
from .config import *
from .engine import *
from .entity import *
from .projectiles import Bullet
from random import randint, choice
from math import sin, sqrt, radians
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
AGRO = 2
ATTACK = 3
ANGRY = 4
DEAD = 5

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
                if enemy is self or enemy.dead: continue
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
        do_collision(self, 2, self.master)

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
    
    def get_picked_up(self):

        if self.state != DEAD or self.sprite_type != "target_fish": return False
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

    def draw(self):

        self.screen.blit(self.image, self.rect.topleft + self.master.offset)
        # pygame.draw.rect(self.screen, "blue", (self.hitbox.x+self.master.offset.x, self.hitbox.y+self.master.offset.y, self.hitbox.width, self.hitbox.height), 1)

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

        self.attack_cooldown_timer = CustomTimer()
        self.chase_path_timer = CustomTimer(auto_clear=True)
        self.chase_path_timer.start(1_000, 0)

    def check_timers(self):

        super().check_timers()
        self.attack_cooldown_timer.check()
        if self.chase_path_timer.check() and self.state in (AGRO, ATTACK):
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
        dist = dist_sq(self.master.player.rect.center, self.rect.center)
        to_player = pygame.Vector2(self.master.player.hitbox.centerx - self.hitbox.centerx,
            self.master.player.hitbox.centery - self.hitbox.centery)
        try:
            to_player.normalize_ip()
        except ValueError: pass
        # in_los = self.in_line_of_sight(dist, to_player)
        # in_fov = self.direction.dot(to_player) <= self.fov

        if dist > self.attack_dist**2 and self.state == ATTACK:
            self.state = AGRO
        elif dist <= self.attack_dist**2 and self.state == AGRO and not self.attack_cooldown_timer.running\
          and self.direction.dot(to_player) > 0.9 \
          and self.in_line_of_sight(dist, self.direction):    
            self.shoot_bullet()
            self.state = ATTACK
            self.attack_cooldown_timer.start(2_000)
            self.anim_index = 0
        elif ( self.state != AGRO and 
                self.rect.colliderect([-self.master.offset.x, -self.master.offset.y, W, H]) and # on screen
                self.direction.dot(to_player) >= self.fov and # in field of view
                dist <= self.agro_dist**2 and # in range
                self.in_line_of_sight(dist, to_player)): # in line of sight
            if self.state == PATH:
                self.state = AGRO
                self.chase_path_timer.start_time = pygame.time.get_ticks() - self.chase_path_timer.duration-10

        if dist > self.calm_dist**2 and self.state != PATH:
            self.chasing = False
            self.state = PATH
            self.generate_new_path()

        if self.state in (AGRO, ATTACK) and not self.chasing:
            self.target_direc.update(self.master.player.rect.centerx - self.rect.centerx,
                self.master.player.rect.centery - self.rect.centery)
            try:
                self.target_direc.normalize_ip()
            except ValueError: pass

        self.master.debug("State:",["IDLE", "PATH", "AGRO", "ATTACK", "ANGRY"][self.state])
        angle = self.direction.angle_to([1, 0])
        pygame.draw.arc(self.master.debug.surface, (108, 10, 50, 50),
            [self.master.offset.x-self.agro_dist+self.rect.centerx, self.master.offset.y-self.agro_dist+self.rect.centery, self.agro_dist*2, self.agro_dist*2],
            radians(angle-(1-self.fov)*90), radians(angle+(1-self.fov)*90),  self.agro_dist)

    def shoot_bullet(self):

        direc = pygame.Vector2()
        direc.from_polar((1, -round(self.direction.angle_to((1, 0))/15)*15))
        Bullet(self.master, [self.master.level.player_bullets_grp], 
               self.hitbox.center, direc, (7, 7), False, 2)
        
    def in_line_of_sight(self, player_dist, direc=None) -> bool:

        start_pos = pygame.Vector2(self.hitbox.center) / TILESIZE
        # end_pos = pygame.Vector2(self.master.player.hitbox.center) / TILESIZE
        if direc is None:
            direc = pygame.Vector2(self.master.player.hitbox.centerx - self.hitbox.centerx,
                self.master.player.hitbox.centery - self.hitbox.centery)
            try:
                direc.normalize_ip()
            except ValueError: pass

        try:
            dx = abs(1 / direc.x)
            # dx = sqrt(1 + (direc.y / direc.x) ** 2)
        except ZeroDivisionError:
            dx = float("inf")
        try:
            dy = abs(1 / direc.y)
            # dy = sqrt(1 + (direc.x / direc.y) ** 2)
        except ZeroDivisionError:
            dy = float("inf")
        step_size = pygame.Vector2( dx, dy )
        # step_size = pygame.Vector2( sqrt(1 + (direc.y / direc.x) ** 2), sqrt(1 + (direc.x / direc.y) ** 2) )
        map_check = pygame.Rect(*start_pos, 0, 0)
        ray_len = pygame.Vector2()
        step_dir = pygame.Rect(0, 0, 0, 0)

        if direc.x < 0:
            step_dir.x = -1
            # ray_len.x = (start_pos.x % 1) * step_size.x
            ray_len.x = (start_pos.x - map_check.x) * step_size.x
        else:
            step_dir.x = 1
            # ray_len.x = (1 - start_pos.x % 1) * step_size.x
            ray_len.x = (map_check.x+1 - start_pos.x) * step_size.x

        if direc.y < 0:
            step_dir.y = -1
            # ray_len.x = (start_pos.y % 1) * step_size.x
            ray_len.x = (start_pos.y - map_check.y) * step_size.x
        else:
            step_dir.y = 1
            # ray_len.x = (1 - start_pos.y % 1) * step_size.x
            ray_len.x = (map_check.y+1 - start_pos.y) * step_size.x

        tile_found = False
        max_dist = W+H
        dist = 0.0
        while (not tile_found and dist < max_dist):
            if ray_len.x < ray_len.y:
                map_check.x += step_dir.x
                dist = ray_len.x
                ray_len.x += step_size.x
            else:
                map_check.y += step_dir.y
                dist = ray_len.y
                ray_len.y += step_size.y

            # if self.level.size[0] > map_check.x >= 0 and self.level.size[1] > map_check.y >= 0:
            if self.level.collision[map_check.y][map_check.x]:
                tile_found = True

        if tile_found:
            intersection = start_pos + direc * dist
            pygame.draw.line(self.master.debug.surface, (255, 215, 0), self.hitbox.center+self.master.offset,
                             intersection*TILESIZE+self.master.offset)

        return not tile_found or (dist*TILESIZE)**2 > player_dist
        

class Fish(Enemy):

    def __init__(self, master, grps, level, sprite_type, pos):

        super().__init__(master, grps, level, sprite_type, pos,
                         (0, 0, 16, 16), 1, 0.5, 0.1, 0.1)
