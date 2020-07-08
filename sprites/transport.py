import pygame
from pygame.locals import *
import pygame.gfxdraw
from config import *
import os
import random
import decimal
import math

import node as NODE
import person as PERSON
import connection as CONNECTION    

vec = pygame.math.Vector2


class Transport(pygame.sprite.Sprite):
    def __init__(self, game, groups, currentConnection, direction, running):
        self.groups = groups
        super().__init__(self.groups)
        
        self.game = game
        self.currentConnection = currentConnection
        self.currentNode = self.currentConnection.getFrom()
        self.currentNode.addTransport(self)
        self.width = 30
        self.height = 30

        self.offset = vec(-5, -5) # -5 is half the offset of the connector
        self.vel = vec(0, 0)
        self.pos = (self.currentConnection.getFrom().pos - self.currentConnection.getFrom().offset) + self.offset

        self.speed = float(decimal.Decimal(random.randrange(40, 50)))
        self.direction = direction #0 forwards, 1 backwards
        
        self.dirty = True

        self.running = running
        self.moving = self.running
        self.timer = 0
        self.timerLength = 300

        #people travelling in the transport
        self.people = []

        self.imageName = "train"
        self.stopType = NODE.MetroStation


    #### Getters ####

    # Return the people, in a list, current on the transport
    def getPeople(self):
        return self.people


    # Return if the transport is moving or not
    def getMoving(self):
        return self.moving


    #### Setters ####

    def setSpeed(self, speed):
        self.speed = speed

    def setDirection(self, direction):
        self.direction = direction

    def setMoving(self, moving):
        self.moving = moving


    # Set the connection that the transport will follow next
    def setConnection(self, nextNode):
        possibleNodes = []
        backwardsNodes = []

        for connection in nextNode.getConnections():
            if connection.getType() == self.currentConnection.getType():
                if connection.getDirection() == self.direction:
                    possibleNodes.append(connection)
                else:
                    backwardsNodes.append(connection)

        #it can keep going the same direction
        if len(possibleNodes) > 0:
            # if theres multiple possible nodes, pick a random one                          #TO DO - make transports follow specific path
            self.currentConnection = possibleNodes[random.randint(0, len(possibleNodes) - 1)]
        else:
            self.direction = CONNECTION.Connection.Direction(not self.direction.value) # Go the opposite direction
            self.currentConnection = backwardsNodes[0]

        self.currentNode.removeTransport(self)
        self.currentNode = self.currentConnection.getFrom()
        self.currentNode.addTransport(self)



    # Set the next connection for the transport to follow
    def setNextConnection(self):
        nextNode = self.currentConnection.getTo()
        
        # If the transport is moving, set its next connection to the next upcoming node
        if self.moving:
            self.setConnection(nextNode)

        if isinstance(self.currentNode, self.stopType): # and len(self.currentNode.getPeople()) > 0

            # Remove anyone departing before we add new people
            self.removePeople()

            # Set people waiting for the transportation to departing 
            self.setPeopleBoarding()

            self.moving = False
            self.timer += 100 * self.game.dt

            # Leaving the station
            if self.timer > self.timerLength:
                self.moving = True
                self.timer = 0

                # Add the people boarding to the transportation
                self.addPeople()


    # Set people waiting at the train station to boarding the transportation 
    def setPeopleBoarding(self):
        # If theres no one at the station, dont bother trying to add anyone
        if len(self.currentNode.getPeople()) <= 0:
            return

        for person in self.currentNode.getPeople():
            if person.getStatus() == PERSON.Person.Status.WAITING: # If they're waiting for the train
                person.setStatus(PERSON.Person.Status.BOARDING)


    # Add a person to the transport
    def addPerson(self, person):
        self.people.append(person)

    # Remove a person from the transport
    def removePerson(self, person):
        self.people.remove(person)


    def remove(self):
        self.kill()
    
    


    # Add multiple people who are departing on the transportation
    def addPeople(self):
        # If theres no one at the station, dont bother trying to add anyone
        if len(self.currentNode.getPeople()) <= 0:
            return

        for person in self.currentNode.getPeople():
            # Only remove people from the station once the train is moving
            if person.getStatus() == PERSON.Person.Status.BOARDING:
                self.addPerson(person)
                self.currentNode.removePerson(person)
                person.setStatus(PERSON.Person.Status.MOVING)

                # Make the person unclicked?
                # self.game.clickManager.setPerson(None)


    # Remove multiple people who are departing from the transportation
    def removePeople(self):
        if len(self.people) <= 0:
            return

        for person in self.people:
            if person.getStatus() == PERSON.Person.Status.DEPARTING:
                self.removePerson(person) # Remove the person from the transport
                self.currentNode.addPerson(person)  # Add the person back to the node where the transport is stopped
                person.setStatus(PERSON.Person.Status.UNASSIGNED)  # Set the person to unassigned so they can be moved
                person.setCurrentNode(self.currentNode) # Set the persons current node to the node they're at

                # Position the person offset to the node
                person.pos = (self.currentNode.pos - self.currentNode.offset) + person.offset
                person.rect.topleft = person.pos * self.game.renderer.getScale()
                person.moveStatusIndicator()


    #move all the people within the transport relative to its location
    def movePeople(self):
        if len(self.people) <= 0:
            return

        for person in self.people:
            person.pos = self.pos + person.offset
            person.rect.topleft = person.pos * self.game.renderer.getScale()
            person.moveStatusIndicator()


    # Draw how long is left at each stop 
    def drawTimer(self):
        scale = self.game.renderer.getScale()

        # Arc Indicator 
        offx = 0.01
        step = self.timer / (self.timerLength / 2) + 0.02
        for x in range(6):
            pygame.draw.arc(self.game.renderer.gameDisplay, YELLOW, ((self.pos.x - 4) * scale, (self.pos.y - 4) * scale, (self.width + 8) * scale, (self.height + 8) * scale), math.pi / 2 + offx, math.pi / 2 + math.pi * step, 8)
            offx += 0.01


    def __render(self):
        self.dirty = False

        self.image = self.game.imageLoader.getImage(self.imageName)
        self.image = pygame.transform.smoothscale(self.image, (int(self.width * self.game.renderer.getScale()), 
                                                            int(self.height * self.game.renderer.getScale())))
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos * self.game.renderer.getScale()



    def draw(self):
        if self.dirty or self.image is None: self.__render()
        self.game.renderer.addSurface(self.image, (self.rect))

        if self.timer > 0:
            #draw the time indicator
            self.drawTimer()


    def events(self):
        pass


    def update(self):
        if hasattr(self, 'rect') and self.running:
            # Reset velocity to prevent infinate movement
            self.vel = (0, 0)

            dxy = (self.currentConnection.getTo().pos - self.currentConnection.getTo().offset) - self.pos + self.offset
            dis = dxy.length()

            if dis >= 0.5 and self.moving: #move towards the node
                # Speed up when leaving a stop
                # Change the number taken away from the length of the connection for the length of the smooth starting 
                # Change the other number to say when the smooth starting should begin (after how many pixels)
                if dis >= self.currentConnection.getDistance() - 15 and dis <= self.currentConnection.getLength().length() - 0.5 and isinstance(self.currentNode, self.stopType):
                    self.vel = (-(self.currentConnection.getLength() + dxy) * (self.speed / 12)) * self.game.dt

                # Slow down when reaching a stop
                # Change what number the distance is smaller than for the length of smooth stopping; larger lengths may make transport further from target
                elif dis <= 15 and isinstance(self.currentConnection.getTo(), self.stopType):
                    self.vel = (dxy * (self.speed / 10)) * self.game.dt

                else:
                    self.vel = dxy / dis * float(self.speed) * self.game.dt
                self.movePeople()

            else: #its reached the node
                self.setNextConnection()
                self.pos = (self.currentConnection.getFrom().pos - self.currentConnection.getFrom().offset) + self.offset

            self.pos += self.vel
            self.rect.topleft = self.pos * self.game.renderer.getScale()


