import pygame
from .engine import *
from .config import *
from math import sin, pi
from random import randint, choice, random


class Level:

    def __init__(self, master, player):

        self.master = master
        master.level = self
        self.screen = pygame.display.get_surface()

        # self.collision = collision
        self.collision, pos = generate_map()
        self.size = len(self.collision[0]), len(self.collision)
        player.hitbox.center = pos
        player.rect.center = pos
        self.master.camera.snap_offset()

        self.player = player
        self.vignette = pygame.image.load("graphics/vignette.png").convert_alpha()
        self.tri_vignette = pygame.image.load("graphics/tri_vignette.png").convert_alpha()

    def draw_bg(self):

        self.screen.fill(0x909090)

        for y, row in enumerate(self.collision):
            for x, cell in enumerate(row):
                if cell == 1:
                    color = "green"
                    if x == 0 or y == 0 or x == len(row)-1 or y == len(self.collision)-1: color = "blue"
                    pygame.draw.rect(self.screen, color, (x*TILESIZE+self.master.offset.x, y*TILESIZE+self.master.offset.y, TILESIZE, TILESIZE), 1)
                    pygame.draw.line(self.screen, color, (x*TILESIZE+self.master.offset.x, y*TILESIZE+self.master.offset.y), (x*TILESIZE+self.master.offset.x+TILESIZE-1, y*TILESIZE+self.master.offset.y+TILESIZE-1), 1)


    def draw_fg(self):

        direc:pygame.Vector2 = self.player.direction
        vignette = self.vignette.copy()
        # pygame.draw.polygon(vignette, 0x00000000, (
        #     (vignette.get_width()/2, vignette.get_height()/2),
        #     direc.rotate(-30)*(W+H)/3 + (vignette.get_width()/2, vignette.get_height()/2),
        #     direc.rotate(30)*(W+H)/3 + (vignette.get_width()/2, vignette.get_height()/2),
        # ))
        # pygame.draw.aalines(vignette, 0x00000000, True, (
        #     (vignette.get_width()/2, vignette.get_height()/2),
        #     direc.rotate(-30)*(W+H)/3 + (vignette.get_width()/2, vignette.get_height()/2),
        #     direc.rotate(30)*(W+H)/3 + (vignette.get_width()/2, vignette.get_height()/2),
        # ))
        if self.master.debug.pl_vignette:
            if self.player.flashlight:
                vignette.blit(self.tri_vignette, (vignette.get_width()//2, vignette.get_height()//2-self.tri_vignette.get_height()//2), special_flags=pygame.BLEND_RGBA_MIN)
            vignette = pygame.transform.rotate(vignette, (direc.angle_to((1, 0))))            
            self.screen.blit(vignette, (self.player.hitbox.center + self.master.offset - (vignette.get_width()/2, vignette.get_height()/2)))


    def update(self):

        pass


class Node:

    def __init__(self, pos, direc):

        self.pos = pos
        self.direc = direc


def generate_map(corridor_len=120, rooms=5, turn_rate=0.30, branch_rate=0.75, chunk=CHUNK):

    """
    chunk        : the size of each tile
    rooms        : the approx number of rooms
    turn_rate    : the how lickly a path will turn
    turn_rate    : the how lickly a turn will become a branch
    corridor_len : the total lenth of the main corridor
    """

    dirs = ( (0, 1), (0, -1), (1, 0), (-1, 0) )
    nodes:list[Node] = [ Node((10, 10), choice(dirs)) ]
    curr_node = nodes[0]
    corridor_len -= 1
    active_nodes:list[Node] = [curr_node]

    min_pos = [10, 10]
    max_pos = [10, 10]

    while corridor_len > 0:

        new_nodes:list[Node] = []
        for curr_node in active_nodes:

            new_direc = curr_node.direc
            if turn_rate >= random():
                new_direc = choice(dirs)
                while (new_direc == curr_node.direc or (new_direc[0]*-1, new_direc[1]*-1) == curr_node.direc):
                    new_direc = choice(dirs)
                if branch_rate >= random():
                    new_nodes.append(curr_node)
                    pass

            new_node = Node(
                (curr_node.pos[0]+new_direc[0], curr_node.pos[1]+new_direc[1]),
                new_direc
            )
            nodes.append(new_node)
            corridor_len -= 1
            new_nodes.append(new_node)
            curr_node = new_node

            if new_node.pos[0] < min_pos[0]:
                min_pos[0] = new_node.pos[0]
            if new_node.pos[1] < min_pos[1]:
                min_pos[1] = new_node.pos[1]

            if new_node.pos[0] > max_pos[0]:
                max_pos[0] = new_node.pos[0]
            if new_node.pos[1] > max_pos[1]:
                max_pos[1] = new_node.pos[1]

        active_nodes = new_nodes

    # print(F"MIN:{min_pos}, MAX:{max_pos}")

    size_diff = tuple(min_pos)
    max_pos = max_pos[0] - size_diff[0], max_pos[1] - size_diff[1]
    min_pos = 0, 0

    collision = [((max_pos[0]+1)*chunk+2)*[1] for _ in range((max_pos[1]+1)*chunk+2)]
    # print("size:", max_pos)

    for node in nodes:

        node.pos = node.pos[0] - size_diff[0], node.pos[1] - size_diff[1]
        for y in range(node.pos[1]*chunk, node.pos[1]*chunk+chunk):
            for x in range(node.pos[0]*chunk, node.pos[0]*chunk+chunk):
                collision[y+1][x+1] = 0

    pos = choice(nodes).pos
    player_pos = pos[0]*chunk*TILESIZE+(2*TILESIZE), pos[1]*chunk*TILESIZE+(2*TILESIZE)


    return collision, player_pos


collision = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]
