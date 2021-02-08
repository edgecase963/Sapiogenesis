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
import torch
import TrainerFunctions
import EditorFunctions
import userInterface

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from userInterface import Ui_MainWindow
from TrainerWindow import Ui_Trainer
from userInterface import Ui_EditorWindow
from EditorWindow import Ui_Form as Editor_Dialog

__version__ = "0.9.5 (Beta)"



def updateUI(window, environment):
    time_passed = time.time() - environment.info["startTime"]

    event_uDiff = time.time() - environment.info["last_event_update"]
    sim_severity = window.sim_severity_slider.value() / 10.

    update_selection_widget(window, environment)

    if not environment.info["paused"]:
        if window.drought_checkbox.isChecked():
            depleted_val = sim_severity * event_uDiff
            environment.info["oxygen"] -= depleted_val
            environment.info["co2"] -= depleted_val
        if window.poison_checkbox.isChecked():
            depleted_val = sim_severity * event_uDiff
            for org in environment.info["organism_list"]:
                for cell_id in org.cells:
                    sprite = org.cells[cell_id]
                    sprite.info["health"] -= depleted_val * 5
        if window.random_cells_checkbox.isChecked():
            rVal = sim_severity * event_uDiff
            if random.random() <= rVal:
                randomPosX = random.randrange(10, environment.width)
                randomPosY = random.randrange(10, environment.height)
                add_dead_clicked(window, environment, [randomPosX, randomPosY])

    environment.info["last_event_update"] = time.time()

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

    #~ Sprite section
    if selected and selected.alive():
        window.generation_val.setText( str(selected.dna.generation) )
        if selected.brain:
            neurons = sum( [len(layer.bias) for layer in selected.brain.layers()] )
            window.neurons_val.setText( str(neurons) )

            window.memory_val.setText( str(len( selected.dna.trainingInput )) )

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

def mouseMoveEvent(worldView, event, environment):
    super(userInterface.World_View, worldView).mouseMoveEvent(event)

    pos = worldView.mapToScene(event.pos())
    pos = [pos.x(), pos.y()]
    environment.info["lastPosition"] = pos

def cell_double_clicked(sprite, environment):
    pass

def add_organism(organism, environment):
    organism.cell_double_clicked = lambda sprite: cell_double_clicked(sprite, environment)

    environment.info["organism_list"].append(organism)
    organism.build_body()

def update_selection_widget(myWindow, environment):
    selected = environment.info["selected"]

    if myWindow.selection_widget is not None:
        myWindow.scene.removeItem( myWindow.selection_widget )
        myWindow.selection_widget = None

    if selected is not None and myWindow.selection_box_checkbox.isChecked():
        new_width = int(selected.get_width() + 20)
        new_height = int(selected.get_height() + 20)
        rect = selected.get_rect()

        sImg = QtGui.QPixmap("Images/selection_image.png")
        sImg = sImg.scaled( new_width, new_height )

        graphicsPixmapItem = QtWidgets.QGraphicsPixmapItem(sImg)

        graphicsPixmapItem.setPixmap(sImg)
        graphicsPixmapItem.setPos(rect[0] - 10, rect[1] - 10)

        myWindow.scene.addItem(graphicsPixmapItem)

        myWindow.selection_widget = graphicsPixmapItem

def organism_selected(myWindow, environment, organism):
    environment.info["selected"] = organism

    myWindow.immortal_checkbox.setChecked(organism.immortal)
    myWindow.maladaptive_checkbox.setChecked(organism.maladaptive)
    myWindow.spec_finite_memory_checkbox.setChecked(organism.finite_memory)
    myWindow.curiosity_val.setText( str(round(organism.dna.base_info["curiosity"], 2)) )

    update_selection_widget(myWindow, environment)

def mousePressEvent(myWindow, event, pos, environment):
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
            if organism is not None:
                organism_selected(myWindow, environment, organism)

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
    pause_world(environment)

    selected = environment.info["selected"]
    if selected:
        new_dna = selected.dna.copy()
        filePath = QtWidgets.QFileDialog.getSaveFileName(window, "Select Directory")
        filePath = filePath[0]
        if filePath:
            with open(filePath, "wb") as f:
                pickle.dump(new_dna, f)
    resume_world(environment)
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

def clear_events_clicked(myWindow, environment):
    myWindow.drought_checkbox.setChecked(False)
    myWindow.poison_checkbox.setChecked(False)
    myWindow.random_cells_checkbox.setChecked(False)

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
def finite_memory_changed(val, environment):
    environment.info["finite_memory"] = val
def hidden_rnn_changed(val, environment):
    environment.info["hidden_rnn_size"] = val

