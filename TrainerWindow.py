# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TrainerWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Trainer(object):
    def setupUi(self, Trainer):
        Trainer.setObjectName("Trainer")
        Trainer.resize(270, 260)
        self.epochs_val = QtWidgets.QSpinBox(Trainer)
        self.epochs_val.setGeometry(QtCore.QRect(130, 30, 101, 25))
        self.epochs_val.setMinimum(0)
        self.epochs_val.setMaximum(999999)
        self.epochs_val.setSingleStep(100)
        self.epochs_val.setProperty("value", 100)
        self.epochs_val.setObjectName("epochs_val")
        self.train_for_label = QtWidgets.QLabel(Trainer)
        self.train_for_label.setGeometry(QtCore.QRect(30, 30, 91, 25))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.train_for_label.setFont(font)
        self.train_for_label.setObjectName("train_for_label")
        self.progress_bar = QtWidgets.QProgressBar(Trainer)
        self.progress_bar.setGeometry(QtCore.QRect(70, 100, 130, 23))
        self.progress_bar.setProperty("value", 0)
        self.progress_bar.setObjectName("progress_bar")
        self.loss_val = QtWidgets.QLabel(Trainer)
        self.loss_val.setGeometry(QtCore.QRect(110, 200, 121, 25))
        self.loss_val.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.loss_val.setObjectName("loss_val")
        self.train_btn = QtWidgets.QPushButton(Trainer)
        self.train_btn.setGeometry(QtCore.QRect(90, 140, 89, 25))
        self.train_btn.setObjectName("train_btn")
        self.loss_label = QtWidgets.QLabel(Trainer)
        self.loss_label.setGeometry(QtCore.QRect(50, 200, 51, 25))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.loss_label.setFont(font)
        self.loss_label.setObjectName("loss_label")
        self.finish_btn = QtWidgets.QPushButton(Trainer)
        self.finish_btn.setGeometry(QtCore.QRect(170, 230, 89, 25))
        self.finish_btn.setObjectName("finish_btn")
        self.epochs_dis_label = QtWidgets.QLabel(Trainer)
        self.epochs_dis_label.setGeometry(QtCore.QRect(50, 170, 61, 25))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.epochs_dis_label.setFont(font)
        self.epochs_dis_label.setObjectName("epochs_dis_label")
        self.epochs_label = QtWidgets.QLabel(Trainer)
        self.epochs_label.setGeometry(QtCore.QRect(120, 170, 111, 25))
        self.epochs_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.epochs_label.setObjectName("epochs_label")

        self.retranslateUi(Trainer)
        QtCore.QMetaObject.connectSlotsByName(Trainer)

    def retranslateUi(self, Trainer):
        _translate = QtCore.QCoreApplication.translate
        Trainer.setWindowTitle(_translate("Trainer", "Trainer"))
        self.train_for_label.setText(_translate("Trainer", "Train For:"))
        self.loss_val.setText(_translate("Trainer", "0"))
        self.train_btn.setText(_translate("Trainer", "Train"))
        self.loss_label.setText(_translate("Trainer", "Loss:"))
        self.finish_btn.setText(_translate("Trainer", "Finish"))
        self.epochs_dis_label.setText(_translate("Trainer", "Epochs:"))
        self.epochs_label.setText(_translate("Trainer", "0"))
