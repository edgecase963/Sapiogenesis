import time
import sys
import random
import networks
import math
import numpy
import copy
import pymunk

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from userInterface import Ui_MainWindow
from threading import Thread
from pymunk import Vec2d
from torch import tensor
import neural
import physics



cell_types = ["barrier", "carniv", "eye", "olfactory", "co2C", "push", "pheremone", "body", "rotate"]
dead_image = "dead.png"
dirType = "/"

if sys.platform.startswith("win"):
    dirType = "\\"

#co2_dispersion_ratio = 20
# The dispersion ratio for dead cells.
# This is used to calculate how much CO2 is added back into the environment when a dead cell is dispersed
# Dispersion equation: <dispersion_ratio> * (<cell_size> / 2) * (<cell_mass> / 2)

co2_conversion_ratio = 12 # The amount of energy generated from 1 CO2 particle

cell_dispersion_rate = 6 # The percentage of a dead cell's mass to disperse per second

reproduction_limit = 6 # The amount of time (in seconds) an organism has to wait before reproducing again

offspring_amount = 1 # How many offspring to create when an organism reproduces

heal_rate = 3 # The percentage of health to heal each second if the cell has enough energy

mass_cutoff = 1 # If a dead cell's mass becomes less than this, it will be removed (dispersed completely)

break_damage = 5 # The amount of damage a cell does to its parent when it dies (break off from body) - multiplied by its size

starvation_rate = 200 # The amount of damage to do to a cell each second if its energy equals 0

neural_update_delay = .3 # How long to wait before activating an organism's brain - helps reduce lag

learning_update_delay = .5 # How long to wait before training an organism

training_epochs = 1 # How many epochs to train a network for per training interval

max_push_speed = 250
max_rotation_speed = 6 # Radians per second

training_dopamine_threshold = 1.

age_limit = 200

eyesight_multiplier = 8 # This multiplied by an eye cell's size is how far away that eye can see

base_cell_info = {
    "health": {
        # This is multiplied by the size and mass of each given cell
        # <max_health> = <base_health> * <cell_size> * <cell_mass>
        "barrier": 60,
        "carniv": 15,
        "co2C": 8,
        "eye": 5,
        "olfactory": 12,
        "push": 12,
        "pheremone": 12,
        "body": 12,
        "heart": 6,
        "rotate": 12
    },
    "energy_usage": {
        # The first variable in the lists below represent an idle cell
        # The second variable reprents a cell's energy intake while in use
        # This is multiplied by the size and mass of each given cell
        # <max_energy_usage> = <base_energy_usage> * (<cell_size> / 2) * (<cell_mass> / 2)
        "barrier": [2, 2],
        "carniv": [5, 8],
        "co2C": [6, 6],
        "eye": [5, 5],
        "olfactory": [6, 8],
        "push": [5, 8],
        "pheremone": [6, 8],
        "body": [2, 2],
        "heart": [5, 5],
        "rotate": [5, 8]
    },
    "energy_storage": {
        # This is multiplied by the size and mass of each given cell
        # <energy_storage> = <base_energy_storage> * <cell_size> * <cell_mass>
        "barrier": 10,
        "carniv": 18,
        "co2C": 20,
        "eye": 18,
        "olfactory": 18,
        "push": 20,
        "pheremone": 18,
        "body": 18,
        "heart": 20,
        "rotate": 18
    },
    "damage": {
        # The damage each cell does when in contact with a cell from another organism
        "barrier": 0,
        "carniv": 90,
        "co2C": 0,
        "eye": 0,
        "olfactory": 0,
        "push": 0,
        "pheremone": 0,
        "body": 0,
        "heart": 0,
        "rotate": 0
    }
}


def random_direction():
    deg = random.randrange(0, 360)
    rad = math.radians(deg)
    x_direction = math.cos(rad)
    y_direction = math.sin(rad)
    return [x_direction, y_direction]

def calculateDistance(x1,y1,x2,y2):
    return math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )

def positive(x):
    if x > 0:
        return x
    return -x

def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))

def getAngle(x1, y1, x2, y2):
    myradians = math.atan2(y2-y1, x2-x1)
    return myradians

def getDirection(angle):
    direction = [math.cos(angle), math.sin(angle)]
    return direction

def randomizeList(l):
    return sorted(l, key=lambda x: random.random())

def viable_organism_position(pos, dna, environment):
    orgList = environment.info["organism_list"]
    dead_cells = [sprite for sprite in environment.sprites if not sprite.alive]
    overlappingSprites = []

    dna_rect = dna.get_rect()

    dna_rect = [
        dna_rect[0] + pos[0],
        dna_rect[1] + pos[1],
        dna_rect[2] + pos[0],
        dna_rect[3] + pos[1]
    ]

    if dna_rect[0] < 0:
        return False, []
    elif dna_rect[2] > environment.width:
        return False, []
    elif dna_rect[1] < 0:
        return False, []
    elif dna_rect[3] > environment.height:
        return False, []

    for org in orgList:
        if not org.alive():
            continue
        rect = org.get_rect()

        # Rect = [min_x, min_y, max_x, max_y]

        if (dna_rect[0] > rect[0] and dna_rect[0] < rect[2]) or (dna_rect[2] > rect[0] and dna_rect[2] < rect[2]) or (rect[0] > dna_rect[0] and rect[2] < dna_rect[2]): # Within X boundaries
            if (dna_rect[1] > rect[1] and dna_rect[1] < rect[3]) or (dna_rect[3] > rect[1] and dna_rect[3] < rect[3]) or (rect[1] > dna_rect[1] and rect[3] < dna_rect[3]): # Within Y boundaries
                return False, []

        for sprite in dead_cells:
            spritePos = sprite.getPos()
            spriteRadius = sprite.radius

            if spritePos[0] > dna_rect[0] and spritePos[0] < dna_rect[2]: # Within X boundaries
                if spritePos[1] > dna_rect[1] and spritePos[1] < dna_rect[3]:
                    overlappingSprites.append(sprite)

    return True, overlappingSprites

def get_new_organism_position(old_organism, dna, environment):
    orgSize = old_organism.dna.get_size()
    newSize = dna.get_size()
    dist = [ (orgSize[0]/1.3) + (newSize[0]/1.3), (orgSize[1]/1.3) + (newSize[1]/1.3) ]

    degList = list(range(360))
    #rDegList = sorted(degList, key=lambda x: random.random())
    rDegList = randomizeList(degList)

    for i in rDegList:
        rad = math.radians(i)
        direction = [math.cos(rad), math.sin(rad)]

        addX = direction[0] * dist[0]
        addY = direction[1] * dist[1]

        xPos = old_organism.pos[0] + addX
        yPos = old_organism.pos[1] + addY

        viable, overlappingSprites = viable_organism_position([xPos, yPos], dna, environment)
        if viable:
            for sprite in overlappingSprites:
                environment.removeSprite(sprite)
                sprite.info["removed"] = True
            return [xPos, yPos]
    return False

