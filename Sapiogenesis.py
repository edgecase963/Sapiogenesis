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
import copy

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from userInterface import Ui_MainWindow

__version__ = "0.6.0 (Beta)"



def updateUI(window, environment):
    time_passed = time.time() - environment.info["startTime"]

    sim_severity = window.sim_severity_slider.value() / 10.

    if environment.info["sim_drought"]:
        depleted_val = sim_severity * time_passed
        environment.info["oxygen"] -= depleted_val
        environment.info["co2"] -= depleted_val
    if environment.info["sim_algal"]:
        depleted_val = sim_severity * time_passed
        environment.info["oxygen"] -= depleted_val
    if environment.info["sim_poison"]:
        depleted_val = sim_severity * time_passed
        for org in environment.info["organism_list"]:
            for cell_id in org.cells:
                sprite = org.cells[cell_id]
                sprite.info["health"] -= depleted_val/10.

    if environment.info["co2"] < 0:
        environment.info["co2"] = 0
    if environment.info["oxygen"] < 0:
        environment.info["oxygen"] = 0

    co2 = environment.info["co2"]
    oxygen = environment.info["oxygen"]
    population = len([i for i in env.info["organism_list"] if i.alive()])
    environment.info["population"] = population
    selected = env.info["selected"]
    window.co2_val.setText( str(int(co2)) )
    window.oxygen_val.setText( str(int(oxygen)) )
    window.time_val.setText( str(int(time_passed)) )
    window.pop_val.setText( str(int(population)) )

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

    #window.test_label = QtWidgets.QLabel(window.worldView)
    #window.test_label.setGeometry(QtCore.QRect(10, 10, 60, 25))
    #window.test_label.setObjectName("test_label")
    #window.test_label.setText("CO2:")

    #~ Sprite section
    if selected and selected.alive():
        window.generation_val.setText( str(selected.dna.generation) )
        if selected.brain:
            neurons = sum( [len(layer.bias) for layer in selected.brain.layers()] )
            window.neurons_val.setText( str(neurons) )

        if not environment.info["paused"]:
            window.age_val.setText( str(int(time.time() - selected.birthTime)) )
        else:
            paused_time = environment.info["paused_time"]
            birth_time_diff = paused_time - selected.birthTime

            birth_val = time.time() - birth_time_diff
            birth_val = time.time() - birth_val

            if birth_val < 0:
                birth_val = 0

            window.age_val.setText( str(int(birth_val)) )

        window.energy_usage_val.setText( str(round(selected.energy_diff, 2)) )

        window.energy_val.setText( str(int( selected.energy_percent() )) + "%" )
        window.health_val.setText( str(int(selected.health_percent())) + "%" )

        dopamineText = str(round(selected.dopamine, 2))
        dopamineText = dopamineText.split(".")[0] + "." + dopamineText.split(".")[1]

        window.neural_loss_val.setText( str( round(selected.brain.lastLoss, 8) ) )
        window.stim_val.setText( str(float( round(selected.brain.stimulation, 4) )) )
        window.boredom_val.setText( str(float( round(selected.brain.boredom, 2) )) )
        window.pain_val.setText( str(float( round(selected.pain, 2) )) )
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
        if not sprite_clicked.isBubble:
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

def kill_btn_clicked(myWindow, environment):
    selected = environment.info["selected"]
    if selected:
        fCell = selected.dna.first_cell()
        sprite = selected.cells[fCell]
        if sprite.alive:
            selected.kill_cell(sprite)
def heal_btn_clicked(myWindow, environment):
    selected = environment.info["selected"]
    if selected:
        for cell_id in selected.living_cells():
            sprite = selected.cells[cell_id]
            cell_info = sprite.cell_info

            sprite.info["health"] = cell_info["max_health"]
def feed_btn_clicked(myWindow, environment):
    selected = environment.info["selected"]
    if selected:
        for cell_id in selected.cells:
            sprite = selected.cells[cell_id]
            if sprite.alive:
                cell_info = selected.dna.cells[cell_id]
                sprite.info["energy"] = cell_info["energy_storage"]
def hurt_btn_clicked(myWindow, environment):
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
    pause_world(window, environment)

    selected = environment.info["selected"]
    if selected:
        new_dna = selected.dna.copy()
        filePath = QtWidgets.QFileDialog.getSaveFileName(window, "Select Directory")
        filePath = filePath[0]
        if filePath:
            with open(filePath, "wb") as f:
                pickle.dump(new_dna, f)
    resume_world(window, environment)
