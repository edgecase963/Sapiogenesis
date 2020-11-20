#!/usr/bin/env python
from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
import time
import sys
import math
import random
import numpy as np
import pymunk
import json
from pymunk import Vec2d



try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)



def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))

def reverseAngle(angle):
    # Reverses an angle (degrees)
    newAngle = angle + 180
    if newAngle > 360:
        newAngle -= 360
    return newAngle

def getPointAvg(lst):
    # Gathers the center of every point in `lst` and returns the average
    # Used to get the exact center of a an object with many sprites in it
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
    try:
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
    except ZeroDivisionError:
        return [0,0]

def getDirection(x1, y1, x2, y2, invert=False):
    if invert:
        direction = [ (x1-x2), (y1-y2) ]
    else:
        direction = [ (x2-x1), (y2-y1) ]
    direction = condition(direction)
    return direction

def spriteDirection(sprite1, sprite2, invert=False):
    direction = getDirection(
        sprite1.getCenter().x(),
        sprite1.getCenter().y(),
        sprite2.getCenter().x(),
        sprite2.getCenter().y(),
        invert=invert
    )
    return direction

def randomDirection(multiplier=1):
    return condition([random.random()-random.random(), random.random()-random.random()], multiplier=multiplier)

def calculateDistance(x1,y1,x2,y2):
    dist = math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )
    return dist

def spriteDistance(sprite1, sprite2):
    x1 = sprite1.getCenter().x()
    y1 = sprite1.getCenter().y()
    x2 = sprite2.getCenter().x()
    y2 = sprite2.getCenter().y()
    return calculateDistance(x1, y1, x2, y2)

def makeCircle(radius, friction=.3, elasticity=.5, mass=10):
    inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))

    body = pymunk.Body(mass, inertia)

    shape = pymunk.Circle(body, radius, Vec2d(0,0))
    shape.friction = friction
    shape.elasticity = elasticity
    shape.sprite = None

    return body, shape



class Sprite(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pos, width, height, environment, body, shape,
                 image=None, parent=None):
        # "pos" should be a QtCore.QPointF class

        self.parent = parent   # Look at self.setParentItem(<item>)
        super(Sprite, self).__init__(parent)

        self.connections = {}
        # Structure: {<sprite>: <angle>}
        # Angle is in degrees

        self.environment = environment

        if image:
            self.pixmap = QtGui.QPixmap(image)
            self.setPixmap( self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio) )

        self.setTransformOriginPoint(width/2, height/2)

        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsSelectable)
        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsMovable)
        self.setEnabled(True)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        self.setAcceptedMouseButtons(QtCore.Qt.AllButtons)

        self.limitedBoundary = True   # If set to True, this sprite will bounce off the edges of the scene

        # Pymunk
        #--

        self.radius = width/2

        self.body = body
        #self.body.position = [i + self.radius for i in pos]
        self.body.position = pos

        self.shape = shape
        self.shape.sprite = self

        #--

        self.connections = {}
        # Structure: {<Sprite>: <pymunk.PinJoint>}


        #self.setPos(self.xPos, self.yPos)
        #self.setPos(pos[0], pos[1])
        self.setPos(pos[0]-self.radius, pos[1]-self.radius)

        self.lastUpdated = time.time()

        #self.mouseHoverFunc = None   # Executes with (self, event)
        #self.mouseReleaseFunc = None   # Executes with (self, event)
        #self.mousePressFunc = None   # Executes with (self, event)
        self.mouseDoubleClickFunc = None # Executes with (self, event)

    def mouseDoubleClickEvent(self, event):
        pass

    def scale(self, width, height):
        tempPixmap = self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio)
        self.setPixmap( tempPixmap )

    def getCenter(self):
        childrenList = self.childItems()
        if not childrenList:
            return self.sceneBoundingRect().center()
        aList = [i.sceneBoundingRect().center() for i in childrenList]
        return getPointAvg(aList)
    def getRect(self):
        return self.sceneBoundingRect()

    def getPos(self):
        return [self.body.position[0], self.body.position[1]]

    def getWidth(self):
        return self.getRect().width()
    def getHeight(self):
        return self.getRect().height()

    def bump(self, direction, speed, invert=False):
        # Set "invert" to True if you want the sprite to move away from the target
        newVel = getDirection(self.body.position[0], self.body.position[1], direction[0], direction[1])
        newVel = [i*speed for i in newVel]
        if invert:
            newVel = [-i for i in newVel]
        self.body.velocity = Vec2d(newVel)

    def collision(self, item):
        pass

    def connectTo(self, sprite, rigid=True):
        if sprite in self.connections:
            return
        #joint = pymunk.DampedSpring(self.body, sprite.body, (0,0), (0,0), 2, 150, 20)
        if rigid:
            joint = pymunk.PinJoint(self.body, sprite.body, [0,0], [0,0])
        else:
            pass
            #joint = pymunk.DampedSpring(self.body, sprite.body, (0,0), (0,0), 2, 150, 20)
        # angle is in degrees
        #direction = getDirection(self.getCenter().x(), self.getCenter().y(), sprite.getCenter().x(), sprite.getCenter().y())

        #point1 = (direction[0]*self.radius, direction[1]*self.radius)
        #point2 = (-direction[0]*self.radius, -direction[1]*self.radius)

        #joint = pymunk.PinJoint(self.body, sprite.body, point1, point2)

        self.body.space.add(joint)
        self.connections[sprite] = joint
        sprite.connections[self] = joint

    def disconnectFrom(self, sprite):
        if sprite in self.connections:
            joint = self.connections[sprite]
            self.connections.pop(sprite)
            sprite.connections.pop(self)
            self.body.space.remove(joint)

    def updateSprite(self):
        uDiff = time.time() - self.lastUpdated

        self.setPos(self.body.position[0]-self.radius, self.body.position[1]-self.radius)

        frictionCutX = perc2num(self.environment.friction, self.body.velocity[0])
        frictionCutY = perc2num(self.environment.friction, self.body.velocity[1])
        frictionCutA = perc2num(self.environment.friction, self.body.angular_velocity)

        frictionCutX *= uDiff
        frictionCutY *= uDiff
        frictionCutA *= uDiff

        newVel = list(self.body.velocity)
        newVel = [newVel[0]-frictionCutX, newVel[1]-frictionCutY]

        self.body.velocity = Vec2d(newVel)

        self.body.angular_velocity -= frictionCutA

        angle = math.degrees(self.body.angle)

        self.setRotation(angle)

        self.update()
        self.lastUpdated = time.time()