def eye_segment_handler(arbiter, space, data):
    if isinstance(arbiter.shapes[0], pymunk.Segment) or isinstance(arbiter.shapes[1], pymunk.Segment):
        return False
    if arbiter.shapes[1].sensor:
        return False
    sensor = arbiter.shapes[0].sprite
    sprite = arbiter.shapes[1].sprite
    if not sensor.alive:
        return False
    if sensor.organism != sprite.organism:
        if not sprite in sensor.info["view"]:
            sensor.info["view"].append(sprite)
    return False



class DNA():
    def __init__(self):
        self.cells = {}
        # Structure: {
        #    <Cell_ID>: {
        #       "size": <integer>,
        #       "type": <string>,
        #       "elasticity": <integer>,
        #       "mass": <integer>,
        #       "first": <boolean>,
        #       "relative_pos": [<integer>, <integer>],
        #       "mirror_self": <cell_id>,
        #       "max_health": <integer>,
        #       "energy_usage": [<idle>, <in use>],
        #       "energy_storage": <integer>
        #   }
        #}
        # `relative_pos` helps keep cells from forming to close to one another (starts at [0,0] for the first cell)

        self.growth_pattern = {}
        # Structure: {
        #   <Cell_ID>: {
        #        <Cell_ID_1>: [<X_Direction>, <Y_Direction>],
        #        <Cell_ID_2>: [<X_Direction>, <Y_Direction>]
        #   },
        #   <Cell_ID>: {
        #        <Cell_ID_1>: [<X_Direction>, <Y_Direction>],
        #        <Cell_ID_2>: [<X_Direction>, <Y_Direction>]
        #   }
        #}

        self._base_brain_structure = {
            "input_size": 6,
            "inputs": ["energy", "health", "rotation", "speed", "x_direction", "y_direction"],
            "hidden_layers": [], # [<integer>, <integer>, <integer>]
            "hidden_weights": [], # [ [<float>, <float>], [<float>, <float>, <float>], [<float>, <float>] ]
            "output_size": 4,
            "outputs": ["rotation", "speed", "x_direction", "y_direction"],
            "optimizer": "adam"
        }

        self.brain_structure = self._base_brain_structure.copy()

        self.trainingInput = []
        self.trainingOutput = []

        self.base_info = {
            "distanceThreshold": 2.2,
            "mirror_x": False,
            "mirror_y": False,
            "maximum_creation_tries": 30,
            "curiosity": 0.5 # Ranges from 0.0 to 1.0
        }
        # Structure: {
        #    "distanceThreshold": <integer>,
        #    "mirror_x": <boolean>,
        #    "mirror_y": <boolean>,
        #    "maximum_creation_tries": <integer>
        #}

        self.cellRange = [3,30]
        self.sizeRange = [6,42]
        self.massRange = [5,20]
        self.mirror_x = [0.6, 0.4]
        self.mirror_y = [0.6, 0.4]
        self.generation = 0

    def copy(self):
        return copy.deepcopy(self)

    def cell_size(self, cell_id):
        if cell_id in self.cells:
            return self.cells[cell_id]["size"]

    def first_cell(self):
        # Returns the first cell that's created while building this creature's body
        for id in self.cells:
            if self.cells[id]["first"]:
                return id

    def sub_cells(self, cell_id):
        if cell_id in self.growth_pattern:
            return [ id for id in self.growth_pattern[cell_id] ]
        return []

    def all_sub_cells(self, cell_id):
        all_cells = []
        checkList = []
        if cell_id in self.growth_pattern:
            checkList.extend( self.sub_cells(cell_id) )

            while checkList:
                id = checkList[0]
                all_cells.append(id)
                checkList.extend( self.sub_cells(id) )
                checkList.remove(id)
        return all_cells

    def remove_cell(self, cell_id, removing_mirror=False):
        if cell_id in self.cells:
            if self.cells[cell_id]["mirror_self"] and not removing_mirror:
                cell_info = self.cells[cell_id]
                if not cell_info["first"]:
                    mirrorID = self.cells[cell_id]["mirror_self"]
                    self.remove_cell(mirrorID, removing_mirror=True)
            self.cells.pop(cell_id)
            self.growth_pattern.pop(cell_id)

            for id in self.growth_pattern:
                if cell_id in self.growth_pattern[id]:
                    self.growth_pattern[id].pop(cell_id)

            for id in self.sub_cells(cell_id):
                self.remove_cell(id)

    def _lower_cells(self):
        # Returns all cells that do not contain children
        lower_cell_list = []

        for cell_id in self.growth_pattern:
            if not self.sub_cells(cell_id):
                lower_cell_list.append(cell_id)
        return lower_cell_list

    def grows_from(self, cell_id):
        # Returns the cell ID that this given cell grows from
        for id in self.growth_pattern:
            if cell_id in self.growth_pattern[id]:
                return id

    def path_to_first(self, cell_id):
        pList = []
        while True:
            parentCell = self.grows_from(cell_id)
            if parentCell:
                cell_id = parentCell
                pList.append(cell_id)
            else:
                break
        return pList

    def get_rect(self):
        # The is a rect of the relative positions of the cells in this DNA class - not their in-world position
        fCell = self.first_cell()
        minX = self.cells[fCell]["relative_pos"][0]
        maxX = self.cells[fCell]["relative_pos"][0]
        minY = self.cells[fCell]["relative_pos"][1]
        maxY = self.cells[fCell]["relative_pos"][1]

        for cell_id in self.cells:
            pos = self.cells[cell_id]["relative_pos"]
            radius = self.cells[cell_id]["size"]/2

            if pos[0]-radius < minX:
                minX = pos[0]
            if pos[0]+radius > maxX:
                maxX = pos[0]

            if pos[1]-radius < minY:
                minY = pos[1]
            if pos[1]+radius > maxY:
                maxY = pos[1]

        return [minX, minY, maxX, maxY]

    def get_size(self):
        rect = self.get_rect()

        minX = rect[0]
        minY = rect[1]
        maxX = rect[2]
        maxY = rect[3]

        if minX < 0:
            minX = -minX
        if minY < 0:
            minY = -minY
        width = maxX + minX
        height = maxY + minY

        return [width, height]

    def cell_distance(self, id1, id2):
        if not id1 in self.cells or not id2 in self.cells:
            return
        rel_pos1 = self.cells[id1]["relative_pos"]
        rel_pos2 = self.cells[id2]["relative_pos"]

        x1 = rel_pos1[0]
        y1 = rel_pos1[1]
        x2 = rel_pos2[0]
        y2 = rel_pos2[1]

        distance = calculateDistance(x1, y1, x2, y2)
        return distance

    def _new_cell_id(self):
        cid = 1
        while cid in self.cells:
            cid += 1
        return cid

    def _make_random_cell(self, sizeRange, massRange, first_cell=False):
        cell_id = self._new_cell_id()
        cell_info = {}

        cell_size = random.randrange(sizeRange[0], sizeRange[1])
        cell_info["size"] = cell_size

        cell_mass = random.randrange(massRange[0], massRange[1])
        cell_info["mass"] = cell_mass

        cell_elasticity = random.random()
        cell_info["elasticity"] = cell_elasticity

        cell_friction = random.random()
        cell_info["friction"] = cell_friction

        if first_cell:
            cell_info["mirror_self"] = cell_id
        else:
            cell_info["mirror_self"] = None

        if first_cell:
            cell_type = "heart"
        else:
            cell_type = random.choice(cell_types)
        cell_info["type"] = cell_type

        cell_health = base_cell_info["health"][cell_type] * cell_size * cell_mass
        cell_info["max_health"] = cell_health

        cell_energy_usage = [i * (cell_size/2) * (cell_mass/2) for i in base_cell_info["energy_usage"][cell_type]]
        cell_info["energy_usage"] = cell_energy_usage

        cell_energy_storage = base_cell_info["energy_storage"][cell_type] * cell_size * cell_mass
        cell_info["energy_storage"] = cell_energy_storage

        cell_damage = base_cell_info["damage"][cell_type]
        cell_info["damage"] = cell_damage

        cell_info["first"] = first_cell

        return cell_id, cell_info

    def _closest_cell_to_point(self, x, y):
        # This function only compares the relative positions of cells
        distances = {}
        for cell_id in self.cells:
            rel_pos = self.cells[cell_id]["relative_pos"]
            dist = calculateDistance(x, y, rel_pos[0], rel_pos[1])
            distances[dist] = cell_id
        if distances:
            closest_cell = distances[min(distances)]
            dist = min(distances)
            return closest_cell, dist

    def _new_relative_pos(self, parentID, direction, childSize):
        relParentPos = self.cells[parentID]["relative_pos"]
        parentSize = self.cells[parentID]["size"]
        newRelPos = relParentPos[:]

        addX = direction[0] * ( (parentSize/2) + (childSize/2) )
        addY = direction[1] * ( (parentSize/2) + (childSize/2) )

        newRelPos = [newRelPos[0] + addX, newRelPos[1] + addY]

        return newRelPos

    def _cell_mirrorable(self, x, y, cell_info):
        cellSize = cell_info["size"]

        newX = x
        newY = y

        if self.base_info["mirror_x"]:
            newX = -newX
        if self.base_info["mirror_y"]:
            newY = -newY

        distance = calculateDistance(x, y, newX, newY)

        if distance > (cellSize/self.base_info["distanceThreshold"]):
            return True
        return False

    def _viable_cell_position(self, x, y, cell_info):
        id, dist = self._closest_cell_to_point(x, y)

        size1 = cell_info["size"]
        size2 = self.cell_size(id)

        if self.base_info["mirror_x"] or self.base_info["mirror_y"]:
            if not self._cell_mirrorable(x, y, cell_info):
                return False

        if dist > (size1/self.base_info["distanceThreshold"] + size2/self.base_info["distanceThreshold"]):
            return True
        return False

    def _apply_mirror(self, cell_id, grows_from, grow_direction):
        newID = self._new_cell_id()
        cell_info = self.cells[cell_id].copy()

        self.cells[cell_id]["mirror_self"] = newID
        cell_info["mirror_self"] = cell_id

        relative_pos = self.cells[cell_id]["relative_pos"][:]

        if self.base_info["mirror_x"]:
            relative_pos[0] = -relative_pos[0]
        if self.base_info["mirror_y"]:
            relative_pos[1] = -relative_pos[1]

        new_grows_from = self.cells[grows_from]["mirror_self"]
        new_grow_direction = [-i for i in grow_direction]

        self.growth_pattern[new_grows_from][newID] = new_grow_direction

        cell_info["relative_pos"] = relative_pos

        self.cells[newID] = cell_info
        self.growth_pattern[newID] = {}

    def add_randomized_cell(self, sizeRange, massRange, first_cell=False):
        cell_id, cell_info = self._make_random_cell(sizeRange, massRange, first_cell=first_cell)

        if first_cell:
            relative_pos = [0,0]

        if self.cells and not first_cell:
            pos_verified = False
            iterations = 0
            while not pos_verified:
                if iterations > self.base_info["maximum_creation_tries"]:
                    return False
                iterations += 1
                grow_from = random.choice( list(self.cells) )
                grow_direction = random_direction()

                relative_pos = self._new_relative_pos(grow_from, grow_direction, cell_info["size"])

                if self._viable_cell_position(relative_pos[0], relative_pos[1], cell_info):
                    pos_verified = True

            self.growth_pattern[grow_from][cell_id] = grow_direction

        cell_info["relative_pos"] = relative_pos

        self.cells[cell_id] = cell_info
        self.growth_pattern[cell_id] = {}

        if not first_cell:
            if self.base_info["mirror_x"] or self.base_info["mirror_y"]:
                grow_from = self.grows_from(cell_id)
                grow_direction = self.growth_pattern[grow_from][cell_id]
                self._apply_mirror(cell_id, grow_from, grow_direction)
        return True

    def _setup_brain_structure(self, hiddenRange):
        self.brain_structure = self._base_brain_structure.copy()

        for cell_id in self.cells:
            cell_info = self.cells[cell_id]

            if cell_info["type"] == "eye":
                self.brain_structure["input_size"] += neural.output_lengths["eye"]
            elif cell_info["type"] == "carniv":
                self.brain_structure["input_size"] += neural.output_lengths["carniv"]

        hiddenSize = random.randrange(hiddenRange[0], hiddenRange[1])
        hiddenLayers = []

        if self.brain_structure["input_size"] > self.brain_structure["output_size"]:
            decRange = numpy.linspace(
                self.brain_structure["input_size"],
                self.brain_structure["output_size"],
                hiddenSize
            )
            decRange = list(decRange)
        else:
            decRange = numpy.linspace(
                self.brain_structure["output_size"],
                self.brain_structure["input_size"],
                hiddenSize
            )
            decRange = list(decRange)
            decRange = decRange.reverse()

        minRange = min(decRange)-1
        maxRange = max(decRange)

        for i in decRange:
            hiddenLayerSize = int(random.triangular(minRange, i, maxRange))
            while hiddenLayerSize == 0:
                hiddenLayerSize = int(random.triangular(minRange, i, maxRange))
            hiddenLayers.append(hiddenLayerSize)

        self.brain_structure["hidden_layers"] = hiddenLayers

        tempNet = neural.setup_network(self)
        for layer in tempNet.hiddenLayers:
            self.brain_structure["hidden_weights"].append( layer.weight.tolist() )

    def randomize(self, cellRange=[3,30], sizeRange=[6,42], massRange=[5,20], mirror_x=[0.6, 0.4], mirror_y=[0.6, 0.4], hiddenRange=[2, 6]):
        self.cellRange = cellRange
        self.sizeRange = sizeRange
        self.massRange = massRange
        self.mirror_x = mirror_x
        self.mirror_y = mirror_y

        self.cells = {}
        self.growth_pattern = {}

        mirror_x = numpy.random.choice(numpy.arange(0, 2), p=mirror_x)
        mirror_y = numpy.random.choice(numpy.arange(0, 2), p=mirror_y)

        mirror_x = bool(mirror_x)
        mirror_y = bool(mirror_y)

        self.base_info["mirror_x"] = mirror_x
        self.base_info["mirror_y"] = mirror_y
        self.base_info["curiosity"] = random.random()

        first_cell = True
        for i in range(random.randrange(cellRange[0], cellRange[1])):
            added = False
            while not added:
                added = self.add_randomized_cell(
                    sizeRange,
                    massRange,
                    first_cell=first_cell
                )
            first_cell = False

        self._setup_brain_structure(hiddenRange)

        return self

    def mutate_cell_count(self, severity):
        new_dna = self.copy()
        current_count = len(self.cells)
        countRange = int(severity * 18.)
        countRange = round(countRange)
        if not countRange:
            return new_dna
        addedCells = random.randrange(-countRange, countRange)

        while current_count + addedCells < 2:
            addedCells = random.randrange(-countRange, countRange)

        if addedCells < 0:
            for i in range(positive(addedCells)):
                lCells = randomizeList(new_dna._lower_cells())
                rCell = lCells[0]
                if rCell in self.cells and not self.cells[rCell]["first"]:
                    new_dna.remove_cell(rCell)
        elif addedCells > 0:
            for i in range(addedCells):
                added = False
                while not added:
                    added = new_dna.add_randomized_cell(
                        new_dna.sizeRange,
                        new_dna.massRange
                    )

        return new_dna

    def mutate_cell_types(self, severity):
        new_dna = self.copy()
        for cell_id in new_dna.cells:
            if random.random() <= severity and not new_dna.cells[cell_id]["first"]:
                new_type = random.choice(cell_types)
                new_dna.cells[cell_id]["type"] = new_type

                if new_dna.base_info["mirror_x"] or new_dna.base_info["mirror_y"]:
                    mirror_id = new_dna.cells[cell_id]["mirror_self"]
                    if mirror_id:
                        if mirror_id in new_dna.cells:
                            new_dna.cells[mirror_id]["type"] = new_type

        return new_dna

    def mutate_cell_masses(self, severity):
        new_dna = self.copy()
        for cell_id in new_dna.cells:
            if random.random() <= severity:
                mRange = int(severity * 10.)
                mRange = round(mRange)
                if not mRange:
                    return new_dna
                addRange = random.randrange(-mRange, mRange)

                while new_dna.cells[cell_id]["mass"] + addRange <= 0:
                    addRange = random.randrange(-mRange, mRange)

                new_dna.cells[cell_id]["mass"] += addRange

        return new_dna

    def mutate_brain_layers(self, severity, weight_persistence):
        oldHidden = self.brain_structure["hidden_layers"][:]
        newHidden = []
        lengthChange = round(severity * 10.)

        try:
            random.randrange(-lengthChange, lengthChange)
        except ValueError:
            return

        #lengthChange = random.randrange(-lengthChange, lengthChange)
        lengthChange = int(random.triangular(-lengthChange, 0, lengthChange))

        if lengthChange > 0:
            for i in range(lengthChange):
                if len(oldHidden)-1 >= i:
                    newLayer = oldHidden[i]
                else:
                    newLayer = random.randrange( min(oldHidden), max(oldHidden)+1 )
                newHidden.append(newLayer)
        else:
            newLength = len(oldHidden) + lengthChange
            if newLength < 1:
                newLength = 1

            for i in range(newLength):
                if len(oldHidden)-1 >= i:
                    newLayer = oldHidden[i]
                else:
                    newLayer = random.randrange( min(oldHidden), max(oldHidden)+1 )
                newHidden.append(newLayer)

        sizeChange = round(severity * 10.)

        for i in range(len(newHidden)):
            newAmt = int(random.triangular(-sizeChange, 0, sizeChange))
            newHidden[i] = newHidden[i]-newAmt
            if newHidden[i] < 2:
                newHidden[i] = 2

        self.brain_structure["hidden_layers"] = newHidden

        tempNet = neural.setup_network(self)

        if not tempNet.hiddenLayers or not weight_persistence:
            return # No hidden layers = no hidden weights to transfer over (or weight persistence is not active)

        #~ Weight preservation
        #  This allows for the weights of the parent network to be passed on to the offspring network - regardless of shape
        old_weights = self.brain_structure["hidden_weights"]
        old_layers = [ neural.torch.tensor(layer).float() for layer in old_weights ]

        self.brain_structure["hidden_weights"] = []

        for i, layer in enumerate(tempNet.hiddenLayers):
            newLayer = []
            for i2, subLayer in enumerate(layer.weight.data):
                try:
                    oldSubLayer = old_layers[i][i2]
                    newSubLayer = oldSubLayer.resize_(subLayer.shape)
                except IndexError:
                    newSubLayer = neural.torch.rand(subLayer.shape)
                newLayer.append(newSubLayer.tolist())
            if newLayer:
                self.brain_structure["hidden_weights"].append(newLayer)
        #~

    def mutate_curiosity(self, severity):
        new_dna = self.copy()
        add_curiosity = random.random() - random.random()
        add_curiosity *= severity
        new_curiosity = self.base_info["curiosity"] + add_curiosity

        if new_curiosity > 1.0:
            new_curiosity = 1.0
        elif new_curiosity < 0.0:
            new_curiosity = 0.0

        new_dna.base_info["curiosity"] = new_curiosity

        return new_dna

    def mutate_brain_structure(self, severity, weight_persistence):
        new_dna = self.copy()
        new_dna.mutate_brain_layers(severity, weight_persistence)

        return new_dna

    def mutate(self, severity, neural_severity, weight_persistence=True):
        # `severity` : 0.0 - 1.0
        new_dna = self.copy()

        new_dna.trainingInput = []
        new_dna.trainingOutput = []

        new_dna = new_dna.mutate_cell_count(severity)

        if random.random() <= severity:
            new_dna = new_dna.mutate_cell_types(severity)

        new_dna = new_dna.mutate_cell_masses(severity)

        new_dna = new_dna.mutate_brain_structure(neural_severity, weight_persistence)

        new_dna = new_dna.mutate_curiosity(neural_severity)

        return new_dna