def train_btn_clicked(environment):
    selected = environment.info["selected"]
    if selected:
        sprites.neural.train_network(selected, epochs=sprites.training_epochs)

def sim_severity_changed(myWindow, environment):
    myWindow.sim_severity_lcd.setProperty("value", myWindow.sim_severity_slider.value())
def mirror_x_val_changed(myWindow, environment):
    myWindow.mirror_x_lcd.setProperty("value", myWindow.mirror_x_slider.value())
def mirror_y_val_changed(myWindow, environment):
    myWindow.mirror_y_lcd.setProperty("value", myWindow.mirror_y_slider.value())
def physical_sev_val_changed(myWindow, environment):
    mutation_severity = myWindow.physical_severity_slider.value()

    myWindow.physical_severity_lcd.setProperty("value", mutation_severity)
    environment.info["mutation_severity"] = mutation_severity / 100.
def neural_sev_val_changed(myWindow, environment):
    neural_mutation_severity = myWindow.neural_severity_slider.value()

    myWindow.neural_severity_lcd.setProperty("value", neural_mutation_severity)
    environment.info["brain_mutation_severity"] = neural_mutation_severity / 100.

def drought_btn_clicked(window, environment):
    if environment.info["sim_drought"]:
        environment.info["sim_drought"] = False
    else:
        environment.info["sim_drought"] = True
def algal_btn_clicked(window, environment):
    if environment.info["sim_algal"]:
        environment.info["sim_algal"] = False
    else:
        environment.info["sim_algal"] = True
def poison_btn_clicked(window, environment):
    if environment.info["sim_poison"]:
        environment.info["sim_poison"] = False
    else:
        environment.info["sim_poison"] = True
def clear_events_clicked(window, environment):
    environment.info["sim_drought"] = False
    environment.info["sim_algal"] = False
    environment.info["sim_poison"] = False

def reproduce_clicked(environment):
    selected = environment.info["selected"]
    if selected:
        selected.reproduce(
            severity=environment.info["mutation_severity"],
            neural_severity=environment.info["brain_mutation_severity"]
        )
def erase_mem_clicked(environment):
    selected = environment.info["selected"]
    if selected:
        selected.dna.trainingInput = []
        selected.dna.trainingOutput = []
        selected.dna.previousInputs = []
        selected.dna.previousOutputs = []

def add_creature_clicked(myWindow, environment):
    minCellRange = myWindow.min_cell_range_spinbox.value()
    maxCellRange = myWindow.max_cell_range_spinbox.value()

    minSizeRange = myWindow.min_size_range_spinbox.value()
    maxSizeRange = myWindow.max_size_range_spinbox.value()

    minMassRange = myWindow.min_mass_range_spinbox.value()
    maxMassRange = myWindow.max_mass_range_spinbox.value()

    mirror_x = myWindow.mirror_x_slider.value() / 100.
    mirror_y = myWindow.mirror_y_slider.value() / 100.

    min_hiddden_layers = myWindow.min_hid_val.value()
    max_hiddden_layers = myWindow.max_hid_val.value()

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

def copy_clicked(environment):
    selected = environment.info["selected"]
    if selected:
        environment.info["copied"] = selected.dna.copy()

def paste_clicked(environment):
    copied_dna = environment.info["copied"]
    if copied_dna:
        newPos = environment.info["lastPosition"]
        newOrganism = sprites.Organism(newPos, environment, dna=copied_dna.copy())
        add_organism(newOrganism, environment)

def disperse_cells_clicked(environment):
    sprites.disperse_all_dead(environment)

def add_co2_clicked(myWindow, environment):
    value = myWindow.co2_spinBox.value()
    environment.info["co2"] += value
def rem_co2_clicked(myWindow, environment):
    value = myWindow.rem_co2_spinbox.value()
    environment.info["co2"] -= value
def set_co2_clicked(myWindow, environment):
    value = myWindow.set_co2_spinbox.value()
    environment.info["co2"] = value

def add_o2_clicked(myWindow, environment):
    value = myWindow.o2_spinbox.value()
    environment.info["oxygen"] += value
def rem_o2_clicked(myWindow, environment):
    value = myWindow.rem_o2_spinbox.value()
    environment.info["oxygen"] -= value
def set_o2_clicked(myWindow, environment):
    value = myWindow.set_o2_spinbox.value()
    environment.info["oxygen"] = value

