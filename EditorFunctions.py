import physics
import sprites
import userInterface
import math
import time

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets



def remake_organism(dialog, new_dna):
    h_layers = dialog.ui.hidden_layers_val.value()
    new_dna._setup_brain_structure([h_layers, h_layers+1])

    selected = dialog.info["selected_cell"]

    cid = None
    if selected is not None:
        cid = selected.cell_id

    new_dna.erase_memory()
    # Necessary in case the input or output sizes of the neural network have changed

    new_organism = sprites.Organism(
        [dialog.ui.scene.width()/2, dialog.ui.scene.height()/2],
        dialog.environment,
        dna = new_dna
    )

    for cell_id in dialog.info["organism"].cells:
        sprite = dialog.info["organism"].cells[cell_id]

        dialog.environment.removeSprite(sprite)
        sprite.info["removed"] = True

        dialog.environment.space.remove(*sprite.info["detection_items"])

    dialog.environment.info["organism_list"].remove( dialog.info["organism"] )

    dialog.info["dna"] = new_dna
    dialog.info["organism"] = new_organism

    dialog.environment.info["organism_list"].append(new_organism)
    new_organism.build_body()

    if cid is not None:
        if cid in new_organism.cells:
            dialog.info["selected_cell"] = new_organism.cells[cid]

def update_ui(dialog, environment):
    dna = dialog.info["dna"]
    organism = dialog.info["organism"]

    update_selection_widget(dialog)

    if dialog.info["selected_cell"]:
        sprite = dialog.info["selected_cell"]
        cell_info = sprite.cell_info
        cell_id = sprite.cell_id

        dialog.ui.selected_cell_val.setText( cell_info["type"].capitalize() )

    max_energy = sum([ dna.cells[cid]["energy_storage"] for cid in dna.cells ])
    max_health = sum([ dna.cells[cid]["max_health"] for cid in dna.cells ])

    dialog.ui.max_energy_val.setText( str(max_energy) )
    dialog.ui.max_health_val.setText( str(max_health) )

    if environment.info["paused"]:
        dialog.ui.physics_val.setText("Paused")
    else:
        dialog.ui.physics_val.setText("Active")

def mousePressEvent(event, pos, dialog, environment):
    sprite_clicked = environment.sprite_under_mouse()

    if sprite_clicked:
        if not sprite_clicked.isBubble:
            dialog.info["selected_cell"] = sprite_clicked

def add_cell_clicked(dialog, cell_type):
    if not dialog.info["selected_cell"]:
        return

    mass = dialog.ui.mass_val.value()
    size = dialog.ui.size_val.value()
    elasticity = dialog.ui.elasticity_val.value()
    friction = dialog.ui.friction_val.value()
    dial_value = dialog.ui.direction_dial.value()

    angle = math.radians( (dial_value / 100.) * 360 )

    new_id = dialog.info["dna"].add_cell(dialog.info["selected_cell"].cell_id, cell_type, size, mass, elasticity, friction, angle)

    remake_organism(dialog, dialog.info["dna"])

    sprite = dialog.info["organism"].cells[new_id]

    cell_selected(dialog, sprite)

def change_cell_clicked(dialog, cell_type):
    if not dialog.info["selected_cell"]:
        return

    cell_id = dialog.info["selected_cell"].cell_id
    dna = dialog.info["dna"]

    if cell_id == dna.first_cell():
        return

    dna.change_type(cell_id, cell_type)

    remake_organism(dialog, dna)

def cell_btn_clicked(dialog, cell_type):
    if dialog.info["adding_cell"]:
        add_cell_clicked(dialog, cell_type)
    else:
        change_cell_clicked(dialog, cell_type)

def update_relative_positions(dna, cell_id, is_mirror=False):
    parentID = dna.grows_from(cell_id)
    if parentID is not None:
        direction = dna.growth_pattern[parentID][cell_id]
        childSize = dna.cells[cell_id]["size"]

        new_rel_pos = dna._new_relative_pos(parentID, direction, childSize)

        dna.cells[cell_id]["relative_pos"] = new_rel_pos

        if dna.cells[cell_id]["mirror_self"] and not is_mirror:
            mirror_id = dna.cells[cell_id]["mirror_self"]
            update_relative_positions(dna, mirror_id, is_mirror=True)

    for cID in dna.sub_cells(cell_id):
        update_relative_positions(dna, cID)