class Organism():
    def __init__(self, pos, environment, dna=None):
        if not dna:
            dna = DNA().randomize()
        self.dna = dna
        self.pos = pos   # [<x>, <y>]
        self.environment = environment

        self.energy_consumed = 0.0
        # The amount of energy this organism has consumed from other cells

        self.cells = {}
        # Structure: {<Cell_ID>: <Sprite_Class>}


        self.movement = {
            "speed": 0,
            "direction": [0.0, 0.0],
            "rotation": 0
        }
        self.lastEnergy = 0.0 # Used to calculate the organism's dopamine
        self.lastHealth = 0.0 # Used to calculate the organism's pain
        self.energy_diff = 0.0
        self.dopamine_average = 0
        self.dopamine_memory = [0]*200
        self.dopamine_usage = 0.0
        self.dopamine = 0.0 # The current dopamine output
        self.pain = 0.0
        self.dopamine_update_interval = .1

        self.brain = None

        self.lastUpdated = time.time()
        self.last_updated_dopamine = time.time()
        self.lastBirth = time.time()
        self.birthTime = time.time()

    def _growth_position(self, newCellID, rel_pos=None):
        if not rel_pos:
            rel_pos = self.dna.cells[newCellID]["relative_pos"]
        new_position = [self.pos[0] + rel_pos[0],
                        self.pos[1] + rel_pos[1]]

        return new_position

    def cell_double_clicked(self, sprite):
        pass

    def _build_sprite(self, pos, cell_id, cell_info, alive=True):
        if alive:
            image = "Images{}{}.png".format(dirType, cell_info["type"])
        else:
            image = "Images{}{}".format(dirType, dead_image)
        body, shape = physics.makeCircle(
            cell_info["size"]/2,
            friction = cell_info["friction"],
            elasticity = cell_info["elasticity"],
            mass = cell_info["mass"]
        )
        newCell = physics.Sprite(
            pos,
            cell_info["size"],
            cell_info["size"],
            self.environment,
            body,
            shape,
            image=image
        )

        newCell.cell_id = cell_id
        newCell.collision = lambda sprite: self._cell_collision(newCell, sprite)
        newCell.organism = self
        newCell.cell_info = cell_info
        newCell.info = {
            "health": cell_info["max_health"],
            "energy": cell_info["energy_storage"]/2,
            "in_use": False,
            "sight": [],
            "view": [],
            "removed": False,
            "colliding": []
        }
        newCell.alive = alive
        newCell.creationTime = time.time()

        newCell.mouseDoubleClickEvent = lambda event: self.cell_double_clicked(newCell)

        if cell_info["type"] == "eye" and newCell.alive:
            num_bodies = 6
            sightRange = cell_info["size"] * eyesight_multiplier

            newBody, newShape = physics.makeCircle(sightRange, friction=0.0, elasticity=0.0, mass=1)
            newShape.sensor = True
            newShape.collision_type = 1
            newShape.sprite = newCell
            newBody.position = pos

            joint = pymunk.PinJoint(newBody, newCell.body, [0,0], [0,0])

            newCell.info["sight"] = [newBody, newShape, joint]

        return newCell

    def _create_cell(self, cell_id, subCells=False):
        # When `subCells` equals True, it will also create all cells that grow from the given cell
        firstCell = self.dna.cells[cell_id]["first"]
        if cell_id in self.dna.cells and not cell_id in self.cells:
            if not self.dna.grows_from(cell_id) in self.cells and not firstCell:
                print("NO PARENT")
                print(self.dna.grows_from(cell_id))
                return
            if firstCell:
                pos = self.pos
            else:
                pos = self._growth_position(cell_id)

            cell_info = self.dna.cells[cell_id]

            newCell = self._build_sprite(pos, cell_id, cell_info, alive=True)

            self.cells[cell_id] = newCell

            if subCells:
                for id in self.dna.sub_cells(cell_id):
                    self._create_cell(id, subCells=False)

            return newCell

    def _make_dead_cell(self, sprite):
        cell_id = sprite.cell_id
        cell_info = sprite.cell_info

        new_cell_info = cell_info.copy()
        new_cell_info["type"] = "dead"

        #pos = sprite.body.position
        pos = [sprite.body.position[0], sprite.body.position[1]]

        newCell = self._build_sprite(pos, cell_id, new_cell_info, alive=False)

        return newCell

    def rotation(self):
        fCell = self.dna.first_cell()

        live_cells = self.living_cells()
        if fCell in live_cells:
            live_cells.remove(fCell)

        if not live_cells:
            return 0

        first_pos = self.cells[fCell].body.position
        first_size = self.dna.cells[fCell]["size"]

        rel_id = live_cells[0]
        rel_pos = self.cells[rel_id].body.position
        rel_info = self.dna.cells[rel_id]

        oldAngle = getAngle( 0, 0, rel_info["relative_pos"][0], rel_info["relative_pos"][1] )
        curAngle = getAngle( first_pos[0], first_pos[1], rel_pos[0], rel_pos[1] )

        angleDiff = curAngle - oldAngle

        return math.degrees(angleDiff) % 360

    def living_cells(self):
        # Returns all living cell IDs
        living_cells = []
        for cell_id in self.cells:
            if self.cells[cell_id].alive:
                living_cells.append(cell_id)
        return living_cells

    def get_rect(self):
        fCell = self.dna.first_cell()
        minX = self.cells[fCell].body.position[0]
        maxX = self.cells[fCell].body.position[0]
        minY = self.cells[fCell].body.position[1]
        maxY = self.cells[fCell].body.position[1]

        for cell_id in self.living_cells():
            pos = self.cells[cell_id].body.position
            radius = self.cells[cell_id].radius

            if pos[0]-radius < minX:
                minX = pos[0]
            if pos[0]+radius > maxX:
                maxX = pos[0]

            if pos[1]-radius < minY:
                minY = pos[1]
            if pos[1]+radius > maxY:
                maxY = pos[1]

        return [minX, minY, maxX, maxY]

    def _revive_cell_angle(self, cell_id):
        # BACKBURNER
        parentID = self.dna.grows_from(cell_id)

        if not self.cells[parentID].alive:
            return

        childSize = self.dna.cells[cell_id]["size"]

        newAngle = math.radians(self.rotation())

        newDirection = getDirection(newAngle)

        newRelPos = self.dna._new_relative_pos(parentID, newDirection, childSize)

        return newRelPos

    def revive_cell(self, sprite):
        # BACKBURNER
        if sprite.alive:
            return
        cell_id = sprite.cell_id

        firstCell = self.dna.cells[cell_id]["first"]

        #if firstCell:
        #    pos = self.pos
        #else:
        #    pos = self._growth_position(cell_id)

        newRelPos = self._revive_cell_angle(cell_id)
        pos = self._growth_position(cell_id, rel_pos=newRelPos)

        cell_info = self.dna.cells[cell_id]
        newCell = self._build_sprite(pos, cell_id, cell_info, alive=True)
        self.cells[cell_id] = newCell

        sprite = self.cells[cell_id]
        self.environment.add_sprite(sprite)

        for id in self.cells:
            if id != cell_id:
                sprite2 = self.cells[id]
                sprite.connectTo(sprite2)

    def dead_children(self, sprite):
        dead_list = []
        cell_id = sprite.cell_id
        if cell_id in self.cells:
            for id in self.dna.sub_cells(cell_id):
                if id in self.cells:
                    sprite = self.cells[id]
                    if not sprite.alive:
                        dead_list.append(sprite)
        return dead_list

    def dead_cells(self):
        # Returns all dead cell IDs
        dead_cells = []
        for cell_id in self.cells:
            if not self.cells[cell_id].alive:
                dead_cells.append(cell_id)
        return dead_cells

    def max_energy(self):
        return sum([ self.dna.cells[id]["energy_storage"] for id in self.living_cells() ])
    def total_energy(self):
        # Returns the total amount of energy within this organism
        energyList = [self.cells[i].info["energy"] for i in self.living_cells()]
        return sum(energyList)
    def energy_percent(self):
        return num2perc( self.total_energy(), self.max_energy() )

    def max_health(self):
        return sum([self.dna.cells[id]["max_health"] for id in self.cells])
    def current_health(self):
        return sum([self.cells[id].info["health"] for id in self.living_cells()])
    def health_percent(self):
        return num2perc( self.current_health(), self.max_health() )

    def kill_cell(self, sprite):
        if not sprite.alive:
            return
        sprite.alive = False
        sprite.info["health"] = 0
        cell_id = sprite.cell_id
        cell_info = sprite.cell_info

        if not cell_info["first"]:
            parentID = self.dna.grows_from(cell_id)
            parentSprite = self.cells[parentID]
            if parentSprite.alive:
                damage_dealt = break_damage * cell_info["size"]
                parentSprite.info["health"] -= damage_dealt

        newCell = self._make_dead_cell(sprite)
        self.environment.removeSprite(sprite)
        sprite.info["removed"] = True
        self.environment.add_sprite(newCell)

        self.environment.space.remove(*sprite.info["sight"])

        newCell.body.velocity = sprite.body.velocity
        newCell.body.angular_velocity = sprite.body.angular_velocity

        for id in self.dna.sub_cells(cell_id):
            self.kill_cell(self.cells[id])

        return newCell

    def alive(self):
        # Returns True if this organism is alive, False otherwise
        if self.living_cells():
            return True
        return False

    def kill(self):
        fCell = self.dna.first_cell()
        if self.cells[fCell].alive:
            self.kill_cell(self.cells[fCell])

    def collision(self, cell, sprite):
        own_id = cell.cell_id
        other_id = sprite.cell_id

        own_info = cell.cell_info
        other_info = sprite.cell_info

        if not sprite in cell.info["colliding"]:
            cell.info["colliding"].append(sprite)
        if not cell in sprite.info["colliding"]:
            sprite.info["colliding"].append(cell)

    def _cell_collision(self, cell, sprite):
        # cell is the sprite for THIS organism's cell
        # sprite is the sprite for the OTHER organism's cell
        if not sprite in self.cells.values():
            if cell.alive or sprite.alive:
                self.collision(cell, sprite)

    def add_energy(self, amount):
        if not self.living_cells():
            return
        energy_per_cell = amount / len(self.living_cells())
        spare_energy = 0
        for cell_id in self.cells.copy():
            if self.cells[cell_id].alive:
                sprite = self.cells[cell_id]
                cell_info = sprite.cell_info

                sprite.info["energy"] += energy_per_cell + spare_energy
                spare_energy = 0

                if sprite.info["energy"] > cell_info["energy_storage"]:
                    diff = sprite.info["energy"] - cell_info["energy_storage"]
                    sprite.info["energy"] = cell_info["energy_storage"]
                    spare_energy = diff

        return spare_energy

    def convert_co2(self, cell_id, uDiff):
        sprite = self.cells[cell_id]
        if sprite.alive:
            cell_info = sprite.cell_info
            conversion_perc = num2perc(cell_info["size"], self.environment.width + self.environment.height)
            conversion_ratio = conversion_perc * uDiff

            co2 = perc2num(conversion_ratio, self.environment.info["co2"])

            self.environment.info["co2"] -= co2
            self.environment.info["oxygen"] += co2
            #added_energy = co2 * (cell_info["mass"] / 3) * (cell_info["size"] / 3)
            added_energy = co2 * co2_conversion_ratio

            spare_energy = self.add_energy(added_energy)

            #spare_co2 = spare_energy / (cell_info["mass"] / 3) / (cell_info["size"] / 3)
            spare_co2 = spare_energy / co2_conversion_ratio
            self.environment.info["co2"] += spare_co2
            self.environment.info["oxygen"] -= spare_co2

    def convert_o2(self, cell_id, uDiff):
        sprite = self.cells[cell_id]
        if sprite.alive:
            cell_info = sprite.cell_info
            conversion_perc = num2perc(cell_info["size"], self.environment.width + self.environment.height)
            conversion_ratio = conversion_perc * uDiff
            oxygen = perc2num(conversion_ratio, self.environment.info["oxygen"])

            self.environment.info["oxygen"] -= oxygen
            self.environment.info["co2"] += oxygen

    def _reproduce_organism(self, severity, neural_severity):
        self.lastBirth = time.time()
        weight_persistence = self.environment.info["weight_persistence"]
        new_dna = self.dna.mutate(severity=severity, neural_severity=neural_severity, weight_persistence=weight_persistence)

        new_pos = get_new_organism_position(self, new_dna, self.environment)
        if not new_pos:
            return False

        organism = Organism(new_pos, self.environment, dna=new_dna)
        organism.dna.generation = self.dna.generation + 1
        self.environment.info["organism_list"].append(organism)
        organism.build_body()
        return True

    def reproduce(self, severity=0.5, neural_severity=0.5):
        for i in range(offspring_amount):
            success = self._reproduce_organism(severity, neural_severity)
            if not success:
                break

    def _update_brain_weights(self):
        new_weights = []

        for layer in self.brain.hiddenLayers:
            layer_weights = layer.weight.data.tolist()
            new_weights.append(layer_weights)

        self.dna.brain_structure["hidden_weights"] = new_weights

    def _update_cell(self, cell_id, uDiff):
        sprite = self.cells[cell_id]
        cell_info = self.dna.cells[cell_id]

        if sprite.info["health"] <= 0:
            self.kill_cell(sprite)
            return

        if not sprite.alive:
            return

        if cell_info["type"] == "eye":
            cShape = sprite.info["sight"][1]
            for cell in sprite.info["view"][:]:
                if not cShape.shapes_collide(cell.shape).points or cell.info["removed"]:
                    sprite.info["view"].remove(cell)

        for cell in sprite.info["colliding"]:
            if not sprite.shape.shapes_collide(cell.shape).points or cell.info["removed"]:
                sprite.info["colliding"].remove(cell)

        if cell_info["type"] == "carniv":
            if sprite.info["colliding"]:
                sprite.info["in_use"] = True
            else:
                sprite.info["in_use"] = False

            damage_dealt = base_cell_info["damage"]["carniv"]
            for cell in sprite.info["colliding"]:
                added_energy = damage_dealt
                if cell.alive:
                    cell.info["health"] -= damage_dealt
                else:
                    mass = cell.body.mass
                    newMass = mass - (damage_dealt / sprite.cell_info["size"])

                    added_energy *= cell.cell_info["mass"]
                    added_energy *= cell.cell_info["size"]

                    if newMass > 0:
                        cell.body._set_mass(newMass)
                    else:
                        cell.body._set_mass(0)

                #sprite.organism.add_energy(added_energy)
                sprite.organism.energy_consumed += added_energy


        if cell_info["type"] == "push" and sprite.alive:
            if positive(self.movement["speed"]) >= .1:
                push_x = self.movement["direction"][0]
                push_y = self.movement["direction"][1]

                rotation = self.rotation()

                push_x += math.cos(math.radians(rotation))
                push_y += math.sin(math.radians(rotation))

                speed = self.movement["speed"] * max_push_speed
                speed *= (uDiff)

                new_velocity = [push_x*speed, push_y*speed]
                new_velocity = Vec2d(new_velocity)

                sprite.body.velocity += new_velocity
                sprite.info["in_use"] = True
            else:
                sprite.info["in_use"] = False

        if cell_info["type"] == "rotate" and sprite.alive:
            sprite.body.angular_velocity += self.movement["rotation"] * max_rotation_speed

            if positive(self.movement["rotation"]) >= .1:
                sprite.info["in_use"] = True
            else:
                sprite.info["in_use"] = False

        if sprite.info["in_use"]:
            if cell_info["type"] == "push":
                usage_diff = cell_info["energy_usage"][1] - cell_info["energy_usage"][0]
                push_energy = usage_diff * self.movement["speed"]

                if push_energy < 0:
                    energy_usage = positive(-cell_info["energy_usage"][0] + push_energy)
                else:
                    energy_usage = cell_info["energy_usage"][0] + push_energy
            elif cell_info["type"] == "rotate":
                usage_diff = cell_info["energy_usage"][1] - cell_info["energy_usage"][0]
                rotate_energy = usage_diff * self.movement["rotation"]

                if rotate_energy < 0:
                    energy_usage = positive(-cell_info["energy_usage"][0] + rotate_energy)
                else:
                    energy_usage = cell_info["energy_usage"][0] + rotate_energy
            else:
                energy_usage = cell_info["energy_usage"][1]
        else:
            energy_usage = cell_info["energy_usage"][0]

        sprite.info["energy"] -= energy_usage * uDiff

        if sprite.info["energy"] < 0:
            sprite.info["energy"] = 0

        if cell_info["type"] == "co2C":
            self.convert_co2(cell_id, uDiff)
        else:
            self.convert_o2(cell_id, uDiff)

        if sprite.info["energy"] > cell_info["energy_storage"]:
            sprite.info["energy"] = cell_info["energy_storage"]

        if sprite.info["energy"] >= cell_info["energy_storage"]/2 and sprite.info["health"] < cell_info["max_health"]:
            added_health = perc2num( heal_rate, cell_info["max_health"] ) * uDiff

            sprite.info["health"] += added_health
            if sprite.info["health"] > cell_info["max_health"]:
                sprite.info["health"] = cell_info["max_health"]

        #if sprite.info["energy"] >= cell_info["energy_storage"]/1.01 and self.dead_children(sprite):
        #    dead_list = self.dead_children(sprite)
        #    print(len(dead_list))
        #    if dead_list:
        #        self.revive_cell(dead_list[0])
        #        sprite.info["energy"] /= 2

        if sprite.info["energy"] <= 0:
            #self.kill_cell(sprite)
            damage_dealt = starvation_rate * uDiff
            sprite.info["health"] -= damage_dealt

    def update(self):
        uDiff = time.time() - self.lastUpdated
        self.lastUpdated = time.time()

        if self.energy_consumed >= self.max_energy()/2:
            self.energy_consumed = self.max_energy()/2
        if self.energy_consumed < 0.001:
            self.energy_consumed = 0

        if self.energy_consumed:
            digested_energy = perc2num(80, self.energy_consumed) * uDiff

            self.energy_consumed -= digested_energy
            self.energy_consumed += self.add_energy(digested_energy)

        #~ Process dopamine and pain levels
        if time.time() - self.last_updated_dopamine >= self.dopamine_update_interval:
            dopamine_uDiff = time.time() - self.last_updated_dopamine
            health_diff = self.health_percent() - self.lastHealth
            energy_diff = self.energy_percent() - self.lastEnergy
            self.energy_diff = energy_diff / dopamine_uDiff

            self.pain = health_diff / dopamine_uDiff
            self.dopamine_usage = energy_diff / dopamine_uDiff

            self.pain *= 2.

            if self.pain > 0:
                self.pain = 0.0

            self.pain = positive(self.pain)
            self.dopamine_usage -= self.pain

            self.dopamine_memory.append(self.dopamine)
            self.dopamine_memory.pop(0)

            self.dopamine_average = sum(self.dopamine_memory) / len(self.dopamine_memory)

            self.dopamine = self.dopamine_usage - self.dopamine_average
            #self.dopamine = self.dopamine_usage
            self.last_updated_dopamine = time.time()
        #~

        self.lastHealth = self.health_percent()
        self.lastEnergy = self.energy_percent()

        cells_alive = self.living_cells()
        if len(cells_alive) == 1:
            self.kill_cell(self.cells[cells_alive[0]])

        fCell = self.dna.first_cell()
        if self.cells[fCell].alive:
            self.pos = self.cells[fCell].body.position

        max_energy = self.max_energy()
        if self.total_energy() >= max_energy/1.01 and (time.time() - self.lastBirth) >= reproduction_limit:
            if random.random()*100. <= self.health_percent():
                if not self.environment.info["population"] >= self.environment.info["population_limit"]:
                    self.reproduce(
                        severity=self.environment.info["mutation_severity"],
                        neural_severity=self.environment.info["brain_mutation_severity"]
                    )

            for cell_id in self.cells:
                sprite = self.cells[cell_id]
                if sprite.alive:
                    sprite.info["energy"] = sprite.info["energy"]/2

        for cell_id in self.cells.copy():
            self._update_cell(cell_id, uDiff)

    def build_brain(self):
        learning_rate = self.environment.info["learning_rate"]
        self.brain = neural.setup_network(
            self.dna,
            learning_rate = learning_rate,
            rnn = self.environment.info["use_rnn"],
            hiddenSize = self.environment.info["hidden_rnn_size"]
        )

        for i, layer in enumerate(self.brain.hiddenLayers):
            new_weights = self.dna.brain_structure["hidden_weights"][i]
            new_weights = neural.torch.tensor(new_weights).float()

            layer.weight.data = new_weights

    def build_body(self):
        self.cells = {}
        self.lastUpdated = time.time()

        self.build_brain()

        fCell = self.dna.first_cell()
        # `fCell` holds information on the first cell that needs to be added

        if fCell:
            self._create_cell(fCell, subCells=True)
        else:
            print("ERROR: First cell not located - Quitting...")
            return

        for cell_id in self.dna.cells:
            self._create_cell(cell_id, subCells=True)

        for cell_id in self.cells:
            sprite = self.cells[cell_id]
            self.environment.add_sprite(sprite)
            self.environment.space.add(*sprite.info["sight"])

        for cell_id in self.cells:
            sprite = self.cells[cell_id]
            for id in self.cells:
                if id != cell_id:
                    sprite2 = self.cells[id]
                    sprite.connectTo(sprite2)

        self.lastHealth = self.health_percent()
        self.lastEnergy = self.energy_percent()



