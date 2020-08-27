#!/usr/bin/env python
import sys
import math
import os
import time
import copy
import numpy as np
from PyQt5 import QtGui, QtCore
from PyQt5 import QtWidgets
import random



def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))

def getPointAvg(lst):
    # Gathers the center of every point in `lst` and returns the average
    # Used to get the exact center of a creature with many different cells
    nList = np.array([[i.x(), i.y()] for i in lst])
    nList = sum(nList) / len(nList)
    return QtCore.QPointF(nList[0], nList[1])

def posList(lst):
    lst2 = []
    for i in lst:
        if (i < 0):
            lst2.append(-i)
        else:
            lst2.append(i)
    return lst2

def condition(listVar, multiplier=1):
    lst2 = []

    for i in listVar:
        i = float(i)
        isneg = False
        if (i < 0):
            isneg = True; i = -i
        i = (i / sum(posList(listVar))*multiplier)
        if (isneg): i = -i
        lst2.append(i)

    return lst2

def cellDirection(cellA, cellB, invert=False):
    if invert:
        direction = [ (cellA.getCenter().x()-cellB.getCenter().x()), (cellA.getCenter().y()-cellB.getCenter().y()) ]
    else:
        direction = [ (cellB.getCenter().x()-cellA.getCenter().x()), (cellB.getCenter().y()-cellA.getCenter().y()) ]
    direction = condition(direction)
    return direction

def randomDirection(multiplier=1):
    return condition([random.random()-random.random(), random.random()-random.random()], multiplier=multiplier)

def calculateDistance(x1,y1,x2,y2):
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return dist

def cellDistance(cell1, cell2):
    x1 = cell1.getPos().x()
    y1 = cell1.getPos().y()
    x2 = cell2.getPos().x()
    y2 = cell2.getPos().y()
    return calculateDistance(x1, y1, x2, y2)



