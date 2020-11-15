import time
import sys
import random
import networks
import math
import numpy
import sprites
import pickle
import MainWindow
import physics

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from userInterface import Ui_MainWindow



default_o2_value = 30000
default_oxygen_value = 0



def updateUI(window, environment):
    time_passed = time.time() - environment.info["startTime"]

    if environment.info["co2"] < 0:
        environment.info["co2"] = 0

    co2 = environment.info["co2"]
    oxygen = environment.info["oxygen"]
    population = len([i for i in env.info["organism_list"] if i.alive()])
    environment.info["population"] = population
    selected = env.info["selected"]
    window.co2_val.setText( str(int(co2)) )
    window.oxygen_val.setText( str(int(oxygen)) )
    window.time_val.setText( str(int(time_passed)) )
    window.pop_val.setText( str(int(population)) )

    if selected and selected.alive():
        window.age_val.setText( str(int(time.time() - selected.birthTime)) )
        window.curiosity_val.setText( str(round(selected.dna.base_info["curiosity"], 2)) )

    if window.min_cell_range_spinbox.value() >= window.max_cell_range_spinbox.value():
        window.max_cell_range_spinbox.setProperty("value", window.min_cell_range_spinbox.value()+1)
    if window.min_size_range_spinbox.value() >= window.max_size_range_spinbox.value():
        window.max_size_range_spinbox.setProperty("value", window.min_size_range_spinbox.value()+1)
    if window.min_mass_range_spinbox.value() >= window.max_mass_range_spinbox.value():
        window.max_mass_range_spinbox.setProperty("value", window.min_mass_range_spinbox.value()+1)
    if window.min_hid_val.value() >= window.max_hid_val.value():
        window.max_hid_val.setProperty("value", window.min_hid_val.value()+1)

    #~ Reproduction section
    sprites.reproduction_limit = window.rep_time_val.value()
    environment.info["population_limit"] = window.max_pop_val.value()
    sprites.offspring_amount = window.offspring_val.value()
    environment.info["weight_persistence"] = window.weight_pers_checkbox.isChecked()
    #~

    mirror_x_chance = window.mirror_x_slider.value()
    mirror_y_chance = window.mirror_y_slider.value()

    mutation_severity = window.physical_severity_slider.value()
    neural_mutation_severity = window.neural_severity_slider.value()

    if selected:
        window.generation_val.setText( str(selected.generation) )
        if selected.brain:
            neurons = sum( [len(layer.bias) for layer in selected.brain.layers()] )
            window.neurons_val.setText( str(neurons) )

    window.mirror_x_lcd.setProperty("value", mirror_x_chance)
    window.mirror_y_lcd.setProperty("value", mirror_y_chance)
    window.physical_severity_lcd.setProperty("value", mutation_severity)
    window.neural_severity_lcd.setProperty("value", neural_mutation_severity)
    environment.info["mutation_severity"] = mutation_severity / 100.
    environment.info["brain_mutation_severity"] = neural_mutation_severity / 100.

    #~ Sprite section
    if selected:
        window.energy_val.setText( str(int(selected.total_energy())) )
        window.health_val.setText( str(int(selected.health_percent())) + "%" )

        dopamineText = str(round(selected.dopamine, 2))
        dopamineText = dopamineText.split(".")[0] + "." + dopamineText.split(".")[1].zfill(2)

        window.neural_loss_val.setText( str( round(selected.brain.lastLoss, 3) ) )
        window.stim_val.setText( str(float( round(selected.brain.stimulation, 2) )) )
        window.boredom_val.setText( str(float( round(selected.brain.boredom, 2) )) )
        window.iterations_val.setText( str(selected.brain.trainer.iterations) )
        window.dopamine_val.setText( dopamineText )
    #~

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
def heal_btn_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        for cell_id in selected.living_cells():
            sprite = selected.cells[cell_id]
            cell_info = sprite.cell_info

            sprite.info["health"] = cell_info["max_health"]
def feed_btn_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        for cell_id in selected.cells:
            sprite = selected.cells[cell_id]
            if sprite.alive:
                cell_info = selected.dna.cells[cell_id]
                sprite.info["energy"] = cell_info["energy_storage"]