def dial_changed(dialog, val):
    if not dialog.info["selected_cell"]:
        return
    if dialog.info["cell_recently_selected"]:
        dialog.info["cell_recently_selected"] = False
        return

    sprite = dialog.info["selected_cell"]
    cell_id = sprite.cell_id
    cell_info = sprite.cell_info
    dna = dialog.info["dna"]

    mirror_id = cell_info["mirror_self"]

    if cell_info["first"]:
        return

    new_angle = math.radians( (val / 100.) * 360 )
    new_angle += math.radians(90)
    new_direction = [ math.cos(new_angle), math.sin(new_angle) ]

    parentID = dna.grows_from(cell_id)

    dna.growth_pattern[parentID][cell_id] = new_direction

    dna._apply_mirror(cell_id, parentID, new_direction, newID=mirror_id)

    #if cell_info["mirror_self"]:
    #    mirror_id = cell_info["mirror_self"]
    #    dna._apply_mirror(cell_id, parentID, new_direction, newID=mirror_id)

    update_relative_positions(dna, cell_id)

    update_organism_mirroring(dialog)

    remake_organism(dialog, dna)

def mouseMoveEvent(self, event):
    super(userInterface.World_View, self).mouseMoveEvent(event)

    pos = self.mapToScene(event.pos())
    mousePos = [pos.x(), pos.y()]

def cell_selected(dialog, sprite):
    dialog.info["selected_cell"] = sprite
    cell_info = sprite.cell_info
    cell_id = sprite.cell_id
    dna = dialog.info["dna"]

    parentID = dna.grows_from(cell_id)

    dialog.ui.mass_val.blockSignals(True)
    dialog.ui.size_val.blockSignals(True)
    dialog.ui.elasticity_val.blockSignals(True)
    dialog.ui.friction_val.blockSignals(True)

    dialog.ui.mass_val.setValue(cell_info["mass"])
    dialog.ui.size_val.setValue(cell_info["size"])
    dialog.ui.elasticity_val.setValue(cell_info["elasticity"])
    dialog.ui.friction_val.setValue(cell_info["friction"])

    dialog.ui.mass_val.blockSignals(False)
    dialog.ui.size_val.blockSignals(False)
    dialog.ui.elasticity_val.blockSignals(False)
    dialog.ui.friction_val.blockSignals(False)

    if cell_info["first"]:
        return

    parentPos = dna.cells[parentID]["relative_pos"]
    cellPos = cell_info["relative_pos"]

    angle = sprites.getAngle(cellPos[0], cellPos[1], parentPos[0], parentPos[1])
    angle += math.radians(90)
    deg = math.degrees(angle)
    dialVal = (deg / 360.) * 100.

    dialog.info["cell_recently_selected"] = True

    dialog.ui.direction_dial.setValue(dialVal)

def delete_btn_clicked(dialog):
    if dialog.info["selected_cell"] is None:
        return

    sprite = dialog.info["selected_cell"]
    cell_id = sprite.cell_id
    dna = dialog.info["dna"]

    if sprite.cell_info["first"]:
        return

    new_dna = dna.remove_cell(cell_id)

    dialog.info["selected_cell"] = None

    remake_organism(dialog, new_dna)

def update_organism_mirroring(dialog):
    dna = dialog.info["dna"]

    if dna.base_info["mirror_x"] or dna.base_info["mirror_y"]:
        for cell_id in dna.cells.copy():
            cell_info = dna.cells[cell_id]
            if cell_info["first"]:
                continue

            parentID = dna.grows_from(cell_id)
            grow_direction = dna.growth_pattern[parentID][cell_id]
            mirror_id = dna.cells[cell_id]["mirror_self"]

            dna._apply_mirror(cell_id, parentID, grow_direction, newID=mirror_id)
    else:
        new_dna = dna.copy()

        for cell_id in dna.cells.copy():
            cell_info = dna.cells[cell_id]
            if cell_info["first"]:
                continue

            mirror_id = cell_info["mirror_self"]
            if mirror_id is None:
                continue

            if mirror_id > cell_id and mirror_id in new_dna.cells:
                new_dna = new_dna.remove_cell(mirror_id, removing_mirror=True, remove_sub_cells=False)

        dialog.info["dna"] = new_dna

def mirror_x_changed(dialog, val):
    dialog.info["dna"].base_info["mirror_x"] = val

    update_organism_mirroring(dialog)

    remake_organism(dialog, dialog.info["dna"])

def mirror_y_changed(dialog, val):
    dialog.info["dna"].base_info["mirror_y"] = val

    update_organism_mirroring(dialog)

    remake_organism(dialog, dialog.info["dna"])

