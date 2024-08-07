import pygame
from .engine import *
from .config import *
from .enemies import Guard, Fish, load_enemy_sprites
from .dialogue import DialogueManager, load_dialogue_sprites
from pytmx.util_pygame import load_pygame
import json
from pathfinding.core.grid import Grid as PathGrid
from random import randint, choice, random

def load_resources():
    load_enemy_sprites()
    load_dialogue_sprites()

class Level:

    def __init__(self, master, player, map_type):

        self.master = master
        master.level = self
        self.player = player
        self.screen = pygame.display.get_surface()

        self.name = map_type
        self.data = load_pygame(F"data/{map_type}.tmx")
        self.size = self.data.width, self.data.height

        self.size = self.data.width, self.data.height
        self.get_collision_data()
        self.get_tile_layers()
        
        self.start_pos = json.loads(self.data.properties["player_start_pos"])
        self.start_pos = self.start_pos[0]*TILESIZE +TILESIZE//2, self.start_pos[1]*TILESIZE +TILESIZE//2
        player.hitbox.center = self.start_pos
        player.rect.center = self.start_pos
        self.master.camera.snap_offset()

        self.player_bullets_grp = CustomGroup()
        self.enemy_grp = CustomGroup()
        self.init_objects()

        self.dialogue_manager = DialogueManager(master)

        self.orig_vignette = pygame.Surface((W*2, H*2), pygame.SRCALPHA)
        # self.orig_vignette = pygame.Surface((W, H), pygame.SRCALPHA)
        self.orig_vignette.fill((0, 0, 0))
        self.vignette = self.orig_vignette.copy()

    def get_collision_data(self):
        
        for tileset in self.data.tilesets:
            if tileset.name == "collision":
                collision_firstgid = tileset.firstgid
            # if tileset.name == "objects":
            #     self.object_firstgid = tileset.firstgid

        self.collision = self.data.get_layer_by_name("collision").data
        self.pathfinding_grid = [[0]*(self.size[0]//2) for _ in range(self.size[1]//2)]
        
        for y, row in enumerate(self.collision):
            for x, gid in enumerate(row):

                cell = self.data.tiledgidmap[gid] - collision_firstgid
                self.collision[y][x] = cell
                self.pathfinding_grid[y//2][x//2] = 1 if cell == 0 else 0
        self.pathfinding_grid = PathGrid(matrix=self.pathfinding_grid)

    def get_tile_layers(self):

        self.tile_map_layers = [self.data.get_layer_by_name("main"), self.data.get_layer_by_name("over")]

    def init_objects(self):

        self.walk_positions = list(self.data.get_layer_by_name("walk_positions"))
        self.guard_walk_positions = list(self.data.get_layer_by_name("guard_walk_positions"))
        total_guards = self.data.properties["guard_fishes"]
        total_fishes = self.data.properties["normal_fishes"] # excluding target fish
        self.player.max_bullets = self.data.properties["bullets"]
        # self.player.max_bullets = int(total_fishes*0.85) + total_guards
        self.player.bullets = self.player.max_bullets
        for _ in range(total_guards):
            point = choice(self.guard_walk_positions)
            pos = point.x//TILESIZE *TILESIZE + TILESIZE//2, point.y//TILESIZE *TILESIZE + TILESIZE//2
            Guard(self.master, [self.enemy_grp], self, "guard", (pos))
        for _ in range(total_fishes):
            point = choice(self.walk_positions)
            pos = point.x//TILESIZE *TILESIZE + TILESIZE//2, point.y//TILESIZE *TILESIZE + TILESIZE//2
            Fish(self.master, [self.enemy_grp], self, F"fish{choice([1, 1, 2, 3])}", (pos))
        
        point = choice(self.walk_positions)
        pos = point.x//TILESIZE *TILESIZE + TILESIZE//2, point.y//TILESIZE *TILESIZE + TILESIZE//2
        Fish(self.master, [self.enemy_grp], self, "target_fish", (pos))

    def draw_bg(self):

        # self.screen.fill(0x909090)
        if self.data.background_color:
            self.screen.fill(self.data.background_color)
        else:
            self.screen.fill(0)

        px1 = int(self.master.offset.x*-1//TILESIZE)
        px2 = px1 + W//TILESIZE +1
        py1 = int(self.master.offset.y*-1//TILESIZE)
        py2 = py1 + H//TILESIZE +1

        if px2 >= self.size[0]: px2 = self.size[0]-1
        if py2 >= self.size[1]: py2 = self.size[1]-1
        if px2 < 0: px2 = 0
        if py2 < 0: py2 = 0

        for y in range(py1, py2+1):
            for x in range(px1, px2+1):

                for layer in self.tile_map_layers:

                    gid = layer.data[y][x]
                    image = self.data.get_tile_image_by_gid(gid)
                    if image is None: continue
                    self.screen.blit(image, (x*TILESIZE + self.master.offset.x, y*TILESIZE + self.master.offset.y - image.get_height() + TILESIZE))

                if self.master.debug.on and False: # disabled
                    cell = self.collision[y][x]
                    if cell == 1:
                        color = "green"
                        if x == 0 or y == 0 or x == self.size[0]-1 or y == self.size[1]-1: color = "blue"
                        pygame.draw.rect(self.screen, color, (x*TILESIZE+self.master.offset.x, y*TILESIZE+self.master.offset.y, TILESIZE, TILESIZE), 1)
                        pygame.draw.line(self.screen, color, (x*TILESIZE+self.master.offset.x, y*TILESIZE+self.master.offset.y), (x*TILESIZE+self.master.offset.x+TILESIZE-1, y*TILESIZE+self.master.offset.y+TILESIZE-1), 1)

    def draw(self):

        self.enemy_grp.draw()
        self.player_bullets_grp.draw()

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
        
        self.dialogue_manager.draw()
        self.player.draw_ui()
        if self.player.dying:
            self.screen.blit(self.vignette, (-W/2, -H/2))
        # if self.master.debug.vignette:
        #     self.screen.blit(self.vignette, (-W/2, -H/2))


    def update(self):

        self.player_bullets_grp.update()
        self.enemy_grp.update()
        self.dialogue_manager.update()


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

