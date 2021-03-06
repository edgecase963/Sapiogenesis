# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'EditorWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(653, 616)
        self.worldView = QtWidgets.QGraphicsView(Form)
        self.worldView.setGeometry(QtCore.QRect(10, 25, 530, 360))
        self.worldView.setObjectName("worldView")
        self.org_info_frame = QtWidgets.QFrame(Form)
        self.org_info_frame.setGeometry(QtCore.QRect(350, 390, 191, 80))
        self.org_info_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.org_info_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.org_info_frame.setObjectName("org_info_frame")
        self.max_energy_val = QtWidgets.QLabel(self.org_info_frame)
        self.max_energy_val.setGeometry(QtCore.QRect(110, 10, 71, 25))
        self.max_energy_val.setStatusTip("")
        self.max_energy_val.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.max_energy_val.setObjectName("max_energy_val")
        self.max_energy_label = QtWidgets.QLabel(self.org_info_frame)
        self.max_energy_label.setGeometry(QtCore.QRect(10, 10, 91, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.max_energy_label.setFont(font)
        self.max_energy_label.setToolTip("")
        self.max_energy_label.setStatusTip("")
        self.max_energy_label.setObjectName("max_energy_label")
        self.max_health_label = QtWidgets.QLabel(self.org_info_frame)
        self.max_health_label.setGeometry(QtCore.QRect(10, 40, 91, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.max_health_label.setFont(font)
        self.max_health_label.setToolTip("")
        self.max_health_label.setStatusTip("")
        self.max_health_label.setObjectName("max_health_label")
        self.max_health_val = QtWidgets.QLabel(self.org_info_frame)
        self.max_health_val.setGeometry(QtCore.QRect(110, 40, 71, 25))
        self.max_health_val.setStatusTip("")
        self.max_health_val.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.max_health_val.setObjectName("max_health_val")
        self.mirror_x_checkbox = QtWidgets.QCheckBox(Form)
        self.mirror_x_checkbox.setGeometry(QtCore.QRect(20, 390, 92, 23))
        self.mirror_x_checkbox.setObjectName("mirror_x_checkbox")
        self.mirror_y_checkbox = QtWidgets.QCheckBox(Form)
        self.mirror_y_checkbox.setGeometry(QtCore.QRect(20, 415, 92, 23))
        self.mirror_y_checkbox.setObjectName("mirror_y_checkbox")
        self.cell_body_btn = QtWidgets.QPushButton(Form)
        self.cell_body_btn.setGeometry(QtCore.QRect(550, 50, 90, 25))
        self.cell_body_btn.setStatusTip("")
        self.cell_body_btn.setObjectName("cell_body_btn")
        self.cell_barrier_btn = QtWidgets.QPushButton(Form)
        self.cell_barrier_btn.setGeometry(QtCore.QRect(550, 80, 90, 25))
        self.cell_barrier_btn.setStatusTip("")
        self.cell_barrier_btn.setWhatsThis("")
        self.cell_barrier_btn.setObjectName("cell_barrier_btn")
        self.cell_carniv_btn = QtWidgets.QPushButton(Form)
        self.cell_carniv_btn.setGeometry(QtCore.QRect(550, 110, 90, 25))
        self.cell_carniv_btn.setObjectName("cell_carniv_btn")
        self.cell_co2c_btn = QtWidgets.QPushButton(Form)
        self.cell_co2c_btn.setGeometry(QtCore.QRect(550, 140, 90, 25))
        self.cell_co2c_btn.setObjectName("cell_co2c_btn")
        self.cell_eye_btn = QtWidgets.QPushButton(Form)
        self.cell_eye_btn.setGeometry(QtCore.QRect(550, 170, 90, 25))
        self.cell_eye_btn.setObjectName("cell_eye_btn")
        self.cell_olfactory_btn = QtWidgets.QPushButton(Form)
        self.cell_olfactory_btn.setGeometry(QtCore.QRect(550, 200, 90, 25))
        self.cell_olfactory_btn.setObjectName("cell_olfactory_btn")
        self.cell_move_btn = QtWidgets.QPushButton(Form)
        self.cell_move_btn.setGeometry(QtCore.QRect(550, 230, 90, 25))
        self.cell_move_btn.setObjectName("cell_move_btn")
        self.cell_rotate_btn = QtWidgets.QPushButton(Form)
        self.cell_rotate_btn.setGeometry(QtCore.QRect(550, 260, 90, 25))
        self.cell_rotate_btn.setObjectName("cell_rotate_btn")
        self.line = QtWidgets.QFrame(Form)
        self.line.setGeometry(QtCore.QRect(550, 290, 90, 10))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.mass_label = QtWidgets.QLabel(Form)
        self.mass_label.setGeometry(QtCore.QRect(550, 300, 95, 20))
        self.mass_label.setAlignment(QtCore.Qt.AlignCenter)
        self.mass_label.setObjectName("mass_label")
        self.mass_val = QtWidgets.QSpinBox(Form)
        self.mass_val.setGeometry(QtCore.QRect(550, 320, 95, 26))
        self.mass_val.setMinimum(1)
        self.mass_val.setMaximum(100)
        self.mass_val.setProperty("value", 10)
        self.mass_val.setObjectName("mass_val")
        self.size_val = QtWidgets.QSpinBox(Form)
        self.size_val.setGeometry(QtCore.QRect(550, 375, 95, 26))
        self.size_val.setMinimum(1)
        self.size_val.setMaximum(1000)
        self.size_val.setProperty("value", 20)
        self.size_val.setObjectName("size_val")
        self.size_label = QtWidgets.QLabel(Form)
        self.size_label.setGeometry(QtCore.QRect(550, 355, 95, 20))
        self.size_label.setAlignment(QtCore.Qt.AlignCenter)
        self.size_label.setObjectName("size_label")
        self.elasticity_val = QtWidgets.QDoubleSpinBox(Form)
        self.elasticity_val.setGeometry(QtCore.QRect(550, 430, 95, 26))
        self.elasticity_val.setMaximum(1.0)
        self.elasticity_val.setSingleStep(0.03)
        self.elasticity_val.setProperty("value", 0.5)
        self.elasticity_val.setObjectName("elasticity_val")
        self.elasticity_label = QtWidgets.QLabel(Form)
        self.elasticity_label.setGeometry(QtCore.QRect(550, 410, 95, 20))
        self.elasticity_label.setAlignment(QtCore.Qt.AlignCenter)
        self.elasticity_label.setObjectName("elasticity_label")
        self.friction_label = QtWidgets.QLabel(Form)
        self.friction_label.setGeometry(QtCore.QRect(550, 465, 95, 20))
        self.friction_label.setAlignment(QtCore.Qt.AlignCenter)
        self.friction_label.setObjectName("friction_label")
        self.friction_val = QtWidgets.QDoubleSpinBox(Form)
        self.friction_val.setGeometry(QtCore.QRect(550, 485, 95, 26))
        self.friction_val.setMaximum(1.0)
        self.friction_val.setSingleStep(0.03)
        self.friction_val.setProperty("value", 0.5)
        self.friction_val.setObjectName("friction_val")
        self.cell_info_frame = QtWidgets.QFrame(Form)
        self.cell_info_frame.setGeometry(QtCore.QRect(350, 480, 191, 91))
        self.cell_info_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.cell_info_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.cell_info_frame.setObjectName("cell_info_frame")
        self.selected_cell_val = QtWidgets.QLabel(self.cell_info_frame)
        self.selected_cell_val.setGeometry(QtCore.QRect(110, 10, 71, 25))
        self.selected_cell_val.setToolTip("")
        self.selected_cell_val.setStatusTip("")
        self.selected_cell_val.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.selected_cell_val.setObjectName("selected_cell_val")
        self.selected_cell_label = QtWidgets.QLabel(self.cell_info_frame)
        self.selected_cell_label.setGeometry(QtCore.QRect(10, 10, 101, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.selected_cell_label.setFont(font)
        self.selected_cell_label.setToolTip("")
        self.selected_cell_label.setObjectName("selected_cell_label")
        self.delete_btn = QtWidgets.QPushButton(self.cell_info_frame)
        self.delete_btn.setGeometry(QtCore.QRect(110, 40, 71, 25))
        self.delete_btn.setObjectName("delete_btn")
        self.direction_dial = QtWidgets.QDial(Form)
        self.direction_dial.setGeometry(QtCore.QRect(590, 520, 50, 50))
        self.direction_dial.setMaximum(100)
        self.direction_dial.setOrientation(QtCore.Qt.Horizontal)
        self.direction_dial.setWrapping(True)
        self.direction_dial.setNotchTarget(1.0)
        self.direction_dial.setObjectName("direction_dial")
        self.brain_frame = QtWidgets.QFrame(Form)
        self.brain_frame.setGeometry(QtCore.QRect(10, 449, 221, 81))
        self.brain_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.brain_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.brain_frame.setObjectName("brain_frame")
        self.curiosity_val = QtWidgets.QDoubleSpinBox(self.brain_frame)
        self.curiosity_val.setGeometry(QtCore.QRect(120, 10, 86, 25))
        self.curiosity_val.setStatusTip("")
        self.curiosity_val.setMinimum(0.0)
        self.curiosity_val.setMaximum(1.0)
        self.curiosity_val.setSingleStep(0.05)
        self.curiosity_val.setProperty("value", 0.5)
        self.curiosity_val.setObjectName("curiosity_val")
        self.curiosity_label = QtWidgets.QLabel(self.brain_frame)
        self.curiosity_label.setGeometry(QtCore.QRect(10, 10, 81, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.curiosity_label.setFont(font)
        self.curiosity_label.setToolTip("")
        self.curiosity_label.setStatusTip("")
        self.curiosity_label.setWhatsThis("")
        self.curiosity_label.setObjectName("curiosity_label")
        self.hidden_layers_val = QtWidgets.QSpinBox(self.brain_frame)
        self.hidden_layers_val.setGeometry(QtCore.QRect(120, 40, 86, 25))
        self.hidden_layers_val.setStatusTip("")
        self.hidden_layers_val.setMinimum(1)
        self.hidden_layers_val.setMaximum(9999)
        self.hidden_layers_val.setProperty("value", 6)
        self.hidden_layers_val.setObjectName("hidden_layers_val")
        self.hidden_layers_label = QtWidgets.QLabel(self.brain_frame)
        self.hidden_layers_label.setGeometry(QtCore.QRect(10, 40, 111, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.hidden_layers_label.setFont(font)
        self.hidden_layers_label.setStatusTip("")
        self.hidden_layers_label.setWhatsThis("")
        self.hidden_layers_label.setObjectName("hidden_layers_label")
        self.finish_btn = QtWidgets.QPushButton(Form)
        self.finish_btn.setGeometry(QtCore.QRect(550, 585, 89, 25))
        self.finish_btn.setObjectName("finish_btn")
        self.cancel_btn = QtWidgets.QPushButton(Form)
        self.cancel_btn.setGeometry(QtCore.QRect(450, 585, 89, 25))
        self.cancel_btn.setObjectName("cancel_btn")
        self.reset_btn = QtWidgets.QPushButton(Form)
        self.reset_btn.setGeometry(QtCore.QRect(350, 585, 89, 25))
        self.reset_btn.setObjectName("reset_btn")
        self.ac_combobox = QtWidgets.QComboBox(Form)
        self.ac_combobox.setGeometry(QtCore.QRect(550, 20, 86, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.ac_combobox.setFont(font)
        self.ac_combobox.setObjectName("ac_combobox")
        self.ac_combobox.addItem("")
        self.ac_combobox.addItem("")
        self.physics_val = QtWidgets.QLabel(Form)
        self.physics_val.setGeometry(QtCore.QRect(200, 390, 81, 25))
        self.physics_val.setToolTip("")
        self.physics_val.setStatusTip("")
        self.physics_val.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.physics_val.setObjectName("physics_val")
        self.physics_label = QtWidgets.QLabel(Form)
        self.physics_label.setGeometry(QtCore.QRect(130, 390, 61, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.physics_label.setFont(font)
        self.physics_label.setToolTip("")
        self.physics_label.setObjectName("physics_label")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Organism Editor"))
        self.max_energy_val.setToolTip(_translate("Form", "The maximum amount of energy for this organism"))
        self.max_energy_val.setText(_translate("Form", "0"))
        self.max_energy_label.setText(_translate("Form", "Max Energy:"))
        self.max_health_label.setText(_translate("Form", "Max Health:"))
        self.max_health_val.setToolTip(_translate("Form", "The maximum amount of health for this organism"))
        self.max_health_val.setText(_translate("Form", "0"))
        self.mirror_x_checkbox.setText(_translate("Form", "Mirror X"))
        self.mirror_y_checkbox.setText(_translate("Form", "Mirror Y"))
        self.cell_body_btn.setToolTip(_translate("Form", "This cell has no features, abilities, or neural inputs. It\'s the most plain cell of any organism"))
        self.cell_body_btn.setText(_translate("Form", "Body"))
        self.cell_barrier_btn.setToolTip(_translate("Form", "This cell is immune to damage from carnivorous cells"))
        self.cell_barrier_btn.setText(_translate("Form", "Barrier"))
        self.cell_carniv_btn.setToolTip(_translate("Form", "Used to damage/destroy cells of other organisms and eat dead cells"))
        self.cell_carniv_btn.setText(_translate("Form", "Carnivorous"))
        self.cell_co2c_btn.setToolTip(_translate("Form", "Converts CO2 into energy (photosynthesis)"))
        self.cell_co2c_btn.setText(_translate("Form", "Plant"))
        self.cell_eye_btn.setToolTip(_translate("Form", "Allows organisms to see nearby cells and their general direction"))
        self.cell_eye_btn.setText(_translate("Form", "Eye"))
        self.cell_olfactory_btn.setToolTip(_translate("Form", "Used to \"smell\" nearby dead cells"))
        self.cell_olfactory_btn.setText(_translate("Form", "Olfactory"))
        self.cell_move_btn.setToolTip(_translate("Form", "Allows organisms to move. The direction and speed is decided by the brain"))
        self.cell_move_btn.setText(_translate("Form", "Movement"))
        self.cell_rotate_btn.setToolTip(_translate("Form", "Organisms can make this cell rotate, allowing other cells around it to also rotate through friction"))
        self.cell_rotate_btn.setText(_translate("Form", "Rotational"))
        self.mass_label.setText(_translate("Form", "Mass"))
        self.mass_val.setToolTip(_translate("Form", "Useful for giving cells more health. But makes them heavier"))
        self.size_label.setText(_translate("Form", "Size"))
        self.elasticity_val.setToolTip(_translate("Form", "Higher = bouncier"))
        self.elasticity_label.setText(_translate("Form", "Elasticity"))
        self.friction_label.setText(_translate("Form", "Friction"))
        self.friction_val.setToolTip(_translate("Form", "Rotational cells move other cells with higher friction like gears"))
        self.selected_cell_val.setText(_translate("Form", "None"))
        self.selected_cell_label.setStatusTip(_translate("Form", "The loss of this organism\'s neural network (The higher the value = the more confused this organism is)"))
        self.selected_cell_label.setText(_translate("Form", "Selected Cell:"))
        self.delete_btn.setText(_translate("Form", "Delete"))
        self.direction_dial.setToolTip(_translate("Form", "This dial changes the growth direction of the selected cell"))
        self.curiosity_val.setToolTip(_translate("Form", "The higher this value, the more easily this organism can become bored"))
        self.curiosity_label.setText(_translate("Form", "Curiosity:"))
        self.hidden_layers_val.setToolTip(_translate("Form", "Pro tip: more doesn\'t always mean smarter"))
        self.hidden_layers_label.setToolTip(_translate("Form", "How many hidden layers this organism has in its neural network"))
        self.hidden_layers_label.setText(_translate("Form", "Hidden Layers:"))
        self.finish_btn.setText(_translate("Form", "Finish"))
        self.cancel_btn.setText(_translate("Form", "Cancel"))
        self.reset_btn.setText(_translate("Form", "Reset"))
        self.ac_combobox.setItemText(0, _translate("Form", "Add"))
        self.ac_combobox.setItemText(1, _translate("Form", "Change"))
        self.physics_val.setText(_translate("Form", "Paused"))
        self.physics_label.setStatusTip(_translate("Form", "The loss of this organism\'s neural network (The higher the value = the more confused this organism is)"))
        self.physics_label.setText(_translate("Form", "Physics:"))
