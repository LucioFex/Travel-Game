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
        self.transports = []
        self.destinations = []
        self.entrances = []

        self.nodePositions = GridManager.setNodePositions(spacing[0], spacing[1])

        # Entry nodes
        self.entryTopPositions = GridManager.setNodePositions(1.5, -0.5, 18, 1)
        self.entryBottomPositions = GridManager.setNodePositions(1.5, 11.5, 18, 1)


        if self.level is not None:
            self.loadMap()

        self.transportMappings = {"metro": Metro, "bus": Bus, "tram": Tram, "taxi": Taxi}
        self.stopMappings = {"metro": MetroStation, "bus": BusStop, "tram": TramStop}
        self.editorStopMappings = {"metro": EditorMetroStation, "bus": EditorBusStop, "tram": EditorTramStop}
        self.destinationMappings = {"airport": Airport, "office": Office}
        self.editorDestinationMappings = {"airport": EditorAirport, "office": EditorOffice}
        self.entranceMappings = {"top": self.entryTopPositions, "bottom": self.entryBottomPositions}


    #### Getters ####

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


    # Return the transportations, in a list for each layer
    def getTransports(self):
        return self.transports


    def getDestinations(self):
        return self.destinations


    def getEntrances(self):
        return self.entrances


    def getMap(self):
        return self.map
        


    #### Setters ####

    #generate an 18 * 10 board of possible node positions (x and y locations) for nodes to be added to
    @staticmethod
    def setNodePositions(offx = 1.5, offy = 1.5, width = 18, height = 10):
        # Offset on the x coordinate
        # Offset on the y coordinate
        spacing = 50 #spacing between each node
        positions = []

        for i in range(width):
            for x in range(height):
                positions.append(((i + offx) * spacing, (x + offy) * spacing))
        return positions


    def addConnections(self, connectionType, A, B):
        c1 = Connection(self.game, connectionType, A, B, Connection.Direction.FORWARDS) 
        c2 = Connection(self.game, connectionType, B, A, Connection.Direction.BACKWARDS) 
        self.connections.append(c1) #forwards
        self.connections.append(c2) #backwards

        return c1, c2


    def removeConnections(self, connections = []):
        for connection in connections:
            self.connections.remove(connection)


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


    # Add a node to the grid if the node is not already on the grid
    def addNode(self, connection, connectionType, currentNodes, direction):
        if connection[direction] not in currentNodes:
            clickManagers = [self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager()]
            n = None
            n = self.addStop(n, self.stopMappings, connectionType, connection[direction], clickManagers)
            n = self.addDestination(n, self.destinationMappings, connectionType, connection[direction], clickManagers)

            if n is None: #no stop was found at this node 
                n = Node(self.game, self.groups, connection[direction], connectionType, self.nodePositions[connection[direction]][0], self.nodePositions[connection[direction]][1], self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager())

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
                        n = mappings[stop["type"]](self.game, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1])
                    else:
                        n = mappings[stop["type"]](self.game, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1], clickManagers[2])
                    break
        return n


    def addDestination(self, n, mappings, connectionType, number, clickManagers = [], x = None, y = None):
        if x is None: x = self.nodePositions[number][0]
        if y is None: y = self.nodePositions[number][1]

        if connectionType in self.map["destinations"]:
            for destination in self.map["destinations"][connectionType]:
                if destination["location"] == number:
                    if len(clickManagers) <= 2:
                        n = mappings[destination["type"]](self.game, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1])
                    else:
                        n = mappings[destination["type"]](self.game, self.groups, number, connectionType, x, y, clickManagers[0], clickManagers[1], clickManagers[2])
                    self.destinations.append(n)
                    break
        return n


    def replaceNode(self, connectionType, node, nodeType):
        number = node.getNumber()
        connections = node.getConnections() #need to transfer the connections from the old node to the new node                
        transports = node.getTransports()
        self.nodes.remove(node)
        node.remove()

        n = nodeType(self.game, self.groups, number, connectionType, self.nodePositions[number][0], self.nodePositions[number][1], self.spriteRenderer.getClickManager(), self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager())

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
        
        # Only add entrances if they exist
        if "entrances" in self.map.keys():
            if connectionType in self.map["entrances"]:
                for entrance in self.map["entrances"][connectionType]:
                    index = int(entrance["location"] / 10)
                    n = EntranceNode(self.game, self.groups, -(index + 1), connectionType, self.entranceMappings[entrance["type"]][index][0], self.entranceMappings[entrance["type"]][index][1], self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager())
                    self.entrances.append(n)

                    for node in self.nodes:
                        if node.getNumber() == entrance["location"]:
                            n1 = node


                    self.addConnections(connectionType, n, n1)


    # Create a full grid with all the nodes populated and no connections (for the map editor)
    def createFullGrid(self, connectionType):
        clickManagers = [self.spriteRenderer.getClickManager(), self.spriteRenderer.getPersonClickManager(), self.spriteRenderer.getTransportClickManager()]
        
        if self.level is None:
            for number, position in enumerate(self.nodePositions):
                n = EditorNode(self.game, self.groups, number, connectionType, position[0], position[1], clickManagers[0], clickManagers[1], clickManagers[2])
                self.nodes.append(n)
        else:
            # Loop through all the node positions
            for number, position in enumerate(self.nodePositions):
                n = None
                n = self.addStop(n, self.editorStopMappings, connectionType, number, clickManagers, position[0], position[1])
                n = self.addDestination(n, self.editorDestinationMappings, connectionType, number, clickManagers, position[0], position[1])

                if n is None:
                    n = EditorNode(self.game, self.groups, number, connectionType, position[0], position[1], clickManagers[0], clickManagers[1], clickManagers[2])
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
            direction = random.randint(0, 1)
            
            # for each connection, find the connection of the transportation
            for connection in self.connections:
                # Ensure it is on the right connection going in the right direction
                if connection.getFrom().getNumber() == transport["location"]:
                    # If the connection is the same as the direction, or its an end node (so theres only one direction)
                    if connection.getDirection().value == direction or len(connection.getFrom().getConnections()) <= 1:
                        t = self.transportMappings[transport["type"]](self.game, self.groups, connection, connection.getDirection(), running, self.spriteRenderer.getTransportClickManager())
                        self.transports.append(t)
                        # t.addToPath(connection.getTo())
                        # t.addToPath(connection.getTo().getConnections()[0].getTo())
                        break


    # Add a transport to the map within the map editor
    def addTransport(self, connectionType, connection, transport, running = True):
        t = transport(self.game, self.groups, connection, connection.getDirection(), running, self.spriteRenderer.getTransportClickManager())
        self.transports.append(t)


    # Remove a transport from the map within the map editor 
    def removeTransport(self, transport):
        self.transports.remove(transport)
        transport.remove()

        
           