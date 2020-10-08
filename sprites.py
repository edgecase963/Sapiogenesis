import time
import sys
import random
import networks
import math

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from MainWindow import Ui_MainWindow

sys.path.insert(1, "../../Programs/shatterbox")

import shatterbox



cell_types = ["barrier", "carniv", "co2C", "eye", "olfactory", "push", "pheremone", "body"]


def random_direction():
    deg = random.randrange(0, 360)
    rad = math.radians(deg)
    x_direction = math.cos(rad)
    y_direction = math.sin(rad)
    return [x_direction, y_direction]

def calculateDistance(x1,y1,x2,y2):
    dist = math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )
    return dist



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
        #       "relative_pos": [<integer>, <integer>]
        #   }
        #}
        # `relative_pos` helps keep cells from forming to close to one another (starts at [0,0] for the first cell)

        #self.connections = {}
        # Structure: {
        #   <Cell_ID>: [<Cell_ID_1>, <Cell_ID_2>],
        #   <Cell_ID>: [<Cell_ID_1>, <Cell_ID_2>]
        #}

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
            cell_type = "heart"
        else:
            cell_type = random.choice(cell_types)
        cell_info["type"] = cell_type

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

        addX = direction[0] * ((parentSize/2) + (childSize/2))
        addY = direction[1] * ((parentSize/2) + (childSize/2))

        newRelPos = [newRelPos[0] + addX, newRelPos[1] + addY]

        return newRelPos

    def add_randomized_cell(self, sizeRange, massRange, first_cell=False):
        cell_id, cell_info = self._make_random_cell(sizeRange, massRange, first_cell=first_cell)

        if first_cell:
            relative_pos = [0,0]

        if self.cells and not first_cell:
            pos_verified = False
            while not pos_verified:
                grow_from = random.choice( list(self.cells) )
                grow_direction = random_direction()

                relative_pos = self._new_relative_pos(grow_from, grow_direction, cell_info["size"])

                id, dist = self._closest_cell_to_point(relative_pos[0], relative_pos[1])

                size1 = cell_info["size"]
                size2 = self.cell_size(id)

                if dist > (size1/2.5 + size2/2.5):
                    pos_verified = True

            self.growth_pattern[grow_from][cell_id] = grow_direction

        cell_info["relative_pos"] = relative_pos

        self.cells[cell_id] = cell_info
        self.growth_pattern[cell_id] = {}

    def randomize(self, cellRange=[5,40], sizeRange=[9,42], massRange=[5,20]):
        self.cells = {}
        self.growth_pattern = {}

        first_cell = True
        for i in range(random.randrange(cellRange[0], cellRange[1])):
            self.add_randomized_cell(sizeRange, massRange, first_cell=first_cell)
            first_cell = False
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

    def _growth_position(self, newCellID):
        rel_pos = self.dna.cells[newCellID]["relative_pos"]
        new_position = [self.pos[0] + rel_pos[0],
                        self.pos[1] + rel_pos[1]]

        return new_position

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

            cellInfo = self.dna.cells[cell_id]

            body, shape = shatterbox.makeCircle(
                cellInfo["size"]/2,
                friction = cellInfo["friction"],
                elasticity = cellInfo["elasticity"],
                mass = cellInfo["mass"]
            )
            newCell = shatterbox.Sprite(
                pos,
                cellInfo["size"],
                cellInfo["size"],
                self.environment,
                body,
                shape,
                image="Images/{}.png".format(cellInfo["type"])
            )

            self.cells[cell_id] = newCell

            if subCells:
                for id in self.dna.sub_cells(cell_id):
                    self._create_cell(id, subCells=False)

    def build_body(self):
        self.cells = {}

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



if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = shatterbox.setupEnvironment(myapp.worldView, myapp.scene)

        org = Organism([300,300], env)
        org2 = Organism([480,480], env)

        fCell = org.dna.first_cell()

        print(org.dna.growth_pattern[fCell])

        org.build_body()
        org2.build_body()

        window.show()
        sys.exit(app.exec_())