def mousePressEvent(event, pos, dialog):
    rightButton = False
    leftButton = False
    Mmodo = QtWidgets.QApplication.mouseButtons()

    if bool(Mmodo == QtCore.Qt.LeftButton):
        leftButton = True
    if bool(Mmodo == QtCore.Qt.RightButton):
        rightButton = True

    dialog.environment.info["lastPosition"] = pos

    sprite_clicked = dialog.environment.sprite_under_mouse()

    if sprite_clicked:
        if not sprite_clicked.isBubble:
            cell_selected(dialog, sprite_clicked)

            organism = sprite_clicked.organism
            dialog.environment.info["selected"] = organism

def reset_clicked(dialog, event):
    dialog.info["dna"] = sprites.DNA().randomize(cellRange=[1, 2], sizeRange=[20, 21], massRange=[10, 11], mirror_x=[1, 0], mirror_y=[1, 0])

    dialog.ui.mirror_x_checkbox.setChecked(dialog.info["dna"].base_info["mirror_x"])
    dialog.ui.mirror_y_checkbox.setChecked(dialog.info["dna"].base_info["mirror_y"])
    remake_organism(dialog, dialog.info["dna"])

def cancel_clicked(dialog, event):
    dialog.info["saving"] = False
    dialog.close()

def finish_clicked(dialog, event):
    dialog.info["saving"] = True
    dialog.close()

def size_changed(dialog, val):
    if dialog.info["selected_cell"] is None:
        return
    cell_id = dialog.info["selected_cell"].cell_id

    dialog.info["dna"].set_size(cell_id, val)

    update_relative_positions(dialog.info["dna"], cell_id)
    update_organism_mirroring(dialog)

    remake_organism(dialog, dialog.info["dna"])
def mass_changed(dialog, val):
    if dialog.info["selected_cell"] is None:
        return
    cell_id = dialog.info["selected_cell"].cell_id
    dna = dialog.info["dna"]

    dna.set_mass(cell_id, val)

    update_relative_positions(dna, cell_id)
    update_organism_mirroring(dialog)

    remake_organism(dialog, dna)
def elasticity_changed(dialog, val):
    if dialog.info["selected_cell"] is None:
        return
    cell_id = dialog.info["selected_cell"].cell_id

    dialog.info["dna"].set_elasticity(cell_id, val)

    remake_organism(dialog, dialog.info["dna"])
def friction_changed(dialog, val):
    if dialog.info["selected_cell"] is None:
        return
    cell_id = dialog.info["selected_cell"].cell_id

    dialog.info["dna"].set_friction(cell_id, val)

    update_relative_positions(dialog.info["dna"], cell_id)
    update_organism_mirroring(dialog)

    remake_organism(dialog, dialog.info["dna"])

def curiosity_changed(dialog, val):
    dna = dialog.info["dna"]

    dna.base_info["curiosity"] = val

def pause_world(dialog):
    dialog.environment.info["paused"] = True
    dialog.environment.info["paused_time"] = time.time()
def resume_world(dialog):
    if not dialog.environment.info["paused"]:
        return
    dialog.environment.lastUpdated = time.time()

    dialog.environment.info["paused"] = False

def ac_combobox_activated(dialog, val):
    if val == 0:
        dialog.info["adding_cell"] = True
    else:
        dialog.info["adding_cell"] = False

def update_selection_widget(dialog):
    selected = dialog.info["selected_cell"]

    if dialog.selection_widget is not None:
        dialog.ui.scene.removeItem( dialog.selection_widget )
        dialog.selection_widget = None

    if selected is not None:
        cell_pos = selected.getPos()
        new_pos = [cell_pos[0] - selected.radius - 5, cell_pos[1] - selected.radius - 5]

        sImg = QtGui.QPixmap("Images/selection_image.png")
        sImg = sImg.scaled( (selected.radius*2) + 10, (selected.radius*2) + 10 )

        graphicsPixmapItem = QtWidgets.QGraphicsPixmapItem(sImg)

        graphicsPixmapItem.setPixmap(sImg)
        graphicsPixmapItem.setPos(new_pos[0], new_pos[1])

        dialog.ui.scene.addItem(graphicsPixmapItem)

        dialog.selection_widget = graphicsPixmapItem

