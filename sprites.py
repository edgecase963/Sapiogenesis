import time
import sys
import random
import networks
import math
import numpy
import copy

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from MainWindow import Ui_MainWindow

sys.path.insert(1, "../../Programs/shatterbox")

import shatterbox



cell_types = ["barrier", "carniv", "eye", "olfactory", "co2C", "push", "pheremone", "body", "rotate"]
dead_image = "dead.png"

co2_dispersion_ratio = 18
# The dispersion ratio for dead cells.
# This is used to calculate how much CO2 is added back into the environment when a dead cell is dispersed
# Dispersion equation: <dispersion_ratio> * (<cell_size> / 2) * (<cell_mass> / 2)

cell_dispersion_rate = 5
# The percentage of a dead cell's mass to disperse per second

mass_cutoff = 1
# If a dead cell's mass becomes less than this, it will be removed (dispersed completely)

base_cell_info = {
    "health": {
        # This is multiplied by the size and mass of each given cell
        # <max_health> = <base_health> * <cell_size> * <cell_mass>
        "barrier": 60,
        "carniv": 15,
        "co2C": 8,
        "eye": 6,
        "olfactory": 12,
        "push": 12,
        "pheremone": 12,
        "body": 12,
        "heart": 8,
        "rotate": 12
    },
    "energy_usage": {
        # The first variable in the lists below represent an idle cell
        # The second variable reprents a cell's energy intake while in use
        # This is multiplied by the size and mass of each given cell
        # <max_energy_usage> = <base_energy_usage> * (<cell_size> / 2) * (<cell_mass> / 2)
        "barrier": [4, 4],
        "carniv": [10, 15],
        "co2C": [10, 10],
        "eye": [8, 8],
        "olfactory": [10, 12],
        "push": [10, 15],
        "pheremone": [8, 10],
        "body": [4, 4],
        "heart": [8, 8],
        "rotate": [10, 15]
    },
    "energy_storage": {
        # This is multiplied by the size and mass of each given cell
        # <energy_storage> = <base_energy_storage> * <cell_size> * <cell_mass>
        "barrier": 10,
        "carniv": 18,
        "co2C": 20,
        "eye": 18,
        "olfactory": 18,
        "push": 18,
        "pheremone": 18,
        "body": 18,
        "heart": 20,
        "rotate": 18
    },
    "damage": {
        # The damage each cell does when in contact with a cell from another organism
        "barrier": 0,
        "carniv": 60,
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
    dist = math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )
    return dist

def positive(x):
    if x > 0:
        return x
    return -x

def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))



class Brain():
    def __init__(self):
        pass


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

        self.base_info = {"distanceThreshold": 2.2, "mirror_x": False, "mirror_y": False, "maximum_creation_tries": 30}
        # Structure: {
        #    "distanceThreshold": <integer>,
        #    "mirror_x": <boolean>,
        #    "mirror_y": <boolean>,
        #    "maximum_creation_tries": <integer>
        #}

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

    def randomize(self, cellRange=[3,30], sizeRange=[6,42], massRange=[5,20], mirror_x=[0.6, 0.4], mirror_y=[0.6, 0.4]):
        self.cells = {}
        self.growth_pattern = {}

        mirror_x = numpy.random.choice(numpy.arange(0, 2), p=mirror_x)
        mirror_y = numpy.random.choice(numpy.arange(0, 2), p=mirror_y)

        mirror_x = bool(mirror_x)
        mirror_y = bool(mirror_y)

        self.base_info["mirror_x"] = mirror_x
        self.base_info["mirror_y"] = mirror_y

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
        print("Mirror X: {}\nMirror Y: {}\n\n".format(self.base_info["mirror_x"], self.base_info["mirror_y"]))
        return self