def dialog_closed(dialog, event, environment):
    dialog.environment.stop()

    resume_world(dialog.main_environment)

    if dialog.info["saving"]:
        environment.info["copied"] = dialog.info["dna"].copy()

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
def reset_clicked(myWindow, environment):
    kill_all_clicked(environment)
    disperse_cells_clicked(environment)
    environment.info["co2"] = 30000
    environment.info["oxygen"] = 0
    environment.info["startTime"] = time.time()
    clear_events_clicked(myWindow, environment)
def import_organism_clicked(window, environment):
    pause_world(environment)

    filePath = QtWidgets.QFileDialog.getOpenFileName(window, "Select File")
    filePath = filePath[0]

    if filePath:
        with open(filePath, "rb") as f:
            new_dna = pickle.load(f)

        environment.info["copied"] = new_dna
    resume_world(environment)
def train_organism_clicked(window, environment):
    pause_world(environment)

    dialog = QtWidgets.QDialog()

    dialog.ui = Ui_Trainer()
    dialog.ui.setupUi(dialog)

    #dialog.closeEvent = lambda event: trainer_dialog_closed(dialog, event)

    selected = environment.info["selected"]
    if selected is not None:
        TrainerFunctions.setup_editor_buttons(dialog, selected)

    dialog.exec_()
def custom_organism_clicked(window, environment):
    pause_world(environment)

    dialog = QtWidgets.QDialog()

    dialog.ui = Ui_EditorWindow()
    dialog.ui.setupUi(dialog)

    dialog.main_environment = environment

    dialog.closeEvent = lambda event: dialog_closed(dialog, event, environment)

    EditorFunctions.setup_editor_buttons(dialog, environment)

    dialog.exec_()
def pause_world(environment):
    environment.pause_world()
def resume_world(environment):
    if not environment.info["paused"]:
        return

    def format_update_difference(diff):
        if diff > 0:
            return time.time() - diff
        return time.time()

    paused_time = environment.info["paused_time"]

    for org in environment.info["organism_list"]:
        last_updated_diff = paused_time - org.lastUpdated
        last_updated_dopamine_diff = paused_time - org.last_updated_dopamine
        brain_last_updated_diff = paused_time - org.brain.lastUpdated
        brain_last_trained_diff = paused_time - org.brain.lastTrained
        birth_time_diff = paused_time - org.birthTime

        org.lastUpdated = format_update_difference(last_updated_diff)
        org.last_updated_dopamine = format_update_difference(last_updated_dopamine_diff)
        org.brain.lastUpdated = format_update_difference(brain_last_updated_diff)
        org.brain.lastTrained = format_update_difference(brain_last_trained_diff)
        org.birthTime = format_update_difference(birth_time_diff)

    for sprite in environment.sprites:
        sprite_update_diff = paused_time - sprite.lastUpdated
        sprite.lastUpdated = format_update_difference(sprite_update_diff)

    env_update_diff = paused_time - environment.lastUpdated
    environment.lastUpdated = format_update_difference(env_update_diff)

    environment.resume_world()

def add_dead_clicked(window, environment, pos):
    cell_id = 0
    cell_info = {
        "size": 30,
        "mass": 12,
        "elasticity": .5,
        "friction": .5,
        "mirror_self": None,
        "first": False,
        "type": "body"
    }

    sprites.finish_cell_info(cell_info)

    newCell = sprites.build_sprite(environment, None, pos, cell_id, cell_info, alive=False)
    #newCell = self._build_sprite(environment.info["lastPosition"], cell_id, cell_info, alive=False)

    environment.add_sprite(newCell)

def keyPressed(event, window, myWindow, environment):
    if event.key() == QtCore.Qt.Key_Space:
        if environment.info["paused"]:
            resume_world(environment)
        else:
            pause_world(environment)
    if event.key() == QtCore.Qt.Key_C:
        copy_clicked(environment)
    if event.key() == QtCore.Qt.Key_V:
        paste_clicked(environment)
    if event.key() == QtCore.Qt.Key_R:
        reproduce_clicked(environment)
    if event.key() == QtCore.Qt.Key_T:
        train_btn_clicked(environment)
    if event.key() == QtCore.Qt.Key_H:
        heal_btn_clicked(myWindow, environment)
    if event.key() == QtCore.Qt.Key_K:
        kill_btn_clicked(myWindow, environment)
    if event.key() == QtCore.Qt.Key_E:
        custom_organism_clicked(window, environment)
    if event.key() == QtCore.Qt.Key_D:
        add_dead_clicked(window, environment, environment.info["lastPosition"])
def keyReleased(event, window, myWindow, environment):
    pass

def immortal_mode_clicked(myWindow, environment):
    selected = environment.info["selected"]

    if selected:
        if myWindow.immortal_checkbox.isChecked():
            selected.immortal = True
        else:
            selected.immortal = False
def maladaptive_mode_clicked(myWindow, environment):
    selected = environment.info["selected"]

    if selected:
        if myWindow.maladaptive_checkbox.isChecked():
            selected.maladaptive = True
        else:
            selected.maladaptive = False
