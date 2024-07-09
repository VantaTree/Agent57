import pygame
from modules import *
import asyncio

class Master:

    def __init__(self):

        self.app:App
        self.dt:float
        self.fps:int = FPS
        self.debug:Debug
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
    PAUSE = 4
    SETTINGS = 5
    
    GAME_WIN = 7
    GAME_LOOSE = 8
    THE_END = 10

    def __init__(self):
        
        pygame.init()
        self.screen = pygame.display.set_mode((W, H), pygame.SCALED)
        # self.screen = pygame.display.set_mode((W, H), pygame.SCALED|pygame.FULLSCREEN)
        pygame.display.set_caption(GAME_NAME)
        self.clock = pygame.time.Clock()
        pygame.event.set_blocked(None)
        pygame.event.set_allowed((pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                    pygame.KEYDOWN, pygame.KEYUP, pygame.FINGERDOWN,
                                    pygame.FINGERUP, pygame.FINGERMOTION))

        self.state = self.MAIN_MENU

        self.master = Master()
        self.master.app = self
        self.debug = Debug(self.screen, font=self.master.font_d, offset=4, surf_enabled=True)
        self.master.debug = self.debug
        self.game = Game(self.master)
        self.main_menu = MainMenu(self.master)
        self.pause_menu = PauseMenu(self.master)
        self.settings_menu = SettingsMenu(self.master)
        self.cutscene = FiFo(self.master, "intro", self.IN_GAME)

        # SoundSet(self.master)
        # Music(self.master)

        self.fingers = {}
        self.fingers_prev = {}

    async def run(self):
        
        while True:

            pygame.display.update()

            self.master.dt = self.clock.tick(self.master.fps) / 16.667
            if self.master.dt > 10: self.master.dt = 10
            self.debug("FPS:", round(self.clock.get_fps(), 2))
            self.debug("Mouse:", pygame.mouse.get_pos())
            # self.debug("Offset:", (round(self.master.offset.x, 2), round(self.master.offset.y, 2)))

            for event in pygame.event.get((pygame.QUIT)):
                
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            await asyncio.sleep(0)

            self.fingers_prev = self.fingers.copy()
            for event in pygame.event.get((pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION)):
                if not self.game.touch_btns_enabled: continue

                if event.type == pygame.FINGERDOWN:
                    self.fingers[event.finger_id] = (event.x*W, event.y*H)
                if event.type == pygame.FINGERMOTION:
                    self.fingers[event.finger_id] = (event.x*W, event.y*H)
                if event.type == pygame.FINGERUP:
                    try:
                        del self.fingers[event.finger_id]
                    except KeyError: pass

            # self.master.music.run()
            self.run_states()
            self.debug.draw()

    def run_states(self):
        
        if self.state == self.MAIN_MENU:
            self.main_menu.run()
        elif self.state in (self.INTRO_CUTSCENE, self.GAME_WIN, self.TRANSITION):
            self.cutscene.run()
        elif self.state == self.GAME_LOOSE:
            if self.cutscene.run():
                self.game.restart_level()
        elif self.state == self.IN_GAME:
            self.game.run()
        elif self.state == self.PAUSE:
            self.pause_menu.run()
        elif self.state == self.SETTINGS:
            self.settings_menu.run()
        elif self.state == self.THE_END:
            self.screen.fill("gold")
            pass

    def death_screen(self):

        self.state = self.GAME_LOOSE
        self.cutscene = FiFo(self.master, "you_died", self.IN_GAME)

    def next_level(self, level):
        self.state = self.TRANSITION
        self.cutscene = FiFo(self.master, F"level_{level}", self.IN_GAME)

    def finish_game(self):

        self.state = self.GAME_WIN
        self.cutscene = FiFo(self.master, "end won", self.THE_END)


if __name__ == "__main__":

    app = App()
    # app.run()
    asyncio.run(app.run())