class Organism():
    def __init__(self, pos, environment, dna=None):
        if not dna:
            dna = DNA().randomize()
        self.dna = dna
        self.pos = pos   # [<x>, <y>]
        self.environment = environment

        self.cells = {}
        # Structure: {<Cell_ID>: <Sprite_Class>}

        self.brain = None

        lastUpdated = time.time()

    def _growth_position(self, newCellID):
        rel_pos = self.dna.cells[newCellID]["relative_pos"]
        new_position = [self.pos[0] + rel_pos[0],
                        self.pos[1] + rel_pos[1]]

        return new_position

    def cell_double_clicked(self, sprite):
        pass

    def _build_sprite(self, pos, cell_id, cell_info, alive=True):
        if alive:
            image = "Images/{}.png".format(cell_info["type"])
        else:
            image = "Images/{}".format(dead_image)
        body, shape = shatterbox.makeCircle(
            cell_info["size"]/2,
            friction = cell_info["friction"],
            elasticity = cell_info["elasticity"],
            mass = cell_info["mass"]
        )
        newCell = shatterbox.Sprite(
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
        newCell.base_info = cell_info
        newCell.info = {
            "health": cell_info["max_health"],
            "energy": cell_info["energy_storage"]/2,
            "in_use": False
        }
        newCell.alive = alive
        newCell.creationTime = time.time()

        newCell.mouseDoubleClickEvent = lambda event: self.cell_double_clicked(newCell)

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

    def _make_dead_cell(self, sprite):
        cell_id = sprite.cell_id
        cell_info = sprite.base_info

        new_cell_info = cell_info.copy()
        new_cell_info["type"] = "body"

        #pos = sprite.body.position
        pos = [sprite.body.position[0], sprite.body.position[1]]

        newCell = self._build_sprite(pos, cell_id, new_cell_info, alive=False)

        return newCell

    def living_cells(self):
        # Returns all living cell IDs
        living_cells = []
        for cell_id in self.cells:
            if self.cells[cell_id].alive:
                living_cells.append(cell_id)
        return living_cells

    def dead_cells(self):
        # Returns all dead cell IDs
        dead_cells = []
        for cell_id in self.cells:
            if not self.cells[cell_id].alive:
                dead_cells.append(cell_id)
        return dead_cells

    def total_energy(self):
        # Returns the total amount of energy within this organism
        energyList = [self.cells[i].info["energy"] for i in self.living_cells()]
        return sum(energyList)

    def kill_cell(self, sprite):
        if not sprite.alive:
            return
        sprite.alive = False
        cell_id = sprite.cell_id
        cell_info = sprite.base_info

        newCell = self._make_dead_cell(sprite)
        self.environment.removeSprite(sprite)
        self.environment.add_sprite(newCell)

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

    def collision(self, cell, sprite):
        own_id = cell.cell_id
        other_id = sprite.cell_id

        own_info = cell.base_info
        other_info = sprite.base_info

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
                cell_info = sprite.base_info

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
            cell_info = sprite.base_info
            conversion_perc = num2perc(cell_info["size"], self.environment.width + self.environment.height)
            conversion_ratio = conversion_perc * uDiff
            co2 = perc2num(conversion_ratio, self.environment.info["co2"])

            self.environment.info["co2"] -= co2
            added_energy = co2 * (cell_info["mass"] / 4) * (cell_info["size"] / 4)

            spare_energy = self.add_energy(added_energy)

            spare_co2 = spare_energy / (cell_info["mass"] / 4) / (cell_info["size"] / 4)
            self.environment.info["co2"] += spare_co2

    def update(self):
        uDiff = time.time() - self.lastUpdated
        self.lastUpdated = time.time()

        cells_alive = self.living_cells()
        if len(cells_alive) == 1:
            self.kill_cell(self.cells[cells_alive[0]])

        for cell_id in self.cells:
            sprite = self.cells[cell_id]
            cell_info = self.dna.cells[cell_id]

            if not sprite.alive:
                continue

            if sprite.info["in_use"]:
                energy_usage = cell_info["energy_usage"][1]
            else:
                energy_usage = cell_info["energy_usage"][0]

            sprite.info["energy"] -= energy_usage * uDiff

            if sprite.info["energy"] < 0:
                sprite.info["energy"] = 0

            if cell_info["type"] == "co2C":
                self.convert_co2(cell_id, uDiff)

            if sprite.info["energy"] > cell_info["energy_storage"]:
                sprite.info["energy"] = cell_info["energy_storage"]

            if sprite.info["energy"] <= 0:
                self.kill_cell(sprite)

    def build_body(self):
        self.cells = {}
        self.lastUpdated = time.time()

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

        for cell_id in self.cells:
            sprite = self.cells[cell_id]
            for id in self.cells:
                if id != cell_id:
                    sprite2 = self.cells[id]
                    sprite.connectTo(sprite2)



def disperse_cell(sprite):
    organism = sprite.organism
    environment = organism.environment
    cell_info = sprite.base_info
    cell_id = sprite.cell_id

    mass = sprite.body.mass

    dispersed_co2 = co2_dispersion_ratio * (cell_info["size"] / 2) + mass

    environment.info["co2"] += dispersed_co2
    environment.removeSprite(sprite)

def disperse_all_dead(environment):
    for sprite in environment.sprites[:]:
        if not sprite.alive:
            disperse_cell(sprite)

def gradual_dispersion(environment, sprite, uDiff):
    mass = sprite.body.mass
    dispersion_rate = perc2num(cell_dispersion_rate, mass) * uDiff
    #dispersion_rate = cell_dispersion_rate * uDiff

    if mass < mass_cutoff:
        disperse_cell(sprite)
    else:
        newMass = mass - dispersion_rate
        sprite.body._set_mass(newMass)

        renewedCo2 = dispersion_rate * co2_dispersion_ratio
        environment.info["co2"] += renewedCo2


def update_organisms(environment):
    # For this to work properly the environment must have the variable `lastUpdated` which holds a time.time() value
    # The environment must also have the ".info" variable which holds a dictionary containing "oganism_list" as a value
    for org in environment.info["organism_list"][:]:
        if not org.living_cells():
            environment.info["organism_list"].remove(org)
        else:
            org.update()

    uDiff = time.time() - environment.lastUpdated
    environment.lastUpdated = time.time()

    for sprite in environment.sprites:
        if not sprite.alive:
            gradual_dispersion(environment, sprite, uDiff)
        if sprite.pos().x() < 0 or sprite.pos().x() > environment.width or sprite.pos().y() < 0 or sprite.pos().y() > environment.height:
            organism = sprite.organism
            if organism in environment.info["organism_list"]:
                for cell_id in organism.cells:
                    sprite = organism.cells[cell_id]
                    environment.removeSprite(sprite)
                environment.info["organism_list"].remove(organism)


if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = shatterbox.setupEnvironment(myapp.worldView, myapp.scene)

        org = Organism([300,300], env)
        org2 = Organism([500,500], env)

        fCell = org.dna.first_cell()

        print(org.dna.growth_pattern[fCell])

        org.build_body()
        org2.build_body()

        window.show()
        sys.exit(app.exec_())