def hurt_btn_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        for cell_id in selected.living_cells():
            sprite = selected.cells[cell_id]
            cell_info = sprite.cell_info

            health_perc = sprites.perc2num( 10, cell_info["max_health"] )
            sprite.info["health"] -= health_perc
            if sprite.info["health"] < 0:
                sprite.info["health"] = 0
def save_organism_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        new_dna = selected.dna.copy()
        filePath = QtWidgets.QFileDialog.getSaveFileName(window, "Select Directory")
        filePath = filePath[0]
        if filePath:
            with open(filePath, "wb") as f:
                pickle.dump(new_dna, f)

def reproduce_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        selected.reproduce(
            severity=environment.info["mutation_severity"],
            neural_severity=environment.info["brain_mutation_severity"]
        )

def add_creature_clicked(window, environment):
    minCellRange = window.min_cell_range_spinbox.value()
    maxCellRange = window.max_cell_range_spinbox.value()

    minSizeRange = window.min_size_range_spinbox.value()
    maxSizeRange = window.max_size_range_spinbox.value()

    minMassRange = window.min_mass_range_spinbox.value()
    maxMassRange = window.max_mass_range_spinbox.value()

    mirror_x = window.mirror_x_slider.value() / 100.
    mirror_y = window.mirror_y_slider.value() / 100.

    min_hiddden_layers = window.min_hid_val.value()
    max_hiddden_layers = window.max_hid_val.value()

    dna = sprites.DNA().randomize(
        cellRange=[minCellRange, maxCellRange],
        sizeRange=[minSizeRange, maxSizeRange],
        massRange=[minMassRange, maxMassRange],
        mirror_x=[1.0 - mirror_x, mirror_x],
        mirror_y=[1.0 - mirror_y, mirror_y],
        hiddenRange=[min_hiddden_layers, max_hiddden_layers]
    )

    organism = sprites.Organism(environment.info["lastPosition"], env, dna=dna)
    add_organism(organism, environment)

def copy_clicked(window, environment):
    selected = environment.info["selected"]
    if selected:
        environment.info["copied"] = selected.dna.copy()

def paste_clicked(window, environment):
    copied_dna = environment.info["copied"]
    if copied_dna:
        newPos = environment.info["lastPosition"]
        newOrganism = sprites.Organism(newPos, environment, dna=copied_dna.copy())
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

def slider_changed(val, window):
    if window.mutations_checkbox.isChecked():
        window.physical_severity_slider.setProperty("value", val)
        window.neural_severity_slider.setProperty("value", val)

def world_speed_changed(val, environment):
    environment.worldSpeed = val
def neural_interval_changed(val):
    sprites.neural_update_delay = val
def learning_delay_changed(val):
    sprites.learning_update_delay = val
def training_epochs_changed(val):
    sprites.training_epochs = val
def learning_threshold_changed(val):
    sprites.training_dopamine_threshold = val
def epoch_memory_changed(val):
    sprites.neural.memory_limit = val
def stim_memory_changed(val):
    sprites.neural.stimulation_memory = val
def age_limit_changed(val):
    sprites.age_limit = val

def feed_all_clicked(window, environment):
    for org in environment.info["organism_list"]:
        for cell_id in org.cells:
            sprite = org.cells[cell_id]
            if sprite.alive:
                cell_info = org.dna.cells[cell_id]
                sprite.info["energy"] = cell_info["energy_storage"]
def kill_all_clicked(window, environment):
    for org in environment.info["organism_list"]:
        org.kill()
def reset_clicked(window, environment):
    kill_all_clicked(window, environment)
    disperse_cells_clicked(window, environment)
    environment.info["co2"] = default_o2_value
    environment.info["oxygen"] = default_oxygen_value
    environment.info["startTime"] = time.time()
def import_organism_clicked(window, environment):
    filePath = QtWidgets.QFileDialog.getOpenFileName(window, "Select File")
    filePath = filePath[0]
    with open(filePath, "rb") as f:
        new_dna = pickle.load(f)

    environment.info["copied"] = new_dna

