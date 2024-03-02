import pygame
from .engine import *
from .config import *
from .enemies import Enemy
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

        self.player_bullets_grp = CustomGroup()
        self.enemy_grp = CustomGroup()

        self.player = player
        self.orig_vignette = pygame.Surface((W*2, H*2), pygame.SRCALPHA)
        # self.orig_vignette = pygame.Surface((W, H), pygame.SRCALPHA)
        self.orig_vignette.fill((0, 0, 0))
        self.vignette = self.orig_vignette.copy()

        Enemy(master, [self.enemy_grp], self, None, self.player.rect.center,
              self.player.hitbox.copy(), self.player.hitbox.copy(), 5, 0.9, 0.1, 0.1,
              ambience_dist=(16*16), calm_dist=(28*16), follow_dist=(4*16), attack_dist=(1.5*16))


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

        # vignette = self.vignette
        # direc = self.master.player.direction
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
        self.enemy_grp.draw()
        self.player_bullets_grp.draw()
        if self.master.debug.vignette:
            self.screen.blit(self.vignette, (-W/2, -H/2))
            # self.screen.blit(self.vignette, (0, 0))


    def update(self):

        self.player_bullets_grp.update()
        self.enemy_grp.update()


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

    # with open("data/test.csv", "w") as f:
    #     for row in collision:
    #         f.write(",".join(map(str, row)))
    #         f.write(",\n")
    return collision, player_pos

