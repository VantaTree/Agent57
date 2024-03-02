import pygame
from .config import *
from .engine import *


class Bullet(pygame.sprite.Sprite):

    def __init__(self, master, grps, pos, direction, speed = 3):

        super().__init__(grps)
        self.master = master
        self.screen = pygame.display.get_surface()

        self.orig_image = pygame.image.load("graphics/test_bullet.png").convert_alpha()
        self.image = self.orig_image
        # self.bullet_vignette = pygame.image.load("graphics/bullet_vignette.png").convert_alpha()
        self.bullet_vignette = pygame.image.load("graphics/vignette_bullet.png").convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.FRect(0, 0, 6, 6)
        self.hitbox.center = pos

        self.direction = pygame.Vector2(direction)
        self.speed = speed
        self.angle = self.direction.angle_to([1, 0])

    def update_image(self):

        self.image = pygame.transform.rotate(self.orig_image, self.angle)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def move(self):

        self.hitbox.x += self.direction.x * self.speed * self.master.dt
        self.hitbox.y += self.direction.y * self.speed * self.master.dt

        if is_colliding(self, self.master):
            self.kill()

    def update(self):

        self.move()
        self.update_image()

    def draw(self):
        
        self.screen.blit(self.image, self.rect.topleft+self.master.offset)

        if self.master.debug.vignette:
            vignette = self.master.level.vignette
            pos = self.rect.center+self.master.offset-(self.bullet_vignette.get_width()/2, self.bullet_vignette.get_height()/2) + (W/2, H/2)
            vignette.blit(self.bullet_vignette, pos, special_flags=pygame.BLEND_RGBA_MIN)


def is_colliding(entity, master, obj_rects=None):

    px = int(entity.hitbox.centerx / TILESIZE)
    py = int(entity.hitbox.centery / TILESIZE)

    collided = False

    for y in range(py-1, py+2):
        for x in range(px-1, px+2):

            if x < 0 or y < 0: continue

            cell = get_xy(master.level.collision, x, y)
            if cell is None or cell <= 0: continue

            rect = pygame.Rect(x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE)
            if not entity.hitbox.colliderect(rect): continue
            collided = True
            break
        if collided: break

    if collided:
        return collided

    if obj_rects is not None:
        for rect in obj_rects:
            if not entity.hitbox.colliderect(rect): continue
            return True

    return False


def do_collision(entity, axis, master, obj_rects=None):

    px = int(entity.hitbox.centerx / TILESIZE)
    py = int(entity.hitbox.centery / TILESIZE)

    for y in range(py-1, py+2):
        for x in range(px-1, px+2):

            if x < 0 or y < 0: continue

            cell = get_xy(master.level.collision, x, y)
            if cell is None or cell <= 0: continue

            rect = pygame.Rect(x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE)
            if not entity.hitbox.colliderect(rect): continue

            apply_collision(master, entity, axis, rect, cell)

def apply_collision(master, entity, axis, rect, cell=1):

    if axis == 0: # x-axis

                if cell in (1, 2):

                    if entity.velocity.x > 0:
                        entity.hitbox.right = rect.left
                    if entity.velocity.x < 0:
                        entity.hitbox.left = rect.right

    elif axis == 1: # y-axis

        if cell in (1, 2):
            if entity.velocity.y < 0:
                entity.hitbox.top = rect.bottom
            if entity.velocity.y > 0:
                entity.hitbox.bottom = rect.top

    elif axis == 2: # slants
            
        if   cell == 4: # ◢
            gapy = rect.bottom - entity.hitbox.bottom
            gapx = entity.hitbox.right - rect.left
            if gapx < gapy: return
            prev_pos = entity.hitbox.right - entity.velocity.x, entity.hitbox.bottom - entity.velocity.y
            entity.hitbox.bottomright = prev_pos
            if entity.velocity.x > 0 and entity.velocity.y > 0:
            # if entity.velocity.x and entity.velocity.y:
                entity.velocity.update()
            elif entity.velocity.x > 0:
                entity.velocity.y = 0
                new_vel = entity.velocity.rotate(-45)
                entity.hitbox.move_ip(new_vel)
            elif entity.velocity.y > 0:
                entity.velocity.x = 0
                new_vel = entity.velocity.rotate(45)
                entity.hitbox.move_ip(new_vel)
        elif cell == 5: # ◣
            gapy = rect.bottom - entity.hitbox.bottom
            gapx = rect.right - entity.hitbox.left
            if gapx < gapy: return
            prev_pos = entity.hitbox.right - entity.velocity.x, entity.hitbox.bottom - entity.velocity.y
            entity.hitbox.bottomright = prev_pos
            if entity.velocity.x < 0 and entity.velocity.y > 0:
            # if entity.velocity.x and entity.velocity.y:
                entity.velocity.update()
            elif entity.velocity.x < 0:
                entity.velocity.y = 0
                new_vel = entity.velocity.rotate(45)
                entity.hitbox.move_ip(new_vel)
            elif entity.velocity.y > 0:
                entity.velocity.x = 0
                new_vel = entity.velocity.rotate(-45)
                entity.hitbox.move_ip(new_vel)
        elif cell == 6: # ◤
            gapy = entity.hitbox.top - rect.top
            gapx = rect.right - entity.hitbox.left
            if gapx < gapy: return
            prev_pos = entity.hitbox.x - entity.velocity.x, entity.hitbox.y - entity.velocity.y
            entity.hitbox.topleft = prev_pos
            if entity.velocity.x < 0 and entity.velocity.y < 0:
            # if entity.velocity.x and entity.velocity.y:
                entity.velocity.update()
            elif entity.velocity.x < 0:
                entity.velocity.y = 0
                new_vel = entity.velocity.rotate(-45)
                entity.hitbox.move_ip(new_vel)
            elif entity.velocity.y < 0:
                entity.velocity.x = 0
                new_vel = entity.velocity.rotate(45)
                entity.hitbox.move_ip(new_vel)
        elif cell == 7: # ◥
            gapy = entity.hitbox.top - rect.top
            gapx = entity.hitbox.right - rect.left
            if gapx < gapy: return
            prev_pos = entity.hitbox.right - entity.velocity.x, entity.hitbox.y - entity.velocity.y
            entity.hitbox.topright = prev_pos
            if entity.velocity.x > 0 and entity.velocity.y < 0:
            # if entity.velocity.x and entity.velocity.y:
                entity.velocity.update()
            elif entity.velocity.x > 0:
                entity.velocity.y = 0
                new_vel = entity.velocity.rotate(45)
                entity.hitbox.move_ip(new_vel)
            elif entity.velocity.y < 0:
                entity.velocity.x = 0
                new_vel = entity.velocity.rotate(-45)
                entity.hitbox.move_ip(new_vel)

                        
def get_xy(grid, x, y):

    if x < 0 or y < 0: return
    try:
        return grid[y][x]
    except IndexError: return