class Sprite(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pos, width, height, image=None, parent=None, collisionInt=.5):
        # "pos" should be a QtCore.QPointF class

        self.parent = parent   # Look at self.setParentItem(<item>)
        super(Sprite, self).__init__(parent)

        if image:
            self.pixmap = QtGui.QPixmap(image)
            self.setPixmap( self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio) )
        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsSelectable)
        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)

        self.collisionInt = float(collisionInt)   # The interval at which to wait before calling "self.collision" again
        self.lastCollision = time.time() - self.collisionInt
        self.lastItemsList = []   # The last list of collision items this object collided with to help keep track of collisions
        # `self.collision` is called with ( self, [<itemsList>] )
        # "[<itemsList>]" is a list of all items this sprite is colliding with

        self.limitedBoundary = True   # If set to True, this sprite will bounce off the edges of the scene

        #self.setPos(self.xPos, self.yPos)
        self.setPos(pos[0], pos[1])

        self.lastUpdated = time.time()

        self.movDirection = [1.0, 1.0]
        self.movSpeed = 0.0
        self.friction = 8.0   # The percentage of movement speed to subtract per second
        # If set to 0, the sprite will not slow down
        self.frictionCutOff = 0.01   # If the movement speed falls below this, it will be set to 0.0 just to help keep things simple

        self.mouseHoverFunc = None   # Executes with (self, event)
        self.mouseReleaseFunc = None   # Executes with (self, event)
        self.mousePressFunc = None   # Executes with (self, event)

    def mousePressEvent(self, event):
        if self.mousePressFunc != None:
            self.mousePressFunc(self, event)
    def mouseReleaseEvent(self, event):
        if self.mouseReleaseFunc != None:
            self.mouseReleaseFunc(self, event)
    def hoverEnterEvent(self, event):
        if self.mouseHoverFunc != None:
            self.mouseHoverFunc(self, event)

    def scale(self, width, height):
        tempPixmap = self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio)
        self.setPixmap( tempPixmap )

    def getPos(self):
        return self.pos()

    def getCollisions(self):
        return self.collidingItems()

    def getCenter(self):
        childrenList = self.childItems()
        if not childrenList:
            return self.sceneBoundingRect().center()
        aList = [i.sceneBoundingRect().center() for i in childrenList]
        return getPointAvg(aList)
    def getRect(self):
        return self.sceneBoundingRect()

    def getWidth(self):
        return self.getRect().width()
    def getHeight(self):
        return self.getRect().height()

    def direct(self, direction, invert=False):   # Set "invert" to True if you want the sprite to move away from the target
        if invert:
            self.movDirection = [ (self.getCenter().x()-direction.x()), (self.getCenter().y()-direction.y()) ]
        else:
            self.movDirection = [ (direction.x()-self.getCenter().x()), (direction.y()-self.getCenter().y()) ]
        self.movDirection = condition(self.movDirection)
        print("Direction:  {}, {}".format( direction.x(), direction.y() ))
        print("Position:   {}, {}".format( self.x(), self.y() ))
        print("Movement:   {}".format( self.movDirection ))

    def bump(self, direction, speed, invert=False):
        # Set "invert" to True if you want the sprite to move away from the target
        self.direct(direction, invert=invert)
        self.movSpeed = speed
        print("Sprite bumped!")

    def collision(self, items):
        pass

    def updateSprite(self):
        uDiff = time.time() - self.lastUpdated
        self.movSpeed -= perc2num(self.friction, self.movSpeed)

        if self.movSpeed <= self.frictionCutOff: self.movSpeed = 0.0

        xPos = self.x() + (self.movSpeed * uDiff * self.movDirection[0])
        yPos = self.y() + (self.movSpeed * uDiff * self.movDirection[1])

        if self.limitedBoundary:
            if self.getRect().left() < 0:   # Too far left
                self.xPos = 0
                if self.movDirection[0] < 0: self.movDirection[0] = -self.movDirection[0]
            if self.getRect().right() > self.scene().sceneRect().width():   # Too far right
                self.xPos = self.scene().sceneRect().width() - self.getRect().width()
                if self.movDirection[0] > 0: self.movDirection[0] = -self.movDirection[0]
            if self.getRect().top() < 0:   # Too far up
                self.yPos = 0
                if self.movDirection[1] < 0: self.movDirection[1] = -self.movDirection[1]
            if self.getRect().bottom() > self.scene().sceneRect().height():   # Too far down
                self.yPos = self.scene().sceneRect().height() - self.getRect().height()
                if self.movDirection[1] > 0: self.movDirection[1] = -self.movDirection[1]


        self.setPos(xPos, yPos)

        hit = False
        preCol = self.getCollisions()
        collisions = []
        for i in preCol:
            if i.parent != self.parent:
                if self.parent and i.parent:
                    collisions.append(i)
        if self.lastItemsList == collisions and len(collisions) > 0 and time.time()-self.lastCollision >= self.collisionInt:
            hit = True
        elif collisions != self.lastItemsList and len(collisions) > 0:
            hit = True
        if hit:
            self.collision(collisions)
            self.lastCollision = time.time()
            self.lastItemsList = collisions

        self.update()

        self.lastUpdated = time.time()



class DNA():
    def __init__(self):
        self.cells = {}
        # Structure: { <cell_id>: {"type": "eye", "size": 25, "xy": [<x_pos>, <y_pos>]} }

        self.connections = {}
        # Structure: { <cell_id>: [<cell_id1>, <cell_id2>] }

        self.types = ["eye", "barrier", "carniv", "co2c", "nose", "push", "scent"]

    def copy(self):
        return copy.deepcopy(self)

    def mutate(self, magnitude):
        # `magnitude` : 0.0 - 1.0
        pass

    def randomize(self, sizeRange=[5,40], connection_range=[0, 2], xy_range=[0,42]):
        size = random.randrange(sizeRange[0], sizeRange[1])
        print("Size: {}".format(size))

        for i in range(size):
            x_pos = random.randrange(xy_range[0], xy_range[1])
            y_pos = random.randrange(xy_range[0], xy_range[1])
            self.cells[i] = {
                             "type": random.choice(self.types),
                             "size": random.randrange(15, 30),
                             "xy": [x_pos, y_pos]
                             }

        for cid in self.cells:
            self.connections[cid] = []

        #connected_id = random.choice([i for i in self.cells if i != self.cells[0]])
        #self.connections[0].append(connected_id)
        for cid in self.cells:
            for i in range( random.randrange(connection_range[0], connection_range[1]) ):
                if len(self.cells) > 1:
                    connected_id = random.choice([i for i in self.cells if i != cid])
                    self.connections[cid].append(connected_id)

        return self


