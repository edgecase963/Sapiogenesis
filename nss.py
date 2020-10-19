import time
import sys
import random
import networks
import math
import numpy
import sprites

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from userInterface import Ui_MainWindow
import MainWindow

sys.path.insert(1, "../../Programs/shatterbox")

import shatterbox



def updateUI(window, environment):
    time_passed = time.time() - env.info["startTime"]

    if env.info["co2"] < 0:
        env.info["co2"] = 0

    co2 = env.info["co2"]
    population = len([i for i in env.info["organism_list"] if i.alive()])
    selected = env.info["selected"]
    window.co2_val.setText( str(int(co2)) )
    window.time_val.setText( str(int(time_passed)) )
    window.pop_val.setText( str(int(population)) )

    if window.min_cell_range_spinbox.value() >= window.max_cell_range_spinbox.value():
        window.max_cell_range_spinbox.setProperty("value", window.min_cell_range_spinbox.value()+1)
    if window.min_size_range_spinbox.value() >= window.max_size_range_spinbox.value():
        window.max_size_range_spinbox.setProperty("value", window.min_size_range_spinbox.value()+1)
    if window.min_mass_range_spinbox.value() >= window.max_mass_range_spinbox.value():
        window.max_mass_range_spinbox.setProperty("value", window.min_mass_range_spinbox.value()+1)

    mirror_x_chance = window.mirror_x_slider.value()
    mirror_y_chance = window.mirror_y_slider.value()

    window.mirror_x_lcd.setProperty("value", mirror_x_chance)
    window.mirror_y_lcd.setProperty("value", mirror_y_chance)
    if selected:
        window.energy_val.setText( str(int(selected.total_energy())) )

def cell_double_clicked(sprite, environment):
    pass

def add_organism(organism, environment):
    organism.cell_double_clicked = lambda sprite: cell_double_clicked(sprite, environment)

    environment.info["organism_list"].append(organism)
    organism.build_body()

def mousePressEvent(event, pos, environment):
    rightButton = False
    leftButton = False
    Mmodo = QtWidgets.QApplication.mouseButtons()

    if bool(Mmodo == QtCore.Qt.LeftButton):
        leftButton = True
    if bool(Mmodo == QtCore.Qt.RightButton):
        rightButton = True

    environment.info["lastPosition"] = pos

    sprite_clicked = environment.sprite_under_mouse()

    if sprite_clicked:
        organism = sprite_clicked.organism
        environment.info["selected"] = organism

def mouseReleaseEvent(event, pos, environment):
    rightButton = False
    leftButton = False
    Mmodo = QtWidgets.QApplication.mouseButtons()

    if bool(Mmodo == QtCore.Qt.LeftButton):
        leftButton = True
    if bool(Mmodo == QtCore.Qt.RightButton):
        rightButton = True

    environment.info["lastPosition"] = pos

def kill_btn_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        fCell = selected.dna.first_cell()
        sprite = selected.cells[fCell]
        if sprite.alive:
            selected.kill_cell(sprite)
def feed_btn_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        for cell_id in selected.cells:
            sprite = selected.cells[cell_id]
            if sprite.alive:
                cell_info = selected.dna.cells[cell_id]
                sprite.info["energy"] = cell_info["energy_storage"]

def add_creature_clicked(window, environment):
    minCellRange = window.min_cell_range_spinbox.value()
    maxCellRange = window.max_cell_range_spinbox.value()

    minSizeRange = window.min_size_range_spinbox.value()
    maxSizeRange = window.max_size_range_spinbox.value()

    minMassRange = window.min_mass_range_spinbox.value()
    maxMassRange = window.max_mass_range_spinbox.value()

    mirror_x = window.mirror_x_slider.value() / 100.
    mirror_y = window.mirror_y_slider.value() / 100.

    print("Mirror: {}, {}".format(mirror_x, mirror_y))

    dna = sprites.DNA().randomize(
        cellRange=[minCellRange, maxCellRange],
        sizeRange=[minSizeRange, maxSizeRange],
        massRange=[minMassRange, maxMassRange],
        mirror_x=[1.0 - mirror_x, mirror_x],
        mirror_y=[1.0 - mirror_y, mirror_y]
    )

    organism = sprites.Organism(environment.info["lastPosition"], env, dna=dna)
    add_organism(organism, environment)

def copy_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        environment.info["copied"] = selected

def paste_clicked(window, environment):
    copied = environment.info["copied"]
    if copied:
        newDna = copied.dna.copy()
        newPos = environment.info["lastPosition"]
        newOrganism = sprites.Organism(newPos, environment, dna=newDna)
        add_organism(newOrganism, environment)

def disperse_cells_clicked(window, environment):
    sprites.disperse_all_dead(environment)

def add_co2_clicked(window, environment):
    value = window.co2_spinBox.value()
    environment.info["co2"] += value
def rem_co2_clicked(window, environment):
    value = window.rem_co2_spinbox.value()
    environment.info["co2"] -= value
def set_co2_clicked(window, environment):
    value = window.set_co2_spinbox.value()
    environment.info["co2"] = value

def setup_window_buttons(window, environment):
    window.add_co2_btn.mouseReleaseEvent = lambda event: add_co2_clicked(window, environment)
    window.rem_co2_btn.mouseReleaseEvent = lambda event: rem_co2_clicked(window, environment)
    window.set_co2_btn.mouseReleaseEvent = lambda event: set_co2_clicked(window, environment)

    window.kill_btn.mouseReleaseEvent = lambda event: kill_btn_clicked(window, environment)
    window.feed_btn.mouseReleaseEvent = lambda event: feed_btn_clicked(window, environment)

    window.add_random_creature_event = lambda: add_creature_clicked(window, environment)
    window.kill_event = lambda: kill_btn_clicked(window, environment)
    window.copy_event = lambda: copy_clicked(window, environment)
    window.paste_event = lambda: paste_clicked(window, environment)
    window.disperse_cells_event = lambda: disperse_cells_clicked(window, environment)


if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        env_info = {
            "startTime": time.time(),
            "co2": 20000,
            "selected": None,
            "lastPosition": [0,0],
            "organism_list": [],
            "copied": None
        }


        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = shatterbox.setupEnvironment(myapp.worldView, myapp.scene)
        env.info = env_info
        env.lastUpdated = time.time()

        setup_window_buttons(myapp, env)

        env.preUpdateEvent = lambda: sprites.update_organisms(env)
        env.postUpdateEvent = lambda: updateUI(myapp, env)

        myapp.mirror_x_slider.setProperty("value", 40)
        myapp.mirror_y_slider.setProperty("value", 40)

        env.mousePressFunc = lambda event, pos: mousePressEvent(event, pos, env)
        env.mouseReleaseFunc = lambda event, pos: mouseReleaseEvent(event, pos, env)

        window.show()
        sys.exit(app.exec_())
