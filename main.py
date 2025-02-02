# Hey bro, import "*" is not a good practice

# import os
# import cProfile
from config import *
from engine import *
from spriteRenderer import *
from menu import *
from sprites import *
from menuComponents import *
from mapEditor import *
import pygame
import sys


# Insert directory paths
sys.path.insert(0, 'menu')
sys.path.insert(0, 'menu/functions')
sys.path.insert(0, 'sprites')


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.key.set_repeat(500, 100)
        pygame.font.init()
        pygame.event.set_allowed([QUIT, VIDEORESIZE, KEYDOWN, MOUSEBUTTONDOWN])

        self.playing = True
        self.clock = pygame.time.Clock()
        self.running = True

        # Start with the game paused (menus will keep running though)
        self.paused = True

        self.fullscreen = config["graphics"]["fullscreen"]
        self.vsync = config["graphics"]["vsync"]

        # Engine
        self.renderer = Renderer(self)
        self.spriteRenderer = SpriteRenderer(self)
        self.clickManager = ClickManager(self)
        self.textHandler = TextHandler()

        # Loaders
        self.imageLoader = ImageLoader(self)
        self.mapLoader = MapLoader()
        self.audioLoader = AudioLoader()

        # Map editor
        self.mapEditor = MapEditor(self)

        # Menu's
        self.mainMenu = MainMenu(self)
        self.optionMenu = OptionMenu(self)

        if self.fullscreen:
            self.renderer.setFullscreen()

        self.setCaption()
        self.setIcon()
        self.setCursor()

        # self.audioLoader.playSound("boot", 2)
        # self.audioLoader.fadeOutSound(10000, 2)

        # print(pygame.font.get_fonts())

    # Set the games caption (name)
    def setCaption(self):
        pygame.display.set_caption(config["game"]["gameTitle"])

    # Set the games icon
    def setIcon(self):
        icon = self.imageLoader.getImage(config["game"]["icon"])
        pygame.display.set_icon(icon)

    # Set the games cursor (cursor class?)
    def setCursor(self):
        pygame.mouse.set_cursor(*pygame.cursors.tri_left)

    def getPaused(self):
        return self.paused

    def __quit(self):
        self.playing = False

    def __events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.__quit()

            elif e.type == pygame.VIDEORESIZE:
                self.renderer.setScale(e.size, self.fullscreen)

            if e.type == pygame.KEYDOWN:
                self.textHandler.events(e)
                self.textHandler.setPressed(True)

                # Only open the option manu if the game isn't paused
                # and the main menu isn't open
                if (e.key == pygame.K_ESCAPE and not self.mainMenu.open
                        and not self.spriteRenderer.getMenu().open):
                    # Close the dropdowns first
                    if not self.mapEditor.isDropdownsClosed():
                        if not self.optionMenu.open:
                            self.optionMenu.main(True, True)
                        elif self.optionMenu.open:
                            self.optionMenu.closeTransition()

                elif e.key == pygame.K_RIGHT and self.mainMenu.open:
                    self.mainMenu.levelForward()
                elif e.key == pygame.K_LEFT and self.mainMenu.open:
                    self.mainMenu.levelBackward()

                elif e.key == pygame.K_p:
                    if self.spriteRenderer.getHud().open:
                        self.spriteRenderer.getHud().togglePauseGame()

                # If the game is not paused and the main menu
                # isnt open and no text inputs are open
                if (not self.paused and not self.mainMenu.open
                        and not self.textHandler.getActive()):
                    # Show / Hide the different layers depending on key press
                    if pygame.key.name(e.key) == config["controls"]["layer1"]:
                        self.spriteRenderer.showLayer(1)
                        self.mapEditor.showLayer(1)

                    elif (pygame.key.name(e.key)
                            == config["controls"]["layer2"]):
                        self.spriteRenderer.showLayer(2)
                        self.mapEditor.showLayer(2)

                    elif (pygame.key.name(e.key)
                            == config["controls"]["layer3"]):
                        self.spriteRenderer.showLayer(3)
                        self.mapEditor.showLayer(3)

                    elif (pygame.key.name(e.key)
                            == config["controls"]["layer4"]):
                        self.spriteRenderer.showLayer(4)
                        self.mapEditor.showLayer(4)

                if (e.key == pygame.K_z
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                        and not self.paused and not self.mainMenu.open):
                    self.mapEditor.undoChange()
                    level = self.mapEditor.getLevelData()
                    layer = self.mapEditor.getLayer()
                    # Reload the level
                    self.mapEditor.createLevel(level, layer=layer)

                elif (e.key == pygame.K_y
                        and pygame.key.get_mods() & pygame.KMOD_CTRL
                        and not self.paused and not self.mainMenu.open):
                    self.mapEditor.redoChange()
                    level = self.mapEditor.getLevelData()
                    layer = self.mapEditor.getLayer()
                    # Reload the level
                    self.mapEditor.createLevel(level, layer=layer)

            elif e.type == pygame.KEYUP:
                self.textHandler.setPressed(False)

            # Just for fun :) - And refactoring ( ͡° ͜ʖ ͡°)
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 4:
                    self.spriteRenderer.setFixedScale(
                        self.spriteRenderer.getFixedScale() + 0.1)
                    self.spriteRenderer.resize()

                elif e.button == 5:
                    self.spriteRenderer.setFixedScale(
                        self.spriteRenderer.getFixedScale() - 0.1)
                    self.spriteRenderer.resize()

            # Make left click set the destination on the click manager instead
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.clickManager.setClicked(True)
                elif e.button == 3:
                    self.clickManager.setRightClicked(True)
            else:
                self.clickManager.setClicked(False)
                self.clickManager.setRightClicked(False)

    def run(self):
        # Main menu
        self.mainMenu.main()

        # Game loop
        while self.playing:
            self.__events()
            self.dt = self.clock.tick() / 1000

            # Prevent game from updating if window is being moved?
            if self.dt >= 0.05:
                continue

            self.__update()
            self.__draw()

        self.running = False

    def __update(self):
        # print(self.paused)
        if not self.paused and not self.mainMenu.open:
            self.spriteRenderer.update()
            self.mapEditor.update()

    def __draw(self):
        # Add sprites
        if self.mainMenu.open:
            self.renderer.prepareSurface(self.mainMenu.getBackgroundColor())

        self.spriteRenderer.render()
        self.mapEditor.render()

        # Add menus when not paused
        if self.paused:
            # To Do:Different option menus for sprite renderer and level editor
            self.optionMenu.display()
        if self.mainMenu.open:
            self.mainMenu.display()

        # render everything
        self.renderer.render()


if __name__ == "__main__":
    g = Game()
    g.run()
    # cProfile.run('g.run()')
    pygame.quit()
