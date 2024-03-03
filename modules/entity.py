import pygame
from .config import *
from .engine import *

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