def spec_finite_memory_clicked(myWindow, environment):
    selected = environment.info["selected"]

    if selected:
        if myWindow.spec_finite_memory_checkbox.isChecked():
            selected.finite_memory = True
        else:
            selected.finite_memory = False

def setup_window_buttons(window, myWindow, environment):
    myWindow.worldView.mouseMoveEvent = lambda event: mouseMoveEvent(myWindow.worldView, event, environment)

    myWindow.mirror_x_lcd.setProperty("value", myWindow.mirror_x_slider.value())
    myWindow.mirror_y_lcd.setProperty("value", myWindow.mirror_y_slider.value())

    myWindow.worldView.keyPressEvent = lambda event: keyPressed(event, window, myWindow, environment)
    myWindow.worldView.keyReleaseEvent = lambda event: keyReleased(event, window, myWindow, environment)

    myWindow.physical_severity_lcd.setProperty("value", myWindow.physical_severity_slider.value())
    myWindow.neural_severity_lcd.setProperty("value", myWindow.neural_severity_slider.value())

    myWindow.immortal_checkbox.clicked.connect(lambda event: immortal_mode_clicked(myWindow, environment))
    myWindow.maladaptive_checkbox.clicked.connect(lambda event: maladaptive_mode_clicked(myWindow, environment))
    myWindow.spec_finite_memory_checkbox.clicked.connect(lambda event: spec_finite_memory_clicked(myWindow, environment))

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
    myWindow.train_btn.mouseReleaseEvent = lambda event: train_organism_clicked(window, environment)
    #myWindow.train_btn.mouseReleaseEvent = lambda event: train_btn_clicked(environment)

    myWindow.sim_severity_slider.valueChanged.connect(lambda: sim_severity_changed(myWindow, environment))
    myWindow.mirror_x_slider.valueChanged.connect(lambda: mirror_x_val_changed(myWindow, environment))
    myWindow.mirror_y_slider.valueChanged.connect(lambda: mirror_y_val_changed(myWindow, environment))

    myWindow.physical_severity_slider.valueChanged.connect(lambda: physical_sev_val_changed(myWindow, environment))
    myWindow.neural_severity_slider.valueChanged.connect(lambda: neural_sev_val_changed(myWindow, environment))

    myWindow.clear_sim_btn.clicked.connect(lambda event: clear_events_clicked(myWindow, environment))

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
    myWindow.actionReset.triggered.connect(lambda: reset_clicked(myWindow, environment))
    myWindow.actionImport_Organism.triggered.connect(lambda: import_organism_clicked(window, environment))
    myWindow.actionCustom_Organism.triggered.connect(lambda: custom_organism_clicked(window, environment))
    myWindow.actionPause.triggered.connect(lambda: pause_world(environment))
    myWindow.actionResume.triggered.connect(lambda: resume_world(environment))

    myWindow.physical_severity_slider.lastChanged = time.time()
    myWindow.neural_severity_slider.lastChanged = time.time()

    myWindow.physical_severity_slider.valueChanged.connect(lambda v: slider_changed(v, myWindow))
    myWindow.neural_severity_slider.valueChanged.connect(lambda v: slider_changed(v, myWindow))
    myWindow.world_speed_spinbox.valueChanged.connect(lambda v: world_speed_changed(v, environment))

    #~ Brain section
    myWindow.neural_interval_spinbox.valueChanged.connect(neural_interval_changed)
    myWindow.training_interval_spinbox.valueChanged.connect(learning_delay_changed)
    myWindow.epochs_spinbox.valueChanged.connect(training_epochs_changed)
    myWindow.epoch_memory_spinbox.valueChanged.connect(epoch_memory_changed)
    myWindow.input_memory_spinbox.valueChanged.connect(stim_memory_changed)
    myWindow.learning_rate_val.valueChanged.connect(lambda val: learning_rate_changed(val, environment))
    myWindow.use_rnn_checkbox.toggled.connect(lambda val: use_rnn_changed(val, environment))
    myWindow.finite_memory_checkbox.toggled.connect(lambda val: finite_memory_changed(val, environment))
    myWindow.hidden_size_val.valueChanged.connect(lambda val: hidden_rnn_changed(val, environment))
    #~

    myWindow.age_limit_spinbox.valueChanged.connect(age_limit_changed)

def initial_creature(myWindow, environment):
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

    organism = sprites.Organism([300, 300], env, dna=dna)
    add_organism(organism, environment)


if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.selection_widget = None

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

        env.mousePressFunc = lambda event, pos: mousePressEvent(myapp, event, pos, env)
        env.mouseReleaseFunc = lambda event, pos: mouseReleaseEvent(event, pos, env)

        #initial_creature(myapp, env)

        window.show()
        sys.exit(app.exec_())