class Environment():
    def __init__(self, worldView, scene, width, height, friction=60.0, gravity=(0, 0), frameWidth=10.0):
        self.worldView = worldView
        self.scene = scene
        self.friction = friction   # The percentage of movement speed to subtract per second
        # If set to 0, the sprite will not slow down
        self.sprites = []
        # A list containing all sprites in this environment
        self.space = pymunk.Space()
        self.space.gravity = gravity

        self.info = {
            "startTime": time.time(),
            "co2": 30000,
            "oxygen": 0,
            "selected": None,
            "lastPosition": [0,0],
            "organism_list": [],
            "copied": None,
            "mutation_severity": 0.5,
            "brain_mutation_severity": 0.5,
            "reproduction_limit": 6,
            "population": 0,
            "population_limit": 50,
            "weight_persistence": True,
            "learning_rate": 0.02,
            "use_rnn": True,
            "paused": False,
            "paused_time": time.time()
        }

        self.width = width
        self.height = height

        with open("environment_settings.json", "r") as f:
            env_settings = json.load(f)

        self.worldSpeed = .06
        self.updateSpeed = env_settings["update_speed"]

        ch = self.space.add_collision_handler(0, 0)
        ch.post_solve = self.collision

        static_body = self.space.static_body

        top_right_corner = (width - frameWidth, frameWidth)
        top_left_corner = (frameWidth, frameWidth)
        bottom_right_corner = (width - frameWidth, height - frameWidth)
        bottom_left_corner = (frameWidth, height - frameWidth)

        static_lines = [
                        pymunk.Segment(static_body, top_left_corner, bottom_left_corner, frameWidth), # left wall
                        pymunk.Segment(static_body, bottom_left_corner, bottom_right_corner, frameWidth), # bottom wall
                        pymunk.Segment(static_body, top_right_corner, bottom_right_corner, frameWidth), # right wall
                        pymunk.Segment(static_body, top_left_corner, top_right_corner, frameWidth) # top wall
                        ]

        for line in static_lines:
            line.elasticity = 0.95
            line.friction = 0.9
        self.space.add(static_lines)

        self.scene.mouseReleaseEvent = self.worldMouseReleaseEvent
        self.scene.mousePressEvent = self.worldMousePressEvent

        # Setup timer
        #--
        self.worldView.timer = QtCore.QBasicTimer()

        self.worldView.timerEvent = self.update

        self.worldView.timer.start(self.updateSpeed, self.worldView)
        #--

        self.scene.keyPressEvent = self.keyPressEvent
        self.scene.keyReleaseEvent = self.keyReleaseEvent

        self.mousePressFunc = None
        self.mouseReleaseFunc = None
        # These both execute with ( [x, y] )

    def sprite_under_mouse(self):
        for sprite in self.sprites:
            if sprite.isUnderMouse():
                return sprite

    def keyPressEvent(self, event):
        pass

    def keyReleaseEvent(self, event):
        pass

    def collision(self, arbiter, space, data):
        shape1, shape2 = arbiter._get_shapes()
        if not isinstance(shape1, pymunk.Segment) and not isinstance(shape2, pymunk.Segment):
            sprite1 = shape1.sprite
            sprite2 = shape2.sprite

            sprite1.collision(sprite2)
            sprite2.collision(sprite1)

    def worldMouseReleaseEvent(self, event):
        if self.mouseReleaseFunc:
            pos = event.lastScenePos()
            x = pos.x()
            y = pos.y()
            self.mouseReleaseFunc(event, [x, y])

    def worldMousePressEvent(self, event):
        if self.mousePressFunc:
            pos = event.lastScenePos()
            x = pos.x()
            y = pos.y()
            self.mousePressFunc(event, [x, y])

    def preUpdateEvent(self):
        # Can be assigned so that another chunk of code is processed before the environment updates
        pass

    def postUpdateEvent(self):
        # Can be assigned so that another chunk of code is processed after the environment updates
        pass

    def update(self, event):
        if self.info["paused"]:
            self.space.step(0.0)
            self.postUpdateEvent()
            return
        self.preUpdateEvent()
        self.space.step(self.worldSpeed)
        for sprite in self.sprites:
            sprite.updateSprite()
        self.scene.update( self.scene.sceneRect() )
        self.postUpdateEvent()

    def removeSprite(self, sprite):
        if not sprite in self.sprites:
            return
        for sp in sprite.connections.copy():
            sprite.disconnectFrom(sp)
        self.space.remove(sprite.body, sprite.shape)
        self.scene.removeItem(sprite)
        self.sprites.remove(sprite)

    def add_sprite(self, sprite):
        self.scene.addItem(sprite)
        self.sprites.append(sprite)
        self.space.add(sprite.body, sprite.shape)

    def add_ball_sprite(self, xy, width, height, mass=10, friction=.3, elasticity=.5, image=None, parent=None):
        body, shape = makeCircle(width/2, friction=friction, elasticity=elasticity, mass=mass)
        newSprite = Sprite(xy, width, height, self, body, shape, image=image, parent=parent)
        self.scene.addItem(newSprite)
        self.sprites.append(newSprite)
        self.space.add(newSprite.body, newSprite.shape)
        return newSprite



