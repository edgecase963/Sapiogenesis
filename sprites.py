#!/usr/bin/env python
import sys
import os
import time
import numpy as np
from PyQt5 import QtGui, QtCore
from PyQt5 import QtWidgets



def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))

def getPointAvg(lst):
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

def condition(listVar):
    lst2 = []

    for i in listVar:
        i = float(i)
        isneg = False
        if (i < 0):
            isneg = True; i = -i
        i = (i / sum(posList(listVar)))
        if (isneg): i = -i
        lst2.append(i)

    return lst2



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
        collisions = self.getCollisions()
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



class Cell(Sprite):
    def __init__(self, *args, **kwargs):
        super(Cell, self).__init__(*args, **kwargs)
        print("Cell Pos: {}".format(self.getPos()))

    def collision(self, items):
        print("COLLISION: {}".format(items))


class Creature(Sprite):
    def __init__(self, *args, **kwargs):
        super(Creature, self).__init__(*args, **kwargs)

        xy = [0, 0]
        for i in range(1):
            cell = Cell(xy, 100, 100, image="Images/neuron.png", parent=self)
            xy[0] += 20
