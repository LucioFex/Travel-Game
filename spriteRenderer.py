# import os
# import json
import pygame
from pygame.locals import *
from config import *
import random
from layer import *
from clickManager import *
from node import *
from gridManager import *
from meterController import *
from menu import *


class SpriteRenderer():
    # Loads all the sprites into groups and stuff
    def __init__(self, game):
        self.allSprites = pygame.sprite.Group()
        self.entities = pygame.sprite.Group()
        self.layer1 = pygame.sprite.Group()  # layer 1
        self.layer2 = pygame.sprite.Group()  # layer 2
        self.layer3 = pygame.sprite.Group()  # layer 3
        self.layer4 = pygame.sprite.Group()  # layer 4 is all layers combined
        self.game = game
        self.currentLayer = 4

        self.level = ""

        # Hud for when the game is running
        self.hud = GameHud(self.game)
        self.menu = GameMenu(self.game)
        self.messageSystem = MessageHud(self.game)

        self.personClickManager = PersonClickManager(self.game)
        self.transportClickManager = TransportClickManager(self.game)

        self.rendering = False

        # Game timer to keep track of how long has been played
        self.timer = 0

        # Make this dependant on the level and make it decrease
        # as the number of people who reach their destinations increase
        self.timeStep = 25

        self.lives = DEFAULTLIVES
        self.score, self.bestScore = 0, 0

        self.dt = 1  # Control the speed of whats on screen
        self.startDt = self.dt
        self.fixedScale = 1  # Control the size of whats on the screen
        self.startingFixedScale = 0
        self.paused = False  # Individual pause for the levels

        self.setDefaultMap()

        self.totalPeople, self.completed, self.totalToComplete = 0, 0, 0
        self.totalPeopleNone = False
        self.slowDownMeterAmount = 75

        self.debug = False
        self.darkMode = False

        # The connection types availabe on the map (always has layer 4)
        self.connectionTypes = ["layer 4"]

    def setDefaultMap(self):
        self.levelData = {
            "mapName": "",
            "locked": {"isLocked": False, "unlock": 0},  # Amount to unlock

            # Map can / cannot be deleted; maps that cant be
            # deleted cant be opened in the editor
            "deletable": True,

            "saved": False,  # Has the map been saved before
            "width": 18,
            "height": 10,
            "difficulty": 1,  # Out of 4
            "total": 8,  # Total to complete the level
            "score": 0,
            "completion": { "total": 10, "completed": False, "time": 0},
            "backgrounds": {
                "layer 1": CREAM,  # Default color: CREAM :)
                "layer 2": CREAM,
                "layer 3": CREAM,
                "layer 4": CREAM
            },
            "connections": {},
            "transport": {},
            "stops": {},
            "destinations": {}
        }  # Level data to be stored, for export to JSON

    # Save function, for when the level has already
    # been created before (and is being edited)
    def saveLevel(self):
        self.game.mapLoader.saveMap(self.levelData["mapName"], self.levelData)

    def setRendering(self, rendering, transition=False):
        self.rendering = rendering
        self.hud.main(transition) if self.rendering else self.hud.close()

        if self.rendering:
            self.messageSystem.main()
        else:
            self.messageSystem.close()

        # Create the paused surface when first rendering
        self.createPausedSurface()

    def runStartScreen(self):
        if self.rendering and not self.debug:
            self.menu.startScreen()

    def runEndScreen(self, completed=False):
        if self.rendering and not self.debug:
            if completed:
                self.menu.endScreenComplete(True)  # Run with transition
            else:
                self.menu.endScreenGameOver(True)  # Run with transition

    def setCompleted(self, completed):
        self.completed = completed
        self.hud.setCompletedText()

    # When the player completed the level, set it to complete
    # in the level data and save the data
    def setLevelComplete(self):
        if not hasattr(self, 'levelData'):
            return

        # If the level is not already set to completed, complete it
        if not self.levelData["completion"]["completed"]:
            self.levelData["completion"]["completed"] = True
            self.saveLevel()

    # Use the number of lives left to work out the players score TODO:
    #   Make this use other factors in the future

    # Return the previous keys and difference so
    # this can be used in the menu animation
    def setLevelScore(self):
        if not hasattr(self, 'levelData'):
            return

        self.score = self.lives
        previousScore = 0

        if "score" in self.levelData:
            previousScore = self.levelData["score"]
            self.bestScore = previousScore

        if self.score > previousScore:
            self.levelData["score"] = self.score
            self.saveLevel()

        if self.score - previousScore > 0:
            scoreDifference = self.score - previousScore
        else:
            scoreDifference = 0

        # Use this in the menu animation
        previousKeys = config["player"]["keys"]
        config["player"]["keys"] += scoreDifference
        dump(config)

        return previousKeys, scoreDifference, previousScore

    def setTotalToComplete(self, totalToComplete):
        self.totalToComplete = totalToComplete

    def setSlowDownMeterAmount(self, slowDownMeterAmount):
        self.slowDownMeterAmount = slowDownMeterAmount

    def setDt(self, dt):
        self.dt = dt

    def setFixedScale(self, fixedScale):
        self.fixedScale = fixedScale

    def setStartingFixedScale(self, startingFixedScale):
        self.startingFixedScale = startingFixedScale

    def setDebug(self, debug):
        self.debug = debug

    def setDarkMode(self):
        if ("backgrounds" in self.levelData and
            "darkMode" in self.levelData["backgrounds"]
                and self.levelData["backgrounds"]["darkMode"]):
            self.darkMode = True

        else:
            self.darkMode = False

    def setTotalPeople(self, totalPeople):
        self.totalPeople = totalPeople

    def setLives(self, lives):
        self.lives = lives

    def togglePaused(self):
        self.dt = 0
        self.paused = not self.paused
        # self.game.paused = not self.game.paused
        # self.createPausedSurface()

    def getStartDt(self):
        return self.startDt

    def getDt(self):
        return self.dt

    def getFixedScale(self):
        return self.fixedScale

    def getStartingFixedScale(self):
        return self.startingFixedScale

    def getHud(self):
        return self.hud

    def getMenu(self):
        return self.menu

    def getMessageSystem(self):
        return self.messageSystem

    def getLevel(self):
        return self.level

    def getLevelData(self):
        return self.levelData

    def getPersonClickManager(self):
        return self.personClickManager

    def getTransportClickManager(self):
        return self.transportClickManager

    def getLayer(self):
        return self.currentLayer

    def getCompleted(self):
        return self.completed

    def getTotalToComplete(self):
        return self.totalToComplete

    def getSlowDownMeterAmount(self):
        return self.slowDownMeterAmount

    def getDebug(self):
        return self.debug

    def getConnectionTypes(self):
        return self.connectionTypes

    def getDarkMode(self):
        return self.darkMode

    def getTotalPeople(self):
        return self.totalPeople

    def getLives(self):
        return self.lives

    def getAllDestination(self):
        if hasattr(self, 'allDestinations'):
            return self.allDestinations

    def getScore(self):
        return self.score

    def getBestScore(self):
        return self.bestScore

    def getPaused(self):
        return self.paused

    def getCurrentLayer(self):
        return self.currentLayer

    def removeLife(self):
        self.lives -= 1
        # remove a heart from the hud here or something
        self.hud.setLifeAmount()
        if self.lives <= 0:
            # Although we pause the game in the timer, we want to
            # stop anything else from reducing the life count here whilst the
            # timer is decreasing (so no one can die whilst it is decreasing)
            pass

    def addToCompleted(self):
        self.completed += 1
        # self.timeStep -= 0.5
        self.hud.setCompletedAmount()
        self.meter.addToAmountToAdd(20)

    # Reset the level back to its default state
    def clearLevel(self):
        self.paused = False  # Not to confuse the option menu
        self.startingFixedScale = 0  # reset the scale back to default
        self.timer = 0
        self.lives = DEFAULTLIVES
        self.totalPeople = 0
        self.totalPeopleNone = False
        self.entities.empty()
        self.allSprites.empty()
        self.layer1.empty()
        self.layer2.empty()
        self.layer3.empty()
        self.layer4.empty()

        # Reset the layers to show the top layer
        self.currentLayer = 4
        self.connectionTypes = []
        self.setDefaultMap()

    def createLevel(self, level, debug=False):
        self.clearLevel()
        # Currently this calls the wrong hud as its done before the hud is set
        self.setCompleted(0)
        self.debug = debug

        self.gridLayer4 = Layer4(self, (self.allSprites, self.layer4), level)

        # Set the name of the level
        self.level = self.gridLayer4.getGrid().getLevelName()

        # Set the level data
        self.levelData = self.gridLayer4.getGrid().getMap()

        # for running the game in test mode (when testing a level)
        if self.debug:
            # Push the level down since we have hud at the top
            spacing = (1.5, 1.5)
            self.hud = PreviewHud(self.game, spacing)
        else:
            # self.startingFixedScale = -0.05
            spacings = {
                (16, 9): (1.5, 1),
                (18, 10): (2, 1.5),
                (20, 11): (1.5, 1),
                (22, 12): (1.5, 1)}

            size = (self.levelData["width"], self.levelData["height"])
            # spacing = spacings[size]
            spacing = (1.5, 1)
            self.hud = GameHud(self.game, spacing)

        # we want to get which connectionTypes are available in the map
        for connectionType in self.levelData['connections']:
            self.connectionTypes.append(connectionType)

        self.gridLayer3 = Layer3(
            self, (self.allSprites, self.layer3, self.layer4), level, spacing)
        self.gridLayer1 = Layer1(
            self, (self.allSprites, self.layer1, self.layer4), level, spacing)

        # Walking layer at the bottom so nodes are drawn above metro stations
        self.gridLayer2 = Layer2(
            self, (self.allSprites, self.layer2, self.layer4), level, spacing)

        self.gridLayer4.addLayerLines(
            self.gridLayer1, self.gridLayer2, self.gridLayer3)

        self.gridLayer1.grid.loadTransport("layer 1")
        self.gridLayer2.grid.loadTransport("layer 2")
        self.gridLayer3.grid.loadTransport("layer 3")

        self.removeDuplicates()

        # Set all the destinations to be the destinations from all layers
        layer1Destinations = self.gridLayer1.getGrid().getDestinations()
        layer2Destinations = self.gridLayer2.getGrid().getDestinations()
        layer3Destinations = self.gridLayer3.getGrid().getDestinations()
        self.allDestinations = (
            layer1Destinations + layer2Destinations + layer3Destinations)

        # Set number of people to complete level
        if "total" not in self.levelData:
            self.totalToComplete = random.randint(8, 12)

        else:
            self.totalToComplete = self.levelData["total"]
        # self.totalToComplete = 1

        self.meter = MeterController(
            self, self.allSprites, self.slowDownMeterAmount)
        self.setDarkMode()

        # If there is more than one layer we want to be able
        # to see 'all' layers at once (layer 4)
        # otherwise we only need to see the single layer

        if len(self.connectionTypes) > 1 or self.debug:
            self.connectionTypes.append("layer 4")
        else:
            self.showLayer(
                self.getGridLayer(self.connectionTypes[0]).getNumber())

    # Draw the level to a surface and return this surface for blitting
    # (i.e on the level selection screen)
    def createLevelSurface(self, level):
        self.clearLevel()
        self.startingFixedScale = -0.2

        spacings = {
            (16, 9): (3.5, 2),
            (18, 10): (4, 2.5),
            (20, 11): (4.5, 2.8),
            (22, 12): (5, 3)}

        gridLayer4 = MenuLayer4(self, (), level)

        levelData = gridLayer4.getGrid().getMap()
        size = (levelData["width"], levelData["height"])
        spacing = spacings[size]

        gridLayer3 = Layer3(self, (), level, spacing)
        gridLayer1 = Layer1(self, (), level, spacing)
        gridLayer2 = Layer2(self, (), level, spacing)
        gridLayer4.addLayerLines(gridLayer1, gridLayer2, gridLayer3)

        return gridLayer4.getLineSurface()

    # Create a new surface when the game is paused with all the sprites
    # currently in the game, so these don't have to be drawn every frame
    # (as they are not moving)

    def createPausedSurface(self):
        if self.rendering and self.game.paused:
            self.pausedSurface = pygame.Surface((
                int(config["graphics"]["displayWidth"]
                    * self.game.renderer.getScale()),

                int(config["graphics"]["displayHeight"]
                    * self.game.renderer.getScale()))).convert()

            self.pausedSurface.blit(self.gridLayer4.getLineSurface(), (0, 0))
            for sprite in self.layer4:
                # sprite.drawPaused(self.pausedSurface)
                sprite.makeSurface()

                if hasattr(sprite, 'image'):  # Not all sprites have an image
                    self.pausedSurface.blit(sprite.image, (sprite.rect))

            # for component in (
            #     self.hud.getComponents()
            #         + self.messageSystem.getComponents()):
            #     # draw hud and message system
            #     component.drawPaused(self.pausedSurface)

            return self.pausedSurface

    def getSpriteLayer(self, connectionType):
        if connectionType == "layer 1":
            return self.layer1
        elif connectionType == "layer 2":
            return self.layer2
        elif connectionType == "layer 3":
            return self.layer3
        elif connectionType == "layer 4":
            return self.layer4

    def getGridLayer(self, connectionType):
        if connectionType == "layer 1":
            return self.gridLayer1
        elif connectionType == "layer 2":
            return self.gridLayer2
        elif connectionType == "layer 3":
            return self.gridLayer3
        elif connectionType == "layer 4":
            return self.gridLayer4

    # Get all the nodes from all layers in the spriterenderer
    def getAllNodes(self, sortNodes=False):
        layer1Nodes = self.gridLayer1.getGrid().getNodes()
        layer2Nodes = self.gridLayer2.getGrid().getNodes()
        layer3Nodes = self.gridLayer3.getGrid().getNodes()
        allNodes = layer1Nodes + layer2Nodes + layer3Nodes

        # Sort the node so that the stops are at the top
        if sortNodes:
            allNodes = sorted(
                allNodes, key=lambda x: isinstance(x, Stop))
            allNodes = sorted(
                allNodes, key=lambda x: isinstance(x, Destination))
            # Reverse the list so they're at the front
            allNodes = allNodes[::-1]

        return allNodes

    # Remove duplicate nodes on layer 4 for layering
    def removeDuplicates(self, allNodes=None, removeLayer=None):
        seen = {}
        dupes = []
        removeLayer = self.layer4 if removeLayer is None else removeLayer

        if allNodes is None:
            allNodes = self.getAllNodes()

        # Make sure stops are at the front of the list, so they are not removed
        allNodes = sorted(allNodes, key=lambda x: isinstance(x, Stop))
        allNodes = sorted(allNodes, key=lambda x: isinstance(x, Destination))
        allNodes = allNodes[::-1]  # Reverse the list so they're at the front

        for node in allNodes:
            if node.getNumber() not in seen:
                seen[node.getNumber()] = 1
            else:
                if seen[node.getNumber()] == 1:
                    dupes.append(node)

        for node in dupes:
            removeLayer.remove(node)

    # if there is a node above the given node,
    # return the highest node, else return node
    def getTopNode(self, bottomNode):
        allNodes = self.getAllNodes(True)

        for node in allNodes:
            if node.getNumber() == bottomNode.getNumber():
                return node

        return bottomNode

    def update(self):
        if not self.rendering:
            return
        self.allSprites.update()

        if self.paused:
            return

        self.events()
        self.timer += self.game.dt * self.dt

        # Always spawn a person if there is no people
        # left on the map, to stop player having to wait
        if self.timer > self.timeStep:
            self.timer = 0
            self.gridLayer2.createPerson(self.allDestinations)

        if self.totalPeople <= 0:
            if not self.totalPeopleNone:
                self.timer = 0
                self.totalPeopleNone = True

            # wait 2 seconds before spawing the next
            # person when there is no people left
            if self.timer > 2 and self.totalPeopleNone:
                self.timer = 0
                self.gridLayer2.createPerson(self.allDestinations)
                self.totalPeopleNone = False

    def events(self):
        keys = pygame.key.get_pressed()
        key = [pygame.key.name(k) for k, v in enumerate(keys) if v]

        #     self.dt = self.startDt
        # keys = pygame.key.get_pressed()
        # key = [pygame.key.name(k) for k, v in enumerate(keys) if v]

        # if len(key) == 1:
        #     if key[0] == config["controls"]["dtDown"]:
        #         self.game.clickManager.setSpaceBar(True)
        # else:
        #     self.game.clickManager.setSpaceBar(False)

        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.game.clickManager.setSpaceBar(True)

            if (
                self.dt != self.startDt - self.meter.getSlowDownAmount()
                    and not self.meter.getEmpty()):
                self.game.audioLoader.playSound("slowIn", 1)
        else:
            if self.dt != self.startDt:
                self.game.audioLoader.playSound("slowOut", 1)

            self.game.clickManager.setSpaceBar(False)

    # Make people on the current layer clickable, and the rest non-clickable
    def resetPeopleClicks(self):
        totalPeople = (
            self.gridLayer1.getPeople() +
            self.gridLayer2.getPeople() +
            self.gridLayer3.getPeople() +
            self.gridLayer4.getPeople())

        currentLayerPeople = self.getGridLayer(
            "layer " + str(self.currentLayer)).getPeople()
        for person in totalPeople:
            if person in currentLayerPeople or self.currentLayer == 4:
                # Always went every person to be clickable on the top layer
                person.setCanClick(True)

            else:
                person.setCanClick(False)

    def showLayer(self, layer):
        if not self.rendering:
            return

        # Only switch to a layer that is in the map
        if "layer " + str(layer) in self.connectionTypes:
            self.currentLayer = layer
            # Redraw the nodes so that the mouse cant collide with them
            self.resize()
            self.hud.updateLayerText()
            self.resetPeopleClicks()

    def resize(self):
        # If a layer has any images, they must be resized here
        if self.rendering:
            self.gridLayer1.resize()
            self.gridLayer2.resize()
            self.gridLayer3.resize()
            # Only need to do this if it has components
            self.gridLayer4.resize()

            # We want to reset the layer 4 lines with the
            # new ones (resized) from the other layers
            self.gridLayer4.addLayerLines(
                self.gridLayer1, self.gridLayer2, self.gridLayer3)

            # resize huds and menus
            self.hud.resize()
            self.menu.resize()
            self.messageSystem.resize()

            for sprite in self.allSprites:
                sprite.dirty = True

            self.createPausedSurface()

    def renderLayer(self, layer, gridLayer, group):
        if self.currentLayer == layer:
            gridLayer.draw()
            for sprite in group:
                sprite.draw()

    def render(self):
        if self.rendering:
            if not self.game.paused:
                # Entities drawn below the other sprites
                for entity in self.entities:
                    entity.draw()

                self.renderLayer(1, self.gridLayer1, self.layer1)
                self.renderLayer(2, self.gridLayer2, self.layer2)
                self.renderLayer(3, self.gridLayer3, self.layer3)
                self.renderLayer(4, self.gridLayer4, self.layer4)

            else:
                if hasattr(self, 'pausedSurface'):
                    self.game.renderer.addSurface(
                        self.pausedSurface, (self.pausedSurface.get_rect()))

            self.hud.display()
            self.messageSystem.display()
            self.menu.display()