def setupEnvironment(worldView, scene, friction=60.0, gravity=(0, 0)):
    # worldView should be a `QGraphicsView` item
    # scene should be a `QGraphicsScene` item
    sceneRect = scene.sceneRect()
    environment = Environment(worldView, scene, sceneRect.width(), sceneRect.height(), friction=friction, gravity=gravity)
    return environment



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        self.width = 1050
        self.height = 1200
        MainWindow.resize(1100, 650)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))

        self.worldView = QtWidgets.QGraphicsView(self.centralwidget)

        self.worldView.setGeometry(QtCore.QRect(15, 20, 1070, 600))
        self.worldView.setObjectName(_fromUtf8("worldView"))

        self.timeline = QtCore.QTimeLine(1000)
        self.timeline.setFrameRange(0, 100)

        self.scene = QtWidgets.QGraphicsScene(self.worldView)

        self.scene.setSceneRect(0, 0, 1050, 1200)
        self.worldView.setScene(self.scene)

        self.worldView.setBackgroundBrush( QtGui.QBrush( QtGui.QColor(180,180,255) ) )

        MainWindow.setCentralWidget(self.centralwidget)



if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)

        env = setupEnvironment(myapp.worldView, myapp.scene)
        # QGraphicsView, QGraphicsScene

        sprite1 = env.add_ball_sprite([300,300], 40, 40, image="dot.png")
        sprite2 = env.add_ball_sprite([322,322], 40, 40, image="dot.png")

        sprite1.connectTo(sprite2)

        #sprite3 = env.add_ball_sprite([480,480], 20, 20, image="dot.png")
        #sprite4 = env.add_ball_sprite([400,460], 20, 20, image="dot.png")

        for i in range(80):
            size = random.randrange(10, 50)
            pos = [random.randrange(50, 1000), random.randrange(50, 1000)]
            sprite = env.add_ball_sprite(pos, size, size, image="dot.png")

        window.show()
        sys.exit(app.exec_())
