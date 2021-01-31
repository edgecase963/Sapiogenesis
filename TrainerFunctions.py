import neural

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets



def train_btn_clicked(dialog):
    for i in range(dialog.ui.epochs_val.value()):
        neural.train_network(
            dialog.organism,
            epochs=1
        )
        progress_perc = (i / dialog.ui.epochs_val.value()) * 100
        dialog.ui.progress_bar.setValue(progress_perc)
        dialog.ui.epochs_label.setText( str(dialog.organism.brain.trainer.iterations) )
        dialog.ui.loss_val.setText( str(round(dialog.organism.brain.lastLoss, 10)) )


def setup_editor_buttons(dialog, organism):
    dialog.organism = organism

    dialog.ui.train_btn.clicked.connect( lambda event: train_btn_clicked(dialog) )
    dialog.ui.finish_btn.clicked.connect( lambda event: dialog.close() )
    dialog.ui.epochs_label.setText( str(dialog.organism.brain.trainer.iterations) )
    dialog.ui.loss_val.setText( str(round(dialog.organism.brain.lastLoss, 8)) )
