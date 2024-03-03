import pygame
from modules import *
import asyncio

class Master:

    def __init__(self):

        self.app:App
        self.debug:Debug
        self.dt:float
        self.offset:pygame.Vector2

        # self.font_d = pygame.font.Font("fonts/PixelOperator.ttf", 10)
        # self.font_1 = pygame.font.Font("fonts/PixelOperator.ttf", 14)
        # self.font = pygame.font.Font("fonts/PixelOperator-Bold.ttf", 18)
        # self.font_big = pygame.font.Font("fonts/PixelOperator.ttf", 32)
        self.font_d = pygame.font.Font("fonts/tom-thumb-modified.ttf", 6)
        self.font_1 = pygame.font.Font("fonts/tom-thumb-modified.ttf", 7)
        # self.font = pygame.font.Font("fonts/tom-thumb-modified.ttf", 9)
        self.font = pygame.font.Font("fonts/PixelOperator.ttf", 12)
        self.font_big = pygame.font.Font("fonts/tom-thumb-modified.ttf", 16)

    
class App:

    MAIN_MENU = 0
    INTRO_CUTSCENE = 1
    IN_GAME = 2
    TRANSITION = 3

    GAME_WIN = 7
    GAME_LOOSE = 8

    def __init__(self):
        
        pygame.init()
        self.screen = pygame.display.set_mode((W, H), pygame.SCALED)
        # self.screen = pygame.display.set_mode((W, H), pygame.SCALED|pygame.FULLSCREEN)
        pygame.display.set_caption(GAME_NAME)
        self.clock = pygame.time.Clock()
        pygame.event.set_blocked(None)
        pygame.event.set_allowed((pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                    pygame.KEYDOWN, pygame.KEYUP))

        self.state = self.MAIN_MENU

        self.master = Master()
        # SoundSet(self.master)
        self.master.app = self
        self.debug = Debug(self.screen, font=self.master.font_d, offset=4)
        self.master.debug = self.debug
        self.game = Game(self.master)
        self.main_menu = MainMenu(self.master)
        Music(self.master)
        self.cutscene = FiFo(self.master, "intro", self.IN_GAME)

    async def run(self):
        
        while True:

            pygame.display.update()

            self.master.dt = self.clock.tick(FPS) / 16.667
            if self.master.dt > 10: self.master.dt = 10
            # self.debug("FPS:", round(self.clock.get_fps(), 2))
            # self.debug("Offset:", (round(self.master.offset.x, 2), round(self.master.offset.y, 2)))

            for event in pygame.event.get((pygame.QUIT)):
                
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            await asyncio.sleep(0)

            # self.master.music.run()
            self.run_states()
            self.debug.draw()

    def run_states(self):
        
        if self.state == self.MAIN_MENU:
            self.main_menu.run()
        elif self.state == self.INTRO_CUTSCENE:
            self.cutscene.run()
                # self.state = self.IN_GAME
        elif self.state == self.IN_GAME:
            self.game.run()

if __name__ == "__main__":

    app = App()
    # app.run()
    asyncio.run(app.run())