def disperse_cell(sprite):
    organism = sprite.organism
    environment = organism.environment
    #cell_info = sprite.cell_info
    #cell_id = sprite.cell_id

    #mass = sprite.body.mass

    #dispersed_co2 = co2_dispersion_ratio * (cell_info["size"] / 2) + mass

    #environment.info["co2"] += dispersed_co2
    #environment.info["oxygen"] -= dispersed_co2
    environment.removeSprite(sprite)
    sprite.info["removed"] = True

def disperse_all_dead(environment):
    for sprite in environment.sprites[:]:
        if not sprite.alive:
            disperse_cell(sprite)

def gradual_dispersion(environment, sprite, uDiff):
    mass = sprite.body.mass
    dispersion_rate = perc2num(cell_dispersion_rate, mass) * uDiff
    organism = sprite.organism
    cell_info = organism.dna.cells[sprite.cell_id]
    #dispersion_rate = cell_dispersion_rate * uDiff

    if mass < mass_cutoff:
        disperse_cell(sprite)
    else:
        newMass = mass - dispersion_rate
        if newMass > 0:
            renewedCo2 = perc2num(dispersion_rate, environment.info["oxygen"])

            sprite.body._set_mass(newMass)

            environment.info["co2"] += renewedCo2
            environment.info["oxygen"] -= renewedCo2
        else:
            disperse_cell(sprite)


