import time
import sys
import random
import networks
import math
import numpy
import sprites

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from MainWindow import Ui_MainWindow
import MainWindow

sys.path.insert(1, "../../Programs/shatterbox")

import shatterbox



def updateUI(window, environment):
    time_passed = time.time() - env.info["startTime"]
    co2 = env.info["co2"]
    population = len([i for i in env.info["organism_list"] if i.alive()])
    selected = env.info["selected"]
    window.co2_val.setText(MainWindow._translate("MainWindow", str(int(co2)), None))
    window.time_val.setText(MainWindow._translate("MainWindow", str(int(time_passed)), None))
    window.pop_val.setText(MainWindow._translate("MainWindow", str(int(population)), None))
    if selected:
        window.energy_val.setText(MainWindow._translate("MainWindow", str(int(selected.total_energy())), None))

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
    dna = sprites.DNA().randomize(
        cellRange=[3,30],
        sizeRange=[6,42],
        massRange=[5,20],
        mirror_x=[0.6, 0.4],
        mirror_y=[0.6, 0.4]
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

        env.mousePressFunc = lambda event, pos: mousePressEvent(event, pos, env)
        env.mouseReleaseFunc = lambda event, pos: mouseReleaseEvent(event, pos, env)

        window.show()
        sys.exit(app.exec_())
