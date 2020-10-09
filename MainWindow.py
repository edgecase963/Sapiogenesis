#!/usr/bin/env python
from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
import sys
#import sprites
import random

sys.path.insert(1, "../../Programs/shatterbox")

import shatterbox


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1100, 800)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))

        self.worldView = QtWidgets.QGraphicsView(self.centralwidget)
        self.worldView.setGeometry(QtCore.QRect(15, 20, 1070, 600))
        self.worldView.setObjectName(_fromUtf8("worldView"))

        self.timeline = QtCore.QTimeLine(1000)
        self.timeline.setFrameRange(0, 100)

        self.scene = QtWidgets.QGraphicsScene(self.worldView)
        self.scene.setSceneRect(0, 0, 1050, 1200)
        self.worldView.setScene(self.scene)

        self.scene.mouseReleaseEvent = self.worldMouseReleaseEvent

        self.worldView.setBackgroundBrush( QtGui.QBrush( QtGui.QColor(180,180,255) ) )

        self.world_info_frame = QtWidgets.QFrame(self.centralwidget)
        self.world_info_frame.setGeometry(QtCore.QRect(15, 630, 220, 110))
        self.world_info_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.world_info_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.world_info_frame.setObjectName(_fromUtf8("world_info_frame"))

        self.pop_val = QtWidgets.QLabel(self.world_info_frame)
        self.pop_val.setGeometry(QtCore.QRect(110, 70, 100, 25))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.pop_val.setFont(font)
        self.pop_val.setObjectName(_fromUtf8("pop_val"))

        self.time_label = QtWidgets.QLabel(self.world_info_frame)
        self.time_label.setGeometry(QtCore.QRect(10, 40, 60, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.time_label.setFont(font)
        self.time_label.setStatusTip(_fromUtf8("This world's age"))
        self.time_label.setObjectName(_fromUtf8("time_label"))

        self.pop_label = QtWidgets.QLabel(self.world_info_frame)
        self.pop_label.setGeometry(QtCore.QRect(10, 70, 90, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pop_label.setFont(font)
        self.pop_label.setStatusTip(_fromUtf8("How many organisms are in this world"))
        self.pop_label.setObjectName(_fromUtf8("pop_label"))

        self.co2_label = QtWidgets.QLabel(self.world_info_frame)
        self.co2_label.setGeometry(QtCore.QRect(10, 10, 60, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.co2_label.setFont(font)
        self.co2_label.setStatusTip(_fromUtf8("The amount of CO2 in this world"))
        self.co2_label.setObjectName(_fromUtf8("co2_label"))

        self.co2_val = QtWidgets.QLabel(self.world_info_frame)
        self.co2_val.setGeometry(QtCore.QRect(70, 10, 140, 25))
        self.co2_val.setObjectName(_fromUtf8("co2_val"))

        self.time_val = QtWidgets.QLabel(self.world_info_frame)
        self.time_val.setGeometry(QtCore.QRect(70, 40, 140, 25))
        self.time_val.setObjectName(_fromUtf8("time_val"))

        self.world_controls_frame = QtWidgets.QFrame(self.centralwidget)
        self.world_controls_frame.setGeometry(QtCore.QRect(260, 630, 271, 110))
        self.world_controls_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.world_controls_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.world_controls_frame.setObjectName(_fromUtf8("world_controls_frame"))

        self.add_co2_btn = QtWidgets.QPushButton(self.world_controls_frame)
        self.add_co2_btn.setGeometry(QtCore.QRect(10, 10, 100, 27))
        self.add_co2_btn.setStatusTip(_fromUtf8("Adds CO2 into the world"))
        self.add_co2_btn.setObjectName(_fromUtf8("add_co2_btn"))

        self.co2_spinBox = QtWidgets.QSpinBox(self.world_controls_frame)
        self.co2_spinBox.setGeometry(QtCore.QRect(120, 10, 131, 29))
        self.co2_spinBox.setStatusTip(_fromUtf8("Amount of CO2 to add"))
        self.co2_spinBox.setMaximum(999999999)
        self.co2_spinBox.setProperty("value", 100)
        self.co2_spinBox.setObjectName(_fromUtf8("co2_spinBox"))

        self.rem_co2_btn = QtWidgets.QPushButton(self.world_controls_frame)
        self.rem_co2_btn.setGeometry(QtCore.QRect(10, 40, 100, 27))
        self.rem_co2_btn.setStatusTip(_fromUtf8("Removes CO2 from the world"))
        self.rem_co2_btn.setObjectName(_fromUtf8("rem_co2_btn"))

        self.rem_co2_spinbox = QtWidgets.QSpinBox(self.world_controls_frame)
        self.rem_co2_spinbox.setGeometry(QtCore.QRect(120, 40, 131, 29))
        self.rem_co2_spinbox.setStatusTip(_fromUtf8("Amount of CO2 to remove"))
        self.rem_co2_spinbox.setMaximum(999999999)
        self.rem_co2_spinbox.setProperty("value", 100)
        self.rem_co2_spinbox.setObjectName(_fromUtf8("rem_co2_spinbox"))

        self.set_co2_btn = QtWidgets.QPushButton(self.world_controls_frame)
        self.set_co2_btn.setGeometry(QtCore.QRect(10, 70, 100, 27))
        self.set_co2_btn.setStatusTip(_fromUtf8("Sets the world's CO2 to a specific value"))
        self.set_co2_btn.setObjectName(_fromUtf8("set_co2_btn"))

        self.set_co2_spinbox = QtWidgets.QSpinBox(self.world_controls_frame)
        self.set_co2_spinbox.setGeometry(QtCore.QRect(120, 70, 131, 29))
        self.set_co2_spinbox.setStatusTip(_fromUtf8("New CO2 value"))
        self.set_co2_spinbox.setMaximum(999999999)
        self.set_co2_spinbox.setProperty("value", 1800)
        self.set_co2_spinbox.setObjectName(_fromUtf8("set_co2_spinbox"))

        self.organismView = QtWidgets.QGraphicsView(self.centralwidget)
        self.organismView.setGeometry(QtCore.QRect(556, 630, 141, 110))
        self.organismView.setObjectName(_fromUtf8("organismView"))

        self.organism_controls_frame = QtWidgets.QFrame(self.centralwidget)
        self.organism_controls_frame.setGeometry(QtCore.QRect(920, 630, 165, 110))
        self.organism_controls_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.organism_controls_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.organism_controls_frame.setObjectName(_fromUtf8("organism_controls_frame"))

        self.kill_btn = QtWidgets.QPushButton(self.organism_controls_frame)
        self.kill_btn.setGeometry(QtCore.QRect(15, 10, 55, 27))
        self.kill_btn.setStatusTip(_fromUtf8("Kill this organism"))
        self.kill_btn.setObjectName(_fromUtf8("kill_btn"))

        self.feed_btn = QtWidgets.QPushButton(self.organism_controls_frame)
        self.feed_btn.setGeometry(QtCore.QRect(15, 40, 55, 27))
        self.feed_btn.setStatusTip(_fromUtf8("Feed this organism"))
        self.feed_btn.setObjectName(_fromUtf8("feed_btn"))

        self.view_brain_btn = QtWidgets.QPushButton(self.organism_controls_frame)
        self.view_brain_btn.setGeometry(QtCore.QRect(40, 75, 85, 27))
        self.view_brain_btn.setStatusTip(_fromUtf8("View this organism's brain"))
        self.view_brain_btn.setObjectName(_fromUtf8("view_brain_btn"))

        self.save_organism_btn = QtWidgets.QPushButton(self.organism_controls_frame)
        self.save_organism_btn.setGeometry(QtCore.QRect(90, 10, 60, 27))
        self.save_organism_btn.setStatusTip(_fromUtf8("Save this organism to a file"))
        self.save_organism_btn.setObjectName(_fromUtf8("save_organism_btn"))

        self.hurt_btn = QtWidgets.QPushButton(self.organism_controls_frame)
        self.hurt_btn.setGeometry(QtCore.QRect(90, 40, 60, 27))
        self.hurt_btn.setStatusTip(_fromUtf8("Take energy from this organism"))
        self.hurt_btn.setObjectName(_fromUtf8("hurt_btn"))

        self.organism_info_frame = QtWidgets.QFrame(self.centralwidget)
        self.organism_info_frame.setGeometry(QtCore.QRect(720, 630, 181, 110))
        self.organism_info_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.organism_info_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.organism_info_frame.setObjectName(_fromUtf8("organism_info_frame"))

        self.energy_label = QtWidgets.QLabel(self.organism_info_frame)
        self.energy_label.setGeometry(QtCore.QRect(10, 10, 60, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.energy_label.setFont(font)
        self.energy_label.setStatusTip(_fromUtf8("How much energy this organism has"))
        self.energy_label.setObjectName(_fromUtf8("energy_label"))

        self.generation_label = QtWidgets.QLabel(self.organism_info_frame)
        self.generation_label.setGeometry(QtCore.QRect(10, 40, 90, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.generation_label.setFont(font)
        self.generation_label.setStatusTip(_fromUtf8("This organism's generation"))
        self.generation_label.setObjectName(_fromUtf8("generation_label"))

        self.neurons_label = QtWidgets.QLabel(self.organism_info_frame)
        self.neurons_label.setGeometry(QtCore.QRect(10, 70, 70, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.neurons_label.setFont(font)
        self.neurons_label.setStatusTip(_fromUtf8("How many neurons are in this organism's brain"))
        self.neurons_label.setObjectName(_fromUtf8("neurons_label"))

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1100, 31))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.actionNew = QtWidgets.QAction(MainWindow)
        self.actionNew.setObjectName(_fromUtf8("actionNew"))

        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName(_fromUtf8("actionOpen"))

        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))

        self.actionSave_As = QtWidgets.QAction(MainWindow)
        self.actionSave_As.setObjectName(_fromUtf8("actionSave_As"))

        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))

        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.timeline.start()

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "NSS", None))
        self.pop_val.setText(_translate("MainWindow", "0", None))
        self.time_label.setText(_translate("MainWindow", "Time:", None))
        self.pop_label.setText(_translate("MainWindow", "Population:", None))
        self.co2_label.setText(_translate("MainWindow", "CO2:", None))
        self.co2_val.setText(_translate("MainWindow", "0", None))
        self.time_val.setText(_translate("MainWindow", "0", None))
        self.add_co2_btn.setText(_translate("MainWindow", "Add CO2", None))
        self.rem_co2_btn.setText(_translate("MainWindow", "Remove CO2", None))
        self.set_co2_btn.setText(_translate("MainWindow", "Set CO2", None))
        self.kill_btn.setText(_translate("MainWindow", "Kill", None))
        self.feed_btn.setText(_translate("MainWindow", "Feed", None))
        self.view_brain_btn.setText(_translate("MainWindow", "View Brain", None))
        self.save_organism_btn.setText(_translate("MainWindow", "Save", None))
        self.hurt_btn.setText(_translate("MainWindow", "Hurt", None))
        self.energy_label.setText(_translate("MainWindow", "Energy:", None))
        self.generation_label.setText(_translate("MainWindow", "Generation:", None))
        self.neurons_label.setText(_translate("MainWindow", "Neurons:", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.actionNew.setText(_translate("MainWindow", "New...", None))
        self.actionOpen.setText(_translate("MainWindow", "Open...", None))
        self.actionSave.setText(_translate("MainWindow", "Save", None))
        self.actionSave_As.setText(_translate("MainWindow", "Save As...", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))

    def addOrganism(self, xy):
        #cell = sprites.Cell(xy, 100, 100, image="Images/neuron.png")
        print("Creature Position: {}".format(xy))
        crit = sprites.Creature(xy, 20, 20)
        self.scene.addItem(crit)
        self.organisms.append(crit)

    def worldMouseReleaseEvent(self, event):
        pos = event.lastScenePos()   # pos = QtCore.QPointF

        print("Pos: {}, {}".format( pos.x(), pos.y() ))
        #for org in self.organisms:
        #    org.bump(pos, 500)



if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = shatterbox.setupEnvironment(myapp.worldView, myapp.scene)

        sprite1 = env.add_ball_sprite([300,300], 40, 40, image="Images/neuron.png")
        sprite2 = env.add_ball_sprite([320,320], 40, 40, image="Images/eye.png")

        window.show()
        sys.exit(app.exec_())