class Taxi(Transport):
    def __init__(self, game, groups, currentConnection, direction, running):
        super().__init__(game, groups, currentConnection, direction, running)

        self.imageName = "taxi"
        self.stopType = NODE.Node

    # override
    def setPeopleBoarding(self):
        # If theres no one at the station, dont bother trying to add anyone
        if len(self.currentNode.getPeople()) <= 0:
            return

        for person in self.currentNode.getPeople():
            if person.getStatus() == PERSON.Person.Status.FLAG: # If they're waiting for the train
                person.setStatus(PERSON.Person.Status.BOARDING)


    # override 
    def setNextConnection(self):
        nextNode = self.currentConnection.getTo()
        
        # If the transport is moving, set its next connection to the next upcoming node
        if self.moving:
            self.setConnection(nextNode)


        if isinstance(self.currentNode, self.stopType) and len(self.currentNode.getPeople()) > 0 and self.checkTaxiStop(self.currentNode):

            # Set people waiting for the transportation to departing 
            self.setPeopleBoarding()

            self.moving = False
            self.timer += 100 * self.game.dt

            # Leaving the station
            if self.timer > self.timerLength:
                self.moving = True
                self.timer = 0

                # Add the people boarding to the transportation
                self.addPeople()

        elif isinstance(self.currentNode, self.stopType):
            # Remove anyone departing before we add new people
            self.removePeople()

            # Do I want to show the timer here?


    def checkTaxiStop(self, node):
        for person in node.getPeople():
            if person.getStatus() == PERSON.Person.Status.FLAG or person.getStatus() == PERSON.Person.Status.BOARDING:
                return True
        return False


    def checkPersonStop(self, node):
        for person in self.people:
            if person.getStatus() == PERSON.Person.Status.DEPARTING:
                return True
        return False


    # override
    def update(self):
        if hasattr(self, 'rect') and self.running:
            self.vel = (0, 0)

            dxy = (self.currentConnection.getTo().pos - self.currentConnection.getTo().offset) - self.pos + self.offset
            dis = dxy.length()

            if dis >= 0.5 and self.moving: #move towards the node
                
                # speed up when leaving
                if dis >= self.currentConnection.getDistance() - 15 and dis <= self.currentConnection.getLength().length() - 0.5 and isinstance(self.currentNode, self.stopType):
                    if self.checkTaxiStop(self.currentNode) or self.checkPersonStop(self.currentNode):
                        self.vel = (-(self.currentConnection.getLength() + dxy) * (self.speed / 12)) * self.game.dt
                    else:
                        self.vel = dxy / dis * float(self.speed) * self.game.dt

                # slow down when stopping
                elif dis <= 15 and isinstance(self.currentConnection.getTo(), self.stopType):
                    if self.checkTaxiStop(self.currentConnection.getTo()) or self.checkPersonStop(self.currentConnection.getTo()):
                        self.vel = (dxy * (self.speed / 10)) * self.game.dt
                    else:
                        self.vel = dxy / dis * float(self.speed) * self.game.dt
                        
                else:
                    self.vel = dxy / dis * float(self.speed) * self.game.dt

                self.movePeople()

            else:
                self.setNextConnection()
                self.pos = (self.currentConnection.getFrom().pos - self.currentConnection.getFrom().offset) + self.offset
            
            self.pos += self.vel
            self.rect.topleft = self.pos * self.game.renderer.getScale()



class Bus(Transport):
    def __init__(self, game, groups, currentConnection, direction, running):
        super().__init__(game, groups, currentConnection, direction, running)
        self.imageName = "bus"
        self.stopType = NODE.BusStop



class Tram(Transport):
    def __init__(self, game, groups, currentConnection, direction, running):
        super().__init__(game, groups, currentConnection, direction, running)
        self.imageName = "tram"
        self.stopType = NODE.TramStop


class Metro(Transport):
    pass