def update_organisms(environment):
    # For this to work properly the environment must have the variable `lastUpdated` which holds a time.time() value
    # The environment must also have the ".info" variable which holds a dictionary containing "oganism_list" as a value
    uDiff = time.time() - environment.lastUpdated

    environment.lastUpdated = time.time()
    if environment.info["paused"]:
        return

    for org in environment.info["organism_list"][:]:
        if time.time() - org.birthTime >= age_limit:
            org.kill()

        if org.alive():
            org.update()

            brain_uDiff = time.time() - org.brain.lastUpdated
            if brain_uDiff >= neural_update_delay:
                neural_thread = Thread( target=org.brain.activate, args=[environment, org, uDiff] )
                neural_thread.run()

            train_uDiff = time.time() - org.brain.lastTrained
            if train_uDiff >= learning_update_delay:
                if org.dopamine >= training_dopamine_threshold or org.pain >= 0.1:
                    save_memory = True
                else:
                    save_memory = False

                if save_memory or environment.info["ambient_training"]:
                    neural.train_network(org, epochs=training_epochs, save_memory=save_memory)
        else:
            environment.info["organism_list"].remove(org)

    for sprite in environment.sprites:
        if not sprite.alive:
            gradual_dispersion(environment, sprite, uDiff)
        sprite_pos = sprite.getPos()
        if sprite_pos[0] < 0 or sprite_pos[0] > environment.width or sprite_pos[1] < 0 or sprite_pos[1] > environment.height:
            if sprite.alive:
                organism = sprite.organism
                sprite.info["health"] = 0
                #if organism in environment.info["organism_list"]:
                #    for cell_id in organism.cells:
                #        sprite = organism.cells[cell_id]
                #        environment.removeSprite(sprite)
                #    environment.info["organism_list"].remove(organism)
            else:
                environment.removeSprite(sprite)
                sprite.info["removed"] = True


if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = physics.setupEnvironment(myapp.worldView, myapp.scene)

        org = Organism([300,300], env)
        org2 = Organism([500,500], env)

        fCell = org.dna.first_cell()

        org.build_body()
        org2.build_body()

        window.show()
        sys.exit(app.exec_())
