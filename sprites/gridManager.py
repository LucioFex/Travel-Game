import pygame
from pygame.locals import *
import pygame.gfxdraw
from config import *
import os
import random
import math
import json

from node import *
from connection import *
from transport import *

class GridManager:
    def __init__(self, layer, groups, level = None, spacing = (1.5, 1.5)):
        self.layer = layer
        self.spriteRenderer = self.layer.getSpriteRenderer()
        self.game = self.layer.game
        self.groups = groups
        self.level = level
        self.levelName = ""

        self.nodes = []
        self.connections = []
        self.tempConnections = []
        self.transports = []
        self.destinations = []

        self.width = 18
        self.height = 10

        if self.level is not None:
            self.loadMap()

        scale = min(18 / self.width, 10 / self.height)
        scale += self.spriteRenderer.getStartingFixedScale() # apply the starting fixed scale when first rendering
        self.spriteRenderer.setFixedScale(scale)

        self.nodePositions = self.setNodePositions(spacing[0], spacing[1], self.width, self.height)

        # Entry nodes
        self.entryTopPositions = self.setNodePositions(1.5, -0.5, 18, 1)
        self.entryBottomPositions = self.setNodePositions(1.5, 11.5, 18, 1)
        
        self.transportMappings = {"metro": Metro, "bus": Bus, "tram": Tram, "taxi": Taxi}
        self.stopMappings = {"metro": MetroStation, "bus": BusStop, "tram": TramStop}
        self.editorStopMappings = {"metro": EditorMetroStation, "bus": EditorBusStop, "tram": EditorTramStop}
        self.destinationMappings = {"airport": Airport, "office": Office, "house": House}
        self.editorDestinationMappings = {"airport": EditorAirport, "office": EditorOffice, "house": EditorHouse}


    def getNodePositions(self):
        return self.nodePositions


    def getTransportMappings(self):
        return self.transportMappings


    def getStopMappings(self):
        return self.stopMappings


    def getEditorStopMappings(self):
        return self.editorStopMappings


    def getDestinationMappings(self):
        return self.destinationMappings


    def getEditorDestinationMappings(self):
        return self.editorDestinationMappings
         

    def getLevelName(self):
        return self.levelName


    # return the nodes, in a list to be appended to each layer
    def getNodes(self):
        return self.nodes


    # Return the connections, in a list for each layer
    def getConnections(self):
        return self.connections


    def getTempConnections(self):
        return self.tempConnections


    # Return the transportations, in a list for each layer
    def getTransports(self):
        return self.transports


    def getDestinations(self):
        return self.destinations


    def getMap(self):
        if hasattr(self, 'map'):
            return self.map
        return {}
        

    #generate an 18 * 10 board of possible node positions (x and y locations) for nodes to be added to
    def setNodePositions(self, offx = 1.5, offy = 1.5, width = 18, height = 10):
        # Offset on the x coordinate
        # Offset on the y coordinate
        spacing = 50 #spacing between each node
        positions = []

        scale = min(self.width / 18, self.height / 10) if min(self.width / 18, self.height / 10) > 1 else 1

        for i in range(width):
            for x in range(height):
                positions.append(((i + offx * scale) * spacing, (x + offy * scale) * spacing))
        return positions


    def addConnections(self, connectionType, A, B, temp = False):
        c1 = Connection(self.spriteRenderer, connectionType, A, B, temp, True) # only need to draw one of the connections
        c2 = Connection(self.spriteRenderer, connectionType, B, A, temp) 

        if temp:
            self.tempConnections.append(c1)
            self.tempConnections.append(c2)
        else:
            self.connections.append(c1) #forwards
            self.connections.append(c2) #backwards

        return c1, c2


    def removeConnections(self, connections = []):
        for connection in connections:
            self.connections.remove(connection)


    def removeTempConnections(self):
        self.tempConnections = []


    def getOppositeConnection(self, currentConnection):
        for connection in self.connections:
            if connection.getFrom() == currentConnection.getTo() and connection.getTo() == currentConnection.getFrom():
                return currentConnection, connection

        # There is no opposite connection
        return False

    
    def reverseMappingsSearch(self, dic, searchValue):
        for key, value in dic.items():
            if isinstance(searchValue, value):
                return key
        return False


    # Load the .json map data into a dictionary
    def loadMap(self):
        if isinstance(self.level, dict):
            self.map = self.level
        else:
            with open(self.level) as f:
                self.map = json.load(f)

        self.levelName = self.map["mapName"] # Get the name of the map
        self.width = self.map["width"]
        self.height = self.map["height"]


    # Add a node to the grid if the node is not already on the grid
    def addNode(self, connection, connectionType, currentNodes, direction):
        if connection[direction] not in currentNodes:
            clickManagers = [self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager()]
            n = None
            n = self.addStop(n, self.stopMappings, connectionType, connection[direction], clickManagers)
            n = self.addDestination(n, self.destinationMappings, connectionType, connection[direction], clickManagers)

            if n is None: #no stop was found at this node 
                n = Node(self.spriteRenderer, self.groups, connection[direction], connectionType, self.nodePositions[connection[direction]][0], self.nodePositions[connection[direction]][1], self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager())

            self.nodes.append(n)
            currentNodes.append(connection[direction])

        return currentNodes


    # Add a stop, instead of a node, to the grid 
    def addStop(self, n, mappings, connectionType, number, clickManagers = [], x = None, y = None):
        if x is None: x = self.nodePositions[number][0]
        if y is None: y = self.nodePositions[number][1]

        # Change if to a for to show all stops from other layers on each layer (i.e metro stations on layer 2, etc.)
        if connectionType in self.map["stops"]:
            for stop in self.map["stops"][connectionType]:
                if stop["location"] == number:
                    if len(clickManagers) <= 2:
                        n = mappings[stop["type"]](self.spriteRenderer, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1])
                    else:
                        n = mappings[stop["type"]](self.spriteRenderer, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1], clickManagers[2])
                    break
        return n


    def addDestination(self, n, mappings, connectionType, number, clickManagers = [], x = None, y = None):
        if x is None: x = self.nodePositions[number][0]
        if y is None: y = self.nodePositions[number][1]

        if connectionType in self.map["destinations"]:
            for destination in self.map["destinations"][connectionType]:
                if destination["location"] == number:
                    if len(clickManagers) <= 2:
                        n = mappings[destination["type"]](self.spriteRenderer, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1])
                    else:
                        n = mappings[destination["type"]](self.spriteRenderer, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1], clickManagers[2])
                    self.destinations.append(n)
                    break
        return n


    def replaceNode(self, connectionType, node, nodeType):
        number = node.getNumber()
        connections = node.getConnections() #need to transfer the connections from the old node to the new node                
        transports = node.getTransports()
        self.nodes.remove(node)
        node.remove()

        n = nodeType(self.spriteRenderer, self.groups, number, connectionType, self.nodePositions[number][0], self.nodePositions[number][1], self.spriteRenderer.getClickManager(), self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager())

        # Need to replace the connection with the new node, otherwise it cant be deleted
        for connection in self.connections:
            if connection.getFrom().getNumber() == n.getNumber():
                connection.setFromNode(n)
            elif connection.getTo().getNumber() == n.getNumber():
                connection.setToNode(n)        

        n.setConnections(connections)
        n.setTransports(transports)
        self.nodes.append(n)
        return n    


    # Create the grid by adding all the nodes and connections to the grid
    def createGrid(self, connectionType):
        currentNodes = []

        if connectionType in self.map["connections"]:
            for connection in self.map["connections"][connectionType]:
                # Add the nodes in the connection
                currentNodes = self.addNode(connection, connectionType, currentNodes, 0)
                currentNodes = self.addNode(connection, connectionType, currentNodes, 1)

                for node in self.nodes:
                    if node.getNumber() == connection[0]:
                        n1 = node
                    if node.getNumber() == connection[1]:
                        n2 = node

                # Create the connection with the nodes
                self.addConnections(connectionType, n1, n2)


    # Create a full grid with all the nodes populated and no connections (for the map editor)
    def createFullGrid(self, connectionType):
        clickManagers = [self.spriteRenderer.getClickManager(), self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager()]
        
        if self.level is None:
            for number, position in enumerate(self.nodePositions):
                n = EditorNode(self.spriteRenderer, self.groups, number, connectionType, position[0], position[1], clickManagers[0], clickManagers[1], clickManagers[2])
                self.nodes.append(n)
        else:
            # Loop through all the node positions
            for number, position in enumerate(self.nodePositions):
                n = None
                n = self.addStop(n, self.editorStopMappings, connectionType, number, clickManagers, position[0], position[1])
                n = self.addDestination(n, self.editorDestinationMappings, connectionType, number, clickManagers, position[0], position[1])

                if n is None:
                    n = EditorNode(self.spriteRenderer, self.groups, number, connectionType, position[0], position[1], clickManagers[0], clickManagers[1], clickManagers[2])
                self.nodes.append(n)

            if connectionType in self.map["connections"]:
                for connection in self.map["connections"][connectionType]:
                    for node in self.nodes:
                        if node.getNumber() == connection[0]:
                            n1 = node
                        if node.getNumber() == connection[1]:
                            n2 = node

                    self.addConnections(connectionType, n1, n2)


    # Load the transportation to the grid on a specified connection 
    def loadTransport(self, connectionType, running = True):
        if len(self.connections) <= 0 or connectionType not in self.map["transport"]:
            return 

        # For each transportation in the map
        for transport in self.map["transport"][connectionType]:      
            possibleConnections = []

            # for each connection, find the connection of the transportation
            for connection in self.connections:
                # Ensure it is on the right connection going in the right direction
                if connection.getFrom().getNumber() == transport["location"]:
                    possibleConnections.append(connection)

            # pick a random connection to change the direction
            if len(possibleConnections) > 0:
                connection = possibleConnections[random.randint(0, len(possibleConnections) - 1)]
                t = self.transportMappings[transport["type"]](self.spriteRenderer, self.groups, connection, running, self.spriteRenderer.getTransportClickManager(), self.spriteRenderer.getPersonClickManager())
                self.transports.append(t)


    # Add a transport to the map within the map editor
    def addTransport(self, connectionType, connection, transport, running = True):
        t = transport(self.spriteRenderer, self.groups, connection, running, self.spriteRenderer.getTransportClickManager(), self.spriteRenderer.getPersonClickManager())
        self.transports.append(t)


    # Remove a transport from the map within the map editor 
    def removeTransport(self, transport):
        self.transports.remove(transport)
        transport.remove()

           
    @staticmethod
    def getMapValues(width, height, reverse = False):
        mapValues = {}
        nodes = 0
        for x in range(0, width):
            for y in range(0, height):
                if reverse:
                    mapValues[(x, y)] = nodes
                else:
                    mapValues[nodes] = (x, y)
                nodes += 1
        return mapValues