def slider_changed(val, myWindow):
    if myWindow.mutations_checkbox.isChecked():
        myWindow.physical_severity_slider.setProperty("value", val)
        myWindow.neural_severity_slider.setProperty("value", val)

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
def learning_rate_changed(val, environment):
    environment.info["learning_rate"] = val
def use_rnn_changed(val, environment):
    environment.info["use_rnn"] = val
def amb_training_changed(val, environment):
    environment.info["ambient_training"] = val
def hidden_rnn_changed(val, environment):
    environment.info["hidden_rnn_size"] = val

def feed_all_clicked(environment):
    for org in environment.info["organism_list"]:
        for cell_id in org.cells:
            sprite = org.cells[cell_id]
            if sprite.alive:
                cell_info = org.dna.cells[cell_id]
                sprite.info["energy"] = cell_info["energy_storage"]
def kill_all_clicked(environment):
    for org in environment.info["organism_list"]:
        org.kill()
def reset_clicked(environment):
    kill_all_clicked(environment)
    disperse_cells_clicked(environment)
    environment.info["co2"] = 30000
    environment.info["oxygen"] = 0
    environment.info["startTime"] = time.time()
    clear_events_clicked(window, environment)
def import_organism_clicked(window, environment):
    pause_world(window, environment)

    filePath = QtWidgets.QFileDialog.getOpenFileName(window, "Select File")
    filePath = filePath[0]

    if filePath:
        with open(filePath, "rb") as f:
            new_dna = pickle.load(f)

        environment.info["copied"] = new_dna
    resume_world(window, environment)
def pause_world(window, environment):
    environment.info["paused"] = True
    environment.info["paused_time"] = time.time()
def resume_world(window, environment):
    if not environment.info["paused"]:
        return

    paused_time = environment.info["paused_time"]

    for org in environment.info["organism_list"]:
        last_updated_diff = paused_time - org.lastUpdated
        last_updated_dopamine_diff = paused_time - org.last_updated_dopamine
        brain_last_updated_diff = paused_time - org.brain.lastUpdated
        brain_last_trained_diff = paused_time - org.brain.lastTrained
        birth_time_diff = paused_time - org.birthTime

        org.lastUpdated = time.time() - last_updated_diff
        org.last_updated_dopamine = time.time() - last_updated_dopamine_diff
        org.brain.lastUpdated = time.time() - brain_last_updated_diff
        org.brain.lastTrained = time.time() - brain_last_trained_diff
        org.birthTime = time.time() - birth_time_diff

        for cell_id in org.cells:
            sprite = org.cells[cell_id]
            if sprite.alive:
                sprite_update_diff = paused_time - sprite.lastUpdated
                sprite.lastUpdated = time.time() - sprite_update_diff

    env_update_diff = paused_time - environment.lastUpdated
    environment.lastUpdated = time.time() - env_update_diff

    environment.info["paused"] = False

def keyPressed(event, window, myWindow, environment):
    if event.key() == QtCore.Qt.Key_Space:
        if environment.info["paused"]:
            resume_world(window, environment)
        else:
            pause_world(window, environment)
    if event.key() == QtCore.Qt.Key_C:
        copy_clicked(environment)
    if event.key() == QtCore.Qt.Key_R:
        reproduce_clicked(environment)
    if event.key() == QtCore.Qt.Key_T:
        train_btn_clicked(environment)
    if event.key() == QtCore.Qt.Key_H:
        heal_btn_clicked(myWindow, environment)
    if event.key() == QtCore.Qt.Key_K:
        kill_btn_clicked(myWindow, environment)
def keyReleased(event, window, myWindow, environment):
    pass