def keyPressed(dialog, event):
    if event.key() == QtCore.Qt.Key_Space:
        if dialog.environment.info["paused"]:
            resume_world(dialog)
        else:
            pause_world(dialog)
    elif event.key() == QtCore.Qt.Key_F:
        finish_clicked(dialog, event)
    elif event.key() == QtCore.Qt.Key_C:
        cancel_clicked(dialog, event)

def hidden_layers_changed(dialog, val):
    remake_organism(dialog, dialog.info["dna"])


def setup_editor_buttons(dialog, environment):
    if not dialog.main_environment.info["copied"]:
        starter_dna = sprites.DNA().randomize(cellRange=[1, 2], sizeRange=[20, 21], massRange=[10, 11], mirror_x=[1, 0], mirror_y=[1, 0])
    else:
        starter_dna = dialog.main_environment.info["copied"].copy()

    dialog.environment = physics.setupEnvironment(dialog.ui.worldView, dialog.ui.scene)
    dialog.selection_widget = None

    dialog.environment.info["paused"] = True
    dialog.environment.info["paused_time"] = time.time()

    dialog.environment.mousePressFunc = lambda event, pos: mousePressEvent(event, pos, dialog)

    organism = sprites.Organism(
        [dialog.ui.scene.width()/2, dialog.ui.scene.height()/2],
        dialog.environment,
        dna = starter_dna
    )

    dialog.info = {
        "selected_cell": None,
        "dna": starter_dna,
        "organism": organism,
        "sprites": [],
        "saving": False,
        "cell_recently_selected": False,
        "adding_cell": True
    }

    dialog.ui.worldView.mouseMoveEvent = lambda event: mouseMoveEvent(dialog.ui.worldView, event)
    dialog.ui.worldView.setMouseTracking(True)

    dialog.ui.curiosity_val.valueChanged.connect( lambda val: curiosity_changed(dialog, val) )
    dialog.ui.curiosity_val.setValue(dialog.info["dna"].base_info["curiosity"])

    dialog.ui.worldView.keyPressEvent = lambda event: keyPressed(dialog, event)

    dialog.environment.info["organism_list"].append(organism)
    organism.build_body()

    dialog.environment.postUpdateEvent = lambda: update_ui(dialog, dialog.environment)

    dialog.environment.mousePressFunc = lambda event, pos: mousePressEvent(event, pos, dialog)

    dialog.ui.direction_dial.valueChanged.connect( lambda val: dial_changed(dialog, val) )

    dialog.ui.mirror_x_checkbox.setChecked(dialog.info["dna"].base_info["mirror_x"])
    dialog.ui.mirror_y_checkbox.setChecked(dialog.info["dna"].base_info["mirror_y"])

    dialog.ui.mirror_x_checkbox.toggled.connect( lambda val: mirror_x_changed(dialog, val) )
    dialog.ui.mirror_y_checkbox.toggled.connect( lambda val: mirror_y_changed(dialog, val) )

    dialog.ui.finish_btn.clicked.connect( lambda event: finish_clicked(dialog, event) )
    dialog.ui.reset_btn.clicked.connect( lambda event: reset_clicked(dialog, event) )
    dialog.ui.cancel_btn.clicked.connect( lambda event: cancel_clicked(dialog, event) )

    dialog.ui.size_val.valueChanged.connect( lambda val: size_changed(dialog, val) )
    dialog.ui.mass_val.valueChanged.connect( lambda val: mass_changed(dialog, val) )
    dialog.ui.elasticity_val.valueChanged.connect( lambda val: elasticity_changed(dialog, val) )
    dialog.ui.friction_val.valueChanged.connect( lambda val: friction_changed(dialog, val) )

    dialog.ui.hidden_layers_val.setValue( len(dialog.info["organism"].brain.layers())-1 )
    dialog.ui.hidden_layers_val.valueChanged.connect( lambda val: hidden_layers_changed(dialog, val) )

    dialog.ui.ac_combobox.activated.connect( lambda val: ac_combobox_activated(dialog, val) )

    dialog.ui.cell_body_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "body") )
    dialog.ui.cell_barrier_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "barrier") )
    dialog.ui.cell_carniv_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "carniv") )
    dialog.ui.cell_co2c_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "co2C") )
    dialog.ui.cell_eye_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "eye") )
    dialog.ui.cell_olfactory_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "olfactory") )
    dialog.ui.cell_move_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "push") )
    dialog.ui.cell_rotate_btn.clicked.connect( lambda v: cell_btn_clicked(dialog, "rotate") )

    dialog.ui.delete_btn.clicked.connect( lambda v: delete_btn_clicked(dialog) )