class Cell(Sprite):
    def __init__(self, *args, **kwargs):
        super(Cell, self).__init__(*args, **kwargs)
        self.connections = []
        self.type = "co2c"
        self.typeImages = {
                           "barrier": "Images/barrier.png",
                           "carniv": "Images/carniv.png",
                           "co2c": "Images/co2C.png",
                           "eye": "Images/eye.png",
                           "health": "Images/health.png",
                           "neuron": "Images/neuron.png",
                           "nose": "Images/nose.png",
                           "push": "Images/push.png",
                           "scent": "Images/scent.png"
                           }

    def setType(self, type):
        if not type in self.typeImages:
            return
        self.type = type

        self.pixmap = QtGui.QPixmap(self.typeImages[type])
        self.setPixmap( self.pixmap.scaled(self.getWidth(), self.getHeight(), QtCore.Qt.KeepAspectRatio) )

        return self

    def collision(self, items):
        print("COLLISION: {}".format(items))


class Creature(Sprite):
    def __init__(self, *args, **kwargs):
        super(Creature, self).__init__(*args, **kwargs)

        self.cells = {}

        self.dna = DNA().randomize(sizeRange=[5,12])

        self.buildCells()

    def buildCells(self):
        for cid in self.dna.cells:
            cell_info = self.dna.cells[cid]
            xy = cell_info["xy"]
            newCell = Cell(xy, cell_info["size"], cell_info["size"], image="Images/neuron.png", parent=self)
            newCell.setType(cell_info["type"])
            self.cells[cid] = newCell
        for cid in self.cells:
            for connected_id in self.dna.connections:
                connected_cell = self.cells[connected_id]
                self.cells[cid].connections.append(connected_cell)

    def replicate(self, cell, direction):
        newX = cell.getPos().x() + direction[0]
        newY = cell.getPos().y() + direction[1]

        newCell = Cell([newX, newY], 20, 20, image="Images/neuron.png", parent=self)
        self.cells.append(newCell)
        return newCell

    def connected(self, cell1, cell2):
        if cell2 in cell1.connections or cell1 in cell2.connections:
            return True
        return False

    def updateCellDistances(self):
        for cell_id in self.cells:
            cell = self.cells[cell_id]

            touchingCells = [self.cells[c] for c in self.cells if cellDistance(cell, self.cells[c]) <= cell.getWidth()/2+self.cells[c].getWidth()/2]
            if cell in touchingCells:
                touchingCells.remove(cell)
            touchingCells = sorted(touchingCells, key=lambda a: random.random())

            for c in touchingCells:
                distance = cellDistance(cell, c)
                mult = 2
                if self.connected(cell, c):
                    mult = 3
                if distance < cell.getWidth()/mult + c.getWidth()/mult:
                    movDir = cellDirection(cell, c, invert=True)
                    cell.setPos( cell.getPos().x() + movDir[0], cell.getPos().y() + movDir[1] )

            connected_cells = [c for c in cell.connections]

            for c in connected_cells:
                distance = cellDistance(cell, c)
                if distance > cell.getWidth()/2.5 + c.getWidth()/2.5:
                    movDir = cellDirection(cell, c, invert=True)
                    cell.setPos( cell.getPos().x() - movDir[0], cell.getPos().y() - movDir[1] )

    def updateCells(self, scene):
        self.updateCellDistances()
        for cid in self.cells:
            self.cells[cid].updateSprite()