def setup_window_buttons(window, myWindow, environment):
    myWindow.mirror_x_lcd.setProperty("value", myWindow.mirror_x_slider.value())
    myWindow.mirror_y_lcd.setProperty("value", myWindow.mirror_y_slider.value())

    myWindow.worldView.keyPressEvent = lambda event: keyPressed(event, window, myWindow, environment)
    myWindow.worldView.keyReleaseEvent = lambda event: keyReleased(event, window, myWindow, environment)

    myWindow.physical_severity_lcd.setProperty("value", myWindow.physical_severity_slider.value())
    myWindow.neural_severity_lcd.setProperty("value", myWindow.neural_severity_slider.value())

    environment.info["mutation_severity"] = myWindow.physical_severity_slider.value() / 100.
    environment.info["brain_mutation_severity"] = myWindow.neural_severity_slider.value() / 100.

    myWindow.add_co2_btn.mouseReleaseEvent = lambda event: add_co2_clicked(myWindow, environment)
    myWindow.rem_co2_btn.mouseReleaseEvent = lambda event: rem_co2_clicked(myWindow, environment)
    myWindow.set_co2_btn.mouseReleaseEvent = lambda event: set_co2_clicked(myWindow, environment)

    myWindow.add_o2_btn.mouseReleaseEvent = lambda event: add_o2_clicked(myWindow, environment)
    myWindow.rem_o2_btn.mouseReleaseEvent = lambda event: rem_o2_clicked(myWindow, environment)
    myWindow.set_o2_btn.mouseReleaseEvent = lambda event: set_o2_clicked(myWindow, environment)

    myWindow.kill_btn.mouseReleaseEvent = lambda event: kill_btn_clicked(myWindow, environment)
    myWindow.feed_btn.mouseReleaseEvent = lambda event: feed_btn_clicked(myWindow, environment)
    myWindow.hurt_btn.mouseReleaseEvent = lambda event: hurt_btn_clicked(myWindow, environment)
    myWindow.reproduce_btn.mouseReleaseEvent = lambda event: reproduce_clicked(environment)
    myWindow.save_organism_btn.mouseReleaseEvent = lambda event: save_organism_clicked(window, environment)
    myWindow.train_btn.mouseReleaseEvent = lambda event: train_btn_clicked(environment)

    myWindow.sim_severity_slider.valueChanged.connect(lambda: sim_severity_changed(myWindow, environment))
    myWindow.mirror_x_slider.valueChanged.connect(lambda: mirror_x_val_changed(myWindow, environment))
    myWindow.mirror_y_slider.valueChanged.connect(lambda: mirror_y_val_changed(myWindow, environment))

    myWindow.physical_severity_slider.valueChanged.connect(lambda: physical_sev_val_changed(myWindow, environment))
    myWindow.neural_severity_slider.valueChanged.connect(lambda: neural_sev_val_changed(myWindow, environment))

    myWindow.drought_btn.mouseReleaseEvent = lambda event: drought_btn_clicked(window, environment)
    myWindow.algal_bloom_btn.mouseReleaseEvent = lambda event: algal_btn_clicked(window, environment)
    myWindow.poison_btn.mouseReleaseEvent = lambda event: poison_btn_clicked(window, environment)
    myWindow.clear_sim_btn.mouseReleaseEvent = lambda event: clear_events_clicked(window, environment)

    myWindow.add_random_creature_event = lambda: add_creature_clicked(myWindow, environment)
    myWindow.heal_event = lambda: heal_btn_clicked(myWindow, environment)
    myWindow.kill_event = lambda: kill_btn_clicked(myWindow, environment)
    myWindow.reproduce_event = lambda: reproduce_clicked(environment)
    myWindow.erase_mem_event = lambda: erase_mem_clicked(environment)
    myWindow.randomize_brain_event = lambda: randomize_brain(environment)
    myWindow.copy_event = lambda: copy_clicked(environment)
    myWindow.paste_event = lambda: paste_clicked(environment)
    myWindow.disperse_cells_event = lambda: disperse_cells_clicked(environment)

    myWindow.actionFeed_All_Organisms.triggered.connect(lambda: feed_all_clicked(environment))
    myWindow.actionKill_All.triggered.connect(lambda: kill_all_clicked(environment))
    myWindow.actionReset.triggered.connect(lambda: reset_clicked(environment))
    myWindow.actionImport_Organism.triggered.connect(lambda: import_organism_clicked(window, environment))
    myWindow.actionPause.triggered.connect(lambda: pause_world(window, environment))
    myWindow.actionResume.triggered.connect(lambda: resume_world(window, environment))

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
    myWindow.learning_rate_val.valueChanged.connect(lambda val: learning_rate_changed(val, environment))
    myWindow.use_rnn_checkbox.toggled.connect(lambda val: use_rnn_changed(val, environment))
    myWindow.amb_training_checkbox.toggled.connect(lambda val: amb_training_changed(val, environment))
    myWindow.hidden_size_val.valueChanged.connect(lambda val: hidden_rnn_changed(val, environment))
    #~

    myWindow.age_limit_spinbox.valueChanged.connect(age_limit_changed)


if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = physics.setupEnvironment(myapp.worldView, myapp.scene)
        env.space.add_collision_handler(1,0).begin = sprites.eye_segment_handler
        env.lastUpdated = time.time()

        myapp.version_val.setText(__version__)
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