def setup_window_buttons(window, myWindow, environment):
    myWindow.add_co2_btn.mouseReleaseEvent = lambda event: add_co2_clicked(myWindow, environment)
    myWindow.rem_co2_btn.mouseReleaseEvent = lambda event: rem_co2_clicked(myWindow, environment)
    myWindow.set_co2_btn.mouseReleaseEvent = lambda event: set_co2_clicked(myWindow, environment)

    myWindow.kill_btn.mouseReleaseEvent = lambda event: kill_btn_clicked(myWindow, environment)
    myWindow.feed_btn.mouseReleaseEvent = lambda event: feed_btn_clicked(myWindow, environment)
    myWindow.hurt_btn.mouseReleaseEvent = lambda event: hurt_btn_clicked(myWindow, environment)
    myWindow.reproduce_btn.mouseReleaseEvent = lambda event: reproduce_clicked(myWindow, environment)
    myWindow.save_organism_btn.mouseReleaseEvent = lambda event: save_organism_clicked(window, environment)

    myWindow.add_random_creature_event = lambda: add_creature_clicked(myWindow, environment)
    myWindow.heal_event = lambda: heal_btn_clicked(myWindow, environment)
    myWindow.kill_event = lambda: kill_btn_clicked(myWindow, environment)
    myWindow.reproduce_event = lambda: reproduce_clicked(myWindow, environment)
    myWindow.copy_event = lambda: copy_clicked(myWindow, environment)
    myWindow.paste_event = lambda: paste_clicked(myWindow, environment)
    myWindow.disperse_cells_event = lambda: disperse_cells_clicked(myWindow, environment)

    myWindow.actionFeed_All_Organisms.triggered.connect(lambda: feed_all_clicked(myWindow, environment))
    myWindow.actionKill_All.triggered.connect(lambda: kill_all_clicked(myWindow, environment))
    myWindow.actionReset.triggered.connect(lambda: reset_clicked(myWindow, environment))
    myWindow.actionImport_Organism.triggered.connect(lambda: import_organism_clicked(window, environment))

    myWindow.physical_severity_slider.lastChanged = time.time()
    myWindow.neural_severity_slider.lastChanged = time.time()

    myWindow.physical_severity_slider.valueChanged.connect(lambda v: slider_changed(v, myWindow))
    myWindow.neural_severity_slider.valueChanged.connect(lambda v: slider_changed(v, myWindow))
    myWindow.world_speed_spinbox.valueChanged.connect(lambda v: world_speed_changed(v, environment))

    #~ Brain section
    myWindow.neural_interval_spinbox.valueChanged.connect(neural_interval_changed)
    myWindow.training_interval_spinbox.valueChanged.connect(learning_delay_changed)
    myWindow.epochs_spinbox.valueChanged.connect(training_epochs_changed)
    myWindow.learn_thresh_val.valueChanged.connect(learning_threshold_changed)
    myWindow.epoch_memory_spinbox.valueChanged.connect(epoch_memory_changed)
    myWindow.input_memory_spinbox.valueChanged.connect(stim_memory_changed)
    #~

    myWindow.age_limit_spinbox.valueChanged.connect(age_limit_changed)


if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        env_info = {
            "startTime": time.time(),
            "co2": default_o2_value,
            "oxygen": default_oxygen_value,
            "selected": None,
            "lastPosition": [0,0],
            "organism_list": [],
            "copied": None,
            "mutation_severity": 0.5,
            "brain_mutation_severity": 0.5,
            "reproduction_limit": 6,
            "population": 0,
            "population_limit": 50,
            "weight_persistence": True
        }


        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = physics.setupEnvironment(myapp.worldView, myapp.scene)
        env.space.add_collision_handler(1,0).begin = sprites.eye_segment_handler
        env.info = env_info
        env.lastUpdated = time.time()

        setup_window_buttons(window, myapp, env)

        env.preUpdateEvent = lambda: sprites.update_organisms(env)
        env.postUpdateEvent = lambda: updateUI(myapp, env)

        myapp.mirror_x_slider.setProperty("value", 40)
        myapp.mirror_y_slider.setProperty("value", 40)

        myapp.physical_severity_slider.setProperty("value", 50)
        myapp.neural_severity_slider.setProperty("value", 50)

        env.mousePressFunc = lambda event, pos: mousePressEvent(event, pos, env)
        env.mouseReleaseFunc = lambda event, pos: mouseReleaseEvent(event, pos, env)

        window.show()
        sys.exit(app.exec_())
